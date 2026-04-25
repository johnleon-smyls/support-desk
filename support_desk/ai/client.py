"""
Shared Claude API client for AI features.

Reads the API key from Frappe site config:
  bench set-config anthropic_api_key sk-ant-...
"""

import frappe

_client = None


def get_client():
    """Lazy-initialize the Anthropic client."""
    global _client
    if _client is None:
        try:
            import anthropic
        except ImportError:
            frappe.throw(
                "anthropic package not installed. Run: pip install anthropic",
                frappe.ValidationError,
            )

        api_key = frappe.conf.get("anthropic_api_key")
        if not api_key:
            frappe.throw(
                "Anthropic API key not configured. Run: bench set-config anthropic_api_key <key>",
                frappe.ValidationError,
            )

        _client = anthropic.Anthropic(api_key=api_key)

    return _client


def call_claude(
    prompt: str,
    system: str = "",
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> str:
    """Send a prompt to Claude and return the text response."""
    client = get_client()
    messages = [{"role": "user", "content": prompt}]

    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system

    response = client.messages.create(**kwargs)
    return response.content[0].text
