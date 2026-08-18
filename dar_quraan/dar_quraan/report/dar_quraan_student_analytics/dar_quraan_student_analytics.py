from collections import Counter, defaultdict

import frappe
from frappe import _
from frappe.utils import flt, getdate

ASSIGNMENT_FIELDS = [
	"name",
	"student",
	"student_name",
	"status",
	"branch",
	"teaching_location",
	"halaqa",
	"teacher",
	"study_track",
	"start_date",
]


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)
	assignments = get_assignments(filters)
	data = get_data(assignments, filters)
	return get_columns(), data, None, get_chart(data), get_report_summary(data)


def validate_filters(filters):
	if filters.from_date and filters.to_date:
		if getdate(filters.from_date) > getdate(filters.to_date):
			frappe.throw(_("From Date cannot be after To Date."))


def get_assignments(filters):
	assignment_filters = {}
	field_map = {
		"student_assignment": "name",
		"student": "student",
		"assignment_status": "status",
		"branch": "branch",
		"teaching_location": "teaching_location",
		"halaqa": "halaqa",
		"teacher": "teacher",
	}
	for filter_name, fieldname in field_map.items():
		if filters.get(filter_name):
			assignment_filters[fieldname] = filters.get(filter_name)
	return frappe.get_all(
		"Dar Quraan Student Assignment",
		filters=assignment_filters,
		fields=ASSIGNMENT_FIELDS,
		order_by="student_name asc, start_date desc",
	)


def get_data(assignments, filters):
	if not assignments:
		return []
	assignment_names = [row.name for row in assignments]
	attendance = get_attendance_metrics(assignment_names, filters)
	progress = get_progress_metrics(assignment_names, filters)
	evaluations = get_evaluation_metrics(assignment_names, filters)
	exceptions = get_exception_metrics(assignment_names)

	data = []
	for assignment in assignments:
		attendance_row = attendance.get(assignment.name, {})
		total_attendance = attendance_row.get("total", 0)
		attended = attendance_row.get("present", 0) + attendance_row.get("late", 0)
		data.append(
			{
				**assignment,
				"attendance_total": total_attendance,
				"present_count": attendance_row.get("present", 0),
				"absent_count": attendance_row.get("absent", 0),
				"late_count": attendance_row.get("late", 0),
				"excused_count": attendance_row.get("excused", 0),
				"attendance_rate": (flt(attended * 100 / total_attendance, 2) if total_attendance else 0),
				"progress_count": progress.get(assignment.name, {}).get("count", 0),
				"last_progress_date": progress.get(assignment.name, {}).get("last_date"),
				"evaluation_count": evaluations.get(assignment.name, {}).get("count", 0),
				"last_evaluation_date": evaluations.get(assignment.name, {}).get("last_date"),
				"latest_result": evaluations.get(assignment.name, {}).get("latest_result"),
				"latest_score": evaluations.get(assignment.name, {}).get("latest_score"),
				"open_exception_count": exceptions.get(assignment.name, 0),
			}
		)
	return data


def get_attendance_metrics(assignment_names, filters):
	parent_filters = {"status": "Completed"}
	apply_date_filters(parent_filters, "attendance_date", filters)
	attendance_names = [
		row.name for row in frappe.get_all("Dar Quraan Attendance", filters=parent_filters, fields=["name"])
	]
	if not attendance_names:
		return {}
	rows = frappe.get_all(
		"Dar Quraan Attendance Item",
		filters={
			"parent": ["in", attendance_names],
			"parenttype": "Dar Quraan Attendance",
			"student_assignment": ["in", assignment_names],
		},
		fields=["student_assignment", "attendance_status"],
	)
	metrics = defaultdict(Counter)
	for row in rows:
		metrics[row.student_assignment]["total"] += 1
		metrics[row.student_assignment][row.attendance_status.lower()] += 1
	return metrics


def get_progress_metrics(assignment_names, filters):
	progress_filters = {
		"status": "Completed",
		"student_assignment": ["in", assignment_names],
	}
	apply_date_filters(progress_filters, "progress_date", filters)
	rows = frappe.get_all(
		"Dar Quraan Student Progress",
		filters=progress_filters,
		fields=["student_assignment", "progress_date"],
		order_by="progress_date desc, creation desc",
	)
	return aggregate_dated_rows(rows, "progress_date")


def get_evaluation_metrics(assignment_names, filters):
	evaluation_filters = {
		"status": "Completed",
		"student_assignment": ["in", assignment_names],
	}
	apply_date_filters(evaluation_filters, "evaluation_date", filters)
	rows = frappe.get_all(
		"Dar Quraan Evaluation",
		filters=evaluation_filters,
		fields=[
			"student_assignment",
			"evaluation_date",
			"overall_result",
			"overall_score",
		],
		order_by="evaluation_date desc, creation desc",
	)
	metrics = aggregate_dated_rows(rows, "evaluation_date")
	for row in rows:
		item = metrics[row.student_assignment]
		if "latest_result" not in item:
			item["latest_result"] = row.overall_result
			item["latest_score"] = row.overall_score
	return metrics


def aggregate_dated_rows(rows, date_field):
	metrics = {}
	for row in rows:
		item = metrics.setdefault(
			row.student_assignment,
			{"count": 0, "last_date": row.get(date_field)},
		)
		item["count"] += 1
	return metrics


def get_exception_metrics(assignment_names):
	rows = frappe.get_all(
		"Dar Quraan Exception",
		filters={
			"student_assignment": ["in", assignment_names],
			"status": ["in", ["Open", "Acknowledged"]],
		},
		fields=["student_assignment"],
	)
	return Counter(row.student_assignment for row in rows)


def apply_date_filters(filters, fieldname, report_filters):
	if report_filters.from_date and report_filters.to_date:
		filters[fieldname] = [
			"between",
			[report_filters.from_date, report_filters.to_date],
		]
	elif report_filters.from_date:
		filters[fieldname] = [">=", report_filters.from_date]
	elif report_filters.to_date:
		filters[fieldname] = ["<=", report_filters.to_date]


def get_chart(data):
	if not data:
		return None
	return {
		"data": {
			"labels": [row.get("student_name") or row.get("student") for row in data],
			"datasets": [
				{
					"name": _("Attendance Rate"),
					"values": [row.get("attendance_rate", 0) for row in data],
				}
			],
		},
		"type": "bar",
		"colors": ["#5e64ff"],
	}


def get_report_summary(data):
	return [
		{
			"value": len(data),
			"label": _("Assignments"),
			"datatype": "Int",
		},
		{
			"value": sum(row.get("attendance_total", 0) for row in data),
			"label": _("Attendance Records"),
			"datatype": "Int",
		},
		{
			"value": sum(row.get("progress_count", 0) for row in data),
			"label": _("Completed Progress"),
			"datatype": "Int",
		},
		{
			"value": sum(row.get("open_exception_count", 0) for row in data),
			"label": _("Open Exceptions"),
			"datatype": "Int",
			"indicator": "Red",
		},
	]


def get_columns():
	return [
		{
			"label": _("Student Assignment"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Dar Quraan Student Assignment",
			"width": 170,
		},
		{
			"label": _("Student"),
			"fieldname": "student",
			"fieldtype": "Link",
			"options": "Dar Quraan Student",
			"width": 150,
		},
		{"label": _("Student Name"), "fieldname": "student_name", "fieldtype": "Data", "width": 180},
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
			"label": _("Halaqa"),
			"fieldname": "halaqa",
			"fieldtype": "Link",
			"options": "Dar Quraan Halaqa",
			"width": 140,
		},
		{
			"label": _("Teacher"),
			"fieldname": "teacher",
			"fieldtype": "Link",
			"options": "Dar Quraan Teacher",
			"width": 140,
		},
		{"label": _("Study Track"), "fieldname": "study_track", "fieldtype": "Data", "width": 100},
		{"label": _("Start Date"), "fieldname": "start_date", "fieldtype": "Date", "width": 100},
		{"label": _("Attendance"), "fieldname": "attendance_total", "fieldtype": "Int", "width": 90},
		{"label": _("Present"), "fieldname": "present_count", "fieldtype": "Int", "width": 80},
		{"label": _("Absent"), "fieldname": "absent_count", "fieldtype": "Int", "width": 80},
		{"label": _("Late"), "fieldname": "late_count", "fieldtype": "Int", "width": 70},
		{"label": _("Excused"), "fieldname": "excused_count", "fieldtype": "Int", "width": 80},
		{"label": _("Attendance Rate"), "fieldname": "attendance_rate", "fieldtype": "Percent", "width": 120},
		{"label": _("Progress Entries"), "fieldname": "progress_count", "fieldtype": "Int", "width": 110},
		{"label": _("Last Progress"), "fieldname": "last_progress_date", "fieldtype": "Date", "width": 110},
		{"label": _("Evaluations"), "fieldname": "evaluation_count", "fieldtype": "Int", "width": 90},
		{
			"label": _("Last Evaluation"),
			"fieldname": "last_evaluation_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{"label": _("Latest Result"), "fieldname": "latest_result", "fieldtype": "Data", "width": 110},
		{"label": _("Latest Score"), "fieldname": "latest_score", "fieldtype": "Float", "width": 100},
		{
			"label": _("Open Exceptions"),
			"fieldname": "open_exception_count",
			"fieldtype": "Int",
			"width": 110,
		},
	]
