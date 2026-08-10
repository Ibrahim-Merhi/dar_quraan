import frappe
from frappe import _
from frappe.model.document import Document


class DarQuraanStudentProgress(Document):
    def validate(self):
        self.validate_student_assignment()
        self.fetch_assignment_context()
        self.validate_progress_date()
        self.validate_quran_progress()
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
        if not self.student_assignment:
            frappe.throw(
                _("Student Assignment is required.")
            )

        return frappe.get_doc(
            "Dar Quraan Student Assignment",
            self.student_assignment,
        )

    def fetch_assignment_context(self):
        """
        Student Progress must always inherit its academic context
        from Student Assignment.

        We deliberately overwrite values supplied manually or through
        an API so that progress can never become disconnected from the
        student's real assignment.
        """

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
        """
        Helper kept separate so the academic-context mapping remains
        easy to extend later.
        """

        if not assignment.meta.has_field(fieldname):
            return None

        return assignment.get(fieldname)

    def validate_progress_date(self):
        if not self.progress_date:
            frappe.throw(
                _("Progress Date is required.")
            )

    def validate_quran_progress(self):
        """
        At least one Quran Range is required.

        Child-table validation is also called explicitly here so these
        rules are enforced by the parent progress document.
        """

        new_memorization = self.get(
            "new_memorization"
        ) or []

        revision = self.get(
            "revision"
        ) or []

        if not new_memorization and not revision:
            frappe.throw(
                _(
                    "At least one New Memorization or "
                    "Revision range is required."
                )
            )

        self.validate_quran_range_rows(
            new_memorization,
            _("New Memorization"),
        )

        self.validate_quran_range_rows(
            revision,
            _("Revision"),
        )

    def validate_quran_range_rows(
        self,
        rows,
        table_label,
    ):
        for row in rows:
            try:
                row.validate()

            except frappe.ValidationError as exc:
                frappe.throw(
                    _(
                        "{0}, row {1}: {2}"
                    ).format(
                        table_label,
                        row.idx or 1,
                        str(exc),
                    )
                )

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