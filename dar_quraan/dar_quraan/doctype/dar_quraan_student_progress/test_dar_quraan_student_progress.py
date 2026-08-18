from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanStudentProgress(FrappeTestCase):
	def make_assignment(self, **kwargs):
		data = {
			"name": "DQ-SA-TEST-00001",
			"student": "DQ-STUDENT-TEST-00001",
			"student_name": "Ahmad Test",
			"branch": "DQ-BRANCH-TEST",
			"teaching_location": "DQ-LOCATION-TEST",
			"halaqa": "DQ-HALAQA-TEST",
			"teacher": "DQ-TEACHER-TEST",
			"study_track": "Hifz",
			"riwayah": "Hafs",
		}

		data.update(kwargs)

		assignment = frappe._dict(data)

		assignment.meta = frappe._dict()

		assignment.meta.has_field = lambda fieldname: fieldname in data

		return assignment

	def make_progress(self, **kwargs):
		data = {
			"doctype": "Dar Quraan Student Progress",
			"student_assignment": "DQ-SA-TEST-00001",
			"progress_date": "2026-08-10",
			"status": "Draft",
			"new_memorization": [
				{
					"doctype": "Dar Quraan Quran Range",
					"surah": "2",
					"from_ayah": 20,
					"to_ayah": 35,
					"from_page": 4,
					"to_page": 6,
				}
			],
		}

		data.update(kwargs)

		return frappe.get_doc(data)

	def make_surah(self, **kwargs):
		data = {
			"ayah_count": 286,
			"start_page": 2,
			"end_page": 49,
			"is_active": 1,
		}

		data.update(kwargs)

		return frappe._dict(data)

	def assignment_exists(self, *args, **kwargs):
		return "DQ-SA-TEST-00001"

	def fake_get_value(
		self,
		doctype,
		name,
		fields,
		as_dict=False,
		**kwargs,
	):
		if doctype == "Dar Quraan Surah" and name == "2":
			result = self.make_surah()

			if as_dict:
				return result

			return result

		return None

	def validate_progress(
		self,
		progress,
		assignment=None,
	):
		if assignment is None:
			assignment = self.make_assignment()

		original_get_doc = frappe.get_doc

		def fake_get_doc(*args, **kwargs):
			if len(args) >= 2 and args[0] == "Dar Quraan Student Assignment":
				return assignment

			return original_get_doc(
				*args,
				**kwargs,
			)

		with (
			patch.object(
				frappe.db,
				"exists",
				side_effect=self.assignment_exists,
			),
			patch.object(
				frappe,
				"get_doc",
				side_effect=fake_get_doc,
			),
			patch.object(
				frappe.db,
				"get_value",
				side_effect=self.fake_get_value,
			),
		):
			progress.validate()

	# ---------------------------------------------------------
	# Valid progress
	# ---------------------------------------------------------

	def test_valid_progress(self):
		progress = self.make_progress()

		self.validate_progress(progress)

		self.assertEqual(
			progress.student_assignment,
			"DQ-SA-TEST-00001",
		)

		self.assertEqual(
			progress.student,
			"DQ-STUDENT-TEST-00001",
		)

		self.assertEqual(
			progress.student_name,
			"Ahmad Test",
		)

		self.assertEqual(
			progress.status,
			"Draft",
		)

	# ---------------------------------------------------------
	# Assignment context
	# ---------------------------------------------------------

	def test_student_is_fetched_from_assignment(self):
		progress = self.make_progress(
			student="WRONG-STUDENT",
		)

		self.validate_progress(progress)

		self.assertEqual(
			progress.student,
			"DQ-STUDENT-TEST-00001",
		)

	def test_student_name_is_fetched_from_assignment(self):
		progress = self.make_progress(
			student_name="Wrong Name",
		)

		self.validate_progress(progress)

		self.assertEqual(
			progress.student_name,
			"Ahmad Test",
		)

	def test_branch_is_fetched_from_assignment(self):
		progress = self.make_progress(
			branch="WRONG-BRANCH",
		)

		self.validate_progress(progress)

		self.assertEqual(
			progress.branch,
			"DQ-BRANCH-TEST",
		)

	def test_teaching_location_is_fetched_from_assignment(self):
		progress = self.make_progress(
			teaching_location="WRONG-LOCATION",
		)

		self.validate_progress(progress)

		self.assertEqual(
			progress.teaching_location,
			"DQ-LOCATION-TEST",
		)

	def test_halaqa_is_fetched_from_assignment(self):
		progress = self.make_progress(
			halaqa="WRONG-HALAQA",
		)

		self.validate_progress(progress)

		self.assertEqual(
			progress.halaqa,
			"DQ-HALAQA-TEST",
		)

	def test_teacher_is_fetched_from_assignment(self):
		progress = self.make_progress(
			teacher="WRONG-TEACHER",
		)

		self.validate_progress(progress)

		self.assertEqual(
			progress.teacher,
			"DQ-TEACHER-TEST",
		)

	def test_study_track_is_fetched_from_assignment(self):
		progress = self.make_progress(
			study_track="Wrong Track",
		)

		self.validate_progress(progress)

		self.assertEqual(
			progress.study_track,
			"Hifz",
		)

	def test_riwayah_is_fetched_from_assignment(self):
		progress = self.make_progress(
			riwayah="Wrong Riwayah",
		)

		self.validate_progress(progress)

		self.assertEqual(
			progress.riwayah,
			"Hafs",
		)

	# ---------------------------------------------------------
	# Assignment validation
	# ---------------------------------------------------------

	def test_missing_student_assignment_is_not_allowed(self):
		progress = self.make_progress(
			student_assignment=None,
		)

		with self.assertRaises(frappe.ValidationError):
			progress.validate()

	def test_nonexistent_student_assignment_is_not_allowed(self):
		progress = self.make_progress(
			student_assignment="DQ-SA-NOT-FOUND",
		)

		with patch.object(
			frappe.db,
			"exists",
			return_value=None,
		):
			with self.assertRaises(frappe.ValidationError):
				progress.validate()

	def test_assignment_without_student_is_not_allowed(self):
		progress = self.make_progress()

		assignment = self.make_assignment(
			student=None,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_progress(
				progress,
				assignment,
			)

	def test_assignment_without_teacher_is_not_allowed(self):
		progress = self.make_progress()

		assignment = self.make_assignment(
			teacher=None,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_progress(
				progress,
				assignment,
			)

	def test_assignment_without_halaqa_is_not_allowed(self):
		progress = self.make_progress()

		assignment = self.make_assignment(
			halaqa=None,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_progress(
				progress,
				assignment,
			)

	# ---------------------------------------------------------
	# Date
	# ---------------------------------------------------------

	def test_progress_date_is_required(self):
		progress = self.make_progress(
			progress_date=None,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_progress(progress)

	# ---------------------------------------------------------
	# Quran progress requirements
	# ---------------------------------------------------------

	def test_at_least_one_quran_range_is_required(self):
		progress = self.make_progress(
			new_memorization=[],
			revision=[],
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_progress(progress)

	def test_revision_only_is_valid(self):
		progress = self.make_progress(
			new_memorization=[],
			revision=[
				{
					"doctype": "Dar Quraan Quran Range",
					"surah": "2",
					"from_ayah": 1,
					"to_ayah": 19,
					"from_page": 2,
					"to_page": 3,
				}
			],
		)

		self.validate_progress(progress)

		self.assertEqual(
			len(progress.revision),
			1,
		)

		self.assertEqual(
			progress.revision[0].ayah_count,
			19,
		)

		self.assertEqual(
			progress.revision[0].page_count,
			2,
		)

	def test_memorization_only_is_valid(self):
		progress = self.make_progress(
			revision=[],
		)

		self.validate_progress(progress)

		self.assertEqual(
			len(progress.new_memorization),
			1,
		)

	def test_memorization_and_revision_are_valid_together(self):
		progress = self.make_progress(
			revision=[
				{
					"doctype": "Dar Quraan Quran Range",
					"surah": "2",
					"from_ayah": 1,
					"to_ayah": 19,
					"from_page": 2,
					"to_page": 3,
				}
			],
		)

		self.validate_progress(progress)

		self.assertEqual(
			len(progress.new_memorization),
			1,
		)

		self.assertEqual(
			len(progress.revision),
			1,
		)

	# ---------------------------------------------------------
	# Quran Range validation through parent
	# ---------------------------------------------------------

	def test_invalid_from_ayah_is_rejected(self):
		progress = self.make_progress(
			new_memorization=[
				{
					"doctype": "Dar Quraan Quran Range",
					"surah": "2",
					"from_ayah": 0,
					"to_ayah": 10,
					"from_page": 2,
					"to_page": 3,
				}
			],
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_progress(progress)

	def test_ayah_exceeding_surah_is_rejected(self):
		progress = self.make_progress(
			new_memorization=[
				{
					"doctype": "Dar Quraan Quran Range",
					"surah": "2",
					"from_ayah": 280,
					"to_ayah": 287,
					"from_page": 48,
					"to_page": 49,
				}
			],
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_progress(progress)

	def test_reverse_ayah_range_is_rejected(self):
		progress = self.make_progress(
			new_memorization=[
				{
					"doctype": "Dar Quraan Quran Range",
					"surah": "2",
					"from_ayah": 35,
					"to_ayah": 20,
					"from_page": 4,
					"to_page": 6,
				}
			],
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_progress(progress)

	def test_page_outside_surah_is_rejected(self):
		progress = self.make_progress(
			new_memorization=[
				{
					"doctype": "Dar Quraan Quran Range",
					"surah": "2",
					"from_ayah": 1,
					"to_ayah": 10,
					"from_page": 1,
					"to_page": 2,
				}
			],
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_progress(progress)

	def test_reverse_page_range_is_rejected(self):
		progress = self.make_progress(
			new_memorization=[
				{
					"doctype": "Dar Quraan Quran Range",
					"surah": "2",
					"from_ayah": 20,
					"to_ayah": 35,
					"from_page": 6,
					"to_page": 4,
				}
			],
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_progress(progress)

	def test_child_counts_are_calculated(self):
		progress = self.make_progress()

		self.validate_progress(progress)

		row = progress.new_memorization[0]

		self.assertEqual(
			row.ayah_count,
			16,
		)

		self.assertEqual(
			row.page_count,
			3,
		)

	# ---------------------------------------------------------
	# Status
	# ---------------------------------------------------------

	def test_missing_status_defaults_to_draft(self):
		progress = self.make_progress(
			status=None,
		)

		self.validate_progress(progress)

		self.assertEqual(
			progress.status,
			"Draft",
		)

	def test_completed_status_is_valid(self):
		progress = self.make_progress(
			status="Completed",
		)

		self.validate_progress(progress)

		self.assertEqual(
			progress.status,
			"Completed",
		)

	def test_cancelled_status_is_valid(self):
		progress = self.make_progress(
			status="Cancelled",
		)

		self.validate_progress(progress)

		self.assertEqual(
			progress.status,
			"Cancelled",
		)

	def test_invalid_status_is_rejected(self):
		progress = self.make_progress(
			status="Something Else",
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_progress(progress)

	# ---------------------------------------------------------
	# Progress Item integration
	# ---------------------------------------------------------

	def test_progress_item_inside_memorization_range_is_valid(self):
		progress = self.make_progress(
			progress_items=[
				{
					"doctype": "Dar Quraan Progress Item",
					"progress_type": "New Memorization",
					"surah": "2",
					"from_ayah": 20,
					"to_ayah": 29,
					"from_page": 4,
					"to_page": 5,
					"result": "Very Good",
					"mistakes_count": 2,
					"prompt_count": 1,
					"memorization_quality": 4,
					"tajweed": 4,
					"fluency": 5,
				}
			],
		)

		self.validate_progress(progress)

		self.assertEqual(
			len(progress.progress_items),
			1,
		)

	def test_progress_item_can_equal_full_memorization_range(self):
		progress = self.make_progress(
			progress_items=[
				{
					"doctype": "Dar Quraan Progress Item",
					"progress_type": "New Memorization",
					"surah": "2",
					"from_ayah": 20,
					"to_ayah": 35,
					"from_page": 4,
					"to_page": 6,
					"result": "Excellent",
				}
			],
		)

		self.validate_progress(progress)

		self.assertEqual(
			progress.progress_items[0].result,
			"Excellent",
		)

	def test_progress_item_cannot_exceed_assigned_ayah_range(self):
		progress = self.make_progress(
			progress_items=[
				{
					"doctype": "Dar Quraan Progress Item",
					"progress_type": "New Memorization",
					"surah": "2",
					"from_ayah": 20,
					"to_ayah": 40,
					"from_page": 4,
					"to_page": 6,
					"result": "Good",
				}
			],
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_progress(progress)

	def test_progress_item_cannot_start_before_assigned_ayah(self):
		progress = self.make_progress(
			progress_items=[
				{
					"doctype": "Dar Quraan Progress Item",
					"progress_type": "New Memorization",
					"surah": "2",
					"from_ayah": 19,
					"to_ayah": 30,
					"from_page": 4,
					"to_page": 5,
					"result": "Good",
				}
			],
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_progress(progress)

	def test_progress_item_cannot_exceed_assigned_page_range(self):
		progress = self.make_progress(
			progress_items=[
				{
					"doctype": "Dar Quraan Progress Item",
					"progress_type": "New Memorization",
					"surah": "2",
					"from_ayah": 20,
					"to_ayah": 35,
					"from_page": 4,
					"to_page": 7,
					"result": "Good",
				}
			],
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_progress(progress)

	def test_progress_item_wrong_surah_is_rejected(self):
		progress = self.make_progress(
			progress_items=[
				{
					"doctype": "Dar Quraan Progress Item",
					"progress_type": "New Memorization",
					"surah": "1",
					"from_ayah": 1,
					"to_ayah": 7,
					"from_page": 1,
					"to_page": 1,
					"result": "Good",
				}
			],
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_progress(progress)

	def test_revision_progress_item_requires_revision_range(self):
		progress = self.make_progress(
			revision=[],
			progress_items=[
				{
					"doctype": "Dar Quraan Progress Item",
					"progress_type": "Revision",
					"surah": "2",
					"from_ayah": 1,
					"to_ayah": 10,
					"from_page": 2,
					"to_page": 3,
					"result": "Good",
				}
			],
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_progress(progress)

	def test_revision_progress_item_inside_revision_range_is_valid(self):
		progress = self.make_progress(
			revision=[
				{
					"doctype": "Dar Quraan Quran Range",
					"surah": "2",
					"from_ayah": 1,
					"to_ayah": 19,
					"from_page": 2,
					"to_page": 3,
				}
			],
			progress_items=[
				{
					"doctype": "Dar Quraan Progress Item",
					"progress_type": "Revision",
					"surah": "2",
					"from_ayah": 1,
					"to_ayah": 10,
					"from_page": 2,
					"to_page": 3,
					"result": "Very Good",
				}
			],
		)

		self.validate_progress(progress)

		self.assertEqual(
			progress.progress_items[0].progress_type,
			"Revision",
		)

	def test_multiple_progress_items_can_fit_same_range(self):
		progress = self.make_progress(
			progress_items=[
				{
					"doctype": "Dar Quraan Progress Item",
					"progress_type": "New Memorization",
					"surah": "2",
					"from_ayah": 20,
					"to_ayah": 25,
					"from_page": 4,
					"to_page": 5,
					"result": "Excellent",
				},
				{
					"doctype": "Dar Quraan Progress Item",
					"progress_type": "New Memorization",
					"surah": "2",
					"from_ayah": 26,
					"to_ayah": 35,
					"from_page": 5,
					"to_page": 6,
					"result": "Good",
				},
			],
		)

		self.validate_progress(progress)

		self.assertEqual(
			len(progress.progress_items),
			2,
		)

	def test_progress_items_are_optional_while_record_is_draft(self):
		progress = self.make_progress(
			progress_items=[],
			status="Draft",
		)

		self.validate_progress(progress)

		self.assertEqual(
			len(progress.progress_items),
			0,
		)
