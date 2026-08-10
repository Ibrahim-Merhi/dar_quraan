import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanProgressItem(FrappeTestCase):
    def setUp(self):
        frappe.db.delete(
            "Dar Quraan Surah",
            {
                "surah_number": [
                    "in",
                    [1, 2],
                ]
            },
        )

        self.create_test_surahs()

    def tearDown(self):
        frappe.db.rollback()

    def create_test_surahs(self):
        frappe.get_doc(
            {
                "doctype": "Dar Quraan Surah",
                "surah_number": 1,
                "arabic_name": "الفاتحة",
                "english_name": "The Opening",
                "transliterated_name": "Al-Fatihah",
                "ayah_count": 7,
                "start_page": 1,
                "end_page": 1,
                "start_juz": 1,
                "end_juz": 1,
                "revelation_place": "Makkah",
                "is_active": 1,
            }
        ).insert()

        frappe.get_doc(
            {
                "doctype": "Dar Quraan Surah",
                "surah_number": 2,
                "arabic_name": "البقرة",
                "english_name": "The Cow",
                "transliterated_name": "Al-Baqarah",
                "ayah_count": 286,
                "start_page": 2,
                "end_page": 49,
                "start_juz": 1,
                "end_juz": 3,
                "revelation_place": "Madinah",
                "is_active": 1,
            }
        ).insert()

    def make_item(self, **kwargs):
        data = {
            "doctype": "Dar Quraan Progress Item",
            "progress_type": "New Memorization",
            "surah": "2",
            "from_ayah": 20,
            "to_ayah": 35,
            "from_page": 4,
            "to_page": 6,
            "result": "Very Good",
            "mistakes_count": 2,
            "prompt_count": 1,
            "memorization_quality": 4,
            "tajweed": 4,
            "fluency": 5,
            "notes": "Good progress",
        }

        data.update(kwargs)

        return frappe.get_doc(data)

    # ---------------------------------------------------------
    # Valid records
    # ---------------------------------------------------------

    def test_valid_new_memorization_item(self):
        item = self.make_item()

        item.validate()

        self.assertEqual(
            item.progress_type,
            "New Memorization",
        )

        self.assertEqual(
            item.result,
            "Very Good",
        )

        self.assertEqual(
            item.mistakes_count,
            2,
        )

    def test_valid_revision_item(self):
        item = self.make_item(
            progress_type="Revision",
            result="Good",
        )

        item.validate()

        self.assertEqual(
            item.progress_type,
            "Revision",
        )

        self.assertEqual(
            item.result,
            "Good",
        )

    def test_complete_fatihah_is_valid(self):
        item = self.make_item(
            surah="1",
            from_ayah=1,
            to_ayah=7,
            from_page=1,
            to_page=1,
        )

        item.validate()

        self.assertEqual(
            item.from_ayah,
            1,
        )

        self.assertEqual(
            item.to_ayah,
            7,
        )

    def test_single_ayah_is_valid(self):
        item = self.make_item(
            from_ayah=20,
            to_ayah=20,
            from_page=4,
            to_page=4,
        )

        item.validate()

        self.assertEqual(
            item.from_ayah,
            item.to_ayah,
        )

    # ---------------------------------------------------------
    # Progress type
    # ---------------------------------------------------------

    def test_missing_progress_type_is_not_allowed(self):
        item = self.make_item(
            progress_type=None,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_invalid_progress_type_is_not_allowed(self):
        item = self.make_item(
            progress_type="Something Else",
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    # ---------------------------------------------------------
    # Surah
    # ---------------------------------------------------------

    def test_missing_surah_is_not_allowed(self):
        item = self.make_item(
            surah=None,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_invalid_surah_is_not_allowed(self):
        item = self.make_item(
            surah="999",
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_inactive_surah_is_not_allowed(self):
        frappe.db.set_value(
            "Dar Quraan Surah",
            "2",
            "is_active",
            0,
        )

        item = self.make_item()

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    # ---------------------------------------------------------
    # Ayah range
    # ---------------------------------------------------------

    def test_from_ayah_cannot_be_zero(self):
        item = self.make_item(
            from_ayah=0,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_from_ayah_cannot_be_negative(self):
        item = self.make_item(
            from_ayah=-1,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_to_ayah_cannot_be_zero(self):
        item = self.make_item(
            to_ayah=0,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_to_ayah_cannot_be_negative(self):
        item = self.make_item(
            to_ayah=-1,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_from_ayah_cannot_exceed_surah_limit(self):
        item = self.make_item(
            surah="1",
            from_ayah=8,
            to_ayah=8,
            from_page=1,
            to_page=1,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_to_ayah_cannot_exceed_surah_limit(self):
        item = self.make_item(
            surah="1",
            from_ayah=1,
            to_ayah=8,
            from_page=1,
            to_page=1,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_to_ayah_cannot_be_before_from_ayah(self):
        item = self.make_item(
            from_ayah=35,
            to_ayah=20,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_last_ayah_of_baqarah_is_valid(self):
        item = self.make_item(
            surah="2",
            from_ayah=286,
            to_ayah=286,
            from_page=49,
            to_page=49,
        )

        item.validate()

        self.assertEqual(
            item.to_ayah,
            286,
        )

    # ---------------------------------------------------------
    # Page range
    # ---------------------------------------------------------

    def test_from_page_cannot_be_before_surah_start(self):
        item = self.make_item(
            surah="2",
            from_page=1,
            to_page=2,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_from_page_cannot_exceed_surah_end(self):
        item = self.make_item(
            surah="2",
            from_page=50,
            to_page=50,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_to_page_cannot_be_before_surah_start(self):
        item = self.make_item(
            surah="2",
            from_page=2,
            to_page=1,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_to_page_cannot_exceed_surah_end(self):
        item = self.make_item(
            surah="2",
            from_page=49,
            to_page=50,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_to_page_cannot_be_before_from_page(self):
        item = self.make_item(
            from_page=10,
            to_page=9,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_first_page_of_surah_is_valid(self):
        item = self.make_item(
            surah="2",
            from_ayah=1,
            to_ayah=10,
            from_page=2,
            to_page=2,
        )

        item.validate()

        self.assertEqual(
            item.from_page,
            2,
        )

    def test_last_page_of_surah_is_valid(self):
        item = self.make_item(
            surah="2",
            from_ayah=280,
            to_ayah=286,
            from_page=49,
            to_page=49,
        )

        item.validate()

        self.assertEqual(
            item.to_page,
            49,
        )

    # ---------------------------------------------------------
    # Result
    # ---------------------------------------------------------

    def test_all_valid_results(self):
        valid_results = [
            "Excellent",
            "Very Good",
            "Good",
            "Needs Revision",
            "Repeat",
        ]

        for result in valid_results:
            item = self.make_item(
                result=result,
            )

            item.validate()

            self.assertEqual(
                item.result,
                result,
            )

    def test_missing_result_is_not_allowed(self):
        item = self.make_item(
            result=None,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_invalid_result_is_not_allowed(self):
        item = self.make_item(
            result="Passed",
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    # ---------------------------------------------------------
    # Mistakes
    # ---------------------------------------------------------

    def test_zero_mistakes_is_valid(self):
        item = self.make_item(
            mistakes_count=0,
        )

        item.validate()

        self.assertEqual(
            item.mistakes_count,
            0,
        )

    def test_negative_mistakes_are_not_allowed(self):
        item = self.make_item(
            mistakes_count=-1,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    # ---------------------------------------------------------
    # Prompts
    # ---------------------------------------------------------

    def test_zero_prompts_is_valid(self):
        item = self.make_item(
            prompt_count=0,
        )

        item.validate()

        self.assertEqual(
            item.prompt_count,
            0,
        )

    def test_negative_prompts_are_not_allowed(self):
        item = self.make_item(
            prompt_count=-1,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    # ---------------------------------------------------------
    # Ratings
    # ---------------------------------------------------------

    def test_rating_one_is_valid(self):
        item = self.make_item(
            memorization_quality=1,
            tajweed=1,
            fluency=1,
        )

        item.validate()

        self.assertEqual(
            item.memorization_quality,
            1,
        )

    def test_rating_five_is_valid(self):
        item = self.make_item(
            memorization_quality=5,
            tajweed=5,
            fluency=5,
        )

        item.validate()

        self.assertEqual(
            item.fluency,
            5,
        )

    def test_memorization_quality_cannot_be_zero(self):
        item = self.make_item(
            memorization_quality=0,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_memorization_quality_cannot_exceed_five(self):
        item = self.make_item(
            memorization_quality=6,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_tajweed_cannot_be_zero(self):
        item = self.make_item(
            tajweed=0,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_tajweed_cannot_exceed_five(self):
        item = self.make_item(
            tajweed=6,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_fluency_cannot_be_zero(self):
        item = self.make_item(
            fluency=0,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_fluency_cannot_exceed_five(self):
        item = self.make_item(
            fluency=6,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_ratings_are_optional(self):
        item = self.make_item(
            memorization_quality=None,
            tajweed=None,
            fluency=None,
        )

        item.validate()

        self.assertIsNone(
            item.memorization_quality
        )

        self.assertIsNone(
            item.tajweed
        )

        self.assertIsNone(
            item.fluency
        )

    # ---------------------------------------------------------
    # Notes
    # ---------------------------------------------------------

    def test_notes_are_optional(self):
        item = self.make_item(
            notes=None,
        )

        item.validate()

        self.assertIsNone(
            item.notes
        )