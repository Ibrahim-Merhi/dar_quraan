from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanException(FrappeTestCase):
	def make_exception(self, **kwargs):
		values = {
			"doctype": "Dar Quraan Exception",
			"exception_type": "Overdue Follow-up",
			"severity": "High",
			"status": "Open",
			"message": "Follow-up is overdue.",
			"occurrence_count": 1,
		}
		values.update(kwargs)
		return frappe.get_doc(values)

	def test_valid_exception(self):
		self.make_exception().validate()

	def test_invalid_select_values(self):
		for fieldname in ("exception_type", "severity", "status"):
			with self.subTest(fieldname=fieldname), self.assertRaises(frappe.ValidationError):
				self.make_exception(**{fieldname: "Invalid"}).validate()

	def test_message_is_required(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_exception(message=" ").validate()

	def test_source_fields_are_paired(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_exception(source_doctype="Dar Quraan Halaqa").validate()

	def test_occurrence_count_is_normalized(self):
		doc = self.make_exception(occurrence_count=0)
		doc.validate()
		self.assertEqual(doc.occurrence_count, 1)

	def test_resolved_requires_notes_and_sets_date(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_exception(status="Resolved").validate()
		doc = self.make_exception(status="Resolved", resolution_notes="Reviewed.")
		doc.validate()
		self.assertTrue(doc.resolved_on)

	def test_assignment_context_is_authoritative(self):
		assignment = frappe._dict(
			{
				"student": "STUDENT",
				"student_name": "Student",
				"branch": "BRANCH",
				"teaching_location": "LOCATION",
				"halaqa": "HALAQA",
				"teacher": "TEACHER",
			}
		)
		doc = self.make_exception(student_assignment="ASSIGNMENT", student="WRONG")
		with (
			patch.object(frappe.db, "exists", return_value="ASSIGNMENT"),
			patch.object(frappe, "get_doc", return_value=assignment),
		):
			doc.validate()
		self.assertEqual(doc.student, "STUDENT")

	def test_source_document_must_exist(self):
		doc = self.make_exception(
			source_doctype="Dar Quraan Halaqa",
			source_document="MISSING",
		)
		with patch.object(frappe.db, "exists", return_value=None):
			with self.assertRaises(frappe.ValidationError):
				doc.validate()

	def test_assignment_source_relationship_is_validated(self):
		assignment = frappe._dict(
			{
				"student": "STUDENT",
				"student_name": "Student",
				"branch": "BRANCH",
				"teaching_location": "LOCATION",
				"halaqa": "HALAQA",
				"teacher": "TEACHER",
			}
		)
		doc = self.make_exception(
			student_assignment="ASSIGNMENT",
			source_doctype="Dar Quraan Evaluation",
			source_document="EVALUATION",
		)
		with (
			patch.object(frappe.db, "exists", return_value="EXISTS"),
			patch.object(frappe, "get_doc", return_value=assignment),
			patch.object(frappe.db, "get_value", return_value="OTHER-ASSIGNMENT"),
		):
			with self.assertRaises(frappe.ValidationError):
				doc.validate()
