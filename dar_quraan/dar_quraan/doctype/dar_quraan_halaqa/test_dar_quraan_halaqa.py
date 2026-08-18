import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, getdate, nowdate, random_string


class TestDarQuraanHalaqa(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()

		cls.test_suffix = random_string(6).upper()

		cls.year_start = getdate(nowdate())
		cls.year_end = getdate(add_days(cls.year_start, 364))

		cls.term_start = getdate(add_days(cls.year_start, 10))
		cls.term_end = getdate(add_days(cls.year_start, 180))

		cls.branch = cls.create_branch(
			branch_code=f"BR-{cls.test_suffix}",
			branch_name=f"Test Branch {cls.test_suffix}",
			status="Active",
		)

		cls.other_branch = cls.create_branch(
			branch_code=f"BR2-{cls.test_suffix}",
			branch_name=f"Other Test Branch {cls.test_suffix}",
			status="Active",
		)

		cls.inactive_branch = cls.create_branch(
			branch_code=f"BRI-{cls.test_suffix}",
			branch_name=f"Inactive Test Branch {cls.test_suffix}",
			status="Inactive",
		)

		cls.location = cls.create_location(
			location_code=f"LOC-{cls.test_suffix}",
			location_name=f"Test Location {cls.test_suffix}",
			branch=cls.branch.name,
			status="Active",
			allow_halaqas=1,
		)

		cls.other_branch_location = cls.create_location(
			location_code=f"LOC2-{cls.test_suffix}",
			location_name=f"Other Branch Location {cls.test_suffix}",
			branch=cls.other_branch.name,
			status="Active",
			allow_halaqas=1,
		)

		cls.inactive_location = cls.create_location(
			location_code=f"LOCI-{cls.test_suffix}",
			location_name=f"Inactive Location {cls.test_suffix}",
			branch=cls.branch.name,
			status="Inactive",
			allow_halaqas=1,
		)

		cls.location_not_allowing_halaqas = cls.create_location(
			location_code=f"LOCN-{cls.test_suffix}",
			location_name=f"No Halaqas Location {cls.test_suffix}",
			branch=cls.branch.name,
			status="Active",
			allow_halaqas=0,
		)

		cls.academic_year = cls.create_academic_year(
			academic_year_name=(f"Test Academic Year {cls.test_suffix}"),
			status="Open",
			start_date=cls.year_start,
			end_date=cls.year_end,
		)

		cls.closed_academic_year = cls.create_academic_year(
			academic_year_name=(f"Closed Academic Year {cls.test_suffix}"),
			status="Closed",
			start_date=cls.year_start,
			end_date=cls.year_end,
		)

		cls.academic_term = cls.create_academic_term(
			term_name=f"Test Term {cls.test_suffix}",
			academic_year=cls.academic_year.name,
			status="Open",
			start_date=cls.term_start,
			end_date=cls.term_end,
		)

		cls.closed_academic_term = cls.create_academic_term(
			term_name=f"Closed Term {cls.test_suffix}",
			academic_year=cls.academic_year.name,
			status="Closed",
			start_date=cls.term_start,
			end_date=cls.term_end,
		)

		cls.other_academic_year = cls.create_academic_year(
			academic_year_name=(f"Other Academic Year {cls.test_suffix}"),
			status="Open",
			start_date=cls.year_start,
			end_date=cls.year_end,
		)

		cls.other_year_term = cls.create_academic_term(
			term_name=f"Other Year Term {cls.test_suffix}",
			academic_year=cls.other_academic_year.name,
			status="Open",
			start_date=cls.term_start,
			end_date=cls.term_end,
		)

	def test_create_valid_halaqa(self):
		halaqa = self.create_halaqa(
			halaqa_code=self.code("VALID"),
			halaqa_name=self.name("Valid Halaqa"),
		)

		self.assertTrue(halaqa.name)
		self.assertEqual(halaqa.status, "Planning")
		self.assertEqual(
			halaqa.branch,
			self.branch.name,
		)
		self.assertEqual(
			halaqa.teaching_location,
			self.location.name,
		)
		self.assertEqual(
			halaqa.maximum_students,
			20,
		)
		self.assertEqual(
			halaqa.current_students,
			0,
		)
		self.assertEqual(
			halaqa.allow_new_enrollments,
			1,
		)

	def test_halaqa_code_is_normalized(self):
		code = self.code("NORMAL")

		halaqa = self.create_halaqa(
			halaqa_code=f"  {code.lower()}  ",
			halaqa_name=self.name("Normalized Code"),
		)

		self.assertEqual(
			halaqa.halaqa_code,
			code,
		)

	def test_halaqa_name_is_trimmed(self):
		halaqa = self.create_halaqa(
			halaqa_code=self.code("TRIM"),
			halaqa_name=(f"  {self.name('Trimmed Name')}  "),
		)

		self.assertEqual(
			halaqa.halaqa_name,
			self.name("Trimmed Name"),
		)

	def test_invalid_halaqa_code_characters(self):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			("Halaqa Code may contain only " "uppercase letters"),
		):
			self.create_halaqa(
				halaqa_code="INVALID CODE!",
				halaqa_name=self.name("Invalid Code"),
			)

	def test_duplicate_halaqa_code_is_rejected(self):
		duplicate_code = self.code("DUPCODE")

		self.create_halaqa(
			halaqa_code=duplicate_code,
			halaqa_name=self.name("First Code Record"),
		)

		with self.assertRaisesRegex(
			frappe.ValidationError,
			"already exists",
		):
			self.create_halaqa(
				halaqa_code=duplicate_code,
				halaqa_name=self.name("Second Code Record"),
			)

	def test_duplicate_name_in_same_context_is_rejected(
		self,
	):
		duplicate_name = self.name("Duplicate Name")

		self.create_halaqa(
			halaqa_code=self.code("DUPNAME1"),
			halaqa_name=duplicate_name,
		)

		with self.assertRaisesRegex(
			frappe.ValidationError,
			"already exists in this Branch",
		):
			self.create_halaqa(
				halaqa_code=self.code("DUPNAME2"),
				halaqa_name=duplicate_name,
			)

	def test_same_name_is_allowed_in_different_branch(
		self,
	):
		shared_name = self.name("Shared Branch Name")

		first_halaqa = self.create_halaqa(
			halaqa_code=self.code("BRANCH1"),
			halaqa_name=shared_name,
		)

		second_halaqa = self.create_halaqa(
			halaqa_code=self.code("BRANCH2"),
			halaqa_name=shared_name,
			branch=self.other_branch.name,
			teaching_location=(self.other_branch_location.name),
		)

		self.assertTrue(first_halaqa.name)
		self.assertTrue(second_halaqa.name)
		self.assertNotEqual(
			first_halaqa.branch,
			second_halaqa.branch,
		)

	def test_inactive_branch_is_rejected(self):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Branch must be Active",
		):
			self.create_halaqa(
				halaqa_code=self.code("INACTIVEBR"),
				halaqa_name=self.name("Inactive Branch"),
				branch=(self.inactive_branch.name),
				teaching_location=(self.location.name),
			)

	def test_inactive_teaching_location_is_rejected(
		self,
	):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			("Teaching Location must be " "Active"),
		):
			self.create_halaqa(
				halaqa_code=self.code("INACTIVELOC"),
				halaqa_name=self.name("Inactive Location"),
				teaching_location=(self.inactive_location.name),
			)

	def test_location_that_does_not_allow_halaqas_is_rejected(
		self,
	):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"does not allow Halaqas",
		):
			self.create_halaqa(
				halaqa_code=self.code("NOHALAQA"),
				halaqa_name=self.name("Location Not Allowed"),
				teaching_location=(self.location_not_allowing_halaqas.name),
			)

	def test_location_must_belong_to_selected_branch(
		self,
	):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			("must belong to the selected " "Branch"),
		):
			self.create_halaqa(
				halaqa_code=self.code("WRONGBRANCH"),
				halaqa_name=self.name("Wrong Location Branch"),
				branch=self.branch.name,
				teaching_location=(self.other_branch_location.name),
			)

	def test_academic_year_must_be_open(self):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Academic Year must be Open",
		):
			self.create_halaqa(
				halaqa_code=self.code("CLOSEDYEAR"),
				halaqa_name=self.name("Closed Academic Year"),
				academic_year=(self.closed_academic_year.name),
			)

	def test_academic_term_must_be_open(self):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Academic Term must be Open",
		):
			self.create_halaqa(
				halaqa_code=self.code("CLOSEDTERM"),
				halaqa_name=self.name("Closed Academic Term"),
				academic_term=(self.closed_academic_term.name),
			)

	def test_term_must_belong_to_selected_academic_year(
		self,
	):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			("must belong to the selected " "Academic Year"),
		):
			self.create_halaqa(
				halaqa_code=self.code("WRONGTERM"),
				halaqa_name=self.name("Wrong Academic Term"),
				academic_year=(self.academic_year.name),
				academic_term=(self.other_year_term.name),
			)

	def test_maximum_students_must_be_greater_than_zero(
		self,
	):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			("Maximum Students must be " "greater than zero"),
		):
			self.create_halaqa(
				halaqa_code=self.code("ZEROCAP"),
				halaqa_name=self.name("Zero Capacity"),
				maximum_students=0,
			)

	def test_current_students_cannot_be_negative(
		self,
	):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			("Current Students cannot be " "negative"),
		):
			self.create_halaqa(
				halaqa_code=self.code("NEGCURRENT"),
				halaqa_name=self.name("Negative Current Students"),
				current_students=-1,
			)

	def test_current_students_cannot_exceed_capacity(
		self,
	):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"cannot exceed Maximum Students",
		):
			self.create_halaqa(
				halaqa_code=self.code("OVERCAP"),
				halaqa_name=self.name("Over Capacity"),
				maximum_students=10,
				current_students=11,
			)

	def test_start_date_cannot_be_after_end_date(
		self,
	):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			("Start Date cannot be after " "End Date"),
		):
			self.create_halaqa(
				halaqa_code=self.code("DATEORDER"),
				halaqa_name=self.name("Invalid Date Order"),
				start_date=add_days(
					self.term_start,
					20,
				),
				end_date=add_days(
					self.term_start,
					10,
				),
			)

	def test_start_date_cannot_be_before_term(
		self,
	):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			("Start Date cannot be before " "the Academic Term starts"),
		):
			self.create_halaqa(
				halaqa_code=self.code("BEFORETERM"),
				halaqa_name=self.name("Before Term"),
				start_date=add_days(
					self.term_start,
					-1,
				),
			)

	def test_end_date_cannot_be_after_term(
		self,
	):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			("End Date cannot be after " "the Academic Term ends"),
		):
			self.create_halaqa(
				halaqa_code=self.code("AFTERTERM"),
				halaqa_name=self.name("After Term"),
				end_date=add_days(
					self.term_end,
					1,
				),
			)

	def test_start_time_must_be_before_end_time(
		self,
	):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			("Start Time must be before " "End Time"),
		):
			self.create_halaqa(
				halaqa_code=self.code("BADTIME"),
				halaqa_name=self.name("Invalid Time"),
				start_time="12:00:00",
				end_time="10:00:00",
			)

	def test_same_mentor_and_assistant_is_rejected(
		self,
	):
		teacher = self.create_teacher(
			teacher_name=(f"Teacher {self.test_suffix}"),
		)

		with self.assertRaisesRegex(
			frappe.ValidationError,
			("Mentor and Assistant Mentor " "cannot be the same person"),
		):
			self.create_halaqa(
				halaqa_code=self.code("SAMEMENTOR"),
				halaqa_name=self.name("Same Mentor"),
				mentor=teacher.name,
				assistant_mentor=teacher.name,
			)

	def test_closed_halaqa_requires_closed_on(
		self,
	):
		with self.assertRaisesRegex(
			frappe.ValidationError,
			"Closed On is required",
		):
			self.create_halaqa(
				halaqa_code=self.code("CLOSEDNO"),
				halaqa_name=self.name("Closed Without Date"),
				status="Closed",
				closed_on=None,
			)

	def test_closed_halaqa_disables_new_enrollments(
		self,
	):
		halaqa = self.create_halaqa(
			halaqa_code=self.code("CLOSEDYES"),
			halaqa_name=self.name("Closed With Date"),
			status="Closed",
			closed_on=nowdate(),
			allow_new_enrollments=1,
		)

		self.assertEqual(
			halaqa.status,
			"Closed",
		)

		self.assertEqual(
			halaqa.allow_new_enrollments,
			0,
		)

	def create_halaqa(
		self,
		halaqa_code,
		halaqa_name,
		branch=None,
		teaching_location=None,
		academic_year=None,
		academic_term=None,
		maximum_students=20,
		current_students=0,
		start_date=None,
		end_date=None,
		start_time=None,
		end_time=None,
		status="Planning",
		allow_new_enrollments=1,
		closed_on=None,
		mentor=None,
		assistant_mentor=None,
	):
		doc = frappe.get_doc(
			{
				"doctype": "Dar Quraan Halaqa",
				"naming_series": ("DQH-.YYYY.-.#####"),
				"halaqa_code": halaqa_code,
				"halaqa_name": halaqa_name,
				"halaqa_category": "Kids",
				"status": status,
				"branch": (branch or self.branch.name),
				"teaching_location": (teaching_location or self.location.name),
				"academic_year": (academic_year or self.academic_year.name),
				"academic_term": (academic_term or self.academic_term.name),
				"mentor": mentor,
				"assistant_mentor": (assistant_mentor),
				"maximum_students": (maximum_students),
				"current_students": (current_students),
				"allow_new_enrollments": (allow_new_enrollments),
				"start_date": (start_date or self.term_start),
				"end_date": (end_date or self.term_end),
				"start_time": start_time,
				"end_time": end_time,
				"closed_on": closed_on,
			}
		)

		doc.insert()

		return doc

	@classmethod
	def create_teacher(
		cls,
		teacher_name,
	):
		return frappe.get_doc(
			{
				"doctype": "Dar Quraan Teacher",
				"naming_series": ("DQT-.#####"),
				"teacher_name": teacher_name,
				"status": "Active",
			}
		).insert()

	@classmethod
	def create_branch(
		cls,
		branch_code,
		branch_name,
		status,
	):
		return frappe.get_doc(
			{
				"doctype": "Dar Quraan Branch",
				"naming_series": ("DQB-.#####"),
				"branch_code": branch_code,
				"branch_name": branch_name,
				"status": status,
			}
		).insert()

	@classmethod
	def create_location(
		cls,
		location_code,
		location_name,
		branch,
		status,
		allow_halaqas,
	):
		return frappe.get_doc(
			{
				"doctype": ("Dar Quraan Teaching Location"),
				"naming_series": ("DQTL-.#####"),
				"location_name": (location_name),
				"location_code": (location_code),
				"status": status,
				"location_type": ("Classroom"),
				"branch": branch,
				"inside_branch_premises": 1,
				"city": "Test City",
				"address": ("Test Teaching Location Address"),
				"capacity": 30,
				"allow_halaqas": (allow_halaqas),
				"disabled": 0,
			}
		).insert()

	@classmethod
	def create_academic_year(
		cls,
		academic_year_name,
		status,
		start_date,
		end_date,
	):
		return frappe.get_doc(
			{
				"doctype": ("Dar Quraan Academic Year"),
				"naming_series": ("DQAY-.#####"),
				"academic_year_name": (academic_year_name),
				"status": status,
				"start_date": start_date,
				"end_date": end_date,
				"is_current": 0,
				"allow_attendance_entry": 1,
				"allow_progress_entry": 1,
				"allow_new_enrollment": 1,
				"disabled": 0,
			}
		).insert()

	@classmethod
	def create_academic_term(
		cls,
		term_name,
		academic_year,
		status,
		start_date,
		end_date,
	):
		return frappe.get_doc(
			{
				"doctype": ("Dar Quraan Academic Term"),
				"naming_series": ("DQAT-.#####"),
				"term_name": term_name,
				"academic_year": (academic_year),
				"status": status,
				"start_date": start_date,
				"end_date": end_date,
				"is_current": 0,
				"allow_new_enrollment": 1,
				"allow_attendance_entry": 1,
				"allow_progress_entry": 1,
				"disabled": 0,
			}
		).insert()

	@classmethod
	def code(
		cls,
		value,
	):
		return f"{value}-{cls.test_suffix}"

	@classmethod
	def name(
		cls,
		value,
	):
		return f"{value} {cls.test_suffix}"
