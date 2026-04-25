"""
File upload API for portal users (Website Users).

Frappe's upload_file checks File doctype create permission which
Website Users don't have. This wrapper handles the upload with
ignore_permissions and validates the session.
"""

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def upload_recording():
    """Upload a file from the portal. Requires authenticated session."""
    if frappe.session.user == "Guest":
        frappe.throw(_("Please log in to upload files"), frappe.AuthenticationError)

    files = frappe.request.files
    if "file" not in files:
        frappe.throw(_("No file provided"), frappe.ValidationError)

    uploaded_file = files["file"]
    is_private = frappe.form_dict.get("is_private", "1")
    doctype = frappe.form_dict.get("doctype")
    docname = frappe.form_dict.get("docname")

    # Save the file
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": uploaded_file.filename,
        "is_private": int(is_private),
        "content": uploaded_file.read(),
        "attached_to_doctype": doctype,
        "attached_to_name": docname,
    })
    file_doc.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "name": file_doc.name,
        "file_name": file_doc.file_name,
        "file_url": file_doc.file_url,
        "file_size": file_doc.file_size,
    }
