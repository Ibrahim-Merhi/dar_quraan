from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from dar_quraan.dar_quraan.services.quran_state import (
	get_or_create_quran_state,
	update_memorization_from_progress,
	update_revision_from_progress,
	update_state_from_evaluation,
	update_state_from_next_assignment,
	update_state_from_progress,
)


class TestQuranStateService(FrappeTestCase):
	def make_state(self, **kwargs):
		data = {
			"doctype": "Dar Quraan Student Quran State",
			"name": "DQ-SA-TEST-00001",
			"student_assignment": "DQ-SA-TEST-00001",
			"status": "Active",
			"current_surah": None,
			"current_ayah": None,
			"current_page": None,
			"revision_surah": None,
			"revision_from_ayah": None,
			"revision_to_ayah": None,
			"revision_from_page": None,
			"revision_to_page": None,
			"last_progress": None,
			"last_evaluation": None,
			"last_next_assignment": None,
		}

		data.update(kwargs)

		state = frappe.get_doc(data)

		state.save = MagicMock(return_value=state)

		return state

	def make_progress_item(
		self,
		progress_type="New Memorization",
		result="Good",
		**kwargs,
	):
		data = {
			"progress_type": progress_type,
			"result": result,
			"surah": "2",
			"from_ayah": 20,
			"to_ayah": 35,
			"from_page": 4,
			"to_page": 6,
		}

		data.update(kwargs)

		return frappe._dict(data)

	def make_progress(
		self,
		status="Completed",
		progress_items=None,
		**kwargs,
	):
		if progress_items is None:
			progress_items = [self.make_progress_item()]

		data = {
			"doctype": "Dar Quraan Student Progress",
			"name": "DQ-PROG-TEST-00001",
			"student_assignment": "DQ-SA-TEST-00001",
			"status": status,
			"progress_items": progress_items,
		}

		data.update(kwargs)

		return frappe._dict(data)

	def make_evaluation(
		self,
		status="Completed",
		**kwargs,
	):
		data = {
			"doctype": "Dar Quraan Evaluation",
			"name": "DQ-EVAL-TEST-00001",
			"student_assignment": "DQ-SA-TEST-00001",
			"status": status,
		}

		data.update(kwargs)

		return frappe._dict(data)

	def make_next_assignment(
		self,
		status="Assigned",
		**kwargs,
	):
		data = {
			"doctype": "Dar Quraan Next Assignment",
			"name": "DQ-NEXT-TEST-00001",
			"student_assignment": "DQ-SA-TEST-00001",
			"status": status,
		}

		data.update(kwargs)

		return frappe._dict(data)

	# ---------------------------------------------------------
	# get_or_create_quran_state
	# ---------------------------------------------------------

	def test_existing_state_is_returned(self):
		state = self.make_state()

		with (
			patch.object(
				frappe.db,
				"exists",
				return_value=state.name,
			),
			patch.object(
				frappe,
				"get_doc",
				return_value=state,
			),
		):
			result = get_or_create_quran_state("DQ-SA-TEST-00001")

		self.assertEqual(
			result,
			state,
		)

	def test_new_state_is_created_when_missing(self):
		created_state = self.make_state()

		original_get_doc = frappe.get_doc

		def fake_get_doc(*args, **kwargs):
			if (
				len(args) == 1
				and isinstance(args[0], dict)
				and args[0].get("doctype") == "Dar Quraan Student Quran State"
			):
				return created_state

			return original_get_doc(
				*args,
				**kwargs,
			)

		with (
			patch.object(
				frappe.db,
				"exists",
				return_value=None,
			),
			patch.object(
				frappe,
				"get_doc",
				side_effect=fake_get_doc,
			),
		):
			result = get_or_create_quran_state("DQ-SA-TEST-00001")

		self.assertEqual(
			result,
			created_state,
		)

	def test_student_assignment_is_required_for_state(self):
		with self.assertRaises(frappe.ValidationError):
			get_or_create_quran_state(None)

	# ---------------------------------------------------------
	# Memorization update
	# ---------------------------------------------------------

	def test_good_memorization_advances_state(self):
		state = self.make_state()

		progress = self.make_progress(
			progress_items=[
				self.make_progress_item(
					result="Good",
					to_ayah=35,
					to_page=6,
				)
			]
		)

		update_memorization_from_progress(
			state,
			progress,
		)

		self.assertEqual(
			state.current_surah,
			"2",
		)
		self.assertEqual(
			state.current_ayah,
			35,
		)
		self.assertEqual(
			state.current_page,
			6,
		)

	def test_very_good_memorization_advances_state(self):
		state = self.make_state()

		progress = self.make_progress(
			progress_items=[
				self.make_progress_item(
					result="Very Good",
					to_ayah=40,
					to_page=7,
				)
			]
		)

		update_memorization_from_progress(
			state,
			progress,
		)

		self.assertEqual(
			state.current_ayah,
			40,
		)
		self.assertEqual(
			state.current_page,
			7,
		)

	def test_excellent_memorization_advances_state(self):
		state = self.make_state()

		progress = self.make_progress(
			progress_items=[
				self.make_progress_item(
					result="Excellent",
					to_ayah=50,
					to_page=8,
				)
			]
		)

		update_memorization_from_progress(
			state,
			progress,
		)

		self.assertEqual(
			state.current_ayah,
			50,
		)

	def test_repeat_does_not_advance_memorization(self):
		state = self.make_state(
			current_surah="2",
			current_ayah=20,
			current_page=4,
		)

		progress = self.make_progress(
			progress_items=[
				self.make_progress_item(
					result="Repeat",
					to_ayah=35,
					to_page=6,
				)
			]
		)

		update_memorization_from_progress(
			state,
			progress,
		)

		self.assertEqual(
			state.current_surah,
			"2",
		)
		self.assertEqual(
			state.current_ayah,
			20,
		)
		self.assertEqual(
			state.current_page,
			4,
		)

	def test_needs_revision_does_not_advance_memorization(self):
		state = self.make_state(
			current_surah="2",
			current_ayah=20,
			current_page=4,
		)

		progress = self.make_progress(
			progress_items=[
				self.make_progress_item(
					result="Needs Revision",
				)
			]
		)

		update_memorization_from_progress(
			state,
			progress,
		)

		self.assertEqual(
			state.current_ayah,
			20,
		)

	def test_last_successful_memorization_item_is_used(self):
		state = self.make_state()

		progress = self.make_progress(
			progress_items=[
				self.make_progress_item(
					result="Good",
					to_ayah=25,
					to_page=5,
				),
				self.make_progress_item(
					result="Very Good",
					to_ayah=35,
					to_page=6,
				),
			]
		)

		update_memorization_from_progress(
			state,
			progress,
		)

		self.assertEqual(
			state.current_ayah,
			35,
		)
		self.assertEqual(
			state.current_page,
			6,
		)

	# ---------------------------------------------------------
	# Revision update
	# ---------------------------------------------------------

	def test_revision_item_updates_revision_state(self):
		state = self.make_state()

		progress = self.make_progress(
			progress_items=[
				self.make_progress_item(
					progress_type="Revision",
					result="Good",
					from_ayah=1,
					to_ayah=19,
					from_page=2,
					to_page=3,
				)
			]
		)

		update_revision_from_progress(
			state,
			progress,
		)

		self.assertEqual(
			state.revision_surah,
			"2",
		)
		self.assertEqual(
			state.revision_from_ayah,
			1,
		)
		self.assertEqual(
			state.revision_to_ayah,
			19,
		)
		self.assertEqual(
			state.revision_from_page,
			2,
		)
		self.assertEqual(
			state.revision_to_page,
			3,
		)

	def test_repeat_revision_is_still_recorded(self):
		state = self.make_state()

		progress = self.make_progress(
			progress_items=[
				self.make_progress_item(
					progress_type="Revision",
					result="Repeat",
					from_ayah=1,
					to_ayah=10,
					from_page=2,
					to_page=3,
				)
			]
		)

		update_revision_from_progress(
			state,
			progress,
		)

		self.assertEqual(
			state.revision_to_ayah,
			10,
		)

	def test_needs_revision_is_recorded(self):
		state = self.make_state()

		progress = self.make_progress(
			progress_items=[
				self.make_progress_item(
					progress_type="Revision",
					result="Needs Revision",
					from_ayah=1,
					to_ayah=15,
				)
			]
		)

		update_revision_from_progress(
			state,
			progress,
		)

		self.assertEqual(
			state.revision_to_ayah,
			15,
		)

	# ---------------------------------------------------------
	# Student Progress integration
	# ---------------------------------------------------------

	def test_completed_progress_updates_state(self):
		state = self.make_state()

		progress = self.make_progress(
			progress_items=[
				self.make_progress_item(
					result="Good",
				)
			]
		)

		with patch(
			"dar_quraan.dar_quraan.services.quran_state." "get_or_create_quran_state",
			return_value=state,
		):
			result = update_state_from_progress(progress)

		self.assertEqual(
			result,
			state,
		)

		self.assertEqual(
			state.last_progress,
			"DQ-PROG-TEST-00001",
		)

		self.assertEqual(
			state.current_ayah,
			35,
		)

		state.save.assert_called_once_with(ignore_permissions=True)

	def test_draft_progress_does_not_update_state(self):
		progress = self.make_progress(
			status="Draft",
		)

		result = update_state_from_progress(progress)

		self.assertIsNone(result)

	def test_cancelled_progress_does_not_update_state(self):
		progress = self.make_progress(
			status="Cancelled",
		)

		result = update_state_from_progress(progress)

		self.assertIsNone(result)

	def test_progress_requires_student_assignment(self):
		progress = self.make_progress(
			student_assignment=None,
		)

		with self.assertRaises(frappe.ValidationError):
			update_state_from_progress(progress)

	# ---------------------------------------------------------
	# Evaluation integration
	# ---------------------------------------------------------

	def test_completed_evaluation_updates_reference(self):
		state = self.make_state()

		evaluation = self.make_evaluation()

		with patch(
			"dar_quraan.dar_quraan.services.quran_state." "get_or_create_quran_state",
			return_value=state,
		):
			result = update_state_from_evaluation(evaluation)

		self.assertEqual(
			result,
			state,
		)

		self.assertEqual(
			state.last_evaluation,
			"DQ-EVAL-TEST-00001",
		)

		state.save.assert_called_once_with(ignore_permissions=True)

	def test_draft_evaluation_is_ignored(self):
		evaluation = self.make_evaluation(
			status="Draft",
		)

		result = update_state_from_evaluation(evaluation)

		self.assertIsNone(result)

	def test_evaluation_requires_student_assignment(self):
		evaluation = self.make_evaluation(
			student_assignment=None,
		)

		with self.assertRaises(frappe.ValidationError):
			update_state_from_evaluation(evaluation)

	# ---------------------------------------------------------
	# Next Assignment integration
	# ---------------------------------------------------------

	def test_assigned_next_assignment_updates_reference(self):
		state = self.make_state()

		next_assignment = self.make_next_assignment()

		with patch(
			"dar_quraan.dar_quraan.services.quran_state." "get_or_create_quran_state",
			return_value=state,
		):
			result = update_state_from_next_assignment(next_assignment)

		self.assertEqual(
			result,
			state,
		)

		self.assertEqual(
			state.last_next_assignment,
			"DQ-NEXT-TEST-00001",
		)

		state.save.assert_called_once_with(ignore_permissions=True)

	def test_draft_next_assignment_is_ignored(self):
		next_assignment = self.make_next_assignment(
			status="Draft",
		)

		result = update_state_from_next_assignment(next_assignment)

		self.assertIsNone(result)

	def test_ready_next_assignment_is_ignored(self):
		next_assignment = self.make_next_assignment(
			status="Ready",
		)

		result = update_state_from_next_assignment(next_assignment)

		self.assertIsNone(result)

	def test_completed_next_assignment_is_ignored(self):
		next_assignment = self.make_next_assignment(
			status="Completed",
		)

		result = update_state_from_next_assignment(next_assignment)

		self.assertIsNone(result)

	def test_next_assignment_requires_student_assignment(self):
		next_assignment = self.make_next_assignment(
			student_assignment=None,
		)

		with self.assertRaises(frappe.ValidationError):
			update_state_from_next_assignment(next_assignment)
