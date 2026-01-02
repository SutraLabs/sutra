# Sutra Examples

These files live under `examples/` and `projects/` and are the ones referenced by the CLI/UI.

## `examples/echo_pipeline.py`
Minimal mock agents (`analyzer`, `classifier`, `replier`) show how Sutra wires `Step` objects cleanly without requiring Ollama. Use `sutra test examples/echo_pipeline.py` to ensure the CLI works before you point to real agents.

## `examples/pdf_extract_pipeline.py`
Demonstrates calling the built-in `pdf.extract_text` tool via `sutra.tools.executor.execute_tool`. Swap the hard-coded `pdf_path` for an actual document to see how tool envelopes propagate through pipeline outputs.

## `examples/rag_pdf_qa.py`
Runs `rag.index_folder` to build embeddings (requires `numpy`, `sentence-transformers`, `reportlab`) and then issues a `rag.query`. This shows how Sutra can coordinate tooling + retrieval prior to an LLM reply.

## `projects/`
The generator (`sutra create <name> "<task>"`) scaffolds agents + pipelines inside `projects/<name>/`. Use it to bootstrap workflows such as ticket triage or study helpers.

## UI surfaces
The FastAPI UI (`sutra.ui.server`) discovers `_pipeline.py` modules under `examples/` and `projects/`, shows run history from `.sutra/runs/`, and lets you edit prompt files and execute pipelines directly from the browser.
