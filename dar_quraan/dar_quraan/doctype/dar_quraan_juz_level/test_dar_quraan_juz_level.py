import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanJuzLevel(FrappeTestCase):
    def tearDown(self):
        frappe.db.delete(
            "Dar Quraan Juz Level",
            {
                "level_name": [
                    "like",
                    "Test%",
                ]
            },
        )

    def make_level(self, **values):
        data = {
            "doctype": "Dar Quraan Juz Level",
            "naming_series": "DQJL-.#####",
            "level_name": "Test 1–5 Juz",
            "arabic_name": "اختبار ١–٥ أجزاء",
            "juz_count": 5,
            "minimum_juz": 1,
            "maximum_juz": 5,
            "display_order": 1,
            "status": "Active",
            "disabled": 0,
        }

        data.update(values)
        return frappe.get_doc(data)

    def test_level_name_is_trimmed(self):
        level = self.make_level(
            level_name="  Test 1–5 Juz  ",
        )
        level.insert()

        self.assertEqual(level.level_name, "Test 1–5 Juz")

    def test_juz_count_cannot_exceed_thirty(self):
        level = self.make_level(
            juz_count=31,
            minimum_juz=26,
            maximum_juz=30,
        )

        self.assertRaises(
            frappe.ValidationError,
            level.insert,
        )

    def test_juz_values_cannot_be_negative(self):
        level = self.make_level(
            juz_count=-1,
            minimum_juz=-1,
            maximum_juz=0,
        )

        self.assertRaises(
            frappe.ValidationError,
            level.insert,
        )

    def test_minimum_cannot_exceed_maximum(self):
        level = self.make_level(
            minimum_juz=10,
            maximum_juz=5,
            juz_count=7,
        )

        self.assertRaises(
            frappe.ValidationError,
            level.insert,
        )

    def test_juz_count_must_be_within_range(self):
        level = self.make_level(
            minimum_juz=1,
            maximum_juz=5,
            juz_count=6,
        )

        self.assertRaises(
            frappe.ValidationError,
            level.insert,
        )

    def test_duplicate_level_name_is_rejected(self):
        first_level = self.make_level()
        first_level.insert()

        duplicate_level = self.make_level(
            display_order=2,
        )

        self.assertRaises(
            frappe.ValidationError,
            duplicate_level.insert,
        )

    def test_duplicate_display_order_is_rejected(self):
        first_level = self.make_level()
        first_level.insert()

        second_level = self.make_level(
            level_name="Test 6–10 Juz",
            minimum_juz=6,
            maximum_juz=10,
            juz_count=10,
            display_order=1,
        )

        self.assertRaises(
            frappe.ValidationError,
            second_level.insert,
        )

    def test_overlapping_range_is_rejected(self):
        first_level = self.make_level()
        first_level.insert()

        overlapping_level = self.make_level(
            level_name="Test 4–8 Juz",
            minimum_juz=4,
            maximum_juz=8,
            juz_count=8,
            display_order=2,
        )

        self.assertRaises(
            frappe.ValidationError,
            overlapping_level.insert,
        )

    def test_adjacent_range_is_allowed(self):
        first_level = self.make_level()
        first_level.insert()

        second_level = self.make_level(
            level_name="Test 6–10 Juz",
            minimum_juz=6,
            maximum_juz=10,
            juz_count=10,
            display_order=2,
        )
        second_level.insert()

        self.assertTrue(second_level.name.startswith("DQJL-"))

    def test_disabled_level_becomes_inactive(self):
        level = self.make_level(
            disabled=1,
            status="Active",
        )
        level.insert()

        self.assertEqual(level.status, "Inactive")

    def test_display_order_must_be_positive(self):
        level = self.make_level(
            display_order=0,
        )

        self.assertRaises(
            frappe.ValidationError,
            level.insert,
        )

    def test_naming_series(self):
        level = self.make_level()
        level.insert()

        self.assertTrue(level.name.startswith("DQJL-"))