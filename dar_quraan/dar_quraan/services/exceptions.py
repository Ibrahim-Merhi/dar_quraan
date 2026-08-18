from collections import Counter

import frappe
from frappe import _
from frappe.utils import add_days, cint, escape_html, getdate, now_datetime, today

OPEN_STATUSES = ("Open", "Acknowledged")
WEAK_RESULTS = ("Needs Revision", "Repeat")


def open_exception(exception_type, duplicate_key, message, severity="Medium", **context):
	"""Open a condition once, or deterministically reopen its existing record."""
	existing = frappe.db.get_value("Dar Quraan Exception", {"duplicate_key": duplicate_key}, "name")
	notify = False
	if existing:
		doc = frappe.get_doc("Dar Quraan Exception", existing)
		if doc.status not in OPEN_STATUSES:
			doc.status = "Open"
			doc.resolution_notes = None
			doc.resolved_on = None
			doc.occurrence_count = cint(doc.occurrence_count) + 1
			notify = True
		doc.detected_on = now_datetime()
		doc.message = message
		doc.severity = severity
		for fieldname, value in context.items():
			doc.set(fieldname, value)
		doc.save(ignore_permissions=True)
	else:
		values = {
			"doctype": "Dar Quraan Exception",
			"exception_type": exception_type,
			"duplicate_key": duplicate_key,
			"message": message,
			"severity": severity,
		}
		values.update(context)
		doc = frappe.get_doc(values).insert(ignore_permissions=True)
		notify = True
	doc.flags.notify_exception = notify
	return doc


def resolve_inactive_exceptions(exception_type, active_keys):
	active_keys = set(active_keys)
	rows = frappe.get_all(
		"Dar Quraan Exception",
		filters={"exception_type": exception_type, "status": ["in", OPEN_STATUSES]},
		fields=["name", "duplicate_key"],
	)
	resolved = []
	for row in rows:
		if row.duplicate_key in active_keys:
			continue
		doc = frappe.get_doc("Dar Quraan Exception", row.name)
		doc.status = "Resolved"
		doc.resolution_notes = _("Condition cleared automatically by exception detection.")
		doc.save(ignore_permissions=True)
		resolved.append(doc)
	return resolved


def _finish_detection(exception_type, conditions):
	docs = [open_exception(exception_type, **condition) for condition in conditions]
	resolve_inactive_exceptions(exception_type, [condition["duplicate_key"] for condition in conditions])
	return docs


def detect_daily_exceptions(as_of=None):
	settings = frappe.get_single("Dar Quraan Settings")
	if not cint(settings.enable_exception_detection):
		return []
	as_of = getdate(as_of or today())
	detectors = (
		detect_repeated_absence,
		detect_repeated_lateness,
		detect_repeated_weak_results,
		detect_no_recent_progress,
		detect_missing_attendance,
		detect_overdue_follow_ups,
		detect_overdue_evaluations,
		detect_halaqa_capacity,
		detect_students_without_active_assignments,
		detect_assignments_without_teachers,
	)
	result = []
	for detector in detectors:
		result.extend(detector(settings=settings, as_of=as_of))
	_send_notification_digest(settings, result)
	return result


def _active_assignments(fields=None):
	requested = list(dict.fromkeys(["name", *(fields or [])]))
	return frappe.get_all(
		"Dar Quraan Student Assignment",
		filters={"status": "Active", "is_current_assignment": 1},
		fields=requested,
	)


def _completed_attendance_items():
	attendance = frappe.get_all("Dar Quraan Attendance", filters={"status": "Completed"}, fields=["name"])
	parents = [row.name for row in attendance]
	if not parents:
		return []
	return frappe.get_all(
		"Dar Quraan Attendance Item",
		filters={
			"parent": ["in", parents],
			"parenttype": "Dar Quraan Attendance",
		},
		fields=["name", "parent", "student_assignment", "attendance_status"],
		order_by="creation desc",
	)


def _detect_repeated_attendance(settings, attendance_status, threshold_field, exception_type, key_prefix):
	threshold = cint(settings.get(threshold_field))
	outcomes = {}
	sources = {}
	for row in _completed_attendance_items():
		if not row.student_assignment:
			continue
		outcomes.setdefault(row.student_assignment, []).append(row.attendance_status)
		sources.setdefault(row.student_assignment, row.parent)
	conditions = []
	for assignment, assignment_outcomes in outcomes.items():
		recent = assignment_outcomes[:threshold]
		if len(recent) < threshold or any(outcome != attendance_status for outcome in recent):
			continue
		conditions.append(
			{
				"duplicate_key": f"{key_prefix}:{assignment}",
				"message": _("Student Assignment {0} has {1} recorded {2} occurrences.").format(
					assignment, threshold, attendance_status.lower()
				),
				"severity": "High",
				"student_assignment": assignment,
				"source_doctype": "Dar Quraan Attendance",
				"source_document": sources[assignment],
			}
		)
	return _finish_detection(exception_type, conditions)


def detect_repeated_absence(settings=None, as_of=None):
	settings = settings or frappe.get_single("Dar Quraan Settings")
	return _detect_repeated_attendance(
		settings, "Absent", "absence_threshold", "Repeated Absence", "repeated-absence"
	)


def detect_repeated_lateness(settings=None, as_of=None):
	settings = settings or frappe.get_single("Dar Quraan Settings")
	return _detect_repeated_attendance(
		settings, "Late", "lateness_threshold", "Repeated Lateness", "repeated-lateness"
	)


def detect_repeated_weak_results(settings=None, as_of=None):
	settings = settings or frappe.get_single("Dar Quraan Settings")
	threshold = cint(settings.weak_result_threshold)
	rows = frappe.get_all(
		"Dar Quraan Evaluation",
		filters={"status": "Completed"},
		fields=["name", "student_assignment", "overall_result"],
		order_by="evaluation_date desc, creation desc",
	)
	outcomes = {}
	sources = {}
	for row in rows:
		if not row.student_assignment:
			continue
		outcomes.setdefault(row.student_assignment, []).append(row.overall_result)
		sources.setdefault(row.student_assignment, row.name)
	conditions = []
	for assignment, assignment_outcomes in outcomes.items():
		recent = assignment_outcomes[:threshold]
		if len(recent) < threshold or any(result not in WEAK_RESULTS for result in recent):
			continue
		conditions.append(
			{
				"duplicate_key": f"repeated-weak-result:{assignment}",
				"message": _("Student Assignment {0} has {1} consecutive weak evaluation results.").format(
					assignment, threshold
				),
				"severity": "High",
				"student_assignment": assignment,
				"source_doctype": "Dar Quraan Evaluation",
				"source_document": sources[assignment],
			}
		)
	return _finish_detection("Repeated Weak Result", conditions)


def detect_no_recent_progress(settings=None, as_of=None):
	settings = settings or frappe.get_single("Dar Quraan Settings")
	cutoff = add_days(getdate(as_of or today()), -cint(settings.no_progress_days))
	assignments = _active_assignments(["start_date"])
	latest = {}
	for row in frappe.get_all(
		"Dar Quraan Student Progress",
		filters={
			"status": "Completed",
			"student_assignment": ["in", [a.name for a in assignments] or [""]],
		},
		fields=["name", "student_assignment", "progress_date"],
		order_by="progress_date desc, creation desc",
	):
		latest.setdefault(row.student_assignment, row)
	conditions = []
	for assignment in assignments:
		progress = latest.get(assignment.name)
		reference_date = getdate(progress.progress_date if progress else assignment.start_date)
		if reference_date > cutoff:
			continue
		conditions.append(
			{
				"duplicate_key": f"no-recent-progress:{assignment.name}",
				"message": _("Student Assignment {0} has no completed progress since {1}.").format(
					assignment.name, reference_date
				),
				"severity": "Medium",
				"student_assignment": assignment.name,
				"source_doctype": (
					"Dar Quraan Student Progress" if progress else "Dar Quraan Student Assignment"
				),
				"source_document": progress.name if progress else assignment.name,
			}
		)
	return _finish_detection("No Recent Progress", conditions)


def detect_missing_attendance(settings=None, as_of=None):
	settings = settings or frappe.get_single("Dar Quraan Settings")
	cutoff = add_days(getdate(as_of or today()), -cint(settings.attendance_grace_days))
	sessions = frappe.get_all(
		"Dar Quraan Session",
		filters={"status": "Completed", "session_date": ["<=", cutoff]},
		fields=["name", "halaqa"],
	)
	attendance_sessions = {
		row.session
		for row in frappe.get_all(
			"Dar Quraan Attendance",
			filters={
				"session": ["in", [s.name for s in sessions] or [""]],
				"status": ["!=", "Cancelled"],
			},
			fields=["session"],
		)
	}
	conditions = [
		{
			"duplicate_key": f"missing-attendance:{session.name}",
			"message": _("Completed Session {0} is missing attendance.").format(session.name),
			"severity": "High",
			"halaqa": session.halaqa,
			"source_doctype": "Dar Quraan Session",
			"source_document": session.name,
		}
		for session in sessions
		if session.name not in attendance_sessions
	]
	return _finish_detection("Missing Attendance", conditions)


def detect_overdue_follow_ups(settings=None, as_of=None):
	settings = settings or frappe.get_single("Dar Quraan Settings")
	cutoff = add_days(getdate(as_of or today()), -cint(settings.follow_up_reminder_days))
	rows = frappe.get_all(
		"Dar Quraan Teacher Follow Up",
		filters={
			"follow_up_required": 1,
			"status": ["in", ["Open", "In Progress"]],
			"next_follow_up_date": ["<=", cutoff],
		},
		fields=["name", "student_assignment"],
	)
	conditions = [
		{
			"duplicate_key": f"overdue-follow-up:{row.name}",
			"message": _("Teacher follow-up {0} is overdue.").format(row.name),
			"severity": "High",
			"student_assignment": row.student_assignment,
			"source_doctype": "Dar Quraan Teacher Follow Up",
			"source_document": row.name,
		}
		for row in rows
	]
	return _finish_detection("Overdue Follow-up", conditions)


def detect_overdue_evaluations(settings=None, as_of=None):
	settings = settings or frappe.get_single("Dar Quraan Settings")
	cutoff = add_days(getdate(as_of or today()), -cint(settings.evaluation_overdue_days))
	assignments = _active_assignments(["start_date"])
	latest = {}
	for row in frappe.get_all(
		"Dar Quraan Evaluation",
		filters={
			"status": "Completed",
			"student_assignment": ["in", [a.name for a in assignments] or [""]],
		},
		fields=["name", "student_assignment", "evaluation_date"],
		order_by="evaluation_date desc, creation desc",
	):
		latest.setdefault(row.student_assignment, row)
	conditions = []
	for assignment in assignments:
		evaluation = latest.get(assignment.name)
		reference_date = getdate(evaluation.evaluation_date if evaluation else assignment.start_date)
		if reference_date > cutoff:
			continue
		conditions.append(
			{
				"duplicate_key": f"overdue-evaluation:{assignment.name}",
				"message": _("Student Assignment {0} has no completed evaluation since {1}.").format(
					assignment.name, reference_date
				),
				"severity": "Medium",
				"student_assignment": assignment.name,
				"source_doctype": (
					"Dar Quraan Evaluation" if evaluation else "Dar Quraan Student Assignment"
				),
				"source_document": evaluation.name if evaluation else assignment.name,
			}
		)
	return _finish_detection("Overdue Evaluation", conditions)


def detect_halaqa_capacity(settings=None, as_of=None):
	assignments = _active_assignments(["halaqa"])
	counts = Counter(row.halaqa for row in assignments if row.halaqa)
	halaqas = frappe.get_all(
		"Dar Quraan Halaqa",
		filters={"status": "Active"},
		fields=["name", "maximum_students", "branch", "teaching_location", "mentor"],
	)
	conditions = []
	for row in halaqas:
		count = counts[row.name]
		if count <= cint(row.maximum_students):
			continue
		conditions.append(
			{
				"duplicate_key": f"halaqa-capacity:{row.name}",
				"message": _("Halaqa {0} has {1} active assignments for a capacity of {2}.").format(
					row.name, count, row.maximum_students
				),
				"severity": "High",
				"branch": row.branch,
				"teaching_location": row.teaching_location,
				"halaqa": row.name,
				"teacher": row.mentor,
				"source_doctype": "Dar Quraan Halaqa",
				"source_document": row.name,
			}
		)
	return _finish_detection("Halaqa Over Capacity", conditions)


def detect_students_without_active_assignments(settings=None, as_of=None):
	students = frappe.get_all(
		"Dar Quraan Student",
		filters={"status": "Active", "disabled": 0},
		fields=[
			"name",
			"student_name",
			"default_branch",
			"default_halaqa",
			"default_teacher",
		],
	)
	assigned = {row.student for row in _active_assignments(["student"]) if row.student}
	conditions = [
		{
			"duplicate_key": f"student-without-assignment:{row.name}",
			"message": _("Active Student {0} does not have an active current assignment.").format(row.name),
			"severity": "High",
			"student": row.name,
			"student_name": row.student_name,
			"branch": row.default_branch,
			"halaqa": row.default_halaqa,
			"teacher": row.default_teacher,
			"source_doctype": "Dar Quraan Student",
			"source_document": row.name,
		}
		for row in students
		if row.name not in assigned
	]
	return _finish_detection("Student Without Active Assignment", conditions)


def detect_assignments_without_teachers(settings=None, as_of=None):
	assignments = [row for row in _active_assignments(["teacher"]) if not row.teacher]
	conditions = [
		{
			"duplicate_key": f"assignment-without-teacher:{row.name}",
			"message": _("Active Student Assignment {0} does not have a teacher.").format(row.name),
			"severity": "Urgent",
			"student_assignment": row.name,
			"source_doctype": "Dar Quraan Student Assignment",
			"source_document": row.name,
		}
		for row in assignments
	]
	return _finish_detection("Assignment Without Teacher", conditions)


def _send_notification_digest(settings, docs):
	if not cint(settings.enable_email_notifications):
		return
	recipients = [
		value.strip()
		for value in (settings.notification_recipients or "").replace("\n", ",").split(",")
		if value.strip()
	]
	notify_docs = [doc for doc in docs if doc.flags.notify_exception]
	if not recipients or not notify_docs:
		return
	frappe.sendmail(
		recipients=recipients,
		subject=_("Dar Quraan exceptions detected"),
		message="<br>".join(escape_html(doc.message) for doc in notify_docs),
	)
