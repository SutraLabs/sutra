"""CLI regression coverage for Sutra."""

from __future__ import annotations
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def _env_for(tmp_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    prefix = str(SRC)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = f"{prefix}{os.pathsep}{existing}" if existing else prefix
    env["SUTRA_APP_DIR"] = str(tmp_path / ".sutra")
    env["SUTRA_MOCK_OLLAMA"] = "1"
    return env


def _run_sutra(args: list[str], cwd: Path, stdin: str | None = None):
    script = (
        "import sys\n"
        "from sutra.cli import main\n"
        f"sys.argv = ['sutra'] + {args!r}\n"
        "main()\n"
    )
    cmd = [sys.executable, "-c", script]
    env = _env_for(cwd)
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, input=stdin)


def _create_demo_project(tmp_path: Path) -> Path:
    result = _run_sutra(["create", "demo", "cli test demo", "--template", "support_triage"], tmp_path)
    assert result.returncode == 0, result.stderr
    return tmp_path / "projects" / "demo"


def test_menu_default_creates_hello(tmp_path: Path):
    result = _run_sutra(["create", "menu", "default hello"], tmp_path, stdin="\n")
    assert result.returncode == 0, result.stderr
    project = tmp_path / "projects" / "menu"
    assert (project / "agents.py").exists()
    assert (project / "pipeline.py").exists()
    content = (project / "agents.py").read_text()
    assert "answer_agent" in content


def test_interactive_wizard(tmp_path: Path):
    # Default responses: one agent, default name/purpose, confirm yes.
    result = _run_sutra(["create", "wizard", "interactive demo", "--interactive"], tmp_path, stdin="\n\n\n\n")
    assert result.returncode == 0, result.stderr
    project = tmp_path / "projects" / "wizard"
    assert (project / "agents.py").exists()
    assert (project / "pipeline.py").exists()


def test_interactive_project_runs(tmp_path: Path):
    stdin = "\n\n\n\n"
    result = _run_sutra(["create", "runwizard", "interactive run", "--interactive"], tmp_path, stdin=stdin)
    assert result.returncode == 0, result.stderr
    project = tmp_path / "projects" / "runwizard"
    pipeline = project / "pipeline.py"
    run = _run_sutra(["run", str(pipeline), "--text", "hello"], tmp_path)
    assert run.returncode == 0, run.stderr
    assert "Missing var" not in run.stderr


def test_cli_help(tmp_path: Path):
    result = _run_sutra(["help"], tmp_path)
    assert result.returncode == 0
    combined = f"{result.stdout}\n{result.stderr}".lower()
    if combined.strip():
        assert "usage" in combined


def test_create_scaffold(tmp_path: Path):
    project = _create_demo_project(tmp_path)
    assert (project / "agents.py").exists()
    assert (project / "pipeline.py").exists()


def test_create_force_overwrite(tmp_path: Path):
    project = _create_demo_project(tmp_path)
    result = _run_sutra(["create", "demo", "cli test demo", "--yes", "--force"], tmp_path)
    assert result.returncode == 0, result.stderr
    assert (project / "agents.py").exists()
    assert (project / "pipeline.py").exists()


def test_run_pipeline_mocked_ollama(tmp_path: Path):
    _create_demo_project(tmp_path)
    result = _run_sutra(["run", "projects/demo/pipeline.py", "--text", "hello"], tmp_path)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "classification" in payload
    assert payload["classification"][0]["urgency"] == "high"
    assert "replier" in payload
    assert "summary" in payload
