# Copyright (c) 2026, Spiral Code and contributors
# For license information, please see license.txt
"""Doctype resolution for Data Import Plus.

The tool now supports any doctype that allows import — the same set the
standard Frappe Data Import tool offers. `DOCTYPE_CONFIG` is only an
optional override: list a doctype here to force a specific duplicate-check
field. Anything not listed is resolved automatically from metadata.
"""

import frappe

# Optional per-doctype override for the duplicate-check field.
# Leave empty to rely entirely on metadata.
DOCTYPE_CONFIG = {
	"Item": {"unique_field": "item_code"},
	"Customer": {"unique_field": "customer_name"},
	"Supplier": {"unique_field": "supplier_name"},
}


def get_supported_doctypes():
	"""Every importable doctype — same list standard Data Import uses."""
	return frappe.get_all(
		"DocType",
		filters={"allow_import": 1, "istable": 0, "issingle": 0},
		pluck="name",
		order_by="name",
	)


def is_supported(doctype):
	"""True if `doctype` allows import (and is not a child/single table)."""
	if not doctype or not frappe.db.exists("DocType", doctype):
		return False
	dt = frappe.get_doc("DocType", doctype)
	return bool(dt.allow_import) and not dt.istable and not dt.issingle


def get_unique_field(doctype):
	"""Field used to detect duplicate rows in an upload.

	An explicit DOCTYPE_CONFIG entry wins; otherwise it is derived from the
	doctype's metadata — the autoname `field:` target, or the first field
	flagged unique. Returns None when no such field exists (the duplicate
	check is then skipped).
	"""
	override = DOCTYPE_CONFIG.get(doctype, {}).get("unique_field")
	if override:
		return override

	meta = frappe.get_meta(doctype)
	autoname = (meta.autoname or "").strip()
	if autoname.startswith("field:"):
		return autoname.split(":", 1)[1].strip()
	for df in meta.fields:
		if df.unique:
			return df.fieldname
	return None
