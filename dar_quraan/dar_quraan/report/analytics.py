from collections import Counter, defaultdict

import frappe
from frappe import _
from frappe.utils import flt

from dar_quraan.dar_quraan.report.dar_quraan_student_analytics import (
	dar_quraan_student_analytics as student_analytics,
)

ASSIGNMENT_FIELDS = [
	"name",
	"student",
	"status",
	"branch",
	"teaching_location",
	"halaqa",
	"teacher",
]
METRIC_DEFAULTS = {
	"assignment_count": 0,
	"active_assignment_count": 0,
	"student_count": 0,
	"halaqa_count": 0,
	"teacher_count": 0,
	"attendance_total": 0,
	"present_count": 0,
	"late_count": 0,
	"absent_count": 0,
	"excused_count": 0,
	"attendance_rate": 0,
	"progress_count": 0,
	"evaluation_count": 0,
}


def get_assignments(filters, extra_filters=None):
	assignment_filters = dict(extra_filters or {})
	for filter_name, fieldname in (
		("assignment_status", "status"),
		("branch", "branch"),
		("teaching_location", "teaching_location"),
		("halaqa", "halaqa"),
		("teacher", "teacher"),
	):
		if filters.get(filter_name):
			assignment_filters[fieldname] = filters.get(filter_name)
	return frappe.get_all(
		"Dar Quraan Student Assignment",
		filters=assignment_filters,
		fields=ASSIGNMENT_FIELDS,
	)


def aggregate_assignments(assignments, filters, group_field):
	if not assignments:
		return {}
	assignment_names = [row.name for row in assignments]
	attendance = student_analytics.get_attendance_metrics(assignment_names, filters)
	progress = student_analytics.get_progress_metrics(assignment_names, filters)
	evaluations = student_analytics.get_evaluation_metrics(assignment_names, filters)
	result = defaultdict(
		lambda: {
			"assignment_count": 0,
			"active_assignment_count": 0,
			"students": set(),
			"halaqas": set(),
			"teachers": set(),
			"attendance_total": 0,
			"present_count": 0,
			"late_count": 0,
			"absent_count": 0,
			"excused_count": 0,
			"progress_count": 0,
			"evaluation_count": 0,
		}
	)
	for assignment in assignments:
		group = assignment.get(group_field)
		if not group:
			continue
		item = result[group]
		item["assignment_count"] += 1
		if assignment.status == "Active":
			item["active_assignment_count"] += 1
		if assignment.student:
			item["students"].add(assignment.student)
		if assignment.halaqa:
			item["halaqas"].add(assignment.halaqa)
		if assignment.teacher:
			item["teachers"].add(assignment.teacher)
		attendance_row = attendance.get(assignment.name, {})
		for fieldname in (
			"attendance_total",
			"present_count",
			"late_count",
			"absent_count",
			"excused_count",
		):
			source = fieldname.removesuffix("_count")
			if fieldname == "attendance_total":
				source = "total"
			item[fieldname] += attendance_row.get(source, 0)
		item["progress_count"] += progress.get(assignment.name, {}).get("count", 0)
		item["evaluation_count"] += evaluations.get(assignment.name, {}).get("count", 0)
	for item in result.values():
		item["student_count"] = len(item.pop("students"))
		item["halaqa_count"] = len(item.pop("halaqas"))
		item["teacher_count"] = len(item.pop("teachers"))
		attended = item["present_count"] + item["late_count"]
		item["attendance_rate"] = (
			flt(attended * 100 / item["attendance_total"], 2) if item["attendance_total"] else 0
		)
	return result


def get_session_counts(group_field, names, filters):
	if not names:
		return Counter()
	session_filters = {"status": "Completed", group_field: ["in", names]}
	student_analytics.apply_date_filters(session_filters, "session_date", filters)
	rows = frappe.get_all(
		"Dar Quraan Session",
		filters=session_filters,
		fields=[group_field],
	)
	return Counter(row.get(group_field) for row in rows)


def get_open_exception_counts(group_field, names):
	if not names:
		return Counter()
	rows = frappe.get_all(
		"Dar Quraan Exception",
		filters={
			group_field: ["in", names],
			"status": ["in", ["Open", "Acknowledged"]],
		},
		fields=[group_field],
	)
	return Counter(row.get(group_field) for row in rows)


def get_summary(data, entity_label):
	return [
		{
			"value": len(data),
			"label": entity_label,
			"datatype": "Int",
		},
		{
			"value": sum(row.get("active_assignment_count", 0) for row in data),
			"label": _("Active Assignments"),
			"datatype": "Int",
		},
		{
			"value": sum(row.get("student_count", 0) for row in data),
			"label": _("Students"),
			"datatype": "Int",
		},
		{
			"value": sum(row.get("open_exception_count", 0) for row in data),
			"label": _("Open Exceptions"),
			"datatype": "Int",
			"indicator": "Red",
		},
	]


def get_chart(data, label_field):
	if not data:
		return None
	return {
		"data": {
			"labels": [row.get(label_field) for row in data],
			"datasets": [
				{
					"name": _("Students"),
					"values": [row.get("student_count", 0) for row in data],
				},
				{
					"name": _("Attendance Rate"),
					"values": [row.get("attendance_rate", 0) for row in data],
				},
			],
		},
		"type": "bar",
	}


def normalize_metrics(values=None):
	return {**METRIC_DEFAULTS, **(values or {})}
