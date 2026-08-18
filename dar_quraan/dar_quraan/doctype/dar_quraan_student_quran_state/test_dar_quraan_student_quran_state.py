from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanStudentQuranState(FrappeTestCase):
	def make_assignment(
		self,
		**kwargs,
	):
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

	def make_state(
		self,
		**kwargs,
	):
		data = {
			"doctype": ("Dar Quraan Student Quran State"),
			"student_assignment": ("DQ-SA-TEST-00001"),
			"current_surah": "2",
			"current_ayah": 35,
			"current_page": 6,
			"revision_surah": "2",
			"revision_from_ayah": 1,
			"revision_to_ayah": 19,
			"revision_from_page": 2,
			"revision_to_page": 3,
			"status": "Active",
		}

		data.update(kwargs)

		return frappe.get_doc(data)

	def make_surah(
		self,
		surah_number=2,
	):
		if surah_number == 1:
			return frappe._dict(
				{
					"surah_number": 1,
					"ayah_count": 7,
					"start_page": 1,
					"end_page": 1,
					"is_active": 1,
				}
			)

		return frappe._dict(
			{
				"surah_number": 2,
				"ayah_count": 286,
				"start_page": 2,
				"end_page": 49,
				"is_active": 1,
			}
		)

	def validate_state(
		self,
		state,
		assignment=None,
		existing_state=None,
		inactive_surah=False,
	):
		if assignment is None:
			assignment = self.make_assignment()

		original_get_doc = frappe.get_doc

		def fake_get_doc(
			*args,
			**kwargs,
		):
			if len(args) >= 2 and args[0] == "Dar Quraan Student Assignment":
				return assignment

			return original_get_doc(
				*args,
				**kwargs,
			)

		def fake_exists(
			doctype,
			filters=None,
			*args,
			**kwargs,
		):
			if doctype == "Dar Quraan Student Assignment":
				if filters == "DQ-SA-TEST-00001":
					return "DQ-SA-TEST-00001"

				return None

			if doctype == "Dar Quraan Student Quran State":
				return existing_state

			return None

		def fake_get_value(
			doctype,
			name,
			fields,
			*args,
			**kwargs,
		):
			if doctype == "Dar Quraan Surah" and name in {"1", "2"}:
				surah = self.make_surah(int(name))

				if inactive_surah:
					surah.is_active = 0

				if kwargs.get("as_dict"):
					return surah

				return None

			return None

		with (
			patch.object(
				frappe,
				"get_doc",
				side_effect=fake_get_doc,
			),
			patch.object(
				frappe.db,
				"exists",
				side_effect=fake_exists,
			),
			patch.object(
				frappe.db,
				"get_value",
				side_effect=fake_get_value,
			),
		):
			state.validate()

	# ---------------------------------------------------------
	# Valid state
	# ---------------------------------------------------------

	def test_valid_state(self):
		state = self.make_state()

		self.validate_state(state)

		self.assertEqual(
			state.student,
			"DQ-STUDENT-TEST-00001",
		)

		self.assertEqual(
			state.teacher,
			"DQ-TEACHER-TEST",
		)

		self.assertEqual(
			state.status,
			"Active",
		)

	def test_assignment_context_is_fetched(self):
		state = self.make_state(
			student="WRONG",
			student_name="Wrong Name",
			branch="WRONG",
			teaching_location="WRONG",
			halaqa="WRONG",
			teacher="WRONG",
			study_track="WRONG",
			riwayah="WRONG",
		)

		self.validate_state(state)

		self.assertEqual(
			state.student,
			"DQ-STUDENT-TEST-00001",
		)

		self.assertEqual(
			state.student_name,
			"Ahmad Test",
		)

		self.assertEqual(
			state.branch,
			"DQ-BRANCH-TEST",
		)

		self.assertEqual(
			state.teaching_location,
			"DQ-LOCATION-TEST",
		)

		self.assertEqual(
			state.halaqa,
			"DQ-HALAQA-TEST",
		)

		self.assertEqual(
			state.teacher,
			"DQ-TEACHER-TEST",
		)

		self.assertEqual(
			state.study_track,
			"Hifz",
		)

		self.assertEqual(
			state.riwayah,
			"Hafs",
		)

	# ---------------------------------------------------------
	# Student Assignment
	# ---------------------------------------------------------

	def test_student_assignment_is_required(self):
		state = self.make_state(
			student_assignment=None,
		)

		with self.assertRaises(frappe.ValidationError):
			state.validate()

	def test_invalid_student_assignment_is_rejected(
		self,
	):
		state = self.make_state(
			student_assignment="INVALID",
		)

		with patch.object(
			frappe.db,
			"exists",
			return_value=None,
		):
			with self.assertRaises(frappe.ValidationError):
				state.validate()

	def test_assignment_without_student_is_rejected(
		self,
	):
		assignment = self.make_assignment(
			student=None,
		)

		state = self.make_state()

		with self.assertRaises(frappe.ValidationError):
			self.validate_state(
				state,
				assignment=assignment,
			)

	def test_assignment_without_teacher_is_rejected(
		self,
	):
		assignment = self.make_assignment(
			teacher=None,
		)

		state = self.make_state()

		with self.assertRaises(frappe.ValidationError):
			self.validate_state(
				state,
				assignment=assignment,
			)

	def test_assignment_without_halaqa_is_rejected(
		self,
	):
		assignment = self.make_assignment(
			halaqa=None,
		)

		state = self.make_state()

		with self.assertRaises(frappe.ValidationError):
			self.validate_state(
				state,
				assignment=assignment,
			)

	def test_duplicate_state_is_rejected(
		self,
	):
		state = self.make_state()

		with self.assertRaisesRegex(
			frappe.ValidationError,
			"A Quran State already exists",
		):
			self.validate_state(
				state,
				existing_state=("DQ-SA-TEST-00001"),
			)

	# ---------------------------------------------------------
	# Empty / new student state
	# ---------------------------------------------------------

	def test_empty_quran_position_is_valid(
		self,
	):
		state = self.make_state(
			current_surah=None,
			current_ayah=None,
			current_page=None,
			revision_surah=None,
			revision_from_ayah=None,
			revision_to_ayah=None,
			revision_from_page=None,
			revision_to_page=None,
		)

		self.validate_state(state)

		self.assertEqual(
			state.completed_pages,
			0,
		)

		self.assertEqual(
			state.memorization_percentage,
			0,
		)

	# ---------------------------------------------------------
	# Current memorization
	# ---------------------------------------------------------

	def test_current_surah_required_when_position_exists(
		self,
	):
		state = self.make_state(
			current_surah=None,
			current_ayah=10,
			current_page=3,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_state(state)

	def test_current_ayah_must_be_positive(
		self,
	):
		state = self.make_state(
			current_ayah=0,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_state(state)

	def test_current_ayah_cannot_exceed_surah(
		self,
	):
		state = self.make_state(
			current_surah="2",
			current_ayah=287,
			current_page=49,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_state(state)

	def test_current_page_cannot_be_before_surah(
		self,
	):
		state = self.make_state(
			current_surah="2",
			current_ayah=1,
			current_page=1,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_state(state)

	def test_current_page_cannot_exceed_surah(
		self,
	):
		state = self.make_state(
			current_surah="2",
			current_ayah=286,
			current_page=50,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_state(state)

	def test_inactive_current_surah_is_rejected(
		self,
	):
		state = self.make_state()

		with self.assertRaises(frappe.ValidationError):
			self.validate_state(
				state,
				inactive_surah=True,
			)

	# ---------------------------------------------------------
	# Revision
	# ---------------------------------------------------------

	def test_revision_can_be_empty(self):
		state = self.make_state(
			revision_surah=None,
			revision_from_ayah=None,
			revision_to_ayah=None,
			revision_from_page=None,
			revision_to_page=None,
		)

		self.validate_state(state)

	def test_revision_surah_required_when_revision_exists(
		self,
	):
		state = self.make_state(
			revision_surah=None,
			revision_from_ayah=1,
			revision_to_ayah=10,
			revision_from_page=2,
			revision_to_page=3,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_state(state)

	def test_revision_from_ayah_must_be_positive(
		self,
	):
		state = self.make_state(
			revision_from_ayah=0,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_state(state)

	def test_revision_to_ayah_cannot_exceed_surah(
		self,
	):
		state = self.make_state(
			revision_to_ayah=287,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_state(state)

	def test_revision_ayah_order_is_validated(
		self,
	):
		state = self.make_state(
			revision_from_ayah=20,
			revision_to_ayah=10,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_state(state)

	def test_revision_page_cannot_be_before_surah(
		self,
	):
		state = self.make_state(
			revision_from_page=1,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_state(state)

	def test_revision_page_cannot_exceed_surah(
		self,
	):
		state = self.make_state(
			revision_to_page=50,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_state(state)

	def test_revision_page_order_is_validated(
		self,
	):
		state = self.make_state(
			revision_from_page=10,
			revision_to_page=5,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_state(state)

	# ---------------------------------------------------------
	# Progress summary
	# ---------------------------------------------------------

	def test_completed_pages_follow_current_page(
		self,
	):
		state = self.make_state(
			current_page=6,
		)

		self.validate_state(state)

		self.assertEqual(
			state.completed_pages,
			6,
		)

	def test_memorization_percentage_is_calculated(
		self,
	):
		state = self.make_state(
			current_page=604,
			current_surah="2",
			current_ayah=35,
		)

		# For this isolated calculation test, bypass Surah
		# page validation because Al-Baqarah itself ends at 49.
		state.calculate_progress_summary()

		self.assertEqual(
			state.completed_pages,
			604,
		)

		self.assertEqual(
			state.memorization_percentage,
			100.0,
		)

	def test_page_six_percentage(self):
		state = self.make_state(
			current_page=6,
		)

		self.validate_state(state)

		expected = round(
			6 / 604 * 100,
			2,
		)

		self.assertEqual(
			state.memorization_percentage,
			expected,
		)

	def test_last_updated_is_set(self):
		state = self.make_state()

		self.validate_state(state)

		self.assertIsNotNone(state.last_updated)

	# ---------------------------------------------------------
	# Status
	# ---------------------------------------------------------

	def test_missing_status_defaults_to_active(
		self,
	):
		state = self.make_state(
			status=None,
		)

		self.validate_state(state)

		self.assertEqual(
			state.status,
			"Active",
		)

	def test_all_valid_statuses(self):
		statuses = [
			"Active",
			"Paused",
			"Completed",
			"Inactive",
		]

		for status in statuses:
			state = self.make_state(
				status=status,
			)

			self.validate_state(state)

			self.assertEqual(
				state.status,
				status,
			)

	def test_invalid_status_is_rejected(
		self,
	):
		state = self.make_state(
			status="Invalid",
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_state(state)
