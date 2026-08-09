# Copyright (c) 2026, ITIHAD
# For license information, please see license.txt

from __future__ import annotations

import unittest

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, cint, getdate, nowdate


ASSIGNMENT_DOCTYPE = "Dar Quraan Student Assignment"
STUDENT_DOCTYPE = "Dar Quraan Student"
BRANCH_DOCTYPE = "Dar Quraan Branch"
LOCATION_DOCTYPE = "Dar Quraan Teaching Location"
TEACHER_DOCTYPE = "Dar Quraan Teacher"
HALAQA_DOCTYPE = "Dar Quraan Halaqa"
ACADEMIC_YEAR_DOCTYPE = "Dar Quraan Academic Year"
ACADEMIC_TERM_DOCTYPE = "Dar Quraan Academic Term"


class TestDarQuraanStudentAssignment(FrappeTestCase):
    """Integration tests for Dar Quraan Student Assignment."""

    def setUp(self):
        super().setUp()

        self.token = frappe.generate_hash(length=8).upper()
        self.today = getdate(nowdate())

        self.year_start = add_days(self.today, -180)
        self.year_end = add_days(self.today, 180)
        self.term_start = add_days(self.today, -90)
        self.term_end = add_days(self.today, 90)

        self.branch = self._insert_fixture(
            BRANCH_DOCTYPE,
            f"DQB-TEST-{self.token}",
            {
                "branch_name": f"Test Branch {self.token}",
                "status": "Active",
            },
        )

        self.other_branch = self._insert_fixture(
            BRANCH_DOCTYPE,
            f"DQB-OTHER-{self.token}",
            {
                "branch_name": f"Other Branch {self.token}",
                "status": "Active",
            },
        )

        self.location = self._insert_fixture(
            LOCATION_DOCTYPE,
            f"DQTL-TEST-{self.token}",
            {
                "location_name": f"Test Location {self.token}",
                "status": "Active",
                "branch": self.branch,
            },
        )

        self.other_location = self._insert_fixture(
            LOCATION_DOCTYPE,
            f"DQTL-OTHER-{self.token}",
            {
                "location_name": f"Other Location {self.token}",
                "status": "Active",
                "branch": self.other_branch,
            },
        )

        self.teacher = self._insert_fixture(
            TEACHER_DOCTYPE,
            f"DQT-TEST-{self.token}",
            {
                "teacher_name": f"Test Teacher {self.token}",
                "status": "Active",
                "branch": self.branch,
            },
        )

        self.other_teacher = self._insert_fixture(
            TEACHER_DOCTYPE,
            f"DQT-OTHER-{self.token}",
            {
                "teacher_name": f"Other Teacher {self.token}",
                "status": "Active",
                "branch": self.other_branch,
            },
        )

        self.academic_year = self._insert_fixture(
            ACADEMIC_YEAR_DOCTYPE,
            f"DQAY-TEST-{self.token}",
            {
                "academic_year_name": f"Academic Year {self.token}",
                "status": "Active",
                "start_date": self.year_start,
                "end_date": self.year_end,
            },
        )

        self.other_academic_year = self._insert_fixture(
            ACADEMIC_YEAR_DOCTYPE,
            f"DQAY-OTHER-{self.token}",
            {
                "academic_year_name": f"Other Academic Year {self.token}",
                "status": "Active",
                "start_date": self.year_start,
                "end_date": self.year_end,
            },
        )

        self.academic_term = self._insert_fixture(
            ACADEMIC_TERM_DOCTYPE,
            f"DQAT-TEST-{self.token}",
            {
                "academic_term_name": f"Academic Term {self.token}",
                "status": "Active",
                "academic_year": self.academic_year,
                "start_date": self.term_start,
                "end_date": self.term_end,
            },
        )

        self.other_academic_term = self._insert_fixture(
            ACADEMIC_TERM_DOCTYPE,
            f"DQAT-OTHER-{self.token}",
            {
                "academic_term_name": f"Other Academic Term {self.token}",
                "status": "Active",
                "academic_year": self.other_academic_year,
                "start_date": self.term_start,
                "end_date": self.term_end,
            },
        )

        self.halaqa = self._insert_fixture(
            HALAQA_DOCTYPE,
            f"DQH-TEST-{self.token}",
            {
                "halaqa_name": f"Test Halaqa {self.token}",
                "status": "Active",
                "branch": self.branch,
                "mentor": self.teacher,
                "teaching_location": self.location,
                "academic_year": self.academic_year,
                "academic_term": self.academic_term,
                "allow_new_enrollments": 1,
            },
        )

        self.student = self._insert_fixture(
            STUDENT_DOCTYPE,
            f"DQS-TEST-{self.token}",
            {
                "student_name": f"Test Student {self.token}",
                "student_code": f"TEST-{self.token}",
                "status": "Active",
                "disabled": 0,
                "study_track": "Hifz",
                "current_riwayah": "Hafs",
                "default_branch": None,
                "default_teacher": None,
                "default_halaqa": None,
            },
        )

    def _insert_fixture(self, doctype: str, name: str, values: dict) -> str:
        meta = frappe.get_meta(doctype)
        valid_fields = {df.fieldname for df in meta.fields}

        data = {"doctype": doctype, "name": name}
        for fieldname, value in values.items():
            if fieldname in valid_fields:
                data[fieldname] = value

        doc = frappe.get_doc(data)
        doc.flags.name_set = True
        doc.db_insert()
        return doc.name

    def _set_fixture_value(self, doctype: str, name: str, fieldname: str, value):
        if frappe.get_meta(doctype).has_field(fieldname):
            frappe.db.set_value(
                doctype,
                name,
                fieldname,
                value,
                update_modified=False,
            )

    def _assignment_values(self, **overrides) -> dict:
        values = {
            "doctype": ASSIGNMENT_DOCTYPE,
            "naming_series": "DQSA-.YYYY.-.#####",
            "student": self.student,
            "assignment_type": "Primary",
            "status": "Active",
            "branch": self.branch,
            "teaching_location": self.location,
            "teacher": self.teacher,
            "halaqa": self.halaqa,
            "academic_year": self.academic_year,
            "academic_term": self.academic_term,
            "start_date": add_days(self.today, -10),
            "end_date": add_days(self.today, 10),
            "study_track": "Hifz",
            "riwayah": "Hafs",
        }
        values.update(overrides)
        return values

    def _insert_assignment(self, **overrides):
        doc = frappe.get_doc(self._assignment_values(**overrides))
        doc.insert(ignore_permissions=True)
        return doc

    def _assert_validation_error(self, expected_text: str, **overrides):
        with self.assertRaises(frappe.ValidationError) as context:
            self._insert_assignment(**overrides)

        self.assertIn(expected_text, str(context.exception))

    def test_valid_assignment_is_created(self):
        assignment = self._insert_assignment()
        self.assertTrue(assignment.name)
        self.assertEqual(assignment.student, self.student)

    def test_assignment_uses_expected_naming_series(self):
        assignment = self._insert_assignment()
        self.assertTrue(assignment.name.startswith("DQSA-"))

    def test_student_name_is_fetched(self):
        assignment = self._insert_assignment(student_name="Wrong Name")
        expected_name = frappe.db.get_value(
            STUDENT_DOCTYPE, self.student, "student_name"
        )
        self.assertEqual(assignment.student_name, expected_name)

    def test_student_track_and_riwayah_are_fetched_when_empty(self):
        assignment = self._insert_assignment(study_track=None, riwayah=None)
        self.assertEqual(assignment.study_track, "Hifz")
        self.assertEqual(assignment.riwayah, "Hafs")

    def test_halaqa_can_fill_missing_organizational_fields(self):
        assignment = self._insert_assignment(
            branch=None,
            teacher=None,
            teaching_location=None,
        )
        self.assertEqual(assignment.branch, self.branch)
        self.assertEqual(assignment.teacher, self.teacher)
        self.assertEqual(assignment.teaching_location, self.location)

    def test_effective_dates_are_generated(self):
        assignment = self._insert_assignment(
            effective_from=None,
            effective_to=None,
        )
        self.assertEqual(
            getdate(assignment.effective_from),
            getdate(assignment.start_date),
        )
        self.assertEqual(
            getdate(assignment.effective_to),
            getdate(assignment.end_date),
        )

    def test_active_assignment_in_current_period_is_current(self):
        assignment = self._insert_assignment()
        self.assertEqual(cint(assignment.is_current_assignment), 1)

    def test_future_assignment_is_not_current(self):
        assignment = self._insert_assignment(
            start_date=add_days(self.today, 20),
            end_date=add_days(self.today, 30),
        )
        self.assertEqual(cint(assignment.is_current_assignment), 0)

    def test_expired_assignment_is_not_current(self):
        assignment = self._insert_assignment(
            status="Completed",
            start_date=add_days(self.today, -30),
            end_date=add_days(self.today, -20),
        )
        self.assertEqual(cint(assignment.is_current_assignment), 0)

    def test_non_active_assignment_is_not_current(self):
        assignment = self._insert_assignment(status="Suspended")
        self.assertEqual(cint(assignment.is_current_assignment), 0)

    def test_student_is_required(self):
        self._assert_validation_error("Student is required", student=None)

    def test_branch_is_required_without_halaqa_autofill(self):
        self._assert_validation_error(
            "Branch is required",
            branch=None,
            halaqa=None,
        )

    def test_teacher_is_required_without_halaqa_autofill(self):
        self._assert_validation_error(
            "Teacher is required",
            teacher=None,
            halaqa=None,
        )

    def test_academic_year_is_required(self):
        self._assert_validation_error(
            "Academic Year is required",
            academic_year=None,
            academic_term=None,
            halaqa=None,
        )

    def test_start_date_is_required(self):
        self._assert_validation_error(
            "Start Date is required",
            start_date=None,
            effective_from=None,
        )

    def test_inactive_student_is_rejected(self):
        self._set_fixture_value(STUDENT_DOCTYPE, self.student, "status", "Inactive")
        self._assert_validation_error("must be Active")

    def test_disabled_student_is_rejected(self):
        self._set_fixture_value(STUDENT_DOCTYPE, self.student, "disabled", 1)
        self._assert_validation_error("Disabled students cannot be assigned")

    def test_inactive_branch_is_rejected(self):
        self._set_fixture_value(BRANCH_DOCTYPE, self.branch, "status", "Inactive")
        self._assert_validation_error("must be Active")

def test_inactive_teacher_is_rejected(self):
    meta = frappe.get_meta(TEACHER_DOCTYPE)

    if meta.has_field("status"):
        self._set_fixture_value(
            TEACHER_DOCTYPE,
            self.teacher,
            "status",
            "Inactive",
        )

    elif meta.has_field("disabled"):
        self._set_fixture_value(
            TEACHER_DOCTYPE,
            self.teacher,
            "disabled",
            1,
        )

    elif meta.has_field("is_active"):
        self._set_fixture_value(
            TEACHER_DOCTYPE,
            self.teacher,
            "is_active",
            0,
        )

    elif meta.has_field("enabled"):
        self._set_fixture_value(
            TEACHER_DOCTYPE,
            self.teacher,
            "enabled",
            0,
        )

    else:
        self.skipTest(
            "Dar Quraan Teacher has no active/inactive field."
        )

    with self.assertRaises(frappe.ValidationError):
        self._insert_assignment()

    def test_inactive_location_is_rejected(self):
        self._set_fixture_value(LOCATION_DOCTYPE, self.location, "status", "Inactive")
        self._assert_validation_error("must be Active")

    def test_inactive_halaqa_is_rejected(self):
        self._set_fixture_value(HALAQA_DOCTYPE, self.halaqa, "status", "Inactive")
        self._assert_validation_error("must be Active")

    def test_location_branch_must_match_assignment_branch(self):
        self._assert_validation_error(
            "belongs to Branch",
            teaching_location=self.other_location,
        )

def test_teacher_branch_must_match_assignment_branch(self):
    meta = frappe.get_meta(TEACHER_DOCTYPE)

    if not meta.has_field("branch"):
        self.skipTest(
            "Dar Quraan Teacher has no branch field."
        )

    self._set_fixture_value(
        TEACHER_DOCTYPE,
        self.other_teacher,
        "branch",
        self.other_branch,
    )

    self._assert_validation_error(
        "belongs to Branch",
        teacher=self.other_teacher,
        halaqa=None,
    )

    def test_halaqa_branch_must_match_assignment_branch(self):
        self._set_fixture_value(
            HALAQA_DOCTYPE, self.halaqa, "branch", self.other_branch
        )
        self._assert_validation_error("belongs to Branch")

    def test_halaqa_teacher_must_match_selected_teacher(self):
        self._set_fixture_value(
            HALAQA_DOCTYPE, self.halaqa, "mentor", self.other_teacher
        )
        self._assert_validation_error("is assigned to Teacher")

    def test_halaqa_location_must_match_selected_location(self):
        self._set_fixture_value(
            HALAQA_DOCTYPE,
            self.halaqa,
            "teaching_location",
            self.other_location,
        )
        self._assert_validation_error("uses Teaching Location")

    def test_halaqa_academic_year_must_match(self):
        self._set_fixture_value(
            HALAQA_DOCTYPE,
            self.halaqa,
            "academic_year",
            self.other_academic_year,
        )
        self._assert_validation_error("belongs to Academic Year")

    def test_halaqa_academic_term_must_match(self):
        self._set_fixture_value(
            HALAQA_DOCTYPE,
            self.halaqa,
            "academic_term",
            self.other_academic_term,
        )
        self._assert_validation_error("belongs to Academic Term")

    def test_new_active_assignment_requires_open_halaqa_enrollment(self):
        self._set_fixture_value(
            HALAQA_DOCTYPE,
            self.halaqa,
            "allow_new_enrollments",
            0,
        )
        self._assert_validation_error(
            "does not currently allow new student assignments"
        )

    def test_academic_term_must_belong_to_selected_year(self):
        self._assert_validation_error(
            "belongs to Academic Year",
            academic_term=self.other_academic_term,
            halaqa=None,
        )

    def test_assignment_start_cannot_precede_academic_year(self):
        self._assert_validation_error(
            "earlier than Academic Year start date",
            start_date=add_days(self.year_start, -1),
            academic_term=None,
            halaqa=None,
        )

    def test_assignment_end_cannot_exceed_academic_year(self):
        self._assert_validation_error(
            "later than Academic Year end date",
            end_date=add_days(self.year_end, 1),
            academic_term=None,
            halaqa=None,
        )

    def test_assignment_start_cannot_precede_academic_term(self):
        self._assert_validation_error(
            "earlier than Academic Term start date",
            start_date=add_days(self.term_start, -1),
            halaqa=None,
        )

    def test_assignment_end_cannot_exceed_academic_term(self):
        self._assert_validation_error(
            "later than Academic Term end date",
            end_date=add_days(self.term_end, 1),
            halaqa=None,
        )

    def test_end_date_cannot_be_before_start_date(self):
        self._assert_validation_error(
            "End Date cannot be earlier than Start Date",
            start_date=self.today,
            end_date=add_days(self.today, -1),
            effective_from=None,
            effective_to=None,
        )

    def test_completed_assignment_requires_end_date(self):
        self._assert_validation_error(
            "End Date is required for a Completed assignment",
            status="Completed",
            end_date=None,
            effective_to=None,
        )

    def test_effective_to_cannot_precede_effective_from(self):
        self._assert_validation_error(
            "Effective To cannot be earlier than Effective From",
            effective_from=f"{self.today} 12:00:00",
            effective_to=f"{self.today} 11:00:00",
        )

    def test_effective_from_cannot_precede_start_date(self):
        start_date = add_days(self.today, -5)
        self._assert_validation_error(
            "Effective From cannot be earlier",
            start_date=start_date,
            effective_from=f"{add_days(start_date, -1)} 12:00:00",
        )

    def test_effective_to_cannot_exceed_end_date(self):
        end_date = add_days(self.today, 5)
        self._assert_validation_error(
            "Effective To cannot be later",
            end_date=end_date,
            effective_to=f"{add_days(end_date, 1)} 12:00:00",
        )

    def test_invalid_assignment_type_is_rejected(self):
        self._assert_validation_error(
            "Assignment Type must be one of",
            assignment_type="Invalid",
        )

    def test_transfer_requires_reason(self):
        self._assert_validation_error(
            "Transfer Reason is required",
            assignment_type="Transfer",
            transfer_reason=None,
        )

    def test_non_transfer_clears_transfer_reason(self):
        assignment = self._insert_assignment(
            assignment_type="Temporary",
            transfer_reason="Should be removed",
        )
        self.assertFalse(assignment.transfer_reason)

    def test_invalid_status_is_rejected(self):
        self._assert_validation_error(
            "Invalid assignment status",
            status="Invalid",
        )

    def test_student_cannot_have_two_active_primary_assignments(self):
        first = self._insert_assignment()
        self.assertTrue(first.name)

        self._assert_validation_error(
            "already has an Active Primary Assignment",
            halaqa=None,
            teaching_location=None,
            start_date=add_days(self.today, -5),
            end_date=add_days(self.today, 5),
        )

    def test_overlapping_completed_primary_assignments_are_rejected(self):
        first = self._insert_assignment(
            status="Completed",
            start_date=add_days(self.today, -40),
            end_date=add_days(self.today, -20),
        )
        self.assertTrue(first.name)

        self._assert_validation_error(
            "overlaps with Primary Assignment",
            status="Completed",
            start_date=add_days(self.today, -30),
            end_date=add_days(self.today, -10),
            halaqa=None,
            teaching_location=None,
        )

    def test_non_overlapping_completed_primary_assignments_are_allowed(self):
        first = self._insert_assignment(
            status="Completed",
            start_date=add_days(self.today, -50),
            end_date=add_days(self.today, -40),
        )
        self.assertTrue(first.name)

        second = self._insert_assignment(
            status="Completed",
            start_date=add_days(self.today, -30),
            end_date=add_days(self.today, -20),
            halaqa=None,
            teaching_location=None,
        )
        self.assertTrue(second.name)

    def test_temporary_assignments_may_overlap_primary_assignment(self):
        primary = self._insert_assignment()
        self.assertTrue(primary.name)

        temporary = self._insert_assignment(
            assignment_type="Temporary",
            halaqa=None,
            teaching_location=None,
        )
        self.assertTrue(temporary.name)

    def test_negative_legacy_assignment_id_is_rejected(self):
        self._assert_validation_error(
            "Legacy Assignment ID cannot be negative",
            legacy_assignment_id=-1,
        )

    def test_duplicate_legacy_assignment_id_is_rejected(self):
        first = self._insert_assignment(
            status="Draft",
            legacy_assignment_id=901001,
        )
        self.assertTrue(first.name)

        self._assert_validation_error(
            "Legacy Assignment ID",
            status="Draft",
            legacy_assignment_id=901001,
            halaqa=None,
            teaching_location=None,
        )

    def test_legacy_updated_at_cannot_precede_created_at(self):
        self._assert_validation_error(
            "Legacy Updated At cannot be earlier",
            legacy_created_at=f"{self.today} 12:00:00",
            legacy_updated_at=f"{add_days(self.today, -1)} 12:00:00",
        )

    def test_current_active_primary_assignment_updates_student_defaults(self):
        assignment = self._insert_assignment()

        student = frappe.db.get_value(
            STUDENT_DOCTYPE,
            self.student,
            ["default_branch", "default_teacher", "default_halaqa"],
            as_dict=True,
        )

        self.assertEqual(student.default_branch, assignment.branch)
        self.assertEqual(student.default_teacher, assignment.teacher)
        self.assertEqual(student.default_halaqa, assignment.halaqa)

    def test_completing_assignment_clears_matching_student_defaults(self):
        assignment = self._insert_assignment()

        assignment.status = "Completed"
        assignment.end_date = self.today
        assignment.save(ignore_permissions=True)

        student = frappe.db.get_value(
            STUDENT_DOCTYPE,
            self.student,
            ["default_branch", "default_teacher", "default_halaqa"],
            as_dict=True,
        )

        self.assertFalse(student.default_branch)
        self.assertFalse(student.default_teacher)
        self.assertFalse(student.default_halaqa)

    def test_future_primary_assignment_does_not_update_student_defaults(self):
        assignment = self._insert_assignment(
            start_date=add_days(self.today, 20),
            end_date=add_days(self.today, 30),
        )
        self.assertEqual(cint(assignment.is_current_assignment), 0)

        student = frappe.db.get_value(
            STUDENT_DOCTYPE,
            self.student,
            ["default_branch", "default_teacher", "default_halaqa"],
            as_dict=True,
        )

        self.assertFalse(student.default_branch)
        self.assertFalse(student.default_teacher)
        self.assertFalse(student.default_halaqa)

    def test_active_assignment_cannot_be_deleted(self):
        assignment = self._insert_assignment()

        with self.assertRaises(frappe.ValidationError) as context:
            assignment.delete(ignore_permissions=True)

        self.assertIn(
            "Only Draft or Cancelled Student Assignments can be deleted",
            str(context.exception),
        )

    def test_draft_assignment_can_be_deleted(self):
        assignment = self._insert_assignment(status="Draft")
        assignment_name = assignment.name
        assignment.delete(ignore_permissions=True)

        self.assertFalse(
            frappe.db.exists(ASSIGNMENT_DOCTYPE, assignment_name)
        )

    def test_cancelled_assignment_can_be_deleted(self):
        assignment = self._insert_assignment(status="Cancelled")
        assignment_name = assignment.name
        assignment.delete(ignore_permissions=True)

        self.assertFalse(
            frappe.db.exists(ASSIGNMENT_DOCTYPE, assignment_name)
        )


if __name__ == "__main__":
    unittest.main()
