from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from dar_quraan.dar_quraan.report.dar_quraan_student_analytics import (
	dar_quraan_student_analytics as report,
)


class TestDarQuraanStudentAnalytics(FrappeTestCase):
	def test_invalid_date_range_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			report.execute({"from_date": "2026-02-01", "to_date": "2026-01-01"})

	def test_assignment_filters_use_authoritative_context(self):
		filters = frappe._dict(
			{
				"student": "STUDENT",
				"branch": "BRANCH",
				"halaqa": "HALAQA",
				"teacher": "TEACHER",
				"assignment_status": "Active",
			}
		)
		with patch.object(frappe, "get_all", return_value=[]) as get_all:
			report.get_assignments(filters)
		self.assertEqual(
			get_all.call_args.kwargs["filters"],
			{
				"student": "STUDENT",
				"branch": "BRANCH",
				"halaqa": "HALAQA",
				"teacher": "TEACHER",
				"status": "Active",
			},
		)

	def test_empty_assignments_skip_metric_queries(self):
		with patch.object(frappe, "get_all", return_value=[]) as get_all:
			columns, data, message, chart, summary = report.execute({})
		self.assertTrue(columns)
		self.assertEqual(data, [])
		self.assertIsNone(message)
		self.assertIsNone(chart)
		self.assertEqual(summary[0]["value"], 0)
		get_all.assert_called_once()

	def test_metrics_are_aggregated_per_assignment(self):
		assignment = frappe._dict(
			{
				"name": "ASSIGN",
				"student": "STUDENT",
				"student_name": "Student",
				"status": "Active",
				"branch": "BRANCH",
				"teaching_location": "LOCATION",
				"halaqa": "HALAQA",
				"teacher": "TEACHER",
				"study_track": "Hifz",
				"start_date": "2026-01-01",
			}
		)
		attendance = {
			"ASSIGN": {
				"total": 4,
				"present": 2,
				"absent": 1,
				"late": 1,
				"excused": 0,
			}
		}
		progress = {"ASSIGN": {"count": 2, "last_date": "2026-01-10"}}
		evaluations = {
			"ASSIGN": {
				"count": 1,
				"last_date": "2026-01-09",
				"latest_result": "Good",
				"latest_score": 88,
			}
		}
		with (
			patch.object(report, "get_attendance_metrics", return_value=attendance),
			patch.object(report, "get_progress_metrics", return_value=progress),
			patch.object(report, "get_evaluation_metrics", return_value=evaluations),
			patch.object(report, "get_exception_metrics", return_value={"ASSIGN": 2}),
		):
			row = report.get_data([assignment], frappe._dict())[0]
		self.assertEqual(row["attendance_rate"], 75)
		self.assertEqual(row["progress_count"], 2)
		self.assertEqual(row["latest_result"], "Good")
		self.assertEqual(row["open_exception_count"], 2)
		self.assertEqual(row["branch"], "BRANCH")
		self.assertEqual(
			report.get_chart([row])["data"]["datasets"][0]["values"],
			[75],
		)
		self.assertEqual(
			[item["value"] for item in report.get_report_summary([row])],
			[1, 4, 2, 2],
		)

	def test_attendance_uses_only_completed_parents(self):
		def get_all(doctype, *args, **kwargs):
			if doctype == "Dar Quraan Attendance":
				self.assertEqual(kwargs["filters"]["status"], "Completed")
				self.assertEqual(
					kwargs["filters"]["attendance_date"],
					["between", ["2026-01-01", "2026-01-31"]],
				)
				return [frappe._dict(name="ATTENDANCE")]
			if doctype == "Dar Quraan Attendance Item":
				self.assertEqual(
					kwargs["filters"]["student_assignment"],
					["in", ["ASSIGN"]],
				)
				return [
					frappe._dict(
						student_assignment="ASSIGN",
						attendance_status="Present",
					),
					frappe._dict(
						student_assignment="ASSIGN",
						attendance_status="Late",
					),
				]
			return []

		with patch.object(frappe, "get_all", side_effect=get_all):
			metrics = report.get_attendance_metrics(
				["ASSIGN"],
				frappe._dict(from_date="2026-01-01", to_date="2026-01-31"),
			)
		self.assertEqual(metrics["ASSIGN"]["total"], 2)
		self.assertEqual(metrics["ASSIGN"]["present"], 1)
		self.assertEqual(metrics["ASSIGN"]["late"], 1)

	def test_latest_evaluation_is_taken_from_ordered_results(self):
		rows = [
			frappe._dict(
				student_assignment="ASSIGN",
				evaluation_date="2026-01-10",
				overall_result="Very Good",
				overall_score=92,
			),
			frappe._dict(
				student_assignment="ASSIGN",
				evaluation_date="2026-01-01",
				overall_result="Good",
				overall_score=80,
			),
		]
		with patch.object(frappe, "get_all", return_value=rows) as get_all:
			metrics = report.get_evaluation_metrics(["ASSIGN"], frappe._dict())
		self.assertEqual(metrics["ASSIGN"]["count"], 2)
		self.assertEqual(metrics["ASSIGN"]["last_date"], "2026-01-10")
		self.assertEqual(metrics["ASSIGN"]["latest_result"], "Very Good")
		self.assertEqual(metrics["ASSIGN"]["latest_score"], 92)
		self.assertEqual(
			get_all.call_args.kwargs["order_by"],
			"evaluation_date desc, creation desc",
		)

	def test_only_open_exceptions_are_counted(self):
		rows = [
			frappe._dict(student_assignment="ASSIGN"),
			frappe._dict(student_assignment="ASSIGN"),
		]
		with patch.object(frappe, "get_all", return_value=rows) as get_all:
			counts = report.get_exception_metrics(["ASSIGN"])
		self.assertEqual(counts["ASSIGN"], 2)
		self.assertEqual(
			get_all.call_args.kwargs["filters"]["status"],
			["in", ["Open", "Acknowledged"]],
		)

	def test_chart_and_summary_match_data(self):
		data = [
			frappe._dict(
				student="STUDENT",
				student_name="Student",
				attendance_rate=75,
				attendance_total=4,
				progress_count=2,
				open_exception_count=1,
			)
		]
		chart = report.get_chart(data)
		summary = report.get_report_summary(data)
		self.assertEqual(chart["data"]["labels"], ["Student"])
		self.assertEqual(chart["data"]["datasets"][0]["values"], [75])
		self.assertEqual(
			[item["value"] for item in summary],
			[1, 4, 2, 1],
		)
