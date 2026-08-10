from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanNextAssignment(FrappeTestCase):
    def make_assignment(self, **kwargs):
        data = {
            "name": "DQ-SA-TEST-00001",
            "student": "DQ-STUDENT-TEST-00001",
            "student_name": "Ahmad Test",
            "branch": "DQ-BRANCH-TEST",
            "teaching_location": "DQ-LOCATION-TEST",
            "halaqa": "DQ-HALAQA-TEST",
            "teacher": "DQ-TEACHER-TEST",
            "study_track": "Hifz",
            "riwayah": "Hafs",
        }

        data.update(kwargs)

        assignment = frappe._dict(data)

        assignment.meta = frappe._dict()
        assignment.meta.has_field = (
            lambda fieldname: fieldname in data
        )

        return assignment

    def make_next_assignment(self, **kwargs):
        data = {
            "doctype": "Dar Quraan Next Assignment",
            "student_assignment": "DQ-SA-TEST-00001",
            "assignment_date": "2026-08-11",
            "status": "Draft",
            "new_memorization": [
                {
                    "doctype": "Dar Quraan Quran Range",
                    "surah": "2",
                    "from_ayah": 36,
                    "to_ayah": 45,
                    "from_page": 6,
                    "to_page": 7,
                }
            ],
            "revision": [],
        }

        data.update(kwargs)

        return frappe.get_doc(data)

    def make_surah(self):
        return frappe._dict(
            {
                "ayah_count": 286,
                "start_page": 2,
                "end_page": 49,
                "is_active": 1,
            }
        )

    def make_progress_item(
        self,
        result="Repeat",
        **kwargs,
    ):
        data = {
            "result": result,
            "surah": "2",
            "from_ayah": 20,
            "to_ayah": 35,
            "from_page": 4,
            "to_page": 6,
        }

        data.update(kwargs)

        return frappe._dict(data)

    def make_source_progress(
        self,
        status="Completed",
        progress_items=None,
        student_assignment="DQ-SA-TEST-00001",
    ):
        if progress_items is None:
            progress_items = [
                self.make_progress_item()
            ]

        return frappe._dict(
            {
                "name": "DQ-PROG-TEST-00001",
                "student_assignment": student_assignment,
                "status": status,
                "progress_items": progress_items,
            }
        )

    def validate_doc(
        self,
        doc,
        assignment=None,
        source_progress_assignment=None,
        source_evaluation_assignment=None,
    ):
        if assignment is None:
            assignment = self.make_assignment()

        original_get_doc = frappe.get_doc

        def fake_get_doc(*args, **kwargs):
            if (
                len(args) >= 2
                and args[0]
                == "Dar Quraan Student Assignment"
            ):
                return assignment

            return original_get_doc(
                *args,
                **kwargs,
            )

        def fake_exists(
            doctype,
            name=None,
            *args,
            **kwargs,
        ):
            if (
                doctype
                == "Dar Quraan Student Assignment"
                and name == "DQ-SA-TEST-00001"
            ):
                return "DQ-SA-TEST-00001"

            if (
                doctype
                == "Dar Quraan Student Progress"
                and name == "DQ-PROG-TEST-00001"
            ):
                return "DQ-PROG-TEST-00001"

            if (
                doctype
                == "Dar Quraan Evaluation"
                and name == "DQ-EVAL-TEST-00001"
            ):
                return "DQ-EVAL-TEST-00001"

            return None

        def fake_get_value(
            doctype,
            name,
            fieldname,
            *args,
            **kwargs,
        ):
            if (
                doctype == "Dar Quraan Surah"
                and name == "2"
            ):
                if kwargs.get("as_dict"):
                    return self.make_surah()

                return None

            if (
                doctype
                == "Dar Quraan Student Progress"
                and name == "DQ-PROG-TEST-00001"
                and fieldname == "student_assignment"
            ):
                return (
                    source_progress_assignment
                    or "DQ-SA-TEST-00001"
                )

            if (
                doctype
                == "Dar Quraan Evaluation"
                and name == "DQ-EVAL-TEST-00001"
                and fieldname == "student_assignment"
            ):
                return (
                    source_evaluation_assignment
                    or "DQ-SA-TEST-00001"
                )

            return None

        with (
            patch.object(
                frappe,
                "get_doc",
                side_effect=fake_get_doc,
            ),
            patch.object(
                frappe.db,
                "exists",
                side_effect=fake_exists,
            ),
            patch.object(
                frappe.db,
                "get_value",
                side_effect=fake_get_value,
            ),
        ):
            doc.validate()

    def generate_from_progress(
        self,
        doc,
        progress,
    ):
        original_get_doc = frappe.get_doc
        original_get_value = frappe.db.get_value

        def fake_get_doc(*args, **kwargs):
            if (
                len(args) >= 2
                and args[0]
                == "Dar Quraan Student Progress"
                and args[1]
                == "DQ-PROG-TEST-00001"
            ):
                return progress

            return original_get_doc(
                *args,
                **kwargs,
            )

        def fake_get_value(
            doctype,
            name,
            fieldname,
            *args,
            **kwargs,
        ):
            if (
                doctype == "Dar Quraan Surah"
                and name == "2"
            ):
                if kwargs.get("as_dict"):
                    return self.make_surah()

            return original_get_value(
                doctype,
                name,
                fieldname,
                *args,
                **kwargs,
            )

        with (
            patch.object(
                frappe,
                "get_doc",
                side_effect=fake_get_doc,
            ),
            patch.object(
                frappe.db,
                "get_value",
                side_effect=fake_get_value,
            ),
        ):
            return doc.generate_from_source_progress()

    # ---------------------------------------------------------
    # Basic validation
    # ---------------------------------------------------------

    def test_valid_next_assignment(self):
        doc = self.make_next_assignment()

        self.validate_doc(doc)

        self.assertEqual(
            doc.student,
            "DQ-STUDENT-TEST-00001",
        )
        self.assertEqual(
            doc.teacher,
            "DQ-TEACHER-TEST",
        )
        self.assertEqual(
            doc.status,
            "Draft",
        )

    def test_student_context_is_fetched(self):
        doc = self.make_next_assignment(
            student="WRONG",
            student_name="Wrong Name",
            branch="WRONG",
            teaching_location="WRONG",
            halaqa="WRONG",
            teacher="WRONG",
            study_track="WRONG",
            riwayah="WRONG",
        )

        self.validate_doc(doc)

        self.assertEqual(
            doc.student,
            "DQ-STUDENT-TEST-00001",
        )
        self.assertEqual(
            doc.student_name,
            "Ahmad Test",
        )
        self.assertEqual(
            doc.branch,
            "DQ-BRANCH-TEST",
        )
        self.assertEqual(
            doc.teaching_location,
            "DQ-LOCATION-TEST",
        )
        self.assertEqual(
            doc.halaqa,
            "DQ-HALAQA-TEST",
        )
        self.assertEqual(
            doc.teacher,
            "DQ-TEACHER-TEST",
        )
        self.assertEqual(
            doc.study_track,
            "Hifz",
        )
        self.assertEqual(
            doc.riwayah,
            "Hafs",
        )

    def test_student_assignment_is_required(self):
        doc = self.make_next_assignment(
            student_assignment=None,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            doc.validate()

    def test_invalid_student_assignment_is_rejected(self):
        doc = self.make_next_assignment(
            student_assignment="INVALID",
        )

        with patch.object(
            frappe.db,
            "exists",
            return_value=None,
        ):
            with self.assertRaises(
                frappe.ValidationError
            ):
                doc.validate()

    def test_assignment_without_student_is_rejected(self):
        assignment = self.make_assignment(
            student=None,
        )

        doc = self.make_next_assignment()

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_doc(
                doc,
                assignment=assignment,
            )

    def test_assignment_without_teacher_is_rejected(self):
        assignment = self.make_assignment(
            teacher=None,
        )

        doc = self.make_next_assignment()

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_doc(
                doc,
                assignment=assignment,
            )

    def test_assignment_without_halaqa_is_rejected(self):
        assignment = self.make_assignment(
            halaqa=None,
        )

        doc = self.make_next_assignment()

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_doc(
                doc,
                assignment=assignment,
            )

    def test_assignment_date_is_required(self):
        doc = self.make_next_assignment(
            assignment_date=None,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_doc(doc)

    def test_at_least_one_quran_range_is_required(self):
        doc = self.make_next_assignment(
            new_memorization=[],
            revision=[],
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_doc(doc)

    def test_revision_only_is_valid(self):
        doc = self.make_next_assignment(
            new_memorization=[],
            revision=[
                {
                    "doctype": "Dar Quraan Quran Range",
                    "surah": "2",
                    "from_ayah": 1,
                    "to_ayah": 20,
                    "from_page": 2,
                    "to_page": 4,
                }
            ],
        )

        self.validate_doc(doc)

        self.assertEqual(
            len(doc.revision),
            1,
        )

    def test_invalid_quran_range_is_rejected(self):
        doc = self.make_next_assignment(
            new_memorization=[
                {
                    "doctype": "Dar Quraan Quran Range",
                    "surah": "2",
                    "from_ayah": 50,
                    "to_ayah": 40,
                    "from_page": 8,
                    "to_page": 7,
                }
            ],
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_doc(doc)

    # ---------------------------------------------------------
    # Source validation
    # ---------------------------------------------------------

    def test_source_progress_same_assignment_is_valid(self):
        doc = self.make_next_assignment(
            source_progress="DQ-PROG-TEST-00001",
        )

        self.validate_doc(doc)

    def test_missing_source_progress_is_rejected(self):
        doc = self.make_next_assignment(
            source_progress="MISSING",
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_doc(doc)

    def test_source_progress_must_match_assignment(self):
        doc = self.make_next_assignment(
            source_progress="DQ-PROG-TEST-00001",
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_doc(
                doc,
                source_progress_assignment=(
                    "DQ-SA-OTHER"
                ),
            )

    def test_source_evaluation_same_assignment_is_valid(self):
        doc = self.make_next_assignment(
            source_evaluation="DQ-EVAL-TEST-00001",
        )

        self.validate_doc(doc)

    def test_missing_source_evaluation_is_rejected(self):
        doc = self.make_next_assignment(
            source_evaluation="MISSING",
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_doc(doc)

    def test_source_evaluation_must_match_assignment(self):
        doc = self.make_next_assignment(
            source_evaluation="DQ-EVAL-TEST-00001",
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_doc(
                doc,
                source_evaluation_assignment=(
                    "DQ-SA-OTHER"
                ),
            )

    def test_both_sources_can_be_used(self):
        doc = self.make_next_assignment(
            source_progress="DQ-PROG-TEST-00001",
            source_evaluation="DQ-EVAL-TEST-00001",
        )

        self.validate_doc(doc)

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    def test_missing_status_defaults_to_draft(self):
        doc = self.make_next_assignment(
            status=None,
        )

        self.validate_doc(doc)

        self.assertEqual(
            doc.status,
            "Draft",
        )

    def test_all_valid_statuses(self):
        statuses = [
            "Draft",
            "Ready",
            "Assigned",
            "Completed",
            "Cancelled",
        ]

        for status in statuses:
            doc = self.make_next_assignment(
                status=status,
            )

            self.validate_doc(doc)

            self.assertEqual(
                doc.status,
                status,
            )

    def test_invalid_status_is_rejected(self):
        doc = self.make_next_assignment(
            status="Invalid",
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_doc(doc)

    # ---------------------------------------------------------
    # Automatic generation from Student Progress
    # ---------------------------------------------------------

    def test_repeat_generates_new_memorization(self):
        doc = self.make_next_assignment(
            source_progress="DQ-PROG-TEST-00001",
        )

        progress = self.make_source_progress(
            progress_items=[
                self.make_progress_item(
                    result="Repeat",
                )
            ]
        )

        result = self.generate_from_progress(
            doc,
            progress,
        )

        self.assertEqual(
            len(doc.new_memorization),
            1,
        )

        self.assertEqual(
            len(doc.revision),
            0,
        )

        row = doc.new_memorization[0]

        self.assertEqual(
            row.surah,
            "2",
        )
        self.assertEqual(
            row.from_ayah,
            20,
        )
        self.assertEqual(
            row.to_ayah,
            35,
        )
        self.assertEqual(
            row.from_page,
            4,
        )
        self.assertEqual(
            row.to_page,
            6,
        )

        self.assertEqual(
            result["new_memorization"],
            1,
        )
        self.assertEqual(
            result["revision"],
            0,
        )
        self.assertEqual(
            result["total"],
            1,
        )

    def test_needs_revision_generates_revision(self):
        doc = self.make_next_assignment(
            source_progress="DQ-PROG-TEST-00001",
        )

        progress = self.make_source_progress(
            progress_items=[
                self.make_progress_item(
                    result="Needs Revision",
                )
            ]
        )

        result = self.generate_from_progress(
            doc,
            progress,
        )

        self.assertEqual(
            len(doc.new_memorization),
            0,
        )

        self.assertEqual(
            len(doc.revision),
            1,
        )

        row = doc.revision[0]

        self.assertEqual(
            row.surah,
            "2",
        )
        self.assertEqual(
            row.from_ayah,
            20,
        )
        self.assertEqual(
            row.to_ayah,
            35,
        )

        self.assertEqual(
            result["new_memorization"],
            0,
        )
        self.assertEqual(
            result["revision"],
            1,
        )
        self.assertEqual(
            result["total"],
            1,
        )

    def test_repeat_and_needs_revision_generate_both_tables(self):
        doc = self.make_next_assignment(
            source_progress="DQ-PROG-TEST-00001",
        )

        progress = self.make_source_progress(
            progress_items=[
                self.make_progress_item(
                    result="Repeat",
                    from_ayah=20,
                    to_ayah=25,
                    from_page=4,
                    to_page=5,
                ),
                self.make_progress_item(
                    result="Needs Revision",
                    from_ayah=26,
                    to_ayah=35,
                    from_page=5,
                    to_page=6,
                ),
            ]
        )

        result = self.generate_from_progress(
            doc,
            progress,
        )

        self.assertEqual(
            len(doc.new_memorization),
            1,
        )
        self.assertEqual(
            len(doc.revision),
            1,
        )
        self.assertEqual(
            result["total"],
            2,
        )

    def test_generation_clears_existing_ranges(self):
        doc = self.make_next_assignment(
            source_progress="DQ-PROG-TEST-00001",
        )

        self.assertEqual(
            len(doc.new_memorization),
            1,
        )

        progress = self.make_source_progress(
            progress_items=[
                self.make_progress_item(
                    result="Needs Revision",
                )
            ]
        )

        self.generate_from_progress(
            doc,
            progress,
        )

        self.assertEqual(
            len(doc.new_memorization),
            0,
        )
        self.assertEqual(
            len(doc.revision),
            1,
        )

    def test_source_progress_is_required_for_generation(self):
        doc = self.make_next_assignment(
            source_progress=None,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            doc.generate_from_source_progress()

    def test_source_progress_must_match_assignment_for_generation(self):
        doc = self.make_next_assignment(
            source_progress="DQ-PROG-TEST-00001",
        )

        progress = self.make_source_progress(
            student_assignment="DQ-SA-OTHER",
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.generate_from_progress(
                doc,
                progress,
            )

    def test_source_progress_must_be_completed_for_generation(self):
        doc = self.make_next_assignment(
            source_progress="DQ-PROG-TEST-00001",
        )

        progress = self.make_source_progress(
            status="Draft",
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.generate_from_progress(
                doc,
                progress,
            )

    def test_source_progress_without_items_is_rejected(self):
        doc = self.make_next_assignment(
            source_progress="DQ-PROG-TEST-00001",
        )

        progress = self.make_source_progress(
            progress_items=[],
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.generate_from_progress(
                doc,
                progress,
            )

    def test_good_result_requires_manual_forward_assignment(self):
        doc = self.make_next_assignment(
            source_progress="DQ-PROG-TEST-00001",
        )

        progress = self.make_source_progress(
            progress_items=[
                self.make_progress_item(
                    result="Good",
                )
            ]
        )

        with self.assertRaisesRegex(
            frappe.ValidationError,
            "No Repeat or Needs Revision items were found",
        ):
            self.generate_from_progress(
                doc,
                progress,
            )

    def test_very_good_result_requires_manual_forward_assignment(self):
        doc = self.make_next_assignment(
            source_progress="DQ-PROG-TEST-00001",
        )

        progress = self.make_source_progress(
            progress_items=[
                self.make_progress_item(
                    result="Very Good",
                )
            ]
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.generate_from_progress(
                doc,
                progress,
            )

    def test_excellent_result_requires_manual_forward_assignment(self):
        doc = self.make_next_assignment(
            source_progress="DQ-PROG-TEST-00001",
        )

        progress = self.make_source_progress(
            progress_items=[
                self.make_progress_item(
                    result="Excellent",
                )
            ]
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.generate_from_progress(
                doc,
                progress,
            )

    def test_successful_items_are_ignored_when_repeat_exists(self):
        doc = self.make_next_assignment(
            source_progress="DQ-PROG-TEST-00001",
        )

        progress = self.make_source_progress(
            progress_items=[
                self.make_progress_item(
                    result="Excellent",
                    from_ayah=1,
                    to_ayah=10,
                    from_page=2,
                    to_page=3,
                ),
                self.make_progress_item(
                    result="Repeat",
                    from_ayah=20,
                    to_ayah=35,
                    from_page=4,
                    to_page=6,
                ),
            ]
        )

        result = self.generate_from_progress(
            doc,
            progress,
        )

        self.assertEqual(
            len(doc.new_memorization),
            1,
        )

        self.assertEqual(
            doc.new_memorization[0].from_ayah,
            20,
        )

        self.assertEqual(
            result["total"],
            1,
        )