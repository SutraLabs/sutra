"""Template safety tests for Sutra scaffolding."""

from __future__ import annotations

import pytest

from sutra.core import (
    HELLO_WORLD_PROMPT_BODY,
    INTERACTIVE_PROMPT_TEMPLATE,
    SUPPORT_TRIAGE_CLASSIFICATION_PROMPT_BODY,
    SUPPORT_TRIAGE_REPLIER_PROMPT_BODY,
    SUPPORT_TRIAGE_SUMMARY_PROMPT_BODY,
)
from sutra.safe_template import find_unsafe_placeholders, render_template


def test_render_template_leaves_json_alone():
    source = '{"answer": "x"}'
    assert render_template(source, {}) == source


def test_render_template_substitutes_double_brace():
    assert render_template("Hello {{name}}", {"name": "node"}) == "Hello node"


def test_render_template_rejects_single_brace_placeholders():
    with pytest.raises(ValueError) as excinfo:
        render_template("Hello {name}", {"name": "node"})
    assert "Unsafe template placeholder" in str(excinfo.value)


def test_render_template_missing_vars_error():
    with pytest.raises(ValueError) as excinfo:
        render_template("Hello {{missing}}", {})
    assert "Missing template var: missing" in str(excinfo.value)


def test_scaffold_templates_have_no_single_brace_identifiers():
    find = find_unsafe_placeholders
    assert find(INTERACTIVE_PROMPT_TEMPLATE) == []
    assert find(HELLO_WORLD_PROMPT_BODY) == []
    assert find(SUPPORT_TRIAGE_CLASSIFICATION_PROMPT_BODY) == []
    assert find(SUPPORT_TRIAGE_REPLIER_PROMPT_BODY) == []
    assert find(SUPPORT_TRIAGE_SUMMARY_PROMPT_BODY) == []
