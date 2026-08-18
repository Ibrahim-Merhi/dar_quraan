from typing import ClassVar

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, now_datetime


class DarQuraanException(Document):
	TYPES: ClassVar[set[str]] = {
		"Repeated Absence",
		"Repeated Lateness",
		"Repeated Weak Result",
		"No Recent Progress",
		"Missing Attendance",
		"Overdue Follow-up",
		"Overdue Evaluation",
		"Halaqa Over Capacity",
		"Student Without Active Assignment",
		"Assignment Without Teacher",
	}
	SEVERITIES: ClassVar[set[str]] = {"Low", "Medium", "High", "Urgent"}
	STATUSES: ClassVar[set[str]] = {"Open", "Acknowledged", "Resolved", "Cancelled"}

	def validate(self):
		if self.exception_type not in self.TYPES:
			frappe.throw(_("Invalid Exception Type."))
		if self.severity not in self.SEVERITIES:
			frappe.throw(_("Invalid Severity."))
		if self.status not in self.STATUSES:
			frappe.throw(_("Invalid Exception Status."))
		if not (self.message or "").strip():
			frappe.throw(_("Exception Message is required."))
		if bool(self.source_doctype) != bool(self.source_document):
			frappe.throw(_("Source DocType and Source Document must be provided together."))
		self.fetch_assignment_context()
		self.validate_source()
		if cint(self.occurrence_count) < 1:
			self.occurrence_count = 1
		if self.status == "Resolved":
			if not (self.resolution_notes or "").strip():
				frappe.throw(_("Resolution Notes are required for a Resolved exception."))
			self.resolved_on = self.resolved_on or now_datetime()
		else:
			self.resolved_on = None

	def fetch_assignment_context(self):
		if not self.student_assignment:
			return
		if not frappe.db.exists("Dar Quraan Student Assignment", self.student_assignment):
			frappe.throw(_("Selected Student Assignment does not exist."))
		assignment = frappe.get_doc("Dar Quraan Student Assignment", self.student_assignment)
		for fieldname in ("student", "student_name", "branch", "teaching_location", "halaqa", "teacher"):
			self.set(fieldname, assignment.get(fieldname))

	def validate_source(self):
		if not self.source_doctype:
			return
		if not frappe.db.exists(self.source_doctype, self.source_document):
			frappe.throw(_("Selected source document does not exist."))
		if not self.student_assignment:
			return
		if self.source_doctype == "Dar Quraan Attendance":
			belongs = frappe.db.exists(
				"Dar Quraan Attendance Item",
				{
					"parent": self.source_document,
					"parenttype": "Dar Quraan Attendance",
					"student_assignment": self.student_assignment,
				},
			)
		elif self.source_doctype in {
			"Dar Quraan Evaluation",
			"Dar Quraan Student Progress",
			"Dar Quraan Teacher Follow Up",
		}:
			belongs = (
				frappe.db.get_value(
					self.source_doctype,
					self.source_document,
					"student_assignment",
				)
				== self.student_assignment
			)
		elif self.source_doctype == "Dar Quraan Student Assignment":
			belongs = self.source_document == self.student_assignment
		else:
			belongs = True
		if not belongs:
			frappe.throw(
				_("Selected source document does not belong to Student Assignment {0}.").format(
					self.student_assignment
				)
			)
