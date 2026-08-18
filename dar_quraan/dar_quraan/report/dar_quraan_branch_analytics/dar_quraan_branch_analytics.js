frappe.query_reports["Dar Quraan Branch Analytics"] = {
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
			fieldname: "branch_status",
			label: __("Branch Status"),
			fieldtype: "Select",
			options: "\nActive\nInactive",
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
	],
};
