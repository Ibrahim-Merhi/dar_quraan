import frappe
from frappe import _

from dar_quraan.dar_quraan.report import analytics
from dar_quraan.dar_quraan.report.dar_quraan_student_analytics import (
	dar_quraan_student_analytics as student_analytics,
)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	student_analytics.validate_filters(filters)
	teacher_filters = {"name": filters.teacher} if filters.teacher else {}
	teachers = frappe.get_all(
		"Dar Quraan Teacher",
		filters=teacher_filters,
		fields=["name"],
		order_by="name asc",
	)
	data = get_data(teachers, filters)
	return (
		get_columns(),
		data,
		None,
		analytics.get_chart(data, "teacher"),
		analytics.get_summary(data, _("Teachers")),
	)


def get_data(teachers, filters):
	if not teachers:
		return []
	assignments = analytics.get_assignments(filters)
	metrics = analytics.aggregate_assignments(assignments, filters, "teacher")
	names = [row.name for row in teachers]
	sessions = analytics.get_session_counts("teacher", names, filters)
	exceptions = analytics.get_open_exception_counts("teacher", names)
	data = []
	for teacher in teachers:
		item = analytics.normalize_metrics(metrics.get(teacher.name))
		data.append(
			{
				"teacher": teacher.name,
				**item,
				"completed_session_count": sessions.get(teacher.name, 0),
				"open_exception_count": exceptions.get(teacher.name, 0),
			}
		)
	return data


def get_columns():
	return [
		{
			"label": _("Teacher"),
			"fieldname": "teacher",
			"fieldtype": "Link",
			"options": "Dar Quraan Teacher",
			"width": 180,
		},
		{
			"label": _("Active Assignments"),
			"fieldname": "active_assignment_count",
			"fieldtype": "Int",
			"width": 120,
		},
		{"label": _("Students"), "fieldname": "student_count", "fieldtype": "Int", "width": 90},
		{"label": _("Halaqas"), "fieldname": "halaqa_count", "fieldtype": "Int", "width": 90},
		{
			"label": _("Completed Sessions"),
			"fieldname": "completed_session_count",
			"fieldtype": "Int",
			"width": 120,
		},
		{"label": _("Attendance Records"), "fieldname": "attendance_total", "fieldtype": "Int", "width": 120},
		{"label": _("Present"), "fieldname": "present_count", "fieldtype": "Int", "width": 80},
		{"label": _("Absent"), "fieldname": "absent_count", "fieldtype": "Int", "width": 80},
		{"label": _("Late"), "fieldname": "late_count", "fieldtype": "Int", "width": 70},
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
