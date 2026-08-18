import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class DarQuraanProgram(Document):
	def validate(self):
		if cint(self.weekly_minutes) < 30:
			frappe.throw(_("Weekly individual time must be at least 30 minutes."))
		sequences = [cint(row.sequence) for row in self.milestones]
		if any(value <= 0 for value in sequences) or len(sequences) != len(set(sequences)):
			frappe.throw(_("Milestone sequences must be positive and unique."))
		for row in self.milestones:
			if not 0 <= cint(row.required_juz) <= 30:
				frappe.throw(_("Required Juz must be between 0 and 30."))
