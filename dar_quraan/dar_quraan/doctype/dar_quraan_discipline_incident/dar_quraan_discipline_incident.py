import frappe
from frappe import _
from frappe.model.document import Document


class DarQuraanDisciplineIncident(Document):
	def validate(self):
		assignment = frappe.db.get_value(
			"Dar Quraan Student Assignment",
			self.student_assignment,
			["student", "student_name"],
			as_dict=True,
		)
		rule = frappe.db.get_value(
			"Dar Quraan Discipline Rule",
			self.rule,
			["severity", "default_action", "requires_guardian_notification", "active"],
			as_dict=True,
		)
		if not assignment or not rule or not rule.active:
			frappe.throw(_("Student Assignment or active Discipline Rule is invalid."))
		self.student, self.student_name, self.severity = (
			assignment.student,
			assignment.student_name,
			rule.severity,
		)
		self.action_taken = self.action_taken or rule.default_action
		if rule.requires_guardian_notification and self.status == "Resolved" and not self.guardian_notified:
			frappe.throw(_("The guardian must be notified before resolving this incident."))
		if self.guardian_notified and not self.guardian_notification_date:
			frappe.throw(_("Guardian Notification Date is required."))
		if self.status == "Resolved" and not (self.resolution_notes or "").strip():
			frappe.throw(_("Resolution Notes are required."))
