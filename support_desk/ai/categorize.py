"""
AI-powered ticket categorization.

Suggests ticket type and priority based on subject and description.
Called during ticket creation to pre-fill fields.
"""

import json
import frappe
from support_desk.ai.client import call_claude


SYSTEM_PROMPT = """You are a helpdesk triage assistant for SMYLS, a B2B SaaS platform for Canadian healthcare/dental clinics.

Given a support ticket's subject and description, classify it and return a JSON object with:

1. "ticket_type": one of ["Bug", "Question", "Feature Request", "Account", "Billing", "Other"]
2. "priority": one of ["Low", "Medium", "High", "Urgent"]
   - Low: general questions, feature requests, non-blocking issues
   - Medium: issues affecting workflow but with workarounds
   - High: issues blocking key functionality for a clinic
   - Urgent: data loss, security issues, or complete system outage
3. "confidence": a number 0-1 indicating how confident you are
4. "reasoning": one sentence explaining why

Return ONLY valid JSON, no markdown fencing."""


def categorize_ticket(subject: str, description: str) -> dict:
    """Classify a ticket and return suggested type + priority."""
    # Strip HTML from description
    from frappe.utils import strip_html
    clean_desc = strip_html(description or "")

    prompt = f"Subject: {subject}\n\nDescription: {clean_desc[:2000]}"

    try:
        response = call_claude(prompt, system=SYSTEM_PROMPT, max_tokens=256)
        result = json.loads(response)

        # Validate fields
        valid_types = ["Bug", "Question", "Feature Request", "Account", "Billing", "Other"]
        valid_priorities = ["Low", "Medium", "High", "Urgent"]

        if result.get("ticket_type") not in valid_types:
            result["ticket_type"] = "Other"
        if result.get("priority") not in valid_priorities:
            result["priority"] = "Medium"

        return result
    except (json.JSONDecodeError, Exception) as e:
        frappe.log_error(f"AI categorization failed: {e}", "Support Desk AI")
        return {
            "ticket_type": "Other",
            "priority": "Medium",
            "confidence": 0,
            "reasoning": "AI categorization unavailable",
        }
