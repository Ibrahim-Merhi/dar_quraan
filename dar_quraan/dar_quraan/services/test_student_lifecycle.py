from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestStudentLifecycle(FrappeTestCase):
	def test_program_requires_thirty_weekly_minutes(self):
		doc = frappe.get_doc(
			{
				"doctype": "Dar Quraan Program",
				"program_name": "Test",
				"study_track": "Hifz",
				"admission_goal": "Hifz",
				"weekly_minutes": 29,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.validate()

	def test_text_completion_requires_memorization_explanation_and_pass(self):
		doc = frappe.get_doc(
			{
				"doctype": "Dar Quraan Text Progress",
				"student_assignment": "A",
				"text_name": "Al-Jazariyyah Introduction",
				"memorization_percentage": 90,
				"explanation_status": "Completed",
				"teacher_assessment": "Passed",
				"status": "Completed",
			}
		)
		assignment = frappe._dict(student="S", teacher="T")
		with (
			patch.object(frappe.db, "get_value", return_value=assignment),
			self.assertRaises(frappe.ValidationError),
		):
			doc.validate()

	def test_ijazah_rejects_failed_exam(self):
		doc = frappe.get_doc(
			{
				"doctype": "Dar Quraan Ijazah",
				"student_assignment": "A",
				"exam": "E",
				"riwayah": "Hafs",
				"qiraat_method": "Ifraad",
				"granting_sheikh": "T",
				"committee_chair": "chair@example.com",
				"sanad_text": "Connected sanad",
			}
		)
		exam = frappe._dict(
			student_assignment="A",
			student="S",
			student_name="Student",
			exam_type="Final 30 Juz",
			final_score=79,
			result="Failed",
			status="Completed",
			riwayah="Hafs",
		)
		with (
			patch.object(frappe.db, "get_value", return_value=exam),
			self.assertRaises(frappe.ValidationError),
		):
			doc.validate()

	def test_discipline_resolution_requires_guardian_notification(self):
		doc = frappe.get_doc(
			{
				"doctype": "Dar Quraan Discipline Incident",
				"student_assignment": "A",
				"rule": "R",
				"description": "Incident",
				"action_taken": "Guardian Meeting",
				"status": "Resolved",
				"resolution_notes": "Resolved",
			}
		)
		assignment = frappe._dict(student="S", student_name="Student")
		rule = frappe._dict(
			severity="High", default_action="Guardian Meeting", requires_guardian_notification=1, active=1
		)
		with (
			patch.object(frappe.db, "get_value", side_effect=[assignment, rule]),
			self.assertRaises(frappe.ValidationError),
		):
			doc.validate()
