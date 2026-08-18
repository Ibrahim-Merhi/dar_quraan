import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import formatdate, getdate


class DarQuraanAcademicTerm(Document):
	def validate(self):
		self.normalize_values()
		self.validate_dates()
		self.validate_academic_year()
		self.validate_term_within_academic_year()
		self.validate_unique_term()
		self.validate_current_term()
		self.apply_status_rules()

	def normalize_values(self):
		if self.term_name:
			self.term_name = self.term_name.strip()

	def validate_dates(self):
		if not self.start_date or not self.end_date:
			return

		if getdate(self.end_date) <= getdate(self.start_date):
			frappe.throw(_("End Date must be later than Start Date."))

	def validate_academic_year(self):
		if not self.academic_year:
			return

		academic_year = frappe.db.get_value(
			"Dar Quraan Academic Year",
			self.academic_year,
			["disabled", "status"],
			as_dict=True,
		)

		if not academic_year:
			frappe.throw(_("The selected Academic Year does not exist."))

		if academic_year.disabled:
			frappe.throw(_("A term cannot be linked to a disabled Academic Year."))

		if academic_year.status == "Archived":
			frappe.throw(_("A term cannot be linked to an archived Academic Year."))

	def validate_term_within_academic_year(self):
		if not self.academic_year or not self.start_date or not self.end_date:
			return

		academic_year = frappe.db.get_value(
			"Dar Quraan Academic Year",
			self.academic_year,
			["start_date", "end_date"],
			as_dict=True,
		)

		if not academic_year:
			return

		term_start = getdate(self.start_date)
		term_end = getdate(self.end_date)
		year_start = getdate(academic_year.start_date)
		year_end = getdate(academic_year.end_date)

		if term_start < year_start or term_end > year_end:
			frappe.throw(
				_("Term dates must fall between {0} and {1}, " "the dates of Academic Year {2}.").format(
					formatdate(year_start),
					formatdate(year_end),
					frappe.bold(self.academic_year),
				)
			)

	def validate_unique_term(self):
		if not self.term_name or not self.academic_year:
			return

		existing_term = frappe.db.exists(
			"Dar Quraan Academic Term",
			{
				"term_name": self.term_name,
				"academic_year": self.academic_year,
				"name": ["!=", self.name or ""],
			},
		)

		if existing_term:
			frappe.throw(
				_("Term {0} already exists in Academic Year {1}.").format(
					frappe.bold(self.term_name),
					frappe.bold(self.academic_year),
				)
			)

	def validate_current_term(self):
		if not self.is_current:
			return

		if self.disabled:
			frappe.throw(_("A disabled Academic Term cannot be current."))

		existing_current = frappe.db.exists(
			"Dar Quraan Academic Term",
			{
				"is_current": 1,
				"name": ["!=", self.name or ""],
			},
		)

		if existing_current:
			frappe.throw(
				_("Academic Term {0} is already marked as current.").format(frappe.bold(existing_current))
			)

	def apply_status_rules(self):
		if self.status in ("Closed", "Archived"):
			self.allow_new_enrollment = 0

		if self.status == "Archived":
			self.allow_attendance_entry = 0
			self.allow_progress_entry = 0
			self.is_current = 0
