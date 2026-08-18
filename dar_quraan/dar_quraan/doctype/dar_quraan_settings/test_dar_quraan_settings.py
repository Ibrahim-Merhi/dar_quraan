import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanSettings(FrappeTestCase):
	def make_settings(self, **kwargs):
		values = {
			"doctype": "Dar Quraan Settings",
			"absence_threshold": 3,
			"lateness_threshold": 3,
			"weak_result_threshold": 3,
			"no_progress_days": 7,
			"evaluation_overdue_days": 30,
			"follow_up_reminder_days": 1,
			"attendance_grace_days": 1,
		}
		values.update(kwargs)
		return frappe.get_doc(values)

	def test_valid_settings(self):
		self.make_settings(notification_recipients="one@example.com, two@example.com").validate()

	def test_positive_thresholds(self):
		for fieldname in (
			"absence_threshold",
			"lateness_threshold",
			"weak_result_threshold",
			"no_progress_days",
			"evaluation_overdue_days",
			"attendance_grace_days",
		):
			with self.subTest(fieldname=fieldname), self.assertRaises(frappe.ValidationError):
				self.make_settings(**{fieldname: 0}).validate()

	def test_reminder_days_cannot_be_negative(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_settings(follow_up_reminder_days=-1).validate()

	def test_invalid_email_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_settings(notification_recipients="invalid").validate()
