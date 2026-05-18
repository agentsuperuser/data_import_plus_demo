# Copyright (c) 2026, Spiral Code and contributors
# For license information, please see license.txt
"""Backend API for the Data Import Plus "Preview & Fix" tool.

Whitelisted endpoints
---------------------
get_supported_doctypes : list doctypes the tool can import into
parse_file             : read an uploaded Excel/CSV file and run validation
validate_data          : re-run validation on edited grid rows
execute_import         : insert clean rows and write a Data Import Log
"""

import csv
import io
import json

import frappe
import pandas as pd
from frappe import _

from data_import_plus.data_import_plus.doctype_config import (
	get_supported_doctypes as _supported,
	get_unique_field,
	is_supported,
)

# Fieldtypes that never carry an importable value.
NO_VALUE_FIELDTYPES = {
	"Section Break",
	"Column Break",
	"Tab Break",
	"HTML",
	"Button",
	"Heading",
	"Fold",
	"Table",
	"Table MultiSelect",
	"Image",
}


# ---------------------------------------------------------------------------
# Field metadata helpers
# ---------------------------------------------------------------------------
def _field_index(target_doctype):
	"""Return ({fieldname: meta}, {normalised header: fieldname})."""
	meta = frappe.get_meta(target_doctype)
	fields = {}
	lookup = {}
	for df in meta.fields:
		if df.fieldtype in NO_VALUE_FIELDTYPES or not df.fieldname:
			continue
		fields[df.fieldname] = {
			"fieldname": df.fieldname,
			"label": df.label or df.fieldname,
			"fieldtype": df.fieldtype,
			"reqd": int(df.reqd or 0),
			"link_doctype": df.options if df.fieldtype == "Link" else None,
		}
		lookup[df.fieldname.strip().lower()] = df.fieldname
		if df.label:
			lookup[df.label.strip().lower()] = df.fieldname

	# The autoname field (e.g. item_code) behaves as mandatory.
	autoname = (meta.autoname or "").strip()
	if autoname.startswith("field:"):
		fn = autoname.split(":", 1)[1].strip()
		if fn in fields:
			fields[fn]["reqd"] = 1
	return fields, lookup


def _columns_for(target_doctype, headers):
	"""Map raw upload headers to doctype fields.

	Returns (columns, ignored_headers). `columns` always includes every
	mandatory field of the doctype so the grid can surface missing data.
	"""
	fields, lookup = _field_index(target_doctype)
	columns = []
	used = set()
	ignored = []

	for raw in headers:
		key = str(raw).strip().lower()
		fieldname = lookup.get(key)
		if fieldname and fieldname not in used:
			columns.append({**fields[fieldname], "header": raw})
			used.add(fieldname)
		else:
			ignored.append(raw)

	# Surface mandatory fields that were not part of the upload.
	for fieldname, meta in fields.items():
		if meta["reqd"] and fieldname not in used:
			columns.append({**meta, "header": meta["label"]})
			used.add(fieldname)

	return columns, ignored


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def _clean(value):
	if value is None:
		return ""
	text = str(value).strip()
	if text.lower() in ("nan", "nat", "none", "<na>"):
		return ""
	return text


def _validate(target_doctype, columns, rows):
	"""Run the three pre-import checks against the active (non-skipped) rows.

	Returns a dict with per-row results and an aggregate summary.
	"""
	unique_field = get_unique_field(target_doctype)
	link_cache = {}

	def link_exists(doctype, value):
		ck = (doctype, value)
		if ck not in link_cache:
			link_cache[ck] = bool(frappe.db.exists(doctype, value))
		return link_cache[ck]

	seen_unique = set()
	results = []
	duplicate_count = mandatory_count = link_count = 0

	for row in rows:
		row_id = row.get("_id")
		skipped = bool(row.get("_skip"))
		res = {"row_id": row_id, "is_duplicate": False, "cell_errors": {}}

		if skipped:
			results.append(res)
			continue

		# Check 1 - duplicates on the configured unique field.
		if unique_field:
			key = _clean(row.get(unique_field)).lower()
			if key:
				if key in seen_unique:
					res["is_duplicate"] = True
					duplicate_count += 1
				else:
					seen_unique.add(key)

		# Checks 2 & 3 - mandatory fields and link field integrity.
		for col in columns:
			fieldname = col["fieldname"]
			value = _clean(row.get(fieldname))
			if col["reqd"] and not value:
				res["cell_errors"][fieldname] = "mandatory"
				mandatory_count += 1
			elif col["link_doctype"] and value and not link_exists(
				col["link_doctype"], value
			):
				res["cell_errors"][fieldname] = "link"
				link_count += 1

		results.append(res)

	total_errors = duplicate_count + mandatory_count + link_count
	return {
		"results": results,
		"summary": {
			"total_errors": total_errors,
			"duplicate_count": duplicate_count,
			"mandatory_count": mandatory_count,
			"link_count": link_count,
		},
	}


def _coerce(rows):
	"""Accept rows as a JSON string (from form-encoded calls) or a list."""
	if isinstance(rows, str):
		rows = json.loads(rows)
	return rows or []


# ---------------------------------------------------------------------------
# Whitelisted endpoints
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_supported_doctypes():
	return _supported()


def _template_fields(target_doctype):
	"""Importable fields for a template — meta order, each with a reqd flag.

	Skips layout / no-value fieldtypes, hidden, read-only and virtual fields.
	The autoname `field:` target (e.g. Item Code) is reported as required.
	"""
	meta = frappe.get_meta(target_doctype)
	autoname = (meta.autoname or "").strip()
	autoname_field = (
		autoname.split(":", 1)[1].strip() if autoname.startswith("field:") else None
	)
	fields = []
	for df in meta.fields:
		if df.fieldtype in NO_VALUE_FIELDTYPES or not df.fieldname:
			continue
		if df.hidden or df.read_only or getattr(df, "is_virtual", 0):
			continue
		fields.append({
			"fieldname": df.fieldname,
			"label": df.label or df.fieldname,
			"reqd": int(bool(df.reqd) or df.fieldname == autoname_field),
		})
	return fields


def _template_headers(target_doctype, selected=None):
	"""Column headers (exact field labels) for an import template.

	`selected` - optional list of fieldnames to include. When given, only
	those fields are used (kept in doctype meta order). When omitted, every
	importable field is used with mandatory fields first. Labels are used as
	headers so a filled-in template re-uploads cleanly through `_columns_for`.
	"""
	fields = _template_fields(target_doctype)
	if selected:
		wanted = set(selected)
		fields = [f for f in fields if f["fieldname"] in wanted]
	else:
		# Stable sort keeps meta order within the mandatory / optional groups.
		fields = sorted(fields, key=lambda f: 0 if f["reqd"] else 1)
	return [f["label"] for f in fields]


@frappe.whitelist()
def get_importable_fields(target_doctype):
	"""Return [{fieldname, label, reqd}] for the field-selection dialog."""
	if not is_supported(target_doctype):
		frappe.throw(_("Doctype {0} does not allow data import").format(target_doctype))
	return _template_fields(target_doctype)


@frappe.whitelist()
def download_template(target_doctype, file_type="Excel", fields=None):
	"""Stream a blank import template (headers only) for the doctype.

	`fields` - optional JSON list of fieldnames chosen in the dialog; when
	omitted the template includes every importable field.
	"""
	if not is_supported(target_doctype):
		frappe.throw(_("Doctype {0} does not allow data import").format(target_doctype))

	selected = None
	if fields:
		selected = fields if isinstance(fields, list) else json.loads(fields)

	headers = _template_headers(target_doctype, selected)
	if not headers:
		frappe.throw(_("Select at least one field for the template."))
	base = target_doctype.replace(" ", "_") + "_template"

	if str(file_type).lower() in ("csv", ".csv"):
		buffer = io.StringIO()
		csv.writer(buffer).writerow(headers)
		content = buffer.getvalue().encode("utf-8")
		filename = base + ".csv"
	else:
		buffer = io.BytesIO()
		pd.DataFrame(columns=headers).to_excel(buffer, index=False, engine="openpyxl")
		content = buffer.getvalue()
		filename = base + ".xlsx"

	frappe.response["filename"] = filename
	frappe.response["filecontent"] = content
	frappe.response["type"] = "binary"


@frappe.whitelist()
def parse_file(file_url, target_doctype):
	"""Read an uploaded file with Pandas and return columns + validated rows."""
	if not is_supported(target_doctype):
		frappe.throw(_("Doctype {0} does not allow data import").format(target_doctype))

	file_doc = frappe.get_doc("File", {"file_url": file_url})
	content = file_doc.get_content()
	if isinstance(content, str):
		content = content.encode("utf-8")

	name = (file_doc.file_name or file_url).lower()
	try:
		if name.endswith(".csv"):
			df = pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False)
		else:
			df = pd.read_excel(io.BytesIO(content), dtype=str, engine="openpyxl")
	except Exception as exc:  # noqa: BLE001
		frappe.throw(_("Could not read the file: {0}").format(str(exc)))

	df = df.fillna("")
	headers = [str(h) for h in df.columns]
	columns, ignored = _columns_for(target_doctype, headers)
	header_to_field = {c["header"]: c["fieldname"] for c in columns}

	rows = []
	for idx, record in enumerate(df.to_dict("records")):
		row = {"_id": idx, "_skip": False}
		for col in columns:
			row[col["fieldname"]] = ""
		for raw_header, value in record.items():
			fieldname = header_to_field.get(raw_header)
			if fieldname:
				row[fieldname] = _clean(value)
		rows.append(row)

	validation = _validate(target_doctype, columns, rows)
	return {
		"target_doctype": target_doctype,
		"unique_field": get_unique_field(target_doctype),
		"columns": columns,
		"rows": rows,
		"ignored_columns": ignored,
		"validation": validation,
		"original_file_url": file_url,
		"original_file_name": file_doc.file_name,
	}


@frappe.whitelist()
def validate_data(target_doctype, rows):
	"""Re-run validation after the user edits the grid."""
	rows = _coerce(rows)
	columns, _ignored = _columns_for(target_doctype, _headers_from_rows(rows))
	return _validate(target_doctype, columns, rows)


def _headers_from_rows(rows):
	headers = []
	for row in rows:
		for key in row:
			if not key.startswith("_") and key not in headers:
				headers.append(key)
	return headers


@frappe.whitelist()
def execute_import(target_doctype, rows, original_file_url=None, original_file_name=None):
	"""Insert all clean, non-skipped rows and record a Data Import Log."""
	rows = _coerce(rows)
	columns, _ignored = _columns_for(target_doctype, _headers_from_rows(rows))

	# Refuse to import if anything is still wrong - the grid should prevent
	# this, but the server is the source of truth.
	validation = _validate(target_doctype, columns, rows)
	if validation["summary"]["total_errors"]:
		frappe.throw(_("Cannot import: {0} unresolved error(s) remain.").format(
			validation["summary"]["total_errors"]
		))

	field_names = [c["fieldname"] for c in columns]
	to_import = [r for r in rows if not r.get("_skip")]
	skipped = len(rows) - len(to_import)

	imported = []
	errors = []
	for row in to_import:
		values = {fn: _clean(row.get(fn)) for fn in field_names if _clean(row.get(fn)) != ""}
		try:
			doc = frappe.get_doc({"doctype": target_doctype, **values})
			doc.insert()
			imported.append({**values, "name": doc.name})
		except Exception as exc:  # noqa: BLE001
			errors.append({"row": row.get("_id"), "error": str(exc)})

	log = _create_log(
		target_doctype=target_doctype,
		total=len(rows),
		imported=imported,
		skipped=skipped,
		errors=errors,
		field_names=field_names,
		original_file_url=original_file_url,
		original_file_name=original_file_name,
	)

	if errors:
		frappe.db.commit()
		frappe.throw(
			_("Imported {0}, but {1} row(s) failed. See Data Import Log {2}.").format(
				len(imported), len(errors), log
			)
		)

	return {
		"log": log,
		"imported_count": len(imported),
		"skipped_count": skipped,
		"message": _("{0} records imported, {1} skipped").format(len(imported), skipped),
	}


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------
def _create_log(target_doctype, total, imported, skipped, errors, field_names,
		original_file_url, original_file_name):
	"""Create the Data Import Log and attach the original + cleaned files."""
	from frappe.utils.file_manager import save_file

	log = frappe.new_doc("Data Import Log")
	log.target_doctype = target_doctype
	log.import_date = frappe.utils.now()
	log.status = "Failed" if errors else "Completed"
	log.total_records = total
	log.imported_count = len(imported)
	log.skipped_count = skipped
	log.original_file = original_file_url
	log.error_log = json.dumps(errors, indent=2) if errors else json.dumps(
		{"info": "All rows validated and imported successfully."}
	)
	log.insert(ignore_permissions=True)

	# Re-parent the original upload to this log for a complete audit trail.
	if original_file_url:
		file_name = frappe.db.get_value("File", {"file_url": original_file_url})
		if file_name:
			fdoc = frappe.get_doc("File", file_name)
			fdoc.attached_to_doctype = "Data Import Log"
			fdoc.attached_to_name = log.name
			fdoc.save(ignore_permissions=True)

	# Build the cleaned Excel from the rows that were actually imported.
	if imported:
		clean_df = pd.DataFrame(imported, columns=field_names + ["name"])
		buffer = io.BytesIO()
		clean_df.to_excel(buffer, index=False, engine="openpyxl")
		base = (original_file_name or f"{target_doctype}.xlsx").rsplit(".", 1)[0]
		cleaned = save_file(
			f"{base}_cleaned.xlsx",
			buffer.getvalue(),
			"Data Import Log",
			log.name,
			is_private=1,
		)
		log.db_set("cleaned_file", cleaned.file_url)

	return log.name
