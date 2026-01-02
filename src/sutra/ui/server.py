"""Simple FastAPI UI for Sutra pipelines."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import List

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from sutra.config import APP_DIR, load_config, resolve_path

PACKAGE_DIR = Path(__file__).resolve().parent
WORKSPACE = Path.cwd()
CONFIG = load_config()
RUNS_DIR = resolve_path(CONFIG.get("runs_dir"), APP_DIR / "runs")
RUNS_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))

app = FastAPI(title="Sutra UI", version="0.1")


def _load_default_for(path: Path):
    try:
        module_name = f"sutra_ui_{hash(path)}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader
        spec.loader.exec_module(mod)
        tpl = getattr(mod, "DEFAULT_INPUT", {})
        return tpl if isinstance(tpl, (dict, list, str, int, float, bool)) else {}
    except Exception:
        return {}


def _discover_pipelines():
    candidates = []
    for base in (WORKSPACE / "projects", WORKSPACE / "examples"):
        if base.exists():
            for f in sorted(base.rglob("*_pipeline.py")):
                rel = str(f.relative_to(WORKSPACE))
                candidates.append(
                    {
                        "path": rel,
                        "default_input": _load_default_for(f),
                    }
                )
    return candidates


def _list_runs(limit: int = 20) -> List[str]:
    if not RUNS_DIR.exists():
        return []
    runs = [p.name for p in RUNS_DIR.iterdir() if p.is_dir()]
    runs.sort(reverse=True)
    return runs[:limit]


def _safe_path(rel: str) -> Path:
    target = (WORKSPACE / rel).resolve()
    if not str(target).startswith(str(WORKSPACE.resolve())):
        raise HTTPException(status_code=400, detail="Path outside workspace")
    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return target


def _base_context():
    pipelines = _discover_pipelines()
    template_map = {p["path"]: p["default_input"] for p in pipelines}
    try:
        templates_json = json.dumps(template_map, ensure_ascii=False)
    except TypeError:
        sanitized = {}
        for key, val in template_map.items():
            if isinstance(val, (dict, list, str, int, float, bool)) or val is None:
                sanitized[key] = val
            else:
                sanitized[key] = str(val)
        templates_json = json.dumps(sanitized, ensure_ascii=False)
    return {
        "pipelines": pipelines,
        "pipeline_templates": templates_json,
        "runs": _list_runs(),
    }


def _render_index(request: Request, *, run_output: str | None = None,
                  run_error: str | None = None,
                  edit_path: str | None = None,
                  edit_content: str | None = None):
    ctx = _base_context()
    ctx.update(
        {
            "request": request,
            "run_output": run_output,
            "run_error": run_error,
            "edit_path": edit_path,
            "edit_content": edit_content,
        }
    )
    return TEMPLATES.TemplateResponse("index.html", ctx)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return _render_index(request)


@app.post("/run", response_class=HTMLResponse)
async def run_pipeline(request: Request, pipeline_file: str = Form(...), input_json: str = Form("")):
    path = (WORKSPACE / pipeline_file).resolve()
    if not path.exists():
        return _render_index(request, run_error=f"Pipeline not found: {pipeline_file}")

    cmd = [sys.executable, "-m", "sutra.cli", "run", pipeline_file]
    if input_json.strip():
        cmd.extend(["--input", input_json])

    proc = subprocess.run(cmd, cwd=WORKSPACE, capture_output=True, text=True)
    if proc.returncode != 0:
        return _render_index(request, run_error=proc.stderr.strip() or proc.stdout.strip())
    return _render_index(request, run_output=proc.stdout.strip())


@app.get("/runs/{run_id}", response_class=HTMLResponse)
async def show_run(request: Request, run_id: str):
    data = _load_run(run_id)
    return TEMPLATES.TemplateResponse(
        "run_detail.html",
        {"request": request, **data},
    )


@app.get("/runs/{run_id}/{file_name}", response_class=PlainTextResponse)
async def show_run_file(run_id: str, file_name: str):
    run_dir = RUNS_DIR / run_id
    file_path = run_dir / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return file_path.read_text(encoding="utf-8")


@app.get("/api/runs/{run_id}", response_class=JSONResponse)
async def api_run(run_id: str):
    return _load_run(run_id)


@app.get("/edit", response_class=HTMLResponse)
async def edit_prompt(request: Request, path: str):
    try:
        file_path = _safe_path(path)
    except HTTPException as exc:
        raise exc
    content = file_path.read_text(encoding="utf-8")
    return _render_index(
        request,
        edit_path=path,
        edit_content=content,
    )


@app.post("/edit", response_class=HTMLResponse)
async def save_prompt(request: Request, path: str = Form(...), content: str = Form(...)):
    try:
        file_path = _safe_path(path)
    except HTTPException as exc:
        raise exc
    file_path.write_text(content, encoding="utf-8")
    return _render_index(request, edit_path=path, edit_content=content)
def _load_run(run_id: str):
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    files = []
    for f in sorted(run_dir.glob("*.json")):
        raw = f.read_text(encoding="utf-8")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = None
        files.append(
            {
                "name": f.name,
                "raw": raw,
                "parsed": parsed,
            }
        )
    return {"run_id": run_id, "files": files}
