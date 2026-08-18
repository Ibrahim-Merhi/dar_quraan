# Copyright (c) 2026, ITIHAD
# For license information, please see license.txt

from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate


class TestDarQuraanStudent(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.test_suffix = uuid4().hex[:8].upper()

	def tearDown(self):
		frappe.db.rollback()

	# -------------------------------------------------------------------------
	# Successful creation
	# -------------------------------------------------------------------------

	def test_valid_student_creation(self):
		student = self.create_student(
			student_code=self.code("VALID"),
			first_name="Ahmad",
			middle_name="Mohammad",
			last_name="Ali",
		)

		self.assertTrue(student.name)
		self.assertEqual(student.student_name, "Ahmad Mohammad Ali")
		self.assertEqual(student.status, "Active")
		self.assertEqual(student.disabled, 0)

	def test_student_name_is_generated(self):
		student = self.create_student(
			student_code=self.code("NAME"),
			first_name="  Ahmad   ",
			middle_name="  Mohammad  Hassan ",
			last_name="  Ali ",
		)

		self.assertEqual(
			student.student_name,
			"Ahmad Mohammad Hassan Ali",
		)

		self.assertEqual(student.first_name, "Ahmad")
		self.assertEqual(student.middle_name, "Mohammad Hassan")
		self.assertEqual(student.last_name, "Ali")

	def test_student_name_without_middle_name(self):
		student = self.create_student(
			student_code=self.code("NOMIDDLE"),
			first_name="Ahmad",
			middle_name=None,
			last_name="Ali",
		)

		self.assertEqual(student.student_name, "Ahmad Ali")

	def test_student_code_is_normalized(self):
		student = self.create_student(
			student_code=f" student {self.test_suffix} ",
		)

		self.assertEqual(
			student.student_code,
			f"STUDENT-{self.test_suffix}",
		)

	def test_student_code_generated_from_document_name(self):
		student = self.create_student(
			student_code=None,
		)

		self.assertTrue(student.name.startswith("DQS-"))
		self.assertEqual(student.student_code, student.name)

	# -------------------------------------------------------------------------
	# Student code validations
	# -------------------------------------------------------------------------

	def test_short_student_code_is_rejected(self):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Student Code must contain at least 3 characters",
		):
			self.create_student(student_code="A")

	def test_empty_student_code_is_rejected(self):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Student Code must contain at least one letter or number",
		):
			self.create_student(student_code="@@@")

	def test_duplicate_student_code_is_rejected(self):
		student_code = self.code("DUPLICATE")

		self.create_student(
			student_code=student_code,
			first_name="First",
		)

		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Student Code .* is already used",
		):
			self.create_student(
				student_code=student_code.lower(),
				first_name="Second",
			)

	# -------------------------------------------------------------------------
	# Legacy ID validations
	# -------------------------------------------------------------------------

	def test_negative_legacy_student_id_is_rejected(self):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Legacy Student ID must be greater than zero",
		):
			self.create_student(
				student_code=self.code("NEGLEGACY"),
				legacy_student_id=-1,
			)

	def test_zero_legacy_student_id_is_allowed_as_empty(self):
		student = self.create_student(
			student_code=self.code("ZEROLEGACY"),
			legacy_student_id=None,
		)

		self.assertTrue(student.name)

	def test_duplicate_legacy_student_id_is_rejected(self):
		legacy_id = int(uuid4().int % 900000) + 100000

		self.create_student(
			student_code=self.code("LEGACY1"),
			legacy_student_id=legacy_id,
		)

		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Legacy Student ID .* is already linked",
		):
			self.create_student(
				student_code=self.code("LEGACY2"),
				legacy_student_id=legacy_id,
			)

	# -------------------------------------------------------------------------
	# Duplicate student detection
	# -------------------------------------------------------------------------

	def test_duplicate_student_identity_is_rejected(self):
		date_of_birth = "2010-01-10"

		self.create_student(
			student_code=self.code("IDENTITY1"),
			first_name="Duplicate",
			middle_name="Student",
			last_name=self.test_suffix,
			date_of_birth=date_of_birth,
		)

		with self.assertRaisesRegex(
			frappe.ValidationError,
			"same name and Date of Birth",
		):
			self.create_student(
				student_code=self.code("IDENTITY2"),
				first_name="Duplicate",
				middle_name="Student",
				last_name=self.test_suffix,
				date_of_birth=date_of_birth,
			)

	def test_same_name_with_different_birth_date_is_allowed(self):
		first_student = self.create_student(
			student_code=self.code("SAMENAME1"),
			first_name="Same",
			last_name=self.test_suffix,
			date_of_birth="2010-01-10",
		)

		second_student = self.create_student(
			student_code=self.code("SAMENAME2"),
			first_name="Same",
			last_name=self.test_suffix,
			date_of_birth="2011-01-10",
		)

		self.assertNotEqual(first_student.name, second_student.name)

	# -------------------------------------------------------------------------
	# Date validations
	# -------------------------------------------------------------------------

	def test_future_date_of_birth_is_rejected(self):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Date of Birth cannot be in the future",
		):
			self.create_student(
				student_code=self.code("FUTUREDOB"),
				date_of_birth=add_days(nowdate(), 1),
			)

	def test_future_registration_date_is_rejected(self):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Registration Date cannot be in the future",
		):
			self.create_student(
				student_code=self.code("FUTUREREG"),
				registration_date=add_days(nowdate(), 1),
			)

	def test_registration_before_birth_is_rejected(self):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Registration Date cannot be earlier than Date of Birth",
		):
			self.create_student(
				student_code=self.code("REGDOB"),
				date_of_birth="2015-01-01",
				registration_date="2014-12-31",
			)

	def test_invalid_legacy_datetime_order_is_rejected(self):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Legacy Updated At cannot be earlier",
		):
			self.create_student(
				student_code=self.code("LEGACYDATE"),
				legacy_created_at="2025-02-01 10:00:00",
				legacy_updated_at="2025-01-01 10:00:00",
			)

	# -------------------------------------------------------------------------
	# Contact validations
	# -------------------------------------------------------------------------

	def test_email_is_normalized(self):
		student = self.create_student(
			student_code=self.code("EMAIL"),
			email="  STUDENT@EXAMPLE.COM ",
		)

		self.assertEqual(student.email, "student@example.com")

	def test_invalid_email_is_rejected(self):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"valid email address",
		):
			self.create_student(
				student_code=self.code("BADEMAIL"),
				email="invalid-email",
			)

	def test_phone_numbers_are_normalized(self):
		student = self.create_student(
			student_code=self.code("PHONE"),
			mobile_number="+961 3 123-456",
			home_number="06 123 456",
			father_number="00 961 70 555 444",
		)

		self.assertEqual(student.mobile_number, "+9613123456")
		self.assertEqual(student.home_number, "06123456")
		self.assertEqual(student.father_number, "+96170555444")

	def test_preferred_contact_uses_mobile_first(self):
		student = self.create_student(
			student_code=self.code("PREFERRED1"),
			mobile_number="03 111 222",
			whatsapp_number="70 333 444",
			father_number="71 555 666",
		)

		self.assertEqual(
			student.preferred_contact_number,
			"03111222",
		)

	def test_preferred_contact_falls_back_to_whatsapp(self):
		student = self.create_student(
			student_code=self.code("PREFERRED2"),
			mobile_number=None,
			whatsapp_number="70 333 444",
			father_number="71 555 666",
		)

		self.assertEqual(
			student.preferred_contact_number,
			"70333444",
		)

	# -------------------------------------------------------------------------
	# Quran profile validations
	# -------------------------------------------------------------------------

	def test_qiraat_track_requires_qiraat_method(self):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Qiraat Method is required",
		):
			self.create_student(
				student_code=self.code("QIRAATREQ"),
				study_track="Qiraat",
				qiraat_method=None,
			)

	def test_qiraat_track_with_method_is_allowed(self):
		student = self.create_student(
			student_code=self.code("QIRAATOK"),
			study_track="Qiraat",
			qiraat_method="Ifraad",
		)

		self.assertEqual(student.study_track, "Qiraat")
		self.assertEqual(student.qiraat_method, "Ifraad")

	def test_qiraat_method_is_cleared_for_non_qiraat_track(self):
		student = self.create_student(
			student_code=self.code("CLEARQIRAAT"),
			study_track="Hifz",
			qiraat_method="Ifraad",
		)

		self.assertIsNone(student.qiraat_method)

	def test_other_qiraat_method_requires_notes(self):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Add the Qiraat method details in Notes",
		):
			self.create_student(
				student_code=self.code("OTHERQIRAAT"),
				study_track="Qiraat",
				qiraat_method="Other",
				notes=None,
			)

	def test_previous_ijazah_requires_details(self):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Previous Ijazah Details are required",
		):
			self.create_student(
				student_code=self.code("IJAZAHDETAIL"),
				has_previous_ijazah=1,
				previous_ijazah_details=None,
			)

	def test_previous_ijazah_details_are_cleared_when_disabled(self):
		student = self.create_student(
			student_code=self.code("CLEARDETAIL"),
			has_previous_ijazah=0,
			previous_ijazah_details="Should be removed",
		)

		self.assertIsNone(student.previous_ijazah_details)

	def test_mujaz_requires_previous_ijazah(self):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Has Previous Ijazah must be enabled",
		):
			self.create_student(
				student_code=self.code("MUJAZREQ"),
				quran_status="Mujaz",
				has_previous_ijazah=0,
			)

	def test_valid_mujaz_student(self):
		student = self.create_student(
			student_code=self.code("MUJAZOK"),
			quran_status="Mujaz",
			has_previous_ijazah=1,
			previous_ijazah_details="Ijazah in Hafs from Asim",
		)

		self.assertEqual(student.quran_status, "Mujaz")
		self.assertEqual(student.has_previous_ijazah, 1)

	# -------------------------------------------------------------------------
	# Status rules
	# -------------------------------------------------------------------------

	def test_active_student_is_not_disabled(self):
		student = self.create_student(
			student_code=self.code("ACTIVE"),
			status="Active",
		)

		self.assertEqual(student.disabled, 0)

	def test_inactive_student_is_disabled(self):
		student = self.create_student(
			student_code=self.code("INACTIVE"),
			status="Inactive",
		)

		self.assertEqual(student.disabled, 1)

	def test_suspended_student_is_disabled(self):
		student = self.create_student(
			student_code=self.code("SUSPENDED"),
			status="Suspended",
		)

		self.assertEqual(student.disabled, 1)

	def test_graduated_student_requires_hafiz_or_mujaz(self):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Graduated student must have Quran Status Hafiz or Mujaz",
		):
			self.create_student(
				student_code=self.code("BADGRAD"),
				status="Graduated",
				quran_status="Memorizing",
			)

	def test_graduated_hafiz_student_is_allowed(self):
		student = self.create_student(
			student_code=self.code("GOODGRAD"),
			status="Graduated",
			quran_status="Hafiz",
		)

		self.assertEqual(student.status, "Graduated")
		self.assertEqual(student.disabled, 1)

	# -------------------------------------------------------------------------
	# Helpers
	# -------------------------------------------------------------------------

	def create_student(self, **overrides):
		values = {
			"doctype": "Dar Quraan Student",
			"naming_series": "DQS-.YYYY.-.#####",
			"student_code": self.code(),
			"first_name": "Test",
			"middle_name": "Dar Quraan",
			"last_name": self.test_suffix,
			"gender": "Male",
			"status": "Active",
			"registration_date": nowdate(),
			"study_track": "Hifz",
			"quran_status": "Memorizing",
			"has_previous_ijazah": 0,
			"disabled": 0,
		}

		values.update(overrides)

		return frappe.get_doc(values).insert()

	def code(self, prefix="STUDENT"):
		return f"{prefix}-{self.test_suffix}"
