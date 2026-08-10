import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanSurah(FrappeTestCase):
    def setUp(self):
        frappe.db.delete(
            "Dar Quraan Surah",
            {
                "surah_number": [
                    "in",
                    [1, 2, 114],
                ]
            },
        )

    def tearDown(self):
        frappe.db.rollback()

    def make_surah(self, **kwargs):
        data = {
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

        data.update(kwargs)

        return frappe.get_doc(data)

    def test_valid_surah_can_be_created(self):
        surah = self.make_surah()
        surah.insert()

        self.assertEqual(int(surah.surah_number), 1)
        self.assertEqual(surah.arabic_name, "الفاتحة")
        self.assertEqual(surah.ayah_count, 7)
        self.assertEqual(surah.start_page, 1)
        self.assertEqual(surah.end_page, 1)

    def test_surah_number_cannot_be_less_than_one(self):
        surah = self.make_surah(
            surah_number=0,
        )

        with self.assertRaises(frappe.ValidationError):
            surah.insert()

    def test_surah_number_cannot_be_greater_than_114(self):
        surah = self.make_surah(
            surah_number=115,
        )

        with self.assertRaises(frappe.ValidationError):
            surah.insert()

    def test_ayah_count_must_be_positive(self):
        surah = self.make_surah(
            ayah_count=0,
        )

        with self.assertRaises(frappe.ValidationError):
            surah.insert()

    def test_start_page_cannot_be_less_than_one(self):
        surah = self.make_surah(
            start_page=0,
        )

        with self.assertRaises(frappe.ValidationError):
            surah.insert()

    def test_start_page_cannot_be_greater_than_604(self):
        surah = self.make_surah(
            start_page=605,
        )

        with self.assertRaises(frappe.ValidationError):
            surah.insert()

    def test_end_page_cannot_be_greater_than_604(self):
        surah = self.make_surah(
            end_page=605,
        )

        with self.assertRaises(frappe.ValidationError):
            surah.insert()

    def test_end_page_cannot_be_before_start_page(self):
        surah = self.make_surah(
            start_page=10,
            end_page=9,
        )

        with self.assertRaises(frappe.ValidationError):
            surah.insert()

    def test_start_juz_cannot_be_less_than_one(self):
        surah = self.make_surah(
            start_juz=0,
        )

        with self.assertRaises(frappe.ValidationError):
            surah.insert()

    def test_start_juz_cannot_be_greater_than_30(self):
        surah = self.make_surah(
            start_juz=31,
        )

        with self.assertRaises(frappe.ValidationError):
            surah.insert()

    def test_end_juz_cannot_be_greater_than_30(self):
        surah = self.make_surah(
            end_juz=31,
        )

        with self.assertRaises(frappe.ValidationError):
            surah.insert()

    def test_end_juz_cannot_be_before_start_juz(self):
        surah = self.make_surah(
            start_juz=2,
            end_juz=1,
        )

        with self.assertRaises(frappe.ValidationError):
            surah.insert()

    def test_duplicate_surah_number_is_not_allowed(self):
        first = self.make_surah()
        first.insert()

        second = self.make_surah(
            arabic_name="اختبار",
            english_name="Duplicate",
            transliterated_name="Duplicate",
        )

        with self.assertRaises(frappe.DuplicateEntryError):
            second.insert()

    def test_surah_114_is_valid(self):
        surah = self.make_surah(
            surah_number=114,
            arabic_name="الناس",
            english_name="Mankind",
            transliterated_name="An-Nas",
            ayah_count=6,
            start_page=604,
            end_page=604,
            start_juz=30,
            end_juz=30,
        )

        surah.insert()

        self.assertEqual(
            int(surah.surah_number),
            114,
        )

        self.assertEqual(
            surah.ayah_count,
            6,
        )

        self.assertEqual(
            surah.end_page,
            604,
        )

    def test_surah_can_span_multiple_pages_and_juz(self):
        surah = self.make_surah(
            surah_number=2,
            arabic_name="البقرة",
            english_name="The Cow",
            transliterated_name="Al-Baqarah",
            ayah_count=286,
            start_page=2,
            end_page=49,
            start_juz=1,
            end_juz=3,
            revelation_place="Madinah",
        )

        surah.insert()

        self.assertEqual(
            surah.ayah_count,
            286,
        )

        self.assertEqual(
            surah.start_page,
            2,
        )

        self.assertEqual(
            surah.end_page,
            49,
        )

        self.assertEqual(
            surah.start_juz,
            1,
        )

        self.assertEqual(
            surah.end_juz,
            3,
        )