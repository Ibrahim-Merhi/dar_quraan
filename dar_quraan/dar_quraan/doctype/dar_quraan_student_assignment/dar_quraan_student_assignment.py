# Copyright (c) 2026, ITIHAD
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import cint, get_datetime, getdate, nowdate


class DarQuraanStudentAssignment(Document):
    """
    Historical assignment of a Dar Quraan student to a branch, teacher,
    teaching location, and optionally a Halaqa.

    The assignment preserves history. It should not be deleted when a student
    transfers, completes, or leaves a Halaqa.
    """

    def autoname(self):
        naming_series = self.naming_series or "DQSA-.YYYY.-.#####"
        self.name = make_autoname(naming_series)

    def before_validate(self):
        self.normalize_values()
        self.fetch_reference_values()
        self.set_effective_dates()
        self.set_current_assignment()

    def validate(self):
        self.validate_student()
        self.validate_branch()
        self.validate_teaching_location()
        self.validate_teacher()
        self.validate_halaqa()
        self.validate_academic_year()
        self.validate_academic_term()
        self.validate_assignment_dates()
        self.validate_effective_dates()
        self.validate_assignment_type()
        self.validate_status()
        self.validate_active_primary_assignment()
        self.validate_overlapping_primary_assignment()
        self.validate_legacy_fields()

        # Recalculate after all validations and fetched values.
        self.set_current_assignment()

    def after_insert(self):
        self.sync_student_defaults()

    def on_update(self):
        self.sync_student_defaults()

    def on_trash(self):
        self.validate_deletion()

     # -------------------------------------------------------------------------
    # Normalization and generated values
    # -------------------------------------------------------------------------

    def normalize_values(self):
        self.assignment_notes = self.clean_text(
            self.assignment_notes
        )
        self.transfer_reason = self.clean_text(
            self.transfer_reason
        )
        self.riwayah = self.clean_text(
            self.riwayah
        )

        if self.status:
            self.status = self.status.strip()

        if self.assignment_type:
            self.assignment_type = (
                self.assignment_type.strip()
            )

        if self.study_track:
            self.study_track = self.study_track.strip()

    @staticmethod
    def clean_text(value):
        if not value:
            return None

        return " ".join(
            str(value).strip().split()
        )

    def fetch_reference_values(self):
        # -------------------------------------------------------------
        # Student
        # -------------------------------------------------------------
        if self.student:
            student = frappe.db.get_value(
                "Dar Quraan Student",
                self.student,
                [
                    "student_name",
                    "study_track",
                    "current_riwayah",
                ],
                as_dict=True,
            )

            if student:
                if student.student_name:
                    self.student_name = student.student_name

                if student.study_track:
                    self.study_track = student.study_track

                if student.current_riwayah:
                    self.riwayah = student.current_riwayah

        # -------------------------------------------------------------
        # Halaqa
        # -------------------------------------------------------------
        if self.halaqa:
            halaqa_values = frappe.db.get_value(
                "Dar Quraan Halaqa",
                self.halaqa,
                [
                    "branch",
                    "mentor",
                    "teaching_location",
                ],
                as_dict=True,
            )

            if halaqa_values:
                if (
                    not self.branch
                    and halaqa_values.branch
                ):
                    self.branch = halaqa_values.branch

                if (
                    not self.teacher
                    and halaqa_values.mentor
                ):
                    self.teacher = halaqa_values.mentor

                if (
                    not self.teaching_location
                    and halaqa_values.teaching_location
                ):
                    self.teaching_location = (
                        halaqa_values.teaching_location
                    )
    def set_effective_dates(self):
        """
        Keep the effective datetime period synchronized
        with the assignment Start Date and End Date.
        """

        if self.start_date:
            self.effective_from = (
                f"{self.start_date} 00:00:00"
            )
        else:
            self.effective_from = None

        if self.end_date:
            self.effective_to = (
                f"{self.end_date} 23:59:59"
            )
        else:
            self.effective_to = None

    def set_current_assignment(self):
        self.is_current_assignment = 0

        if self.status != "Active":
            return

        if not self.start_date:
            return

        today = getdate(nowdate())
        start_date = getdate(self.start_date)

        if start_date > today:
            return

        if (
            self.end_date
            and getdate(self.end_date) < today
        ):
            return

        self.is_current_assignment = 1

    # -------------------------------------------------------------------------
    # Student validation
    # -------------------------------------------------------------------------

    def validate_student(self):
        if not self.student:
            frappe.throw(_("Student is required."))

        student = frappe.db.get_value(
            "Dar Quraan Student",
            self.student,
            [
                "student_name",
                "status",
                "disabled",
                "study_track",
                "current_riwayah",
            ],
            as_dict=True,
        )

        if not student:
            frappe.throw(
                _("Student {0} does not exist.").format(
                    frappe.bold(self.student)
                )
            )

        self.student_name = student.student_name

        if student.status != "Active":
            frappe.throw(
                _(
                    "Student {0} must be Active before an assignment "
                    "can be activated. Current status: {1}."
                ).format(
                    frappe.bold(
                        student.student_name or self.student
                    ),
                    frappe.bold(student.status),
                )
            )

        if cint(student.disabled):
            frappe.throw(
                _("Disabled students cannot be assigned.")
            )

    # -------------------------------------------------------------------------
    # Organizational validations
    # -------------------------------------------------------------------------

    def validate_branch(self):
        if not self.branch:
            frappe.throw(_("Branch is required."))

        branch = frappe.db.get_value(
            "Dar Quraan Branch",
            self.branch,
            ["status"],
            as_dict=True,
        )

        if not branch:
            frappe.throw(
                _("Branch {0} does not exist.").format(
                    frappe.bold(self.branch)
                )
            )

        if branch.status != "Active":
            frappe.throw(
                _(
                    "Branch {0} must be Active. Current status: {1}."
                ).format(
                    frappe.bold(self.branch),
                    frappe.bold(branch.status),
                )
            )

    def validate_teaching_location(self):
        if not self.teaching_location:
            return

        location = frappe.db.get_value(
            "Dar Quraan Teaching Location",
            self.teaching_location,
            [
                "status",
                "branch",
            ],
            as_dict=True,
        )

        if not location:
            frappe.throw(
                _("Teaching Location {0} does not exist.").format(
                    frappe.bold(self.teaching_location)
                )
            )

        if location.status != "Active":
            frappe.throw(
                _(
                    "Teaching Location {0} must be Active. "
                    "Current status: {1}."
                ).format(
                    frappe.bold(self.teaching_location),
                    frappe.bold(location.status),
                )
            )

        if location.branch and location.branch != self.branch:
            frappe.throw(
                _(
                    "Teaching Location {0} belongs to Branch {1}, "
                    "not the selected Branch {2}."
                ).format(
                    frappe.bold(self.teaching_location),
                    frappe.bold(location.branch),
                    frappe.bold(self.branch),
                )
            )

    def validate_teacher(self):
        if not self.teacher:
            frappe.throw(_("Teacher is required."))

        if not frappe.db.exists(
            "Dar Quraan Teacher",
            self.teacher,
        ):
            frappe.throw(
                _("Teacher {0} does not exist.").format(
                    frappe.bold(self.teacher)
                )
            )

        teacher_meta = frappe.get_meta("Dar Quraan Teacher")

        # Only query fields that actually exist in Dar Quraan Teacher.
        fields = []

        for fieldname in (
            "status",
            "disabled",
            "is_active",
            "enabled",
            "branch",
        ):
            if teacher_meta.has_field(fieldname):
                fields.append(fieldname)

        teacher = frappe._dict()

        if fields:
            teacher = (
                frappe.db.get_value(
                    "Dar Quraan Teacher",
                    self.teacher,
                    fields,
                    as_dict=True,
                )
                or frappe._dict()
            )

        # -------------------------------------------------------------
        # Active / inactive validation
        # -------------------------------------------------------------

        if teacher_meta.has_field("status"):
            if teacher.get("status") != "Active":
                frappe.throw(
                    _(
                        "Teacher {0} must be Active. Current status: {1}."
                    ).format(
                        frappe.bold(self.teacher),
                        frappe.bold(
                            teacher.get("status") or _("Not Set")
                        ),
                    )
                )

        elif teacher_meta.has_field("disabled"):
            if cint(teacher.get("disabled")):
                frappe.throw(
                    _("Teacher {0} is disabled.").format(
                        frappe.bold(self.teacher)
                    )
                )

        elif teacher_meta.has_field("is_active"):
            if not cint(teacher.get("is_active")):
                frappe.throw(
                    _("Teacher {0} must be Active.").format(
                        frappe.bold(self.teacher)
                    )
                )

        elif teacher_meta.has_field("enabled"):
            if not cint(teacher.get("enabled")):
                frappe.throw(
                    _("Teacher {0} must be enabled.").format(
                        frappe.bold(self.teacher)
                    )
                )

        # -------------------------------------------------------------
        # Branch validation
        # Only enforce this if Teacher actually has a branch field.
        # -------------------------------------------------------------

        if teacher_meta.has_field("branch"):
            teacher_branch = teacher.get("branch")

            if (
                teacher_branch
                and self.branch
                and teacher_branch != self.branch
            ):
                frappe.throw(
                    _(
                        "Teacher {0} belongs to Branch {1}, "
                        "not the selected Branch {2}."
                    ).format(
                        frappe.bold(self.teacher),
                        frappe.bold(teacher_branch),
                        frappe.bold(self.branch),
                    )
                )

    def validate_halaqa(self):
        if not self.halaqa:
            return

        halaqa = frappe.db.get_value(
            "Dar Quraan Halaqa",
            self.halaqa,
            [
                "status",
                "branch",
                "mentor",
                "teaching_location",
                "academic_year",
                "academic_term",
                "allow_new_enrollments",
            ],
            as_dict=True,
        )

        if not halaqa:
            frappe.throw(
                _("Halaqa {0} does not exist.").format(
                    frappe.bold(self.halaqa)
                )
            )

        if halaqa.status != "Active":
            frappe.throw(
                _(
                    "Halaqa {0} must be Active. Current status: {1}."
                ).format(
                    frappe.bold(self.halaqa),
                    frappe.bold(halaqa.status),
                )
            )

        if halaqa.branch and halaqa.branch != self.branch:
            frappe.throw(
                _(
                    "Halaqa {0} belongs to Branch {1}, "
                    "not the selected Branch {2}."
                ).format(
                    frappe.bold(self.halaqa),
                    frappe.bold(halaqa.branch),
                    frappe.bold(self.branch),
                )
            )

        if halaqa.mentor and halaqa.mentor != self.teacher:
            frappe.throw(
                _(
                    "Halaqa {0} is assigned to Teacher {1}, "
                    "not the selected Teacher {2}."
                ).format(
                    frappe.bold(self.halaqa),
                    frappe.bold(halaqa.mentor),
                    frappe.bold(self.teacher),
                )
            )

        if (
            self.teaching_location
            and halaqa.teaching_location
            and halaqa.teaching_location != self.teaching_location
        ):
            frappe.throw(
                _(
                    "Halaqa {0} uses Teaching Location {1}, "
                    "not the selected Teaching Location {2}."
                ).format(
                    frappe.bold(self.halaqa),
                    frappe.bold(halaqa.teaching_location),
                    frappe.bold(self.teaching_location),
                )
            )

        if (
            halaqa.academic_year
            and self.academic_year
            and halaqa.academic_year != self.academic_year
        ):
            frappe.throw(
                _(
                    "Halaqa {0} belongs to Academic Year {1}, "
                    "not {2}."
                ).format(
                    frappe.bold(self.halaqa),
                    frappe.bold(halaqa.academic_year),
                    frappe.bold(self.academic_year),
                )
            )

        if (
            halaqa.academic_term
            and self.academic_term
            and halaqa.academic_term != self.academic_term
        ):
            frappe.throw(
                _(
                    "Halaqa {0} belongs to Academic Term {1}, "
                    "not {2}."
                ).format(
                    frappe.bold(self.halaqa),
                    frappe.bold(halaqa.academic_term),
                    frappe.bold(self.academic_term),
                )
            )

        if (
            self.is_new()
            and self.status == "Active"
            and not cint(halaqa.allow_new_enrollments)
        ):
            frappe.throw(
                _(
                    "Halaqa {0} does not currently allow new "
                    "student assignments."
                ).format(
                    frappe.bold(self.halaqa)
                )
            )
    # -------------------------------------------------------------------------
    # Academic period validations
    # -------------------------------------------------------------------------

    def validate_academic_year(self):
        if not self.academic_year:
            frappe.throw(_("Academic Year is required."))

        academic_year = frappe.db.get_value(
            "Dar Quraan Academic Year",
            self.academic_year,
            [
                "status",
                "start_date",
                "end_date",
            ],
            as_dict=True,
        )

        if not academic_year:
            frappe.throw(
                _("Academic Year {0} does not exist.").format(
                    frappe.bold(self.academic_year)
                )
            )

        if academic_year.status not in {"Active", "Planned"}:
            frappe.throw(
                _(
                    "Academic Year {0} cannot be used because its "
                    "status is {1}."
                ).format(
                    frappe.bold(self.academic_year),
                    frappe.bold(academic_year.status),
                )
            )

        if (
            self.start_date
            and academic_year.start_date
            and getdate(self.start_date) < getdate(academic_year.start_date)
        ):
            frappe.throw(
                _(
                    "Assignment Start Date cannot be earlier than "
                    "Academic Year start date {0}."
                ).format(
                    frappe.bold(academic_year.start_date)
                )
            )

        if (
            self.start_date
            and academic_year.end_date
            and getdate(self.start_date) > getdate(academic_year.end_date)
        ):
            frappe.throw(
                _(
                    "Assignment Start Date cannot be later than "
                    "Academic Year end date {0}."
                ).format(
                    frappe.bold(academic_year.end_date)
                )
            )

        if (
            self.end_date
            and academic_year.end_date
            and getdate(self.end_date) > getdate(academic_year.end_date)
        ):
            frappe.throw(
                _(
                    "Assignment End Date cannot be later than "
                    "Academic Year end date {0}."
                ).format(
                    frappe.bold(academic_year.end_date)
                )
            )

        if (
            self.end_date
            and academic_year.start_date
            and getdate(self.end_date) < getdate(academic_year.start_date)
        ):
            frappe.throw(
                _(
                    "Assignment End Date cannot be earlier than "
                    "Academic Year start date {0}."
                ).format(
                    frappe.bold(academic_year.start_date)
                )
            )

    def validate_academic_term(self):
        if not self.academic_term:
            return

        academic_term = frappe.db.get_value(
            "Dar Quraan Academic Term",
            self.academic_term,
            [
                "status",
                "academic_year",
                "start_date",
                "end_date",
            ],
            as_dict=True,
        )

        if not academic_term:
            frappe.throw(
                _("Academic Term {0} does not exist.").format(
                    frappe.bold(self.academic_term)
                )
            )

        if academic_term.academic_year != self.academic_year:
            frappe.throw(
                _(
                    "Academic Term {0} belongs to Academic Year {1}, "
                    "not the selected Academic Year {2}."
                ).format(
                    frappe.bold(self.academic_term),
                    frappe.bold(academic_term.academic_year),
                    frappe.bold(self.academic_year),
                )
            )

        if academic_term.status not in {"Active", "Planned"}:
            frappe.throw(
                _(
                    "Academic Term {0} cannot be used because its "
                    "status is {1}."
                ).format(
                    frappe.bold(self.academic_term),
                    frappe.bold(academic_term.status),
                )
            )

        if (
            self.start_date
            and academic_term.start_date
            and getdate(self.start_date) < getdate(academic_term.start_date)
        ):
            frappe.throw(
                _(
                    "Assignment Start Date cannot be earlier than "
                    "Academic Term start date {0}."
                ).format(
                    frappe.bold(academic_term.start_date)
                )
            )

        if (
            self.start_date
            and academic_term.end_date
            and getdate(self.start_date) > getdate(academic_term.end_date)
        ):
            frappe.throw(
                _(
                    "Assignment Start Date cannot be later than "
                    "Academic Term end date {0}."
                ).format(
                    frappe.bold(academic_term.end_date)
                )
            )

        if (
            self.end_date
            and academic_term.end_date
            and getdate(self.end_date) > getdate(academic_term.end_date)
        ):
            frappe.throw(
                _(
                    "Assignment End Date cannot be later than "
                    "Academic Term end date {0}."
                ).format(
                    frappe.bold(academic_term.end_date)
                )
            )

        if (
            self.end_date
            and academic_term.start_date
            and getdate(self.end_date) < getdate(academic_term.start_date)
        ):
            frappe.throw(
                _(
                    "Assignment End Date cannot be earlier than "
                    "Academic Term start date {0}."
                ).format(
                    frappe.bold(academic_term.start_date)
                )
            )

    # -------------------------------------------------------------------------
    # Date and effective-period validations
    # -------------------------------------------------------------------------

    def validate_assignment_dates(self):
        if not self.start_date:
            frappe.throw(_("Start Date is required."))

        if self.end_date and getdate(self.end_date) < getdate(self.start_date):
            frappe.throw(
                _("End Date cannot be earlier than Start Date.")
            )

        if self.status == "Completed" and not self.end_date:
            frappe.throw(
                _("End Date is required for a Completed assignment.")
            )

        if self.status == "Cancelled" and self.is_current_assignment:
            frappe.throw(
                _("A Cancelled assignment cannot be current.")
            )

    def validate_effective_dates(self):
        if (
            self.effective_from
            and self.effective_to
            and get_datetime(self.effective_to)
            < get_datetime(self.effective_from)
        ):
            frappe.throw(
                _("Effective To cannot be earlier than Effective From.")
            )

        if (
            self.start_date
            and self.effective_from
            and getdate(self.effective_from) < getdate(self.start_date)
        ):
            frappe.throw(
                _(
                    "Effective From cannot be earlier than "
                    "the assignment Start Date."
                )
            )

        if (
            self.end_date
            and self.effective_to
            and getdate(self.effective_to) > getdate(self.end_date)
        ):
            frappe.throw(
                _(
                    "Effective To cannot be later than "
                    "the assignment End Date."
                )
            )

    # -------------------------------------------------------------------------
    # Assignment rules
    # -------------------------------------------------------------------------

    def validate_assignment_type(self):
        valid_types = {
            "Primary",
            "Temporary",
            "Transfer",
            "Substitute",
        }

        if self.assignment_type not in valid_types:
            frappe.throw(
                _(
                    "Assignment Type must be one of: {0}."
                ).format(", ".join(sorted(valid_types)))
            )

        if (
            self.assignment_type == "Transfer"
            and not self.transfer_reason
        ):
            frappe.throw(
                _("Transfer Reason is required for a Transfer assignment.")
            )

        if self.assignment_type != "Transfer":
            self.transfer_reason = None

    def validate_status(self):
        valid_statuses = {
            "Draft",
            "Active",
            "Completed",
            "Cancelled",
            "Suspended",
        }

        if self.status not in valid_statuses:
            frappe.throw(
                _("Invalid assignment status: {0}.").format(
                    frappe.bold(self.status)
                )
            )

        if self.status in {"Completed", "Cancelled", "Suspended"}:
            self.is_current_assignment = 0

    def validate_active_primary_assignment(self):
        if self.status != "Active":
            return

        if self.assignment_type != "Primary":
            return

        existing_assignment = frappe.db.get_value(
            "Dar Quraan Student Assignment",
            {
                "student": self.student,
                "assignment_type": "Primary",
                "status": "Active",
                "name": ["!=", self.name or ""],
            },
            "name",
        )

        if existing_assignment:
            frappe.throw(
                _(
                    "Student {0} already has an Active Primary "
                    "Assignment: {1}."
                ).format(
                    frappe.bold(self.student_name or self.student),
                    frappe.bold(existing_assignment),
                )
            )

    def validate_overlapping_primary_assignment(self):
        if self.assignment_type != "Primary":
            return

        if self.status in {"Cancelled", "Draft"}:
            return

        new_start = getdate(self.start_date)
        new_end = (
            getdate(self.end_date)
            if self.end_date
            else getdate("9999-12-31")
        )

        existing_assignments = frappe.get_all(
            "Dar Quraan Student Assignment",
            filters={
                "student": self.student,
                "assignment_type": "Primary",
                "status": ["in", ["Active", "Completed", "Suspended"]],
                "name": ["!=", self.name or ""],
            },
            fields=[
                "name",
                "start_date",
                "end_date",
            ],
        )

        for assignment in existing_assignments:
            if not assignment.start_date:
                continue

            existing_start = getdate(assignment.start_date)
            existing_end = (
                getdate(assignment.end_date)
                if assignment.end_date
                else getdate("9999-12-31")
            )

            periods_overlap = (
                new_start <= existing_end
                and new_end >= existing_start
            )

            if periods_overlap:
                frappe.throw(
                    _(
                        "The assignment period overlaps with Primary "
                        "Assignment {0}, from {1} to {2}."
                    ).format(
                        frappe.bold(assignment.name),
                        frappe.bold(assignment.start_date),
                        frappe.bold(
                            assignment.end_date or _("Open-ended")
                        ),
                    )
                )

    # -------------------------------------------------------------------------
    # Legacy validation
    # -------------------------------------------------------------------------

    def validate_legacy_fields(self):
        legacy_integer_fields = {
            "legacy_assignment_id": _("Legacy Assignment ID"),
            "legacy_student_id": _("Legacy Student ID"),
            "legacy_center_id": _("Legacy Center ID"),
            "legacy_teacher_id": _("Legacy Teacher ID"),
        }

        for fieldname, label in legacy_integer_fields.items():
            value = self.get(fieldname)

            if value is None or value == "":
                continue

            if cint(value) < 0:
                frappe.throw(
                    _("{0} cannot be negative.").format(label)
                )

        if (
            self.legacy_created_at
            and self.legacy_updated_at
            and get_datetime(self.legacy_updated_at)
            < get_datetime(self.legacy_created_at)
        ):
            frappe.throw(
                _(
                    "Legacy Updated At cannot be earlier than "
                    "Legacy Created At."
                )
            )

        if self.legacy_assignment_id:
            duplicate = frappe.db.get_value(
                "Dar Quraan Student Assignment",
                {
                    "legacy_assignment_id": self.legacy_assignment_id,
                    "name": ["!=", self.name or ""],
                },
                "name",
            )

            if duplicate:
                frappe.throw(
                    _(
                        "Legacy Assignment ID {0} is already used by "
                        "Student Assignment {1}."
                    ).format(
                        frappe.bold(self.legacy_assignment_id),
                        frappe.bold(duplicate),
                    )
                )

    # -------------------------------------------------------------------------
    # Student summary synchronization
    # -------------------------------------------------------------------------

    def sync_student_defaults(self):
        """
        Update the Student summary only from a current Active Primary
        Assignment.

        Historical assignments remain unchanged.
        """

        if not self.student:
            return

        if (
            self.status == "Active"
            and self.assignment_type == "Primary"
            and cint(self.is_current_assignment)
        ):
            frappe.db.set_value(
                "Dar Quraan Student",
                self.student,
                {
                    "default_branch": self.branch,
                    "default_teacher": self.teacher,
                    "default_halaqa": self.halaqa,
                },
                update_modified=False,
            )

            return

        self.restore_student_defaults_from_current_assignment()

    def restore_student_defaults_from_current_assignment(self):
        """
        When this assignment is completed, suspended, cancelled, or no longer
        current, use another current Primary Assignment if one exists.
        Otherwise, clear only defaults that still belong to this assignment.
        """

        current_assignment = frappe.db.get_value(
            "Dar Quraan Student Assignment",
            {
                "student": self.student,
                "assignment_type": "Primary",
                "status": "Active",
                "is_current_assignment": 1,
                "name": ["!=", self.name or ""],
            },
            [
                "branch",
                "teacher",
                "halaqa",
            ],
            as_dict=True,
            order_by="start_date desc",
        )

        if current_assignment:
            frappe.db.set_value(
                "Dar Quraan Student",
                self.student,
                {
                    "default_branch": current_assignment.branch,
                    "default_teacher": current_assignment.teacher,
                    "default_halaqa": current_assignment.halaqa,
                },
                update_modified=False,
            )
            return

        student = frappe.db.get_value(
            "Dar Quraan Student",
            self.student,
            [
                "default_branch",
                "default_teacher",
                "default_halaqa",
            ],
            as_dict=True,
        )

        if not student:
            return

        values_to_clear = {}

        if student.default_branch == self.branch:
            values_to_clear["default_branch"] = None

        if student.default_teacher == self.teacher:
            values_to_clear["default_teacher"] = None

        if student.default_halaqa == self.halaqa:
            values_to_clear["default_halaqa"] = None

        if values_to_clear:
            frappe.db.set_value(
                "Dar Quraan Student",
                self.student,
                values_to_clear,
                update_modified=False,
            )

    # -------------------------------------------------------------------------
    # Deletion protection
    # -------------------------------------------------------------------------

    def validate_deletion(self):
        if self.status not in {"Draft", "Cancelled"}:
            frappe.throw(
                _(
                    "Only Draft or Cancelled Student Assignments "
                    "can be deleted. Use Completed to preserve history."
                )
            )