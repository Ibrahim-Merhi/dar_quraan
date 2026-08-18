from typing import ClassVar

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate


class DarQuraanSupervisionVisit(Document):
	VISIT_TYPES: ClassVar[set[str]] = {"Scheduled", "Unannounced", "Remote", "Follow-up"}
	STATUSES: ClassVar[set[str]] = {"Draft", "Completed", "Cancelled"}

	def validate(self):
		self.validate_halaqa()
		self.fetch_halaqa_context()
		self.validate_required_values()
		self.validate_select_values()
		self.validate_source_session()
		self.validate_items()
		self.calculate_summary()
		self.validate_completion()

	def validate_halaqa(self):
		if not self.halaqa:
			frappe.throw(_("Halaqa is required."))
		if not frappe.db.exists("Dar Quraan Halaqa", self.halaqa):
			frappe.throw(_("Selected Halaqa does not exist."))

	def fetch_halaqa_context(self):
		halaqa = frappe.get_doc("Dar Quraan Halaqa", self.halaqa)
		self.halaqa_name = halaqa.get("halaqa_name")
		self.branch = halaqa.get("branch")
		self.teaching_location = halaqa.get("teaching_location")
		self.teacher = halaqa.get("mentor")
		self.academic_year = halaqa.get("academic_year")
		self.academic_term = halaqa.get("academic_term")
		for fieldname, label in (
			("branch", _("Branch")),
			("teaching_location", _("Teaching Location")),
			("teacher", _("Mentor")),
		):
			if not self.get(fieldname):
				frappe.throw(_("Halaqa {0} does not have a {1}.").format(self.halaqa, label))

	def validate_required_values(self):
		if not self.visit_date:
			frappe.throw(_("Visit Date is required."))
		if not self.supervisor:
			frappe.throw(_("Supervisor is required."))
		if not frappe.db.exists("User", self.supervisor):
			frappe.throw(_("Selected Supervisor does not exist."))

	def validate_select_values(self):
		if self.visit_type not in self.VISIT_TYPES:
			frappe.throw(_("Invalid Visit Type."))
		if self.status not in self.STATUSES:
			frappe.throw(_("Invalid Supervision Visit Status."))

	def validate_source_session(self):
		if not self.source_session:
			return
		if not frappe.db.exists("Dar Quraan Session", self.source_session):
			frappe.throw(_("Selected Source Session does not exist."))
		session_halaqa = frappe.db.get_value("Dar Quraan Session", self.source_session, "halaqa")
		if session_halaqa != self.halaqa:
			frappe.throw(_("Source Session must belong to the selected Halaqa."))

	def validate_items(self):
		rows = self.get("supervision_items") or []
		if not rows:
			frappe.throw(_("At least one Supervision Item is required."))
		normalized = []
		for index, row in enumerate(rows, start=1):
			if isinstance(row, dict):
				row = frappe.get_doc(dict(row, doctype="Dar Quraan Supervision Item"))
				row.idx = index
			try:
				row.validate()
			except frappe.ValidationError as exc:
				frappe.throw(_("Supervision Item, row {0}: {1}").format(row.idx or index, str(exc)))
			if row.due_date and getdate(row.due_date) < getdate(self.visit_date):
				frappe.throw(
					_("Supervision Item, row {0}: Due Date cannot be before Visit Date.").format(
						row.idx or index
					)
				)
			normalized.append(row)
		self.set("supervision_items", normalized)

	def calculate_summary(self):
		rows = self.get("supervision_items") or []
		self.overall_rating = round(sum(flt(row.rating) for row in rows) / len(rows), 2)
		self.follow_up_item_count = sum(cint(row.requires_follow_up) for row in rows)

	def validate_completion(self):
		if self.status == "Completed" and not (self.supervisor_summary or "").strip():
			frappe.throw(_("Supervisor Summary is required for a Completed visit."))
