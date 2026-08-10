import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, now_datetime


class DarQuraanStudentQuranState(Document):
    def validate(self):
        self.validate_student_assignment()
        self.validate_unique_state()
        self.fetch_assignment_context()

        self.validate_current_memorization()
        self.validate_revision_state()

        self.calculate_progress_summary()
        self.set_last_updated()

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

    def validate_unique_state(self):
        """
        There must be only one Quran State per Student Assignment.

        Since autoname is field:student_assignment, the database
        primary key will already protect against duplicates on insert.
        This validation also gives a clear application-level error
        before the database rejects the record.
        """

        if not self.student_assignment:
            return

        existing = frappe.db.exists(
            "Dar Quraan Student Quran State",
            {
                "student_assignment": self.student_assignment,
                "name": ["!=", self.name or ""],
            },
        )

        if existing:
            frappe.throw(
                _(
                    "A Quran State already exists for Student "
                    "Assignment {0}."
                ).format(
                    self.student_assignment
                )
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

    def get_surah_data(
        self,
        surah_name,
    ):
        if not surah_name:
            return None

        surah = frappe.db.get_value(
            "Dar Quraan Surah",
            surah_name,
            [
                "surah_number",
                "ayah_count",
                "start_page",
                "end_page",
                "is_active",
            ],
            as_dict=True,
        )

        if not surah:
            frappe.throw(
                _(
                    "Selected Surah {0} does not exist."
                ).format(
                    surah_name
                )
            )

        if not surah.is_active:
            frappe.throw(
                _(
                    "Selected Surah {0} is inactive."
                ).format(
                    surah_name
                )
            )

        return surah

    def validate_current_memorization(self):
        """
        Current Surah / Ayah / Page are optional for a completely new
        student. Once any one of them is supplied, all three are
        required.
        """

        values_present = any(
            [
                self.current_surah,
                self.current_ayah not in (None, "", 0),
                self.current_page not in (None, "", 0),
            ]
        )

        if not values_present:
            return

        if not self.current_surah:
            frappe.throw(
                _("Current Surah is required.")
            )

        if self.current_ayah in (None, ""):
            frappe.throw(
                _("Current Ayah is required.")
            )

        if self.current_page in (None, ""):
            frappe.throw(
                _("Current Page is required.")
            )

        surah = self.get_surah_data(
            self.current_surah
        )

        current_ayah = cint(
            self.current_ayah
        )

        current_page = cint(
            self.current_page
        )

        if current_ayah < 1:
            frappe.throw(
                _("Current Ayah must be greater than zero.")
            )

        if current_ayah > cint(
            surah.ayah_count
        ):
            frappe.throw(
                _(
                    "Current Ayah cannot exceed {0} for "
                    "the selected Surah."
                ).format(
                    surah.ayah_count
                )
            )

        if current_page < cint(
            surah.start_page
        ):
            frappe.throw(
                _(
                    "Current Page cannot be before page {0} "
                    "for the selected Surah."
                ).format(
                    surah.start_page
                )
            )

        if current_page > cint(
            surah.end_page
        ):
            frappe.throw(
                _(
                    "Current Page cannot exceed page {0} "
                    "for the selected Surah."
                ).format(
                    surah.end_page
                )
            )

    def validate_revision_state(self):
        """
        Revision position is optional.

        If any revision coordinate is supplied, all required revision
        coordinates must be present and form a valid range.
        """

        revision_values_present = any(
            [
                self.revision_surah,
                self.revision_from_ayah
                not in (None, "", 0),
                self.revision_to_ayah
                not in (None, "", 0),
                self.revision_from_page
                not in (None, "", 0),
                self.revision_to_page
                not in (None, "", 0),
            ]
        )

        if not revision_values_present:
            return

        required_fields = {
            "revision_surah": _("Revision Surah"),
            "revision_from_ayah": _(
                "Revision From Ayah"
            ),
            "revision_to_ayah": _(
                "Revision To Ayah"
            ),
            "revision_from_page": _(
                "Revision From Page"
            ),
            "revision_to_page": _(
                "Revision To Page"
            ),
        }

        for fieldname, label in required_fields.items():
            value = self.get(
                fieldname
            )

            if value in (None, ""):
                frappe.throw(
                    _(
                        "{0} is required."
                    ).format(
                        label
                    )
                )

        surah = self.get_surah_data(
            self.revision_surah
        )

        from_ayah = cint(
            self.revision_from_ayah
        )

        to_ayah = cint(
            self.revision_to_ayah
        )

        from_page = cint(
            self.revision_from_page
        )

        to_page = cint(
            self.revision_to_page
        )

        if from_ayah < 1:
            frappe.throw(
                _(
                    "Revision From Ayah must be "
                    "greater than zero."
                )
            )

        if to_ayah < 1:
            frappe.throw(
                _(
                    "Revision To Ayah must be "
                    "greater than zero."
                )
            )

        if from_ayah > cint(
            surah.ayah_count
        ):
            frappe.throw(
                _(
                    "Revision From Ayah cannot exceed {0} "
                    "for the selected Surah."
                ).format(
                    surah.ayah_count
                )
            )

        if to_ayah > cint(
            surah.ayah_count
        ):
            frappe.throw(
                _(
                    "Revision To Ayah cannot exceed {0} "
                    "for the selected Surah."
                ).format(
                    surah.ayah_count
                )
            )

        if to_ayah < from_ayah:
            frappe.throw(
                _(
                    "Revision To Ayah cannot be before "
                    "Revision From Ayah."
                )
            )

        if from_page < cint(
            surah.start_page
        ):
            frappe.throw(
                _(
                    "Revision From Page cannot be before "
                    "page {0} for the selected Surah."
                ).format(
                    surah.start_page
                )
            )

        if from_page > cint(
            surah.end_page
        ):
            frappe.throw(
                _(
                    "Revision From Page cannot exceed "
                    "page {0} for the selected Surah."
                ).format(
                    surah.end_page
                )
            )

        if to_page < cint(
            surah.start_page
        ):
            frappe.throw(
                _(
                    "Revision To Page cannot be before "
                    "page {0} for the selected Surah."
                ).format(
                    surah.start_page
                )
            )

        if to_page > cint(
            surah.end_page
        ):
            frappe.throw(
                _(
                    "Revision To Page cannot exceed "
                    "page {0} for the selected Surah."
                ).format(
                    surah.end_page
                )
            )

        if to_page < from_page:
            frappe.throw(
                _(
                    "Revision To Page cannot be before "
                    "Revision From Page."
                )
            )

    def calculate_progress_summary(self):
        """
        Initial implementation:

        completed_pages:
            Current Mushaf page reached.

        memorization_percentage:
            completed_pages / 604 * 100

        completed_ayahs:
            Not calculated cumulatively yet because the simplified
            Surah master no longer stores a global Ayah sequence.
            For the first version we keep it at 0 unless it is
            calculated later by the state update service.
        """

        if not self.current_page:
            self.completed_pages = 0
            self.completed_ayahs = 0
            self.memorization_percentage = 0
            return

        completed_pages = cint(
            self.current_page
        )

        if completed_pages < 0:
            completed_pages = 0

        if completed_pages > 604:
            completed_pages = 604

        self.completed_pages = (
            completed_pages
        )

        self.memorization_percentage = round(
            flt(
                completed_pages
                / 604
                * 100
            ),
            2,
        )

        # Will be populated accurately by the state update service
        # once cumulative Surah completion logic is added.
        if self.completed_ayahs is None:
            self.completed_ayahs = 0

    def set_last_updated(self):
        self.last_updated = (
            now_datetime()
        )

    def validate_status(self):
        allowed_statuses = {
            "Active",
            "Paused",
            "Completed",
            "Inactive",
        }

        if not self.status:
            self.status = "Active"

        if self.status not in allowed_statuses:
            frappe.throw(
                _(
                    "Status must be Active, Paused, "
                    "Completed, or Inactive."
                )
            )