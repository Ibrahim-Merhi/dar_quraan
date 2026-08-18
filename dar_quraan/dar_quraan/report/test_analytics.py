from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from dar_quraan.dar_quraan.report import analytics


class TestAnalytics(FrappeTestCase):
	def test_assignment_filters_preserve_organizational_context(self):
		filters = frappe._dict(
			assignment_status="Active",
			branch="BRANCH",
			teaching_location="LOCATION",
			halaqa="HALAQA",
			teacher="TEACHER",
		)
		with patch.object(frappe, "get_all", return_value=[]) as get_all:
			analytics.get_assignments(filters)
		self.assertEqual(
			get_all.call_args.kwargs["filters"],
			{
				"status": "Active",
				"branch": "BRANCH",
				"teaching_location": "LOCATION",
				"halaqa": "HALAQA",
				"teacher": "TEACHER",
			},
		)

	def test_assignment_metrics_are_grouped_without_double_counting_students(self):
		assignments = [
			frappe._dict(
				name="A1",
				student="STUDENT",
				status="Active",
				branch="BRANCH",
				teaching_location="L",
				halaqa="H1",
				teacher="T1",
			),
			frappe._dict(
				name="A2",
				student="STUDENT",
				status="Completed",
				branch="BRANCH",
				teaching_location="L",
				halaqa="H2",
				teacher="T2",
			),
		]
		attendance = {
			"A1": {"total": 2, "present": 1, "late": 1},
			"A2": {"total": 2, "present": 1, "absent": 1},
		}
		with (
			patch.object(
				analytics.student_analytics,
				"get_attendance_metrics",
				return_value=attendance,
			),
			patch.object(
				analytics.student_analytics,
				"get_progress_metrics",
				return_value={"A1": {"count": 2}},
			),
			patch.object(
				analytics.student_analytics,
				"get_evaluation_metrics",
				return_value={"A2": {"count": 1}},
			),
		):
			item = analytics.aggregate_assignments(assignments, frappe._dict(), "branch")["BRANCH"]
		self.assertEqual(item["assignment_count"], 2)
		self.assertEqual(item["active_assignment_count"], 1)
		self.assertEqual(item["student_count"], 1)
		self.assertEqual(item["halaqa_count"], 2)
		self.assertEqual(item["teacher_count"], 2)
		self.assertEqual(item["attendance_rate"], 75)
		self.assertEqual(item["progress_count"], 2)
		self.assertEqual(item["evaluation_count"], 1)

	def test_date_filters_are_applied_to_completed_sessions(self):
		with patch.object(frappe, "get_all", return_value=[]) as get_all:
			analytics.get_session_counts(
				"branch",
				["BRANCH"],
				frappe._dict(from_date="2026-01-01", to_date="2026-01-31"),
			)
		self.assertEqual(
			get_all.call_args.kwargs["filters"],
			{
				"status": "Completed",
				"branch": ["in", ["BRANCH"]],
				"session_date": ["between", ["2026-01-01", "2026-01-31"]],
			},
		)
