import frappe
from frappe.tests.utils import FrappeTestCase

from dar_quraan.dar_quraan.doctype.dar_quraan_evaluation_item.dar_quraan_evaluation_item import (
	DarQuraanEvaluationItem,
)


class TestDarQuraanEvaluationItem(FrappeTestCase):
	def make_surah(self):
		return frappe._dict(
			{
				"name": "2",
				"surah_number": 2,
				"ayah_count": 286,
				"from_page": 2,
				"to_page": 49,
			}
		)

	def make_item(self, **kwargs):
		values = {
			"doctype": "Dar Quraan Evaluation Item",
			"surah": "2",
			"from_ayah": 1,
			"to_ayah": 10,
			"from_page": 2,
			"to_page": 3,
			"memorization_quality": 4,
			"tajweed": 4,
			"fluency": 4,
			"mistakes_count": 0,
			"prompt_count": 0,
			"result": "Very Good",
		}

		values.update(kwargs)

		item = DarQuraanEvaluationItem(values)

		return item

	def validate_item(self, item):
		original_exists = frappe.db.exists
		original_get_doc = frappe.get_doc

		def fake_exists(doctype, name=None, *args, **kwargs):
			if doctype == "Dar Quraan Surah" and name == "2":
				return "2"

			return original_exists(doctype, name, *args, **kwargs)

		def fake_get_doc(doctype, name=None, *args, **kwargs):
			if doctype == "Dar Quraan Surah" and name == "2":
				return self.make_surah()

			return original_get_doc(doctype, name, *args, **kwargs)

		frappe.db.exists = fake_exists
		frappe.get_doc = fake_get_doc

		try:
			item.validate()
		finally:
			frappe.db.exists = original_exists
			frappe.get_doc = original_get_doc

	def test_valid_evaluation_item(self):
		item = self.make_item()

		self.validate_item(item)

	def test_surah_is_required(self):
		item = self.make_item(surah=None)

		with self.assertRaises(frappe.ValidationError):
			self.validate_item(item)

	def test_invalid_surah_is_rejected(self):
		item = self.make_item(surah="999")

		with self.assertRaises(frappe.ValidationError):
			self.validate_item(item)

	def test_from_ayah_must_be_positive(self):
		item = self.make_item(from_ayah=0)

		with self.assertRaises(frappe.ValidationError):
			self.validate_item(item)

	def test_to_ayah_must_be_positive(self):
		item = self.make_item(to_ayah=0)

		with self.assertRaises(frappe.ValidationError):
			self.validate_item(item)

	def test_from_ayah_cannot_exceed_to_ayah(self):
		item = self.make_item(
			from_ayah=20,
			to_ayah=10,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_item(item)

	def test_ayah_cannot_exceed_surah(self):
		item = self.make_item(
			from_ayah=280,
			to_ayah=287,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_item(item)

	def test_page_must_be_positive(self):
		item = self.make_item(from_page=0)

		with self.assertRaises(frappe.ValidationError):
			self.validate_item(item)

	def test_from_page_cannot_exceed_to_page(self):
		item = self.make_item(
			from_page=10,
			to_page=5,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_item(item)

	def test_page_cannot_be_before_surah(self):
		item = self.make_item(
			from_page=1,
			to_page=3,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_item(item)

	def test_page_cannot_exceed_surah(self):
		item = self.make_item(
			from_page=48,
			to_page=50,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_item(item)

	def test_scores_accept_one(self):
		item = self.make_item(
			memorization_quality=1,
			tajweed=1,
			fluency=1,
		)

		self.validate_item(item)

	def test_scores_accept_five(self):
		item = self.make_item(
			memorization_quality=5,
			tajweed=5,
			fluency=5,
		)

		self.validate_item(item)

	def test_score_below_one_is_rejected(self):
		item = self.make_item(tajweed=0)

		with self.assertRaises(frappe.ValidationError):
			self.validate_item(item)

	def test_score_above_five_is_rejected(self):
		item = self.make_item(fluency=6)

		with self.assertRaises(frappe.ValidationError):
			self.validate_item(item)

	def test_negative_mistakes_rejected(self):
		item = self.make_item(mistakes_count=-1)

		with self.assertRaises(frappe.ValidationError):
			self.validate_item(item)

	def test_negative_prompts_rejected(self):
		item = self.make_item(prompt_count=-1)

		with self.assertRaises(frappe.ValidationError):
			self.validate_item(item)

	def test_invalid_result_rejected(self):
		item = self.make_item(result="Bad")

		with self.assertRaises(frappe.ValidationError):
			self.validate_item(item)

	def test_score_calculation(self):
		item = self.make_item(
			memorization_quality=4,
			tajweed=5,
			fluency=4,
		)

		self.assertEqual(
			item.get_score(),
			86.0,
		)

	def test_perfect_score_is_100(self):
		item = self.make_item(
			memorization_quality=5,
			tajweed=5,
			fluency=5,
		)

		self.assertEqual(
			item.get_score(),
			100.0,
		)
