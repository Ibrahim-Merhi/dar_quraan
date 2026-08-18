import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanSupervisionItem(FrappeTestCase):
	def make_item(self, **kwargs):
		values = {
			"doctype": "Dar Quraan Supervision Item",
			"review_area": "Attendance",
			"rating": 4,
			"finding": "Attendance was recorded correctly.",
			"status": "Open",
		}
		values.update(kwargs)
		return frappe.get_doc(values)

	def assert_invalid(self, **kwargs):
		with self.assertRaises(frappe.ValidationError):
			self.make_item(**kwargs).validate()

	def test_valid_item(self):
		self.make_item().validate()

	def test_all_review_areas_are_valid(self):
		for area in (
			"Session Management",
			"Attendance",
			"Student Progress",
			"Quran Performance",
			"Teacher Adherence",
			"Learning Environment",
			"Other",
		):
			with self.subTest(area=area):
				self.make_item(review_area=area).validate()

	def test_invalid_review_area(self):
		self.assert_invalid(review_area="Invalid")

	def test_rating_boundaries(self):
		self.make_item(rating=1).validate()
		self.make_item(rating=5).validate()
		self.assert_invalid(rating=0)
		self.assert_invalid(rating=6)

	def test_finding_is_required(self):
		self.assert_invalid(finding="  ")

	def test_invalid_status(self):
		self.assert_invalid(status="Invalid")

	def test_follow_up_requires_action_and_due_date(self):
		self.assert_invalid(requires_follow_up=1)
		self.assert_invalid(requires_follow_up=1, corrective_action="Review records")
		self.make_item(
			requires_follow_up=1, corrective_action="Review records", due_date="2026-08-25"
		).validate()

	def test_resolved_requires_notes_and_cannot_require_follow_up(self):
		self.assert_invalid(status="Resolved")
		self.assert_invalid(
			status="Resolved",
			resolution_notes="Resolved",
			requires_follow_up=1,
			corrective_action="Review",
			due_date="2026-08-25",
		)
		self.make_item(status="Resolved", resolution_notes="Corrective action verified.").validate()
