import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class DarQuraanIjazah(Document):
	def before_validate(self):
		self.certificate_number = self.certificate_number or (
			self.name if self.name and not self.is_new() else None
		)

	def validate(self):
		exam = frappe.db.get_value(
			"Dar Quraan Exam",
			self.exam,
			[
				"student_assignment",
				"student",
				"student_name",
				"exam_type",
				"final_score",
				"result",
				"status",
				"riwayah",
			],
			as_dict=True,
		)
		if not exam:
			frappe.throw(_("Final Exam does not exist."))
		if exam.student_assignment != self.student_assignment:
			frappe.throw(_("Final Exam belongs to another Student Assignment."))
		if (
			exam.exam_type not in {"Final 30 Juz", "Final 10 Juz", "Ijazah Retest"}
			or exam.status != "Completed"
			or exam.result != "Passed"
			or flt(exam.final_score) < 80
		):
			frappe.throw(_("Ijazah requires a completed passing final exam with at least 80%."))
		self.student, self.student_name, self.final_score = exam.student, exam.student_name, exam.final_score
		self.riwayah = self.riwayah or exam.riwayah
		if self.status == "Issued" and not (self.sanad_text or "").strip():
			frappe.throw(_("Connected Sanad Text is required before issuance."))
		if self.status == "Revoked" and not (self.revocation_reason or "").strip():
			frappe.throw(_("Revocation Reason is required."))

	def after_insert(self):
		if not self.certificate_number:
			self.db_set("certificate_number", self.name, update_modified=False)
