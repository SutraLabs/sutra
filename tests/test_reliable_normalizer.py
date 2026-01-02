from __future__ import annotations

from types import SimpleNamespace

from sutra.core import Pipeline, Step, _resolve_normalizer, _run_pipeline_with_work_item
from sutra.input import coerce_work_item


class DummyAgent:
    def __init__(self, name, output_key, fn):
        self.name = name
        self.output_key = output_key
        self._fn = fn

    def run(self, inputs):
        return {self.output_key: self._fn(inputs)}


def test_normalizer_pre_step_runs_before_pipeline():
    def normalize(inputs):
        wi = inputs["work_item"]
        return {
            "record_type": "ticket",
            "identifiers": {"primary": wi["id"], "secondary": []},
            "summary": wi["text"],
            "entities": [{"type": "user", "value": "Jane Doe"}],
            "extracted_fields": {"channel": wi["fields"].get("channel", "text")},
        }

    normalizer_step = Step(DummyAgent("normalizer", "normalized", normalize))
    module = SimpleNamespace(NORMALIZER_STEP=normalizer_step)
    resolved = _resolve_normalizer(module)
    assert resolved is normalizer_step

    def copy_normalized(inputs):
        return inputs.get("normalized")

    pipeline = Pipeline([Step(DummyAgent("collector", "final", copy_normalized))])
    work_item = coerce_work_item({"text": "Ticket #10 via email", "fields": {"channel": "email"}})

    result = _run_pipeline_with_work_item(pipeline, work_item, normalizer_step=resolved)

    assert result["normalized"]["record_type"] == "ticket"
    assert result["final"]["summary"] == "Ticket #10 via email"
    assert result["final"]["extracted_fields"]["channel"] == "email"
