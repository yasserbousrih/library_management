app_name = "library_management"
app_title = "Library Management"
app_publisher = "Yasser Bousrih"
app_description = "Library Management"
app_email = "yasser040503@gmail.com"
app_license = "mit"
app_icon = "octicon octicon-book"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "library_management",
		"title": "Library Management",
		"route": "/library_management"
	}
]

# Modules
# ------------------
modules = ["library_management"]

# Website Settings
# ------------------
# Disable default Frappe navbar
website_context = {
    "hide_sidebar": True,
    "hide_navbar": True
}

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/library_management/css/library_management.css"
# app_include_js = "/assets/library_management/js/library_management.js"

# include js, css files in header of web template
# web_include_css = "/assets/library_management/css/library_management.css"
# web_include_js = "/assets/library_management/js/library_management.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "library_management/library_management/public/scss/website"

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
# app_include_icons = "library_management/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "home"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Web Page Routes
# ---------------
# Define custom routes for web pages
website_route_rules = [
    {"from_route": "/", "to_route": "home"},
    {"from_route": "/home", "to_route": "home"},
    {"from_route": "/signup", "to_route": "signup"},
    {"from_route": "/login", "to_route": "login"},
    {"from_route": "/articles-page", "to_route": "articles-page"},
    {"from_route": "/article-detail", "to_route": "article-detail"},
    {"from_route": "/membership", "to_route": "membership"},
    {"from_route": "/my-articles", "to_route": "my-articles"},
]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "library_management.library_management.utils.jinja_methods",
# 	"filters": "library_management.library_management.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "library_management.library_management.install.before_install"
# after_install = "library_management.setup_web_pages.after_install"

# Uninstallation
# ------------

# before_uninstall = "library_management.library_management.uninstall.before_uninstall"
# after_uninstall = "library_management.library_management.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "library_management.library_management.utils.before_app_install"
# after_app_install = "library_management.library_management.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "library_management.library_management.utils.before_app_uninstall"
# after_app_uninstall = "library_management.library_management.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "library_management.library_management.notifications.get_notification_config"

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
# 		"library_management.library_management.tasks.all"
# 	],
# 	"daily": [
# 		"library_management.library_management.tasks.daily"
# 	],
# 	"hourly": [
# 		"library_management.library_management.tasks.hourly"
# 	],
# 	"weekly": [
# 		"library_management.library_management.tasks.weekly"
# 	],
# 	"monthly": [
# 		"library_management.library_management.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "library_management.library_management.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "library_management.library_management.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "library_management.library_management.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["library_management.library_management.utils.before_request"]
# after_request = ["library_management.library_management.utils.after_request"]

# Job Events
# ----------
# before_job = ["library_management.library_management.utils.before_job"]
# after_job = ["library_management.library_management.utils.after_job"]

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
# 	"library_management.library_management.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Fixtures - what to export from database to code
fixtures = [
    {
        "dt": "Role",
        "filters": [
            ["name", "in", ["Librarian", "Library Member"]]
        ]
    },
    {
        "dt": "Module Def",
        "filters": [
            ["module_name", "=", "library_management"]
        ]
    },
    {
        "dt": "Web Page",
        "filters": [
            ["name", "in", ["home", "signup", "login", "articles-page", "article-detail", "membership", "my-articles"]]
        ]
    },
    {
        "dt": "DocType",
        "filters": [
            ["module", "=", "library_management"]
        ]
    },
    {
        "dt": "Web Template",
        "filters": [
            ["module", "=", "library_management"]
        ]
    }
]