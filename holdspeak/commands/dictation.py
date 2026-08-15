"""`holdspeak dictation` CLI subcommand (HS-1-08).

Spec: `docs/internal/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` §6.2 #8 + §9.3
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


def run_dictation_command(
    args,
    *,
    stream: TextIO | None = None,
    principal: Any = None,
    config_snapshot: Any = None,
) -> int:
    """Top-level dispatch for `holdspeak dictation <action> ...`.

    `stream` is a test seam so the unit tests can capture output
    without relying on `capsys` interleavings.

    `principal` (HS-131-15) is derived at the TOP level, in `main.py`, from the
    hub-issued owner credential this process holds. It is never derived here and
    never synthesized: `dry-run` refuses by name when it needs a provider and this
    is `None`. Every other subcommand ignores it — listing blocks reaches no model.

    `config_snapshot` is the SAME configuration that credential was checked
    against. `dry-run` freezes its plan and assembles its pipeline from it rather
    than re-reading, so authority and execution cannot be decided against two
    different configurations. The block/runtime subcommands reach no model and
    keep their own local reads.
    """
    out = stream if stream is not None else sys.stdout
    action = getattr(args, "dictation_action", None)

    if action == "dry-run":
        return _cmd_dry_run(
            args, out, principal=principal, config_snapshot=config_snapshot
        )
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

def _cmd_dry_run(
    args, out: TextIO, *, principal: Any = None, config_snapshot: Any = None
) -> int:
    """Run the full configured pipeline over one synthetic utterance (DIR-F-010).

    HS-131-15 admits this command like any other provider-bearing entrance:

    * **Authenticated or lexical, never in between.** A configuration that
      selects a provider-backed stage needs the hub-issued owner credential
      derived in `main.py`; missing it is a NAMED refusal before any runtime is
      constructed. A configuration that selects none stays lexical, constructs no
      runtime, mints no inference child, and needs no credential.
    * **Egress is disclosed from the frozen plan, before construction** — not from
      whatever the settings say afterwards, and not after a model has been warmed.
    * **The result body is buffered** and printed only if it wins the session's
      publication election, so `Ctrl-C` (or an expiry, or a revocation) cannot be
      followed by a late wall of stage output for work that was cancelled.
    """
    from ..plugins.dictation.assembly import build_pipeline
    from ..plugins.dictation.contracts import Utterance
    from ..plugins.dictation.project_root import detect_project_for_cwd
    from ..speech_session import (
        AIM_CLI_DRY_RUN,
        CLI_CREDENTIAL_ENV,
        CLI_CREDENTIAL_REQUIRED,
        SpeechEntry,
        SpeechProviderFailure,
        SpeechSessionRefused,
        admit_text_entry_session,
        pipeline_provider_capabilities,
    )

    # ONE snapshot: the credential was checked against it, the plan is frozen from
    # it, and the pipeline is assembled from it, so a config edit mid-run cannot
    # retarget either — and authority is never decided against a configuration
    # different from the one that runs. `main.py` supplies it; the fallback load
    # is for a direct in-process caller that has no snapshot of its own.
    cfg = Config.load() if config_snapshot is None else config_snapshot
    text: str = args.text

    project = detect_project_for_cwd()
    project_root = Path(project["root"]) if project else None
    capabilities = pipeline_provider_capabilities(cfg)

    entry = None
    if capabilities:
        if principal is None:
            print(f"refused: {CLI_CREDENTIAL_REQUIRED}", file=out)
            print(
                f"  this pipeline reaches a model ({', '.join(capabilities)}); "
                f"export ${CLI_CREDENTIAL_ENV} with the hub's owner token to run it.",
                file=out,
            )
            return _EXIT_USAGE
        try:
            entry = SpeechEntry(
                admit_text_entry_session(
                    principal=principal,
                    insertion_aim=AIM_CLI_DRY_RUN,
                    config_snapshot=cfg,
                )
            )
        except SpeechSessionRefused as exc:
            print(f"refused: {exc.reason}", file=out)
            return _EXIT_USAGE

    outcome = "succeeded"
    try:
        if entry is not None:
            # Live admission + every required capability, BEFORE construction.
            entry.validate()
            # Article III.2: say where this work goes before anything is built or
            # warmed, and say it from the frozen plan.
            print(
                f"egress: {entry.plan.egress_boundary()} "
                f"(plan {entry.plan.sha256[:19]}, session {entry.session.operation_id})",
                file=out,
            )
        result = build_pipeline(
            cfg.dictation,
            project_root=project_root,
            admission=None if entry is None else entry.provider,
            lexical=entry is None,
        )

        body: list[str] = []
        if entry is None:
            body.append(
                "note: no provider-backed stage is configured "
                f"({result.runtime_detail}); provider stages are skipped."
            )
        elif result.runtime_status != "loaded":
            body.append(
                f"warning: LLM runtime unavailable ({result.runtime_detail}); "
                "running with intent-router skipped."
            )

        if project is not None:
            body.append(
                f"project: {project['name']} ({project['anchor']} @ {project['root']})"
            )
        else:
            body.append("project: (none detected)")
        body.append(
            f"resolved blocks: {len(result.blocks.blocks)} from "
            f"{result.blocks.source_path or '(no blocks file)'}"
        )
        body.append(f"runtime: {result.runtime_status} ({result.runtime_detail})")
        body.append(f"input: {text!r}")
        body.append("---")

        utt = Utterance(
            raw_text=text,
            audio_duration_s=0.0,
            transcribed_at=datetime.now(),
            project=project,
        )
        run = result.pipeline.run(utt)

        if run.short_circuited and not run.stage_results:
            body.append("(pipeline disabled — no stages executed)")
        else:
            for sr in run.stage_results:
                body.append(f"[{sr.stage_id}] elapsed_ms={sr.elapsed_ms:.2f}")
                if sr.intent is not None:
                    tag = sr.intent
                    body.append(
                        f"  intent: matched={tag.matched} block_id={tag.block_id} "
                        f"confidence={tag.confidence:.2f}"
                    )
                if sr.warnings:
                    for w in sr.warnings:
                        body.append(f"  warning: {w}")
                if sr.metadata:
                    body.append(f"  metadata: {sr.metadata}")
                body.append(f"  text: {sr.text!r}")

            body.append("---")
            body.append(f"final_text: {run.final_text!r}")
            body.append(f"total_elapsed_ms: {run.total_elapsed_ms:.2f}")
            if run.warnings:
                body.append("pipeline warnings:")
                for w in run.warnings:
                    body.append(f"  - {w}")

        # ONE bounded write, not a print-per-line loop. A loop holds the election
        # open across dozens of syscalls and — worse — a `Ctrl-C` landing
        # mid-loop leaves a truncated tail on the terminal for a run that was
        # then cancelled. Rendering to a single string first means the election
        # guards an atomic act: either the whole body lands or none of it does.
        rendered = "".join(f"{line}\n" for line in body)

        def _emit() -> None:
            out.write(rendered)
            if entry is not None:
                # Settle success before releasing the SAME election that made the
                # model-derived stdout visible. Otherwise Ctrl-C/revocation could
                # cancel the parent in the gap after a complete body was printed.
                entry.close("succeeded")

        if entry is None:
            # Nothing model-derived to elect: no provider ran.
            _emit()
            return _EXIT_OK
        published, _value = entry.fence.publish("cli dry-run stdout", _emit)
        if not published:
            outcome = "cancelled"
            print("cancelled: this dry-run session is no longer live", file=out)
            return _EXIT_USAGE
        return _EXIT_OK
    except KeyboardInterrupt:
        # Interrupt CANCELS. Nothing buffered is printed, and the parent closes
        # cancelled rather than succeeding over work the owner stopped.
        outcome = "cancelled"
        raise
    except SpeechSessionRefused as exc:
        outcome = "refused"
        print(f"refused: {exc.reason}", file=out)
        return _EXIT_USAGE
    except SpeechProviderFailure as exc:
        outcome = "failed"
        print(f"failed: {exc.contract}:{exc.reason}", file=out)
        return _EXIT_USAGE
    except BaseException:
        outcome = "failed"
        raise
    finally:
        if entry is not None:
            if outcome == "cancelled":
                entry.cancel()
            else:
                entry.close(outcome)
            if entry.indeterminate:
                # Say it on the terminal too. The stage output above (if it was
                # published) is real; what is unknown is whether this run's
                # parent receipt was written, and the owner should not have to
                # read a log file to find that out.
                print(
                    "warning: this run's session receipt could not be recorded; "
                    "its terminal state is indeterminate.",
                    file=out,
                )


# ---------------------------------------------------------------------------
# blocks
# ---------------------------------------------------------------------------

def _resolved_blocks(args) -> "LoadedBlocks":
    from ..plugins.dictation.assembly import DEFAULT_GLOBAL_BLOCKS_PATH
    from ..plugins.dictation.blocks import resolve_blocks
    from ..plugins.dictation.project_root import detect_project_for_cwd

    project_root: Optional[Path] = None
    if getattr(args, "project", None):
        project_root = Path(args.project).expanduser()
    else:
        # F-03: match dry-run — inside a project, ls/show resolve that
        # project's blocks without needing --project.
        project = detect_project_for_cwd()
        if project:
            project_root = Path(project["root"])
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

    from ..intel.providers import effective_dictation_llm

    cfg = Config.load().dictation
    effective = effective_dictation_llm(cfg.runtime)
    print(f"requested backend: {cfg.runtime.backend}", file=out)
    print(f"mlx_model: {cfg.runtime.mlx_model}", file=out)
    print(f"llama_cpp_model_path: {cfg.runtime.llama_cpp_model_path}", file=out)
    print(f"destination: {effective.profile_name or 'hub default'}", file=out)
    try:
        resolved, reason = resolve_backend(cfg.runtime.backend)
    except RuntimeUnavailableError as exc:
        print(f"resolution: unavailable — {exc}", file=out)
        return _EXIT_OK
    print(f"resolved backend: {resolved} ({reason})", file=out)

    if resolved == "openai_compatible":
        print(
            "endpoint: "
            f"({effective.base_url or 'unset'}, model={effective.model or 'unset'})",
            file=out,
        )
        return _EXIT_OK

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
