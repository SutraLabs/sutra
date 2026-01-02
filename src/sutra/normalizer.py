"""Built-in helper for creating a normalization agent."""
from __future__ import annotations

from typing import Any, Dict, List, TypedDict

from .core import Agent


class IdentifierBlock(TypedDict):
    primary: str | None
    secondary: List[str]


class EntityBlock(TypedDict):
    type: str
    value: str


class NormalizedItem(TypedDict):
    record_type: str
    identifiers: IdentifierBlock
    summary: str
    entities: List[EntityBlock]
    extracted_fields: Dict[str, Any]


NORMALIZED_REQUIRED_KEYS = ["record_type", "identifiers", "summary", "entities", "extracted_fields"]

NORMALIZER_PROMPT = """You are the Sutra Normalizer.

Goal: convert heterogeneous WorkItem inputs into a predictable NormalizedItem JSON.

WorkItem schema:
- id: string | null
- type: string | null
- text: string (may include markdown or structured content)
- fields: object (pre-parsed metadata)
- attachments: [string]
- meta: object (raw + extra hints)

NormalizedItem schema (ALWAYS output valid JSON):
{
  "record_type": string,            # e.g., "ticket", "kyc_case", "invoice", "other"
  "identifiers": {
    "primary": string | null,
    "secondary": [string]
  },
  "summary": string,                # concise 1-2 sentence summary
  "entities": [
    {"type": string, "value": string}
  ],
  "extracted_fields": object        # machine-friendly key/value pairs inferred from text/fields
}

Instructions:
- Prefer data from WorkItem.fields when present.
- Always set identifiers.secondary (can be empty list).
- Entities should highlight important persons, companies, locations, or account numbers.
- extracted_fields should include canonical facts (dates, amounts, statuses, etc.).
- If information is missing, use null/empty strings but keep schema intact.

Return ONLY the JSON object."""


def create_normalizer_agent(model: str = "llama3.1:latest", *, name: str = "normalizer") -> Agent:
    """Return a ready-to-use normalizer Agent."""
    return Agent(
        name=name,
        objective="Normalize WorkItem inputs into canonical NormalizedItem payloads.",
        model=model,
        prompt=NORMALIZER_PROMPT,
        expects_json=True,
        output_key="normalized",
        required_keys=NORMALIZED_REQUIRED_KEYS,
        retries=2,
        temperature=0.0,
    )


__all__ = [
    "IdentifierBlock",
    "EntityBlock",
    "NormalizedItem",
    "NORMALIZER_PROMPT",
    "NORMALIZED_REQUIRED_KEYS",
    "create_normalizer_agent",
]
