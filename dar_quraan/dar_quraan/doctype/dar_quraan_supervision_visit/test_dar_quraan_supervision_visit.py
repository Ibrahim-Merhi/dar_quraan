from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanSupervisionVisit(FrappeTestCase):
	def make_halaqa(self, **kwargs):
		values = {
			"halaqa_name": "Test Halaqa",
			"branch": "DQ-BRANCH-001",
			"teaching_location": "DQ-LOCATION-001",
			"mentor": "DQ-TEACHER-001",
			"academic_year": "DQ-YEAR-001",
			"academic_term": "DQ-TERM-001",
		}
		values.update(kwargs)
		return frappe._dict(values)

	def make_item(self, **kwargs):
		values = {
			"doctype": "Dar Quraan Supervision Item",
			"review_area": "Attendance",
			"rating": 4,
			"finding": "Records reviewed.",
			"status": "Open",
		}
		values.update(kwargs)
		return frappe.get_doc(values)

	def make_visit(self, **kwargs):
		values = {
			"doctype": "Dar Quraan Supervision Visit",
			"halaqa": "DQ-HALAQA-001",
			"visit_date": "2026-08-18",
			"visit_type": "Scheduled",
			"supervisor": "supervisor@example.com",
			"status": "Draft",
			"supervision_items": [self.make_item()],
		}
		values.update(kwargs)
		return frappe.get_doc(values)

	def validate_visit(self, doc, halaqa=None, existing=None, session_halaqa="DQ-HALAQA-001"):
		halaqa = halaqa or self.make_halaqa()
		existing = existing or {}
		original_get_doc = frappe.get_doc

		def fake_exists(doctype, name=None, *args, **kwargs):
			if doctype == "Dar Quraan Halaqa":
				return name if name == "DQ-HALAQA-001" else None
			if doctype == "User":
				return name if name == "supervisor@example.com" else None
			if doctype == "Dar Quraan Session":
				return name if existing.get("session") else None
			return None

		def fake_get_doc(*args, **kwargs):
			if len(args) >= 2 and args[0] == "Dar Quraan Halaqa":
				return halaqa
			return original_get_doc(*args, **kwargs)

		def fake_get_value(doctype, name, fieldname, *args, **kwargs):
			if doctype == "Dar Quraan Session" and fieldname == "halaqa":
				return session_halaqa
			return None

		with (
			patch.object(frappe.db, "exists", side_effect=fake_exists),
			patch.object(frappe, "get_doc", side_effect=fake_get_doc),
			patch.object(frappe.db, "get_value", side_effect=fake_get_value),
		):
			doc.validate()

	def assert_invalid(self, **kwargs):
		with self.assertRaises(frappe.ValidationError):
			self.validate_visit(self.make_visit(**kwargs))

	def test_valid_visit_fetches_context_and_summary(self):
		doc = self.make_visit(
			halaqa_name="Wrong",
			branch="Wrong",
			supervision_items=[
				self.make_item(rating=3),
				self.make_item(
					rating=5, requires_follow_up=1, corrective_action="Improve", due_date="2026-08-20"
				),
			],
		)
		self.validate_visit(doc)
		self.assertEqual(doc.halaqa_name, "Test Halaqa")
		self.assertEqual(doc.branch, "DQ-BRANCH-001")
		self.assertEqual(doc.teacher, "DQ-TEACHER-001")
		self.assertEqual(doc.overall_rating, 4.0)
		self.assertEqual(doc.follow_up_item_count, 1)

	def test_halaqa_and_supervisor_are_required_and_must_exist(self):
		self.assert_invalid(halaqa=None)
		self.assert_invalid(halaqa="INVALID")
		self.assert_invalid(supervisor=None)
		self.assert_invalid(supervisor="unknown@example.com")

	def test_halaqa_requires_operational_context(self):
		for fieldname in ("branch", "teaching_location", "mentor"):
			with self.subTest(fieldname=fieldname), self.assertRaises(frappe.ValidationError):
				self.validate_visit(self.make_visit(), self.make_halaqa(**{fieldname: None}))

	def test_visit_date_is_required(self):
		self.assert_invalid(visit_date=None)

	def test_all_visit_types_are_valid(self):
		for visit_type in ("Scheduled", "Unannounced", "Remote", "Follow-up"):
			with self.subTest(visit_type=visit_type):
				self.validate_visit(self.make_visit(visit_type=visit_type))

	def test_invalid_select_values(self):
		self.assert_invalid(visit_type="Invalid")
		self.assert_invalid(status="Invalid")

	def test_source_session_must_exist_and_match_halaqa(self):
		doc = self.make_visit(source_session="DQ-SESSION-001")
		with self.assertRaises(frappe.ValidationError):
			self.validate_visit(doc)
		with self.assertRaises(frappe.ValidationError):
			self.validate_visit(doc, existing={"session": True}, session_halaqa="OTHER")
		self.validate_visit(doc, existing={"session": True})

	def test_at_least_one_item_is_required(self):
		self.assert_invalid(supervision_items=[])

	def test_child_validation_is_enforced(self):
		self.assert_invalid(supervision_items=[self.make_item(rating=0)])

	def test_item_due_date_cannot_precede_visit(self):
		self.assert_invalid(
			supervision_items=[
				self.make_item(requires_follow_up=1, corrective_action="Improve", due_date="2026-08-17")
			]
		)

	def test_completed_visit_requires_summary(self):
		self.assert_invalid(status="Completed")
		self.validate_visit(
			self.make_visit(status="Completed", supervisor_summary="Visit reviewed and completed.")
		)
