from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate

from dar_quraan.dar_quraan.services import exceptions


def settings(**values):
	defaults = {
		"enable_exception_detection": 1,
		"absence_threshold": 3,
		"lateness_threshold": 3,
		"weak_result_threshold": 3,
		"no_progress_days": 7,
		"evaluation_overdue_days": 30,
		"follow_up_reminder_days": 1,
		"attendance_grace_days": 1,
		"enable_email_notifications": 0,
		"notification_recipients": "",
	}
	defaults.update(values)
	return frappe._dict(defaults)


class TestExceptionDetection(FrappeTestCase):
	def rows_for(self, values):
		def get_all(doctype, *args, **kwargs):
			return values.get(doctype, [])

		return get_all

	def test_disabled_detection_does_nothing(self):
		with (
			patch.object(
				frappe,
				"get_single",
				return_value=settings(enable_exception_detection=0),
			),
			patch.object(exceptions, "detect_overdue_follow_ups") as overdue,
		):
			self.assertEqual(exceptions.detect_daily_exceptions(), [])
			overdue.assert_not_called()

	def test_existing_open_exception_is_idempotent(self):
		doc = MagicMock(status="Open", occurrence_count=2)
		doc.flags = frappe._dict()
		with (
			patch.object(frappe.db, "get_value", return_value="DQ-EXC-001"),
			patch.object(frappe, "get_doc", return_value=doc),
		):
			result = exceptions.open_exception("Overdue Follow-up", "key", "Still overdue")
		self.assertIs(result, doc)
		self.assertEqual(doc.occurrence_count, 2)
		self.assertFalse(doc.flags.notify_exception)
		doc.save.assert_called_once_with(ignore_permissions=True)

	def test_resolved_exception_reopens_same_record(self):
		doc = MagicMock(
			status="Resolved",
			occurrence_count=2,
			resolution_notes="Cleared",
			resolved_on="2026-01-01",
		)
		doc.flags = frappe._dict()
		with (
			patch.object(frappe.db, "get_value", return_value="DQ-EXC-001"),
			patch.object(frappe, "get_doc", return_value=doc),
		):
			exceptions.open_exception("Overdue Follow-up", "key", "Again")
		self.assertEqual(doc.status, "Open")
		self.assertEqual(doc.occurrence_count, 3)
		self.assertIsNone(doc.resolution_notes)
		self.assertTrue(doc.flags.notify_exception)

	def test_new_exception_is_inserted(self):
		doc = MagicMock()
		doc.flags = frappe._dict()
		doc.insert.return_value = doc
		with (
			patch.object(frappe.db, "get_value", return_value=None),
			patch.object(frappe, "get_doc", return_value=doc) as get_doc,
		):
			self.assertIs(
				exceptions.open_exception("Halaqa Over Capacity", "key", "Over capacity"),
				doc,
			)
		self.assertEqual(get_doc.call_args.args[0]["duplicate_key"], "key")
		self.assertTrue(doc.flags.notify_exception)
		doc.insert.assert_called_once_with(ignore_permissions=True)

	def test_inactive_conditions_are_resolved(self):
		doc = MagicMock()
		with (
			patch.object(
				frappe,
				"get_all",
				return_value=[frappe._dict(name="EXC", duplicate_key="gone")],
			),
			patch.object(frappe, "get_doc", return_value=doc),
		):
			exceptions.resolve_inactive_exceptions("Repeated Absence", {"active"})
		self.assertEqual(doc.status, "Resolved")
		self.assertTrue(doc.resolution_notes)
		doc.save.assert_called_once_with(ignore_permissions=True)

	def test_repeated_absence_and_lateness_use_independent_thresholds(self):
		values = {
			"Dar Quraan Attendance": [frappe._dict(name="ATT-1"), frappe._dict(name="ATT-2")],
			"Dar Quraan Attendance Item": [
				frappe._dict(
					name="ITEM",
					parent="ATT-2",
					student_assignment="ASSIGN",
					attendance_status="Absent",
				),
				frappe._dict(
					name="ITEM2",
					parent="ATT-1",
					student_assignment="ASSIGN",
					attendance_status="Absent",
				),
			],
			"Dar Quraan Exception": [],
		}
		with (
			patch.object(frappe, "get_all", side_effect=self.rows_for(values)),
			patch.object(exceptions, "open_exception", return_value="EXC") as opener,
		):
			self.assertEqual(
				exceptions.detect_repeated_absence(settings=settings(absence_threshold=2)),
				["EXC"],
			)
			self.assertEqual(
				exceptions.detect_repeated_lateness(settings=settings(lateness_threshold=3)),
				[],
			)
		self.assertEqual(opener.call_args.args[0], "Repeated Absence")
		self.assertEqual(
			opener.call_args.kwargs["duplicate_key"],
			"repeated-absence:ASSIGN",
		)

	def test_repeated_weak_results_respect_threshold(self):
		values = {
			"Dar Quraan Evaluation": [
				frappe._dict(
					name=f"EVAL-{n}",
					student_assignment="ASSIGN",
					overall_result="Repeat",
				)
				for n in range(2)
			],
			"Dar Quraan Exception": [],
		}
		with (
			patch.object(frappe, "get_all", side_effect=self.rows_for(values)),
			patch.object(exceptions, "open_exception", return_value="EXC"),
		):
			self.assertEqual(
				exceptions.detect_repeated_weak_results(settings=settings(weak_result_threshold=2)),
				["EXC"],
			)

	def test_no_recent_progress_uses_assignment_context(self):
		values = {
			"Dar Quraan Student Assignment": [frappe._dict(name="ASSIGN", start_date="2026-01-01")],
			"Dar Quraan Student Progress": [],
			"Dar Quraan Exception": [],
		}
		with (
			patch.object(frappe, "get_all", side_effect=self.rows_for(values)),
			patch.object(exceptions, "open_exception", return_value="EXC") as opener,
		):
			self.assertEqual(
				exceptions.detect_no_recent_progress(
					settings=settings(no_progress_days=7), as_of="2026-01-10"
				),
				["EXC"],
			)
		self.assertEqual(opener.call_args.kwargs["student_assignment"], "ASSIGN")
		self.assertEqual(
			opener.call_args.kwargs["source_doctype"],
			"Dar Quraan Student Assignment",
		)

	def test_missing_attendance_observes_grace_days(self):
		values = {
			"Dar Quraan Session": [frappe._dict(name="SESSION", halaqa="HALAQA")],
			"Dar Quraan Attendance": [],
			"Dar Quraan Exception": [],
		}
		with (
			patch.object(frappe, "get_all", side_effect=self.rows_for(values)) as get_all,
			patch.object(exceptions, "open_exception", return_value="EXC"),
		):
			self.assertEqual(
				exceptions.detect_missing_attendance(
					settings=settings(attendance_grace_days=2),
					as_of="2026-01-10",
				),
				["EXC"],
			)
		session_call = get_all.call_args_list[0]
		self.assertEqual(
			session_call.kwargs["filters"]["session_date"],
			["<=", getdate("2026-01-08")],
		)

	def test_overdue_follow_ups_use_reminder_days(self):
		values = {
			"Dar Quraan Teacher Follow Up": [frappe._dict(name="FUP-001", student_assignment="ASSIGN-001")],
			"Dar Quraan Exception": [],
		}
		with (
			patch.object(frappe, "get_all", side_effect=self.rows_for(values)) as get_all,
			patch.object(exceptions, "open_exception", return_value="EXCEPTION") as opener,
		):
			self.assertEqual(
				exceptions.detect_overdue_follow_ups(
					settings=settings(follow_up_reminder_days=2),
					as_of="2026-01-10",
				),
				["EXCEPTION"],
			)
		self.assertEqual(
			get_all.call_args_list[0].kwargs["filters"]["next_follow_up_date"],
			["<=", getdate("2026-01-08")],
		)
		self.assertEqual(opener.call_args.kwargs["duplicate_key"], "overdue-follow-up:FUP-001")

	def test_overdue_evaluation_uses_latest_completed_date(self):
		values = {
			"Dar Quraan Student Assignment": [frappe._dict(name="ASSIGN", start_date="2025-01-01")],
			"Dar Quraan Evaluation": [
				frappe._dict(
					name="EVAL",
					student_assignment="ASSIGN",
					evaluation_date="2026-01-09",
				)
			],
			"Dar Quraan Exception": [],
		}
		with (
			patch.object(frappe, "get_all", side_effect=self.rows_for(values)),
			patch.object(exceptions, "open_exception") as opener,
		):
			self.assertEqual(
				exceptions.detect_overdue_evaluations(
					settings=settings(evaluation_overdue_days=30),
					as_of="2026-01-10",
				),
				[],
			)
		opener.assert_not_called()

	def test_halaqa_capacity_counts_active_assignments(self):
		values = {
			"Dar Quraan Student Assignment": [frappe._dict(name=f"A-{n}", halaqa="FULL") for n in range(3)],
			"Dar Quraan Halaqa": [
				frappe._dict(
					name="FULL",
					maximum_students=2,
					branch="B",
					teaching_location="L",
					mentor="T",
				),
				frappe._dict(
					name="OK",
					maximum_students=2,
					branch="B",
					teaching_location="L",
					mentor="T",
				),
			],
			"Dar Quraan Exception": [],
		}
		with (
			patch.object(frappe, "get_all", side_effect=self.rows_for(values)),
			patch.object(exceptions, "open_exception", return_value="EXCEPTION") as opener,
		):
			self.assertEqual(exceptions.detect_halaqa_capacity(), ["EXCEPTION"])
		opener.assert_called_once()
		self.assertEqual(opener.call_args.kwargs["halaqa"], "FULL")

	def test_active_student_without_assignment_is_detected(self):
		values = {
			"Dar Quraan Student": [
				frappe._dict(
					name="STUDENT",
					student_name="Student",
					default_branch="B",
					default_halaqa=None,
					default_teacher=None,
				)
			],
			"Dar Quraan Student Assignment": [],
			"Dar Quraan Exception": [],
		}
		with (
			patch.object(frappe, "get_all", side_effect=self.rows_for(values)),
			patch.object(exceptions, "open_exception", return_value="EXCEPTION") as opener,
		):
			self.assertEqual(
				exceptions.detect_students_without_active_assignments(),
				["EXCEPTION"],
			)
		self.assertEqual(opener.call_args.kwargs["student"], "STUDENT")

	def test_active_assignment_without_teacher_is_detected(self):
		values = {
			"Dar Quraan Student Assignment": [frappe._dict(name="ASSIGN", teacher=None)],
			"Dar Quraan Exception": [],
		}
		with (
			patch.object(frappe, "get_all", side_effect=self.rows_for(values)),
			patch.object(exceptions, "open_exception", return_value="EXCEPTION") as opener,
		):
			self.assertEqual(
				exceptions.detect_assignments_without_teachers(),
				["EXCEPTION"],
			)
		self.assertEqual(opener.call_args.kwargs["student_assignment"], "ASSIGN")

	def test_notification_digest_only_sends_new_or_reopened(self):
		old = MagicMock(message="old")
		old.flags = frappe._dict(notify_exception=False)
		new = MagicMock(message="new")
		new.flags = frappe._dict(notify_exception=True)
		with patch.object(frappe, "sendmail") as sendmail:
			exceptions._send_notification_digest(
				settings(
					enable_email_notifications=1,
					notification_recipients="one@example.com, two@example.com",
				),
				[old, new],
			)
		sendmail.assert_called_once()
		self.assertEqual(
			sendmail.call_args.kwargs["recipients"],
			["one@example.com", "two@example.com"],
		)
		self.assertNotIn("old", sendmail.call_args.kwargs["message"])

	def test_daily_detection_runs_all_detectors(self):
		detector_names = (
			"detect_repeated_absence",
			"detect_repeated_lateness",
			"detect_repeated_weak_results",
			"detect_no_recent_progress",
			"detect_missing_attendance",
			"detect_overdue_follow_ups",
			"detect_overdue_evaluations",
			"detect_halaqa_capacity",
			"detect_students_without_active_assignments",
			"detect_assignments_without_teachers",
		)
		patches = [patch.object(exceptions, name, return_value=[name]) for name in detector_names]
		mocks = [item.start() for item in patches]
		self.addCleanup(lambda: [item.stop() for item in patches])
		with (
			patch.object(frappe, "get_single", return_value=settings()),
			patch.object(exceptions, "_send_notification_digest"),
		):
			result = exceptions.detect_daily_exceptions(as_of="2026-01-10")
		self.assertEqual(len(result), 10)
		for mock in mocks:
			mock.assert_called_once()
