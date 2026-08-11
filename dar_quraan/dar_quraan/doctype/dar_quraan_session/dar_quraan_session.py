import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class DarQuraanSession(Document):
    def validate(self):
        self.validate_halaqa()
        self.fetch_halaqa_context()
        self.validate_session_date()
        self.validate_timing()
        self.validate_session_type()
        self.validate_status()

    def validate_halaqa(self):
        if not self.halaqa:
            frappe.throw(
                _("Halaqa is required.")
            )

        if not frappe.db.exists(
            "Dar Quraan Halaqa",
            self.halaqa,
        ):
            frappe.throw(
                _("Selected Halaqa does not exist.")
            )

    def get_halaqa(self):
        return frappe.get_doc(
            "Dar Quraan Halaqa",
            self.halaqa,
        )

    def fetch_halaqa_context(self):
        """
        Session context must always come from the selected Halaqa.

        This prevents a Session from being linked to one Halaqa while
        manually carrying another Branch, Location, Teacher, Year,
        or Term.
        """

        halaqa = self.get_halaqa()

        self.halaqa_name = halaqa.halaqa_name

        self.branch = halaqa.branch
        self.teaching_location = halaqa.teaching_location

        self.academic_year = halaqa.academic_year
        self.academic_term = halaqa.academic_term

        # Halaqa currently uses mentor as its primary teacher.
        self.teacher = halaqa.mentor

        if not self.branch:
            frappe.throw(
                _(
                    "Halaqa {0} does not have a Branch."
                ).format(
                    self.halaqa
                )
            )

        if not self.teaching_location:
            frappe.throw(
                _(
                    "Halaqa {0} does not have a "
                    "Teaching Location."
                ).format(
                    self.halaqa
                )
            )

        if not self.academic_year:
            frappe.throw(
                _(
                    "Halaqa {0} does not have an "
                    "Academic Year."
                ).format(
                    self.halaqa
                )
            )

        if not self.academic_term:
            frappe.throw(
                _(
                    "Halaqa {0} does not have an "
                    "Academic Term."
                ).format(
                    self.halaqa
                )
            )

        if not self.teacher:
            frappe.throw(
                _(
                    "Halaqa {0} does not have a Mentor."
                ).format(
                    self.halaqa
                )
            )

        if halaqa.status == "Closed":
            frappe.throw(
                _("Sessions cannot be created for a Closed Halaqa.")
            )

        # Use Halaqa schedule when Session times were not entered.
        if not self.start_time and halaqa.start_time:
            self.start_time = halaqa.start_time

        if not self.end_time and halaqa.end_time:
            self.end_time = halaqa.end_time

    def validate_session_date(self):
        if not self.session_date:
            frappe.throw(
                _("Session Date is required.")
            )

        session_date = getdate(
            self.session_date
        )

        halaqa = self.get_halaqa()

        if halaqa.start_date:
            if session_date < getdate(
                halaqa.start_date
            ):
                frappe.throw(
                    _(
                        "Session Date cannot be before "
                        "the Halaqa Start Date."
                    )
                )

        if halaqa.end_date:
            if session_date > getdate(
                halaqa.end_date
            ):
                frappe.throw(
                    _(
                        "Session Date cannot be after "
                        "the Halaqa End Date."
                    )
                )

        self.validate_session_date_against_term(
            session_date
        )

    def validate_session_date_against_term(
        self,
        session_date,
    ):
        if not self.academic_term:
            return

        term = frappe.db.get_value(
            "Dar Quraan Academic Term",
            self.academic_term,
            [
                "start_date",
                "end_date",
                "status",
            ],
            as_dict=True,
        )

        if not term:
            frappe.throw(
                _("Selected Academic Term does not exist.")
            )

        if term.status != "Open":
            frappe.throw(
                _("Academic Term must be Open.")
            )

        if term.start_date:
            if session_date < getdate(
                term.start_date
            ):
                frappe.throw(
                    _(
                        "Session Date cannot be before "
                        "the Academic Term starts."
                    )
                )

        if term.end_date:
            if session_date > getdate(
                term.end_date
            ):
                frappe.throw(
                    _(
                        "Session Date cannot be after "
                        "the Academic Term ends."
                    )
                )

    def validate_timing(self):
        """
        Timing is optional only when both values are absent.

        If one is supplied, both are required.
        """

        if not self.start_time and not self.end_time:
            return

        if not self.start_time:
            frappe.throw(
                _("Start Time is required when End Time is set.")
            )

        if not self.end_time:
            frappe.throw(
                _("End Time is required when Start Time is set.")
            )

        if self.start_time >= self.end_time:
            frappe.throw(
                _("Start Time must be before End Time.")
            )

    def validate_session_type(self):
        allowed_types = {
            "Regular",
            "Makeup",
            "Extra",
            "Evaluation",
        }

        if not self.session_type:
            self.session_type = "Regular"

        if self.session_type not in allowed_types:
            frappe.throw(
                _(
                    "Session Type must be Regular, Makeup, "
                    "Extra, or Evaluation."
                )
            )

    def validate_status(self):
        allowed_statuses = {
            "Planned",
            "In Progress",
            "Completed",
            "Cancelled",
        }

        if not self.status:
            self.status = "Planned"

        if self.status not in allowed_statuses:
            frappe.throw(
                _(
                    "Status must be Planned, In Progress, "
                    "Completed, or Cancelled."
                )
            )