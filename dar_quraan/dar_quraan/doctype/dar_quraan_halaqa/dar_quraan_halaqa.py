import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class DarQuraanHalaqa(Document):
	def validate(self):
		self.normalize_values()
		self.validate_halaqa_code()
		self.validate_unique_halaqa_code()
		self.validate_unique_halaqa_name()

		self.validate_branch()
		self.validate_teaching_location()
		self.validate_academic_year()
		self.validate_academic_term()

		self.validate_capacity()
		self.validate_dates()
		self.validate_times()
		self.validate_mentors()

		self.apply_status_rules()

	def normalize_values(self):
		if self.halaqa_code:
			self.halaqa_code = self.halaqa_code.strip().upper()

		if self.halaqa_name:
			self.halaqa_name = self.halaqa_name.strip()

		if self.arabic_name:
			self.arabic_name = self.arabic_name.strip()

	def validate_halaqa_code(self):
		if not self.halaqa_code:
			return

		if not re.fullmatch(r"[A-Z0-9_-]+", self.halaqa_code):
			frappe.throw(
				_("Halaqa Code may contain only uppercase letters, numbers, hyphens and underscores.")
			)

	def validate_unique_halaqa_code(self):
		if not self.halaqa_code:
			return

		existing = frappe.db.exists(
			"Dar Quraan Halaqa",
			{
				"halaqa_code": self.halaqa_code,
				"name": ["!=", self.name or ""],
			},
		)

		if existing:
			frappe.throw(_("Halaqa Code {0} already exists.").format(frappe.bold(self.halaqa_code)))

	def validate_unique_halaqa_name(self):
		if not self.halaqa_name:
			return

		existing = frappe.db.exists(
			"Dar Quraan Halaqa",
			{
				"halaqa_name": self.halaqa_name,
				"branch": self.branch,
				"academic_year": self.academic_year,
				"academic_term": self.academic_term,
				"name": ["!=", self.name or ""],
			},
		)

		if existing:
			frappe.throw(
				_(
					"A Halaqa named {0} already exists in this Branch, Academic Year and Academic Term."
				).format(frappe.bold(self.halaqa_name))
			)

	def validate_branch(self):
		if not self.branch:
			return

		branch = frappe.db.get_value(
			"Dar Quraan Branch",
			self.branch,
			["status"],
			as_dict=True,
		)

		if not branch:
			frappe.throw(_("Branch does not exist."))

		if branch.status != "Active":
			frappe.throw(_("The selected Branch must be Active."))

	def validate_teaching_location(self):
		if not self.teaching_location:
			return

		location = frappe.db.get_value(
			"Dar Quraan Teaching Location",
			self.teaching_location,
			["branch", "status", "allow_halaqas"],
			as_dict=True,
		)

		if not location:
			frappe.throw(_("Teaching Location does not exist."))

		if location.status != "Active":
			frappe.throw(_("Teaching Location must be Active."))

		if not location.allow_halaqas:
			frappe.throw(_("Teaching Location does not allow Halaqas."))

		if location.branch != self.branch:
			frappe.throw(_("Teaching Location must belong to the selected Branch."))

	def validate_academic_year(self):
		if not self.academic_year:
			return

		year = frappe.db.get_value(
			"Dar Quraan Academic Year",
			self.academic_year,
			["status", "start_date", "end_date"],
			as_dict=True,
		)

		if not year:
			frappe.throw(_("Academic Year does not exist."))

		if year.status != "Open":
			frappe.throw(_("Academic Year must be Open."))

	def validate_academic_term(self):
		if not self.academic_term:
			return

		term = frappe.db.get_value(
			"Dar Quraan Academic Term",
			self.academic_term,
			[
				"status",
				"academic_year",
				"start_date",
				"end_date",
			],
			as_dict=True,
		)

		if not term:
			frappe.throw(_("Academic Term does not exist."))

		if term.status != "Open":
			frappe.throw(_("Academic Term must be Open."))

		if term.academic_year != self.academic_year:
			frappe.throw(_("Academic Term must belong to the selected Academic Year."))

	def validate_capacity(self):
		if cint(self.maximum_students) <= 0:
			frappe.throw(_("Maximum Students must be greater than zero."))

		if cint(self.current_students) < 0:
			frappe.throw(_("Current Students cannot be negative."))

		if cint(self.current_students) > cint(self.maximum_students):
			frappe.throw(_("Current Students cannot exceed Maximum Students."))

	def validate_dates(self):
		if self.start_date and self.end_date:
			if self.start_date > self.end_date:
				frappe.throw(_("Start Date cannot be after End Date."))

		if self.academic_term and self.start_date:
			term = frappe.db.get_value(
				"Dar Quraan Academic Term",
				self.academic_term,
				["start_date", "end_date"],
				as_dict=True,
			)

			if term:
				if self.start_date < term.start_date:
					frappe.throw(_("Start Date cannot be before the Academic Term starts."))

				if self.end_date and self.end_date > term.end_date:
					frappe.throw(_("End Date cannot be after the Academic Term ends."))

	def validate_times(self):
		if self.start_time and self.end_time:
			if self.start_time >= self.end_time:
				frappe.throw(_("Start Time must be before End Time."))

	def validate_mentors(self):
		if self.mentor and self.assistant_mentor and self.mentor == self.assistant_mentor:
			frappe.throw(_("Mentor and Assistant Mentor cannot be the same person."))

		for teacher in (self.mentor, self.assistant_mentor):
			if not teacher:
				continue

			teacher_doc = frappe.db.get_value(
				"Dar Quraan Teacher",
				teacher,
				["status"],
				as_dict=True,
			)

			if not teacher_doc:
				frappe.throw(_("Teacher {0} does not exist.").format(frappe.bold(teacher)))

			if teacher_doc.status != "Active":
				frappe.throw(_("Teacher {0} must be Active.").format(frappe.bold(teacher)))

	def apply_status_rules(self):
		if self.status == "Closed":
			self.allow_new_enrollments = 0

			if not self.closed_on:
				frappe.throw(_("Closed On is required when the Halaqa is Closed."))
