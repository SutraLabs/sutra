"""Lightweight helper for double-brace template rendering."""
from __future__ import annotations

import re

_PLACEHOLDER_RE = re.compile(r"(?<!{){([a-zA-Z_][a-zA-Z0-9_]*)}(?!})")
_DOUBLE_BRACE_RE = re.compile(r"{{([a-zA-Z_][a-zA-Z0-9_]*)}}")


def render_template(text: str, vars: dict[str, str]) -> str:
    """Substitute only {{var}} placeholders; treat {var} as unsafe."""
    unsafe = _PLACEHOLDER_RE.search(text)
    if unsafe:
        name = unsafe.group(1)
        raise ValueError(f"Unsafe template placeholder '{{{name}}}' detected. Use '{{{{{name}}}}}' instead.")

    def _replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in vars:
            raise ValueError(f"Missing template var: {name}")
        return str(vars[name])

    return _DOUBLE_BRACE_RE.sub(_replace, text)


def find_unsafe_placeholders(text: str) -> list[str]:
    """Return list of single-brace placeholders that look like {var}."""
    return [match.group(1) for match in _PLACEHOLDER_RE.finditer(text)]


def _find_double_brace_placeholders(text: str) -> set[str]:
    return {match.group(1) for match in _DOUBLE_BRACE_RE.finditer(text)}


def render_with_placeholders(template: str, vars: dict[str, str]) -> str:
    """Render a template while preserving placeholders for later substitution."""
    placeholders = _find_double_brace_placeholders(template)
    context = {name: vars.get(name, f"{{{name}}}") for name in placeholders}
    rendered = render_template(template, context)
    return rendered.replace("{{", "{").replace("}}", "}")
