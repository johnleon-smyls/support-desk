"""
AI-powered ticket thread summarization.

Generates a concise summary of a long ticket conversation,
useful for agents picking up a ticket they didn't start.
"""

import frappe
from frappe.utils import strip_html
from support_desk.ai.client import call_claude


SYSTEM_PROMPT = """Summarize this support ticket conversation in 2-4 bullet points. Focus on:
- What the customer's issue is
- What has been tried or discussed
- Current status and next steps needed

Be concise. Use plain text, no HTML. Start each bullet with "- "."""


def summarize_ticket(ticket_name: str) -> str:
    """Generate a summary of the ticket conversation."""
    ticket = frappe.get_doc("HD Ticket", ticket_name)

    from helpdesk.helpdesk.doctype.hd_ticket.api import get_communications
    communications = get_communications(ticket_name)

    conversation = []
    for comm in communications:
        sender = comm.get("sender", "Unknown")
        content = strip_html(comm.get("content", ""))[:500]
        conversation.append(f"{sender}: {content}")

    prompt = f"""Subject: {ticket.subject}
Priority: {ticket.priority}
Status: {ticket.status}

Description:
{strip_html(ticket.description or '')[:1000]}

Conversation ({len(communications)} messages):
{chr(10).join(conversation[-10:])}"""

    try:
        return call_claude(prompt, system=SYSTEM_PROMPT, max_tokens=512)
    except Exception as e:
        frappe.log_error(f"AI summarization failed: {e}", "Support Desk AI")
        return "Summary unavailable."
