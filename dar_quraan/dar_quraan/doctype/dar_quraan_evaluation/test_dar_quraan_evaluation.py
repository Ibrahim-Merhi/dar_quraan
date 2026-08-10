import frappe
from frappe.tests.utils import FrappeTestCase

from dar_quraan.dar_quraan.doctype.dar_quraan_evaluation.dar_quraan_evaluation import (
    DarQuraanEvaluation,
)


class TestDarQuraanEvaluation(FrappeTestCase):
    def make_assignment(self):
        return frappe._dict({
            "name": "TEST-ASSIGNMENT",
            "student": "TEST-STUDENT",
            "student_name": "Test Student",
            "branch": "TEST-BRANCH",
            "teaching_location": "TEST-LOCATION",
            "halaqa": "TEST-HALAQA",
            "teacher": "TEST-TEACHER",
            "study_track": "Hifz",
            "riwayah": "Hafs",
            "meta": frappe._dict({
                "has_field": lambda fieldname: True
            }),
        })

    def make_item(
        self,
        memorization_quality=4,
        tajweed=4,
        fluency=4,
    ):
        return frappe._dict({
            "idx": 1,
            "memorization_quality":
                memorization_quality,
            "tajweed": tajweed,
            "fluency": fluency,
            "validate": lambda: None,
            "get_score": lambda: round(
                (
                    memorization_quality * 0.40
                    + tajweed * 0.30
                    + fluency * 0.30
                )
                / 5
                * 100,
                2,
            ),
        })

    def make_evaluation(self, **kwargs):
        values = {
            "doctype": "Dar Quraan Evaluation",
            "student_assignment":
                "TEST-ASSIGNMENT",
            "evaluation_date":
                "2026-08-10",
            "evaluation_type":
                "Monthly",
            "evaluation_items": [
                self.make_item()
            ],
            "status": "Draft",
        }

        values.update(kwargs)

        return DarQuraanEvaluation(
            values
        )

    def validate_evaluation(
        self,
        evaluation,
    ):
        original_exists = frappe.db.exists
        original_get_doc = frappe.get_doc

        assignment = self.make_assignment()

        def fake_exists(
            doctype,
            name=None,
            *args,
            **kwargs
        ):
            if (
                doctype
                == "Dar Quraan Student Assignment"
                and name == "TEST-ASSIGNMENT"
            ):
                return "TEST-ASSIGNMENT"

            return original_exists(
                doctype,
                name,
                *args,
                **kwargs
            )

        def fake_get_doc(
            doctype,
            name=None,
            *args,
            **kwargs
        ):
            if (
                doctype
                == "Dar Quraan Student Assignment"
                and name == "TEST-ASSIGNMENT"
            ):
                return assignment

            return original_get_doc(
                doctype,
                name,
                *args,
                **kwargs
            )

        frappe.db.exists = fake_exists
        frappe.get_doc = fake_get_doc

        try:
            evaluation.validate()
        finally:
            frappe.db.exists = original_exists
            frappe.get_doc = original_get_doc

    def test_valid_evaluation(self):
        evaluation = self.make_evaluation()

        self.validate_evaluation(
            evaluation
        )

    def test_student_assignment_required(self):
        evaluation = self.make_evaluation(
            student_assignment=None
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_evaluation(
                evaluation
            )

    def test_invalid_student_assignment(self):
        evaluation = self.make_evaluation(
            student_assignment="INVALID"
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_evaluation(
                evaluation
            )

    def test_assignment_context_is_fetched(self):
        evaluation = self.make_evaluation()

        self.validate_evaluation(
            evaluation
        )

        self.assertEqual(
            evaluation.student,
            "TEST-STUDENT",
        )

        self.assertEqual(
            evaluation.student_name,
            "Test Student",
        )

        self.assertEqual(
            evaluation.branch,
            "TEST-BRANCH",
        )

        self.assertEqual(
            evaluation.teaching_location,
            "TEST-LOCATION",
        )

        self.assertEqual(
            evaluation.halaqa,
            "TEST-HALAQA",
        )

        self.assertEqual(
            evaluation.teacher,
            "TEST-TEACHER",
        )

        self.assertEqual(
            evaluation.study_track,
            "Hifz",
        )

        self.assertEqual(
            evaluation.riwayah,
            "Hafs",
        )

    def test_evaluation_date_required(self):
        evaluation = self.make_evaluation(
            evaluation_date=None
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_evaluation(
                evaluation
            )

    def test_evaluation_type_required(self):
        evaluation = self.make_evaluation(
            evaluation_type=None
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_evaluation(
                evaluation
            )

    def test_invalid_evaluation_type(self):
        evaluation = self.make_evaluation(
            evaluation_type="Unknown"
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_evaluation(
                evaluation
            )

    def test_all_evaluation_types_are_valid(self):
        evaluation_types = [
            "Placement",
            "Monthly",
            "Periodic",
            "Final",
            "Special",
        ]

        for evaluation_type in evaluation_types:
            evaluation = self.make_evaluation(
                evaluation_type=evaluation_type
            )

            self.validate_evaluation(
                evaluation
            )

    def test_evaluation_item_required(self):
        evaluation = self.make_evaluation(
            evaluation_items=[]
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_evaluation(
                evaluation
            )

    def test_score_80_is_very_good(self):
        evaluation = self.make_evaluation(
            evaluation_items=[
                self.make_item(
                    4,
                    4,
                    4,
                )
            ]
        )

        self.validate_evaluation(
            evaluation
        )

        self.assertEqual(
            evaluation.overall_score,
            80.0,
        )

        self.assertEqual(
            evaluation.overall_result,
            "Very Good",
        )

    def test_perfect_score(self):
        evaluation = self.make_evaluation(
            evaluation_items=[
                self.make_item(
                    5,
                    5,
                    5,
                )
            ]
        )

        self.validate_evaluation(
            evaluation
        )

        self.assertEqual(
            evaluation.overall_score,
            100.0,
        )

        self.assertEqual(
            evaluation.overall_result,
            "Excellent",
        )

    def test_multiple_items_are_averaged(self):
        evaluation = self.make_evaluation(
            evaluation_items=[
                self.make_item(
                    5,
                    5,
                    5,
                ),
                self.make_item(
                    4,
                    4,
                    4,
                ),
            ]
        )

        self.validate_evaluation(
            evaluation
        )

        self.assertEqual(
            evaluation.overall_score,
            90.0,
        )

        self.assertEqual(
            evaluation.overall_result,
            "Excellent",
        )

    def test_good_result(self):
        evaluation = self.make_evaluation(
            evaluation_items=[
                self.make_item(
                    3.5,
                    3.5,
                    3.5,
                )
            ]
        )

        self.validate_evaluation(
            evaluation
        )

        self.assertEqual(
            evaluation.overall_result,
            "Good",
        )

    def test_needs_revision_result(self):
        evaluation = self.make_evaluation(
            evaluation_items=[
                self.make_item(
                    3,
                    3,
                    3,
                )
            ]
        )

        self.validate_evaluation(
            evaluation
        )

        self.assertEqual(
            evaluation.overall_result,
            "Needs Revision",
        )

    def test_repeat_result(self):
        evaluation = self.make_evaluation(
            evaluation_items=[
                self.make_item(
                    2,
                    2,
                    2,
                )
            ]
        )

        self.validate_evaluation(
            evaluation
        )

        self.assertEqual(
            evaluation.overall_result,
            "Repeat",
        )

    def test_default_status(self):
        evaluation = self.make_evaluation(
            status=None
        )

        self.validate_evaluation(
            evaluation
        )

        self.assertEqual(
            evaluation.status,
            "Draft",
        )

    def test_invalid_status_rejected(self):
        evaluation = self.make_evaluation(
            status="Invalid"
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_evaluation(
                evaluation
            )