import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class DarQuraanAttendanceItem(Document):
	def validate(self):
		self.validate_student()
		self.validate_student_assignment()
		self.validate_attendance_status()
		self.validate_late_minutes()
		self.validate_excuse()

	def validate_student(self):
		if not self.student:
			frappe.throw(_("Student is required."))

	def validate_student_assignment(self):
		if not self.student_assignment:
			frappe.throw(_("Student Assignment is required."))

	def validate_attendance_status(self):
		allowed_statuses = {
			"Present",
			"Absent",
			"Late",
			"Excused",
		}

		if not self.attendance_status:
			self.attendance_status = "Present"

		if self.attendance_status not in allowed_statuses:
			frappe.throw(_("Attendance Status must be Present, " "Absent, Late, or Excused."))

	def validate_late_minutes(self):
		late_minutes = cint(self.late_minutes)

		if late_minutes < 0:
			frappe.throw(_("Late Minutes cannot be negative."))

		if self.attendance_status == "Late":
			if late_minutes <= 0:
				frappe.throw(_("Late Minutes must be greater than " "zero when Attendance Status is Late."))

		else:
			self.late_minutes = 0

	def validate_excuse(self):
		if self.attendance_status == "Excused":
			if not self.excuse_reason:
				frappe.throw(_("Excuse Reason is required when " "Attendance Status is Excused."))

		else:
			self.excuse_reason = None
