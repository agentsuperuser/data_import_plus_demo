// Copyright (c) 2026, Spiral Code and contributors
// For license information, please see license.txt
//
// Replaces Frappe's built-in Data Import tool with Data Import Plus.
// Any attempt to open a "Data Import" form is redirected to the
// Preview & Fix page (/app/data-import-plus).

frappe.ui.form.on("Data Import", {
	onload(frm) {
		const target = frm.doc && frm.doc.reference_doctype;
		frappe.show_alert({
			message: __("Opening Data Import Plus instead of the default importer"),
			indicator: "blue",
		});
		if (target) {
			frappe.route_options = { doctype: target };
		}
		frappe.set_route("data-import-plus");
	},
});
