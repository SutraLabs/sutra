**Sutra**

Sutra is a small framework for running sequential LLM pipelines locally.
This project is not affiliated with, endorsed by, or associated with any company or product named Sutra or Sutra AI.

## Install
```bash
pip install sutra-ai
```

## Examples
### Hello world
```bash
pip install -e .
sutra run examples/hello_world/pipeline.py --text "Hello example"
```

### Support triage
```bash
pip install -e .
sutra run examples/support_triage/pipeline.py --text "Need help with the dashboard"
sutra run examples/support_triage/pipeline.py --input examples/support_triage/sample_input.json
```

```json
{
  "classification": [{"category": "bug", "urgency": "high"}],
  "replier": {"reply": "Team notified, working on it.", "tone": "calm"},
  "summary": {"summary": "Dashboard error blocking invoices", "next_steps": "Network to confirm deployment", "status": "pending"}
}
```

## Commands
- `sutra create <name> <description>` (writes to `projects/<name>`; `projects/` is a working directory and not tracked in this repo)
- `sutra run <pipeline.py> [--text TEXT | \"TEXT\"]`
- `sutra doctor`

## Requirements
- Python >=3.10
- Ollama server at http://localhost:11434
- Model requirement: `ollama pull llama3.1:latest`

## What Sutra is / is not
- Is: a CLI-driven pipeline runner that enforces JSON contracts.
- Is: a local workflow for orchestrating Ollama-powered agents.
- Is not: an autonomous planner with self-directed agents.
- Is not: a hosted API service.

## Links
- GitHub: https://github.com/rajat4493/SutraFramework
- Issues: https://github.com/rajat4493/SutraFramework/issues
- Changelog: https://github.com/rajat4493/SutraFramework/blob/main/CHANGELOG.md
- PyPI: https://pypi.org/project/sutra-ai/0.1.0/
