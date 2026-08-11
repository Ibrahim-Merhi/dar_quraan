from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanAttendance(FrappeTestCase):
    def make_session(
        self,
        **kwargs,
    ):
        data = {
            "name": "DQ-SES-TEST-00001",
            "session_date": "2026-08-11",
            "halaqa": "DQH-TEST",
            "halaqa_name": "Test Halaqa",
            "branch": "DQB-TEST",
            "teaching_location": "DQTL-TEST",
            "teacher": "DQT-TEST",
            "academic_year": "DQAY-TEST",
            "academic_term": "DQAT-TEST",
            "status": "Planned",
        }

        data.update(kwargs)

        return frappe._dict(data)

    def make_assignment(
        self,
        name="DQ-SA-TEST-001",
        student="DQ-STUDENT-001",
        student_name="Student One",
        halaqa="DQH-TEST",
    ):
        return frappe._dict(
            {
                "name": name,
                "student": student,
                "student_name": student_name,
                "halaqa": halaqa,
            }
        )

    def make_attendance(
        self,
        **kwargs,
    ):
        data = {
            "doctype": "Dar Quraan Attendance",
            "session": "DQ-SES-TEST-00001",
            "status": "Draft",
            "attendance_items": [],
        }

        data.update(kwargs)

        return frappe.get_doc(data)

    def validate_attendance(
        self,
        attendance,
        session=None,
        assignments=None,
        existing_attendance=None,
        session_exists=True,
    ):
        if session is None:
            session = self.make_session()

        if assignments is None:
            assignments = [
                self.make_assignment(
                    name="DQ-SA-TEST-001",
                    student="DQ-STUDENT-001",
                    student_name="Student One",
                ),
                self.make_assignment(
                    name="DQ-SA-TEST-002",
                    student="DQ-STUDENT-002",
                    student_name="Student Two",
                ),
            ]

        original_get_doc = frappe.get_doc
        original_get_meta = frappe.get_meta
        original_get_value = frappe.db.get_value

        def fake_get_doc(
            *args,
            **kwargs,
        ):
            if (
                len(args) >= 2
                and args[0] == "Dar Quraan Session"
                and args[1] == "DQ-SES-TEST-00001"
            ):
                return session

            return original_get_doc(
                *args,
                **kwargs,
            )

        def fake_exists(
            doctype,
            filters=None,
            *args,
            **kwargs,
        ):
            if doctype == "Dar Quraan Session":
                if (
                    session_exists
                    and filters == "DQ-SES-TEST-00001"
                ):
                    return "DQ-SES-TEST-00001"

                return None

            if doctype == "Dar Quraan Attendance":
                return existing_attendance

            if doctype == "Dar Quraan Student Assignment":
                if isinstance(filters, str):
                    for assignment in assignments:
                        if assignment.name == filters:
                            return assignment.name

                return None

            return None

        def fake_get_all(
            doctype,
            *args,
            **kwargs,
        ):
            if (
                doctype
                == "Dar Quraan Student Assignment"
            ):
                return assignments

            return []

        def fake_get_value(
            doctype,
            name,
            fields,
            *args,
            **kwargs,
        ):
            if (
                doctype
                == "Dar Quraan Student Assignment"
            ):
                for assignment in assignments:
                    if assignment.name == name:
                        if kwargs.get("as_dict"):
                            return frappe._dict(
                                {
                                    "student": (
                                        assignment.student
                                    ),
                                    "halaqa": (
                                        assignment.halaqa
                                    ),
                                }
                            )

                        if fields == "student":
                            return assignment.student

                        if fields == "halaqa":
                            return assignment.halaqa

            return original_get_value(
                doctype,
                name,
                fields,
                *args,
                **kwargs,
            )

        def fake_get_meta(
            doctype,
            *args,
            **kwargs,
        ):
            # Only fake Student Assignment metadata.
            # All other DocTypes must use their real metadata,
            # especially Dar Quraan Attendance Item.
            if (
                doctype
                == "Dar Quraan Student Assignment"
            ):
                fake_meta = frappe._dict()

                fake_meta.has_field = (
                    lambda fieldname:
                    fieldname
                    in {
                        "status",
                        "student_name",
                    }
                )

                return fake_meta

            return original_get_meta(
                doctype,
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
                "exists",
                side_effect=fake_exists,
            ),
            patch.object(
                frappe,
                "get_all",
                side_effect=fake_get_all,
            ),
            patch.object(
                frappe.db,
                "get_value",
                side_effect=fake_get_value,
            ),
            patch.object(
                frappe,
                "get_meta",
                side_effect=fake_get_meta,
            ),
        ):
            attendance.validate()

    # ---------------------------------------------------------
    # Basic validation
    # ---------------------------------------------------------

    def test_valid_attendance(self):
        attendance = self.make_attendance()

        self.validate_attendance(
            attendance
        )

        self.assertEqual(
            attendance.halaqa,
            "DQH-TEST",
        )

        self.assertEqual(
            str(attendance.attendance_date),
            "2026-08-11",
        )

        self.assertEqual(
            attendance.status,
            "Draft",
        )

    def test_session_is_required(self):
        attendance = self.make_attendance(
            session=None,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            attendance.validate()

    def test_invalid_session_is_rejected(self):
        attendance = self.make_attendance()

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_attendance(
                attendance,
                session_exists=False,
            )

    # ---------------------------------------------------------
    # Session context
    # ---------------------------------------------------------

    def test_session_context_is_fetched(self):
        attendance = self.make_attendance(
            attendance_date="2000-01-01",
            halaqa="WRONG",
            halaqa_name="Wrong",
            branch="WRONG",
            teaching_location="WRONG",
            teacher="WRONG",
            academic_year="WRONG",
            academic_term="WRONG",
        )

        self.validate_attendance(
            attendance
        )

        self.assertEqual(
            str(attendance.attendance_date),
            "2026-08-11",
        )

        self.assertEqual(
            attendance.halaqa,
            "DQH-TEST",
        )

        self.assertEqual(
            attendance.halaqa_name,
            "Test Halaqa",
        )

        self.assertEqual(
            attendance.branch,
            "DQB-TEST",
        )

        self.assertEqual(
            attendance.teaching_location,
            "DQTL-TEST",
        )

        self.assertEqual(
            attendance.teacher,
            "DQT-TEST",
        )

        self.assertEqual(
            attendance.academic_year,
            "DQAY-TEST",
        )

        self.assertEqual(
            attendance.academic_term,
            "DQAT-TEST",
        )

    def test_cancelled_session_rejected(self):
        attendance = self.make_attendance()

        session = self.make_session(
            status="Cancelled",
        )

        with self.assertRaisesRegex(
            frappe.ValidationError,
            "Cancelled Session",
        ):
            self.validate_attendance(
                attendance,
                session=session,
            )

    def test_session_without_date_rejected(self):
        attendance = self.make_attendance()

        session = self.make_session(
            session_date=None,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_attendance(
                attendance,
                session=session,
            )

    def test_session_without_halaqa_rejected(self):
        attendance = self.make_attendance()

        session = self.make_session(
            halaqa=None,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_attendance(
                attendance,
                session=session,
            )

    # ---------------------------------------------------------
    # One attendance per session
    # ---------------------------------------------------------

    def test_duplicate_attendance_rejected(self):
        attendance = self.make_attendance()

        with self.assertRaisesRegex(
            frappe.ValidationError,
            "Attendance already exists",
        ):
            self.validate_attendance(
                attendance,
                existing_attendance="DQ-ATT-OLD",
            )

    # ---------------------------------------------------------
    # Automatic student population
    # ---------------------------------------------------------

    def test_students_are_auto_populated(self):
        attendance = self.make_attendance()

        self.validate_attendance(
            attendance
        )

        self.assertEqual(
            len(attendance.attendance_items),
            2,
        )

        self.assertEqual(
            attendance.attendance_items[0].student,
            "DQ-STUDENT-001",
        )

        self.assertEqual(
            attendance.attendance_items[0].student_name,
            "Student One",
        )

        self.assertEqual(
            attendance.attendance_items[
                0
            ].student_assignment,
            "DQ-SA-TEST-001",
        )

        self.assertEqual(
            attendance.attendance_items[
                0
            ].attendance_status,
            "Present",
        )

    def test_existing_items_are_not_repopulated(self):
        attendance = self.make_attendance(
            attendance_items=[
                {
                    "doctype": (
                        "Dar Quraan Attendance Item"
                    ),
                    "student": "DQ-STUDENT-001",
                    "student_name": "Student One",
                    "student_assignment": (
                        "DQ-SA-TEST-001"
                    ),
                    "attendance_status": "Absent",
                }
            ],
        )

        assignments = [
            self.make_assignment(
                name="DQ-SA-TEST-001",
                student="DQ-STUDENT-001",
                student_name="Student One",
            )
        ]

        self.validate_attendance(
            attendance,
            assignments=assignments,
        )

        self.assertEqual(
            len(attendance.attendance_items),
            1,
        )

        self.assertEqual(
            attendance.attendance_items[
                0
            ].attendance_status,
            "Absent",
        )

    def test_no_students_available_is_rejected(self):
        attendance = self.make_attendance()

        with self.assertRaisesRegex(
            frappe.ValidationError,
            "No students are available",
        ):
            self.validate_attendance(
                attendance,
                assignments=[],
            )

    # ---------------------------------------------------------
    # Student Assignment validation
    # ---------------------------------------------------------

    def test_student_must_match_assignment(self):
        attendance = self.make_attendance(
            attendance_items=[
                {
                    "doctype": (
                        "Dar Quraan Attendance Item"
                    ),
                    "student": "WRONG-STUDENT",
                    "student_assignment": (
                        "DQ-SA-TEST-001"
                    ),
                    "attendance_status": "Present",
                }
            ],
        )

        assignments = [
            self.make_assignment(
                name="DQ-SA-TEST-001",
                student="DQ-STUDENT-001",
            )
        ]

        with self.assertRaisesRegex(
            frappe.ValidationError,
            "does not match",
        ):
            self.validate_attendance(
                attendance,
                assignments=assignments,
            )

    def test_assignment_from_other_halaqa_rejected(
        self,
    ):
        attendance = self.make_attendance(
            attendance_items=[
                {
                    "doctype": (
                        "Dar Quraan Attendance Item"
                    ),
                    "student": "S1",
                    "student_assignment": "A1",
                    "attendance_status": "Present",
                }
            ],
        )

        assignments = [
            self.make_assignment(
                name="A1",
                student="S1",
                halaqa="OTHER-HALAQA",
            )
        ]

        with self.assertRaisesRegex(
            frappe.ValidationError,
            "does not belong to this Halaqa",
        ):
            self.validate_attendance(
                attendance,
                assignments=assignments,
            )

    def test_duplicate_student_assignment_rejected(
        self,
    ):
        attendance = self.make_attendance(
            attendance_items=[
                {
                    "doctype": (
                        "Dar Quraan Attendance Item"
                    ),
                    "student": "S1",
                    "student_assignment": "A1",
                    "attendance_status": "Present",
                },
                {
                    "doctype": (
                        "Dar Quraan Attendance Item"
                    ),
                    "student": "S1",
                    "student_assignment": "A1",
                    "attendance_status": "Present",
                },
            ],
        )

        assignments = [
            self.make_assignment(
                name="A1",
                student="S1",
            )
        ]

        with self.assertRaisesRegex(
            frappe.ValidationError,
            "appears more than once",
        ):
            self.validate_attendance(
                attendance,
                assignments=assignments,
            )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    def test_summary_is_calculated(self):
        attendance = self.make_attendance(
            attendance_items=[
                {
                    "doctype": (
                        "Dar Quraan Attendance Item"
                    ),
                    "student": "S1",
                    "student_assignment": "A1",
                    "attendance_status": "Present",
                },
                {
                    "doctype": (
                        "Dar Quraan Attendance Item"
                    ),
                    "student": "S2",
                    "student_assignment": "A2",
                    "attendance_status": "Absent",
                },
                {
                    "doctype": (
                        "Dar Quraan Attendance Item"
                    ),
                    "student": "S3",
                    "student_assignment": "A3",
                    "attendance_status": "Late",
                    "late_minutes": 10,
                },
                {
                    "doctype": (
                        "Dar Quraan Attendance Item"
                    ),
                    "student": "S4",
                    "student_assignment": "A4",
                    "attendance_status": "Excused",
                    "excuse_reason": "Medical",
                },
            ],
        )

        assignments = [
            self.make_assignment(
                name="A1",
                student="S1",
            ),
            self.make_assignment(
                name="A2",
                student="S2",
            ),
            self.make_assignment(
                name="A3",
                student="S3",
            ),
            self.make_assignment(
                name="A4",
                student="S4",
            ),
        ]

        self.validate_attendance(
            attendance,
            assignments=assignments,
        )

        self.assertEqual(
            attendance.total_students,
            4,
        )

        self.assertEqual(
            attendance.present_count,
            1,
        )

        self.assertEqual(
            attendance.absent_count,
            1,
        )

        self.assertEqual(
            attendance.late_count,
            1,
        )

        self.assertEqual(
            attendance.excused_count,
            1,
        )

    def test_all_present_summary(self):
        attendance = self.make_attendance()

        self.validate_attendance(
            attendance
        )

        self.assertEqual(
            attendance.total_students,
            2,
        )

        self.assertEqual(
            attendance.present_count,
            2,
        )

        self.assertEqual(
            attendance.absent_count,
            0,
        )

        self.assertEqual(
            attendance.late_count,
            0,
        )

        self.assertEqual(
            attendance.excused_count,
            0,
        )

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    def test_all_statuses_are_valid(self):
        statuses = [
            "Draft",
            "Completed",
            "Cancelled",
        ]

        for status in statuses:
            attendance = self.make_attendance(
                status=status,
            )

            self.validate_attendance(
                attendance
            )

            self.assertEqual(
                attendance.status,
                status,
            )

    def test_missing_status_defaults_to_draft(self):
        attendance = self.make_attendance(
            status=None,
        )

        self.validate_attendance(
            attendance
        )

        self.assertEqual(
            attendance.status,
            "Draft",
        )

    def test_invalid_status_rejected(self):
        attendance = self.make_attendance(
            status="Unknown",
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            self.validate_attendance(
                attendance
            )