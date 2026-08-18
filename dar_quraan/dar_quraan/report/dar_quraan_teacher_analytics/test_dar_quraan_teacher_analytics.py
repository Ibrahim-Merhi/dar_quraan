from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from dar_quraan.dar_quraan.report import analytics
from dar_quraan.dar_quraan.report.dar_quraan_teacher_analytics import (
	dar_quraan_teacher_analytics as report,
)


class TestDarQuraanTeacherAnalytics(FrappeTestCase):
	def test_teacher_filter_is_applied(self):
		with patch.object(frappe, "get_all", return_value=[]) as get_all:
			report.execute({"teacher": "TEACHER"})
		teacher_call = next(call for call in get_all.call_args_list if call.args[0] == "Dar Quraan Teacher")
		self.assertEqual(teacher_call.kwargs["filters"], {"name": "TEACHER"})

	def test_teacher_metrics_come_from_assignments(self):
		teacher = frappe._dict(name="TEACHER")
		metrics = {
			"TEACHER": {
				"active_assignment_count": 4,
				"student_count": 4,
				"halaqa_count": 2,
				"attendance_rate": 75,
			}
		}
		with (
			patch.object(analytics, "get_assignments", return_value=[]),
			patch.object(analytics, "aggregate_assignments", return_value=metrics),
			patch.object(analytics, "get_session_counts", return_value={"TEACHER": 3}),
			patch.object(analytics, "get_open_exception_counts", return_value={"TEACHER": 1}),
		):
			row = report.get_data([teacher], frappe._dict())[0]
		self.assertEqual(row["student_count"], 4)
		self.assertEqual(row["halaqa_count"], 2)
		self.assertEqual(row["completed_session_count"], 3)
		self.assertEqual(row["open_exception_count"], 1)
