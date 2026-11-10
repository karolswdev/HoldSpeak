"""Transport-neutral dictation: the journal, the corrections, the floor and the files.

HS-122-05 gave the journal its service. 2026-11-09 (one contract) moved the
bodies of the hand-written ``/api/dictation/*`` routes in here: the journal
edits and the teach, the corrections, the open mic's floor, the project
context, the ``.hs`` files, the project KB and the blocks.
``holdspeak/dictation_operations.py`` declares each verb once; the routes and
the MCP tools are produced from it.

Readiness, intent controls, browser audio and the cancellable/committed speech
jobs use this same service. Request lifetime stays in HTTP; its callbacks and
audio are held inputs to declared operations, never arguments from a client.
The runtime parts are providers read at each call from the composed context.
"""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import csv
import asyncio
import io
import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Optional

from ..config import Config
from ..db.core import Database
from ..principals import Principal
from holdspeak.services.errors import NotFound, ServiceError, ValidationError

log = logging.getLogger("holdspeak.services.dictation")

Provider = Callable[[], Any]

#: The browser open mic's name on the floor. One owner, every tab.
OPEN_MIC_OWNER = "open_mic"
#: Lease bounds. The client renews at roughly half the lease it asked for.
DEFAULT_LEASE_SECONDS = 20.0
MAX_LEASE_SECONDS = 120.0


def _refused(status: int, body: dict[str, Any], code: str = "refused") -> ServiceError:
    """A refusal that keeps the hand-written route's status and body (``context``)."""
    detail = str(body.get("error") or body.get("refusal") or code)
    return ServiceError(code, detail, context={"status": status, "body": body})


def bind_dictation_runtime(service: "DictationService", source: Any) -> "DictationService":
    """Read the runtime parts from *source* (the hub's ``WebContext``) at each call:
    the correction store, the floor's arbiter, the config-changed hook, the bus."""
    service._runtime_source = source
    service._corrections_of = lambda: getattr(source, "corrections", None)
    # The journal edits write through the recorder's durable repository; a
    # server with no recorder repository refuses them (404), as it always did.
    service._edits_of = lambda: getattr(getattr(source, "journal", None), "repository", None)
    service._voice_session_of = lambda: getattr(source, "voice_session", None)
    service._config_changed_of = lambda: getattr(source, "on_dictation_config_changed", None)

    def broadcast(kind: str, data: Any) -> None:
        send = getattr(source, "broadcast", None)
        if send is not None:
            send(kind, data)

    service._broadcast = broadcast
    return service


def pipeline_context(source: Any) -> Any:
    """The one context shape read by browser and streaming transcript processing."""
    from types import SimpleNamespace

    return SimpleNamespace(
        dictation_corrections=getattr(source, "corrections", None),
        dictation_telemetry=getattr(source, "telemetry", None),
        dictation_journal=getattr(source, "journal", None),
    )


def _none(*_: Any) -> Any:
    return None


@observe_service
class DictationService:
    def __init__(
        self,
        db: Database | None = None,
        journal_repository: Any | None = None,
        journal_available: bool = True,
        delivery_repository: Any | None = None,
        *,
        observer: PipelineObserver | None = None,
    ) -> None:
        if db is None:
            from ..db import get_database

            db = get_database()
        self._db = db
        self._journal = journal_repository if journal_available else None
        if self._journal is None and journal_available:
            self._journal = db.dictation_journal
        self._deliveries = (
            delivery_repository
            if delivery_repository is not None
            else db.dictation_deliveries
        )
        self._observer = observer or NullObserver()
        # The runtime parts: none until bind_dictation_runtime names their holder.
        self._runtime_source: Any = None
        self._corrections_of: Provider = _none
        self._edits_of: Provider = lambda: self._journal
        self._voice_session_of: Provider = _none
        self._config_changed_of: Provider = _none
        self._broadcast: Optional[Callable[[str, Any], Any]] = None

    def readiness(
        self, principal: Principal, project_root: Optional[str] = None
    ) -> dict[str, Any]:
        from .dictation_readiness import readiness

        return readiness(self._runtime_source, project_root)

    def intent_controls(self, principal: Principal) -> dict[str, Any]:
        callback = getattr(self._runtime_source, "on_get_intent_controls", None)
        if callback is None:
            return {
                "enabled": False,
                "profile": "balanced",
                "available_profiles": [],
                "supported_intents": [],
                "override_intents": [],
            }
        result = self._intent_callback(callback)
        return result if isinstance(result, dict) else {"controls": result}

    @staticmethod
    def _intent_callback(
        callback: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        try:
            return callback(*args, **kwargs)
        except Exception as exc:
            raise _refused(500, {"success": False, "error": str(exc)}) from exc

    def set_intent_profile(self, principal: Principal, profile: str) -> dict[str, Any]:
        callback = getattr(self._runtime_source, "on_set_intent_profile", None)
        if callback is None:
            raise _refused(
                501, {"success": False, "error": "Intent profile updates not supported"}
            )
        result = self._intent_callback(callback, profile)
        if isinstance(result, dict) and self._broadcast:
            self._broadcast("intent_controls_updated", result)
        return {"success": True, "controls": result}

    def preview_intent_route(self, principal: Principal, **args: Any) -> dict[str, Any]:
        callback = getattr(self._runtime_source, "on_route_preview", None)
        if callback is None:
            raise _refused(
                501, {"success": False, "error": "Intent route preview not supported"}
            )
        result = self._intent_callback(
            callback,
            **{
                key: args.get(key)
                for key in (
                    "profile",
                    "threshold",
                    "intent_scores",
                    "override_intents",
                    "previous_intents",
                    "tags",
                    "transcript",
                )
            },
        )
        return {"success": True, "route": result}

    def wake_type(self, principal: Principal, payload: dict[str, Any]) -> Any:
        """HS-60: type a stored wake preview, exactly once."""
        ctx = self._runtime_source
        if ctx.on_wake_type is None:
            raise _refused(
                503,
                {
                    "success": False,
                    "error": "Wake typing is unavailable in this runtime. Nothing was typed. Start the desktop runtime and retry.",
                },
            )
        token = str((payload or {}).get("token", "")).strip()
        if not token:
            raise _refused(
                400, {"success": False, "error": "A preview token is required."}
            )
        typed = ctx.on_wake_type(token)
        if typed is None:
            raise _refused(
                404,
                {"success": False, "error": "Unknown or already used preview token."},
            )
        return {"success": True, "typed": typed}

    def open_mic(self, principal: Principal) -> Any:
        """Open ONE admitted open-mic interval for this authenticated identity."""
        from ..speech_session import browser_mic_sessions, SpeechSessionRefused

        try:
            interval = browser_mic_sessions().open(principal)
        except SpeechSessionRefused as exc:
            raise _refused(
                403,
                {
                    "success": False,
                    "reason": exc.reason,
                    "error": "The microphone session was not admitted. Nothing is being captured.",
                },
            )
        return {
            "success": True,
            "mic_session": interval.handle,
            "expires_at": interval.ceiling_at,
            "inactivity_expires_at": interval.lease_until,
        }

    def close_mic(self, principal: Principal) -> Any:
        """Close the interval: the parent is cancelled and closed, not left live."""
        from ..speech_session import browser_mic_sessions

        closed = browser_mic_sessions().close(principal, reason="browser_mic_stopped")
        return {"success": True, "closed": bool(closed)}

    async def transcribe_audio(
        self,
        principal: Principal,
        raw: bytes,
        *,
        pipeline: bool = False,
        mic_handle: str = "",
    ) -> Any:
        """HS-78-01: speak-to-fill -- browser-captured audio in, text out."""
        ctx = self._runtime_source
        from ..speech_session import (
            MIC_INTERVAL_CLOSED,
            OUTCOME_INDETERMINATE,
            SpeechProviderFailure,
            SpeechSessionRefused,
        )

        server = pipeline_context(ctx)
        if ctx.on_transcribe is None:
            raise _refused(
                503,
                {
                    "success": False,
                    "error": "Transcription is unavailable in this runtime. Your audio is kept in the browser for Retry. Start the desktop runtime.",
                },
            )
        if not raw:
            raise _refused(
                400, {"success": False, "error": "An audio body is required."}
            )
        if len(raw) > 16000000:
            raise _refused(
                413, {"success": False, "error": "Audio too large (cap: 16 MB)."}
            )
        egress_boundary = "local"
        try:
            import io
            import wave
            import numpy as np

            with wave.open(io.BytesIO(raw)) as wf:
                if (
                    wf.getnchannels() != 1
                    or wf.getframerate() != 16000
                    or wf.getsampwidth() != 2
                ):
                    raise _refused(
                        400,
                        {
                            "success": False,
                            "error": "Expected WAV: 16 kHz, mono, 16-bit PCM.",
                        },
                    )
                frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        except ServiceError:
            raise
        except Exception:
            raise _refused(400, {"success": False, "error": "Not a readable WAV body."})
        admitted = None
        transcribe = ctx.on_transcribe_admitted if pipeline else None
        if pipeline and transcribe is None:
            raise _refused(
                503,
                {
                    "success": False,
                    "error": "The dictation pipeline is unavailable: this runtime exposes no admitted transcription seam to run its model calls under. Your audio is kept in the browser. Retry without the pipeline for a verbatim transcript.",
                },
            )
        try:
            if transcribe is not None:
                admitted = await asyncio.to_thread(
                    transcribe,
                    audio,
                    principal=principal,
                    mic_handle=str(mic_handle or ""),
                )
                text = str(admitted.text)
                egress_boundary = str(admitted.provider.egress_boundary)
            else:
                text = await asyncio.to_thread(
                    ctx.on_transcribe,
                    audio,
                    principal=principal,
                    mic_handle=str(mic_handle or ""),
                )
        except SpeechSessionRefused as exc:
            raise _refused(
                409,
                {
                    "success": False,
                    "mic_interval": MIC_INTERVAL_CLOSED,
                    "reason": exc.reason,
                    "error": "The microphone session closed. Click the mic again to continue; your audio is kept in the browser for Retry.",
                },
            )
        except Exception as exc:
            log.error(f"speak-to-fill transcription failed: {exc}")
            raise _refused(
                502,
                {
                    "success": False,
                    "error": "Transcription failed. Your audio is kept in the browser for Retry.",
                },
            )
        if not pipeline:
            return {"success": True, "text": text}
        raw_text = text
        outcome = "succeeded"
        failure_body: dict[str, Any] | None = None
        failure_status = 0
        terminal = ""
        try:
            from ..dictation_runner import process_transcript

            corrected = await process_transcript(
                raw_text=raw_text,
                source="browser",
                context=None,
                config=getattr(ctx, "_config", None) or await asyncio.to_thread(Config.load),
                server=server,
                admission=None if admitted is None else admitted.provider,
            )
        except SpeechSessionRefused as exc:
            outcome = "refused"
            failure_status = 422
            failure_body = {
                "success": False,
                "error": exc.reason,
                "reason": exc.reason,
                "refusal": exc.reason,
                "failure_category": "speech_session_refused",
            }
        except SpeechProviderFailure as exc:
            outcome = "failed"
            failure_status = 502
            failure_body = {
                "success": False,
                "error": f"{exc.contract}:{exc.reason}",
                "reason": exc.reason,
                "failure_category": "speech_provider_failure",
            }
        except Exception as exc:
            log.warning(f"Browser pipeline processing failed, returning raw: {exc}")
            corrected = raw_text
            outcome = "failed"
        finally:
            if admitted is not None:
                terminal = admitted.close(outcome)
        terminal_marker = (
            {"session_terminal": OUTCOME_INDETERMINATE}
            if terminal == OUTCOME_INDETERMINATE
            else {}
        )
        if failure_body is not None:
            raise _refused(failure_status, {**failure_body, **terminal_marker})
        return {
            "success": True,
            "text": corrected,
            "raw": raw_text,
            "egress_boundary": egress_boundary,
            **terminal_marker,
        }

    def preview_type(self, principal: Principal, payload: dict[str, Any]) -> Any:
        """HS-75-01: type a stored hold-key preview, exactly once."""
        ctx = self._runtime_source
        if ctx.on_preview_type is None:
            raise _refused(
                503,
                {
                    "success": False,
                    "error": "Preview typing is unavailable in this runtime. Nothing was typed. Start the desktop runtime and retry.",
                },
            )
        token = str((payload or {}).get("token", "")).strip()
        if not token:
            raise _refused(
                400, {"success": False, "error": "A preview token is required."}
            )
        typed = ctx.on_preview_type(token)
        if typed is None:
            raise _refused(
                404,
                {"success": False, "error": "Unknown or already used preview token."},
            )
        return {"success": True, "typed": typed}

    def preview_discard(self, principal: Principal, payload: dict[str, Any]) -> Any:
        """HS-75-01: burn a stored preview without typing."""
        ctx = self._runtime_source
        if ctx.on_preview_discard is None:
            raise _refused(
                503,
                {
                    "success": False,
                    "error": "Preview discard is unavailable in this runtime. The preview is unchanged. Start the desktop runtime and retry.",
                },
            )
        token = str((payload or {}).get("token", "")).strip()
        if not token:
            raise _refused(
                400, {"success": False, "error": "A preview token is required."}
            )
        if not ctx.on_preview_discard(token):
            raise _refused(
                404,
                {"success": False, "error": "Unknown or already used preview token."},
            )
        return {"success": True}

    def test_voice_command(self, principal: Principal, payload: dict[str, Any]) -> Any:
        """HS-52-05: fire one voice command action from the board, to verify it."""
        from ..config import VoiceMacroAction, VoiceMacroError

        try:
            action = VoiceMacroAction(
                kind=str((payload or {}).get("kind", "")),
                payload=str((payload or {}).get("payload", "")),
            )
        except VoiceMacroError as exc:
            raise _refused(400, {"ok": False, "error": str(exc)})
        if action.kind in {"type_text", "desk_verb"}:
            return {
                "ok": True,
                "tested": False,
                "preview": action.preview(),
                "note": f"Preview · {action.preview()}"
                if action.kind == "desk_verb"
                else "types into the focused app",
            }
        from ..plugins.actuators import ActuatorProposal
        from ..plugins.voice_macro_connector import build_voice_macro_connector

        proposal = ActuatorProposal(
            target="voice_macro",
            action=action.kind,
            preview=action.preview(),
            payload={"kind": action.kind, "payload": action.payload},
            reversible=False,
            required_capabilities=(),
        )
        try:
            connector = build_voice_macro_connector(action)
            result = connector(proposal)
            return {"ok": True, "tested": True, "result": result}
        except Exception as exc:
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    async def rehearse(self, principal: Principal, **args: Any) -> Any:
        from .dictation_jobs import rehearse

        return await rehearse(self, principal, **args)

    async def remote_delivery(self, principal: Principal, **args: Any) -> Any:
        from .dictation_jobs import remote_delivery

        return await remote_delivery(self, principal, **args)

    async def replay_journal(self, principal: Principal, **args: Any) -> Any:
        from .dictation_jobs import replay_journal

        return await replay_journal(self, principal, **args)

    async def create_template_block(self, principal: Principal, **args: Any) -> Any:
        from .dictation_jobs import create_template_block

        return await create_template_block(self, principal, **args)

    def list_journal(
        self,
        principal: Principal,
        *,
        limit: int = 200,
        cursor: int | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        from ..plugins.dictation.journal import VALID_SOURCES

        clean_source = source if source in VALID_SOURCES else None
        records: list[Any] = []
        if self._journal is not None:
            if cursor is None:
                records = self._journal.recent(limit=limit, source=clean_source)
            else:
                # HS-176-03: `before` is a PAGE cursor, so it has to bound the
                # query, not the page it produced — filtering the newest `limit`
                # rows after the fact returns nothing once the cursor is older
                # than the first page. Prefer the repository's own `before`;
                # fall back to an unbounded read + slice while it lands.
                try:
                    records = self._journal.recent(
                        limit=limit, source=clean_source, before=cursor
                    )
                except TypeError:
                    records = [
                        record
                        for record in self._journal.recent(source=clean_source)
                        if record.id < cursor
                    ][: max(0, int(limit))]
        cfg = Config.load().dictation.pipeline
        return {
            "enabled": bool(getattr(cfg, "journal_enabled", True)),
            "retention": int(getattr(cfg, "journal_retention", 500)),
            "count": self._journal.count() if self._journal is not None else 0,
            # HS-176 counsel C4: the Speak footer's `N TODAY` token. `count` is
            # the all-time RETAINED total and stays what it is (Export and the
            # journal's own trust statement read it); `today` is the count the
            # token actually claims — rows on the local calendar day.
            # `getattr` because a bare/legacy repository double may not carry
            # the method; absent-as-zero, never an error into a journal read.
            "today": self._count_today(),
            "items": [self._entry(record) for record in records],
        }

    def _count_today(self) -> int:
        if self._journal is None:
            return 0
        counter = getattr(self._journal, "count_today", None)
        if not callable(counter):
            return 0
        try:
            return int(counter())
        except Exception:
            return 0

    def get_entry(self, principal: Principal, entry_id: int) -> dict[str, Any]:
        entry = self._journal.get(entry_id) if self._journal is not None else None
        if entry is None:
            raise NotFound("journal entry", str(entry_id))
        return self._entry(entry)

    def export_journal(self, principal: Principal, format: str = "json") -> dict[str, Any]:
        entries = [
            self._entry(record)
            for record in (self._journal.recent() if self._journal is not None else [])
        ]
        if format == "json":
            return {"format": "json", "content": json.dumps(entries, indent=2, sort_keys=True)}
        if format == "csv":
            output = io.StringIO()
            fields = list(entries[0]) if entries else ["id", "created_at", "source", "transcript", "final_text"]
            writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for entry in entries:
                writer.writerow({key: self._csv_value(value) for key, value in entry.items()})
            return {"format": "csv", "content": output.getvalue()}
        raise ValidationError("format must be json or csv")

    def clear_journal(self, principal: Principal) -> dict[str, Any]:
        repo = self._repo()
        removed = repo.clear()
        return {"cleared": True, "removed": removed, "count": repo.count()}

    def claim_delivery(
        self, principal: Principal, delivery_id: str, *, request_hash: str
    ) -> dict[str, Any]:
        clean_id = str(delivery_id or "").strip()
        if not clean_id:
            raise ValidationError("delivery_id must be a non-empty identifier")
        return self._deliveries.claim(clean_id, request_hash=request_hash)

    def complete_delivery(
        self,
        principal: Principal,
        delivery_id: str,
        *,
        response_status: int,
        response: dict[str, Any],
    ) -> None:
        self._deliveries.complete(
            delivery_id, response_status=response_status, response=response
        )

    def fail_delivery(
        self,
        principal: Principal,
        delivery_id: str,
        *,
        response_status: int,
        response: dict[str, Any],
        error: str,
    ) -> None:
        self._deliveries.fail(
            delivery_id,
            response_status=response_status,
            response=response,
            error=error,
        )

    def submit_dictation(
        self,
        principal: Principal,
        text: str,
        *,
        aim: str | None = None,
        source: str = "dictation",
    ) -> dict[str, Any]:
        clean_text = str(text or "").strip()
        if not clean_text:
            raise ValidationError("text must be a non-empty string")
        if source not in {"dictation", "dry_run", "browser", "hotkey"}:
            raise ValidationError("unknown dictation source")
        if self._journal is None:
            raise NotFound("journal", "default")
        cfg = Config.load().dictation.pipeline
        entry = self._journal.record(
            source=source,
            transcript=clean_text,
            final_text=clean_text,
            intent=aim,
            retention=int(getattr(cfg, "journal_retention", 500)),
        )
        return {"success": True, "final_text": clean_text, "entry": self._entry(entry)}

    # ── the runtime parts, read at each call ─────────────────────────────

    def _store(self) -> Any:
        store = self._corrections_of()
        if store is None:
            raise _refused(503, {"error": "correction store unavailable"}, "corrections_unavailable")
        return store

    def _repo(self) -> Any:
        repo = self._edits_of()
        if repo is None:
            raise _refused(404, {"error": "journal unavailable"}, "journal_unavailable")
        return repo

    def _config_changed(self) -> None:
        hook = self._config_changed_of()
        if hook is None:
            return
        try:
            hook()
        except Exception as exc:
            log.error(f"on_dictation_config_changed failed: {exc}")

    @staticmethod
    def _corrections_enabled() -> bool:
        return bool(getattr(Config.load().dictation.pipeline, "corrections_enabled", False))

    # ── the journal: edit, delete, teach ─────────────────────────────────

    def update_entry(self, principal: Principal, entry_id: int, transcript: Any) -> dict[str, Any]:
        """HS-101 B3: edit one entry's transcript in place; an empty transcript refuses."""
        repo = self._repo()
        clean = str(transcript or "").strip()
        if not clean:
            raise _refused(422, {"error": "transcript required"}, "transcript_required")
        if repo.update_transcript(int(entry_id), clean):
            return {"updated": True, "transcript": clean}
        raise _refused(404, {"updated": False, "error": "entry not found"}, "not_found")

    def delete_entry(self, principal: Principal, entry_id: int) -> dict[str, Any]:
        repo = self._repo()
        if repo.delete(int(entry_id)):
            return {"removed": True, "count": repo.count()}
        raise _refused(404, {"removed": False, "error": "entry not found"}, "not_found")

    def correct_entry(
        self, principal: Principal, entry_id: int, *, kind: Any, value: Any = None,
        heard: Any = None, said: Any = None,
    ) -> dict[str, Any]:
        """HS-45-03 / HS-176-02 (R4): correct a journaled run and teach.

        A refused teach flips nothing on the row and names its ``reason``; the
        linked ``correction_id`` is the id the store returned.
        """
        from ..dictation_learning import reach_for_gist
        from ..plugins.dictation.corrections import CORRECTION_KINDS
        from .dictation_files import _teach

        repo = self._repo()
        store = self._store()
        if kind not in CORRECTION_KINDS:
            raise _refused(400, {"error": f"kind must be one of {list(CORRECTION_KINDS)}"}, "invalid_kind")
        if kind == "text":
            said = said if isinstance(said, str) else value
            if not isinstance(said, str) or not said.strip():
                raise _refused(400, {"error": "said must be a non-empty string"}, "invalid_said")
        elif not isinstance(value, str) or not value.strip():
            raise _refused(400, {"error": "value must be a non-empty string"}, "invalid_value")
        entry = repo.get(int(entry_id))
        if entry is None:
            raise _refused(404, {"error": "entry not found"}, "not_found")
        if kind == "text":
            heard_text = heard if isinstance(heard, str) and heard.strip() else entry.transcript
            result = _teach(store, "text", heard=heard_text, said=said)
        else:
            result = _teach(store, kind, key=entry.transcript, value=value)
        recorded = bool(result["recorded"])
        correction_id = result["id"]
        if recorded:
            repo.mark_corrected(int(entry_id), correction_id=correction_id)
        # HS-48-02: a routing teach's honest reach (the digest's Jaccard count);
        # a `text` rule is exact-phrase and reaches 0.
        similar = (
            reach_for_gist(entry.transcript, [r.transcript for r in repo.recent()])
            if recorded and kind != "text" else 0
        )
        enabled = self._corrections_enabled()
        # HS-56-04: the presence surface hears only a real teach with real reach.
        if recorded and similar > 0 and self._broadcast is not None:
            gist = (entry.transcript or "").strip()
            self._broadcast("learning_event", {
                "kind": kind,
                "gist": gist[:120] + ("…" if len(gist) > 120 else ""),
                "value": str(result["value"] or "").strip(),
                "similar": int(similar),
                "enabled": enabled,
            })
        body: dict[str, Any] = {
            "corrected": recorded, "recorded": recorded,
            "taught": recorded,  # the long-standing mirror; `recorded` is canon
            "correction_id": correction_id, "size": len(store), "similar": similar, "enabled": enabled,
        }
        if recorded:
            body.update({"id": correction_id, "kind": result["kind"], "key": result["key"], "value": result["value"]})
        else:
            body["reason"] = result["reason"]
        return body

    # ── the corrections ──────────────────────────────────────────────────

    def _applied_counts(self) -> dict[int, int]:
        """HS-176-02 (R3): how many RETAINED journal rows each correction fired on."""
        repo = self._edits_of()
        if repo is None:
            return {}
        counts: dict[int, int] = {}
        try:
            for record in repo.recent():
                for raw_id in getattr(record, "corrections_applied", None) or []:
                    try:
                        correction_id = int(raw_id)
                    except (TypeError, ValueError):
                        continue
                    counts[correction_id] = counts.get(correction_id, 0) + 1
        except Exception:  # pragma: no cover - a read must never fail the list
            return {}
        return counts

    def list_corrections(self, principal: Principal) -> dict[str, Any]:
        """The taught rules; ``applied`` is the times each actually fired (R3)."""
        from ..plugins.dictation.corrections import CORRECTION_KINDS

        store = self._corrections_of()
        items = store.list_for_display() if store is not None else []
        counts = self._applied_counts()
        for item in items:
            try:
                item["applied"] = int(counts.get(int(item.get("id")), 0))  # type: ignore[arg-type]
            except (TypeError, ValueError):
                item["applied"] = 0
        return {
            "enabled": self._corrections_enabled(),
            "kinds": list(CORRECTION_KINDS),
            "size": len(store) if store is not None else 0,
            "items": items,
        }

    def learning_digest(self, principal: Principal, window: str = "week") -> dict[str, Any]:
        """HS-48-01: the read-only "What HoldSpeak learned" aggregation."""
        from ..dictation_learning import build_learning_digest

        store = self._corrections_of()
        repo = self._edits_of()
        rows = [
            {"transcript": r.transcript, "created_at": r.created_at, "corrected": r.corrected}
            for r in (repo.recent() if repo is not None else [])
        ]
        return build_learning_digest(
            corrections=store.list_for_display() if store is not None else [],
            journal_rows=rows, window=window, enabled=self._corrections_enabled(),
        )

    def teach(
        self, principal: Principal, *, kind: Any, text: Any = None, value: Any = None,
        heard: Any = None, said: Any = None,
    ) -> dict[str, Any]:
        """Teach one correction with no journal row (the fallback teach).

        Routing kinds take ``text`` (the gist) and ``value``; the ``text`` kind
        takes ``heard`` and ``said`` (``text``/``value`` as aliases), and the
        server runs the word-level diff.
        """
        from ..plugins.dictation.corrections import CORRECTION_KINDS
        from .dictation_files import _teach

        store = self._store()
        if kind not in CORRECTION_KINDS:
            raise _refused(400, {"error": f"kind must be one of {list(CORRECTION_KINDS)}"}, "invalid_kind")
        if kind == "text":
            heard = heard if isinstance(heard, str) else text
            said = said if isinstance(said, str) else value
            if not isinstance(heard, str) or not heard.strip():
                raise _refused(400, {"error": "heard must be a non-empty string"}, "invalid_heard")
            if not isinstance(said, str) or not said.strip():
                raise _refused(400, {"error": "said must be a non-empty string"}, "invalid_said")
            result = _teach(store, "text", heard=heard, said=said)
        else:
            if not isinstance(text, str) or not text.strip():
                raise _refused(400, {"error": "text must be a non-empty string"}, "invalid_text")
            if not isinstance(value, str) or not value.strip():
                raise _refused(400, {"error": "value must be a non-empty string"}, "invalid_value")
            result = _teach(store, kind, key=text, value=value)
        body: dict[str, Any] = {"recorded": bool(result["recorded"]), "size": len(store)}
        if result["recorded"]:
            body.update({"id": result["id"], "kind": result["kind"], "key": result["key"], "value": result["value"]})
        else:
            body["reason"] = result["reason"]
        return body

    def remove_correction(self, principal: Principal, correction_id: int) -> dict[str, Any]:
        """HS-40-04: remove one persistent correction by id."""
        store = self._store()
        if store.remove(int(correction_id)):
            return {"removed": True, "size": len(store)}
        raise _refused(404, {"removed": False, "error": "correction not found"}, "not_found")

    # ── the audio floor (HS-112-06): the browser's open mic on the one arbiter ──

    def claim_floor(self, principal: Principal, lease_seconds: Any = None) -> dict[str, Any]:
        """Claim the floor for the browser's open mic, on a lease; a held floor names its owner."""
        try:
            requested = float(lease_seconds) if lease_seconds is not None else None
        except (TypeError, ValueError):
            requested = None
        lease = DEFAULT_LEASE_SECONDS if requested is None or requested <= 0 else min(requested, MAX_LEASE_SECONDS)
        session = self._voice_session_of()
        if session is None:  # nothing to arbitrate against: say so
            return {"arbitrated": False, "held": True, "owner": OPEN_MIC_OWNER, "lease_seconds": lease}
        if session.acquire(OPEN_MIC_OWNER, lease_seconds=lease):
            return {"arbitrated": True, "held": True, "owner": OPEN_MIC_OWNER, "lease_seconds": lease}
        owner = session.active_owner
        log.info("audio_floor_open_mic_refused", extra={"active_owner": owner})
        raise _refused(409, {"success": False, "refusal": f"floor_held_{owner or 'unknown'}", "owner": owner,
                             "held": True, "arbitrated": True}, "floor_held")

    def release_floor(self, principal: Principal) -> dict[str, Any]:
        """Drop the browser's claim. Safe when it holds nothing."""
        session = self._voice_session_of()
        if session is not None:
            session.release(OPEN_MIC_OWNER)
        return {"held": False, "owner": None}

    # ── the project: context, agent hooks, .hs files, the KB ─────────────

    @staticmethod
    def _project(project_root: Optional[str]) -> dict[str, Any]:
        from .dictation_files import _resolve_project_context

        try:
            return _resolve_project_context(project_root)
        except ValueError as exc:
            raise _refused(400 if project_root else 404, {"error": str(exc)}, "project_not_found") from exc

    def project_context(self, principal: Principal, project_root: Optional[str] = None) -> dict[str, Any]:
        """Validate and describe the active or named dictation project root."""
        project = self._project(project_root)
        root = Path(project["root"])
        return {"project": project, "paths": {"blocks": str(root / ".holdspeak" / "blocks.yaml"),
                                              "project_kb": str(root / ".holdspeak" / "project.yaml")}}

    def agent_hooks(self, principal: Principal, capture_messages: bool = True) -> dict[str, Any]:
        """The copy-ready Claude and Codex hook templates and each agent's last session."""
        from ..agent_context import (
            AGENT_CONTEXT_FILE,
            claude_hook_template,
            codex_hook_template,
            get_recent_agent_session,
        )
        from ..agent_summarizer import summarizer_provider_statuses

        templates = {"claude": claude_hook_template(capture_messages=capture_messages),
                     "codex": codex_hook_template(capture_messages=capture_messages)}
        agents: dict[str, dict[str, Any]] = {}
        for agent, template in templates.items():
            latest = get_recent_agent_session(agent=agent, max_age_seconds=7 * 24 * 60 * 60)
            agents[agent] = {"latest_session": latest.to_dict() if latest else None, "template": template,
                             "template_json": json.dumps(template, indent=2, sort_keys=True)}
        return {
            "capture_messages": capture_messages,
            "registry_path": str(AGENT_CONTEXT_FILE),
            "destinations": {"claude": "~/.claude/settings.json or project .claude/settings.json",
                             "codex": "~/.codex/hooks.json or project .codex/hooks.json"},
            "summarizers": summarizer_provider_statuses(),
            "agents": agents,
        }

    def project_hs(self, principal: Principal, project_root: Optional[str] = None) -> dict[str, Any]:
        """The project's ``.hs`` context files."""
        from .dictation_files import _project_hs_payload

        return _project_hs_payload(self._project(project_root))

    def write_project_hs(self, principal: Principal, files: Any, project_root: Optional[str] = None) -> dict[str, Any]:
        """Write the named ``.hs`` files and answer the files as they now are."""
        from .dictation_files import _project_hs_payload, _resolve_project_context, _write_project_hs_files

        if not isinstance(files, dict):
            raise _refused(400, {"error": "request body must be {'files': {<filename>: <content>, ...}}"}, "invalid_files")
        project = self._project(project_root)
        try:
            _write_project_hs_files(Path(project["root"]), files)
        except ValueError as exc:
            raise _refused(400, {"error": str(exc)}, "invalid_files") from exc
        redetected = _resolve_project_context(project_root)
        self._config_changed()
        return _project_hs_payload(redetected)

    def project_kb(self, principal: Principal, project_root: Optional[str] = None) -> dict[str, Any]:
        """The project's facts (``.holdspeak/project.yaml``); no project found is an empty answer."""
        from ..plugins.dictation.project_kb import ProjectKBError, read_project_kb
        from .dictation_files import _resolve_project_context

        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            if project_root:
                raise _refused(400, {"error": str(exc)}, "project_not_found") from exc
            return {"detected": None, "kb": None, "kb_path": None,
                    "message": f"no project root detected from cwd={Path.cwd()}"}
        root = Path(project["root"])
        try:
            kb = read_project_kb(root)
        except ProjectKBError as exc:
            raise _refused(422, {"error": str(exc)}, "invalid_kb") from exc
        return {"detected": dict(project), "kb": kb, "kb_path": str(root / ".holdspeak" / "project.yaml")}

    def _kb_written(self, project: dict[str, Any], project_root: Optional[str]) -> dict[str, Any]:
        from ..plugins.dictation.project_kb import ProjectKBError, kb_path_for, read_project_kb
        from .dictation_files import _resolve_project_context

        root = Path(project["root"])
        self._config_changed()
        try:
            fresh = read_project_kb(root)
        except ProjectKBError as exc:
            raise _refused(500, {"error": str(exc)}, "invalid_kb") from exc
        # Re-detect: a write that made `<root>/.holdspeak/` upgrades the anchor.
        redetected = _resolve_project_context(project_root) if project_root else project
        return {"detected": dict(redetected), "kb": fresh, "kb_path": str(kb_path_for(root))}

    def write_project_kb(self, principal: Principal, kb: Any, project_root: Optional[str] = None) -> dict[str, Any]:
        """Replace the project's facts."""
        from ..plugins.dictation.project_kb import ProjectKBError, write_project_kb

        if not isinstance(kb, dict):
            raise _refused(400, {"error": "request body must be {'kb': {<key>: <value>, ...}}"}, "invalid_kb")
        project = self._project(project_root)
        try:
            write_project_kb(Path(project["root"]), kb)
        except ProjectKBError as exc:
            raise _refused(422, {"error": str(exc)}, "invalid_kb") from exc
        return self._kb_written(project, project_root)

    def start_project_kb(self, principal: Principal, project_root: Optional[str] = None) -> dict[str, Any]:
        """Write the starter facts file; one that exists refuses."""
        from ..plugins.dictation.project_kb import ProjectKBError, kb_path_for, write_project_kb
        from .dictation_files import _STARTER_PROJECT_KB

        project = self._project(project_root)
        path = kb_path_for(Path(project["root"]))
        if path.exists():
            raise _refused(409, {"error": f"project KB already exists at {path}"}, "kb_exists")
        try:
            write_project_kb(Path(project["root"]), _STARTER_PROJECT_KB)
        except ProjectKBError as exc:
            raise _refused(422, {"error": str(exc)}, "invalid_kb") from exc
        return {**self._kb_written(project, project_root), "starter": True}

    # ── the blocks ───────────────────────────────────────────────────────

    def block_templates(self, principal: Principal) -> dict[str, Any]:
        from .dictation_files import _STARTER_BLOCK_TEMPLATES

        keys = ("id", "title", "description", "sample_utterance", "requires_project")
        return {"templates": [{**{key: template[key] for key in keys}, "block": deepcopy(template["block"])}
                              for template in _STARTER_BLOCK_TEMPLATES]}

    @staticmethod
    def _blocks_target(scope: str, project_root: Optional[str]) -> tuple[Path, Optional[dict[str, Any]]]:
        from .dictation_files import _resolve_blocks_target

        try:
            return _resolve_blocks_target(scope, project_root)
        except ValueError as exc:
            missing = "no project detected" in str(exc)
            raise _refused(404 if missing else 400, {"error": str(exc)},
                           "project_not_found" if missing else "invalid_scope") from exc

    @staticmethod
    def _blocks_document(path: Path) -> tuple[dict[str, Any], bool]:
        from .dictation_files import _read_blocks_document

        try:
            return _read_blocks_document(path)
        except Exception as exc:
            log.error(f"Failed to read blocks document: {exc}")
            raise _refused(500, {"error": str(exc)}, "unreadable") from exc

    def _save_blocks(self, path: Path, document: dict[str, Any]) -> None:
        from ..plugins.dictation.blocks import BlockConfigError, save_blocks_yaml

        try:
            save_blocks_yaml(path, document)
        except BlockConfigError as exc:
            raise _refused(422, {"error": str(exc)}, "invalid_blocks") from exc
        self._config_changed()

    def list_blocks(self, principal: Principal, scope: str = "global", project_root: Optional[str] = None) -> dict[str, Any]:
        """The blocks document of one scope, validated."""
        from ..plugins.dictation.blocks import BlockConfigError, load_blocks_yaml

        path, project = self._blocks_target(scope, project_root)
        try:
            document, exists = self._blocks_document(path)
            if exists:
                load_blocks_yaml(path)  # validate, surface errors to the face
        except BlockConfigError as exc:
            raise _refused(422, {"error": str(exc), "scope": scope, "path": str(path)}, "invalid_blocks") from exc
        return {"scope": scope, "path": str(path), "exists": exists, "project": project, "document": document}

    def create_block(self, principal: Principal, block: Any, scope: str = "global",
                     project_root: Optional[str] = None) -> dict[str, Any]:
        if not isinstance(block, dict):
            raise _refused(400, {"error": "request body must be {'block': {...}}"}, "invalid_block")
        path, _project = self._blocks_target(scope, project_root)
        document, _exists = self._blocks_document(path)
        new_id = block.get("id")
        if new_id in {b.get("id") for b in document["blocks"] if isinstance(b, dict)}:
            raise _refused(409, {"error": f"block id {new_id!r} already exists"}, "conflict")
        document["blocks"].append(block)
        self._save_blocks(path, document)
        return {"scope": scope, "path": str(path), "document": document}

    def _existing_blocks(self, scope: str, project_root: Optional[str]) -> tuple[Path, dict[str, Any]]:
        path, _project = self._blocks_target(scope, project_root)
        if not path.exists():
            raise _refused(404, {"error": f"no blocks file at {path}"}, "not_found")
        return path, self._blocks_document(path)[0]

    def update_block(self, principal: Principal, block_id: str, block: Any, scope: str = "global",
                     project_root: Optional[str] = None) -> dict[str, Any]:
        if not isinstance(block, dict):
            raise _refused(400, {"error": "request body must be {'block': {...}}"}, "invalid_block")
        path, document = self._existing_blocks(scope, project_root)
        blocks = document["blocks"]
        index = next((i for i, b in enumerate(blocks) if isinstance(b, dict) and b.get("id") == block_id), None)
        if index is None:
            raise _refused(404, {"error": f"unknown block id {block_id!r}"}, "not_found")
        new_id = block.get("id", block_id)
        if new_id != block_id and any(isinstance(b, dict) and b.get("id") == new_id for b in blocks):
            raise _refused(409, {"error": f"block id {new_id!r} already exists"}, "conflict")
        blocks[index] = block
        self._save_blocks(path, document)
        return {"scope": scope, "path": str(path), "document": document}

    def delete_block(self, principal: Principal, block_id: str, scope: str = "global",
                     project_root: Optional[str] = None) -> dict[str, Any]:
        path, document = self._existing_blocks(scope, project_root)
        blocks = document["blocks"]
        kept = [b for b in blocks if not (isinstance(b, dict) and b.get("id") == block_id)]
        if len(kept) == len(blocks):
            raise _refused(404, {"error": f"unknown block id {block_id!r}"}, "not_found")
        document["blocks"] = kept
        # save_blocks_yaml refuses an empty list (422): delete-then-recreate.
        self._save_blocks(path, document)
        return {"scope": scope, "path": str(path), "document": document}

    @staticmethod
    def _csv_value(value: Any) -> Any:
        if isinstance(value, (dict, list)):
            return json.dumps(value, sort_keys=True)
        return value

    @staticmethod
    def _entry(record: Any) -> dict[str, Any]:
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
            # HS-176-02 (R5): the two stored facts, split and both named.
            # `taught_from` is the existing `corrected` column under its true
            # meaning — "he taught FROM this row"; `corrections_applied` is the
            # new per-run fact — "these stored rules fired ON this row". The
            # `getattr` keeps a record shape that predates the column working.
            "taught_from": bool(record.corrected),
            "corrections_applied": [
                int(x) for x in (getattr(record, "corrections_applied", None) or [])
            ],
        }
