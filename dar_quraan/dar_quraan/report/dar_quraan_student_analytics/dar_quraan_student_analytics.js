frappe.query_reports["Dar Quraan Student Analytics"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "assignment_status",
			label: __("Assignment Status"),
			fieldtype: "Select",
			options: "\nDraft\nActive\nCompleted\nCancelled\nSuspended",
			default: "Active",
		},
		{
			fieldname: "student",
			label: __("Student"),
			fieldtype: "Link",
			options: "Dar Quraan Student",
		},
		{
			fieldname: "student_assignment",
			label: __("Student Assignment"),
			fieldtype: "Link",
			options: "Dar Quraan Student Assignment",
			get_query: () => ({
				filters: {
					student: frappe.query_report.get_filter_value("student"),
				},
			}),
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Dar Quraan Branch",
		},
		{
			fieldname: "teaching_location",
			label: __("Teaching Location"),
			fieldtype: "Link",
			options: "Dar Quraan Teaching Location",
			get_query: () => ({
				filters: {
					branch: frappe.query_report.get_filter_value("branch"),
				},
			}),
		},
		{
			fieldname: "halaqa",
			label: __("Halaqa"),
			fieldtype: "Link",
			options: "Dar Quraan Halaqa",
			get_query: () => ({
				filters: {
					branch: frappe.query_report.get_filter_value("branch"),
					teaching_location: frappe.query_report.get_filter_value("teaching_location"),
				},
			}),
		},
		{
			fieldname: "teacher",
			label: __("Teacher"),
			fieldtype: "Link",
			options: "Dar Quraan Teacher",
		},
	],
};
