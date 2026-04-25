"""
Helpdesk API overrides for Support Portal.

Hides priority from customer portal views. Agents still see priority
in the Desk and admin portal.
"""

import frappe
from helpdesk.api.doc import get_list_data as _get_list_data
from helpdesk.utils import is_agent


@frappe.whitelist()
def get_list_data(
    doctype: str,
    filters: dict = {},
    default_filters: dict = {},
    order_by: str = "modified desc",
    page_length: int = 20,
    columns: list = [],
    rows: list = [],
    show_customer_portal_fields: bool = False,
    view: dict | None = None,
    is_default: bool = False,
):
    """Wrapper around Helpdesk's get_list_data that strips priority for non-agents."""
    result = _get_list_data(
        doctype=doctype,
        filters=filters,
        default_filters=default_filters,
        order_by=order_by,
        page_length=page_length,
        columns=columns,
        rows=rows,
        show_customer_portal_fields=show_customer_portal_fields,
        view=view,
        is_default=is_default,
    )

    # Only strip priority for non-agent users viewing the customer portal
    if not is_agent() and show_customer_portal_fields:
        # Remove priority from columns
        if isinstance(result, dict) and "columns" in result:
            result["columns"] = [
                col for col in result["columns"]
                if col.get("key") != "priority" and col.get("value") != "priority"
            ]

        # Remove priority values from rows
        if isinstance(result, dict) and "rows" in result:
            for row in result["rows"]:
                row.pop("priority", None)

    return result
