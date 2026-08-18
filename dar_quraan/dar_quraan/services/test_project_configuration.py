import frappe
from frappe.tests.utils import FrappeTestCase


class TestProjectConfiguration(FrappeTestCase):
	def permission(self, doctype, role):
		meta = frappe.get_meta(doctype, cached=False)
		return next((row for row in meta.permissions if row.role == role), None)

	def test_teacher_schema_supports_runtime_contracts(self):
		meta = frappe.get_meta("Dar Quraan Teacher", cached=False)
		for fieldname in ("teacher_name", "status", "branch", "user", "email", "phone"):
			with self.subTest(fieldname=fieldname):
				self.assertTrue(meta.has_field(fieldname))
		self.assertEqual(meta.title_field, "teacher_name")

	def test_manager_has_full_access(self):
		for doctype in (
			"Dar Quraan Settings",
			"Dar Quraan Student",
			"Dar Quraan Attendance",
			"Dar Quraan Exception",
		):
			with self.subTest(doctype=doctype):
				p = self.permission(doctype, "Dar Quraan Manager")
				self.assertTrue(p and p.read and p.write and p.create and p.delete)

	def test_supervisor_cannot_delete_or_manage_settings(self):
		self.assertIsNone(self.permission("Dar Quraan Settings", "Dar Quraan Supervisor"))
		p = self.permission("Dar Quraan Attendance", "Dar Quraan Supervisor")
		self.assertTrue(p and p.read and p.write and p.create)
		self.assertFalse(p.delete)

	def test_teacher_operates_daily_records_but_not_student_master(self):
		operational = self.permission("Dar Quraan Attendance", "Dar Quraan Teacher")
		student = self.permission("Dar Quraan Student", "Dar Quraan Teacher")
		self.assertTrue(operational.read and operational.write and operational.create)
		self.assertFalse(operational.delete)
		self.assertTrue(student.read)
		self.assertFalse(student.write or student.create or student.delete)

	def test_data_entry_can_manage_students_without_delete(self):
		p = self.permission("Dar Quraan Student", "Dar Quraan Data Entry")
		self.assertTrue(p.read and p.write and p.create)
		self.assertFalse(p.delete)

	def test_viewer_is_read_only_and_has_no_settings_access(self):
		self.assertIsNone(self.permission("Dar Quraan Settings", "Dar Quraan Viewer"))
		for doctype in ("Dar Quraan Student", "Dar Quraan Attendance", "Dar Quraan Exception"):
			with self.subTest(doctype=doctype):
				p = self.permission(doctype, "Dar Quraan Viewer")
				self.assertTrue(p.read)
				self.assertFalse(p.write or p.create or p.delete)

	def test_workspace_has_operational_navigation(self):
		workspace = frappe.get_doc("Workspace", "Dar Quraan")
		content = frappe.parse_json(workspace.content)
		shortcuts = {item.get("data", {}).get("shortcut_name") for item in content}
		for target in ("Dar Quraan Attendance", "Dar Quraan Student", "Dar Quraan Exception"):
			with self.subTest(target=target):
				self.assertIn(target, shortcuts)
