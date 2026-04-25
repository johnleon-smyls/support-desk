"""
AI-powered reply suggestions for agents.

Generates 2-3 draft replies based on the ticket context and
conversation history. Agents can click to populate the editor,
then edit before sending.
"""

import frappe
from frappe.utils import strip_html
from support_desk.ai.client import call_claude


SYSTEM_PROMPT = """You are a senior support agent for SMYLS, a B2B SaaS platform for Canadian healthcare/dental clinics. Your tone is professional, warm, and solution-oriented.

Given a support ticket with its conversation history, generate 2-3 suggested reply drafts that the agent can use or adapt. Each reply should:
- Acknowledge the customer's issue
- Provide a clear next step or resolution
- Be ready to send as-is (complete, not a template with blanks)

Return a JSON array of objects, each with:
- "label": a 3-5 word summary (e.g., "Request more details", "Provide solution", "Escalate to engineering")
- "content": the full HTML reply (use <p> tags, keep it concise)

Return ONLY valid JSON, no markdown fencing."""


def suggest_replies(ticket_name: str) -> list[dict]:
    """Generate reply suggestions for a ticket."""
    ticket = frappe.get_doc("HD Ticket", ticket_name)

    # Build conversation context
    from helpdesk.helpdesk.doctype.hd_ticket.api import get_communications
    communications = get_communications(ticket_name)

    conversation = []
    for comm in communications:
        sender = comm.get("sender", "Unknown")
        content = strip_html(comm.get("content", ""))[:500]
        conversation.append(f"{sender}: {content}")

    conversation_text = "\n\n".join(conversation[-6:])  # Last 6 messages max

    prompt = f"""Ticket #{ticket.name}
Subject: {ticket.subject}
Status: {ticket.status}
Priority: {ticket.priority}
Customer: {ticket.customer or 'Unknown'}
Raised by: {ticket.raised_by}

Description:
{strip_html(ticket.description or '')[:1000]}

Conversation history:
{conversation_text or 'No replies yet.'}"""

    try:
        response = call_claude(prompt, system=SYSTEM_PROMPT, max_tokens=1024)
        import json
        suggestions = json.loads(response)

        if not isinstance(suggestions, list):
            return []

        # Validate and limit
        return [
            {"label": s.get("label", "Suggestion"), "content": s.get("content", "")}
            for s in suggestions[:3]
            if s.get("content")
        ]
    except Exception as e:
        frappe.log_error(f"AI reply suggestion failed: {e}", "Support Desk AI")
        return []
