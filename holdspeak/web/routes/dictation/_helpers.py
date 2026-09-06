"""Shared, ctx-free helpers for the dictation route sub-package (HS-34-01).

These are the private helpers that several dictation route groups share —
project-context resolution, blocks-document IO, the dry-run executor, the starter
templates, and the project-doc-suggestion plumbing. They were inline closures in
the original 1,607-line `dictation.py`; the split moves them here verbatim, with
two signature tweaks so the shared in-memory suggestion store is passed
explicitly (it used to be a closure variable):
`_store_project_doc_suggestion(..., suggestions)` and
`_run_dictation_dry_run_text(..., suggestions)`.

Imports gained one relative dot — these modules sit one package deeper than the
old `web/routes/dictation.py`.
"""

from __future__ import annotations

import os
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def _resolve_project_context(project_root: Optional[str] = None) -> dict[str, Any]:
    """Return detected/manual project context for dictation project APIs."""
    from ....plugins.dictation.project_root import detect_project_for_cwd

    if project_root is None or not str(project_root).strip():
        project = detect_project_for_cwd()
        if project is None:
            raise ValueError("no project detected for current working directory")
        return dict(project)

    root = Path(str(project_root)).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"project_root must be an existing directory: {root}")

    project = detect_project_for_cwd(root)
    if project is not None:
        return dict(project)
    return {"name": root.name, "root": str(root), "anchor": "manual"}


def _resolve_blocks_target(
    scope: str,
    project_root: Optional[str] = None,
) -> tuple[Path, Optional[dict[str, Any]]]:
    """Return `(path, project_ctx)` for the requested scope.

    Raises `ValueError` with a user-facing message on bad input.
    """
    from ....plugins.dictation.assembly import DEFAULT_GLOBAL_BLOCKS_PATH

    if scope == "global":
        return DEFAULT_GLOBAL_BLOCKS_PATH, None
    if scope == "project":
        project = _resolve_project_context(project_root)
        return Path(project["root"]) / ".holdspeak" / "blocks.yaml", dict(project)
    raise ValueError(f"scope must be 'global' or 'project', got {scope!r}")


# ── project-doc-suggestion helpers (operate on a caller-owned store) ──────


def _project_suggestion_key(project: dict[str, Any]) -> str:
    return str(Path(project["root"]).resolve())


def _extract_project_doc_suggestion(stages: list[dict[str, Any]]) -> dict[str, str] | None:
    from ....project_doc_suggestions import validate_project_doc_suggestion_payload

    for stage in stages:
        metadata = stage.get("metadata") if isinstance(stage, dict) else None
        raw = metadata.get("project_doc_suggestion") if isinstance(metadata, dict) else None
        if not isinstance(raw, dict):
            continue
        try:
            return validate_project_doc_suggestion_payload(
                target_path=str(raw.get("target_path") or ""),
                rationale=str(raw.get("rationale") or ""),
                content=str(raw.get("content") or ""),
            ).to_dict()
        except ValueError:
            continue
    return None


def _store_project_doc_suggestion(
    project: dict[str, Any] | None,
    stages: list[dict[str, Any]],
    suggestions: dict[str, dict[str, str]],
    *,
    dismissed_signatures: set[str] | None = None,
) -> str:
    """Store the dry-run's suggestion (or suppress it). Returns the outcome.

    HS-39-04: a suggestion whose signature was previously dismissed in this
    session is suppressed (``"dismissed"``) so it doesn't recur.
    """
    if not project:
        return "no_project"
    key = _project_suggestion_key(project)
    suggestion = _extract_project_doc_suggestion(stages)
    if suggestion is None:
        suggestions.pop(key, None)
        return "no_suggestion"
    if dismissed_signatures is not None:
        from ....project_doc_suggestions import suggestion_signature

        sig = suggestion_signature(
            str(suggestion.get("target_path") or ""), str(suggestion.get("content") or "")
        )
        if sig in dismissed_signatures:
            suggestions.pop(key, None)
            return "dismissed"
    suggestions[key] = suggestion
    return "stored"


def _validate_project_doc_suggestion_body(payload: dict[str, Any]) -> Any:
    from ....project_doc_suggestions import validate_project_doc_suggestion_payload

    raw = payload.get("suggestion") if isinstance(payload.get("suggestion"), dict) else payload
    if not isinstance(raw, dict):
        raise ValueError("request body must include a suggestion object")
    return validate_project_doc_suggestion_payload(
        target_path=str(raw.get("target_path") or ""),
        rationale=str(raw.get("rationale") or ""),
        content=str(raw.get("content") or ""),
    )


def _write_project_doc_suggestion(root: Path, suggestion: Any) -> Path:
    target = (root / suggestion.target_path).resolve()
    resolved_root = root.resolve()
    if resolved_root not in target.parents:
        raise ValueError("target_path must stay inside the project root")
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(suggestion.content, encoding="utf-8")
    os.replace(tmp, target)
    return target


# ── .hs project-context payload helpers ──────────────────────────────────


def _project_hs_payload(project: dict[str, Any]) -> dict[str, Any]:
    from ....agent_context import (
        DEFAULT_CONTEXT_HARD_FILE_MAX_BYTES,
        HS_CONTEXT_FILES,
        load_hs_project_context,
    )

    root = Path(project["root"])
    hs_dir = root / ".hs"
    loaded = load_hs_project_context(
        root,
        max_bytes=DEFAULT_CONTEXT_HARD_FILE_MAX_BYTES * 8,
        per_file_max_bytes=DEFAULT_CONTEXT_HARD_FILE_MAX_BYTES,
    )
    loaded_files = loaded.get("files") if isinstance(loaded.get("files"), dict) else {}
    files: dict[str, dict[str, Any]] = {}
    for name in (*HS_CONTEXT_FILES, "ignore"):
        path = hs_dir / name
        loaded_entry = loaded_files.get(name) if isinstance(loaded_files, dict) else None
        entry = loaded_entry if isinstance(loaded_entry, dict) else {}
        files[name] = {
            "path": str(path),
            "exists": path.is_file(),
            "actual_path": str(entry.get("path") or path),
            "content": str(entry.get("content") or ""),
            "source": str(entry.get("source") or "directory"),
            "read_only": bool(entry.get("read_only")),
            "truncated": bool(entry.get("truncated")),
        }
    return {
        "detected": dict(project),
        "context_dir": str(hs_dir),
        "exists": bool(loaded.get("exists")),
        "context_dir_exists": hs_dir.is_dir(),
        "files": files,
        "flat_files": loaded.get("flat_files") if isinstance(loaded.get("flat_files"), dict) else {},
        "skipped": loaded.get("skipped") if isinstance(loaded.get("skipped"), list) else [],
        "warnings": loaded.get("warnings") if isinstance(loaded.get("warnings"), list) else [],
        "write_policy": loaded.get("write_policy") if isinstance(loaded.get("write_policy"), dict) else {},
    }


def _write_project_hs_files(root: Path, files: dict[str, Any]) -> None:
    from ....agent_context import HS_CONTEXT_FILES

    allowed = set(HS_CONTEXT_FILES) | {"ignore"}
    unknown = sorted(set(files) - allowed)
    if unknown:
        raise ValueError(f"unknown .hs file(s): {unknown}; allowed: {sorted(allowed)}")
    hs_dir = root / ".hs"
    hs_dir.mkdir(parents=True, exist_ok=True)
    for name, raw_content in files.items():
        if not isinstance(raw_content, str):
            raise ValueError(f".hs/{name} content must be a string")
        if len(raw_content.encode("utf-8")) > 128_000:
            raise ValueError(f".hs/{name} is too large; max is 128KB")
        path = hs_dir / name
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(raw_content, encoding="utf-8")
        os.replace(tmp, path)


# ── blocks-document IO + starter templates ───────────────────────────────


def _read_blocks_document(path: Path) -> tuple[dict[str, Any], bool]:
    """Read `path` as a raw YAML mapping; return empty default if missing."""
    import yaml

    if not path.exists():
        return {"version": 1, "default_match_confidence": 0.6, "blocks": []}, False
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if data is None:
        return {"version": 1, "default_match_confidence": 0.6, "blocks": []}, True
    if not isinstance(data, dict):
        raise ValueError(
            f"{path}: top-level YAML must be a mapping, got {type(data).__name__}"
        )
    data.setdefault("version", 1)
    data.setdefault("default_match_confidence", 0.6)
    data.setdefault("blocks", [])
    return data, True


_STARTER_BLOCK_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        # HS-47-03: a starter block that consumes a Project Fact, so a fact set
        # in the KB actually shows up in dictation out of the box (otherwise
        # facts have nothing referencing them). The {project.kb.stack}
        # placeholder is left unresolved -- and the injection skipped -- until
        # the user fills in the `stack` fact, so it is safe by default.
        "id": "project_facts_context",
        "title": "Project facts context",
        "description": "Append your project's stack fact to AI-assistant prompts so the copilot always has it. Set the `stack` fact in Project Facts to see it appear.",
        "sample_utterance": "help me refactor the payments module",
        "requires_project": True,
        "block": {
            "id": "project_facts_context",
            "description": "User is dictating a prompt for an AI assistant and wants the project's facts attached.",
            "match": {
                "examples": [
                    "help me refactor the payments module",
                    "write a test for this endpoint",
                    "explain how this service is wired together",
                ],
                "negative_examples": ["remind me to buy milk"],
                "threshold": 0.7,
            },
            "inject": {
                "mode": "append",
                "template": "\n\nProject stack: {project.kb.stack}",
            },
        },
    },
    {
        "id": "ai_prompt_context",
        "title": "AI prompt context",
        "description": "Append the selected project name and clear instruction context to AI-assistant prompts.",
        "sample_utterance": "help me design the settings panel",
        "requires_project": True,
        "block": {
            "id": "ai_prompt_context",
            "description": "User is dictating a prompt for an AI assistant and wants project context attached.",
            "match": {
                "examples": [
                    "Claude help me write a function for this project",
                    "build a prompt for the settings panel",
                    "ask the assistant to debug this module",
                ],
                "negative_examples": ["remind me to buy milk"],
                "threshold": 0.7,
            },
            "inject": {
                "mode": "append",
                "template": "\n\nProject: {project.name}\nUse the selected project's constraints and local context when answering.",
            },
        },
    },
    {
        "id": "action_item",
        "title": "Action item",
        "description": "Turn short task dictation into a consistent action-item line.",
        "sample_utterance": "follow up with Sam about the launch checklist",
        "requires_project": False,
        "block": {
            "id": "action_item",
            "description": "User is capturing a task or follow-up item.",
            "match": {
                "examples": [
                    "follow up with Sam about the launch checklist",
                    "remember to review the pull request",
                    "make a task to update the docs",
                ],
                "negative_examples": ["write a paragraph about the architecture"],
                "threshold": 0.7,
            },
            "inject": {
                "mode": "replace",
                "template": "Action item: {raw_text}",
            },
        },
    },
    {
        "id": "concise_note",
        "title": "Concise note",
        "description": "Format quick thoughts as a clean note that is easy to scan later.",
        "sample_utterance": "the retry worker should surface its next scheduled run",
        "requires_project": False,
        "block": {
            "id": "concise_note",
            "description": "User is dictating a concise note or implementation observation.",
            "match": {
                "examples": [
                    "note that the retry worker needs a status line",
                    "capture this implementation idea",
                    "write down this design concern",
                ],
                "negative_examples": ["send an email to Alex"],
                "threshold": 0.7,
            },
            "inject": {
                "mode": "replace",
                "template": "Note: {raw_text}",
            },
        },
    },
    {
        "id": "code_review_focus",
        "title": "Code review focus",
        "description": "Append a review rubric for correctness, edge cases, and tests.",
        "sample_utterance": "review the queue processing change",
        "requires_project": False,
        "block": {
            "id": "code_review_focus",
            "description": "User is dictating a code-review request.",
            "match": {
                "examples": [
                    "review the queue processing change",
                    "look over this implementation for bugs",
                    "check this diff for edge cases",
                ],
                "negative_examples": ["start a meeting recording"],
                "threshold": 0.7,
            },
            "inject": {
                "mode": "append",
                "template": "\n\nReview focus: correctness, edge cases, regressions, and missing tests.",
            },
        },
    },
)

_STARTER_PROJECT_KB: dict[str, Any] = {
    "stack": None,
    "task_focus": None,
    "constraints": None,
}


def _starter_template(template_id: str) -> Optional[dict[str, Any]]:
    for template in _STARTER_BLOCK_TEMPLATES:
        if template["id"] == template_id:
            return deepcopy(template)
    return None


def _unique_block_id(base_id: str, document: dict[str, Any]) -> str:
    existing = {
        b.get("id")
        for b in document.get("blocks", [])
        if isinstance(b, dict)
    }
    if base_id not in existing:
        return base_id
    index = 2
    while f"{base_id}_{index}" in existing:
        index += 1
    return f"{base_id}_{index}"


def _block_summary(path: Path) -> dict[str, Any]:
    from ....plugins.dictation.blocks import BlockConfigError, load_blocks_yaml

    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "valid": True,
            "count": 0,
            "error": None,
        }
    try:
        loaded = load_blocks_yaml(path)
    except BlockConfigError as exc:
        return {
            "path": str(path),
            "exists": True,
            "valid": False,
            "count": 0,
            "error": str(exc),
        }
    return {
        "path": str(path),
        "exists": True,
        "valid": True,
        "count": len(loaded.blocks),
        "error": None,
    }


# ── dry-run executor + its serialization helpers ─────────────────────────


def _serialize_intent(intent: Any) -> Optional[dict[str, Any]]:
    if intent is None:
        return None
    return {
        "matched": bool(getattr(intent, "matched", False)),
        "block_id": getattr(intent, "block_id", None),
        "confidence": float(getattr(intent, "confidence", 0.0)),
        "raw_label": getattr(intent, "raw_label", None),
        "extras": dict(getattr(intent, "extras", {}) or {}),
    }


def _serialize_stage_result(result: Any) -> dict[str, Any]:
    from ....dictation_telemetry import summarize_stage

    payload = {
        "stage_id": str(getattr(result, "stage_id", "")),
        "elapsed_ms": float(getattr(result, "elapsed_ms", 0.0)),
        "intent": _serialize_intent(getattr(result, "intent", None)),
        "warnings": list(getattr(result, "warnings", []) or []),
        "metadata": dict(getattr(result, "metadata", {}) or {}),
        "text": str(getattr(result, "text", "")),
    }
    payload["telemetry"] = summarize_stage(payload)
    return payload


def _open_text_entry(
    request: Any, insertion_aim: str, *, config_snapshot: Any = None
) -> tuple[Any, Any]:
    """ONE fresh, credential-authenticated text-entry session for this request.

    HS-131-15. Three properties this seam exists to guarantee:

    * **Authority comes only from the credential middleware.** The principal is
      ``request.state.principal`` and nothing else — never a payload field, never
      the request's network location, never a synthesized owner. A request that
      arrived without a principal refuses by name inside ``admit_*``.
    * **The session is always fresh.** Four different routes share the pipeline
      helper; each opens its own short parent and never joins the browser open-mic
      interval, whose authority belongs to a visible microphone the caller is not
      holding.
    * **One snapshot.** The ``Config`` returned here is the SAME object the plan
      was frozen from and the same one assembly builds from, so mutation after
      admission cannot retarget construction, dispatch, egress, or publication.

    Returns ``(config_snapshot, entry)``; the caller owns the entry's terminal
    outcome.
    """
    from ....config import Config
    from ....db import get_database
    from ....speech_session import SpeechEntry, admit_text_entry_session

    config_snapshot = Config.load() if config_snapshot is None else config_snapshot
    session = admit_text_entry_session(
        principal=getattr(getattr(request, "state", None), "principal", None),
        insertion_aim=insertion_aim,
        config_snapshot=config_snapshot,
        registry_snapshot=get_database(),
    )
    return config_snapshot, SpeechEntry(session)


#: How often a cancellable preview asks whether its client is still there.
_DISCONNECT_POLL_SECONDS = 0.25


async def _watch_disconnect(request: Any, entry: Any) -> None:
    """Cancel ``entry`` as soon as this request's client goes away.

    The ASGI server does NOT reliably cancel a handler when the socket closes —
    it depends on the server, the protocol, and whether the handler is awaiting
    something cancellable at that moment. A preview that relied on handler
    cancellation therefore kept a real classify/rewrite running with a live
    session behind it, and its publication could still land minutes after the
    person had closed the tab. So the disconnect is OBSERVED, not assumed:
    ``request.is_disconnected()`` is polled, and the first observation cancels
    the session. The worker thread keeps running (a native model call is not
    interruptible), but the fence is now closed, so it loses the publication
    election and nothing it produced is written or returned.
    """
    import asyncio

    probe = getattr(request, "is_disconnected", None)
    if not callable(probe):
        return
    while True:
        # Probe BEFORE the first sleep. A lexical or already-warm preview can
        # publish in less than one polling interval, and ASGI servers such as
        # Uvicorn report connection_lost without cancelling the application task.
        try:
            gone = bool(await probe())
        except Exception:  # noqa: BLE001 - an unreadable socket is not a cancel
            return
        if gone:
            try:
                # Terminal cancellation performs SQLite transactions and may wait
                # behind a publication election. Keep that blocking work off the
                # ASGI loop; the worker still contends on the same lock, so exactly
                # one of cancellation or publication wins.
                await asyncio.to_thread(entry.cancel)
            except Exception as exc:  # noqa: BLE001 - best-effort teardown
                from ....logging_config import get_logger

                get_logger("web.routes.dictation").error(
                    f"Preview cancellation after disconnect failed: {exc}"
                )
            return
        await asyncio.sleep(_DISCONNECT_POLL_SECONDS)


async def _run_cancellable_entry(request: Any, insertion_aim: str, work: Any) -> Any:
    """Run ``work(config_snapshot, entry)`` off the loop under a fresh entry.

    A provider-free snapshot takes the lexical branch: ``entry`` is ``None`` and
    no parent/watcher/terminal I/O exists. For provider-bearing work, three things
    happen here that a bare ``await asyncio.to_thread(...)`` did not:

    * **Off the event loop, always.** A mesh-routed rewrite WAITS on the relay
      queue, and this loop is what serves the worker's claim polls. Journal replay
      and template preview used to call the helper inline and could deadlock a
      mesh-backed pipeline against its own poller.
    * **Disconnect actively cancels.** These entries are cancellable PREVIEWS, not
      committed effects, and a watcher polls ``request.is_disconnected()`` rather
      than trusting the server to cancel this coroutine. Either route to
      cancellation — the watcher or a real ``CancelledError`` — closes the fence
      before the worker can publish.
    * **The terminal outcome is reported, not swallowed** — on BOTH exits. If the
      parent's close could not be persisted, the success payload says so, and so
      does the refusal or failure that propagates instead of one. A run that
      refused AND could not record its own terminal state is two facts, and the
      caller is owed both; reporting only the first is the same swallow the
      success path already fixed.
    """
    import asyncio

    from ....config import Config
    from ....speech_session import pipeline_provider_capabilities

    config_snapshot = Config.load()
    if not pipeline_provider_capabilities(config_snapshot):
        # Intentionally lexical: no provider runtime, parent, child, disconnect
        # watcher, or terminal receipt exists. This is the same contract as CLI
        # dry-run; only the caller's text and lexical stages run off-loop.
        return await asyncio.to_thread(work, config_snapshot, None)

    config_snapshot, entry = _open_text_entry(
        request, insertion_aim, config_snapshot=config_snapshot
    )
    watcher = asyncio.ensure_future(_watch_disconnect(request, entry))
    try:
        try:
            with entry:
                payload = await asyncio.to_thread(work, config_snapshot, entry)
        except BaseException as exc:
            # `with entry` has already run its terminal close by the time this
            # handler sees the exception, so `indeterminate` is settled. Ride the
            # marker on the exception (a fixed string, never content) so the
            # route's named-refusal response can carry it too.
            mark_session_terminal(exc, entry)
            raise
    finally:
        watcher.cancel()
    if entry.indeterminate and isinstance(payload, dict):
        payload["session_terminal"] = "indeterminate"
    return payload


def mark_session_terminal(exc: BaseException, entry: Any) -> None:
    """Stamp an unknown parent terminal state onto a propagating safe exception."""
    if entry is not None and getattr(entry, "indeterminate", False):
        try:
            exc.session_terminal = "indeterminate"  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001 - a slotted exception is not worth failing over
            pass


def session_terminal_of(source: Any) -> dict[str, str]:
    """``{"session_terminal": "indeterminate"}`` when known, else ``{}``.

    A merge-in fragment so every response shape can carry the marker without each
    call site re-deriving it. Content-free by construction: the only value it ever
    produces is the fixed string.
    """
    if str(getattr(source, "session_terminal", "") or "") == "indeterminate":
        return {"session_terminal": "indeterminate"}
    if getattr(source, "indeterminate", False):
        return {"session_terminal": "indeterminate"}
    return {}


def _run_dictation_dry_run_text(
    text: str,
    project_root_override: Optional[str],
    target_hints: Optional[dict[str, Any]] = None,
    *,
    suggestions: dict[str, dict[str, str]],
    config_snapshot: Any,
    admission: Any,
    fence: Any,
    terminal_entry: Any = None,
    corrections: Any = None,
    dismissed_signatures: set[str] | None = None,
    telemetry: Any = None,
    journal: Any = None,
    activity_context: Optional[dict[str, Any]] = None,
    journal_source: str = "dry_run",
) -> dict[str, Any]:
    """Execute the browser dry-run path for already-validated text.

    ``activity_context`` (HSM-18-05): a pre-built activity dict (the runner's
    ``build_activity_context(...).to_dict()`` shape) folded into the utterance so
    the rewrite can ground in a selected record — the remote relay passes it when
    a "Dictate with this" pin is pending. ``None`` keeps the historical
    target-only activity dict byte-identical.

    ``journal_source`` (HS-112-02): which lane the run belongs to. The rich
    pipeline is shared by the REHEARSE preview (``dry_run``) and by a real
    delivery (``dictation``) — one helper, one journal schema, an honest row.
    Only an explicit rehearsal writes a ``dry_run`` entry.

    HS-131-15 — ``config_snapshot`` is caller-owned; ``admission`` and ``fence``
    are REQUIRED exactly when that frozen snapshot selects a provider capability,
    and MUST be absent when it is intentionally lexical. This helper mints no
    session and reads no ambient one; it takes no principal, parent id, warrant,
    placement, client profile, or revision, so a payload cannot choose authority
    or where the model runs. A provider path proves its handed admission is a
    live, fresh text-entry admission before construction, and every model-derived
    publication — returned body, stored suggestion, journal row — goes through
    that session's election. A lexical path constructs no runtime and mints no
    parent or child.

    A cancellable preview also passes its ``terminal_entry``. Its final publication
    and successful parent close then happen inside ONE election: publication-first
    cannot be overwritten by a disconnect watcher. Committed remote delivery omits
    it because that session must remain live through the later pre-delivery gate.
    """
    from ....dictation_telemetry import summarize_dry_run
    from ....plugins.dictation.assembly import DEFAULT_GLOBAL_BLOCKS_PATH, build_pipeline
    from ....plugins.dictation.contracts import Utterance
    from ....speech_session import (
        ENTRY_SESSION_REQUIRED,
        SpeechSessionRefused,
        pipeline_provider_capabilities,
        require_entry_admission,
    )
    from ....target_profile import (
        apply_model_assisted_target,
        apply_target_correction,
        collect_active_target_hints,
        detect_target_profile_with_override,
    )

    capabilities = pipeline_provider_capabilities(config_snapshot)
    lexical = not capabilities
    # Before construction: provider work needs OUR live, fresh entry admission.
    # An intentionally provider-free configuration is the opposite contract: it
    # mints no parent and constructs no runtime.
    if lexical:
        if admission is not None or fence is not None or terminal_entry is not None:
            raise SpeechSessionRefused(ENTRY_SESSION_REQUIRED)
        egress_boundary = "local"
    else:
        require_entry_admission(admission, fence)
        # Execution proof comes only from the same frozen route members every
        # child dispatches under.  A text entry has no transcription route, so
        # the ProviderAdmission accessor must still see its provider members.
        egress_boundary = str(admission.egress_boundary)
        if terminal_entry is not None and (
            getattr(terminal_entry, "provider", None) is not admission
            or getattr(terminal_entry, "fence", None) is not fence
        ):
            raise SpeechSessionRefused(ENTRY_SESSION_REQUIRED)

    def _elect_publication(stage: str, publication: Any) -> tuple[bool, Any]:
        """Publish, then settle a cancellable entry before releasing its election."""

        def _publish_and_settle() -> Any:
            payload = publication()
            if terminal_entry is not None:
                terminal_entry.close("succeeded")
            return payload

        if lexical:
            return True, _publish_and_settle()
        return fence.publish(stage, _publish_and_settle)

    def _lost(stage: str) -> SpeechSessionRefused:
        from ....speech_session import SESSION_NOT_LIVE

        return SpeechSessionRefused(fence.reason() or SESSION_NOT_LIVE, stage)

    cfg = config_snapshot.dictation
    # HS-39-02: only consult corrections when the feature is on; a None snapshot
    # keeps routing + target detection byte-identical.
    correction_snapshot = (
        corrections.snapshot()
        if corrections is not None and getattr(cfg.pipeline, "corrections_enabled", False)
        else None
    )
    try:
        project = _resolve_project_context(project_root_override)
    except ValueError:
        if project_root_override:
            raise
        project = None
    project_root = Path(project["root"]) if project else None

    if not cfg.pipeline.enabled:
        warnings = ["dictation pipeline disabled"]

        def _publish_disabled() -> dict[str, Any]:
            # F-07: the journal follows `journal_enabled`, not the pipeline gate —
            # a pipeline-off dry-run records a passthrough row so the review
            # surface reflects real activity. Best-effort like every journal write.
            journal_id = None
            if journal is not None:
                from ....plugins.dictation.journal import passthrough_run

                recorded = journal.record(
                    passthrough_run(text),
                    source=journal_source,
                    transcript=text,
                    enabled=bool(getattr(cfg.pipeline, "journal_enabled", True)),
                    retention=int(getattr(cfg.pipeline, "journal_retention", 500)),
                )
                journal_id = getattr(recorded, "id", None)
            return {
                "project": dict(project) if project else None,
                "egress_boundary": egress_boundary,
                "runtime_status": "disabled",
                "runtime_detail": "dictation pipeline disabled (opt-in)",
                "blocks_count": 0,
                "stages": [],
                "final_text": text,
                # HS-176-02 (N2): the transcript AS HEARD, before any rewrite.
                # The TEXT teach well pre-fills from this, and the word-level
                # diff runs heard(raw) vs said(his edit) — a key harvested from
                # `final_text` would be matched against a string it never equals.
                # Pipeline off: nothing rewrote and no rule fired.
                "raw_text": text,
                "corrections_applied": [],
                "total_elapsed_ms": 0.0,
                "warnings": warnings,
                "journal_id": journal_id,
                "learning": None,
                "telemetry": summarize_dry_run(
                    runtime_status="disabled",
                    runtime_detail="dictation pipeline disabled (opt-in)",
                    stages=[],
                    warnings=warnings,
                    total_elapsed_ms=0.0,
                    max_total_latency_ms=cfg.pipeline.max_total_latency_ms,
                ),
            }

        # A disabled pipeline is not an exemption from the election: a cancelled
        # session still writes no journal row and returns no body.
        won, payload = _elect_publication(
            "dictation entry (pipeline disabled)", _publish_disabled
        )
        if not won:
            raise _lost("dictation entry (pipeline disabled)")
        return payload

    # Runtime construction and cancellation elect one winner. A preceding
    # liveness check was only a snapshot: the worker could then build a runtime
    # after the disconnect watcher had cancelled this entry. Construction itself
    # is bounded by the fence; no model attempt occurs here (admitted construction
    # forces warm_on_start=False), and each later physical attempt still mints its
    # own child.
    construction = lambda: build_pipeline(
        cfg,
        project_root=project_root,
        global_blocks_path=DEFAULT_GLOBAL_BLOCKS_PATH,
        corrections=correction_snapshot,
        on_run=(telemetry.record_run if telemetry is not None else None),
        admission=admission,
        lexical=lexical,
    )

    if lexical:
        result = construction()
    else:
        constructed, result = fence.publish(
            "dictation entry construction", construction
        )
        if not constructed:
            raise _lost("dictation entry construction")
        assert result is not None
    resolved_hints = target_hints or collect_active_target_hints()
    target_profile = detect_target_profile_with_override(
        resolved_hints,
        cfg.pipeline.target_profile_override,
    )
    target_profile = apply_target_correction(
        target_profile, text=text, corrections=correction_snapshot
    )
    target_profile = apply_model_assisted_target(
        target_profile,
        runtime=result.runtime,
        hints=resolved_hints,
        text=text,
        enabled=bool(getattr(cfg.pipeline, "target_detect_llm_enabled", False)),
        below_confidence=float(getattr(cfg.pipeline, "target_detect_llm_below", 0.8)),
    )
    # Model-assisted target detection is a provider-bearing continuation; check
    # the fence again before the pipeline's own provider work begins.
    if not lexical and fence.discarded("dictation entry pipeline"):
        raise _lost("dictation entry pipeline")
    activity = dict(activity_context) if activity_context else {}
    activity["target"] = target_profile.to_dict()
    run = result.pipeline.run(
        Utterance(
            raw_text=text,
            audio_duration_s=0.0,
            transcribed_at=datetime.now(),
            project=project,
            activity=activity,
        )
    )
    # HS-45-01: journal the dry-run as a side-channel (best-effort; never alters
    # the returned result). Tagged `source='dry_run'` so the no-mic path is
    # first-class. A recorder with no repository (bare server) is a no-op.
    # HS-45-03: the returned record's id flows back so the result panel can
    # offer an in-the-moment "fix it here" that attaches to this entry.
    # HS-48-02: the inline "learned from N similar" signal for this utterance.
    # Computed from the same snapshot routing used (None when corrections are
    # off -> no signal), over the journal as it stood *before* this run, so the
    # count reflects past utterances rather than counting this one. Quiet when
    # nothing matches.
    learning_signal = None
    if correction_snapshot:
        from ....dictation_learning import best_correction_signal, reach_by_gist_map

        repo = getattr(journal, "repository", None) if journal is not None else None
        past_transcripts = (
            [r.transcript for r in repo.recent()] if repo is not None else []
        )
        reach_map = reach_by_gist_map(correction_snapshot, past_transcripts)
        learning_signal = best_correction_signal(text, correction_snapshot, reach_map)

    def _publish() -> dict[str, Any]:
        """Every model-derived output of this run, under one election.

        The journal row, the stored project-doc suggestion, and the returned body
        are ONE publication. Splitting them would let a cancellation land between
        a written journal row and a suppressed response — a persisted claim about
        work whose result the caller never receives.
        """
        journal_id = None
        if journal is not None:
            recorded = journal.record(
                run,
                source=journal_source,
                transcript=text,
                target_profile=target_profile,
                project_root=project_root,
                enabled=bool(getattr(cfg.pipeline, "journal_enabled", True)),
                retention=int(getattr(cfg.pipeline, "journal_retention", 500)),
            )
            journal_id = getattr(recorded, "id", None)
        stages = [_serialize_stage_result(sr) for sr in run.stage_results]
        suggestion_status = _store_project_doc_suggestion(
            project, stages, suggestions, dismissed_signatures=dismissed_signatures
        )
        warnings = list(run.warnings)
        return {
            "project": dict(project) if project else None,
            "egress_boundary": egress_boundary,
            "target": target_profile.to_dict(),
            "suggestion_status": suggestion_status,
            "journal_id": journal_id,
            "learning": learning_signal,
            "runtime_status": result.runtime_status,
            "runtime_detail": result.runtime_detail,
            "blocks_count": len(result.blocks.blocks),
            "stages": stages,
            "final_text": run.final_text,
            # HS-176-02 (N2): the transcript AS HEARD — the exact string the
            # `text` rules are applied to at the head of `Pipeline.run` — beside
            # the landed text, plus the ids of the rules that actually fired on
            # this run (R2: the APPLIED chip renders from this stored fact, never
            # from a read-time "would match"). `getattr` because `PipelineRun`'s
            # field is additive and the passthrough fakes a run (C5 note).
            "raw_text": text,
            "corrections_applied": _correction_ids(
                getattr(run, "corrections_applied", None)
            ),
            "total_elapsed_ms": float(run.total_elapsed_ms),
            "warnings": warnings,
            "telemetry": summarize_dry_run(
                runtime_status=result.runtime_status,
                runtime_detail=result.runtime_detail,
                stages=stages,
                warnings=warnings,
                total_elapsed_ms=float(run.total_elapsed_ms),
                max_total_latency_ms=cfg.pipeline.max_total_latency_ms,
            ),
        }

    won, payload = _elect_publication("dictation entry publication", _publish)
    if not won:
        raise _lost("dictation entry publication")
    return payload


def _runtime_readiness(cfg: Any) -> dict[str, Any]:
    from ....dictation_telemetry import summarize_readiness_telemetry
    from ....plugins.dictation import runtime as runtime_module
    from ....plugins.dictation.runtime_counters import get_counters, get_session_status

    if not cfg.pipeline.enabled:
        payload = {
            "status": "disabled",
            "requested_backend": cfg.runtime.backend,
            "resolved_backend": None,
            "detail": "dictation pipeline disabled",
            "model_path": None,
            "model_exists": False,
            "counters": get_counters(),
            "session": get_session_status(),
        }
        payload["telemetry"] = summarize_readiness_telemetry(
            runtime_payload=payload,
            max_total_latency_ms=cfg.pipeline.max_total_latency_ms,
        )
        return payload

    try:
        resolved_backend, reason = runtime_module.resolve_backend(cfg.runtime.backend)
    except runtime_module.RuntimeUnavailableError as exc:
        from ....plugins.dictation.guidance import runtime_guidance

        payload = {
            "status": "unavailable",
            "requested_backend": cfg.runtime.backend,
            "resolved_backend": None,
            "detail": str(exc),
            "model_path": None,
            "model_exists": False,
            "guidance": runtime_guidance(
                kind="unavailable",
                requested_backend=cfg.runtime.backend,
            ),
            "counters": get_counters(),
            "session": get_session_status(),
        }
        payload["telemetry"] = summarize_readiness_telemetry(
            runtime_payload=payload,
            max_total_latency_ms=cfg.pipeline.max_total_latency_ms,
        )
        return payload

    if resolved_backend == "openai_compatible":
        from ....intel.providers import effective_dictation_llm
        from ....plugins.dictation.guidance import runtime_guidance

        effective = effective_dictation_llm(cfg.runtime)
        payload = {
            "status": "available",
            "requested_backend": cfg.runtime.backend,
            "resolved_backend": resolved_backend,
            "detail": (
                f"endpoint={effective.base_url or 'unset'}; "
                f"model={effective.model or 'unset'}"
            ),
            "model_path": None,
            "model_exists": True,
            "guidance": runtime_guidance(
                kind="endpoint_config",
                requested_backend=cfg.runtime.backend,
                resolved_backend=resolved_backend,
            ),
            "counters": get_counters(),
            "session": get_session_status(),
        }
        payload["telemetry"] = summarize_readiness_telemetry(
            runtime_payload=payload,
            max_total_latency_ms=cfg.pipeline.max_total_latency_ms,
        )
        return payload

    model_path = Path(
        cfg.runtime.mlx_model
        if resolved_backend == "mlx"
        else cfg.runtime.llama_cpp_model_path
    ).expanduser()
    model_exists = model_path.exists()
    guidance = None
    if not model_exists:
        from ....plugins.dictation.guidance import runtime_guidance

        guidance = runtime_guidance(
            kind="missing_model",
            requested_backend=cfg.runtime.backend,
            resolved_backend=resolved_backend,
            model_path=model_path,
        )
    payload = {
        "status": "available" if model_exists else "missing_model",
        "requested_backend": cfg.runtime.backend,
        "resolved_backend": resolved_backend,
        "detail": reason if model_exists else f"model file missing at {model_path}",
        "model_path": str(model_path),
        "model_exists": model_exists,
        "guidance": guidance,
        "counters": get_counters(),
        "session": get_session_status(),
    }
    payload["telemetry"] = summarize_readiness_telemetry(
        runtime_payload=payload,
        max_total_latency_ms=cfg.pipeline.max_total_latency_ms,
    )
    return payload


# ── HS-176-02: the teach seam (the ONE server-side diff + refusal vocabulary) ──
#
# The `text` correction kind teaches from a pair: what the mic HEARD (the raw
# transcript, now served on the run response beside `final_text`) and what the
# owner SAID (his edit). The word-level diff runs HERE, on the server, so both
# teach routes — `POST /api/dictation/corrections` and
# `POST /api/dictation/journal/{entry_id}/correct` — produce identical rules.
#
# The ruled outcomes (assets/settled-design-speak-loop.md D2(a), rulings R1/N3):
#   * no difference                          -> nothing stored, reason `no_change`
#   * exactly one contiguous differing span,
#     at most half the heard tokens          -> a WORD rule (key = the heard
#                                               span, value = the said span)
#   * more than one span, or a span over
#     half the tokens                        -> a WHOLE-PHRASE rule (key = the
#                                               full heard text, value = the
#                                               full said text)
#
# N3: `Utterance.raw_text` is post-TextProcessor on the capture path, so spoken
# punctuation is already attached to the token (`postgress,`). Every stored span
# is therefore stripped of leading/trailing punctuation before it is stored, and
# the key is stored lowercased (matching is case-insensitive; the store's own
# matcher is case-preserving on the first letter).

#: Named refusal reasons on the teach wire. The face turns these into
#: `REFUSED · SECRET` / `REFUSED · ONE WORD` / `NO CHANGE` (R4, R7, R8).
TEACH_NO_CHANGE = "no_change"
TEACH_EMPTY = "empty"
TEACH_SECRET = "secret"
TEACH_ONE_WORD = "one_word"
TEACH_REFUSED = "refused"

#: Leading/trailing characters stripped from a stored span (N3).
_TEACH_PUNCTUATION = "\"'`.,;:!?()[]{}<>…-–—*_/\\"


def _strip_span(span: str) -> str:
    """One whitespace-collapsed line, stripped of leading/trailing punctuation."""
    return " ".join(str(span or "").split()).strip(_TEACH_PUNCTUATION).strip()


def diff_text_correction(heard: str, said: str) -> dict[str, Any]:
    """The ruled word-level diff of `heard` vs `said`.

    Returns ``{"rule": {"key", "value", "shape"}, "reason": None}`` when
    something should be stored, or ``{"rule": None, "reason": "<token>"}`` when
    nothing should be — `no_change` when the two texts agree, `empty` when a
    side is blank. `shape` is ``"word"`` or ``"phrase"`` (diagnostic only; the
    stored kind is `text` either way).
    """
    from difflib import SequenceMatcher

    heard_norm = " ".join(str(heard or "").split())
    said_norm = " ".join(str(said or "").split())
    if not heard_norm or not said_norm:
        return {"rule": None, "reason": TEACH_EMPTY}
    if heard_norm == said_norm:
        return {"rule": None, "reason": TEACH_NO_CHANGE}

    heard_tokens = heard_norm.split()
    said_tokens = said_norm.split()
    spans = [
        op
        for op in SequenceMatcher(
            a=heard_tokens, b=said_tokens, autojunk=False
        ).get_opcodes()
        if op[0] != "equal"
    ]

    key_raw = ""
    value = ""
    shape = "phrase"
    if len(spans) == 1:
        _tag, i1, i2, j1, j2 = spans[0]
        heard_span = " ".join(heard_tokens[i1:i2])
        said_span = " ".join(said_tokens[j1:j2])
        # A pure insertion has no heard span and a pure deletion no said span —
        # neither can be keyed as a word rule. A span over half the heard tokens
        # is the sentence, not a word.
        if heard_span and said_span and (i2 - i1) * 2 <= len(heard_tokens):
            key_raw = _strip_span(heard_span)
            value = _strip_span(said_span)
            shape = "word"
    if shape != "word" or not key_raw or not value:
        key_raw = _strip_span(heard_norm)
        value = _strip_span(said_norm)
        shape = "phrase"

    if not key_raw or not value:
        return {"rule": None, "reason": TEACH_EMPTY}
    if key_raw == value:
        # Only whitespace or edge punctuation differed: the rule would be a
        # no-op, so nothing is written and the receipt says so.
        return {"rule": None, "reason": TEACH_NO_CHANGE}
    return {"rule": {"key": key_raw.lower(), "value": value, "shape": shape}, "reason": None}


def teach_refusal_reason(kind: str, key: str, value: str) -> str:
    """The named reason `CorrectionStore.record` refused a teach (R4/R7).

    `CorrectionStore.record` names its own refusal (`kind` / `empty` / `secret` /
    `one_word`) and `record_correction` passes that through verbatim — the ONE
    vocabulary. This is the fallback for a store that predates that contract:
    the same guards, mirrored, so the wire can still NAME the refusal instead of
    smoothing it (Article V.3). `refused` when no guard explains the no-op.
    """
    from ....project_doc_suggestions import looks_like_secret

    clean_key = " ".join(str(key or "").split())
    clean_value = str(value or "").strip()
    if not clean_key or not clean_value:
        return TEACH_EMPTY
    try:
        if looks_like_secret(clean_key) or looks_like_secret(clean_value):
            return TEACH_SECRET
    except Exception:  # pragma: no cover - the secret check must never raise here
        pass
    # The one-word refusal binds the ROUTING kinds only: a `text` rule is
    # exact-phrase, so a single token is legal and precise (R7).
    if kind in ("intent", "target") and len(clean_key.split()) < 2:
        return TEACH_ONE_WORD
    return TEACH_REFUSED


def _newest_correction_id(store: Any) -> Optional[int]:
    """The durable id of the newest stored correction, or None."""
    try:
        items = store.list_for_display()
    except Exception:  # pragma: no cover - the id linkage is best-effort
        return None
    if items and items[0].get("id") is not None:
        try:
            return int(items[0]["id"])
        except (TypeError, ValueError):
            return None
    return None


def record_correction(
    store: Any, kind: str, key: str, value: str
) -> tuple[bool, Optional[int], Optional[str]]:
    """Teach one correction; return ``(recorded, stored id, refusal reason)``.

    R4: the id and the refusal's NAME both come from `CorrectionStore.record`,
    which returns a `RecordOutcome` (`stored` / `correction_id` / `refusal`).
    No more guessing the id from `list_for_display()[0]` — on a refusal that was
    somebody else's rule entirely.

    The older return shapes are still honoured so a bare/older store cannot
    500 the route: a plain `bool` reads the id back from the durable list and
    ONLY when the record was accepted (which is itself the R4 fix), and the
    refusal is then re-derived from the store's own guards.
    """
    outcome = store.record(kind, key, value)
    stored = getattr(outcome, "stored", None)
    if stored is not None:  # the HS-176-02 `RecordOutcome`
        if not bool(stored):
            reason = getattr(outcome, "refusal", None)
            return False, None, str(reason) if reason else TEACH_REFUSED
        correction_id = getattr(outcome, "correction_id", None)
        return True, (int(correction_id) if correction_id is not None else None), None
    if not bool(outcome):
        return False, None, teach_refusal_reason(kind, key, value)
    return True, _newest_correction_id(store), None


def _correction_ids(value: Any) -> list[int]:
    """A clean ``list[int]`` of correction ids from whatever the run carries."""
    ids: list[int] = []
    for item in (value or []):
        try:
            ids.append(int(item))
        except (TypeError, ValueError):  # pragma: no cover - defensive
            continue
    return ids
