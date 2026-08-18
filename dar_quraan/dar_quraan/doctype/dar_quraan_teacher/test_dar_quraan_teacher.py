from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanTeacher(FrappeTestCase):
	def make_teacher(self, **kwargs):
		values = {"doctype": "Dar Quraan Teacher", "teacher_name": "Test Teacher", "status": "Active"}
		values.update(kwargs)
		return frappe.get_doc(values)

	def test_valid_teacher(self):
		self.make_teacher().validate()

	def test_name_is_required(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_teacher(teacher_name=" ").validate()

	def test_invalid_status_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_teacher(status="Unknown").validate()

	def test_email_is_normalized(self):
		doc = self.make_teacher(email=" Teacher@Example.COM ")
		doc.validate()
		self.assertEqual(doc.email, "teacher@example.com")

	def test_invalid_email_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_teacher(email="invalid").validate()

	def test_active_teacher_requires_active_branch(self):
		doc = self.make_teacher(branch="DQ-BRANCH-001")
		with patch.object(frappe.db, "get_value", return_value="Inactive"):
			with self.assertRaises(frappe.ValidationError):
				doc.validate()

	def test_missing_branch_is_rejected(self):
		doc = self.make_teacher(branch="MISSING")
		with patch.object(frappe.db, "get_value", return_value=None):
			with self.assertRaises(frappe.ValidationError):
				doc.validate()
