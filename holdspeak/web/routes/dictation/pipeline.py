"""Dictation readiness + dry-run routes — HS-34-01 split of `dictation.py`.

`/api/dictation/readiness` and `/api/dictation/dry-run`. The dry-run path writes
detected project-doc suggestions into the shared store owned by
`build_dictation_router`, so it is passed in.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ._helpers import (
    _block_summary,
    _resolve_blocks_target,
    _resolve_project_context,
    _run_dictation_dry_run_text,
    _runtime_readiness,
)

log = get_logger("web.routes.dictation")


def build_pipeline_router(
    ctx: WebContext,
    project_doc_suggestions: dict[str, dict[str, str]],
    dismissed_signatures: set[str] | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/dictation/readiness")
    async def api_dictation_readiness(project_root: Optional[str] = None) -> Any:
        """Return one browser-facing readiness snapshot for dictation setup."""
        from ....agent_context import get_recent_agent_session
        from ....config import Config
        from ....plugins.dictation.project_kb import ProjectKBError, kb_path_for, read_project_kb
        from ....target_profile import detect_active_target_profile, detect_target_profile_with_override

        cfg = Config.load().dictation
        warnings: list[dict[str, Any]] = []

        project: Optional[dict[str, Any]]
        project_error: Optional[str] = None
        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            if project_root:
                return JSONResponse({"error": str(exc)}, status_code=400)
            project = None
            project_error = str(exc)

        global_path, _ = _resolve_blocks_target("global")
        global_blocks = _block_summary(global_path)

        project_blocks: Optional[dict[str, Any]] = None
        project_root_path: Optional[Path] = None
        if project is not None:
            project_root_path = Path(project["root"])
            project_blocks = _block_summary(project_root_path / ".holdspeak" / "blocks.yaml")

        resolved_blocks = (
            project_blocks
            if project_blocks is not None and project_blocks["exists"]
            else global_blocks
        )
        resolved_scope = (
            "project"
            if project_blocks is not None and project_blocks["exists"]
            else "global"
        )

        kb_payload: dict[str, Any] = {
            "path": None,
            "exists": False,
            "valid": True,
            "keys": [],
            "error": None,
        }
        if project_root_path is not None:
            kb_path = kb_path_for(project_root_path)
            kb_payload["path"] = str(kb_path)
            kb_payload["exists"] = kb_path.exists()
            try:
                kb = read_project_kb(project_root_path)
                kb_payload["keys"] = sorted((kb or {}).keys())
            except ProjectKBError as exc:
                kb_payload["valid"] = False
                kb_payload["error"] = str(exc)

        # HS-47-04: the `.hs/` context existence, so the discovery nudge can tell
        # "this project has no knowledge yet" (no KB and no context) without a new
        # detection path.
        hs_context_payload: dict[str, Any] = {"path": None, "exists": False}
        if project_root_path is not None:
            hs_dir = project_root_path / ".hs"
            hs_context_payload["path"] = str(hs_dir)
            hs_context_payload["exists"] = hs_dir.is_dir()

        runtime_payload = _runtime_readiness(cfg)
        try:
            target_payload = detect_active_target_profile(
                cfg.pipeline.target_profile_override
            ).to_dict()
        except Exception:
            target_payload = detect_target_profile_with_override(
                {},
                cfg.pipeline.target_profile_override,
            ).to_dict()
        agent_hooks_payload: dict[str, Any] = {}
        for agent in ("claude", "codex"):
            latest = get_recent_agent_session(agent=agent, max_age_seconds=7 * 24 * 60 * 60)
            agent_hooks_payload[agent] = {
                "fresh": latest is not None,
                "latest_session": latest.to_dict() if latest else None,
            }

        if not cfg.pipeline.enabled:
            warnings.append({
                "code": "pipeline_disabled",
                "message": "Dictation pipeline is disabled.",
                "action": "Enable the dictation pipeline from Runtime.",
                "section": "runtime",
                "runtime_action": "enable_pipeline",
            })
        if project is None:
            warnings.append({
                "code": "no_project",
                "message": project_error or "No project root detected.",
                "action": "Set a project root override or launch holdspeak from a project directory.",
                "section": "readiness",
            })
        if not resolved_blocks["exists"] or int(resolved_blocks["count"]) == 0:
            warnings.append({
                "code": "no_blocks",
                "message": "No dictation blocks are loaded for the selected project.",
                "action": "Create the Action item starter and run its sample.",
                "section": "blocks",
                "template_id": "action_item",
                "template_action": "create_dry_run",
                "template_scope": "project" if project is not None else "global",
            })
        if not global_blocks["valid"] or (project_blocks is not None and not project_blocks["valid"]):
            warnings.append({
                "code": "invalid_blocks",
                "message": "A blocks.yaml file is invalid.",
                "action": "Open Blocks and fix the validation error.",
                "section": "blocks",
            })
        if project is not None and not kb_payload["exists"]:
            warnings.append({
                "code": "missing_project_kb",
                "message": "Project KB file is missing.",
                "action": "Create a starter Project KB file.",
                "section": "kb",
                "kb_action": "create_starter",
            })
        if not kb_payload["valid"]:
            warnings.append({
                "code": "invalid_project_kb",
                "message": "Project KB file is invalid.",
                "action": "Open Project KB and fix the validation error.",
                "section": "kb",
            })
        if runtime_payload["status"] == "unavailable":
            warnings.append({
                "code": "runtime_unavailable",
                "message": runtime_payload["detail"],
                "action": "Install the selected runtime extra or change backend.",
                "section": "runtime",
                "guidance": runtime_payload.get("guidance"),
            })
        elif runtime_payload["status"] == "missing_model":
            warnings.append({
                "code": "runtime_model_missing",
                "message": runtime_payload["detail"],
                "action": "Download the model or update the runtime model path.",
                "section": "runtime",
                "guidance": runtime_payload.get("guidance"),
            })

        ready = (
            cfg.pipeline.enabled
            and project is not None
            and bool(resolved_blocks["valid"])
            and int(resolved_blocks["count"]) > 0
            and bool(kb_payload["valid"])
            and runtime_payload["status"] == "available"
        )

        # HS-39-05: depth telemetry — per-stage latency quantiles + budget
        # guidance + multi-pass timings + correction-store state.
        from ....dictation_telemetry import build_depth_readiness

        telemetry_store = ctx.telemetry
        corrections_store = ctx.corrections
        depth_payload = build_depth_readiness(
            stage_quantiles=telemetry_store.stage_quantiles() if telemetry_store is not None else {},
            rewrite_pass_ms=telemetry_store.latest_rewrite_pass_ms() if telemetry_store is not None else [],
            run_count=len(telemetry_store) if telemetry_store is not None else 0,
            budget_ms=cfg.pipeline.max_total_latency_ms,
            corrections_enabled=bool(getattr(cfg.pipeline, "corrections_enabled", False)),
            corrections_size=len(corrections_store) if corrections_store is not None else 0,
            corrections_recent=(
                [c.key for c in corrections_store.recent(limit=5)]
                if corrections_store is not None
                else []
            ),
        )

        return JSONResponse(
            {
                "ready": ready,
                "project": project,
                "config": {
                    "pipeline_enabled": cfg.pipeline.enabled,
                    "max_total_latency_ms": cfg.pipeline.max_total_latency_ms,
                    "backend": cfg.runtime.backend,
                },
                "blocks": {
                    "global": global_blocks,
                    "project": project_blocks,
                    "resolved_scope": resolved_scope,
                    "resolved": resolved_blocks,
                },
                "project_kb": kb_payload,
                "project_context": hs_context_payload,
                "runtime": runtime_payload,
                "telemetry": runtime_payload.get("telemetry"),
                "depth": depth_payload,
                "target": target_payload,
                "agent_hooks": agent_hooks_payload,
                "warnings": warnings,
            }
        )

    @router.post("/api/dictation/dry-run")
    async def api_dictation_dry_run(payload: dict[str, Any]) -> Any:
        utterance = payload.get("utterance") if isinstance(payload, dict) else None
        if not isinstance(utterance, str):
            return JSONResponse(
                {
                    "error": "utterance must be a string",
                    "detail": {"utterance": "required string"},
                },
                status_code=400,
            )
        text = utterance.strip()
        if not text:
            return JSONResponse(
                {
                    "error": "utterance must not be empty",
                    "detail": {"utterance": "must not be empty"},
                },
                status_code=400,
            )
        project_root_override = payload.get("project_root") if isinstance(payload, dict) else None
        if project_root_override is not None and not isinstance(project_root_override, str):
            return JSONResponse(
                {
                    "error": "project_root must be a string when provided",
                    "detail": {"project_root": "optional string path"},
                },
                status_code=400,
            )
        target_hints = payload.get("target") if isinstance(payload, dict) else None
        if target_hints is not None and not isinstance(target_hints, dict):
            return JSONResponse(
                {
                    "error": "target must be an object when provided",
                    "detail": {"target": "optional object of app/window/process hints"},
                },
                status_code=400,
            )

        try:
            return JSONResponse(
                _run_dictation_dry_run_text(
                    text,
                    project_root_override,
                    target_hints,
                    suggestions=project_doc_suggestions,
                    corrections=ctx.corrections,
                    dismissed_signatures=dismissed_signatures,
                    telemetry=ctx.telemetry,
                    journal=ctx.journal,
                )
            )
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            log.error(f"Dictation dry-run failed: {exc}")
            return JSONResponse({"error": str(exc)}, status_code=500)

    @router.post("/api/dictation/remote")
    async def api_dictation_remote(payload: dict[str, Any]) -> Any:
        """HSM-13-01 — accept a dictated answer from a companion client (iPhone/iPad),
        run it through the rich dictation pipeline (corrections/blocks/plugins), and
        deliver it into the desktop's dictation target / AI PI path.

        Auth: gated by the runtime's web-auth middleware (``Authorization: Bearer``)
        exactly like every other route when bound off-loopback — the companion client
        mirrors the server's ``web_auth_token`` on every request. Delivery is
        deliver-on-command (the client user pressed send); there is no autonomous path.
        """
        text = payload.get("text") if isinstance(payload, dict) else None
        if not isinstance(text, str) or not text.strip():
            return JSONResponse({"error": "text must be a non-empty string"}, status_code=400)
        text = text.strip()
        target_hints = payload.get("target") if isinstance(payload, dict) else None
        if target_hints is not None and not isinstance(target_hints, dict):
            return JSONResponse(
                {"error": "target must be an object when provided"}, status_code=400
            )
        # HSM-15-01a: the delivery target mode. "agent" (default) answers the
        # waiting coder exactly as before (byte-identical); "focused" free-types
        # the processed text into whatever Mac app is focused, with no awaiting
        # coder session required.
        target_mode = payload.get("target_mode") if isinstance(payload, dict) else None
        if target_mode is None:
            target_mode = "agent"
        if target_mode not in ("agent", "focused"):
            return JSONResponse(
                {"error": 'target_mode must be one of "agent" or "focused"'},
                status_code=400,
            )

        # Reuse the exact rich-pipeline path the browser dry-run uses, so the same
        # corrections/blocks/plugins apply — the answer is as smart as one spoken at
        # the desk, not raw transcript.
        try:
            processed = _run_dictation_dry_run_text(
                text,
                None,
                target_hints,
                suggestions=project_doc_suggestions,
                corrections=ctx.corrections,
                dismissed_signatures=dismissed_signatures,
                telemetry=ctx.telemetry,
                journal=ctx.journal,
            )
        except Exception as exc:
            log.error(f"Remote dictation pipeline failed: {exc}")
            return JSONResponse({"error": str(exc)}, status_code=500)

        final_text = (
            processed.get("final_text", text) if isinstance(processed, dict) else text
        )
        delivered = False
        if ctx.on_remote_dictation is not None:
            try:
                if target_mode == "agent":
                    # Byte-identical to the pre-15 call (a plain str hook): the
                    # default path never threads the new keyword.
                    ctx.on_remote_dictation(final_text)
                else:
                    ctx.on_remote_dictation(final_text, target=target_mode)
                delivered = True
            except Exception as exc:
                log.error(f"Remote dictation delivery failed: {exc}")
                return JSONResponse(
                    {"error": f"delivery failed: {exc}", "final_text": final_text, "delivered": False},
                    status_code=502,
                )
        return JSONResponse({"success": True, "final_text": final_text, "delivered": delivered})

    @router.get("/api/dictation/corrections")
    async def api_dictation_corrections_list() -> Any:
        from ....config import Config
        from ....dictation_learning import reach_for_gist
        from ....plugins.dictation.corrections import CORRECTION_KINDS

        store = ctx.corrections
        cfg = Config.load().dictation
        items = store.list_for_display() if store is not None else []
        # HS-48-02: each correction's real reach over the journal (the same
        # Jaccard count the digest reports), so the Memory list shows how far
        # each thing it learned actually carries.
        transcripts = _journal_transcripts()
        for item in items:
            item["similar"] = reach_for_gist(str(item.get("key") or ""), transcripts)
        return JSONResponse(
            {
                "enabled": bool(getattr(cfg.pipeline, "corrections_enabled", False)),
                "kinds": list(CORRECTION_KINDS),
                "size": len(store) if store is not None else 0,
                "items": items,
            }
        )

    @router.get("/api/dictation/learning-digest")
    async def api_dictation_learning_digest(window: str = "week") -> Any:
        """HS-48-01: a read-only "What HoldSpeak learned" aggregation.

        Reads the correction memory + the journal and returns honest, windowed
        counts: corrections made, dictations corrected, the by-kind / by-block /
        by-target breakdown, and a real "learned from N similar" per correction.
        The "N similar" is the same Jaccard matcher that nudges routing, so the
        reported reach is exactly what the live pipeline would nudge. No writes.
        """
        from ....config import Config
        from ....dictation_learning import build_learning_digest

        cfg = Config.load().dictation
        store = ctx.corrections
        corrections = store.list_for_display() if store is not None else []
        repo = _journal_repo()
        journal_rows = (
            [
                {
                    "transcript": r.transcript,
                    "created_at": r.created_at,
                    "corrected": r.corrected,
                }
                for r in repo.recent()
            ]
            if repo is not None
            else []
        )
        digest = build_learning_digest(
            corrections=corrections,
            journal_rows=journal_rows,
            window=window,
            enabled=bool(getattr(cfg.pipeline, "corrections_enabled", False)),
        )
        return JSONResponse(digest)

    @router.post("/api/dictation/corrections")
    async def api_dictation_corrections_record(payload: dict[str, Any]) -> Any:
        from ....plugins.dictation.corrections import CORRECTION_KINDS

        store = ctx.corrections
        if store is None:
            return JSONResponse({"error": "correction store unavailable"}, status_code=503)
        kind = payload.get("kind") if isinstance(payload, dict) else None
        text = payload.get("text") if isinstance(payload, dict) else None
        value = payload.get("value") if isinstance(payload, dict) else None
        if kind not in CORRECTION_KINDS:
            return JSONResponse(
                {"error": f"kind must be one of {list(CORRECTION_KINDS)}"}, status_code=400
            )
        if not isinstance(text, str) or not text.strip():
            return JSONResponse({"error": "text must be a non-empty string"}, status_code=400)
        if not isinstance(value, str) or not value.strip():
            return JSONResponse({"error": "value must be a non-empty string"}, status_code=400)
        recorded = store.record(kind, text, value)
        return JSONResponse({"recorded": bool(recorded), "size": len(store)})

    @router.delete("/api/dictation/corrections/{correction_id}")
    async def api_dictation_corrections_delete(correction_id: int) -> Any:
        """HS-40-04: remove one persistent correction by id (curate the memory)."""
        store = ctx.corrections
        if store is None:
            return JSONResponse({"error": "correction store unavailable"}, status_code=503)
        if store.remove(correction_id):
            return JSONResponse({"removed": True, "size": len(store)})
        return JSONResponse({"removed": False, "error": "correction not found"}, status_code=404)

    @router.delete("/api/dictation/corrections")
    async def api_dictation_corrections_clear() -> Any:
        """HS-40-04: forget everything the copilot has learned (ring + durable)."""
        store = ctx.corrections
        if store is None:
            return JSONResponse({"error": "correction store unavailable"}, status_code=503)
        store.clear()
        return JSONResponse({"cleared": True, "size": len(store)})

    # ── HS-45-02: the dictation journal (review + curate) ─────────────────
    def _journal_repo():
        """The durable journal repository behind the recorder, or None."""
        recorder = ctx.journal
        return getattr(recorder, "repository", None) if recorder is not None else None

    def _journal_transcripts() -> list[str]:
        """Every journal transcript (for reach counts), or [] on a bare server."""
        repo = _journal_repo()
        return [r.transcript for r in repo.recent()] if repo is not None else []

    @router.get("/api/dictation/journal")
    async def api_dictation_journal_list(
        limit: int = 200, source: Optional[str] = None
    ) -> Any:
        """List journal entries newest-first (HS-45-02).

        Reports the toggle + retention from config so the UI can show the
        local-only trust statement. With no durable repo (a bare server) the
        list is empty — never an error.
        """
        from ....config import Config
        from ....dictation_learning import best_correction_signal, reach_by_gist_map

        cfg = Config.load().dictation
        repo = _journal_repo()
        clean_source = source if source in ("dictation", "dry_run") else None
        records = repo.recent(limit=limit, source=clean_source) if repo is not None else []
        items = [_journal_to_dict(r) for r in records]
        # HS-48-02: a per-entry "learned from N similar" signal — the correction
        # the live router would apply to this utterance, and its reach. Gated on
        # `corrections_enabled`: a None snapshot means the router nudges nothing,
        # so we claim nothing. Reach is over the whole journal, precomputed once.
        store = ctx.corrections
        snapshot = (
            store.snapshot()
            if store is not None and bool(getattr(cfg.pipeline, "corrections_enabled", False))
            else None
        )
        if snapshot:
            transcripts = _journal_transcripts()
            reach_map = reach_by_gist_map(snapshot, transcripts)
            for item in items:
                item["learning"] = best_correction_signal(
                    str(item.get("transcript") or ""), snapshot, reach_map
                )
        else:
            for item in items:
                item["learning"] = None
        return JSONResponse(
            {
                "enabled": bool(getattr(cfg.pipeline, "journal_enabled", True)),
                "retention": int(getattr(cfg.pipeline, "journal_retention", 500)),
                "count": repo.count() if repo is not None else 0,
                "items": items,
            }
        )

    @router.delete("/api/dictation/journal/{entry_id}")
    async def api_dictation_journal_delete(entry_id: int) -> Any:
        """Delete one journal entry by id (HS-45-02)."""
        repo = _journal_repo()
        if repo is None:
            return JSONResponse({"error": "journal unavailable"}, status_code=404)
        if repo.delete(entry_id):
            return JSONResponse({"removed": True, "count": repo.count()})
        return JSONResponse({"removed": False, "error": "entry not found"}, status_code=404)

    @router.delete("/api/dictation/journal")
    async def api_dictation_journal_clear() -> Any:
        """Wipe the whole journal (HS-45-02 — the one-click local wipe)."""
        repo = _journal_repo()
        if repo is None:
            return JSONResponse({"error": "journal unavailable"}, status_code=404)
        removed = repo.clear()
        return JSONResponse({"cleared": True, "removed": removed, "count": repo.count()})

    @router.post("/api/dictation/journal/{entry_id}/correct")
    async def api_dictation_journal_correct(entry_id: int, payload: dict[str, Any]) -> Any:
        """HS-45-03: correct a journaled run in the moment — and teach.

        Records a correction (reusing the Phase-40 `CorrectionStore`, so future
        routing is nudged) keyed on the entry's own transcript, then flips the
        journal entry's `corrected` flag and links the correction. The teach
        path is gist-only + secret-filtered by the store, exactly like the
        Memory tab.
        """
        from ....plugins.dictation.corrections import CORRECTION_KINDS

        repo = _journal_repo()
        store = ctx.corrections
        if repo is None:
            return JSONResponse({"error": "journal unavailable"}, status_code=404)
        if store is None:
            return JSONResponse({"error": "correction store unavailable"}, status_code=503)
        kind = payload.get("kind") if isinstance(payload, dict) else None
        value = payload.get("value") if isinstance(payload, dict) else None
        if kind not in CORRECTION_KINDS:
            return JSONResponse(
                {"error": f"kind must be one of {list(CORRECTION_KINDS)}"}, status_code=400
            )
        if not isinstance(value, str) or not value.strip():
            return JSONResponse({"error": "value must be a non-empty string"}, status_code=400)
        entry = repo.get(entry_id)
        if entry is None:
            return JSONResponse({"error": "entry not found"}, status_code=404)
        # Teach from the entry's own transcript (the gist the correction applies
        # to). The store secret-filters + dedups; a secret-like transcript is a
        # no-op teach but the entry is still flagged corrected.
        recorded = store.record(kind, entry.transcript, value)
        correction_id = None
        try:
            items = store.list_for_display()
            if items and items[0].get("id") is not None:
                correction_id = int(items[0]["id"])
        except Exception:  # pragma: no cover - id linkage is best-effort
            correction_id = None
        repo.mark_corrected(entry_id, correction_id=correction_id)
        # HS-48-02: the honest coverage this teach now has — how many journal
        # utterances the correction reaches (the same Jaccard count the digest
        # uses). Only meaningful when something was actually taught; `enabled`
        # lets the UI say "now nudges N" vs "will nudge N once corrections are on"
        # without ever overclaiming.
        from ....config import Config
        from ....dictation_learning import reach_for_gist

        similar = (
            reach_for_gist(entry.transcript, _journal_transcripts()) if recorded else 0
        )
        cfg = Config.load().dictation
        corrections_enabled = bool(getattr(cfg.pipeline, "corrections_enabled", False))
        # HS-56-04: reflect the learning loop on the presence surface — but only
        # honestly. The broadcast fires only when something was actually taught
        # AND has real reach (similar > 0); a no-op teach or a reach of zero
        # stays silent, so Qlippy never claims learning that did not happen.
        if recorded and similar > 0:
            gist = (entry.transcript or "").strip()
            ctx.broadcast(
                "learning_event",
                {
                    "kind": kind,
                    "gist": gist[:120] + ("…" if len(gist) > 120 else ""),
                    "value": str(value).strip(),
                    "similar": int(similar),
                    "enabled": corrections_enabled,
                },
            )
        return JSONResponse(
            {
                "corrected": True,
                "taught": bool(recorded),
                "correction_id": correction_id,
                "size": len(store),
                "similar": similar,
                "enabled": corrections_enabled,
            }
        )

    @router.post("/api/dictation/journal/{entry_id}/replay")
    async def api_dictation_journal_replay(entry_id: int) -> Any:
        """HS-45-04: re-run a stored utterance through the *current* pipeline.

        Replays the entry's stored **transcript** (not audio) through the dry-run
        pipeline — no typing, no new journal row — using the entry's original
        project root so routing context matches, and returns a before → after
        diff. This makes "it learned" tangible: correct an utterance, replay it,
        and watch the routing change. The original journal row is never mutated.
        """
        repo = _journal_repo()
        if repo is None:
            return JSONResponse({"error": "journal unavailable"}, status_code=404)
        entry = repo.get(entry_id)
        if entry is None:
            return JSONResponse({"error": "entry not found"}, status_code=404)
        try:
            after = _run_dictation_dry_run_text(
                entry.transcript,
                entry.project_root,  # original context
                None,
                suggestions=project_doc_suggestions,
                corrections=ctx.corrections,
                dismissed_signatures=dismissed_signatures,
                telemetry=None,  # a preview — don't pollute readiness telemetry
                journal=None,  # replay never journals (it's not a new dictation)
            )
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:  # pragma: no cover - mirrors the dry-run route
            log.error(f"Journal replay failed: {exc}")
            return JSONResponse({"error": str(exc)}, status_code=500)

        after_block, after_conf = _routed_from_stages(after.get("stages") or [])
        after_summary = {
            "block_id": after_block,
            "confidence": after_conf,
            "target_profile": (after.get("target") or {}).get("id"),
            "final_text": after.get("final_text") or "",
            "runtime_status": after.get("runtime_status"),
        }
        before = {
            "block_id": entry.block_id,
            "confidence": entry.confidence,
            "target_profile": entry.target_profile,
            "final_text": entry.final_text,
        }
        changed = (
            (before["block_id"] or None) != (after_summary["block_id"] or None)
            or (before["target_profile"] or None) != (after_summary["target_profile"] or None)
            or (before["final_text"] or "") != (after_summary["final_text"] or "")
        )
        return JSONResponse(
            {
                "entry_id": entry_id,
                "before": before,
                "after": after_summary,
                "detail": after,
                "changed": changed,
            }
        )

    return router


def _routed_from_stages(stages: list[Any]) -> tuple[Optional[str], Optional[float]]:
    """The block the run routed to (the newest stage intent with a block_id)."""
    block: Optional[str] = None
    conf: Optional[float] = None
    for stage in stages:
        intent = stage.get("intent") if isinstance(stage, dict) else None
        if isinstance(intent, dict) and intent.get("block_id"):
            block = intent.get("block_id")
            conf = intent.get("confidence")
    return block, conf


def _journal_to_dict(record: Any) -> dict[str, Any]:
    """Serialize a `DictationJournalRecord` for the Journal UI (HS-45-02)."""
    return {
        "id": record.id,
        "created_at": record.created_at,
        "source": record.source,
        "transcript": record.transcript,
        "final_text": record.final_text,
        "project_root": record.project_root,
        "intent": record.intent,
        "block_id": record.block_id,
        "target_profile": record.target_profile,
        "stage_ms": record.stage_ms,
        "total_ms": record.total_ms,
        "rewrite_pass_ms": record.rewrite_pass_ms,
        "confidence": record.confidence,
        "warnings": record.warnings,
        "corrected": record.corrected,
        "correction_id": record.correction_id,
    }
