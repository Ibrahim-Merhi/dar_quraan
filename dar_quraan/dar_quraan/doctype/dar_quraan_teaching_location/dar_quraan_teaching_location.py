import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class DarQuraanTeachingLocation(Document):
    def validate(self):
        self.normalize_values()
        self.validate_location_code()
        self.validate_unique_location_code()
        self.validate_unique_location_name()
        self.validate_capacity()
        self.validate_branch()
        self.validate_location_type()
        self.validate_physical_location()
        self.apply_inactive_rules()

    def normalize_values(self):
        if self.location_code:
            self.location_code = self.location_code.strip().upper()

        if self.location_name:
            self.location_name = self.location_name.strip()

        if self.arabic_name:
            self.arabic_name = self.arabic_name.strip()

        if self.city:
            self.city = self.city.strip()

        if self.area:
            self.area = self.area.strip()

        if self.contact_person:
            self.contact_person = self.contact_person.strip()

        if self.contact_number:
            self.contact_number = self.contact_number.strip()

        if self.google_maps_link:
            self.google_maps_link = self.google_maps_link.strip()

    def validate_location_code(self):
        if not self.location_code:
            return

        if not re.fullmatch(r"[A-Z0-9_-]+", self.location_code):
            frappe.throw(
                _(
                    "Location Code may contain only uppercase letters, "
                    "numbers, hyphens, and underscores."
                )
            )

    def validate_unique_location_code(self):
        if not self.location_code:
            return

        existing_location = frappe.db.exists(
            "Dar Quraan Teaching Location",
            {
                "location_code": self.location_code,
                "name": ["!=", self.name or ""],
            },
        )

        if existing_location:
            frappe.throw(
                _("Location Code {0} is already used by location {1}.").format(
                    frappe.bold(self.location_code),
                    frappe.bold(existing_location),
                )
            )

    def validate_unique_location_name(self):
        if not self.location_name or not self.branch:
            return

        existing_location = frappe.db.exists(
            "Dar Quraan Teaching Location",
            {
                "location_name": self.location_name,
                "branch": self.branch,
                "name": ["!=", self.name or ""],
            },
        )

        if existing_location:
            frappe.throw(
                _("Location Name {0} already exists in branch {1}.").format(
                    frappe.bold(self.location_name),
                    frappe.bold(self.branch),
                )
            )

    def validate_capacity(self):
        if self.capacity is not None and cint(self.capacity) < 0:
            frappe.throw(_("Capacity cannot be negative."))

    def validate_branch(self):
        if not self.branch:
            return

        branch_status = frappe.db.get_value(
            "Dar Quraan Branch",
            self.branch,
            "status",
        )

        if branch_status is None:
            frappe.throw(_("The selected Dar Quraan Branch does not exist."))

        if branch_status != "Active":
            frappe.throw(
                _("Teaching locations cannot be linked to an inactive branch.")
            )

    def validate_location_type(self):
        if self.location_type in ("Branch", "Classroom"):
            if not self.inside_branch_premises:
                frappe.throw(
                    _(
                        "Inside Branch Premises must be enabled for "
                        "Branch and Classroom locations."
                    )
                )

        if self.location_type == "Online":
            self.inside_branch_premises = 0

    def validate_physical_location(self):
        if self.location_type == "Online":
            return

        if not self.city and not self.address:
            frappe.throw(
                _(
                    "Enter at least a City or Address for a physical "
                    "teaching location."
                )
            )

    def apply_inactive_rules(self):
        if self.status == "Inactive":
            self.allow_halaqas = 0