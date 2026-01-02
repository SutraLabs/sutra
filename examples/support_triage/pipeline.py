from __future__ import annotations

import json

from sutra import Pipeline, Step

import agents

DEFAULT_INPUT = {
    "id": "triage-2024",
    "type": "support_ticket",
    "text": "User cannot access account after resetting password; priority is high.",
    "fields": {"channel": "email", "product": "dashboard"},
    "attachments": [],
    "meta": {"source": "examples/support_triage"},
}


def build() -> Pipeline:
    steps = [
        Step(agents.classification_agent, takes=["text"]),
        Step(agents.replier_agent, takes=["text", "classification"]),
        Step(agents.summary_agent, takes=["text", "classification", "replier"]),
    ]
    return Pipeline(steps)


def _run_default() -> None:
    pipeline = build()
    result = pipeline.run(DEFAULT_INPUT)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _run_default()
