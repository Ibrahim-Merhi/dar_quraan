import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class DarQuraanTextProgress(Document):
	def validate(self):
		assignment = frappe.db.get_value(
			"Dar Quraan Student Assignment", self.student_assignment, ["student", "teacher"], as_dict=True
		)
		if not assignment:
			frappe.throw(_("Student Assignment does not exist."))
		self.student, self.teacher = assignment.student, assignment.teacher
		if not 0 <= flt(self.memorization_percentage) <= 100:
			frappe.throw(_("Memorization Percentage must be between 0 and 100."))
		if self.status == "Completed" and (
			flt(self.memorization_percentage) != 100
			or self.explanation_status != "Completed"
			or self.teacher_assessment != "Passed"
		):
			frappe.throw(
				_(
					"Text completion requires 100% memorization, completed explanation, and a passing teacher assessment."
				)
			)
