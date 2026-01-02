"""Command-line interface for Sutra."""
from __future__ import annotations

import argparse
import sys

from .core import (
    cmd_create,
    cmd_run,
    cmd_test,
    cmd_doctor,
    cmd_template,
    cmd_ui,
)


def main() -> None:
    ap = argparse.ArgumentParser(prog="sutra")
    sub = ap.add_subparsers(dest="cmd", required=True)

    argv = sys.argv[1:]
    if argv:
        if argv[0] == "help":
            argv[0] = "--help"
        elif len(argv) >= 2 and argv[-1] == "help":
            argv[-1] = "--help"

    c = sub.add_parser("create")
    c.add_argument("project_name")
    c.add_argument("description")
    c.add_argument("--yes", action="store_true", help="Skip confirmation prompts when a project already exists.")
    c.add_argument("--force", action="store_true", help="Overwrite projects without prompting if they already exist.")

    r = sub.add_parser(
        "run",
        description="Execute a pipeline; use --text or the optional positional text_target alias.",
        help="Run a pipeline (shorthand text may be given positionally instead of --text).",
    )
    r.add_argument("pipeline_file")
    r.add_argument("--input", default=None, help="Path to JSON/JSONL file or inline JSON")
    r.add_argument("--text", default=None, help="Raw text payload (mutually exclusive with --input)")
    r.add_argument("text_payload", nargs="?", default=None, help="Alias for --text (free text input)")
    r.add_argument("--reliable", action="store_true", help="Enable Reliable Input mode (requires NORMALIZER)")
    r.add_argument("--output", default=None, help="Optional output file path (JSONL)")

    t = sub.add_parser("test")
    t.add_argument("pipeline_file")

    d = sub.add_parser("doctor")

    tpl = sub.add_parser("template")
    tpl.add_argument("pipeline_file")

    u = sub.add_parser("ui")
    u.add_argument("--host", default=None)
    u.add_argument("--port", type=int, default=None)
    u.add_argument("--reload", action="store_true")

    args = ap.parse_args(argv)
    if args.cmd == "create":
        cmd_create(args.project_name, args.description, yes=args.yes, force=args.force)
    elif args.cmd == "run":
        text_arg = args.text if args.text is not None else args.text_payload
        cmd_run(
            args.pipeline_file,
            args.input,
            text=text_arg,
            reliable=args.reliable,
            output=args.output,
        )
    elif args.cmd == "test":
        cmd_test(args.pipeline_file)
    elif args.cmd == "doctor":
        cmd_doctor()
    elif args.cmd == "template":
        cmd_template(args.pipeline_file)
    elif args.cmd == "ui":
        cmd_ui(args.host, args.port, args.reload)
