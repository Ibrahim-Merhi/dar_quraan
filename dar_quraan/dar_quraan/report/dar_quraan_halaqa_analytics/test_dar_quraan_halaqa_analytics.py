from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from dar_quraan.dar_quraan.report import analytics
from dar_quraan.dar_quraan.report.dar_quraan_halaqa_analytics import (
	dar_quraan_halaqa_analytics as report,
)


class TestDarQuraanHalaqaAnalytics(FrappeTestCase):
	def test_filters_are_applied_to_halaqa_context(self):
		filters = {
			"halaqa_status": "Active",
			"branch": "BRANCH",
			"teaching_location": "LOCATION",
			"teacher": "TEACHER",
		}
		with patch.object(frappe, "get_all", return_value=[]) as get_all:
			report.execute(filters)
		halaqa_call = next(call for call in get_all.call_args_list if call.args[0] == "Dar Quraan Halaqa")
		self.assertEqual(
			halaqa_call.kwargs["filters"],
			{
				"status": "Active",
				"branch": "BRANCH",
				"teaching_location": "LOCATION",
				"mentor": "TEACHER",
			},
		)

	def test_capacity_uses_active_assignment_count(self):
		halaqa = frappe._dict(
			name="HALAQA",
			halaqa_name="Halaqa",
			status="Active",
			branch="B",
			teaching_location="L",
			mentor="T",
			maximum_students=10,
		)
		metrics = {
			"HALAQA": {
				"active_assignment_count": 8,
				"student_count": 8,
				"attendance_total": 10,
				"attendance_rate": 90,
			}
		}
		with (
			patch.object(analytics, "get_assignments", return_value=[]),
			patch.object(analytics, "aggregate_assignments", return_value=metrics),
			patch.object(analytics, "get_session_counts", return_value={"HALAQA": 4}),
			patch.object(analytics, "get_open_exception_counts", return_value={"HALAQA": 2}),
		):
			row = report.get_data([halaqa], frappe._dict())[0]
		self.assertEqual(row["capacity_utilization"], 80)
		self.assertEqual(row["completed_session_count"], 4)
		self.assertEqual(row["open_exception_count"], 2)
