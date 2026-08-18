import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanAcademicTerm(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()

		cls.academic_year = frappe.get_doc(
			{
				"doctype": "Dar Quraan Academic Year",
				"naming_series": "DQAY-.#####",
				"academic_year_name": "TEST TERM YEAR 2026-2027",
				"start_date": "2026-09-01",
				"end_date": "2027-08-31",
				"status": "Open",
				"allow_new_enrollment": 1,
				"allow_attendance_entry": 1,
				"allow_progress_entry": 1,
			}
		).insert()

	@classmethod
	def tearDownClass(cls):
		frappe.db.delete(
			"Dar Quraan Academic Term",
			{"academic_year": cls.academic_year.name},
		)
		frappe.db.delete(
			"Dar Quraan Academic Year",
			{"name": cls.academic_year.name},
		)

		super().tearDownClass()

	def tearDown(self):
		frappe.db.delete(
			"Dar Quraan Academic Term",
			{"academic_year": self.academic_year.name},
		)

	def make_term(self, **values):
		data = {
			"doctype": "Dar Quraan Academic Term",
			"naming_series": "DQAT-.#####",
			"term_name": "Test First Term",
			"academic_year": self.academic_year.name,
			"start_date": "2026-09-01",
			"end_date": "2026-12-31",
			"status": "Draft",
			"allow_new_enrollment": 1,
			"allow_attendance_entry": 1,
			"allow_progress_entry": 1,
		}

		data.update(values)
		return frappe.get_doc(data)

	def test_term_dates_must_be_valid(self):
		term = self.make_term(
			start_date="2026-12-31",
			end_date="2026-09-01",
		)

		self.assertRaises(frappe.ValidationError, term.insert)

	def test_term_must_be_within_academic_year(self):
		term = self.make_term(
			start_date="2026-08-01",
			end_date="2026-12-31",
		)

		self.assertRaises(frappe.ValidationError, term.insert)

	def test_duplicate_term_name_in_same_year_is_rejected(self):
		first_term = self.make_term()
		first_term.insert()

		duplicate_term = self.make_term()

		self.assertRaises(frappe.ValidationError, duplicate_term.insert)

	def test_only_one_current_term_is_allowed(self):
		first_term = self.make_term(
			term_name="Test First Current Term",
			is_current=1,
		)
		first_term.insert()

		second_term = self.make_term(
			term_name="Test Second Current Term",
			start_date="2027-01-01",
			end_date="2027-04-30",
			is_current=1,
		)

		self.assertRaises(frappe.ValidationError, second_term.insert)

	def test_closed_term_disables_enrollment(self):
		term = self.make_term(
			status="Closed",
			allow_new_enrollment=1,
		)
		term.insert()

		self.assertEqual(term.allow_new_enrollment, 0)

	def test_archived_term_disables_operations(self):
		term = self.make_term(
			status="Archived",
			allow_new_enrollment=1,
			allow_attendance_entry=1,
			allow_progress_entry=1,
		)
		term.insert()

		self.assertEqual(term.allow_new_enrollment, 0)
		self.assertEqual(term.allow_attendance_entry, 0)
		self.assertEqual(term.allow_progress_entry, 0)

	def test_naming_series_generates_term_id(self):
		term = self.make_term()
		term.insert()

		self.assertTrue(term.name.startswith("DQAT-"))
