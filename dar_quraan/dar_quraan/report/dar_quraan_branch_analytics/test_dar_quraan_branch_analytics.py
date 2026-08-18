from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from dar_quraan.dar_quraan.report import analytics
from dar_quraan.dar_quraan.report.dar_quraan_branch_analytics import (
	dar_quraan_branch_analytics as report,
)


class TestDarQuraanBranchAnalytics(FrappeTestCase):
	def test_branch_filters_are_applied(self):
		with patch.object(frappe, "get_all", return_value=[]) as get_all:
			report.execute({"branch": "BRANCH", "branch_status": "Active"})
		branch_call = next(call for call in get_all.call_args_list if call.args[0] == "Dar Quraan Branch")
		self.assertEqual(
			branch_call.kwargs["filters"],
			{"name": "BRANCH", "status": "Active"},
		)

	def test_capacity_is_aggregated_from_active_halaqas(self):
		rows = [
			frappe._dict(branch="BRANCH", maximum_students=10),
			frappe._dict(branch="BRANCH", maximum_students=15),
		]
		with patch.object(frappe, "get_all", return_value=rows):
			metrics = report.get_halaqa_metrics(["BRANCH"])
		self.assertEqual(metrics["BRANCH"]["active_halaqa_count"], 2)
		self.assertEqual(metrics["BRANCH"]["halaqa_capacity"], 25)

	def test_branch_metrics_are_combined(self):
		branch = frappe._dict(name="BRANCH", branch_name="Branch", status="Active", capacity=50)
		metrics = {
			"BRANCH": {
				"active_assignment_count": 20,
				"student_count": 20,
				"teacher_count": 4,
				"attendance_rate": 90,
			}
		}
		with (
			patch.object(analytics, "get_assignments", return_value=[]),
			patch.object(analytics, "aggregate_assignments", return_value=metrics),
			patch.object(analytics, "get_session_counts", return_value={"BRANCH": 5}),
			patch.object(analytics, "get_open_exception_counts", return_value={"BRANCH": 2}),
			patch.object(
				report,
				"get_halaqa_metrics",
				return_value={"BRANCH": {"active_halaqa_count": 2, "halaqa_capacity": 25}},
			),
			patch.object(report, "get_location_counts", return_value={"BRANCH": 3}),
		):
			row = report.get_data([branch], frappe._dict())[0]
		self.assertEqual(row["capacity_utilization"], 80)
		self.assertEqual(row["teaching_location_count"], 3)
		self.assertEqual(row["open_exception_count"], 2)
