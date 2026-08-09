import frappe
from frappe import _
from frappe.model.document import Document


class DarQuraanSurah(Document):
    def validate(self):
        self.validate_surah_number()
        self.validate_ayah_count()
        self.validate_global_ayah_range()
        self.validate_page_range()
        self.validate_juz_range()
        self.validate_duplicate_surah_number()

    def validate_surah_number(self):
        if not self.surah_number:
            frappe.throw(_("Surah Number is required."))

        if self.surah_number < 1 or self.surah_number > 114:
            frappe.throw(_("Surah Number must be between 1 and 114."))

    def validate_ayah_count(self):
        if not self.ayah_count:
            frappe.throw(_("Ayah Count is required."))

        if self.ayah_count < 1:
            frappe.throw(_("Ayah Count must be greater than zero."))

    def validate_global_ayah_range(self):
        if not self.start_global_ayah:
            frappe.throw(_("Start Global Ayah is required."))

        if not self.end_global_ayah:
            frappe.throw(_("End Global Ayah is required."))

        if self.start_global_ayah < 1:
            frappe.throw(_("Start Global Ayah must be greater than zero."))

        if self.end_global_ayah < self.start_global_ayah:
            frappe.throw(
                _("End Global Ayah cannot be before Start Global Ayah.")
            )

        calculated_count = (
            self.end_global_ayah - self.start_global_ayah + 1
        )

        if calculated_count != self.ayah_count:
            frappe.throw(
                _(
                    "Ayah Count must match the global Ayah range. "
                    "Expected {0}, but got {1}."
                ).format(calculated_count, self.ayah_count)
            )

    def validate_page_range(self):
        if not self.start_page:
            frappe.throw(_("Start Page is required."))

        if not self.end_page:
            frappe.throw(_("End Page is required."))

        if self.start_page < 1 or self.start_page > 604:
            frappe.throw(_("Start Page must be between 1 and 604."))

        if self.end_page < 1 or self.end_page > 604:
            frappe.throw(_("End Page must be between 1 and 604."))

        if self.end_page < self.start_page:
            frappe.throw(_("End Page cannot be before Start Page."))

    def validate_juz_range(self):
        if not self.start_juz:
            frappe.throw(_("Start Juz is required."))

        if not self.end_juz:
            frappe.throw(_("End Juz is required."))

        if self.start_juz < 1 or self.start_juz > 30:
            frappe.throw(_("Start Juz must be between 1 and 30."))

        if self.end_juz < 1 or self.end_juz > 30:
            frappe.throw(_("End Juz must be between 1 and 30."))

        if self.end_juz < self.start_juz:
            frappe.throw(_("End Juz cannot be before Start Juz."))

    def validate_duplicate_surah_number(self):
        existing = frappe.db.exists(
            "Dar Quraan Surah",
            {
                "surah_number": self.surah_number,
                "name": ["!=", self.name or ""],
            },
        )

        if existing:
            frappe.throw(
                _("Surah Number {0} already exists.").format(
                    self.surah_number
                )
            )