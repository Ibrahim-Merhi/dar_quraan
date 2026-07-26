import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class DarQuraanAcademicYear(Document):
    def validate(self):
        self.normalize_values()
        self.validate_dates()
        self.validate_unique_name()
        self.validate_current_year()
        self.apply_status_rules()

    def normalize_values(self):
        if self.academic_year_name:
            self.academic_year_name = self.academic_year_name.strip()

    def validate_dates(self):
        if not self.start_date or not self.end_date:
            return

        if getdate(self.end_date) <= getdate(self.start_date):
            frappe.throw(
                _("End Date must be later than Start Date.")
            )

    def validate_unique_name(self):
        if not self.academic_year_name:
            return

        existing = frappe.db.exists(
            "Dar Quraan Academic Year",
            {
                "academic_year_name": self.academic_year_name,
                "name": ["!=", self.name or ""],
            },
        )

        if existing:
            frappe.throw(
                _("Academic Year {0} already exists.").format(
                    frappe.bold(self.academic_year_name)
                )
            )

    def validate_current_year(self):
        if not self.is_current:
            return

        if self.disabled:
            frappe.throw(
                _("A disabled Academic Year cannot be marked as current.")
            )

        existing_current = frappe.db.exists(
            "Dar Quraan Academic Year",
            {
                "is_current": 1,
                "name": ["!=", self.name or ""],
            },
        )

        if existing_current:
            frappe.throw(
                _(
                    "Academic Year {0} is already marked as current. "
                    "Unset it before selecting another current year."
                ).format(frappe.bold(existing_current))
            )

    def apply_status_rules(self):
        if self.status in ("Closed", "Archived"):
            self.allow_new_enrollment = 0

        if self.status == "Archived":
            self.allow_attendance_entry = 0
            self.allow_progress_entry = 0
            self.is_current = 0