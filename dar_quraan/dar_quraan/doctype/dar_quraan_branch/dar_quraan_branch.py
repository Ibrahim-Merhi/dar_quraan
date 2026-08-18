# Copyright (c) 2026, Ibrahim Merhi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate


class DarQuraanBranch(Document):
	def validate(self):
		self.normalize_branch_code()
		self.validate_branch_code()
		self.validate_unique_branch_code()
		self.validate_unique_branch_name()
		self.validate_capacity()
		self.validate_dates()

	def normalize_branch_code(self):
		if self.branch_code:
			self.branch_code = self.branch_code.strip().upper()

	def validate_branch_code(self):
		if not self.branch_code:
			return

		if " " in self.branch_code:
			frappe.throw(_("Branch Code cannot contain spaces."))

		if not self.branch_code.replace("-", "").replace("_", "").isalnum():
			frappe.throw(_("Branch Code may contain only letters, numbers, hyphens, " "and underscores."))

	def validate_unique_branch_code(self):
		if not self.branch_code:
			return

		existing_branch = frappe.db.exists(
			"Dar Quraan Branch",
			{
				"branch_code": self.branch_code,
				"name": ["!=", self.name or ""],
			},
		)

		if existing_branch:
			frappe.throw(
				_("Branch Code {0} is already used by branch {1}.").format(
					frappe.bold(self.branch_code),
					frappe.bold(existing_branch),
				)
			)

	def validate_unique_branch_name(self):
		if not self.branch_name:
			return

		normalized_name = self.branch_name.strip()
		self.branch_name = normalized_name

		existing_branch = frappe.db.exists(
			"Dar Quraan Branch",
			{
				"branch_name": normalized_name,
				"name": ["!=", self.name or ""],
			},
		)

		if existing_branch:
			frappe.throw(_("Branch Name {0} already exists.").format(frappe.bold(normalized_name)))

	def validate_capacity(self):
		if self.capacity is not None and cint(self.capacity) < 0:
			frappe.throw(_("Capacity cannot be negative."))

	def validate_dates(self):
		if not self.opening_date or not self.closing_date:
			return

		if getdate(self.closing_date) < getdate(self.opening_date):
			frappe.throw(_("Closing Date cannot be before Opening Date."))
