# Sutra Compared

Compared to frameworks like **LangChain** or **CrewAI**, Sutra keeps the execution model deliberately simple:

- **Local-first** – Sutra talks to Ollama or any HTTP-based LLM server you run locally; there are no cloud API keys or hosted plans.
- **Sequential pipelines** – Instead of building DAGs, you define a clear list of `Step` objects. Dependencies are explicit through the `takes` argument, keeping data flow easy to follow.
- **Minimal core** – The package core is <100 KB and uses standard Python modules (no exotic graph DSLs). Agents are just prompt templates in Python files.
- **Observability-ready** – Every run produces JSON traces and outputs under `.sutra/`, which makes debugging deterministic step-by-step.
- **Offline tooling** – Sutra ships with local RAG helpers (`rag.index_folder`, `rag.query`), PDF/text chunkers, and a FastAPI UI instead of relying on remote services.

LangChain and CrewAI are broader in scope, but Sutra carves out the niche of hackable pipelines where you control each prompt, run trace, and dependency.
