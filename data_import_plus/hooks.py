app_name = "data_import_plus"
app_title = "Data Import Plus"
app_publisher = "Spiral Code"
app_description = "Preview and Fix data imports before committing"
app_email = "spiralcodeinnovatesllp@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "data_import_plus",
# 		"logo": "/assets/data_import_plus/logo.png",
# 		"title": "Data Import Plus",
# 		"route": "/data_import_plus",
# 		"has_permission": "data_import_plus.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/data_import_plus/css/data_import_plus.css"
# app_include_js = "/assets/data_import_plus/js/data_import_plus.js"

# Add the "Import with Preview" button to supported list views.
doctype_list_js = {
	"Item": "public/js/import_with_preview.js",
	"Customer": "public/js/import_with_preview.js",
	"Supplier": "public/js/import_with_preview.js",
}

# Replace the built-in Data Import tool with Data Import Plus.
doctype_js = {
	"Data Import": "public/js/data_import_override.js",
}

# include js, css files in header of web template
# web_include_css = "/assets/data_import_plus/css/data_import_plus.css"
# web_include_js = "/assets/data_import_plus/js/data_import_plus.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "data_import_plus/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "data_import_plus/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "data_import_plus.utils.jinja_methods",
# 	"filters": "data_import_plus.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "data_import_plus.install.before_install"
# after_install = "data_import_plus.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "data_import_plus.uninstall.before_uninstall"
# after_uninstall = "data_import_plus.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "data_import_plus.utils.before_app_install"
# after_app_install = "data_import_plus.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "data_import_plus.utils.before_app_uninstall"
# after_app_uninstall = "data_import_plus.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "data_import_plus.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"data_import_plus.tasks.all"
# 	],
# 	"daily": [
# 		"data_import_plus.tasks.daily"
# 	],
# 	"hourly": [
# 		"data_import_plus.tasks.hourly"
# 	],
# 	"weekly": [
# 		"data_import_plus.tasks.weekly"
# 	],
# 	"monthly": [
# 		"data_import_plus.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "data_import_plus.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "data_import_plus.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "data_import_plus.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["data_import_plus.utils.before_request"]
# after_request = ["data_import_plus.utils.after_request"]

# Job Events
# ----------
# before_job = ["data_import_plus.utils.before_job"]
# after_job = ["data_import_plus.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"data_import_plus.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

