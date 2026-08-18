from collections import Counter, defaultdict

import frappe
from frappe import _
from frappe.utils import flt

from dar_quraan.dar_quraan.report import analytics
from dar_quraan.dar_quraan.report.dar_quraan_student_analytics import (
	dar_quraan_student_analytics as student_analytics,
)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	student_analytics.validate_filters(filters)
	branch_filters = {}
	if filters.branch:
		branch_filters["name"] = filters.branch
	if filters.branch_status:
		branch_filters["status"] = filters.branch_status
	branches = frappe.get_all(
		"Dar Quraan Branch",
		filters=branch_filters,
		fields=["name", "branch_name", "status", "capacity"],
		order_by="branch_name asc",
	)
	data = get_data(branches, filters)
	return (
		get_columns(),
		data,
		None,
		analytics.get_chart(data, "branch_name"),
		analytics.get_summary(data, _("Branches")),
	)


def get_data(branches, filters):
	if not branches:
		return []
	assignments = analytics.get_assignments(filters)
	metrics = analytics.aggregate_assignments(assignments, filters, "branch")
	names = [row.name for row in branches]
	sessions = analytics.get_session_counts("branch", names, filters)
	exceptions = analytics.get_open_exception_counts("branch", names)
	halaqas = get_halaqa_metrics(names)
	locations = get_location_counts(names)
	data = []
	for branch in branches:
		item = analytics.normalize_metrics(metrics.get(branch.name))
		halaqa_item = halaqas.get(branch.name, {})
		capacity = halaqa_item.get("halaqa_capacity", 0) or branch.capacity or 0
		active = item.get("active_assignment_count", 0)
		data.append(
			{
				**branch,
				**item,
				"student_count": item.get("student_count", 0),
				"teacher_count": item.get("teacher_count", 0),
				"active_assignment_count": active,
				"teaching_location_count": locations.get(branch.name, 0),
				"active_halaqa_count": halaqa_item.get("active_halaqa_count", 0),
				"halaqa_capacity": capacity,
				"capacity_utilization": flt(active * 100 / capacity, 2) if capacity else 0,
				"completed_session_count": sessions.get(branch.name, 0),
				"open_exception_count": exceptions.get(branch.name, 0),
			}
		)
	return data


def get_halaqa_metrics(branch_names):
	rows = frappe.get_all(
		"Dar Quraan Halaqa",
		filters={"branch": ["in", branch_names], "status": "Active"},
		fields=["branch", "maximum_students"],
	)
	result = defaultdict(lambda: {"active_halaqa_count": 0, "halaqa_capacity": 0})
	for row in rows:
		result[row.branch]["active_halaqa_count"] += 1
		result[row.branch]["halaqa_capacity"] += row.maximum_students or 0
	return result


def get_location_counts(branch_names):
	rows = frappe.get_all(
		"Dar Quraan Teaching Location",
		filters={"branch": ["in", branch_names], "status": "Active"},
		fields=["branch"],
	)
	return Counter(row.branch for row in rows)


def get_columns():
	return [
		{
			"label": _("Branch"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Dar Quraan Branch",
			"width": 150,
		},
		{"label": _("Branch Name"), "fieldname": "branch_name", "fieldtype": "Data", "width": 180},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
		{
			"label": _("Teaching Locations"),
			"fieldname": "teaching_location_count",
			"fieldtype": "Int",
			"width": 120,
		},
		{"label": _("Active Halaqas"), "fieldname": "active_halaqa_count", "fieldtype": "Int", "width": 110},
		{"label": _("Teachers"), "fieldname": "teacher_count", "fieldtype": "Int", "width": 80},
		{
			"label": _("Active Assignments"),
			"fieldname": "active_assignment_count",
			"fieldtype": "Int",
			"width": 120,
		},
		{"label": _("Students"), "fieldname": "student_count", "fieldtype": "Int", "width": 80},
		{"label": _("Halaqa Capacity"), "fieldname": "halaqa_capacity", "fieldtype": "Int", "width": 110},
		{
			"label": _("Capacity Utilization"),
			"fieldname": "capacity_utilization",
			"fieldtype": "Percent",
			"width": 130,
		},
		{
			"label": _("Completed Sessions"),
			"fieldname": "completed_session_count",
			"fieldtype": "Int",
			"width": 120,
		},
		{"label": _("Attendance Records"), "fieldname": "attendance_total", "fieldtype": "Int", "width": 120},
		{"label": _("Attendance Rate"), "fieldname": "attendance_rate", "fieldtype": "Percent", "width": 110},
		{"label": _("Progress Entries"), "fieldname": "progress_count", "fieldtype": "Int", "width": 110},
		{"label": _("Evaluations"), "fieldname": "evaluation_count", "fieldtype": "Int", "width": 90},
		{
			"label": _("Open Exceptions"),
			"fieldname": "open_exception_count",
			"fieldtype": "Int",
			"width": 110,
		},
	]
