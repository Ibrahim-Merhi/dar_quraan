from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanExam(FrappeTestCase):
	def make_exam(self, exam_type="Final 30 Juz", **values):
		mem_count, tajweed_count = (5, 2) if exam_type == "Final 30 Juz" else (3, 2)
		data = {
			"doctype": "Dar Quraan Exam",
			"student_assignment": "DQ-SA-TEST",
			"exam_type": exam_type,
			"status": "Completed",
			"passing_score": 80,
			"completed_juz_at_exam": 30,
			"committee": [
				{"member": "chair@example.com", "role": "Chair"},
				{"member": "examiner@example.com", "role": "Examiner"},
				{"member": "observer@example.com", "role": "Observer"},
			],
			"questions": [],
		}
		for index in range(mem_count):
			data["questions"].append(
				{
					"category": "Memorization and Performance",
					"question_text": f"M{index}",
					"max_score": 90 / mem_count,
				}
			)
		for index in range(tajweed_count):
			data["questions"].append(
				{"category": "Tajweed Theory", "question_text": f"T{index}", "max_score": 10 / tajweed_count}
			)
		data.update(values)
		return frappe.get_doc(data)

	def assignment(self):
		return frappe._dict(student="STUDENT", student_name="Student", teacher="TEACHER", riwayah="Hafs")

	def test_final_exam_uses_90_10_and_passes_at_80(self):
		doc = self.make_exam()
		with patch.object(frappe.db, "get_value", return_value=self.assignment()):
			doc.validate()
		self.assertEqual(doc.final_score, 100)
		self.assertEqual(doc.result, "Passed")

	def test_final_30_requires_five_memorization_questions(self):
		doc = self.make_exam()
		doc.remove(doc.questions[0])
		with (
			patch.object(frappe.db, "get_value", return_value=self.assignment()),
			self.assertRaises(frappe.ValidationError),
		):
			doc.validate()

	def test_committee_requires_three_unique_members(self):
		doc = self.make_exam()
		doc.committee = doc.committee[:2]
		with (
			patch.object(frappe.db, "get_value", return_value=self.assignment()),
			self.assertRaises(frappe.ValidationError),
		):
			doc.validate()
