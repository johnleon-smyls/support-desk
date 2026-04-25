"""
AI API endpoints for the Support Portal.

All endpoints require authentication. suggest_reply and summarize_ticket
are agent-only.
"""

import frappe
from helpdesk.utils import is_agent


@frappe.whitelist()
def categorize(subject: str, description: str = ""):
    """
    Suggest ticket type and priority for a new ticket.
    Available to all authenticated users (called during ticket creation).
    """
    from support_desk.ai.categorize import categorize_ticket
    return categorize_ticket(subject, description)


@frappe.whitelist()
def suggest_reply(ticket_name: str):
    """
    Generate reply suggestions for an agent.
    Agent-only — returns 2-3 draft replies.
    """
    if not is_agent():
        frappe.throw("Only agents can use AI suggestions", frappe.PermissionError)

    from support_desk.ai.suggest_reply import suggest_replies
    return suggest_replies(ticket_name)


@frappe.whitelist()
def summarize(ticket_name: str):
    """
    Summarize a ticket conversation.
    Agent-only — returns a concise bullet-point summary.
    """
    if not is_agent():
        frappe.throw("Only agents can use AI summaries", frappe.PermissionError)

    from support_desk.ai.summarize import summarize_ticket
    return summarize_ticket(ticket_name)
