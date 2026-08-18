import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanAcademicYear(FrappeTestCase):
	def tearDown(self):
		frappe.db.delete(
			"Dar Quraan Academic Year",
			{
				"academic_year_name": [
					"in",
					[
						"TEST 2025-2026",
						"TEST 2026-2027",
						"TEST 2027-2028",
					],
				]
			},
		)

	def make_academic_year(self, **values):
		data = {
			"doctype": "Dar Quraan Academic Year",
			"naming_series": "DQAY-.#####",
			"academic_year_name": "TEST 2026-2027",
			"start_date": "2026-09-01",
			"end_date": "2027-08-31",
			"status": "Draft",
			"allow_new_enrollment": 1,
			"allow_attendance_entry": 1,
			"allow_progress_entry": 1,
		}

		data.update(values)
		return frappe.get_doc(data)

	def test_end_date_must_be_after_start_date(self):
		academic_year = self.make_academic_year(
			start_date="2026-09-01",
			end_date="2026-08-31",
		)

		self.assertRaises(
			frappe.ValidationError,
			academic_year.insert,
		)

	def test_duplicate_academic_year_name_is_rejected(self):
		first_year = self.make_academic_year()
		first_year.insert()

		duplicate_year = self.make_academic_year(
			start_date="2026-10-01",
			end_date="2027-09-30",
		)

		self.assertRaises(
			frappe.ValidationError,
			duplicate_year.insert,
		)

	def test_only_one_current_year_is_allowed(self):
		first_year = self.make_academic_year(
			academic_year_name="TEST 2025-2026",
			start_date="2025-09-01",
			end_date="2026-08-31",
			is_current=1,
		)
		first_year.insert()

		second_year = self.make_academic_year(
			academic_year_name="TEST 2027-2028",
			start_date="2027-09-01",
			end_date="2028-08-31",
			is_current=1,
		)

		self.assertRaises(
			frappe.ValidationError,
			second_year.insert,
		)

	def test_closed_year_disables_enrollment(self):
		academic_year = self.make_academic_year(
			status="Closed",
			allow_new_enrollment=1,
		)
		academic_year.insert()

		self.assertEqual(academic_year.allow_new_enrollment, 0)

	def test_archived_year_disables_operations(self):
		academic_year = self.make_academic_year(
			status="Archived",
			is_current=0,
			allow_new_enrollment=1,
			allow_attendance_entry=1,
			allow_progress_entry=1,
		)
		academic_year.insert()

		self.assertEqual(academic_year.allow_new_enrollment, 0)
		self.assertEqual(academic_year.allow_attendance_entry, 0)
		self.assertEqual(academic_year.allow_progress_entry, 0)
