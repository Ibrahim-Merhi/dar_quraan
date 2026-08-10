import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class DarQuraanEvaluationItem(Document):
    def validate(self):
        self.validate_surah()
        self.validate_ayah_range()
        self.validate_page_range()
        self.validate_scores()
        self.validate_counts()
        self.validate_result()

    def validate_surah(self):
        if not self.surah:
            frappe.throw(
                _("Surah is required.")
            )

        if not frappe.db.exists(
            "Dar Quraan Surah",
            self.surah,
        ):
            frappe.throw(
                _("Selected Surah does not exist.")
            )

    def get_surah(self):
        return frappe.get_doc(
            "Dar Quraan Surah",
            self.surah,
        )

    def validate_ayah_range(self):
        if cint(self.from_ayah) <= 0:
            frappe.throw(
                _("From Ayah must be greater than zero.")
            )

        if cint(self.to_ayah) <= 0:
            frappe.throw(
                _("To Ayah must be greater than zero.")
            )

        if cint(self.from_ayah) > cint(self.to_ayah):
            frappe.throw(
                _(
                    "From Ayah cannot be greater than "
                    "To Ayah."
                )
            )

        surah = self.get_surah()

        ayah_count = cint(
            surah.get("ayah_count")
        )

        if ayah_count and (
            cint(self.from_ayah) > ayah_count
            or cint(self.to_ayah) > ayah_count
        ):
            frappe.throw(
                _(
                    "Ayah range cannot exceed the Surah "
                    "Ayah Count of {0}."
                ).format(
                    ayah_count
                )
            )

    def validate_page_range(self):
        if cint(self.from_page) <= 0:
            frappe.throw(
                _("From Page must be greater than zero.")
            )

        if cint(self.to_page) <= 0:
            frappe.throw(
                _("To Page must be greater than zero.")
            )

        if cint(self.from_page) > cint(self.to_page):
            frappe.throw(
                _(
                    "From Page cannot be greater than "
                    "To Page."
                )
            )

        surah = self.get_surah()

        surah_from_page = cint(
            surah.get("from_page")
        )

        surah_to_page = cint(
            surah.get("to_page")
        )

        if (
            surah_from_page
            and cint(self.from_page) < surah_from_page
        ):
            frappe.throw(
                _(
                    "From Page cannot be before the Surah "
                    "starting page {0}."
                ).format(
                    surah_from_page
                )
            )

        if (
            surah_to_page
            and cint(self.to_page) > surah_to_page
        ):
            frappe.throw(
                _(
                    "To Page cannot exceed the Surah "
                    "ending page {0}."
                ).format(
                    surah_to_page
                )
            )

    def validate_scores(self):
        score_fields = {
            "memorization_quality": _(
                "Memorization Quality"
            ),
            "tajweed": _("Tajweed"),
            "fluency": _("Fluency"),
        }

        for fieldname, label in score_fields.items():
            value = cint(
                self.get(fieldname)
            )

            if value < 1 or value > 5:
                frappe.throw(
                    _(
                        "{0} must be between 1 and 5."
                    ).format(
                        label
                    )
                )

    def validate_counts(self):
        if cint(self.mistakes_count) < 0:
            frappe.throw(
                _(
                    "Mistakes Count cannot be negative."
                )
            )

        if cint(self.prompt_count) < 0:
            frappe.throw(
                _(
                    "Prompt Count cannot be negative."
                )
            )

    def validate_result(self):
        allowed_results = {
            "Excellent",
            "Very Good",
            "Good",
            "Needs Revision",
            "Repeat",
        }

        if not self.result:
            frappe.throw(
                _("Result is required.")
            )

        if self.result not in allowed_results:
            frappe.throw(
                _(
                    "Result must be Excellent, Very Good, "
                    "Good, Needs Revision, or Repeat."
                )
            )

    def get_score(self):
        memorization_quality = cint(
            self.memorization_quality
        )

        tajweed = cint(
            self.tajweed
        )

        fluency = cint(
            self.fluency
        )

        weighted_score = (
            memorization_quality * 0.40
            + tajweed * 0.30
            + fluency * 0.30
        )

        return round(
            weighted_score / 5 * 100,
            2,
        )