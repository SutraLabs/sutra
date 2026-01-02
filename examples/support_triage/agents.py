from __future__ import annotations

from sutra import Agent

DEFAULT_MODEL = "llama3.1:latest"
MODEL_HINT = (
    "Use the Ollama model 'llama3.1:latest'. "
    "Install it with `ollama pull llama3.1:latest` if missing."
)

classification_agent = Agent(
    name="classification",
    objective="Tag support tickets with category and urgency.",
    model=DEFAULT_MODEL,
    prompt=MODEL_HINT + '''
Ticket text: {text}

Return JSON with "category" and "urgency" (low/medium/high).
Example: {"category": "bug", "urgency": "high"}
''',
    expects_json=True,
    required_keys=["category", "urgency"],
    output_key="classification",
    temperature=0.1,
)

replier_agent = Agent(
    name="replier",
    objective="Draft a short support reply referencing category and urgency.",
    model=DEFAULT_MODEL,
    prompt=MODEL_HINT + '''
Ticket: {text}
Classification: {classification}

Return JSON with "reply" and "tone".
''',
    expects_json=True,
    required_keys=["reply", "tone"],
    output_key="replier",
    temperature=0.1,
)

summary_agent = Agent(
    name="summary",
    objective="Summarize the ticket plus reply for status updates.",
    model=DEFAULT_MODEL,
    prompt=MODEL_HINT + '''
Ticket: {text}
Classification: {classification}
Reply: {replier}

Return JSON with "summary", "next_steps", and "status".
''',
    expects_json=True,
    required_keys=["summary", "next_steps", "status"],
    output_key="summary",
    temperature=0.0,
)

__all__ = [
    "classification_agent",
    "replier_agent",
    "summary_agent",
    "DEFAULT_MODEL",
    "MODEL_HINT",
]
