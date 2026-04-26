"""`holdspeak dictation` CLI subcommand (HS-1-08).

Spec: `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` §6.2 #8 + §9.3
(`DIR-A-001`) + §9.1 (`DIR-F-010`). Five subcommands:

  - `dry-run "<text>"` — execute the full pipeline against a
    synthetic `Utterance` without touching the keyboard typer.
  - `blocks ls` — list block ids loaded from the resolved
    `blocks.yaml`.
  - `blocks show <id>` — print one block's full spec.
  - `blocks validate [--project PATH]` — load + validate a YAML.
  - `runtime status` — report the resolved backend + load status.

Designed to run without an LLM backend installed: when the runtime
build fails, `dry-run` prints a warning and runs the pipeline with
`llm_enabled=False` (HS-1-03 contract: `intent-router` is skipped,
not errored). Block authors can therefore validate their YAML and
inspect the non-LLM stages without `mlx-lm` or `llama-cpp-python`
on the host.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, TextIO

from ..config import Config

if TYPE_CHECKING:  # pragma: no cover — type-only import
    from ..plugins.dictation.assembly import BuildResult
    from ..plugins.dictation.blocks import LoadedBlocks


_EXIT_OK = 0
_EXIT_USAGE = 2


def run_dictation_command(args, *, stream: TextIO | None = None) -> int:
    """Top-level dispatch for `holdspeak dictation <action> ...`.

    `stream` is a test seam so the unit tests can capture output
    without relying on `capsys` interleavings.
    """
    out = stream if stream is not None else sys.stdout
    action = getattr(args, "dictation_action", None)

    if action == "dry-run":
        return _cmd_dry_run(args, out)
    if action == "blocks-ls":
        return _cmd_blocks_ls(args, out)
    if action == "blocks-show":
        return _cmd_blocks_show(args, out)
    if action == "blocks-validate":
        return _cmd_blocks_validate(args, out)
    if action == "runtime-status":
        return _cmd_runtime_status(args, out)

    print("usage: holdspeak dictation <dry-run|blocks|runtime> ...", file=out)
    return _EXIT_USAGE


# ---------------------------------------------------------------------------
# dry-run
# ---------------------------------------------------------------------------

def _cmd_dry_run(args, out: TextIO) -> int:
    from ..plugins.dictation.assembly import build_pipeline
    from ..plugins.dictation.contracts import Utterance

    cfg = Config.load()
    text: str = args.text

    result = build_pipeline(cfg.dictation)
    if result.runtime_status != "loaded":
        print(
            f"warning: LLM runtime unavailable ({result.runtime_detail}); "
            "running with intent-router skipped.",
            file=out,
        )

    print(f"resolved blocks: {len(result.blocks.blocks)} from "
          f"{result.blocks.source_path or '(no blocks file)'}", file=out)
    print(f"runtime: {result.runtime_status} ({result.runtime_detail})", file=out)
    print(f"input: {text!r}", file=out)
    print("---", file=out)

    utt = Utterance(
        raw_text=text,
        audio_duration_s=0.0,
        transcribed_at=datetime.now(),
        project=None,
    )
    run = result.pipeline.run(utt)

    if run.short_circuited and not run.stage_results:
        print("(pipeline disabled — no stages executed)", file=out)
        return _EXIT_OK

    for sr in run.stage_results:
        print(f"[{sr.stage_id}] elapsed_ms={sr.elapsed_ms:.2f}", file=out)
        if sr.intent is not None:
            tag = sr.intent
            print(
                f"  intent: matched={tag.matched} block_id={tag.block_id} "
                f"confidence={tag.confidence:.2f}",
                file=out,
            )
        if sr.warnings:
            for w in sr.warnings:
                print(f"  warning: {w}", file=out)
        if sr.metadata:
            print(f"  metadata: {sr.metadata}", file=out)
        print(f"  text: {sr.text!r}", file=out)

    print("---", file=out)
    print(f"final_text: {run.final_text!r}", file=out)
    print(f"total_elapsed_ms: {run.total_elapsed_ms:.2f}", file=out)
    if run.warnings:
        print("pipeline warnings:", file=out)
        for w in run.warnings:
            print(f"  - {w}", file=out)
    return _EXIT_OK


# ---------------------------------------------------------------------------
# blocks
# ---------------------------------------------------------------------------

def _resolved_blocks(args) -> "LoadedBlocks":
    from ..plugins.dictation.assembly import DEFAULT_GLOBAL_BLOCKS_PATH
    from ..plugins.dictation.blocks import resolve_blocks

    project_root: Optional[Path] = None
    if getattr(args, "project", None):
        project_root = Path(args.project).expanduser()
    return resolve_blocks(DEFAULT_GLOBAL_BLOCKS_PATH, project_root)


def _cmd_blocks_ls(args, out: TextIO) -> int:
    blocks = _resolved_blocks(args)
    if not blocks.blocks:
        print("no blocks loaded", file=out)
        return _EXIT_OK
    print(f"# {len(blocks.blocks)} blocks from {blocks.source_path}", file=out)
    for b in blocks.blocks:
        print(f"{b.id}\t{b.description}", file=out)
    return _EXIT_OK


def _cmd_blocks_show(args, out: TextIO) -> int:
    blocks = _resolved_blocks(args)
    block_id: str = args.block_id
    for b in blocks.blocks:
        if b.id == block_id:
            print(f"id: {b.id}", file=out)
            print(f"description: {b.description}", file=out)
            print(f"match.examples: {list(b.match.examples)}", file=out)
            print(f"match.negative_examples: {list(b.match.negative_examples)}", file=out)
            print(f"match.threshold: {b.match.threshold}", file=out)
            if b.match.extras_schema:
                print(f"match.extras_schema: {dict(b.match.extras_schema)}", file=out)
            print(f"inject.mode: {b.inject.mode.value}", file=out)
            print("inject.template:", file=out)
            for line in b.inject.template.splitlines() or [""]:
                print(f"  {line}", file=out)
            return _EXIT_OK
    print(f"error: no block with id {block_id!r}", file=out)
    return _EXIT_USAGE


def _cmd_blocks_validate(args, out: TextIO) -> int:
    from ..plugins.dictation.assembly import DEFAULT_GLOBAL_BLOCKS_PATH
    from ..plugins.dictation.blocks import (
        BlockConfigError,
        load_blocks_yaml,
    )

    if getattr(args, "project", None):
        project_root = Path(args.project).expanduser()
        target = project_root / ".holdspeak" / "blocks.yaml"
    else:
        target = DEFAULT_GLOBAL_BLOCKS_PATH

    if not target.exists():
        print(f"no blocks file at {target}; nothing to validate", file=out)
        return _EXIT_OK

    try:
        loaded = load_blocks_yaml(target)
    except BlockConfigError as exc:
        print(f"error: {exc}", file=out)
        return _EXIT_USAGE

    print(f"ok: {target} — {len(loaded.blocks)} block(s), version={loaded.version}", file=out)
    return _EXIT_OK


# ---------------------------------------------------------------------------
# runtime status
# ---------------------------------------------------------------------------

def _cmd_runtime_status(args, out: TextIO) -> int:
    from ..plugins.dictation.runtime import RuntimeUnavailableError, resolve_backend

    cfg = Config.load().dictation
    print(f"requested backend: {cfg.runtime.backend}", file=out)
    print(f"mlx_model: {cfg.runtime.mlx_model}", file=out)
    print(f"llama_cpp_model_path: {cfg.runtime.llama_cpp_model_path}", file=out)
    try:
        resolved, reason = resolve_backend(cfg.runtime.backend)
    except RuntimeUnavailableError as exc:
        print(f"resolution: unavailable — {exc}", file=out)
        return _EXIT_OK
    print(f"resolved backend: {resolved} ({reason})", file=out)

    # Check model availability without actually loading.
    target = (
        Path(cfg.runtime.mlx_model).expanduser()
        if resolved == "mlx"
        else Path(cfg.runtime.llama_cpp_model_path).expanduser()
    )
    if target.exists():
        print(f"model: available at {target}", file=out)
    else:
        print(f"model: missing at {target}", file=out)
    return _EXIT_OK


def _build_argparse_subparsers(dictation_parser) -> None:
    """Wire `holdspeak dictation <action>` subparsers.

    Called from `main.py`; lives here so the CLI surface stays in
    one file.
    """
    actions = dictation_parser.add_subparsers(dest="dictation_action")

    dr = actions.add_parser("dry-run", help="Run the pipeline against a synthetic utterance")
    dr.add_argument("text", help="The utterance text to feed through the pipeline")

    blocks = actions.add_parser("blocks", help="Inspect / validate block-config YAML")
    blocks_actions = blocks.add_subparsers(dest="dictation_blocks_action")

    ls = blocks_actions.add_parser("ls", help="List loaded block ids")
    ls.add_argument("--project", help="Project root override (looks at <root>/.holdspeak/blocks.yaml)")

    show = blocks_actions.add_parser("show", help="Print one block's spec")
    show.add_argument("block_id")
    show.add_argument("--project", help="Project root override")

    validate = blocks_actions.add_parser("validate", help="Validate a blocks.yaml file")
    validate.add_argument("--project", help="Validate <PROJECT>/.holdspeak/blocks.yaml instead of the global file")

    runtime = actions.add_parser("runtime", help="Inspect the LLM runtime resolution")
    runtime_actions = runtime.add_subparsers(dest="dictation_runtime_action")
    runtime_actions.add_parser("status", help="Print resolved backend + model availability")


def normalize_args(args) -> Any:
    """Map nested argparse subparser attrs into a flat `dictation_action`.

    `main.py` calls this after `parse_args()` so the dispatcher
    sees one of the canonical action strings.
    """
    top = getattr(args, "dictation_action", None)
    if top == "blocks":
        sub = getattr(args, "dictation_blocks_action", None)
        if sub is None:
            args.dictation_action = None
        else:
            args.dictation_action = f"blocks-{sub}"
    elif top == "runtime":
        sub = getattr(args, "dictation_runtime_action", None)
        if sub is None:
            args.dictation_action = None
        else:
            args.dictation_action = f"runtime-{sub}"
    return args
