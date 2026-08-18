import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanQuranRange(FrappeTestCase):
	def setUp(self):
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
		# Al-Fatihah
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

		# Al-Baqarah
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

	def make_range(self, **kwargs):
		data = {
			"doctype": "Dar Quraan Quran Range",
			"surah": "2",
			"from_ayah": 20,
			"to_ayah": 35,
			"from_page": 4,
			"to_page": 6,
		}

		data.update(kwargs)

		return frappe.get_doc(data)

	# ---------------------------------------------------------
	# Valid ranges
	# ---------------------------------------------------------

	def test_valid_range(self):
		quran_range = self.make_range()

		quran_range.validate()

		self.assertEqual(quran_range.surah, "2")
		self.assertEqual(quran_range.from_ayah, 20)
		self.assertEqual(quran_range.to_ayah, 35)
		self.assertEqual(quran_range.from_page, 4)
		self.assertEqual(quran_range.to_page, 6)

	def test_single_ayah_is_valid(self):
		quran_range = self.make_range(
			from_ayah=20,
			to_ayah=20,
			from_page=4,
			to_page=4,
		)

		quran_range.validate()

		self.assertEqual(
			quran_range.ayah_count,
			1,
		)

		self.assertEqual(
			quran_range.page_count,
			1,
		)

	def test_complete_fatihah_is_valid(self):
		quran_range = self.make_range(
			surah="1",
			from_ayah=1,
			to_ayah=7,
			from_page=1,
			to_page=1,
		)

		quran_range.validate()

		self.assertEqual(
			quran_range.ayah_count,
			7,
		)

		self.assertEqual(
			quran_range.page_count,
			1,
		)

	def test_complete_baqarah_is_valid(self):
		quran_range = self.make_range(
			surah="2",
			from_ayah=1,
			to_ayah=286,
			from_page=2,
			to_page=49,
		)

		quran_range.validate()

		self.assertEqual(
			quran_range.ayah_count,
			286,
		)

		self.assertEqual(
			quran_range.page_count,
			48,
		)

	# ---------------------------------------------------------
	# Automatic calculations
	# ---------------------------------------------------------

	def test_ayah_count_is_calculated(self):
		quran_range = self.make_range(
			from_ayah=20,
			to_ayah=35,
		)

		quran_range.validate()

		self.assertEqual(
			quran_range.ayah_count,
			16,
		)

	def test_page_count_is_calculated(self):
		quran_range = self.make_range(
			from_page=4,
			to_page=6,
		)

		quran_range.validate()

		self.assertEqual(
			quran_range.page_count,
			3,
		)

	def test_manual_counts_are_overwritten(self):
		quran_range = self.make_range(
			from_ayah=20,
			to_ayah=35,
			from_page=4,
			to_page=6,
			ayah_count=999,
			page_count=999,
		)

		quran_range.validate()

		self.assertEqual(
			quran_range.ayah_count,
			16,
		)

		self.assertEqual(
			quran_range.page_count,
			3,
		)

	# ---------------------------------------------------------
	# Surah validation
	# ---------------------------------------------------------

	def test_missing_surah_is_not_allowed(self):
		quran_range = self.make_range(
			surah=None,
		)

		with self.assertRaises(frappe.ValidationError):
			quran_range.validate()

	def test_invalid_surah_is_not_allowed(self):
		quran_range = self.make_range(
			surah="999",
		)

		with self.assertRaises(frappe.ValidationError):
			quran_range.validate()

	def test_inactive_surah_is_not_allowed(self):
		frappe.db.set_value(
			"Dar Quraan Surah",
			"2",
			"is_active",
			0,
		)

		quran_range = self.make_range()

		with self.assertRaises(frappe.ValidationError):
			quran_range.validate()

	# ---------------------------------------------------------
	# From Ayah validation
	# ---------------------------------------------------------

	def test_from_ayah_cannot_be_zero(self):
		quran_range = self.make_range(
			from_ayah=0,
		)

		with self.assertRaises(frappe.ValidationError):
			quran_range.validate()

	def test_from_ayah_cannot_be_negative(self):
		quran_range = self.make_range(
			from_ayah=-1,
		)

		with self.assertRaises(frappe.ValidationError):
			quran_range.validate()

	def test_from_ayah_cannot_exceed_surah_ayah_count(self):
		quran_range = self.make_range(
			surah="1",
			from_ayah=8,
			to_ayah=8,
			from_page=1,
			to_page=1,
		)

		with self.assertRaises(frappe.ValidationError):
			quran_range.validate()

	# ---------------------------------------------------------
	# To Ayah validation
	# ---------------------------------------------------------

	def test_to_ayah_cannot_be_zero(self):
		quran_range = self.make_range(
			to_ayah=0,
		)

		with self.assertRaises(frappe.ValidationError):
			quran_range.validate()

	def test_to_ayah_cannot_be_negative(self):
		quran_range = self.make_range(
			to_ayah=-1,
		)

		with self.assertRaises(frappe.ValidationError):
			quran_range.validate()

	def test_to_ayah_cannot_exceed_surah_ayah_count(self):
		quran_range = self.make_range(
			surah="1",
			from_ayah=1,
			to_ayah=8,
			from_page=1,
			to_page=1,
		)

		with self.assertRaises(frappe.ValidationError):
			quran_range.validate()

	def test_to_ayah_cannot_be_before_from_ayah(self):
		quran_range = self.make_range(
			from_ayah=30,
			to_ayah=20,
		)

		with self.assertRaises(frappe.ValidationError):
			quran_range.validate()

	# ---------------------------------------------------------
	# From Page validation
	# ---------------------------------------------------------

	def test_from_page_cannot_be_before_surah_start_page(self):
		quran_range = self.make_range(
			surah="2",
			from_page=1,
			to_page=2,
		)

		with self.assertRaises(frappe.ValidationError):
			quran_range.validate()

	def test_from_page_cannot_exceed_surah_end_page(self):
		quran_range = self.make_range(
			surah="2",
			from_page=50,
			to_page=50,
		)

		with self.assertRaises(frappe.ValidationError):
			quran_range.validate()

	# ---------------------------------------------------------
	# To Page validation
	# ---------------------------------------------------------

	def test_to_page_cannot_be_before_surah_start_page(self):
		quran_range = self.make_range(
			surah="2",
			from_page=2,
			to_page=1,
		)

		with self.assertRaises(frappe.ValidationError):
			quran_range.validate()

	def test_to_page_cannot_exceed_surah_end_page(self):
		quran_range = self.make_range(
			surah="2",
			from_page=49,
			to_page=50,
		)

		with self.assertRaises(frappe.ValidationError):
			quran_range.validate()

	def test_to_page_cannot_be_before_from_page(self):
		quran_range = self.make_range(
			from_page=10,
			to_page=9,
		)

		with self.assertRaises(frappe.ValidationError):
			quran_range.validate()

	# ---------------------------------------------------------
	# Boundary tests
	# ---------------------------------------------------------

	def test_first_ayah_and_first_page_are_valid(self):
		quran_range = self.make_range(
			surah="2",
			from_ayah=1,
			to_ayah=1,
			from_page=2,
			to_page=2,
		)

		quran_range.validate()

		self.assertEqual(
			quran_range.ayah_count,
			1,
		)

		self.assertEqual(
			quran_range.page_count,
			1,
		)

	def test_last_ayah_and_last_page_are_valid(self):
		quran_range = self.make_range(
			surah="2",
			from_ayah=286,
			to_ayah=286,
			from_page=49,
			to_page=49,
		)

		quran_range.validate()

		self.assertEqual(
			quran_range.ayah_count,
			1,
		)

		self.assertEqual(
			quran_range.page_count,
			1,
		)
