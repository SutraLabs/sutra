from __future__ import annotations

import json

from sutra import Pipeline, Step

import agents

DEFAULT_INPUT = {
    "id": "hello-001",
    "type": "example",
    "text": "Hello, Sutra. Show me how you summarize a short request.",
    "fields": {},
    "attachments": [],
    "meta": {"source": "examples"},
}


def build() -> Pipeline:
    steps = [
        Step(agents.greeting_agent, takes=["text"]),
        Step(agents.summary_agent, takes=["text", "greeting"]),
    ]
    return Pipeline(steps)


def _run_default() -> None:
    pipeline = build()
    result = pipeline.run(DEFAULT_INPUT)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _run_default()
