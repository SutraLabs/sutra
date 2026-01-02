from __future__ import annotations

from sutra import Agent

DEFAULT_MODEL = "llama3.1:latest"
MODEL_HINT = (
    "Sutra runs with the Ollama model 'llama3.1:latest'. "
    "Install it with `ollama pull llama3.1:latest` when needed."
)

GREET_PROMPT = MODEL_HINT + '''
Input: {text}

Return JSON with "reply" and "tone".
Example: {"reply": "Hello!", "tone": "friendly"}
'''

SUMMARY_PROMPT = MODEL_HINT + '''
Original text: {text}
Reply: {greeting}

Return JSON with "summary" and "next_step".
'''

greeting_agent = Agent(
    name="greeting",
    objective="Generate a friendly reply that references the input text.",
    model=DEFAULT_MODEL,
    prompt=GREET_PROMPT,
    expects_json=True,
    required_keys=["reply", "tone"],
    output_key="greeting",
    temperature=0.0,
)

summary_agent = Agent(
    name="summary",
    objective="Summarize the request and the greeting for a follow-up.",
    model=DEFAULT_MODEL,
    prompt=SUMMARY_PROMPT,
    expects_json=True,
    required_keys=["summary", "next_step"],
    output_key="summary",
    temperature=0.3,
)

__all__ = ["greeting_agent", "summary_agent", "DEFAULT_MODEL", "MODEL_HINT"]
