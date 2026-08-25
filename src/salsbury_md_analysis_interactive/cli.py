"""Command-line entry point for the optional interactive result browser."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from . import __version__
from .report import InteractiveReportError, build_interactive_report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="salsbury-md-analysis-interactive",
        description=(
            "Build an immutable offline browser from a completed "
            "salsbury-md-analysis campaign."
        ),
    )
    parser.add_argument("root", nargs="?", type=Path, help="completed analysis root")
    parser.add_argument("--output-name", default="interactive-report")
    parser.add_argument("--title")
    parser.add_argument("--maximum-inline-structures", type=int, default=100)
    parser.add_argument("--maximum-inline-structure-bytes", type=int, default=50_000_000)
    parser.add_argument("--maximum-inline-figure-bytes", type=int, default=25_000_000)
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.root is None:
        parser.error("a completed analysis root is required")
    try:
        result = build_interactive_report(
            args.root,
            output_name=args.output_name,
            title=args.title,
            maximum_inline_structures=args.maximum_inline_structures,
            maximum_inline_structure_bytes=args.maximum_inline_structure_bytes,
            maximum_inline_figure_bytes=args.maximum_inline_figure_bytes,
        )
    except (InteractiveReportError, OSError, ValueError) as exc:
        parser.exit(2, f"interactive report failed: {exc}\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0

