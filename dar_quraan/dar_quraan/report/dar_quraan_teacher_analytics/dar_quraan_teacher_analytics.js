frappe.query_reports["Dar Quraan Teacher Analytics"] = {
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
			fieldname: "teacher",
			label: __("Teacher"),
			fieldtype: "Link",
			options: "Dar Quraan Teacher",
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
		},
		{
			fieldname: "halaqa",
			label: __("Halaqa"),
			fieldtype: "Link",
			options: "Dar Quraan Halaqa",
		},
	],
};
