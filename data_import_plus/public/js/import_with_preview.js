// Copyright (c) 2026, Spiral Code and contributors
// For license information, please see license.txt
//
// Adds an "Import with Preview" button to the list view of every doctype
// supported by Data Import Plus. The button opens a file picker and then
// routes to the Preview & Fix page with the uploaded file.

frappe.provide("frappe.listview_settings");

(function () {
	const SUPPORTED = ["Item", "Customer", "Supplier"];

	function open_preview_import(doctype) {
		new frappe.ui.FileUploader({
			allow_multiple: false,
			restrictions: { allowed_file_types: [".xlsx", ".xls", ".csv"] },
			on_success: (file) => {
				frappe.route_options = { doctype: doctype, file_url: file.file_url };
				frappe.set_route("data-import-plus");
			},
		});
	}

	SUPPORTED.forEach((doctype) => {
		const existing = frappe.listview_settings[doctype] || {};
		const prev_onload = existing.onload;

		// Extend, don't replace - other apps (e.g. ERPNext) configure these.
		frappe.listview_settings[doctype] = Object.assign(existing, {
			onload(listview) {
				if (typeof prev_onload === "function") prev_onload(listview);
				listview.page.add_inner_button(__("Import with Preview"), () =>
					open_preview_import(doctype)
				);
			},
		});
	});
})();
