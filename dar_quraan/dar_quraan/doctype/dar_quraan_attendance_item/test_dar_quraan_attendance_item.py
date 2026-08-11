import frappe
from frappe.tests.utils import FrappeTestCase


class TestDarQuraanAttendanceItem(
    FrappeTestCase
):
    def make_item(
        self,
        **kwargs,
    ):
        data = {
            "doctype": (
                "Dar Quraan Attendance Item"
            ),
            "student": "DQ-STUDENT-TEST",
            "student_name": "Ahmad Test",
            "student_assignment": "DQ-SA-TEST",
            "attendance_status": "Present",
            "late_minutes": 0,
        }

        data.update(
            kwargs
        )

        return frappe.get_doc(
            data
        )

    def test_valid_present_item(self):
        item = self.make_item()

        item.validate()

        self.assertEqual(
            item.attendance_status,
            "Present",
        )

    def test_student_is_required(self):
        item = self.make_item(
            student=None,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_student_assignment_is_required(self):
        item = self.make_item(
            student_assignment=None,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_all_statuses_are_valid(self):
        statuses = [
            "Present",
            "Absent",
            "Late",
            "Excused",
        ]

        for status in statuses:
            kwargs = {
                "attendance_status": status
            }

            if status == "Late":
                kwargs["late_minutes"] = 10

            if status == "Excused":
                kwargs["excuse_reason"] = (
                    "Medical"
                )

            item = self.make_item(
                **kwargs
            )

            item.validate()

            self.assertEqual(
                item.attendance_status,
                status,
            )

    def test_invalid_status_is_rejected(self):
        item = self.make_item(
            attendance_status="Unknown",
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_negative_late_minutes_rejected(self):
        item = self.make_item(
            attendance_status="Late",
            late_minutes=-1,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_late_requires_late_minutes(self):
        item = self.make_item(
            attendance_status="Late",
            late_minutes=0,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_present_resets_late_minutes(self):
        item = self.make_item(
            attendance_status="Present",
            late_minutes=20,
        )

        item.validate()

        self.assertEqual(
            item.late_minutes,
            0,
        )

    def test_excused_requires_reason(self):
        item = self.make_item(
            attendance_status="Excused",
            excuse_reason=None,
        )

        with self.assertRaises(
            frappe.ValidationError
        ):
            item.validate()

    def test_excused_with_reason_is_valid(self):
        item = self.make_item(
            attendance_status="Excused",
            excuse_reason="Medical",
        )

        item.validate()

        self.assertEqual(
            item.excuse_reason,
            "Medical",
        )

    def test_non_excused_clears_reason(self):
        item = self.make_item(
            attendance_status="Present",
            excuse_reason="Old reason",
        )

        item.validate()

        self.assertIsNone(
            item.excuse_reason
        )