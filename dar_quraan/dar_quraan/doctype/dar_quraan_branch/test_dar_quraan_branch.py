import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanBranch(FrappeTestCase):
    def tearDown(self):
        frappe.db.delete(
            "Dar Quraan Branch",
            {
                "branch_code": [
                    "in",
                    [
                        "TEST-BEI",
                        "TEST-TRI",
                        "TEST-SID",
                        "TEST-NAME-1",
                        "TEST-NAME-2",
                    ],
                ]
            },
        )

    def make_branch(self, **values):
        branch_data = {
            "doctype": "Dar Quraan Branch",
            "naming_series": "DQB-.#####",
            "branch_code": "TEST-BEI",
            "branch_name": "Test Beirut Branch",
            "status": "Active",
            "capacity": 100,
        }

        branch_data.update(values)

        return frappe.get_doc(branch_data)

    def test_branch_code_is_converted_to_uppercase(self):
        branch = self.make_branch(branch_code=" test-bei ")
        branch.insert()

        self.assertEqual(branch.branch_code, "TEST-BEI")

    def test_negative_capacity_is_rejected(self):
        branch = self.make_branch(capacity=-1)

        self.assertRaises(frappe.ValidationError, branch.insert)

    def test_closing_date_before_opening_date_is_rejected(self):
        branch = self.make_branch(
            opening_date="2026-07-26",
            closing_date="2026-07-25",
        )

        self.assertRaises(frappe.ValidationError, branch.insert)

    def test_duplicate_branch_code_is_rejected(self):
        first_branch = self.make_branch(
            branch_code="TEST-TRI",
            branch_name="Test Tripoli Branch",
        )
        first_branch.insert()

        duplicate_branch = self.make_branch(
            branch_code="test-tri",
            branch_name="Another Tripoli Branch",
        )

        self.assertRaises(frappe.ValidationError, duplicate_branch.insert)

    def test_duplicate_branch_name_is_rejected(self):
        first_branch = self.make_branch(
            branch_code="TEST-NAME-1",
            branch_name="Test Shared Branch Name",
        )
        first_branch.insert()

        duplicate_branch = self.make_branch(
            branch_code="TEST-NAME-2",
            branch_name="Test Shared Branch Name",
        )

        self.assertRaises(frappe.ValidationError, duplicate_branch.insert)

    def test_naming_series_generates_branch_id(self):
        branch = self.make_branch(
            branch_code="TEST-SID",
            branch_name="Test Sidon Branch",
        )
        branch.insert()

        self.assertTrue(branch.name.startswith("DQB-"))