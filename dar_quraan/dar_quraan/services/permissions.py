import frappe

ELEVATED_ROLES = {"System Manager", "Dar Quraan Manager", "Dar Quraan Supervisor", "Dar Quraan Data Entry"}
TEACHER_SCOPED_DOCTYPES = {
	"Dar Quraan Attendance",
	"Dar Quraan Evaluation",
	"Dar Quraan Exception",
	"Dar Quraan Next Assignment",
	"Dar Quraan Session",
	"Dar Quraan Student Progress",
	"Dar Quraan Student Quran State",
	"Dar Quraan Supervision Visit",
	"Dar Quraan Teacher Follow Up",
	"Dar Quraan Student Weekly Slot",
	"Dar Quraan Text Progress",
}


def is_restricted_teacher(user=None):
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	return "Dar Quraan Teacher" in roles and not roles.intersection(ELEVATED_ROLES)


def get_user_teachers(user=None):
	user = user or frappe.session.user
	return frappe.get_all("Dar Quraan Teacher", filters={"user": user, "status": "Active"}, pluck="name")


def _teacher_sql(user=None):
	teachers = get_user_teachers(user)
	return ", ".join(frappe.db.escape(name) for name in teachers) or "NULL"


def get_teacher_query_condition(user=None):
	if not is_restricted_teacher(user):
		return ""
	return f"`tabDar Quraan Teacher`.`name` in ({_teacher_sql(user)})"


def get_halaqa_query_condition(user=None):
	if not is_restricted_teacher(user):
		return ""
	teachers = _teacher_sql(user)
	return f"(`tabDar Quraan Halaqa`.`mentor` in ({teachers}) or `tabDar Quraan Halaqa`.`assistant_mentor` in ({teachers}))"


def get_student_query_condition(user=None):
	if not is_restricted_teacher(user):
		return ""
	teachers = _teacher_sql(user)
	return f"exists (select 1 from `tabDar Quraan Student Assignment` dqsa where dqsa.student = `tabDar Quraan Student`.name and dqsa.teacher in ({teachers}))"


def get_scoped_query_condition(doctype, user=None):
	if not is_restricted_teacher(user):
		return ""
	return f"`tab{doctype}`.`teacher` in ({_teacher_sql(user)})"


def get_assignment_query_condition(user=None):
	return get_scoped_query_condition("Dar Quraan Student Assignment", user)


def get_attendance_query_condition(user=None):
	return get_scoped_query_condition("Dar Quraan Attendance", user)


def get_evaluation_query_condition(user=None):
	return get_scoped_query_condition("Dar Quraan Evaluation", user)


def get_exception_query_condition(user=None):
	return get_scoped_query_condition("Dar Quraan Exception", user)


def get_next_assignment_query_condition(user=None):
	return get_scoped_query_condition("Dar Quraan Next Assignment", user)


def get_session_query_condition(user=None):
	return get_scoped_query_condition("Dar Quraan Session", user)


def get_progress_query_condition(user=None):
	return get_scoped_query_condition("Dar Quraan Student Progress", user)


def get_quran_state_query_condition(user=None):
	return get_scoped_query_condition("Dar Quraan Student Quran State", user)


def get_supervision_query_condition(user=None):
	return get_scoped_query_condition("Dar Quraan Supervision Visit", user)


def get_follow_up_query_condition(user=None):
	return get_scoped_query_condition("Dar Quraan Teacher Follow Up", user)


def get_weekly_slot_query_condition(user=None):
	return get_scoped_query_condition("Dar Quraan Student Weekly Slot", user)


def get_text_progress_query_condition(user=None):
	return get_scoped_query_condition("Dar Quraan Text Progress", user)


def get_exam_query_condition(user=None):
	return get_scoped_query_condition("Dar Quraan Exam", user).replace(".`teacher`", ".`examiner_teacher`")


def get_assignment_related_query_condition(doctype, user=None):
	if not is_restricted_teacher(user):
		return ""
	teachers = _teacher_sql(user)
	return f"exists (select 1 from `tabDar Quraan Student Assignment` dqsa where dqsa.name = `tab{doctype}`.`student_assignment` and dqsa.teacher in ({teachers}))"


def get_ijazah_query_condition(user=None):
	return get_assignment_related_query_condition("Dar Quraan Ijazah", user)


def get_discipline_query_condition(user=None):
	return get_assignment_related_query_condition("Dar Quraan Discipline Incident", user)


def has_teacher_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if not is_restricted_teacher(user):
		return None
	teachers = set(get_user_teachers(user))
	if doc.doctype == "Dar Quraan Teacher":
		return doc.name in teachers
	if doc.doctype == "Dar Quraan Halaqa":
		return bool(teachers.intersection({doc.get("mentor"), doc.get("assistant_mentor")}))
	if doc.doctype == "Dar Quraan Student":
		return bool(
			frappe.db.exists(
				"Dar Quraan Student Assignment", {"student": doc.name, "teacher": ["in", list(teachers)]}
			)
		)
	if doc.doctype == "Dar Quraan Exam":
		return doc.get("examiner_teacher") in teachers
	if doc.doctype in {"Dar Quraan Ijazah", "Dar Quraan Discipline Incident"}:
		return bool(
			frappe.db.exists(
				"Dar Quraan Student Assignment",
				{"name": doc.get("student_assignment"), "teacher": ["in", list(teachers)]},
			)
		)
	if doc.doctype == "Dar Quraan Student Assignment" or doc.doctype in TEACHER_SCOPED_DOCTYPES:
		return doc.get("teacher") in teachers
	return None
