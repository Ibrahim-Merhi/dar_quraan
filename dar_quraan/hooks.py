app_name = "dar_quraan"
app_title = "Dar Quraan"
app_publisher = "Ibrahim Merhi"
app_description = "Quraan Institute Managment System"
app_email = "ibrahim.m.merhy@gmail.com"
app_license = "mit"

fixtures = [
	{
		"dt": "Role",
		"filters": [
			[
				"name",
				"in",
				[
					"Dar Quraan Manager",
					"Dar Quraan Supervisor",
					"Dar Quraan Teacher",
					"Dar Quraan Data Entry",
					"Dar Quraan Viewer",
				],
			]
		],
	}
]

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "dar_quraan",
# 		"logo": "/assets/dar_quraan/logo.png",
# 		"title": "Dar Quraan",
# 		"route": "/dar_quraan",
# 		"has_permission": "dar_quraan.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/dar_quraan/css/dar_quraan.css"
# app_include_js = "/assets/dar_quraan/js/dar_quraan.js"

# include js, css files in header of web template
# web_include_css = "/assets/dar_quraan/css/dar_quraan.css"
# web_include_js = "/assets/dar_quraan/js/dar_quraan.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "dar_quraan/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "dar_quraan/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "dar_quraan.utils.jinja_methods",
# 	"filters": "dar_quraan.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "dar_quraan.install.before_install"
# after_install = "dar_quraan.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "dar_quraan.uninstall.before_uninstall"
# after_uninstall = "dar_quraan.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "dar_quraan.utils.before_app_install"
# after_app_install = "dar_quraan.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "dar_quraan.utils.before_app_uninstall"
# after_app_uninstall = "dar_quraan.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "dar_quraan.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

permission_query_conditions = {
	"Dar Quraan Teacher": "dar_quraan.dar_quraan.services.permissions.get_teacher_query_condition",
	"Dar Quraan Halaqa": "dar_quraan.dar_quraan.services.permissions.get_halaqa_query_condition",
	"Dar Quraan Student": "dar_quraan.dar_quraan.services.permissions.get_student_query_condition",
	"Dar Quraan Student Assignment": "dar_quraan.dar_quraan.services.permissions.get_assignment_query_condition",
	"Dar Quraan Attendance": "dar_quraan.dar_quraan.services.permissions.get_attendance_query_condition",
	"Dar Quraan Evaluation": "dar_quraan.dar_quraan.services.permissions.get_evaluation_query_condition",
	"Dar Quraan Exception": "dar_quraan.dar_quraan.services.permissions.get_exception_query_condition",
	"Dar Quraan Next Assignment": "dar_quraan.dar_quraan.services.permissions.get_next_assignment_query_condition",
	"Dar Quraan Session": "dar_quraan.dar_quraan.services.permissions.get_session_query_condition",
	"Dar Quraan Student Progress": "dar_quraan.dar_quraan.services.permissions.get_progress_query_condition",
	"Dar Quraan Student Quran State": "dar_quraan.dar_quraan.services.permissions.get_quran_state_query_condition",
	"Dar Quraan Supervision Visit": "dar_quraan.dar_quraan.services.permissions.get_supervision_query_condition",
	"Dar Quraan Teacher Follow Up": "dar_quraan.dar_quraan.services.permissions.get_follow_up_query_condition",
}

has_permission = {
	doctype: "dar_quraan.dar_quraan.services.permissions.has_teacher_permission"
	for doctype in permission_query_conditions
}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": ["dar_quraan.dar_quraan.services.exceptions.detect_daily_exceptions"],
}

# Testing
# -------

# before_tests = "dar_quraan.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "dar_quraan.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "dar_quraan.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["dar_quraan.utils.before_request"]
# after_request = ["dar_quraan.utils.after_request"]

# Job Events
# ----------
# before_job = ["dar_quraan.utils.before_job"]
# after_job = ["dar_quraan.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"dar_quraan.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
