frappe.ui.form.on("Dar Quraan Admission Application", {
	refresh(frm) {
		if (frm.is_new()) return;
		if (frm.doc.status === "Pending") {
			frm.add_custom_button(__("Start Review"), () =>
				frm.call("start_review").then(() => frm.reload_doc())
			);
		}
		if (frm.doc.status === "In Process") {
			frm.add_custom_button(
				__("Provisionally Approve"),
				() => frm.call("provisionally_approve").then(() => frm.reload_doc()),
				__("Actions")
			);
			frm.add_custom_button(
				__("Reject"),
				() => {
					frappe.prompt(
						{
							fieldname: "reason",
							fieldtype: "Small Text",
							label: __("Rejection Reason"),
							reqd: 1,
						},
						(values) =>
							frm
								.call("reject", { reason: values.reason })
								.then(() => frm.reload_doc())
					);
				},
				__("Actions")
			);
		}
		if (frm.doc.status === "Provisionally Approved" && !frm.doc.student) {
			frm.add_custom_button(__("Finalize Admission"), () =>
				frm.call("finalize_admission").then(() => frm.reload_doc())
			);
		}
	},
});
