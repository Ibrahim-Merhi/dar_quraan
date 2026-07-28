# Copyright (c) 2026, ITIHAD
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import getdate, nowdate, validate_email_address


class DarQuraanStudent(Document):
    def autoname(self):
        naming_series = self.naming_series or "DQS-.YYYY.-.#####"
        self.name = make_autoname(naming_series)

    def before_validate(self):
        self.normalize_values()
        self.set_student_name()
        self.set_student_code()
        self.set_preferred_contact_number()

    def validate(self):
        self.validate_student_code()
        self.validate_unique_student_code()
        self.validate_legacy_student_id()
        self.validate_dates()
        self.validate_email()
        self.validate_duplicate_student()
        self.validate_branch()
        self.validate_teacher()
        self.validate_halaqa()
        self.validate_quran_profile()
        self.apply_status_rules()

    # -------------------------------------------------------------------------
    # Normalization
    # -------------------------------------------------------------------------

    def normalize_values(self):
        self.first_name = self.clean_text(self.first_name)
        self.middle_name = self.clean_text(self.middle_name)
        self.last_name = self.clean_text(self.last_name)
        self.mother_name = self.clean_text(self.mother_name)
        self.english_name = self.clean_text(self.english_name)

        original_student_code = self.student_code

        self.student_code = self.normalize_code(self.student_code)

        if original_student_code and not self.student_code:
            frappe.throw(
        _(
            "Student Code must contain at least one letter or number."
        )
    )

        self.mobile_number = self.normalize_phone(self.mobile_number)
        self.home_number = self.normalize_phone(self.home_number)
        self.work_number = self.normalize_phone(self.work_number)
        self.father_number = self.normalize_phone(self.father_number)
        self.mother_number = self.normalize_phone(self.mother_number)
        self.whatsapp_number = self.normalize_phone(self.whatsapp_number)

        if self.email:
            self.email = self.email.strip().lower()

    @staticmethod
    def clean_text(value):
        if not value:
            return None

        return " ".join(str(value).strip().split())

    @staticmethod
    def normalize_code(value):
        if not value:
            return None

        value = str(value).strip().upper()
        value = re.sub(r"\s+", "-", value)
        value = re.sub(r"[^A-Z0-9\-_]", "", value)
        value = re.sub(r"-{2,}", "-", value)

        return value.strip("-_")

    @staticmethod
    def normalize_phone(value):
        if not value:
            return None

        value = str(value).strip()

        # Remove common visual separators while preserving a leading +
        value = re.sub(r"[\s\-\(\)\.]", "", value)

        if value.startswith("00"):
            value = f"+{value[2:]}"

        return value or None

    # -------------------------------------------------------------------------
    # Generated values
    # -------------------------------------------------------------------------

    def set_student_name(self):
        name_parts = [
            self.first_name,
            self.middle_name,
            self.last_name,
        ]

        self.student_name = " ".join(
            value for value in name_parts if value
        )

    def set_student_code(self):
        if self.student_code:
            return

        if self.name and not self.name.startswith("new-"):
            self.student_code = self.name

    def set_preferred_contact_number(self):
        self.preferred_contact_number = (
            self.mobile_number
            or self.whatsapp_number
            or self.father_number
            or self.mother_number
            or self.home_number
            or self.work_number
        )

    # -------------------------------------------------------------------------
    # Student validations
    # -------------------------------------------------------------------------

    def validate_student_code(self):
        if not self.student_code:
            frappe.throw(_("Student Code is required."))

        if len(self.student_code) < 3:
            frappe.throw(
                _("Student Code must contain at least 3 characters.")
            )

        if not re.fullmatch(r"[A-Z0-9][A-Z0-9\-_]*", self.student_code):
            frappe.throw(
                _(
                    "Student Code may contain only uppercase letters, "
                    "numbers, hyphens, and underscores."
                )
            )

    def validate_unique_student_code(self):
        existing_student = frappe.db.exists(
            "Dar Quraan Student",
            {
                "student_code": self.student_code,
                "name": ["!=", self.name],
            },
        )

        if existing_student:
            frappe.throw(
                _(
                    "Student Code {0} is already used by student {1}."
                ).format(
                    frappe.bold(self.student_code),
                    frappe.bold(existing_student),
                )
            )

    def validate_legacy_student_id(self):
        if not self.legacy_student_id:
            return

        if int(self.legacy_student_id) <= 0:
            frappe.throw(
                _("Legacy Student ID must be greater than zero.")
            )

        existing_student = frappe.db.exists(
            "Dar Quraan Student",
            {
                "legacy_student_id": self.legacy_student_id,
                "name": ["!=", self.name],
            },
        )

        if existing_student:
            frappe.throw(
                _(
                    "Legacy Student ID {0} is already linked to student {1}."
                ).format(
                    frappe.bold(self.legacy_student_id),
                    frappe.bold(existing_student),
                )
            )

    def validate_duplicate_student(self):
        if not self.first_name or not self.last_name or not self.date_of_birth:
            return

        filters = {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "date_of_birth": self.date_of_birth,
            "name": ["!=", self.name],
        }

        if self.middle_name:
            filters["middle_name"] = self.middle_name

        duplicate = frappe.db.exists(
            "Dar Quraan Student",
            filters,
        )

        if duplicate:
            frappe.throw(
                _(
                    "A student with the same name and Date of Birth "
                    "already exists: {0}."
                ).format(frappe.bold(duplicate))
            )

    # -------------------------------------------------------------------------
    # Date validations
    # -------------------------------------------------------------------------

    def validate_dates(self):
        today = getdate(nowdate())

        if self.date_of_birth:
            date_of_birth = getdate(self.date_of_birth)

            if date_of_birth > today:
                frappe.throw(
                    _("Date of Birth cannot be in the future.")
                )

        if self.registration_date:
            registration_date = getdate(self.registration_date)

            if registration_date > today:
                frappe.throw(
                    _("Registration Date cannot be in the future.")
                )

            if self.date_of_birth:
                date_of_birth = getdate(self.date_of_birth)

                if registration_date < date_of_birth:
                    frappe.throw(
                        _(
                            "Registration Date cannot be earlier than "
                            "Date of Birth."
                        )
                    )

        if (
            self.legacy_created_at
            and self.legacy_updated_at
            and self.legacy_updated_at < self.legacy_created_at
        ):
            frappe.throw(
                _(
                    "Legacy Updated At cannot be earlier than "
                    "Legacy Created At."
                )
            )

    # -------------------------------------------------------------------------
    # Contact validations
    # -------------------------------------------------------------------------

    def validate_email(self):
        if not self.email:
            return

        if not validate_email_address(self.email):
            frappe.throw(
                _("Please enter a valid email address.")
            )

    # -------------------------------------------------------------------------
    # Organization validations
    # -------------------------------------------------------------------------

    def validate_branch(self):
        if not self.default_branch:
            return

        branch = frappe.db.get_value(
            "Dar Quraan Branch",
            self.default_branch,
            ["status"],
            as_dict=True,
        )

        if not branch:
            frappe.throw(
                _("The selected Default Branch does not exist.")
            )

        if branch.status != "Active":
            frappe.throw(
                _(
                    "The selected Default Branch must be Active. "
                    "Current status: {0}."
                ).format(frappe.bold(branch.status))
            )

    def validate_teacher(self):
        if not self.default_teacher:
            return

        teacher = frappe.db.get_value(
            "Dar Quraan Teacher",
            self.default_teacher,
            ["status"],
            as_dict=True,
        )

        if not teacher:
            frappe.throw(
                _("The selected Default Teacher does not exist.")
            )

        if teacher.status != "Active":
            frappe.throw(
                _(
                    "The selected Default Teacher must be Active. "
                    "Current status: {0}."
                ).format(frappe.bold(teacher.status))
            )

    def validate_halaqa(self):
        if not self.default_halaqa:
            return

        halaqa = frappe.db.get_value(
            "Dar Quraan Halaqa",
            self.default_halaqa,
            [
                "status",
                "branch",
                "mentor",
                "allow_new_enrollments",
            ],
            as_dict=True,
        )

        if not halaqa:
            frappe.throw(
                _("The selected Default Halaqa does not exist.")
            )

        if halaqa.status != "Active":
            frappe.throw(
                _(
                    "The selected Default Halaqa must be Active. "
                    "Current status: {0}."
                ).format(frappe.bold(halaqa.status))
            )

        if (
            self.default_branch
            and halaqa.branch
            and halaqa.branch != self.default_branch
        ):
            frappe.throw(
                _(
                    "Default Halaqa belongs to Branch {0}, "
                    "not the selected Default Branch {1}."
                ).format(
                    frappe.bold(halaqa.branch),
                    frappe.bold(self.default_branch),
                )
            )

        if (
            self.default_teacher
            and halaqa.mentor
            and halaqa.mentor != self.default_teacher
        ):
            frappe.throw(
                _(
                    "Default Halaqa mentor is {0}, "
                    "not the selected Default Teacher {1}."
                ).format(
                    frappe.bold(halaqa.mentor),
                    frappe.bold(self.default_teacher),
                )
            )

        if not halaqa.allow_new_enrollments:
            frappe.throw(
                _(
                    "The selected Default Halaqa does not allow "
                    "new student assignments."
                )
            )

        if not self.default_branch and halaqa.branch:
            self.default_branch = halaqa.branch

        if not self.default_teacher and halaqa.mentor:
            self.default_teacher = halaqa.mentor

    # -------------------------------------------------------------------------
    # Quran profile validations
    # -------------------------------------------------------------------------

    def validate_quran_profile(self):
        if self.study_track == "Qiraat" and not self.qiraat_method:
            frappe.throw(
                _("Qiraat Method is required when Study Track is Qiraat.")
            )

        if self.study_track != "Qiraat":
            self.qiraat_method = None

        if self.qiraat_method == "Other" and not self.notes:
            frappe.throw(
                _(
                    "Add the Qiraat method details in Notes "
                    "when Qiraat Method is Other."
                )
            )

        if not self.has_previous_ijazah:
            self.previous_ijazah_details = None

        if (
            self.has_previous_ijazah
            and not self.previous_ijazah_details
        ):
            frappe.throw(
                _(
                    "Previous Ijazah Details are required when "
                    "Has Previous Ijazah is enabled."
                )
            )

        if self.quran_status == "Mujaz" and not self.has_previous_ijazah:
            frappe.throw(
                _(
                    "Has Previous Ijazah must be enabled when "
                    "Quran Status is Mujaz."
                )
            )

    # -------------------------------------------------------------------------
    # Status rules
    # -------------------------------------------------------------------------

    def apply_status_rules(self):
        inactive_statuses = {
            "Inactive",
            "Suspended",
            "Withdrawn",
            "Graduated",
            "Deceased",
        }

        self.disabled = 1 if self.status in inactive_statuses else 0

        if self.status == "Graduated" and self.quran_status not in {
            "Hafiz",
            "Mujaz",
        }:
            frappe.throw(
                _(
                    "A Graduated student must have Quran Status "
                    "Hafiz or Mujaz."
                )
            )

        if self.status == "Deceased":
            self.default_teacher = None
            self.default_halaqa = None