from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from dar_quraan.dar_quraan.services import permissions


class TestTeacherPermissions(FrappeTestCase):
	def restricted_roles(self, user=None):
		return ["Dar Quraan Teacher"]

	def test_elevated_roles_are_not_restricted(self):
		for role in permissions.ELEVATED_ROLES:
			with (
				self.subTest(role=role),
				patch.object(frappe, "get_roles", return_value=["Dar Quraan Teacher", role]),
			):
				self.assertFalse(permissions.is_restricted_teacher("user@example.com"))

	def test_teacher_query_is_scoped_to_linked_teacher(self):
		with (
			patch.object(frappe, "get_roles", side_effect=self.restricted_roles),
			patch.object(frappe, "get_all", return_value=["DQ-TEA-00001"]),
		):
			condition = permissions.get_attendance_query_condition("teacher@example.com")
		self.assertIn("`tabDar Quraan Attendance`.`teacher`", condition)
		self.assertIn("DQ-TEA-00001", condition)

	def test_teacher_without_profile_sees_no_scoped_records(self):
		with (
			patch.object(frappe, "get_roles", side_effect=self.restricted_roles),
			patch.object(frappe, "get_all", return_value=[]),
		):
			condition = permissions.get_assignment_query_condition("teacher@example.com")
		self.assertIn("in (NULL)", condition)

	def test_teacher_has_permission_only_for_own_record(self):
		owned = frappe._dict(doctype="Dar Quraan Attendance", teacher="DQ-TEA-00001")
		other = frappe._dict(doctype="Dar Quraan Attendance", teacher="DQ-TEA-00002")
		with (
			patch.object(frappe, "get_roles", side_effect=self.restricted_roles),
			patch.object(frappe, "get_all", return_value=["DQ-TEA-00001"]),
		):
			self.assertTrue(permissions.has_teacher_permission(owned, "teacher@example.com"))
			self.assertFalse(permissions.has_teacher_permission(other, "teacher@example.com"))

	def test_student_scope_uses_teacher_assignments(self):
		with (
			patch.object(frappe, "get_roles", side_effect=self.restricted_roles),
			patch.object(frappe, "get_all", return_value=["DQ-TEA-00001"]),
		):
			condition = permissions.get_student_query_condition("teacher@example.com")
		self.assertIn("Dar Quraan Student Assignment", condition)
		self.assertIn("dqsa.teacher", condition)
