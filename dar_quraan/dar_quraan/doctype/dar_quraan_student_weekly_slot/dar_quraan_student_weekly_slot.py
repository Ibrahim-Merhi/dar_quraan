import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class DarQuraanStudentWeeklySlot(Document):
	def validate(self):
		if not frappe.db.exists("Dar Quraan Student Assignment", self.student_assignment):
			frappe.throw(_("Student Assignment does not exist."))
		assignment = frappe.db.get_value(
			"Dar Quraan Student Assignment",
			self.student_assignment,
			["student", "teacher", "halaqa"],
			as_dict=True,
		)
		self.student, self.teacher, self.halaqa = assignment.student, assignment.teacher, assignment.halaqa
		start = (
			self.start_time.total_seconds()
			if hasattr(self.start_time, "total_seconds")
			else self._seconds(self.start_time)
		)
		end = (
			self.end_time.total_seconds()
			if hasattr(self.end_time, "total_seconds")
			else self._seconds(self.end_time)
		)
		self.duration_minutes = int((end - start) / 60)
		if self.duration_minutes < 30:
			frappe.throw(_("Each student must receive at least 30 minutes per week."))
		if self.effective_to and getdate(self.effective_to) < getdate(self.effective_from):
			frappe.throw(_("Effective To cannot be before Effective From."))

	@staticmethod
	def _seconds(value):
		parts = [int(part) for part in str(value).split(":")]
		return parts[0] * 3600 + parts[1] * 60 + (parts[2] if len(parts) > 2 else 0)
