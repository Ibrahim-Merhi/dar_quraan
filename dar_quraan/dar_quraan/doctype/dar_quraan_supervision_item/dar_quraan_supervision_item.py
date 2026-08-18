from typing import ClassVar

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class DarQuraanSupervisionItem(Document):
	REVIEW_AREAS: ClassVar[set[str]] = {
		"Session Management",
		"Attendance",
		"Student Progress",
		"Quran Performance",
		"Teacher Adherence",
		"Learning Environment",
		"Other",
	}
	STATUSES: ClassVar[set[str]] = {"Open", "In Progress", "Resolved", "Not Applicable"}

	def validate(self):
		if self.review_area not in self.REVIEW_AREAS:
			frappe.throw(_("Invalid Review Area."))
		if cint(self.rating) < 1 or cint(self.rating) > 5:
			frappe.throw(_("Rating must be between 1 and 5."))
		if not (self.finding or "").strip():
			frappe.throw(_("Finding is required."))
		if self.status not in self.STATUSES:
			frappe.throw(_("Invalid Supervision Item Status."))
		if cint(self.requires_follow_up) and not (self.corrective_action or "").strip():
			frappe.throw(_("Corrective Action is required when follow-up is required."))
		if cint(self.requires_follow_up) and not self.due_date:
			frappe.throw(_("Due Date is required when follow-up is required."))
		if self.status == "Resolved" and not (self.resolution_notes or "").strip():
			frappe.throw(_("Resolution Notes are required for a Resolved supervision item."))
		if self.status in {"Resolved", "Not Applicable"} and cint(self.requires_follow_up):
			frappe.throw(_("Resolved or Not Applicable items cannot require follow-up."))
