from __future__ import annotations

# sutra core — Local-first agent workflows
import importlib.util, json, pathlib, sys, time, types, urllib.request, urllib.error, subprocess
from pathlib import Path
from typing import Any, Iterable, List, Optional, Tuple

from .config import APP_DIR, CONFIG_PATH, DEFAULT_CONFIG, load_config, resolve_path
from .input import WorkItem, coerce_work_item, load_work_items

CONFIG = load_config()

_MODEL_CACHE = {"host": None, "models": [], "ts": 0.0}

def get_available_models(host=None, timeout=2, force=False):
    """Return a list of model names from a local Ollama instance, cached briefly."""
    target_host = (host or CONFIG.get("ollama_host", DEFAULT_CONFIG["ollama_host"])).rstrip("/")
    now = time.time()
    cache_valid = (
        not force
        and _MODEL_CACHE["models"]
        and _MODEL_CACHE["host"] == target_host
        and now - _MODEL_CACHE["ts"] < 30
    )
    if cache_valid:
        return _MODEL_CACHE["models"]
    try:
        resp = urllib.request.urlopen(f"{target_host}/api/tags", timeout=timeout)
        data = json.loads(resp.read().decode('utf-8'))
        models = [m.get('name') for m in data.get('models', []) if isinstance(m, dict) and 'name' in m]
        models = [m for m in models if m]
        _MODEL_CACHE.update({"host": target_host, "models": models, "ts": now})
        return models
    except Exception:
        return _MODEL_CACHE["models"]

# ---------- Trace ----------
RUNS_DIR = resolve_path(CONFIG.get("runs_dir"), APP_DIR / "runs")
RUNS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR = resolve_path(CONFIG.get("outputs_dir"), APP_DIR / "outputs")
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

class Trace:
    def __init__(self, directory: Path | None = None):
        if directory is None:
            directory = RUNS_DIR / time.strftime("%Y%m%d-%H%M%S")
        self.d = directory
        self.d.mkdir(parents=True, exist_ok=True)
        self.i = 0

    @property
    def directory(self) -> Path:
        return self.d

    def dump(self, name, payload):
        self.i += 1
        (self.d / f"{self.i:02d}_{name}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

def create_run_root() -> Tuple[Path, str]:
    """Allocate a run directory and return (path, run_id)."""
    run_id = time.strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir, run_id

# ---------- Ollama ----------
class Ollama:
    def __init__(self, model=None, host=None, timeout=None):
        self.model = model or CONFIG.get("default_model", DEFAULT_CONFIG["default_model"])
        self.host = (host or CONFIG.get("ollama_host", DEFAULT_CONFIG["ollama_host"])).rstrip("/")
        self.timeout = timeout or CONFIG.get("request_timeout", DEFAULT_CONFIG["request_timeout"])
        available = get_available_models(self.host)
        if available and self.model not in available:
            fallback = available[0]
            print(f"[Sutra] Model '{self.model}' not found on {self.host}, falling back to '{fallback}'.", file=sys.stderr)
            self.model = fallback

    def generate(self, prompt, temperature=0.2, json_mode=False, timeout=None):
        url = f"{self.host}/api/generate"
        payload = {"model": self.model, "prompt": prompt, "temperature": temperature, "stream": False}
        if json_mode: payload["format"] = "json"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.timeout) as r:
                body = r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8")
            except Exception:
                body = str(e)
            raise RuntimeError(f"Ollama HTTP error {e.code}: {body}")
        except Exception as e:
            raise RuntimeError(f"Ollama connection error: {e}")

        # Try to parse JSON responses and normalize common shapes
        try:
            j = json.loads(body)
            if isinstance(j, dict):
                for key in ("response", "text", "output", "result"):
                    if key in j:
                        val = j[key]
                        return val if isinstance(val, str) else json.dumps(val)
                if "choices" in j and isinstance(j["choices"], list) and j["choices"]:
                    choice = j["choices"][0]
                    if isinstance(choice, dict):
                        for k in ("text", "message"):
                            if k in choice:
                                val = choice[k]
                                return val if isinstance(val, str) else json.dumps(val)
                    if isinstance(choice, str):
                        return choice
            # If parsed JSON didn't contain a clear text field, return raw body
            return body
        except Exception:
            # Not JSON — return raw body
            return body

# ---------- JSON Helpers ----------
def _extract_json(text: str):
    import re
    m = None
    # Try full-text JSON parse first
    try:
        return json.loads(text)
    except Exception:
        pass

    # Fallback: find first JSON object/array (non-greedy)
    m = re.search(r'(\{.*?\}|\[.*?\])', text, re.DOTALL)
    if not m: return None
    try: return json.loads(m.group(1))
    except: return None

def _validate(obj, required):
    if not required: return True, ""
    if isinstance(obj, list):
        for i, it in enumerate(obj):
            if not isinstance(it, dict):
                return False, f"item {i} not dict"
            miss = [k for k in required if k not in it]
            if miss: return False, f"item {i} missing {miss}"
        return True, ""
    if isinstance(obj, dict):
        miss = [k for k in required if k not in obj]
        return (not miss, f"missing {miss}" if miss else "")
    return False, "not dict/list"

_WRAPPER_KEYS = ("items", "data", "result", "results", "topics", "list")

def _coerce_json_shape(obj, required):
    if obj is None: return None
    if isinstance(obj, dict):
        for k in _WRAPPER_KEYS:
            if k in obj and isinstance(obj[k], list):
                obj = obj[k]
                break
        else:
            if required and all(k in obj for k in required):
                obj = [obj]
    if isinstance(obj, list):
        out = []
        for it in obj:
            if not isinstance(it, dict): return obj
            it = it.copy()
            if "note" not in it and "notes" in it:
                it["note"] = it.pop("notes")
            if required:
                it = {k: it.get(k, "") for k in required}
            out.append(it)
        return out
    return obj

# ---------- CORE CLASSES ----------
class Agent:
    def __init__(self, name, objective, model, prompt,
                 expects_json=False, output_key="output", system_hint=None,
                 required_keys=None, retries=1, temperature=0.0):
        self.name=name; self.objective=objective; self.model=model; self.prompt=prompt
        self.expects_json=expects_json; self.output_key=output_key; self.system_hint=system_hint
        self.required_keys=required_keys or []; self.retries=retries; self.temperature=temperature

    def run(self, inputs: dict)->dict:
        try:
            p = self.prompt.format(**inputs, objective=self.objective)
        except KeyError as e:
            raise ValueError(f"[{self.name}] Missing var: {e}")
        if self.system_hint:
            p = f"{self.system_hint}\n\n---\n{p}"

        llm = Ollama(model=self.model)
        attempts = self.retries + 1
        last_raw = ""

        modes = ([True, False] if self.expects_json else [False])
        for a in range(attempts):
            prompt_now = p if a == 0 else p + "\n\nReturn ONLY valid JSON."
            for jm in modes:
                raw = llm.generate(
                    prompt_now,
                    json_mode=jm and self.expects_json,
                    temperature=self.temperature
                )
                last_raw = raw.strip()

                if not self.expects_json:
                    return {self.output_key: raw}

                obj = None
                try:
                    obj = json.loads(raw)
                except:
                    obj = _extract_json(raw)

                obj = _coerce_json_shape(obj, self.required_keys)
                ok, why = _validate(obj, self.required_keys)
                if ok:
                    return {self.output_key: obj}

        return {self.output_key: {"error":"invalid_json", "raw": last_raw[:2000]}}

class Step:
    def __init__(self, agent: 'Agent', takes=None, on_error="continue"):
        self.agent=agent; self.takes=takes or []; self.on_error=on_error
    def __call__(self, state: dict)->dict:
        subset = {k: state.get(k) for k in self.takes} if self.takes else state
        try:
            out = self.agent.run(subset)
        except Exception as e:
            if self.on_error=="stop": raise
            out = { self.agent.output_key: {"error":"exception", "message": str(e)} }
        new = state.copy(); new.update(out); return new

class Pipeline:
    def __init__(self, steps):
        if not steps: raise ValueError("Pipeline needs steps")
        self.steps = steps
    def run(self, initial: dict, trace: Trace | None = None)->dict:
        s = dict(initial or {}); tr = trace or Trace()
        for st in self.steps:
            tr.dump(f"{st.agent.name}_in", s)
            s = st(s)
            tr.dump(f"{st.agent.name}_out", s)
        return s


def _initial_state_from_work_item(work_item: WorkItem) -> dict:
    """Provide backward-compatible state payloads for pipelines."""
    state = {
        "work_item": work_item,
        "input": work_item,
        "text": work_item["text"],
        "fields": work_item["fields"],
        "attachments": work_item["attachments"],
    }
    if work_item["id"] is not None:
        state["id"] = work_item["id"]
    if work_item["type"] is not None:
        state["type"] = work_item["type"]
    for key, value in work_item["fields"].items():
        state.setdefault(key, value)
    return state


def _resolve_normalizer(mod) -> Step | None:
    """Return a pre-step normalizer exported by the pipeline module."""
    for attr in ("NORMALIZER_STEP", "NORMALIZER", "NORMALIZER_AGENT"):
        candidate = getattr(mod, attr, None)
        if candidate is None:
            continue
        if isinstance(candidate, Step):
            return candidate
        if isinstance(candidate, Agent):
            return Step(candidate)
    return None


def _run_pipeline_with_work_item(
    pipe: Pipeline,
    work_item: WorkItem,
    *,
    normalizer_step: Step | None = None,
    trace: Trace | None = None,
) -> dict:
    state = _initial_state_from_work_item(work_item)
    if normalizer_step is not None:
        state = normalizer_step(state)
    return pipe.run(state, trace=trace)

# ---------- INTERACTIVE GENERATOR ----------
def create_generic_agent(project_name: str, agent_name: str, agent_purpose: str, model: str) -> str:
    """Generate a generic agent file"""
    return f"""# {project_name}_{agent_name}.py
from sutra import Agent

{agent_name} = Agent(
    name='{agent_name}',
    objective='{agent_purpose}',
    model='{model}',
    prompt='''{agent_purpose}

Input: {{text}}

Process the input and return structured JSON.
Be specific and clear in your output.

Return only valid JSON.''',
    expects_json=True,
    output_key='{agent_name}',
    required_keys=[],
    retries=1,
    temperature=0.1
)"""

def interactive_agent_config(project_name: str) -> list:
    """Get agent configuration from user"""
    print("\nConfigure your agents:")

    while True:
        try:
            num = int(input("How many agents? (1-5): "))
            if 1 <= num <= 5:
                break
        except:  # pragma: no cover - interactive helper
            pass
        print("Enter 1-5")

    agents = []
    models = get_available_models() or []
    missing_models_warning = False
    if not models:
        default_model = CONFIG.get("default_model", DEFAULT_CONFIG["default_model"])
        print(
            f"[Sutra] Ollama did not return any models. "
            f"Install at least the configured default model (`ollama pull {default_model}`), "
            f"then rerun creation. Falling back to '{default_model}' for now."
        )
        models = [default_model]
        missing_models_warning = True

    for i in range(num):
        print(f"\n=== Agent {i+1} ===")

        while True:
            name = input("Name: ").strip().lower().replace(" ", "_")
            if name and name.isidentifier():
                break
            print("Invalid name")

        purpose = input("Purpose: ").strip() or f"Process {name}"

        print("Models: " + ", ".join(f"{j+1}={m}" for j, m in enumerate(models)))
        while True:
            try:
                choice = input(f"Model (1-{len(models)}) [1]: ").strip() or "1"
                idx = int(choice) - 1
                if 0 <= idx < len(models):
                    model = models[idx]
                    break
            except:  # pragma: no cover - interactive helper
                pass

        agents.append({"name": name, "purpose": purpose, "model": model})

    print("\n=== Summary ===")
    for i, a in enumerate(agents, 1):
        print(f"{i}. {a['name']} ({a['model']}): {a['purpose']}")
    if missing_models_warning:
        default_model = CONFIG.get("default_model", DEFAULT_CONFIG["default_model"])
        print(
            "\n[Sutra] No Ollama models were listed, so Sutra used the default "
            f"model '{default_model}'. Configure a model under `.sutra/config.json` "
            f"and install it (e.g., `ollama pull {default_model}`) before running more pipelines."
        )

    if input("\nCreate? [Y/n]: ").lower() in ("", "y"):
        return agents
    return []

def generate_dynamic_pipeline(project_name: str, description: str, agent_names: list) -> str:
    """Generate pipeline file"""
    agents_str = ", ".join([f'"{project_name}_{n}"' for n in agent_names])
    
    return f"""# {project_name}_pipeline.py
# {description}

from sutra import Step, Pipeline
import importlib

AGENT_ORDER = [{agents_str}]

def build():
    steps = []
    prev = ['text']
    
    for agent_file in AGENT_ORDER:
        mod = importlib.import_module(agent_file)
        agent_name = agent_file.split('_')[-1]
        agent = getattr(mod, agent_name)
        steps.append(Step(agent, takes=prev.copy()))
        prev.append(agent_name)
    
    return Pipeline(steps)

DEFAULT_INPUT = {{'text': 'test input'}}
"""

def cmd_create(project_name, description):
    """Create new project"""
    project_name = project_name.replace('.py', '').replace('.', '_').replace('-', '_')
    project_dir = pathlib.Path("projects") / project_name
    
    if project_dir.exists():
        if input(f"{project_dir} exists. Overwrite? [y/N]: ").lower() != 'y':
            return
    
    project_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nProject: {project_name}")
    print(f"Location: {project_dir}")
    
    agents = interactive_agent_config(project_name)
    if not agents: 
        print("Cancelled")
        return
    
    print(f"\nGenerating files...")
    
    for a in agents:
        f = project_dir / f"{project_name}_{a['name']}.py"
        f.write_text(create_generic_agent(project_name, a['name'], a['purpose'], a['model']), encoding="utf-8")
        print(f"  {f.name}")
    
    names = [a['name'] for a in agents]
    pipeline = project_dir / f"{project_name}_pipeline.py"
    pipeline.write_text(generate_dynamic_pipeline(project_name, description, names), encoding="utf-8")
    print(f"  {pipeline.name}")
    
    print(f"\nTest: sutra test {pipeline}")

# ---------- CLI ----------
def _import_module(path_str)->types.ModuleType:
    p = pathlib.Path(path_str)
    if not p.exists(): raise FileNotFoundError(p)
    spec = importlib.util.spec_from_file_location("user_pipeline", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def _load_default_input(path_str):
    try:
        mod = _import_module(path_str)
        tpl = getattr(mod, "DEFAULT_INPUT", None)
        if tpl is None:
            return {}
        return tpl
    except Exception:
        return {}

def cmd_run(
    filename,
    input_arg: str | None = None,
    *,
    text: str | None = None,
    reliable: bool = False,
    output: str | None = None,
):
    # 1) Resolve paths
    pipeline_path = Path(filename).resolve()
    project_dir = pipeline_path.parent  # e.g., projects/QuizMaster

    if input_arg and text:
        raise ValueError("--text and --input cannot be used together.")

    # 2) Make project folder importable (so pipeline can import sibling agents)
    if str(project_dir) not in sys.path:
        sys.path.insert(0, str(project_dir))

    # 3) Import the pipeline module by file path
    spec = importlib.util.spec_from_file_location("pipeline", str(pipeline_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    pipe = mod.build()
    default_payload = getattr(mod, "DEFAULT_INPUT", {"text": ""})
    work_items = load_work_items(input_arg, text, default_payload)
    normalizer_step = _resolve_normalizer(mod)
    if reliable and normalizer_step is None:
        print("[Sutra] --reliable requested but this pipeline does not define NORMALIZER.", file=sys.stderr)

    run_root, run_id = create_run_root()
    dest = Path(output) if output else OUTPUTS_DIR / f"{run_id}.jsonl"
    dest.parent.mkdir(parents=True, exist_ok=True)
    multi = len(work_items) > 1
    results: List[dict] = []

    with dest.open("w", encoding="utf-8") as fh:
        for idx, work_item in enumerate(work_items, start=1):
            trace_dir = run_root if not multi else run_root / f"{idx:03d}_{work_item.get('id') or 'item'}"
            trace = Trace(trace_dir)
            result = _run_pipeline_with_work_item(
                pipe,
                work_item,
                normalizer_step=normalizer_step,
                trace=trace,
            )
            record = {"work_item": work_item, "result": result}
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            results.append(result)

    if multi:
        payload = {"run_id": run_id, "output_file": str(dest), "items": len(work_items)}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(results[0], indent=2, ensure_ascii=False))

def cmd_test(filename):
    mod = _import_module(filename)
    pipe = mod.build()
    default_payload = getattr(mod, "DEFAULT_INPUT", {"text": ""})
    work_item = load_work_items(None, None, default_payload)[0]
    print(f"Testing WorkItem: {json.dumps(work_item, ensure_ascii=False)}")
    out = _run_pipeline_with_work_item(pipe, work_item, normalizer_step=_resolve_normalizer(mod))
    print(json.dumps(out, indent=2, ensure_ascii=False))

def cmd_doctor():
    models = get_available_models()
    if models:
        print("Ollama OK")
        print(f"Models: {', '.join(models)}")
    else:
        print("Ollama not reachable or no models found")

    try:
        r = Ollama().generate("Say OK.", json_mode=False)
        print(f"Test: {r[:60]}")
    except Exception as e:
        print(f"Error: {e}")

def cmd_template(filename):
    tpl = _load_default_input(filename)
    work_item = load_work_items(None, None, tpl or {"text": ""})[0]
    print(json.dumps(work_item, indent=2, ensure_ascii=False))

def cmd_ui(host: str | None, port: int | None, reload: bool):
    import uvicorn
    from sutra.ui.server import app

    cfg_host = host or CONFIG.get("ui_host", DEFAULT_CONFIG["ui_host"])
    cfg_port = port or CONFIG.get("ui_port", DEFAULT_CONFIG["ui_port"])
    uvicorn.run(app, host=cfg_host, port=cfg_port, reload=reload, reload_dirs=[str(pathlib.Path.cwd())])
