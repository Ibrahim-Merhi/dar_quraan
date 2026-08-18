import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanTeachingLocation(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()

		cls.branch = frappe.get_doc(
			{
				"doctype": "Dar Quraan Branch",
				"naming_series": "DQB-.#####",
				"branch_code": "TEST-TL-BRANCH",
				"branch_name": "Test Teaching Location Branch",
				"status": "Active",
				"capacity": 500,
			}
		).insert()

	@classmethod
	def tearDownClass(cls):
		frappe.db.delete(
			"Dar Quraan Teaching Location",
			{"branch": cls.branch.name},
		)

		frappe.db.delete(
			"Dar Quraan Branch",
			{"name": cls.branch.name},
		)

		super().tearDownClass()

	def tearDown(self):
		frappe.db.delete(
			"Dar Quraan Teaching Location",
			{"branch": self.branch.name},
		)

	def make_location(self, **values):
		data = {
			"doctype": "Dar Quraan Teaching Location",
			"naming_series": "DQTL-.#####",
			"location_code": "TEST-LOCATION-01",
			"location_name": "Test Teaching Location",
			"location_type": "Mosque",
			"status": "Active",
			"branch": self.branch.name,
			"inside_branch_premises": 0,
			"city": "Beirut",
			"capacity": 50,
			"allow_halaqas": 1,
		}

		data.update(values)

		return frappe.get_doc(data)

	def test_location_code_is_normalized(self):
		location = self.make_location(location_code=" test-location-01 ")
		location.insert()

		self.assertEqual(
			location.location_code,
			"TEST-LOCATION-01",
		)

	def test_invalid_location_code_is_rejected(self):
		location = self.make_location(location_code="TEST LOCATION 01")

		self.assertRaises(
			frappe.ValidationError,
			location.insert,
		)

	def test_duplicate_location_code_is_rejected(self):
		first = self.make_location()
		first.insert()

		second = self.make_location(
			location_code="test-location-01",
			location_name="Another Location",
		)

		self.assertRaises(
			frappe.ValidationError,
			second.insert,
		)

	def test_duplicate_location_name_same_branch(self):
		first = self.make_location()
		first.insert()

		second = self.make_location(
			location_code="TEST-LOCATION-02",
			location_name="Test Teaching Location",
		)

		self.assertRaises(
			frappe.ValidationError,
			second.insert,
		)

	def test_negative_capacity_is_rejected(self):
		location = self.make_location(capacity=-10)

		self.assertRaises(
			frappe.ValidationError,
			location.insert,
		)

	def test_classroom_must_be_inside_branch(self):
		location = self.make_location(
			location_type="Classroom",
			inside_branch_premises=0,
		)

		self.assertRaises(
			frappe.ValidationError,
			location.insert,
		)

	def test_physical_location_requires_city_or_address(self):
		location = self.make_location(
			city="",
			address="",
		)

		self.assertRaises(
			frappe.ValidationError,
			location.insert,
		)

	def test_online_location_without_address(self):
		location = self.make_location(
			location_code="ONLINE-01",
			location_name="Online Room",
			location_type="Online",
			city="",
			address="",
			inside_branch_premises=0,
		)

		location.insert()

		self.assertTrue(location.name.startswith("DQTL-"))

	def test_inactive_location_disables_halaqas(self):
		location = self.make_location(
			status="Inactive",
			allow_halaqas=1,
		)

		location.insert()

		self.assertEqual(
			location.allow_halaqas,
			0,
		)

	def test_inactive_branch_is_rejected(self):
		inactive_branch = frappe.get_doc(
			{
				"doctype": "Dar Quraan Branch",
				"naming_series": "DQB-.#####",
				"branch_code": "TEST-INACTIVE",
				"branch_name": "Inactive Branch",
				"status": "Inactive",
			}
		).insert()

		try:
			location = self.make_location(
				location_code="TEST-LOCATION-99",
				location_name="Inactive Branch Location",
				branch=inactive_branch.name,
			)

			self.assertRaises(
				frappe.ValidationError,
				location.insert,
			)
		finally:
			frappe.delete_doc(
				"Dar Quraan Branch",
				inactive_branch.name,
				force=True,
			)

	def test_naming_series(self):
		location = self.make_location(
			location_code="TEST-LOCATION-10",
			location_name="Naming Series Test",
		)

		location.insert()

		self.assertTrue(location.name.startswith("DQTL-"))
