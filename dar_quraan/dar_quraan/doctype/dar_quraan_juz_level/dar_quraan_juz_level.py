import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class DarQuraanJuzLevel(Document):
	def validate(self):
		self.normalize_values()
		self.validate_juz_values()
		self.validate_range()
		self.validate_juz_count_within_range()
		self.validate_unique_level_name()
		self.validate_unique_display_order()
		self.validate_overlapping_range()
		self.apply_inactive_rules()

	def normalize_values(self):
		if self.level_name:
			self.level_name = self.level_name.strip()

		if self.arabic_name:
			self.arabic_name = self.arabic_name.strip()

	def validate_juz_values(self):
		values = {
			_("Juz Count"): self.juz_count,
			_("Minimum Juz"): self.minimum_juz,
			_("Maximum Juz"): self.maximum_juz,
		}

		for label, value in values.items():
			numeric_value = cint(value)

			if numeric_value < 0 or numeric_value > 30:
				frappe.throw(_("{0} must be between 0 and 30.").format(label))

		if cint(self.display_order) < 1:
			frappe.throw(_("Display Order must be greater than zero."))

	def validate_range(self):
		minimum_juz = cint(self.minimum_juz)
		maximum_juz = cint(self.maximum_juz)

		if minimum_juz > maximum_juz:
			frappe.throw(_("Minimum Juz cannot be greater than Maximum Juz."))

	def validate_juz_count_within_range(self):
		juz_count = cint(self.juz_count)
		minimum_juz = cint(self.minimum_juz)
		maximum_juz = cint(self.maximum_juz)

		if juz_count < minimum_juz or juz_count > maximum_juz:
			frappe.throw(
				_("Juz Count must be between Minimum Juz {0} " "and Maximum Juz {1}.").format(
					frappe.bold(minimum_juz),
					frappe.bold(maximum_juz),
				)
			)

	def validate_unique_level_name(self):
		if not self.level_name:
			return

		existing_level = frappe.db.exists(
			"Dar Quraan Juz Level",
			{
				"level_name": self.level_name,
				"name": ["!=", self.name or ""],
			},
		)

		if existing_level:
			frappe.throw(_("Juz Level {0} already exists.").format(frappe.bold(self.level_name)))

	def validate_unique_display_order(self):
		if not self.display_order:
			return

		existing_level = frappe.db.exists(
			"Dar Quraan Juz Level",
			{
				"display_order": self.display_order,
				"name": ["!=", self.name or ""],
			},
		)

		if existing_level:
			frappe.throw(
				_("Display Order {0} is already assigned to Juz Level {1}.").format(
					frappe.bold(self.display_order),
					frappe.bold(existing_level),
				)
			)

	def validate_overlapping_range(self):
		minimum_juz = cint(self.minimum_juz)
		maximum_juz = cint(self.maximum_juz)

		overlapping_level = frappe.db.sql(
			"""
            SELECT name, level_name, minimum_juz, maximum_juz
            FROM `tabDar Quraan Juz Level`
            WHERE name != %(name)s
              AND disabled = 0
              AND status = 'Active'
              AND minimum_juz <= %(maximum_juz)s
              AND maximum_juz >= %(minimum_juz)s
            LIMIT 1
            """,
			{
				"name": self.name or "",
				"minimum_juz": minimum_juz,
				"maximum_juz": maximum_juz,
			},
			as_dict=True,
		)

		if overlapping_level:
			level = overlapping_level[0]

			frappe.throw(
				_("The range {0}-{1} overlaps with Juz Level {2}, " "which uses the range {3}-{4}.").format(
					frappe.bold(minimum_juz),
					frappe.bold(maximum_juz),
					frappe.bold(level.level_name),
					frappe.bold(level.minimum_juz),
					frappe.bold(level.maximum_juz),
				)
			)

	def apply_inactive_rules(self):
		if self.disabled:
			self.status = "Inactive"
