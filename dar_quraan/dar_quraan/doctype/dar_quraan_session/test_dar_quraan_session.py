from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, getdate, nowdate


class TestDarQuraanSession(FrappeTestCase):
	def setUp(self):
		self.term_start = getdate(nowdate())

		self.term_end = getdate(
			add_days(
				self.term_start,
				90,
			)
		)

		self.session_date = getdate(
			add_days(
				self.term_start,
				10,
			)
		)

	def make_halaqa(
		self,
		**kwargs,
	):
		data = {
			"name": "DQH-TEST-00001",
			"halaqa_name": "Test Halaqa",
			"branch": "DQB-TEST",
			"teaching_location": "DQTL-TEST",
			"academic_year": "DQAY-TEST",
			"academic_term": "DQAT-TEST",
			"mentor": "DQT-TEST",
			"status": "Active",
			"start_date": self.term_start,
			"end_date": self.term_end,
			"start_time": "09:00:00",
			"end_time": "11:00:00",
		}

		data.update(kwargs)

		return frappe._dict(data)

	def make_term(
		self,
		**kwargs,
	):
		data = {
			"start_date": self.term_start,
			"end_date": self.term_end,
			"status": "Open",
		}

		data.update(kwargs)

		return frappe._dict(data)

	def make_session(
		self,
		**kwargs,
	):
		data = {
			"doctype": "Dar Quraan Session",
			"halaqa": "DQH-TEST-00001",
			"session_date": self.session_date,
			"session_type": "Regular",
			"status": "Planned",
		}

		data.update(kwargs)

		return frappe.get_doc(data)

	def validate_session(
		self,
		session,
		halaqa=None,
		term=None,
		halaqa_exists=True,
	):
		if halaqa is None:
			halaqa = self.make_halaqa()

		if term is None:
			term = self.make_term()

		original_get_doc = frappe.get_doc

		def fake_get_doc(
			*args,
			**kwargs,
		):
			if len(args) >= 2 and args[0] == "Dar Quraan Halaqa":
				return halaqa

			return original_get_doc(
				*args,
				**kwargs,
			)

		def fake_exists(
			doctype,
			name=None,
			*args,
			**kwargs,
		):
			if doctype == "Dar Quraan Halaqa":
				if halaqa_exists and name == "DQH-TEST-00001":
					return "DQH-TEST-00001"

				return None

			return None

		def fake_get_value(
			doctype,
			name,
			fields,
			*args,
			**kwargs,
		):
			if doctype == "Dar Quraan Academic Term" and name == "DQAT-TEST":
				if kwargs.get("as_dict"):
					return term

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
			session.validate()

	# ---------------------------------------------------------
	# Basic valid session
	# ---------------------------------------------------------

	def test_valid_session(self):
		session = self.make_session()

		self.validate_session(session)

		self.assertEqual(
			session.halaqa,
			"DQH-TEST-00001",
		)

		self.assertEqual(
			session.status,
			"Planned",
		)

		self.assertEqual(
			session.session_type,
			"Regular",
		)

	# ---------------------------------------------------------
	# Halaqa context fetching
	# ---------------------------------------------------------

	def test_context_is_fetched_from_halaqa(self):
		session = self.make_session(
			halaqa_name="Wrong",
			branch="Wrong",
			teaching_location="Wrong",
			academic_year="Wrong",
			academic_term="Wrong",
			teacher="Wrong",
		)

		self.validate_session(session)

		self.assertEqual(
			session.halaqa_name,
			"Test Halaqa",
		)

		self.assertEqual(
			session.branch,
			"DQB-TEST",
		)

		self.assertEqual(
			session.teaching_location,
			"DQTL-TEST",
		)

		self.assertEqual(
			session.academic_year,
			"DQAY-TEST",
		)

		self.assertEqual(
			session.academic_term,
			"DQAT-TEST",
		)

		self.assertEqual(
			session.teacher,
			"DQT-TEST",
		)

	def test_halaqa_is_required(self):
		session = self.make_session(
			halaqa=None,
		)

		with self.assertRaises(frappe.ValidationError):
			session.validate()

	def test_invalid_halaqa_is_rejected(self):
		session = self.make_session()

		with self.assertRaises(frappe.ValidationError):
			self.validate_session(
				session,
				halaqa_exists=False,
			)

	def test_closed_halaqa_is_rejected(self):
		session = self.make_session()

		halaqa = self.make_halaqa(
			status="Closed",
		)

		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Closed Halaqa",
		):
			self.validate_session(
				session,
				halaqa=halaqa,
			)

	def test_halaqa_without_branch_is_rejected(self):
		session = self.make_session()

		halaqa = self.make_halaqa(
			branch=None,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_session(
				session,
				halaqa=halaqa,
			)

	def test_halaqa_without_location_is_rejected(self):
		session = self.make_session()

		halaqa = self.make_halaqa(
			teaching_location=None,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_session(
				session,
				halaqa=halaqa,
			)

	def test_halaqa_without_academic_year_is_rejected(self):
		session = self.make_session()

		halaqa = self.make_halaqa(
			academic_year=None,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_session(
				session,
				halaqa=halaqa,
			)

	def test_halaqa_without_academic_term_is_rejected(self):
		session = self.make_session()

		halaqa = self.make_halaqa(
			academic_term=None,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_session(
				session,
				halaqa=halaqa,
			)

	def test_halaqa_without_mentor_is_rejected(self):
		session = self.make_session()

		halaqa = self.make_halaqa(
			mentor=None,
		)

		with self.assertRaisesRegex(
			frappe.ValidationError,
			"does not have a Mentor",
		):
			self.validate_session(
				session,
				halaqa=halaqa,
			)

	# ---------------------------------------------------------
	# Session date
	# ---------------------------------------------------------

	def test_session_date_is_required(self):
		session = self.make_session(
			session_date=None,
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_session(session)

	def test_session_before_halaqa_start_is_rejected(self):
		session = self.make_session(
			session_date=add_days(
				self.term_start,
				-1,
			)
		)

		with self.assertRaisesRegex(
			frappe.ValidationError,
			"before the Halaqa Start Date",
		):
			self.validate_session(session)

	def test_session_after_halaqa_end_is_rejected(self):
		session = self.make_session(
			session_date=add_days(
				self.term_end,
				1,
			)
		)

		with self.assertRaisesRegex(
			frappe.ValidationError,
			"after the Halaqa End Date",
		):
			self.validate_session(session)

	def test_session_before_term_is_rejected(self):
		session = self.make_session(
			session_date=self.term_start,
		)

		halaqa = self.make_halaqa(
			start_date=add_days(
				self.term_start,
				-10,
			)
		)

		term = self.make_term(
			start_date=add_days(
				self.term_start,
				1,
			)
		)

		with self.assertRaisesRegex(
			frappe.ValidationError,
			"before the Academic Term starts",
		):
			self.validate_session(
				session,
				halaqa=halaqa,
				term=term,
			)

	def test_session_after_term_is_rejected(self):
		session = self.make_session(
			session_date=self.term_end,
		)

		halaqa = self.make_halaqa(
			end_date=add_days(
				self.term_end,
				10,
			)
		)

		term = self.make_term(
			end_date=add_days(
				self.term_end,
				-1,
			)
		)

		with self.assertRaisesRegex(
			frappe.ValidationError,
			"after the Academic Term ends",
		):
			self.validate_session(
				session,
				halaqa=halaqa,
				term=term,
			)

	def test_closed_term_is_rejected(self):
		session = self.make_session()

		term = self.make_term(
			status="Closed",
		)

		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Academic Term must be Open",
		):
			self.validate_session(
				session,
				term=term,
			)

	# ---------------------------------------------------------
	# Timing
	# ---------------------------------------------------------

	def test_session_inherits_halaqa_times(self):
		session = self.make_session(
			start_time=None,
			end_time=None,
		)

		self.validate_session(session)

		self.assertEqual(
			str(session.start_time),
			"09:00:00",
		)

		self.assertEqual(
			str(session.end_time),
			"11:00:00",
		)

	def test_custom_session_times_are_preserved(self):
		session = self.make_session(
			start_time="13:00:00",
			end_time="14:00:00",
		)

		self.validate_session(session)

		self.assertEqual(
			str(session.start_time),
			"13:00:00",
		)

		self.assertEqual(
			str(session.end_time),
			"14:00:00",
		)

	def test_start_time_must_be_before_end_time(self):
		session = self.make_session(
			start_time="12:00:00",
			end_time="10:00:00",
		)

		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Start Time must be before End Time",
		):
			self.validate_session(session)

	def test_equal_times_are_rejected(self):
		session = self.make_session(
			start_time="10:00:00",
			end_time="10:00:00",
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_session(session)

	# ---------------------------------------------------------
	# Session type
	# ---------------------------------------------------------

	def test_all_session_types_are_valid(self):
		session_types = [
			"Regular",
			"Makeup",
			"Extra",
			"Evaluation",
		]

		for session_type in session_types:
			session = self.make_session(
				session_type=session_type,
			)

			self.validate_session(session)

			self.assertEqual(
				session.session_type,
				session_type,
			)

	def test_missing_session_type_defaults_to_regular(self):
		session = self.make_session(
			session_type=None,
		)

		self.validate_session(session)

		self.assertEqual(
			session.session_type,
			"Regular",
		)

	def test_invalid_session_type_is_rejected(self):
		session = self.make_session(
			session_type="Unknown",
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_session(session)

	# ---------------------------------------------------------
	# Status
	# ---------------------------------------------------------

	def test_all_statuses_are_valid(self):
		statuses = [
			"Planned",
			"In Progress",
			"Completed",
			"Cancelled",
		]

		for status in statuses:
			session = self.make_session(
				status=status,
			)

			self.validate_session(session)

			self.assertEqual(
				session.status,
				status,
			)

	def test_missing_status_defaults_to_planned(self):
		session = self.make_session(
			status=None,
		)

		self.validate_session(session)

		self.assertEqual(
			session.status,
			"Planned",
		)

	def test_invalid_status_is_rejected(self):
		session = self.make_session(
			status="Unknown",
		)

		with self.assertRaises(frappe.ValidationError):
			self.validate_session(session)
