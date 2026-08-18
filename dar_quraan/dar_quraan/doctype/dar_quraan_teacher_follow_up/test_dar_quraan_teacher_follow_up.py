from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanTeacherFollowUp(FrappeTestCase):
	def make_follow_up(self, **kwargs):
		values = {
			"doctype": "Dar Quraan Teacher Follow Up",
			"student_assignment": "DQ-SA-TEST-001",
			"follow_up_date": "2026-08-18",
			"follow_up_type": "Attendance",
			"priority": "Medium",
			"issue_description": "Repeated absence requires intervention.",
			"status": "Open",
		}
		values.update(kwargs)
		return frappe.get_doc(values)

	def make_assignment(self, **kwargs):
		values = {
			"student": "DQ-STUDENT-001",
			"student_name": "Student One",
			"branch": "DQ-BRANCH-001",
			"teaching_location": "DQ-LOCATION-001",
			"halaqa": "DQ-HALAQA-001",
			"teacher": "DQ-TEACHER-001",
			"study_track": "Hifz",
			"riwayah": "Hafs",
		}
		values.update(kwargs)
		return frappe._dict(values)

	def validate_follow_up(self, doc, assignment=None, existing=None, values=None):
		assignment = assignment or self.make_assignment()
		existing = existing or {}
		values = values or {}
		original_get_doc = frappe.get_doc

		def fake_exists(doctype, name=None, *args, **kwargs):
			if doctype == "Dar Quraan Student Assignment":
				return name if name == "DQ-SA-TEST-001" else None
			if doctype == "Dar Quraan Attendance Item":
				return existing.get("attendance_item")
			return name if existing.get(doctype) else None

		def fake_get_doc(*args, **kwargs):
			if len(args) >= 2 and args[0] == "Dar Quraan Student Assignment":
				return assignment
			return original_get_doc(*args, **kwargs)

		def fake_get_value(doctype, name, fieldname, *args, **kwargs):
			return values.get((doctype, name, fieldname))

		with (
			patch.object(frappe.db, "exists", side_effect=fake_exists),
			patch.object(frappe, "get_doc", side_effect=fake_get_doc),
			patch.object(frappe.db, "get_value", side_effect=fake_get_value),
		):
			doc.validate()

	def assert_invalid(self, **kwargs):
		with self.assertRaises(frappe.ValidationError):
			self.validate_follow_up(self.make_follow_up(**kwargs))

	def test_valid_manual_follow_up_and_context_fetch(self):
		doc = self.make_follow_up(student="WRONG", teacher="WRONG")
		self.validate_follow_up(doc)
		self.assertEqual(doc.student, "DQ-STUDENT-001")
		self.assertEqual(doc.student_name, "Student One")
		self.assertEqual(doc.branch, "DQ-BRANCH-001")
		self.assertEqual(doc.teaching_location, "DQ-LOCATION-001")
		self.assertEqual(doc.halaqa, "DQ-HALAQA-001")
		self.assertEqual(doc.teacher, "DQ-TEACHER-001")
		self.assertEqual(doc.study_track, "Hifz")
		self.assertEqual(doc.riwayah, "Hafs")

	def test_student_assignment_is_required(self):
		self.assert_invalid(student_assignment=None)

	def test_invalid_student_assignment_is_rejected(self):
		self.assert_invalid(student_assignment="INVALID")

	def test_assignment_requires_student_teacher_and_halaqa(self):
		for fieldname in ("student", "teacher", "halaqa"):
			with self.subTest(fieldname=fieldname), self.assertRaises(frappe.ValidationError):
				self.validate_follow_up(self.make_follow_up(), self.make_assignment(**{fieldname: None}))

	def test_required_values(self):
		for fieldname in ("follow_up_date", "follow_up_type", "priority", "issue_description"):
			with self.subTest(fieldname=fieldname):
				self.assert_invalid(**{fieldname: None})

	def test_whitespace_issue_description_is_rejected(self):
		self.assert_invalid(issue_description="   ")

	def test_all_follow_up_types_are_valid(self):
		for value in (
			"Attendance",
			"Memorization",
			"Revision",
			"Tajweed",
			"Fluency",
			"Evaluation",
			"Behavior",
			"Parent Contact",
			"General Academic",
			"Other",
		):
			with self.subTest(value=value):
				self.validate_follow_up(self.make_follow_up(follow_up_type=value))

	def test_invalid_select_values(self):
		for fieldname in ("follow_up_type", "priority", "status"):
			with self.subTest(fieldname=fieldname):
				self.assert_invalid(**{fieldname: "Invalid"})

	def test_valid_progress_source(self):
		doc = self.make_follow_up(source_progress="DQ-PROG-001")
		self.validate_follow_up(
			doc,
			existing={"Dar Quraan Student Progress": True},
			values={("Dar Quraan Student Progress", "DQ-PROG-001", "student_assignment"): "DQ-SA-TEST-001"},
		)

	def test_missing_or_mismatched_progress_source_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self.validate_follow_up(self.make_follow_up(source_progress="MISSING"))
		with self.assertRaises(frappe.ValidationError):
			self.validate_follow_up(
				self.make_follow_up(source_progress="DQ-PROG-001"),
				existing={"Dar Quraan Student Progress": True},
				values={("Dar Quraan Student Progress", "DQ-PROG-001", "student_assignment"): "OTHER"},
			)

	def test_valid_and_mismatched_evaluation_source(self):
		values = {("Dar Quraan Evaluation", "DQ-EVAL-001", "student_assignment"): "DQ-SA-TEST-001"}
		self.validate_follow_up(
			self.make_follow_up(source_evaluation="DQ-EVAL-001"),
			existing={"Dar Quraan Evaluation": True},
			values=values,
		)
		values["Dar Quraan Evaluation", "DQ-EVAL-001", "student_assignment"] = "OTHER"
		with self.assertRaises(frappe.ValidationError):
			self.validate_follow_up(
				self.make_follow_up(source_evaluation="DQ-EVAL-001"),
				existing={"Dar Quraan Evaluation": True},
				values=values,
			)

	def test_attendance_must_exist_and_contain_assignment(self):
		doc = self.make_follow_up(source_attendance="DQ-ATT-001")
		with self.assertRaises(frappe.ValidationError):
			self.validate_follow_up(doc)
		with self.assertRaises(frappe.ValidationError):
			self.validate_follow_up(doc, existing={"Dar Quraan Attendance": True})
		self.validate_follow_up(doc, existing={"Dar Quraan Attendance": True, "attendance_item": "ROW-001"})

	def test_follow_up_required_needs_valid_next_date(self):
		self.assert_invalid(follow_up_required=1, next_follow_up_date=None)
		self.assert_invalid(follow_up_required=1, next_follow_up_date="2026-08-17")
		self.validate_follow_up(self.make_follow_up(follow_up_required=1, next_follow_up_date="2026-08-18"))

	def test_resolved_requires_notes_and_no_future_follow_up(self):
		self.assert_invalid(status="Resolved")
		self.assert_invalid(
			status="Resolved", resolution_notes="Done", follow_up_required=1, next_follow_up_date="2026-08-20"
		)
		self.validate_follow_up(
			self.make_follow_up(status="Resolved", resolution_notes="Issue reviewed and resolved.")
		)

	def test_cancelled_cannot_require_future_follow_up(self):
		self.assert_invalid(status="Cancelled", follow_up_required=1, next_follow_up_date="2026-08-20")
