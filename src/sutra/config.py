"""Configuration helpers for Sutra."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

APP_DIR = Path(".sutra")
CONFIG_PATH = APP_DIR / "config.json"
DEFAULT_CONFIG: Dict[str, Any] = {
    "ollama_host": "http://localhost:11434",
    "default_model": "llama3.1:latest",
    "runs_dir": ".sutra/runs",
    "outputs_dir": ".sutra/outputs",
    "request_timeout": 120,
    "ui_host": "127.0.0.1",
    "ui_port": 8000,
}

_CONFIG_CACHE: Dict[str, Any] | None = None


def _write_config(cfg: Dict[str, Any]) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def load_config(force: bool = False) -> Dict[str, Any]:
    """Load config from disk (cached) and ensure defaults exist."""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None and not force:
        return _CONFIG_CACHE

    APP_DIR.mkdir(parents=True, exist_ok=True)
    cfg = DEFAULT_CONFIG.copy()
    if CONFIG_PATH.exists():
        try:
            user = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(user, dict):
                for k, v in user.items():
                    if v is not None:
                        cfg[k] = v
        except Exception:
            pass
    _write_config(cfg)
    _CONFIG_CACHE = cfg
    return cfg


def resolve_path(path_str: str | None, fallback: Path | str) -> Path:
    target = Path(path_str) if path_str else Path(fallback)
    if not target.is_absolute():
        target = (Path.cwd() / target).resolve()
    return target
