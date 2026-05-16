// Copyright (c) 2026, Spiral Code and contributors
// For license information, please see license.txt

frappe.pages["data-import-plus"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Data Import Plus"),
		single_column: true,
	});
	wrapper.data_import_plus = new DataImportPlus(page);
};

frappe.pages["data-import-plus"].on_page_show = function (wrapper) {
	const opts = frappe.route_options;
	if (opts && opts.doctype) {
		// A file picked from a list view jumps straight to the grid;
		// otherwise we just preselect the doctype on the setup screen.
		if (opts.file_url) {
			wrapper.data_import_plus.render_setup();
			wrapper.data_import_plus.load_file(opts.file_url, opts.doctype);
		} else {
			wrapper.data_import_plus.preselect(opts.doctype);
		}
		frappe.route_options = null;
	}
};

class DataImportPlus {
	constructor(page) {
		this.page = page;
		this.body = $(`<div class="dip-wrapper"></div>`).appendTo(page.body);
		this.state = {};
		this.render_setup();
	}

	preselect(doctype) {
		if (this.doctype_field) {
			this.doctype_field.set_value(doctype);
		}
	}

	// --- Step 1: choose doctype + upload --------------------------------
	render_setup() {
		this.body.empty();
		this.state = {};
		const setup = $(`
			<div class="dip-setup">
				<h4>${__("Step 1 · Choose a target & upload a file")}</h4>
				<div class="dip-doctype-field"></div>
				<button class="btn btn-primary dip-upload-btn">
					${frappe.utils.icon("upload", "sm")} ${__("Upload Excel / CSV")}
				</button>
				<p class="text-muted dip-hint">${__("Accepted formats: .xlsx, .xls, .csv")}</p>
			</div>
		`).appendTo(this.body);

		this.doctype_field = frappe.ui.form.make_control({
			parent: setup.find(".dip-doctype-field"),
			df: {
				fieldtype: "Select",
				fieldname: "target_doctype",
				label: __("Import Into"),
				options: [],
				reqd: 1,
			},
			render_input: true,
		});

		frappe.call("data_import_plus.data_import_plus.api.get_supported_doctypes").then((r) => {
			this.doctype_field.df.options = ["", ...(r.message || [])];
			this.doctype_field.refresh();
		});

		setup.find(".dip-upload-btn").on("click", () => this.open_uploader());
	}

	open_uploader() {
		const target = this.doctype_field.get_value();
		if (!target) {
			frappe.msgprint(__("Please choose a target doctype first."));
			return;
		}
		new frappe.ui.FileUploader({
			allow_multiple: false,
			restrictions: { allowed_file_types: [".xlsx", ".xls", ".csv"] },
			on_success: (file) => this.load_file(file.file_url, target),
		});
	}

	load_file(file_url, target_doctype) {
		frappe.dom.freeze(__("Parsing & validating file..."));
		frappe
			.call({
				method: "data_import_plus.data_import_plus.api.parse_file",
				args: { file_url, target_doctype },
			})
			.then((r) => {
				frappe.dom.unfreeze();
				if (r.message) {
					this.state = r.message;
					this.render_grid();
				}
			})
			.catch(() => frappe.dom.unfreeze());
	}

	// --- Step 2: preview & fix grid -------------------------------------
	render_grid() {
		this.body.empty();
		const s = this.state;

		const head = $(`
			<div class="dip-grid-head">
				<div>
					<h4>${__("Step 2 · Preview & Fix")} —
						<span class="text-muted">${frappe.utils.escape_html(s.target_doctype)}</span>
					</h4>
					<div class="dip-legend">
						<span><i class="dip-swatch dip-sw-dup"></i>${__("Duplicate row")}</span>
						<span><i class="dip-swatch dip-sw-mand"></i>${__("Missing mandatory")}</span>
						<span><i class="dip-swatch dip-sw-link"></i>${__("Invalid link value")}</span>
					</div>
				</div>
				<div class="dip-actions">
					<button class="btn btn-default btn-sm dip-restart">${__("Start Over")}</button>
					<button class="btn btn-warning btn-sm dip-autofix">${__("Auto-fix Duplicates")}</button>
					<button class="btn btn-default btn-sm dip-import" disabled>${__("Import")}</button>
				</div>
			</div>
			<div class="dip-summary"></div>
		`).appendTo(this.body);

		if (s.ignored_columns && s.ignored_columns.length) {
			$(`<div class="dip-ignored text-muted">${__("Ignored unrecognised columns")}:
				${frappe.utils.escape_html(s.ignored_columns.join(", "))}</div>`).appendTo(this.body);
		}

		const table = $(`<table class="table table-bordered dip-table"></table>`).appendTo(this.body);
		const thead = $(`<thead></thead>`).appendTo(table);
		const hr = $(`<tr><th class="dip-rownum">#</th></tr>`).appendTo(thead);
		s.columns.forEach((col) => {
			const req = col.reqd ? ` <span class="text-danger">*</span>` : "";
			const link = col.link_doctype ? ` <span class="text-muted">→ ${col.link_doctype}</span>` : "";
			$(`<th>${frappe.utils.escape_html(col.label)}${req}${link}</th>`).appendTo(hr);
		});
		$(`<th class="dip-rowact">${__("Action")}</th>`).appendTo(hr);

		this.tbody = $(`<tbody></tbody>`).appendTo(table);
		s.rows.forEach((row) => this.tbody.append(this.build_row(row)));

		head.find(".dip-restart").on("click", () => this.render_setup());
		head.find(".dip-autofix").on("click", () => this.auto_fix_duplicates());
		head.find(".dip-import").on("click", () => this.do_import());
		this.import_btn = head.find(".dip-import");
		this.autofix_btn = head.find(".dip-autofix");
		this.summary_el = head.find(".dip-summary");

		this.paint();
	}

	build_row(row) {
		const tr = $(`<tr data-row="${row._id}"></tr>`);
		$(`<td class="dip-rownum">${row._id + 1}</td>`).appendTo(tr);

		this.state.columns.forEach((col) => {
			const td = $(`<td data-field="${col.fieldname}"></td>`);
			const input = $(`<input type="text" class="dip-cell-input">`)
				.val(row[col.fieldname] || "")
				.appendTo(td);
			input.on("input", () => {
				row[col.fieldname] = input.val();
				this.revalidate();
			});
			tr.append(td);
		});

		const act = $(`<td class="dip-rowact"></td>`);
		const btn = $(`<button class="btn btn-xs btn-danger dip-del">${__("Delete")}</button>`);
		btn.on("click", () => this.toggle_skip(row._id));
		act.append(btn);
		tr.append(act);
		return tr;
	}

	toggle_skip(row_id) {
		const row = this.state.rows.find((r) => r._id === row_id);
		row._skip = !row._skip;
		const tr = this.tbody.find(`tr[data-row="${row_id}"]`);
		tr.find(".dip-cell-input").prop("disabled", row._skip);
		tr.find(".dip-del").text(row._skip ? __("Restore") : __("Delete"));
		this.revalidate();
	}

	auto_fix_duplicates() {
		// Keep the first occurrence of each duplicate, skip the rest.
		const v = this.state.validation;
		let fixed = 0;
		(v.results || []).forEach((res) => {
			if (res.is_duplicate) {
				const row = this.state.rows.find((r) => r._id === res.row_id);
				if (row && !row._skip) {
					row._skip = true;
					fixed++;
					const tr = this.tbody.find(`tr[data-row="${res.row_id}"]`);
					tr.find(".dip-cell-input").prop("disabled", true);
					tr.find(".dip-del").text(__("Restore"));
				}
			}
		});
		frappe.show_alert(
			fixed
				? __("{0} duplicate row(s) marked to skip", [fixed])
				: __("No duplicate rows to fix")
		);
		this.revalidate();
	}

	// --- Validation painting --------------------------------------------
	revalidate() {
		clearTimeout(this._revalidate_timer);
		this._revalidate_timer = setTimeout(() => {
			frappe
				.call({
					method: "data_import_plus.data_import_plus.api.validate_data",
					args: {
						target_doctype: this.state.target_doctype,
						rows: JSON.stringify(this.state.rows),
					},
				})
				.then((r) => {
					if (r.message) {
						this.state.validation = r.message;
						this.paint();
					}
				});
		}, 350);
	}

	paint() {
		const v = this.state.validation;
		// Reset all visual state.
		this.tbody.find("tr").removeClass("dip-row-duplicate dip-row-skipped");
		this.tbody.find("td").removeClass("dip-cell-mandatory dip-cell-link");

		(v.results || []).forEach((res) => {
			const tr = this.tbody.find(`tr[data-row="${res.row_id}"]`);
			const row = this.state.rows.find((r) => r._id === res.row_id);
			if (row && row._skip) {
				tr.addClass("dip-row-skipped");
				return;
			}
			if (res.is_duplicate) tr.addClass("dip-row-duplicate");
			Object.keys(res.cell_errors || {}).forEach((field) => {
				const cls = res.cell_errors[field] === "link" ? "dip-cell-link" : "dip-cell-mandatory";
				tr.find(`td[data-field="${field}"]`).addClass(cls);
			});
		});

		const sm = v.summary || { total_errors: 0 };
		const active = this.state.rows.filter((r) => !r._skip).length;
		const skipped = this.state.rows.length - active;
		this.summary_el.html(`
			<span class="dip-stat">${__("Rows")}: <b>${this.state.rows.length}</b></span>
			<span class="dip-stat">${__("To import")}: <b>${active}</b></span>
			<span class="dip-stat">${__("Skipped")}: <b>${skipped}</b></span>
			<span class="dip-stat ${sm.total_errors ? "dip-has-errors" : "dip-no-errors"}">
				${__("Errors")}: <b>${sm.total_errors}</b>
				${sm.total_errors ? `(${sm.duplicate_count} ${__("dup")},
					${sm.mandatory_count} ${__("missing")}, ${sm.link_count} ${__("link")})` : ""}
			</span>
		`);

		// Import button enabled only when zero errors and ≥1 row to import.
		const ready = sm.total_errors === 0 && active > 0;
		this.import_btn.prop("disabled", !ready);
		this.import_btn.toggleClass("btn-primary", ready).toggleClass("btn-default", !ready);
	}

	// --- Final import ---------------------------------------------------
	do_import() {
		frappe.confirm(
			__("Import {0} clean record(s) into {1}?", [
				this.state.rows.filter((r) => !r._skip).length,
				this.state.target_doctype,
			]),
			() => {
				frappe.dom.freeze(__("Importing..."));
				frappe
					.call({
						method: "data_import_plus.data_import_plus.api.execute_import",
						args: {
							target_doctype: this.state.target_doctype,
							rows: JSON.stringify(this.state.rows),
							original_file_url: this.state.original_file_url,
							original_file_name: this.state.original_file_name,
						},
					})
					.then((r) => {
						frappe.dom.unfreeze();
						if (r.message) {
							frappe.show_alert(
								{ message: r.message.message, indicator: "green" },
								7
							);
							frappe.msgprint({
								title: __("Import Complete"),
								indicator: "green",
								message: `${r.message.message}.<br>
									${__("Audit log")}:
									<a href="/app/data-import-log/${r.message.log}">${r.message.log}</a>`,
							});
							this.render_setup();
						}
					})
					.catch(() => frappe.dom.unfreeze());
			}
		);
	}
}
