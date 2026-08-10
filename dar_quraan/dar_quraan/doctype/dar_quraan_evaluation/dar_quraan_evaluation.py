import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class DarQuraanEvaluation(Document):
    def validate(self):
        self.validate_student_assignment()
        self.fetch_assignment_context()
        self.validate_evaluation_date()
        self.validate_evaluation_type()
        self.validate_evaluation_items()
        self.calculate_overall_score()
        self.set_overall_result()
        self.validate_status()

    def validate_student_assignment(self):
        if not self.student_assignment:
            frappe.throw(
                _("Student Assignment is required.")
            )

        if not frappe.db.exists(
            "Dar Quraan Student Assignment",
            self.student_assignment,
        ):
            frappe.throw(
                _("Selected Student Assignment does not exist.")
            )

    def get_student_assignment(self):
        return frappe.get_doc(
            "Dar Quraan Student Assignment",
            self.student_assignment,
        )

    def fetch_assignment_context(self):
        assignment = self.get_student_assignment()

        self.student = assignment.student

        self.student_name = self.get_assignment_value(
            assignment,
            "student_name",
        )

        self.branch = self.get_assignment_value(
            assignment,
            "branch",
        )

        self.teaching_location = self.get_assignment_value(
            assignment,
            "teaching_location",
        )

        self.halaqa = self.get_assignment_value(
            assignment,
            "halaqa",
        )

        self.teacher = self.get_assignment_value(
            assignment,
            "teacher",
        )

        self.study_track = self.get_assignment_value(
            assignment,
            "study_track",
        )

        self.riwayah = self.get_assignment_value(
            assignment,
            "riwayah",
        )

        if not self.student:
            frappe.throw(
                _(
                    "Student Assignment {0} does not have "
                    "a Student."
                ).format(
                    self.student_assignment
                )
            )

        if not self.teacher:
            frappe.throw(
                _(
                    "Student Assignment {0} does not have "
                    "a Teacher."
                ).format(
                    self.student_assignment
                )
            )

        if not self.halaqa:
            frappe.throw(
                _(
                    "Student Assignment {0} does not have "
                    "a Halaqa."
                ).format(
                    self.student_assignment
                )
            )

    def get_assignment_value(
        self,
        assignment,
        fieldname,
    ):
        if not assignment.meta.has_field(fieldname):
            return None

        return assignment.get(fieldname)

    def validate_evaluation_date(self):
        if not self.evaluation_date:
            frappe.throw(
                _("Evaluation Date is required.")
            )

    def validate_evaluation_type(self):
        allowed_types = {
            "Placement",
            "Monthly",
            "Periodic",
            "Final",
            "Special",
        }

        if not self.evaluation_type:
            frappe.throw(
                _("Evaluation Type is required.")
            )

        if self.evaluation_type not in allowed_types:
            frappe.throw(
                _("Invalid Evaluation Type.")
            )

    def validate_evaluation_items(self):
        items = self.get(
            "evaluation_items"
        ) or []

        if not items:
            frappe.throw(
                _(
                    "At least one Evaluation Item "
                    "is required."
                )
            )

        for index, item in enumerate(
            items,
            start=1,
        ):
            try:
                item.validate()

            except frappe.ValidationError as exc:
                frappe.throw(
                    _(
                        "Evaluation Item, row {0}: {1}"
                    ).format(
                        item.idx or index,
                        str(exc),
                    )
                )

    def calculate_overall_score(self):
        items = self.get(
            "evaluation_items"
        ) or []

        if not items:
            self.overall_score = 0
            return

        total_score = 0

        for item in items:
            total_score += flt(
                item.get_score()
            )

        self.overall_score = round(
            total_score / len(items),
            2,
        )

    def set_overall_result(self):
        score = flt(
            self.overall_score
        )

        if score >= 90:
            self.overall_result = "Excellent"

        elif score >= 80:
            self.overall_result = "Very Good"

        elif score >= 70:
            self.overall_result = "Good"

        elif score >= 50:
            self.overall_result = "Needs Revision"

        else:
            self.overall_result = "Repeat"

    def validate_status(self):
        allowed_statuses = {
            "Draft",
            "Completed",
            "Cancelled",
        }

        if not self.status:
            self.status = "Draft"

        if self.status not in allowed_statuses:
            frappe.throw(
                _(
                    "Status must be Draft, Completed, "
                    "or Cancelled."
                )
            )