import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanAyah(FrappeTestCase):
    def setUp(self):
        # Remove test Ayahs first.
        frappe.db.delete(
            "Dar Quraan Ayah",
            {
                "surah": [
                    "in",
                    ["1", "2"],
                ]
            },
        )

        # Remove test Surahs so every test starts
        # from known master data.
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
        fatihah = frappe.get_doc(
            {
                "doctype": "Dar Quraan Surah",
                "surah_number": 1,
                "arabic_name": "الفاتحة",
                "english_name": "The Opening",
                "transliterated_name": "Al-Fatihah",
                "ayah_count": 7,
                "start_global_ayah": 1,
                "end_global_ayah": 7,
                "start_page": 1,
                "end_page": 1,
                "start_juz": 1,
                "end_juz": 1,
                "revelation_place": "Makkah",
                "is_active": 1,
            }
        )
        fatihah.insert()

        baqarah = frappe.get_doc(
            {
                "doctype": "Dar Quraan Surah",
                "surah_number": 2,
                "arabic_name": "البقرة",
                "english_name": "The Cow",
                "transliterated_name": "Al-Baqarah",
                "ayah_count": 286,
                "start_global_ayah": 8,
                "end_global_ayah": 293,
                "start_page": 2,
                "end_page": 49,
                "start_juz": 1,
                "end_juz": 3,
                "revelation_place": "Madinah",
                "is_active": 1,
            }
        )
        baqarah.insert()

    def make_ayah(self, **kwargs):
        data = {
            "doctype": "Dar Quraan Ayah",
            "surah": "1",
            "ayah_number": 1,
            "page_number": 1,
            "juz_number": 1,
            "hizb_number": 1,
            "rub_el_hizb_number": 1,
            "text_uthmani": "",
            "is_active": 1,
        }

        data.update(kwargs)

        return frappe.get_doc(data)

    def test_valid_ayah_can_be_created(self):
        ayah = self.make_ayah()
        ayah.insert()

        self.assertEqual(ayah.name, "1:1")
        self.assertEqual(ayah.verse_key, "1:1")
        self.assertEqual(int(ayah.surah_number), 1)
        self.assertEqual(ayah.ayah_number, 1)
        self.assertEqual(
            ayah.global_ayah_number,
            1,
        )

    def test_verse_key_is_generated_automatically(self):
        ayah = self.make_ayah(
            verse_key="WRONG",
        )

        ayah.insert()

        self.assertEqual(
            ayah.verse_key,
            "1:1",
        )

        self.assertEqual(
            ayah.name,
            "1:1",
        )

    def test_surah_number_is_generated_automatically(self):
        ayah = self.make_ayah(
            surah="2",
            ayah_number=1,
            page_number=2,
            juz_number=1,
            surah_number=99,
        )

        ayah.insert()

        self.assertEqual(
            int(ayah.surah_number),
            2,
        )

    def test_global_ayah_number_is_generated_automatically(self):
        ayah = self.make_ayah(
            surah="2",
            ayah_number=1,
            page_number=2,
            juz_number=1,
            global_ayah_number=999,
        )

        ayah.insert()

        self.assertEqual(
            ayah.global_ayah_number,
            8,
        )

    def test_baqarah_255_has_correct_global_number(self):
        ayah = self.make_ayah(
            surah="2",
            ayah_number=255,
            page_number=42,
            juz_number=3,
        )

        ayah.insert()

        self.assertEqual(
            ayah.verse_key,
            "2:255",
        )

        self.assertEqual(
            int(ayah.surah_number),
            2,
        )

        self.assertEqual(
            ayah.global_ayah_number,
            262,
        )

    def test_missing_surah_is_not_allowed(self):
        ayah = self.make_ayah(
            surah=None,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            ayah.insert()

    def test_invalid_surah_is_not_allowed(self):
        ayah = self.make_ayah(
            surah="999",
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            ayah.insert()

    def test_ayah_number_cannot_be_zero(self):
        ayah = self.make_ayah(
            ayah_number=0,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            ayah.insert()

    def test_ayah_number_cannot_be_negative(self):
        ayah = self.make_ayah(
            ayah_number=-1,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            ayah.insert()

    def test_ayah_number_cannot_exceed_surah_ayah_count(self):
        ayah = self.make_ayah(
            surah="1",
            ayah_number=8,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            ayah.insert()

    def test_last_ayah_of_fatihah_is_valid(self):
        ayah = self.make_ayah(
            surah="1",
            ayah_number=7,
            page_number=1,
            juz_number=1,
        )

        ayah.insert()

        self.assertEqual(
            ayah.verse_key,
            "1:7",
        )

        self.assertEqual(
            ayah.global_ayah_number,
            7,
        )

    def test_last_ayah_of_baqarah_is_valid(self):
        ayah = self.make_ayah(
            surah="2",
            ayah_number=286,
            page_number=49,
            juz_number=3,
        )

        ayah.insert()

        self.assertEqual(
            ayah.verse_key,
            "2:286",
        )

        self.assertEqual(
            ayah.global_ayah_number,
            293,
        )

    def test_page_number_cannot_be_zero(self):
        ayah = self.make_ayah(
            page_number=0,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            ayah.insert()

    def test_page_number_cannot_exceed_604(self):
        ayah = self.make_ayah(
            page_number=605,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            ayah.insert()

    def test_page_must_be_inside_surah_page_range(self):
        ayah = self.make_ayah(
            surah="2",
            ayah_number=1,
            page_number=50,
            juz_number=1,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            ayah.insert()

    def test_juz_number_cannot_be_zero(self):
        ayah = self.make_ayah(
            juz_number=0,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            ayah.insert()

    def test_juz_number_cannot_exceed_30(self):
        ayah = self.make_ayah(
            juz_number=31,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            ayah.insert()

    def test_juz_must_be_inside_surah_juz_range(self):
        ayah = self.make_ayah(
            surah="1",
            ayah_number=1,
            page_number=1,
            juz_number=2,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            ayah.insert()

    def test_hizb_number_cannot_be_zero(self):
        ayah = self.make_ayah(
            hizb_number=0,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            ayah.insert()

    def test_hizb_number_cannot_exceed_60(self):
        ayah = self.make_ayah(
            hizb_number=61,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            ayah.insert()

    def test_rub_el_hizb_number_cannot_be_zero(self):
        ayah = self.make_ayah(
            rub_el_hizb_number=0,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            ayah.insert()

    def test_rub_el_hizb_number_cannot_exceed_240(self):
        ayah = self.make_ayah(
            rub_el_hizb_number=241,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            ayah.insert()

    def test_hizb_and_rub_are_optional(self):
        ayah = self.make_ayah(
            hizb_number=None,
            rub_el_hizb_number=None,
        )

        ayah.insert()

        self.assertEqual(
            ayah.name,
            "1:1",
        )

    def test_duplicate_ayah_is_not_allowed(self):
        first = self.make_ayah()
        first.insert()

        second = self.make_ayah()

        with self.assertRaises(
            frappe.DuplicateEntryError
        ):
            second.insert()