"""Smoke tests that ensure scaffolds import and run without Ollama."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
os.environ.setdefault("SUTRA_MOCK_OLLAMA", "1")


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


def _import_pipeline(pipeline_path: Path):
    spec = importlib.util.spec_from_file_location("user_pipeline", str(pipeline_path))
    module = importlib.util.module_from_spec(spec)
    project_dir = pipeline_path.parent
    original_sys_path = list(sys.path)
    if str(project_dir) not in sys.path:
        sys.path.insert(0, str(project_dir))
    old_agents = sys.modules.pop("agents", None)
    try:
        spec.loader.exec_module(module)
    finally:
        if old_agents is not None:
            sys.modules["agents"] = old_agents
        else:
            sys.modules.pop("agents", None)
        sys.path[:] = original_sys_path
    return module


def _run_pipeline(pipeline_path: Path):
    mod = _import_pipeline(pipeline_path)
    pipeline = mod.build()
    payload = getattr(mod, "DEFAULT_INPUT", {"text": "ok"})
    return pipeline.run(payload)


def test_hello_world_scaffold_runs(tmp_path: Path):
    result = _run_sutra(
        ["create", "smoke_hello", "basic smoke", "--template", "hello_world", "--yes"],
        tmp_path,
    )
    assert result.returncode == 0, result.stderr
    pipeline_path = tmp_path / "projects" / "smoke_hello" / "pipeline.py"
    output = _run_pipeline(pipeline_path)
    assert "answer" in output
    assert isinstance(output["answer"], list)


def test_interactive_scaffold_runs(tmp_path: Path):
    stdin = "\n\n\n\n"
    result = _run_sutra(
        ["create", "smoke_interactive", "wizard smoke", "--interactive"],
        tmp_path,
        stdin=stdin,
    )
    assert result.returncode == 0, result.stderr
    pipeline_path = tmp_path / "projects" / "smoke_interactive" / "pipeline.py"
    output = _run_pipeline(pipeline_path)
    baseline = {"work_item", "input", "text", "fields", "attachments"}
    emitted = set(output.keys()) - baseline
    assert emitted, "Interactive scaffold did not emit agent outputs"
