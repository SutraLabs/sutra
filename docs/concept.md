# Sutra Concept

Sutra is a **local-first, sequential agent workflow framework** designed for building deterministic AI pipelines you can inspect and debug on your own machine. Instead of graph-based orchestration, Sutra exposes a few primitives written in plain Python:

- `Agent`: wraps a prompt-driven Ollama model call (or any `run`-compatible object) with schema validation, retries, and optional system hints.
- `Step`: binds an `Agent` to a list of input keys; it selects the appropriate slice of the pipeline state and merges outputs back into the shared context.
- `Pipeline`: runs a list of `Step` objects while tracing inputs/outputs (via `Trace`) and optionally prepends a normalization step.
- `WorkItem`: represents every request as `{text, fields, attachments, meta}` so agents can rely on consistent payload structures.

Agents can declare `required_keys` and `expects_json=True` so Sutra can coerce and validate nested JSON output. When you run `sutra run my_pipeline.py`, Sutra:

1. Loads the pipeline module and optional `NORMALIZER`.
2. Coerces CLI inputs (`--text`, `--input`, JSONL, or `DEFAULT_INPUT`) into `WorkItem`s.
3. Executes the pipeline step-by-step, writing traces to `.sutra/runs/<run_id>/`.
4. Dumps the results to `.sutra/outputs/<run_id>.jsonl` or prints single-item runs in the console.

`cmd_doctor` verifies Ollama reachability, and `cmd_ui` boots the FastAPI UI that lists pipelines, run history, and lets you edit prompt code in-place.
