import frappe
from frappe import _
from frappe.model.document import Document


class DarQuraanNextAssignment(Document):
    def validate(self):
        self.validate_student_assignment()
        self.fetch_assignment_context()
        self.validate_assignment_date()
        self.validate_quran_work()
        self.validate_sources()
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
                    "Student Assignment {0} does not have a Student."
                ).format(
                    self.student_assignment
                )
            )

        if not self.teacher:
            frappe.throw(
                _(
                    "Student Assignment {0} does not have a Teacher."
                ).format(
                    self.student_assignment
                )
            )

        if not self.halaqa:
            frappe.throw(
                _(
                    "Student Assignment {0} does not have a Halaqa."
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

    def validate_assignment_date(self):
        if not self.assignment_date:
            frappe.throw(
                _("Assignment Date is required.")
            )

    def validate_quran_work(self):
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
        for index, row in enumerate(
            rows,
            start=1,
        ):
            if isinstance(row, dict):
                row = frappe.get_doc(
                    {
                        "doctype": "Dar Quraan Quran Range",
                        **row,
                    }
                )
                row.idx = index

            try:
                row.validate()

            except frappe.ValidationError as exc:
                frappe.throw(
                    _(
                        "{0}, row {1}: {2}"
                    ).format(
                        table_label,
                        row.idx or index,
                        str(exc),
                    )
                )

    def validate_sources(self):
        if self.source_progress:
            self.validate_source_progress()

        if self.source_evaluation:
            self.validate_source_evaluation()

    def validate_source_progress(self):
        if not frappe.db.exists(
            "Dar Quraan Student Progress",
            self.source_progress,
        ):
            frappe.throw(
                _("Selected Source Progress does not exist.")
            )

        source_assignment = frappe.db.get_value(
            "Dar Quraan Student Progress",
            self.source_progress,
            "student_assignment",
        )

        if (
            source_assignment
            and source_assignment != self.student_assignment
        ):
            frappe.throw(
                _(
                    "Source Progress must belong to the same "
                    "Student Assignment."
                )
            )

    def validate_source_evaluation(self):
        if not frappe.db.exists(
            "Dar Quraan Evaluation",
            self.source_evaluation,
        ):
            frappe.throw(
                _("Selected Source Evaluation does not exist.")
            )

        source_assignment = frappe.db.get_value(
            "Dar Quraan Evaluation",
            self.source_evaluation,
            "student_assignment",
        )

        if (
            source_assignment
            and source_assignment != self.student_assignment
        ):
            frappe.throw(
                _(
                    "Source Evaluation must belong to the same "
                    "Student Assignment."
                )
            )

    @frappe.whitelist()
    def generate_from_source_progress(self):
        """
        Generate repeat/revision Quran work from a completed
        Student Progress record.

        Rules:
        - Repeat -> same range goes to New Memorization.
        - Needs Revision -> same range goes to Revision.
        - Good / Very Good / Excellent do not automatically
          generate a forward assignment yet.
        """

        if not self.source_progress:
            frappe.throw(
                _("Source Progress is required.")
            )

        progress = frappe.get_doc(
            "Dar Quraan Student Progress",
            self.source_progress,
        )

        if (
            progress.student_assignment
            != self.student_assignment
        ):
            frappe.throw(
                _(
                    "Source Progress must belong to the same "
                    "Student Assignment."
                )
            )

        if progress.status != "Completed":
            frappe.throw(
                _(
                    "Source Progress must be Completed before "
                    "generating the next assignment."
                )
            )

        progress_items = (
            progress.get("progress_items")
            or []
        )

        if not progress_items:
            frappe.throw(
                _(
                    "Source Progress does not contain any "
                    "Progress Items."
                )
            )

        # Clear existing generated Quran work before rebuilding it.
        self.set(
            "new_memorization",
            [],
        )

        self.set(
            "revision",
            [],
        )

        generated_new_memorization = 0
        generated_revision = 0

        for item in progress_items:
            result = self.get_row_value(
                item,
                "result",
            )

            if result == "Repeat":
                self.append(
                    "new_memorization",
                    {
                        "surah": self.get_row_value(
                            item,
                            "surah",
                        ),
                        "from_ayah": self.get_row_value(
                            item,
                            "from_ayah",
                        ),
                        "to_ayah": self.get_row_value(
                            item,
                            "to_ayah",
                        ),
                        "from_page": self.get_row_value(
                            item,
                            "from_page",
                        ),
                        "to_page": self.get_row_value(
                            item,
                            "to_page",
                        ),
                    },
                )

                generated_new_memorization += 1

            elif result == "Needs Revision":
                self.append(
                    "revision",
                    {
                        "surah": self.get_row_value(
                            item,
                            "surah",
                        ),
                        "from_ayah": self.get_row_value(
                            item,
                            "from_ayah",
                        ),
                        "to_ayah": self.get_row_value(
                            item,
                            "to_ayah",
                        ),
                        "from_page": self.get_row_value(
                            item,
                            "from_page",
                        ),
                        "to_page": self.get_row_value(
                            item,
                            "to_page",
                        ),
                    },
                )

                generated_revision += 1

        total_generated = (
            generated_new_memorization
            + generated_revision
        )

        if total_generated == 0:
            frappe.throw(
                _(
                    "No Repeat or Needs Revision items were found. "
                    "A forward assignment should be entered manually "
                    "for now."
                )
            )

        # Validate the generated ranges immediately.
        self.validate_quran_work()

        return {
            "new_memorization": (
                generated_new_memorization
            ),
            "revision": generated_revision,
            "total": total_generated,
        }

    def get_row_value(
        self,
        row,
        fieldname,
    ):
        if isinstance(row, dict):
            return row.get(fieldname)

        return row.get(fieldname)

    def validate_status(self):
        allowed_statuses = {
            "Draft",
            "Ready",
            "Assigned",
            "Completed",
            "Cancelled",
        }

        if not self.status:
            self.status = "Draft"

        if self.status not in allowed_statuses:
            frappe.throw(
                _(
                    "Status must be Draft, Ready, Assigned, "
                    "Completed, or Cancelled."
                )
            )