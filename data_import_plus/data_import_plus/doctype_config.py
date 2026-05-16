# Copyright (c) 2026, Spiral Code and contributors
# For license information, please see license.txt
"""Per-doctype configuration for Data Import Plus.

`unique_field` is the field used to detect duplicate rows in an upload.
Add an entry here to support a new doctype in the Preview & Fix tool.
"""

DOCTYPE_CONFIG = {
	"Item": {"unique_field": "item_code"},
	"Customer": {"unique_field": "customer_name"},
	"Supplier": {"unique_field": "supplier_name"},
}


def get_supported_doctypes():
	return sorted(DOCTYPE_CONFIG.keys())


def get_unique_field(doctype):
	return DOCTYPE_CONFIG.get(doctype, {}).get("unique_field")
