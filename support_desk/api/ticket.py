"""
Ticket creation API for portal users (Website Users).

Frappe's @whitelist() blocks Website Users from calling non-guest methods.
This wrapper uses allow_guest=True but validates the session internally.
"""

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def create_ticket(subject: str, description: str, ticket_type: str = "Support", raised_by: str = ""):
    """Create a new HD Ticket. Requires authenticated session."""
    if frappe.session.user == "Guest":
        frappe.throw(_("Please log in to create a ticket"), frappe.AuthenticationError)

    doc = frappe.get_doc({
        "doctype": "HD Ticket",
        "subject": subject,
        "description": description,
        "ticket_type": ticket_type,
        "raised_by": raised_by or frappe.session.user,
        "via_customer_portal": 1,
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    return doc.as_dict()
