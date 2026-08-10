import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from dar_quraan.dar_quraan.services.quran_state import (
    update_state_from_progress,
)


class DarQuraanStudentProgress(Document):
    def validate(self):
        self.validate_student_assignment()
        self.fetch_assignment_context()
        self.validate_progress_date()
        self.validate_quran_progress()
        self.validate_progress_items()
        self.validate_status()

    def on_update(self):
        """
        Update the student's Quran State only when this
        progress record reaches Completed status.

        The service itself checks the status, so calling it
        from on_update is safe for Draft and Cancelled records.
        """
        update_state_from_progress(self)

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

    def validate_progress_date(self):
        if not self.progress_date:
            frappe.throw(
                _("Progress Date is required.")
            )

    def validate_quran_progress(self):
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
            row = self.get_quran_range_document(
                row,
                index,
            )

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

    def get_quran_range_document(
        self,
        row,
        index,
    ):
        if not isinstance(row, dict):
            return row

        row_data = dict(row)

        row_data.setdefault(
            "doctype",
            "Dar Quraan Quran Range",
        )

        child = frappe.get_doc(
            row_data
        )

        child.idx = index

        return child

    def validate_progress_items(self):
        progress_items = self.get(
            "progress_items"
        ) or []

        if not progress_items:
            return

        normalized_items = []

        for index, row in enumerate(
            progress_items,
            start=1,
        ):
            row = self.get_progress_item_document(
                row,
                index,
            )

            try:
                row.validate()

            except frappe.ValidationError as exc:
                frappe.throw(
                    _(
                        "Progress Item, row {0}: {1}"
                    ).format(
                        row.idx or index,
                        str(exc),
                    )
                )

            self.validate_progress_item_against_assignment(
                row
            )

            normalized_items.append(
                row
            )

        self.set(
            "progress_items",
            normalized_items,
        )

    def get_progress_item_document(
        self,
        row,
        index,
    ):
        if not isinstance(row, dict):
            return row

        row_data = dict(row)

        row_data.setdefault(
            "doctype",
            "Dar Quraan Progress Item",
        )

        child = frappe.get_doc(
            row_data
        )

        child.idx = index

        return child

    def validate_progress_item_against_assignment(
        self,
        item,
    ):
        progress_type = self.get_row_value(
            item,
            "progress_type",
        )

        if progress_type == "New Memorization":
            assigned_ranges = self.get(
                "new_memorization"
            ) or []

        elif progress_type == "Revision":
            assigned_ranges = self.get(
                "revision"
            ) or []

        else:
            frappe.throw(
                _(
                    "Invalid Progress Type in Progress Item "
                    "row {0}."
                ).format(
                    self.get_row_value(
                        item,
                        "idx",
                    ) or 1
                )
            )

        if not assigned_ranges:
            frappe.throw(
                _(
                    "Progress Item row {0} is marked as {1}, "
                    "but no {1} range exists in this progress "
                    "record."
                ).format(
                    self.get_row_value(
                        item,
                        "idx",
                    ) or 1,
                    progress_type,
                )
            )

        for assigned in assigned_ranges:
            if self.progress_item_fits_range(
                item,
                assigned,
            ):
                return

        frappe.throw(
            _(
                "Progress Item row {0} does not fall inside "
                "any assigned {1} Quran range."
            ).format(
                self.get_row_value(
                    item,
                    "idx",
                ) or 1,
                progress_type,
            )
        )

    def progress_item_fits_range(
        self,
        item,
        assigned,
    ):
        if (
            self.get_row_value(
                item,
                "surah",
            )
            != self.get_row_value(
                assigned,
                "surah",
            )
        ):
            return False

        if (
            cint(
                self.get_row_value(
                    item,
                    "from_ayah",
                )
            )
            < cint(
                self.get_row_value(
                    assigned,
                    "from_ayah",
                )
            )
        ):
            return False

        if (
            cint(
                self.get_row_value(
                    item,
                    "to_ayah",
                )
            )
            > cint(
                self.get_row_value(
                    assigned,
                    "to_ayah",
                )
            )
        ):
            return False

        if (
            cint(
                self.get_row_value(
                    item,
                    "from_page",
                )
            )
            < cint(
                self.get_row_value(
                    assigned,
                    "from_page",
                )
            )
        ):
            return False

        if (
            cint(
                self.get_row_value(
                    item,
                    "to_page",
                )
            )
            > cint(
                self.get_row_value(
                    assigned,
                    "to_page",
                )
            )
        ):
            return False

        return True

    def get_row_value(
        self,
        row,
        fieldname,
    ):
        if isinstance(row, dict):
            return row.get(
                fieldname
            )

        return row.get(
            fieldname
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