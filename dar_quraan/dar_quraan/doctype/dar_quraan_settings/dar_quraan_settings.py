import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, validate_email_address


class DarQuraanSettings(Document):
	POSITIVE_FIELDS = (
		"absence_threshold",
		"lateness_threshold",
		"weak_result_threshold",
		"no_progress_days",
		"evaluation_overdue_days",
		"attendance_grace_days",
	)

	def validate(self):
		for fieldname in self.POSITIVE_FIELDS:
			if cint(self.get(fieldname)) <= 0:
				frappe.throw(_("{0} must be greater than zero.").format(self.meta.get_label(fieldname)))
		if cint(self.follow_up_reminder_days) < 0:
			frappe.throw(_("Follow-up Reminder Days cannot be negative."))
		recipients = [
			value.strip() for value in (self.notification_recipients or "").split(",") if value.strip()
		]
		for recipient in recipients:
			if not validate_email_address(recipient):
				frappe.throw(_("Invalid notification email address: {0}").format(recipient))
		self.notification_recipients = ", ".join(recipients)
