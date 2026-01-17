## Sutra

Sutra is a small framework for running sequential LLM pipelines locally.
This project is not affiliated with, endorsed by, or associated with any company or product named Sutra or Sutra AI.

Learn agentic AI on your laptop

Sutra is a local-first agentic AI playground for learning and tinkering — not a production framework.

   ❌ No cloud APIs
   💸 No costs
   🧱 No framework bloat
   🐍 Just Python + Ollama
   🛠 Build small, actually useful tools

If LangChain feels heavy and AutoGen feels overengineered, Sutra is for you.


## DISCLAIMER
Sutra is not trying to replace LangChain or AutoGen.
It’s a learning tool and side-agent sandbox for understanding agentic AI without the fuss.


## Install
```bash
pip install sutra-ai
```

## Quick start
1. Create a demo project (menu lets you pick Hello World, support triage, or the interactive wizard):
   ```bash
   sutra create demo "Support ticket helper" --yes
   ```
2. Run the generated pipeline with a short question:
   ```bash
   sutra run projects/demo/pipeline.py --text "My internet is down"
   ```
3. Verify everything still works by running the doctor self-test:
   ```bash
   sutra doctor --selftest
   ```

You can also open the demo pipeline directly with Python:
```bash
python projects/demo/pipeline.py --text "My internet is down"
```

After `sutra create` you will see guidance such as "What happens next?" and reminders like `ollama pull <model>` if the model is missing.

For formal docs and release notes, visit the GitHub repo or PyPI page:
```bash
echo https://github.com/SutraLabs/sutra
echo https://pypi.org/project/sutra-ai/
```

## Example output
The demo pipeline writes an `answer` entry:
```json
{
  "answer": [{"answer": "Thanks for the question."}]
}
```

## Concepts
- **Agent**: one actor (model + prompt) that enforces `expects_json` and `required_keys`.
- **Step**: runs an agent and feeds its outputs to the next step.
- **Pipeline**: a list of steps wired together; it always exposes `build()` and `DEFAULT_INPUT`.

## Recommended Envinroment
1. Install Ollama before-hand
2. Download model of your choice
3. Create a virtual Python environment

## Commands (Quick Start)
- `sutra create <name> <description>`: menu lets you pick Hello World, support triage, or the input wizard.
- `sutra run <pipeline.py> --text "Hey!"` (or `sutra run <pipeline.py> "Hey!"`): feeds text to the first agent.
- `sutra --version`: prints the installed `sutra-ai` version.
- `sutra doctor [--selftest]`: checks Ollama connectivity; `--selftest` also tries to import and run a generated pipeline.
- `sutra help`: shows the CLI usage and the names of supported commands.

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
- GitHub: https://github.com/SutraLabs/sutra
- Issues: https://github.com/SutraLabs/sutra/issues
- Changelog: https://github.com/SutraLabs/sutra/blob/main/CHANGELOG.md
- PyPI: https://pypi.org/project/sutra-ai/0.1.0/
