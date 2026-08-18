from typing import ClassVar

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import validate_email_address


class DarQuraanTeacher(Document):
	STATUSES: ClassVar[set[str]] = {"Active", "Inactive"}

	def validate(self):
		self.teacher_name = (self.teacher_name or "").strip()
		if not self.teacher_name:
			frappe.throw(_("Teacher Name is required."))
		if self.status not in self.STATUSES:
			frappe.throw(_("Invalid Teacher Status."))
		if self.get("email"):
			self.email = self.email.strip().lower()
			if not validate_email_address(self.email):
				frappe.throw(_("Invalid teacher email address."))
		if self.get("branch"):
			branch_status = frappe.db.get_value("Dar Quraan Branch", self.branch, "status")
			if not branch_status:
				frappe.throw(_("Selected Branch does not exist."))
			if self.status == "Active" and branch_status != "Active":
				frappe.throw(_("An active Teacher must belong to an active Branch."))
