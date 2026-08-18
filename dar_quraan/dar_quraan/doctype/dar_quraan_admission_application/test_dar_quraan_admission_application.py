from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanAdmissionApplication(FrappeTestCase):
	def make_application(self, **values):
		data = {
			"doctype": "Dar Quraan Admission Application",
			"first_name": "Ahmad",
			"last_name": "Test",
			"gender": "Male",
			"date_of_birth": "2000-01-01",
			"mobile_number": "+961 70 123 456",
			"admission_goal": "Hifz",
			"study_track": "Hifz",
			"quran_status": "Memorizing",
			"memorized_juz": 3,
			"status": "Pending",
			"notify_by_email": 0,
		}
		data.update(values)
		return frappe.get_doc(data)

	def test_normalizes_profile(self):
		doc = self.make_application(middle_name="  Mohammad ")
		doc.before_validate()
		self.assertEqual(doc.applicant_name, "Ahmad Mohammad Test")
		self.assertEqual(doc.mobile_number, "+96170123456")

	def test_memorized_juz_range(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_application(memorized_juz=31).validate()

	def test_previous_ijazah_requires_details(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_application(has_previous_ijazah=1).validate()

	def test_rejection_requires_reason(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_application(status="Rejected").validate()

	def test_approval_requires_placement(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_application(status="Provisionally Approved").validate()

	def test_finalization_requires_provisional_status(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_application().finalize_admission()

	def test_notification_is_disabled_without_channels(self):
		doc = self.make_application(name="DQ-ADM-TEST", notify_by_email=0, notify_by_sms=0)
		with patch.object(doc, "db_set") as db_set:
			doc.send_status_notification()
		db_set.assert_called_once_with("last_notification_status", "Disabled", update_modified=False)
