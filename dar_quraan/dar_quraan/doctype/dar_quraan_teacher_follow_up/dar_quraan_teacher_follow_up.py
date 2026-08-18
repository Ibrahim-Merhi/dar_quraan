from typing import ClassVar

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate


class DarQuraanTeacherFollowUp(Document):
	FOLLOW_UP_TYPES: ClassVar[set[str]] = {
		"Attendance",
		"Memorization",
		"Revision",
		"Tajweed",
		"Fluency",
		"Evaluation",
		"Behavior",
		"Parent Contact",
		"General Academic",
		"Other",
	}
	PRIORITIES: ClassVar[set[str]] = {"Low", "Medium", "High", "Urgent"}
	STATUSES: ClassVar[set[str]] = {"Open", "In Progress", "Resolved", "Cancelled"}

	def validate(self):
		self.validate_student_assignment()
		self.fetch_assignment_context()
		self.validate_required_values()
		self.validate_select_values()
		self.validate_sources()
		self.validate_follow_up_schedule()
		self.validate_resolution()

	def validate_student_assignment(self):
		if not self.student_assignment:
			frappe.throw(_("Student Assignment is required."))
		if not frappe.db.exists("Dar Quraan Student Assignment", self.student_assignment):
			frappe.throw(_("Selected Student Assignment does not exist."))

	def fetch_assignment_context(self):
		assignment = frappe.get_doc("Dar Quraan Student Assignment", self.student_assignment)
		for fieldname in (
			"student",
			"student_name",
			"branch",
			"teaching_location",
			"halaqa",
			"teacher",
			"study_track",
			"riwayah",
		):
			self.set(fieldname, assignment.get(fieldname))
		if not self.student:
			frappe.throw(_("Student Assignment {0} does not have a Student.").format(self.student_assignment))
		if not self.teacher:
			frappe.throw(_("Student Assignment {0} does not have a Teacher.").format(self.student_assignment))
		if not self.halaqa:
			frappe.throw(_("Student Assignment {0} does not have a Halaqa.").format(self.student_assignment))

	def validate_required_values(self):
		if not self.follow_up_date:
			frappe.throw(_("Follow-up Date is required."))
		if not self.follow_up_type:
			frappe.throw(_("Follow-up Type is required."))
		if not self.priority:
			frappe.throw(_("Priority is required."))
		if not (self.issue_description or "").strip():
			frappe.throw(_("Issue Description is required."))

	def validate_select_values(self):
		if self.follow_up_type not in self.FOLLOW_UP_TYPES:
			frappe.throw(_("Invalid Follow-up Type."))
		if self.priority not in self.PRIORITIES:
			frappe.throw(_("Invalid Priority."))
		if self.status not in self.STATUSES:
			frappe.throw(_("Invalid Status."))

	def validate_sources(self):
		self.validate_assignment_source(
			"Dar Quraan Student Progress", self.source_progress, _("Student Progress")
		)
		self.validate_assignment_source("Dar Quraan Evaluation", self.source_evaluation, _("Evaluation"))
		self.validate_attendance_source()

	def validate_assignment_source(self, doctype, source, label):
		if not source:
			return
		if not frappe.db.exists(doctype, source):
			frappe.throw(_("Selected {0} does not exist.").format(label))
		source_assignment = frappe.db.get_value(doctype, source, "student_assignment")
		if source_assignment != self.student_assignment:
			frappe.throw(
				_("Selected {0} does not belong to Student Assignment {1}.").format(
					label, self.student_assignment
				)
			)

	def validate_attendance_source(self):
		if not self.source_attendance:
			return
		if not frappe.db.exists("Dar Quraan Attendance", self.source_attendance):
			frappe.throw(_("Selected Attendance does not exist."))
		matching_item = frappe.db.exists(
			"Dar Quraan Attendance Item",
			{
				"parent": self.source_attendance,
				"parenttype": "Dar Quraan Attendance",
				"student_assignment": self.student_assignment,
			},
		)
		if not matching_item:
			frappe.throw(
				_("Selected Attendance does not contain Student Assignment {0}.").format(
					self.student_assignment
				)
			)

	def validate_follow_up_schedule(self):
		closed = self.status in {"Resolved", "Cancelled"}
		if closed and cint(self.follow_up_required):
			frappe.throw(_("Resolved or Cancelled follow-ups cannot require another follow-up."))
		if cint(self.follow_up_required) and not self.next_follow_up_date:
			frappe.throw(_("Next Follow-up Date is required when follow-up is required."))
		if self.next_follow_up_date and getdate(self.next_follow_up_date) < getdate(self.follow_up_date):
			frappe.throw(_("Next Follow-up Date cannot be before Follow-up Date."))

	def validate_resolution(self):
		if self.status == "Resolved" and not (self.resolution_notes or "").strip():
			frappe.throw(_("Resolution Notes are required for a Resolved follow-up."))
