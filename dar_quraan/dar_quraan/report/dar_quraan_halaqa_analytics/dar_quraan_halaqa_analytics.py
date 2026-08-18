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
	halaqa_filters = {}
	for filter_name, fieldname in (
		("halaqa", "name"),
		("halaqa_status", "status"),
		("branch", "branch"),
		("teaching_location", "teaching_location"),
		("teacher", "mentor"),
	):
		if filters.get(filter_name):
			halaqa_filters[fieldname] = filters.get(filter_name)
	halaqas = frappe.get_all(
		"Dar Quraan Halaqa",
		filters=halaqa_filters,
		fields=[
			"name",
			"halaqa_name",
			"status",
			"branch",
			"teaching_location",
			"mentor",
			"maximum_students",
		],
		order_by="halaqa_name asc",
	)
	data = get_data(halaqas, filters)
	return (
		get_columns(),
		data,
		None,
		analytics.get_chart(data, "halaqa_name"),
		analytics.get_summary(data, _("Halaqas")),
	)


def get_data(halaqas, filters):
	if not halaqas:
		return []
	assignments = analytics.get_assignments(filters)
	metrics = analytics.aggregate_assignments(assignments, filters, "halaqa")
	names = [row.name for row in halaqas]
	sessions = analytics.get_session_counts("halaqa", names, filters)
	exceptions = analytics.get_open_exception_counts("halaqa", names)
	data = []
	for halaqa in halaqas:
		item = analytics.normalize_metrics(metrics.get(halaqa.name))
		maximum = halaqa.maximum_students or 0
		active = item.get("active_assignment_count", 0)
		data.append(
			{
				**halaqa,
				**item,
				"student_count": item.get("student_count", 0),
				"active_assignment_count": active,
				"capacity_utilization": flt(active * 100 / maximum, 2) if maximum else 0,
				"completed_session_count": sessions.get(halaqa.name, 0),
				"open_exception_count": exceptions.get(halaqa.name, 0),
			}
		)
	return data


def get_columns():
	return [
		{
			"label": _("Halaqa"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Dar Quraan Halaqa",
			"width": 150,
		},
		{"label": _("Halaqa Name"), "fieldname": "halaqa_name", "fieldtype": "Data", "width": 180},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
		{
			"label": _("Branch"),
			"fieldname": "branch",
			"fieldtype": "Link",
			"options": "Dar Quraan Branch",
			"width": 130,
		},
		{
			"label": _("Teaching Location"),
			"fieldname": "teaching_location",
			"fieldtype": "Link",
			"options": "Dar Quraan Teaching Location",
			"width": 150,
		},
		{
			"label": _("Mentor"),
			"fieldname": "mentor",
			"fieldtype": "Link",
			"options": "Dar Quraan Teacher",
			"width": 140,
		},
		{"label": _("Capacity"), "fieldname": "maximum_students", "fieldtype": "Int", "width": 80},
		{
			"label": _("Active Assignments"),
			"fieldname": "active_assignment_count",
			"fieldtype": "Int",
			"width": 120,
		},
		{"label": _("Students"), "fieldname": "student_count", "fieldtype": "Int", "width": 80},
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
