"""One-time, idempotent import helpers for the legacy Dar Quraan database."""

from __future__ import annotations

import frappe
from frappe.utils import getdate


RECOVERED_TEACHER_NAMES = {93: "زينب طالب", 94: "مروة طالب", 95: "سناء إبراهيم"}

CENTERS = {
	1: ("بيروت", "منطقة فردان", "DQB-00002"),
	2: ("طرابلس", "شارع المئتين", "DQB-00001"),
	3: ("الفضيلة", "البداوي", None),
	4: ("عرمون", "عرمون", None),
	6: ("عكار", "عكار", None),
	7: ("صيدا", "صيدا", None),
}


def execute():
	"""Import centers, teachers and historical student/teacher relationships."""
	result = {"centers": 0, "locations": 0, "teachers": 0, "assignments": 0, "skipped": []}
	branch_map, location_map = _ensure_centers(result)
	year = _ensure_legacy_academic_year()
	teacher_map = _ensure_teachers(result)
	frappe.db.commit()

	rows = frappe.db.sql(
		"""select id, user_id, student_id, center_id, created_at, updated_at
		from students_centers_teachers where is_deleted = 0 order by id""",
		as_dict=True,
	)
	for row in rows:
		if frappe.db.exists("Dar Quraan Student Assignment", {"legacy_assignment_id": row.id}):
			continue
		student = frappe.db.get_value("Dar Quraan Student", {"legacy_student_id": row.student_id}, "name")
		teacher = teacher_map.get(row.user_id)
		branch = branch_map.get(row.center_id)
		if not student or not teacher or not branch:
			result["skipped"].append(
				{"id": row.id, "student_id": row.student_id, "teacher_id": row.user_id, "center_id": row.center_id}
			)
			continue
		start_date = getdate(row.created_at) if row.created_at else getdate("2023-01-01")
		doc = frappe.get_doc(
			{
				"doctype": "Dar Quraan Student Assignment",
				"student": student,
				"assignment_type": "Temporary",
				"status": "Completed",
				"branch": branch,
				"teaching_location": location_map.get(row.center_id),
				"teacher": teacher,
				"academic_year": year,
				"start_date": start_date,
				"end_date": start_date,
				"legacy_assignment_id": row.id,
				"legacy_student_id": row.student_id,
				"legacy_center_id": row.center_id,
				"legacy_teacher_id": row.user_id or 0,
				"legacy_created_at": row.created_at,
				"legacy_updated_at": row.updated_at,
				"assignment_notes": "Imported from legacy students_centers_teachers table.",
			}
		)
		try:
			frappe.db.savepoint("legacy_assignment")
			doc.insert(ignore_permissions=True)
			result["assignments"] += 1
		except Exception as exc:
			result["skipped"].append({"id": row.id, "error": str(exc)})
			frappe.db.rollback(save_point="legacy_assignment")
	frappe.db.commit()
	return result


def _ensure_centers(result):
	branch_map, location_map = {}, {}
	for legacy_id, (arabic_name, area, existing_branch) in CENTERS.items():
		branch = existing_branch if existing_branch and frappe.db.exists("Dar Quraan Branch", existing_branch) else None
		if not branch:
			branch = frappe.db.get_value("Dar Quraan Branch", {"branch_code": f"LEGACY-{legacy_id}"}, "name")
		if not branch:
			branch = frappe.get_doc(
				{
					"doctype": "Dar Quraan Branch",
					"branch_code": f"LEGACY-{legacy_id}",
					"branch_name": arabic_name,
					"arabic_name": arabic_name,
					"status": "Active",
					"city": area,
					"address_line": area,
					"notes": f"Legacy center ID: {legacy_id}",
				}
			).insert(ignore_permissions=True).name
			result["centers"] += 1
		branch_map[legacy_id] = branch
		code = f"LEGACY-CENTER-{legacy_id}"
		location = frappe.db.get_value("Dar Quraan Teaching Location", {"location_code": code}, "name")
		if not location:
			location = frappe.get_doc(
				{
					"doctype": "Dar Quraan Teaching Location",
					"location_name": arabic_name,
					"location_code": code,
					"arabic_name": arabic_name,
					"status": "Active",
					"location_type": "Branch",
					"branch": branch,
					"inside_branch_premises": 1,
					"area": area,
					"address": area,
					"allow_halaqas": 1,
					"notes": f"Legacy center ID: {legacy_id}",
				}
			).insert(ignore_permissions=True).name
			result["locations"] += 1
		location_map[legacy_id] = location
	return branch_map, location_map


def _ensure_legacy_academic_year():
	name = frappe.db.get_value("Dar Quraan Academic Year", {"academic_year_name": "Legacy 2023–2024"}, "name")
	if name:
		if frappe.db.get_value("Dar Quraan Academic Year", name, "status") in {"Archived", "Closed"}:
			frappe.db.set_value("Dar Quraan Academic Year", name, "status", "Open", update_modified=False)
		return name
	return frappe.get_doc(
		{
			"doctype": "Dar Quraan Academic Year",
			"academic_year_name": "Legacy 2023–2024",
			"status": "Open",
			"start_date": "2023-01-01",
			"end_date": "2024-12-31",
		}
	).insert(ignore_permissions=True).name


def _ensure_teachers(result):
	ids = [r[0] for r in frappe.db.sql("select distinct user_id from students_centers_teachers where is_deleted=0") if r[0]]
	users = {
		r.id: r
		for r in frappe.db.sql(
			"select id, first_name, middle_name, last_name, phone_number, username from users where id in %(ids)s",
			{"ids": ids or [-1]},
			as_dict=True,
		)
	}
	teacher_map = {}
	for legacy_id in ids:
		marker = f"Legacy user ID: {legacy_id}"
		teacher = frappe.db.get_value("Dar Quraan Teacher", {"notes": ["like", f"%{marker}%"]}, "name")
		if not teacher:
			user = users.get(legacy_id)
			parts = [user.first_name, user.middle_name, user.last_name] if user else []
			teacher_name = " ".join(str(part).strip() for part in parts if part) or RECOVERED_TEACHER_NAMES.get(legacy_id) or f"Legacy Teacher {legacy_id}"
			notes = marker if user else f"{marker}\nPlaceholder: user details were absent from the supplied users dump."
			teacher = frappe.get_doc(
				{
					"doctype": "Dar Quraan Teacher",
					"teacher_name": teacher_name,
					"status": "Active",
					"phone": str(user.phone_number) if user and user.phone_number else None,
					"notes": notes,
				}
			).insert(ignore_permissions=True).name
			result["teachers"] += 1
		teacher_map[legacy_id] = teacher
	return teacher_map
