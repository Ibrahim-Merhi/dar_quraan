import re
from typing import ClassVar

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate, now_datetime, nowdate, validate_email_address


class DarQuraanAdmissionApplication(Document):
	STATUSES: ClassVar[set[str]] = {
		"Pending",
		"In Process",
		"Provisionally Approved",
		"Final Approved",
		"Rejected",
		"Withdrawn",
	}
	TRANSITIONS: ClassVar[dict[str, set[str]]] = {
		"Pending": {"In Process", "Withdrawn"},
		"In Process": {"Provisionally Approved", "Rejected", "Withdrawn"},
		"Provisionally Approved": {"Final Approved", "Rejected", "Withdrawn"},
		"Final Approved": set(),
		"Rejected": {"In Process"},
		"Withdrawn": {"In Process"},
	}

	def before_validate(self):
		for fieldname in ("first_name", "middle_name", "last_name", "mother_name"):
			self.set(fieldname, self.clean_text(self.get(fieldname)))
		self.applicant_name = " ".join(filter(None, (self.first_name, self.middle_name, self.last_name)))
		for fieldname in ("mobile_number", "whatsapp_number", "home_number", "emergency_contact_number"):
			self.set(fieldname, self.normalize_phone(self.get(fieldname)))
		if self.email:
			self.email = self.email.strip().lower()

	def validate(self):
		if self.status not in self.STATUSES:
			frappe.throw(_("Invalid admission status."))
		if self.email and not validate_email_address(self.email):
			frappe.throw(_("Please enter a valid email address."))
		if self.date_of_birth and getdate(self.date_of_birth) >= getdate(nowdate()):
			frappe.throw(_("Date of Birth must be before today."))
		if not 0 <= cint(self.memorized_juz) <= 30:
			frappe.throw(_("Memorized Juz must be between 0 and 30."))
		if cint(self.has_previous_ijazah) and not (self.previous_ijazah_details or "").strip():
			frappe.throw(_("Previous Ijazah Details are required."))
		if (
			self.preferred_time_from
			and self.preferred_time_to
			and self.preferred_time_from >= self.preferred_time_to
		):
			frappe.throw(_("Preferred end time must be after start time."))
		self.validate_transition()
		self.validate_decision()

	def validate_transition(self):
		old = self.get_doc_before_save()
		if not old or old.status == self.status:
			return
		if self.status not in self.TRANSITIONS.get(old.status, set()):
			frappe.throw(_("Admission status cannot change from {0} to {1}.").format(old.status, self.status))

	def validate_decision(self):
		if self.status == "Rejected" and not (self.rejection_reason or "").strip():
			frappe.throw(_("Rejection Reason is required."))
		if self.status in {"Provisionally Approved", "Final Approved"}:
			for fieldname, label in (
				("proposed_teacher", _("Proposed Teacher")),
				("proposed_halaqa", _("Proposed Halaqa")),
				("expected_start_date", _("Expected Start Date")),
			):
				if not self.get(fieldname):
					frappe.throw(_("{0} is required for approval.").format(label))
		if self.status == "Final Approved" and not self.student:
			frappe.throw(_("Use Finalize Admission to create the linked student."))

	@staticmethod
	def clean_text(value):
		return " ".join(str(value).strip().split()) if value else None

	@staticmethod
	def normalize_phone(value):
		if not value:
			return None
		value = re.sub(r"[\s\-().]", "", str(value).strip())
		return f"+{value[2:]}" if value.startswith("00") else value

	def set_status(self, status):
		self.status = status
		if status == "In Process" and not self.review_started_on:
			self.review_started_on = now_datetime()
		if status == "Provisionally Approved":
			self.provisional_approval_date = nowdate()
		if status == "Rejected":
			self.decision_date = nowdate()
		self.save()
		self.send_status_notification()

	@frappe.whitelist()
	def start_review(self):
		self.set_status("In Process")

	@frappe.whitelist()
	def provisionally_approve(self):
		self.set_status("Provisionally Approved")

	@frappe.whitelist()
	def reject(self, reason=None):
		self.rejection_reason = reason or self.rejection_reason
		self.set_status("Rejected")

	@frappe.whitelist()
	def finalize_admission(self):
		if self.status != "Provisionally Approved":
			frappe.throw(_("Only a provisionally approved application can be finalized."))
		if self.student:
			frappe.throw(_("This application is already linked to a student."))
		student = frappe.get_doc(
			{
				"doctype": "Dar Quraan Student",
				"student_code": self.name,
				"first_name": self.first_name,
				"middle_name": self.middle_name,
				"last_name": self.last_name,
				"mother_name": self.mother_name,
				"gender": self.gender,
				"date_of_birth": self.date_of_birth,
				"nationality": self.nationality,
				"marital_status": self.marital_status,
				"mobile_number": self.mobile_number,
				"home_number": self.home_number,
				"email": self.email,
				"whatsapp_number": self.whatsapp_number,
				"address": self.address,
				"school_or_university": self.school_or_university,
				"major_or_grade": self.major_or_grade,
				"current_occupation": self.current_occupation,
				"skills": self.skills,
				"study_track": self.study_track,
				"qiraat_method": self.qiraat_method,
				"quran_status": self.quran_status,
				"current_riwayah": self.current_riwayah,
				"previous_sheikhs": self.previous_sheikhs,
				"has_previous_ijazah": self.has_previous_ijazah,
				"previous_ijazah_details": self.previous_ijazah_details,
				"initial_memorization_description": self.current_level_description,
				"default_branch": self.preferred_branch,
				"default_teacher": self.proposed_teacher,
				"default_halaqa": self.proposed_halaqa,
				"registration_date": nowdate(),
				"status": "Active",
			}
		).insert()
		halaqa = frappe.db.get_value(
			"Dar Quraan Halaqa",
			self.proposed_halaqa,
			["branch", "teaching_location", "academic_year", "academic_term"],
			as_dict=True,
		)
		if not halaqa or not halaqa.academic_year:
			frappe.throw(_("The proposed Halaqa must have a Branch and Academic Year."))
		assignment = frappe.get_doc(
			{
				"doctype": "Dar Quraan Student Assignment",
				"student": student.name,
				"assignment_type": "Primary",
				"status": "Active",
				"branch": halaqa.branch,
				"teaching_location": halaqa.teaching_location,
				"teacher": self.proposed_teacher,
				"halaqa": self.proposed_halaqa,
				"academic_year": halaqa.academic_year,
				"academic_term": halaqa.academic_term,
				"start_date": self.expected_start_date,
				"effective_from": self.expected_start_date,
				"study_track": self.study_track,
				"riwayah": self.current_riwayah,
				"current_juz_level": self.proposed_level,
				"admission_application": self.name,
				"program": self.proposed_program,
			}
		).insert()
		self.db_set("student", student.name, update_modified=False)
		self.db_set("student_assignment", assignment.name, update_modified=False)
		self.db_set("final_approval_date", nowdate(), update_modified=False)
		self.db_set("status", "Final Approved")
		self.reload()
		self.send_status_notification()
		return student.name

	def send_status_notification(self):
		message = _("Your Dar Quraan admission application {0} is now {1}.").format(self.name, self.status)
		delivered = []
		if cint(self.notify_by_email) and self.email:
			frappe.sendmail(
				recipients=[self.email], subject=_("Dar Quraan Admission Update"), message=message
			)
			delivered.append("Email")
		if cint(self.notify_by_sms) and self.mobile_number:
			from frappe.core.doctype.sms_settings.sms_settings import send_sms

			send_sms([self.mobile_number], message, success_msg=False)
			delivered.append("SMS")
		self.db_set(
			"last_notification_status",
			", ".join(delivered) if delivered else "Disabled",
			update_modified=False,
		)
