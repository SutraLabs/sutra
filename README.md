**SutraAI** 
Local-first agent workflow framework for hackable, reliable multi-agent pipelines.

Build, run, and debug AI agent pipelines entirely on your machine. No API keys, no cloud, no bloat.

SutraAI is a lightweight, open-source framework for orchestrating AI agent pipelines. Designed for developers who want control, hackability, and offline execution, SutraAI lets you sequence small-to-mid-sized language models (2B–7B) with a simple, Python-based workflow. Think of it as the anti-bloat alternative to heavy frameworks like LangChain or CrewAI—built for intermediates who value clarity and flexibility.

**Features**

Multi-Agent Pipelines – Define clear, sequential agent workflows using simple Python files, no complex graph abstractions.
Local-First Execution – Runs entirely offline using Ollama or similar local model servers. No cloud dependency, no API keys.
Hackable Core – Agents are just Python scripts with editable prompts, making customization a breeze.
CLI & Templates – Generate working pipelines in seconds with commands like sutra create study-helper.
Reliable Orchestration – Built-in retries, JSON schema validation, and error recovery for robust execution.


**Quickstart**
Get up and running in minutes:
# Clone the repository
git clone https://github.com/yourusername/sutra
cd sutra

# Install dependencies
- `pip install -r requirements.txt` (developer quickstart; installs sutra-ai with UI/PDF/RAG extras plus `pytest`)
- `pip install -e .` (editable install for ongoing work; exposes the `sutra` CLI)
- `pip install "sutra-ai[ui,pdf,rag]"` to grab the extras from PyPI if you don’t need the editable install

If `ollama list` shows no models, install the configured default (`llama3.1:latest` by default) with `ollama pull <model>`. `sutra create` and the README warnings explain that the CLI falls back to that model and you can rerun once a model is available.

Before running `sutra create`, verify `ollama list` (or `curl http://localhost:11434/api/tags`). The CLI reminds you when the default model is being used because Ollama could not report any models.

# Run a sample pipeline (no Ollama required)
python3 sutra.py test examples/echo_pipeline.py

Or run with explicit input:
python3 sutra.py run examples/echo_pipeline.py --input '{"text":"Ticket #12847: App crashes on photo upload after update 2.3.1"}'

When running your own pipelines use:
```
sutra create demo "Support triage assistant"
sutra run projects/demo/pipeline.py --text "My support request"
sutra run projects/demo/pipeline.py "My support request"  # shorthand positional alias
```

**Install + CLI smoke**

- Run `pip install -e .` from the repo root to install the package and expose the `sutra` CLI (optionally combine with the above dependency installs).
- Confirm the CLI is wired: `sutra --help`.
- Scaffold a demo project: `sutra create demo "Support triage assistant"`.
- Run it: `sutra run projects/demo/pipeline.py --text "Need login access reset"`.
- Check the outputs under `.sutra/runs/<latest>/` and `.sutra/outputs/<latest>.jsonl`.

**How to run a pipeline**

- Each pipeline should expose a `build()` function and optionally `DEFAULT_INPUT` so `sutra test <pipeline>` works without extra arguments.
- To run with custom text, pass `--text`:  
  `sutra run projects/testchat_v1/testchat_v1_pipeline.py --text "What is Agentic AI?"`
- To source structured work items, point `--input` at a JSON/JSONL file (`--input work.jsonl`).
- For larger batches use `--output <path>` so results write to your own JSONL and you can inspect `.sutra/runs/<run_id>/` for traces.
- Add `--reliable` when your pipeline exports `NORMALIZER` or `NORMALIZER_STEP` so Sutra preprocesses inputs before agents run.

If a project has additional helpers (tools, attachments, metadata), include those fields in `DEFAULT_INPUT` and mention them in the pipeline docstring so fellow contributors know how to grade the inputs.

**Example Output (from `examples/echo_pipeline.py`):**
{
  "text": "Ticket #12847: App crashes on photo upload after update 2.3.1",
  "analyzer": [
    {
      "summary": "Ticket #12847: App crashes on photo upload after update 2.3.1",
      "category": "Bug Report",
      "root_cause": "Crash on photo upload"
    }
  ],
  "classifier": [
    {
      "priority": "High",
      "team": "mobile",
      "ticket_type": "bug"
    }
  ],
  "replier": {
    "reply": "Thanks for the report. We've identified the issue and our mobile team is on it.",
    "tone": "calm"
  }
}


**Testing**

- `pytest tests` runs the input coercion utilities, tools, and a minimal smoke test to cover Sutra’s package exports.


**Status**

Status: Alpha | Experimental

**Why SutraAI? Why one more framework?**
SutraAI is built for developers who want to avoid the complexity and overhead of bloated frameworks. Here’s how it stacks up:

Local Execution
✅ Fully offline (Ollama)

Ease of Hacking
✅ Plain Python scripts

Lightweight
✅ <100 KB core

Pipeline Clarity
✅ Sequential, explicit

Setup Time
✅ Seconds (CLI templates)


SutraAI is the framework for those who want to build fast, debug easily, and stay in control.

**Roadmap**

 CLI generator (sutra create <name> "<task>") for instant pipeline creation
 DAG executor for parallel branches and joins
 Observability with OpenTelemetry spans and JSONL logs
 Template library (e.g., resume-helper, ticket-triage, invoice-extract)
 Web UI for run history, input/output visualization, and replays


**Project Structure**

sutra/
├── sutra.py               # CLI entry point & packaged CLI shim
├── examples/              # Ready-to-run pipelines (echo, PDF, RAG demos)
├── projects/              # Generator scaffolds for agent suites
├── docs/                  # Documentation (concept/comparisons/examples)
├── src/                   # Package implementation
├── tests/                 # Pytest suite (input coercion, tools, smoke)
├── requirements.txt       # Quickstart bundle (installs sutra-ai extras + pytest)
├── pyproject.toml         # Packaging metadata
├── CHANGELOG.md
└── README.md


**Documentation**

- [`docs/concept.md`](docs/concept.md) – Core ideas about agents, steps, pipelines, tracing, and normalization.
- [`docs/comparisons.md`](docs/comparisons.md) – How SutraAI differs from other frameworks such as LangChain or CrewAI.
- [`docs/examples.md`](docs/examples.md) – Notes on the ready-to-run pipelines and recommended starting points for new workflows.


**Demo**

Check out a short demo video on X or YouTube. - Upcoming

**Contributing**
We welcome contributions! Check out our Issues for bugs, features, or new pipeline ideas. Use our Discussions to share templates or ask questions.
To get started:

**Fork the repo**
Create a branch (git checkout -b feature/awesome-agent)
Commit changes (git commit -m "Add awesome agent")
Push and open a PR


License
MIT License – see LICENSE for details.

Try SutraAI Today!
SutraAI is the fastest way to build and debug local AI agent pipelines. Clone the repo, try the examples, and let us know what you think in Discussions!
