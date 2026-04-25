"""
User invitation system for Support Portal.

Allows admins to invite clinic staff to the portal. Creates a disabled user,
sends an invite email with a token link, and activates the account when accepted.
"""

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def validate_invite_token(key: str):
    """Validate an invite token and return the associated user info."""
    if not key:
        return {"valid": False, "error": "No invite key provided"}

    user = frappe.db.get_value(
        "User",
        {"reset_password_key": key, "enabled": 0},
        ["name", "email", "first_name", "last_name"],
        as_dict=True,
    )

    if not user:
        return {"valid": False, "error": "Invalid or expired invite link"}

    return {
        "valid": True,
        "email": user.email,
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
    }


@frappe.whitelist(allow_guest=True)
def accept_invite(key: str, password: str, first_name: str, last_name: str = ""):
    """Accept an invitation by setting password and enabling the user."""
    if not key or not password:
        frappe.throw(_("Missing required fields"), frappe.ValidationError)

    user_email = frappe.db.get_value(
        "User",
        {"reset_password_key": key, "enabled": 0},
        "name",
    )

    if not user_email:
        frappe.throw(_("Invalid or expired invite link"), frappe.ValidationError)

    user = frappe.get_doc("User", user_email)
    user.first_name = first_name
    user.last_name = last_name
    user.enabled = 1
    user.reset_password_key = None
    user.new_password = password
    user.save(ignore_permissions=True)

    frappe.db.commit()

    return {"success": True, "email": user.email}


@frappe.whitelist()
def invite_user(email: str, first_name: str, last_name: str = "", customer: str = ""):
    """
    Invite a new user to the portal.
    Creates a disabled user, assigns portal role, links to HD Customer,
    and sends an invite email.

    Must be called by an agent or admin.
    """
    from helpdesk.utils import is_agent

    if not is_agent():
        frappe.throw(_("Only agents can invite users"), frappe.PermissionError)

    if frappe.db.exists("User", email):
        frappe.throw(_("User {0} already exists").format(email), frappe.DuplicateEntryError)

    # Create disabled user
    user = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "enabled": 0,
        "user_type": "Website User",
        "send_welcome_email": 0,
    })
    user.insert(ignore_permissions=True)

    # Generate invite token
    from frappe.utils import random_string
    key = random_string(32)
    user.reset_password_key = key
    user.save(ignore_permissions=True)

    # Create Contact and link to HD Customer if provided
    if customer:
        contact = frappe.get_doc({
            "doctype": "Contact",
            "first_name": first_name,
            "last_name": last_name,
            "email_id": email,
            "email_ids": [{"email_id": email, "is_primary": 1}],
            "links": [{"link_doctype": "HD Customer", "link_name": customer}],
        })
        contact.insert(ignore_permissions=True)

    # Send invite email
    site_url = frappe.utils.get_url()
    # Portal runs on a different port — use PORTAL_URL if configured
    portal_url = frappe.db.get_single_value("HD Settings", "portal_url") or site_url
    invite_link = f"{portal_url}/accept-invite?key={key}"

    frappe.sendmail(
        recipients=[email],
        subject=f"You've been invited to SMYLS Support Portal",
        message=f"""
        <p>Hi {first_name},</p>
        <p>You've been invited to the SMYLS Support Portal. Click the link below to set your password and activate your account:</p>
        <p><a href="{invite_link}">{invite_link}</a></p>
        <p>This link will expire after use.</p>
        """,
    )

    frappe.db.commit()

    return {"success": True, "email": email, "invite_link": invite_link}
