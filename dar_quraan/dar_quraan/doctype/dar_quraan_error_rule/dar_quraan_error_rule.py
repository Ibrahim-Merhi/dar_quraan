import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class DarQuraanErrorRule(Document):
	def validate(self):
		if flt(self.deduction) <= 0:
			frappe.throw(_("Deduction must be greater than zero."))
