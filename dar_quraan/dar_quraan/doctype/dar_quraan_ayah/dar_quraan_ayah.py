import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class DarQuraanAyah(Document):
    def before_naming(self):
        """
        Populate canonical Quran coordinates before Frappe generates
        the document name from field:verse_key.
        """
        self.set_derived_quran_fields()

    def validate(self):
        """
        Recalculate derived fields and validate all Quran coordinates.
        """
        self.set_derived_quran_fields()

        self.validate_ayah_number()
        self.validate_global_ayah_number()
        self.validate_page_number()
        self.validate_juz_number()
        self.validate_hizb_number()
        self.validate_rub_el_hizb_number()

    def get_surah_data(self):
        if not self.surah:
            frappe.throw(_("Surah is required."))

        surah = frappe.db.get_value(
            "Dar Quraan Surah",
            self.surah,
            [
                "surah_number",
                "ayah_count",
                "start_global_ayah",
                "end_global_ayah",
                "start_page",
                "end_page",
                "start_juz",
                "end_juz",
            ],
            as_dict=True,
        )

        if not surah:
            frappe.throw(
                _("Surah {0} does not exist.").format(self.surah)
            )

        return surah

    def set_derived_quran_fields(self):
        """
        The following values must never depend on manual user input:

        - surah_number
        - verse_key
        - global_ayah_number

        They are derived from Surah + Ayah Number.
        """
        if not self.surah:
            return

        if self.ayah_number in (None, ""):
            return

        surah = self.get_surah_data()

        surah_number = cint(surah.surah_number)
        ayah_number = cint(self.ayah_number)

        self.surah_number = surah_number

        self.verse_key = "{0}:{1}".format(
            surah_number,
            ayah_number,
        )

        if ayah_number >= 1:
            self.global_ayah_number = (
                cint(surah.start_global_ayah)
                + ayah_number
                - 1
            )

    def validate_ayah_number(self):
        if self.ayah_number in (None, ""):
            frappe.throw(_("Ayah Number is required."))

        ayah_number = cint(self.ayah_number)

        if ayah_number < 1:
            frappe.throw(
                _("Ayah Number must be greater than zero.")
            )

        surah = self.get_surah_data()
        ayah_count = cint(surah.ayah_count)

        if ayah_number > ayah_count:
            frappe.throw(
                _(
                    "Ayah Number {0} is invalid for this Surah. "
                    "The Surah contains {1} Ayahs."
                ).format(
                    ayah_number,
                    ayah_count,
                )
            )

    def validate_global_ayah_number(self):
        if not self.global_ayah_number:
            frappe.throw(
                _("Global Ayah Number could not be calculated.")
            )

        global_ayah_number = cint(
            self.global_ayah_number
        )

        if (
            global_ayah_number < 1
            or global_ayah_number > 6236
        ):
            frappe.throw(
                _(
                    "Global Ayah Number must be between "
                    "1 and 6236."
                )
            )

        surah = self.get_surah_data()

        expected_global_ayah = (
            cint(surah.start_global_ayah)
            + cint(self.ayah_number)
            - 1
        )

        if global_ayah_number != expected_global_ayah:
            frappe.throw(
                _(
                    "Global Ayah Number is inconsistent. "
                    "Expected {0}."
                ).format(expected_global_ayah)
            )

        if (
            global_ayah_number
            < cint(surah.start_global_ayah)
            or global_ayah_number
            > cint(surah.end_global_ayah)
        ):
            frappe.throw(
                _(
                    "Global Ayah Number is outside the "
                    "configured Surah range."
                )
            )

    def validate_page_number(self):
        if self.page_number in (None, ""):
            frappe.throw(_("Page Number is required."))

        page_number = cint(self.page_number)

        if page_number < 1 or page_number > 604:
            frappe.throw(
                _("Page Number must be between 1 and 604.")
            )

        surah = self.get_surah_data()

        start_page = cint(surah.start_page)
        end_page = cint(surah.end_page)

        if (
            page_number < start_page
            or page_number > end_page
        ):
            frappe.throw(
                _(
                    "Page Number {0} is outside the page "
                    "range for this Surah ({1} to {2})."
                ).format(
                    page_number,
                    start_page,
                    end_page,
                )
            )

    def validate_juz_number(self):
        if self.juz_number in (None, ""):
            frappe.throw(_("Juz Number is required."))

        juz_number = cint(self.juz_number)

        if juz_number < 1 or juz_number > 30:
            frappe.throw(
                _("Juz Number must be between 1 and 30.")
            )

        surah = self.get_surah_data()

        start_juz = cint(surah.start_juz)
        end_juz = cint(surah.end_juz)

        if (
            juz_number < start_juz
            or juz_number > end_juz
        ):
            frappe.throw(
                _(
                    "Juz Number {0} is outside the Juz "
                    "range for this Surah ({1} to {2})."
                ).format(
                    juz_number,
                    start_juz,
                    end_juz,
                )
            )

    def validate_hizb_number(self):
        if self.hizb_number in (None, ""):
            return

        hizb_number = cint(self.hizb_number)

        if hizb_number < 1 or hizb_number > 60:
            frappe.throw(
                _("Hizb Number must be between 1 and 60.")
            )

    def validate_rub_el_hizb_number(self):
        if self.rub_el_hizb_number in (None, ""):
            return

        rub_number = cint(
            self.rub_el_hizb_number
        )

        if rub_number < 1 or rub_number > 240:
            frappe.throw(
                _(
                    "Rub El Hizb Number must be between "
                    "1 and 240."
                )
            )