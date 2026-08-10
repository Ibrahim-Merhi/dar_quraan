import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class DarQuraanQuranRange(Document):
    def validate(self):
        self.validate_surah()
        self.validate_ayah_range()
        self.validate_page_range()
        self.calculate_counts()

    def get_surah_data(self):
        if not self.surah:
            frappe.throw(
                _("Surah is required.")
            )

        surah = frappe.db.get_value(
            "Dar Quraan Surah",
            self.surah,
            [
                "ayah_count",
                "start_page",
                "end_page",
                "is_active",
            ],
            as_dict=True,
        )

        if not surah:
            frappe.throw(
                _("Selected Surah does not exist.")
            )

        return surah

    def validate_surah(self):
        surah = self.get_surah_data()

        if not surah.is_active:
            frappe.throw(
                _("Selected Surah is inactive.")
            )

    def validate_ayah_range(self):
        surah = self.get_surah_data()

        from_ayah = cint(self.from_ayah)
        to_ayah = cint(self.to_ayah)
        maximum_ayah = cint(
            surah.ayah_count
        )

        if from_ayah < 1:
            frappe.throw(
                _("From Ayah must be greater than zero.")
            )

        if to_ayah < 1:
            frappe.throw(
                _("To Ayah must be greater than zero.")
            )

        if from_ayah > maximum_ayah:
            frappe.throw(
                _(
                    "From Ayah cannot exceed {0} "
                    "for the selected Surah."
                ).format(maximum_ayah)
            )

        if to_ayah > maximum_ayah:
            frappe.throw(
                _(
                    "To Ayah cannot exceed {0} "
                    "for the selected Surah."
                ).format(maximum_ayah)
            )

        if to_ayah < from_ayah:
            frappe.throw(
                _("To Ayah cannot be before From Ayah.")
            )

    def validate_page_range(self):
        surah = self.get_surah_data()

        from_page = cint(self.from_page)
        to_page = cint(self.to_page)

        start_page = cint(
            surah.start_page
        )

        end_page = cint(
            surah.end_page
        )

        if from_page < start_page:
            frappe.throw(
                _(
                    "From Page cannot be before page {0} "
                    "for the selected Surah."
                ).format(start_page)
            )

        if from_page > end_page:
            frappe.throw(
                _(
                    "From Page cannot exceed page {0} "
                    "for the selected Surah."
                ).format(end_page)
            )

        if to_page < start_page:
            frappe.throw(
                _(
                    "To Page cannot be before page {0} "
                    "for the selected Surah."
                ).format(start_page)
            )

        if to_page > end_page:
            frappe.throw(
                _(
                    "To Page cannot exceed page {0} "
                    "for the selected Surah."
                ).format(end_page)
            )

        if to_page < from_page:
            frappe.throw(
                _("To Page cannot be before From Page.")
            )

    def calculate_counts(self):
        self.ayah_count = (
            cint(self.to_ayah)
            - cint(self.from_ayah)
            + 1
        )

        self.page_count = (
            cint(self.to_page)
            - cint(self.from_page)
            + 1
        )