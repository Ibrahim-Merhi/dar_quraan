import frappe
from frappe.desk.desktop import get_workspace_sidebar_items
from frappe.tests.utils import FrappeTestCase


class TestRoleDeskSmoke(FrappeTestCase):
	def make_user(self, role):
		email = f"dq-{frappe.scrub(role)}-{frappe.generate_hash(length=8)}@example.com"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": role,
				"enabled": 1,
				"send_welcome_email": 0,
				"roles": [{"role": role}],
			}
		).insert(ignore_permissions=True)
		return user.name

	def test_all_roles_can_open_desk_workspace_and_analytics(self):
		expectations = {
			"Dar Quraan Manager": ("Dar Quraan Settings", "write", True),
			"Dar Quraan Supervisor": ("Dar Quraan Attendance", "delete", False),
			"Dar Quraan Teacher": ("Dar Quraan Attendance", "create", True),
			"Dar Quraan Data Entry": ("Dar Quraan Student", "create", True),
			"Dar Quraan Viewer": ("Dar Quraan Attendance", "write", False),
		}
		try:
			for role, (doctype, permission_type, expected) in expectations.items():
				with self.subTest(role=role):
					frappe.set_user(self.make_user(role))
					frappe.clear_cache(user=frappe.session.user)
					sidebar = get_workspace_sidebar_items()
					self.assertIn("Dar Quraan", {page.name for page in sidebar["pages"]})
					self.assertTrue(frappe.get_doc("Report", "Dar Quraan Student Analytics").is_permitted())
					self.assertEqual(frappe.has_permission(doctype, permission_type), expected)
		finally:
			frappe.set_user("Administrator")
