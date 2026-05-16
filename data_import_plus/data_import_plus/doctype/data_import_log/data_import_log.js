// Copyright (c) 2026, Spiral Code and contributors
// For license information, please see license.txt

frappe.ui.form.on("Data Import Log", {
	refresh(frm) {
		if (frm.doc.target_doctype) {
			frm.add_custom_button(__("New Import"), () => {
				frappe.set_route("data-import-plus", { doctype: frm.doc.target_doctype });
			});
		}
	},
});
