frappe.query_reports["Dar Quraan Halaqa Analytics"] = {
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
			fieldname: "halaqa_status",
			label: __("Halaqa Status"),
			fieldtype: "Select",
			options: "\nPlanning\nActive\nSuspended\nClosed",
			default: "Active",
		},
		{
			fieldname: "assignment_status",
			label: __("Assignment Status"),
			fieldtype: "Select",
			options: "\nDraft\nActive\nCompleted\nCancelled\nSuspended",
			default: "Active",
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
		{
			fieldname: "teacher",
			label: __("Mentor"),
			fieldtype: "Link",
			options: "Dar Quraan Teacher",
		},
	],
};
