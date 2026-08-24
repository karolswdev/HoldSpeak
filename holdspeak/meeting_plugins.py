"""HS-80-01 — the persisted-meeting plugin-run seam.

The Phase-67 dogfood run's headline finding (F-05): imported meetings never
receive typed plugin artifacts, because the MIR router + plugin host run only
on LIVE meeting windows (`runtime/routing_glue.py`). This module is the missing
seam: run the routed plugin chain over a *saved* meeting's full transcript and
persist exactly what the live path persists — one intent window, the per-plugin
run records, and the synthesized typed artifacts.

Design (the phase's load-bearing call):

- **Pure module, host built on demand.** No web-runtime state; callable from the
  deferred-intel processor (HS-80-02), the reroute CLI/API (HS-80-03), and
  tests. The live windowed path is untouched.
- **Idempotent by construction.** The window id is stable
  (``{meeting_id}:full``) and the host's idempotency key is
  meeting/window/plugin/transcript-hash, so re-running an unchanged meeting
  dedups instead of duplicating; artifact synthesis upserts by artifact id.
- **Actuators stay proposal-only** (`allow_actuators=False` on the standalone
  host — proposing is always allowed, executing is the approval flow's job).
- **Heavy plugins run inline** (``defer_heavy=False``): callers are background
  contexts (the queue, the CLI), not a latency-budgeted UI thread.
"""

from __future__ import annotations

import hashlib
from typing import Any, Mapping, Optional

from .logging_config import get_logger

log = get_logger("meeting_plugins")

#: The one full-transcript window this seam writes per meeting.
FULL_WINDOW_SUFFIX = "full"

# These outcomes have no remaining execution for the same transcript. Errors,
# timeouts, capability blocks, and queued work remain eligible for an exact-key
# retry; a disabled plugin's explicit ``skipped`` outcome is already resolved.
COMPLETED_PLUGIN_STATUSES = frozenset(
    {"success", "proposed", "deduped", "skipped"}
)


def _meeting_transcript(meeting: Any) -> str:
    lines: list[str] = []
    for segment in getattr(meeting, "segments", []) or []:
        text = str(getattr(segment, "text", "") or "").strip()
        if not text:
            continue
        speaker = str(getattr(segment, "speaker", "") or "").strip()
        lines.append(f"{speaker}: {text}" if speaker else text)
    return "\n".join(lines)


def _meeting_tags(meeting: Any) -> list[str]:
    tags: list[str] = []
    for raw in getattr(meeting, "tags", []) or []:
        tag = str(raw).strip().lower()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def _build_host() -> Any:
    """A standalone `PluginHost` mirroring the web runtime's registry: the
    built-ins + the project detector (fed the same detector snapshot), the
    LLM capability resolved from config, actuators proposal-only."""
    from .config import Config
    from .intel import resolve_llm_capability
    from .plugins.builtin import register_builtin_plugins
    from .plugins.host import PluginHost
    from .plugins.project_detector import ProjectDetectorPlugin

    llm_enabled = resolve_llm_capability(Config.load().meeting)
    host = PluginHost(
        default_timeout_seconds=30.0,
        enabled_capabilities={"llm"} if llm_enabled else None,
        allow_actuators=False,
    )
    register_builtin_plugins(host)

    detector = ProjectDetectorPlugin()
    try:
        from .db import get_database

        detector.reload_projects(get_database().projects.get_all_projects_for_detector())
    except Exception as exc:  # pragma: no cover - projects are optional context
        log.warning(f"meeting_plugins: could not load projects for detector: {exc}")
    host.register(detector)
    return host


def run_meeting_plugin_chain(
    db: Any,
    meeting: Any,
    *,
    profile: Optional[str] = None,
    override_intents: Optional[list[str]] = None,
    threshold: Optional[float] = None,
    window_suffix: str = FULL_WINDOW_SUFFIX,
    host: Any = None,
    record_window: bool = True,
    admission: Any = None,
) -> dict[str, Any]:
    """Route + execute the plugin chain for a SAVED meeting and persist the lot.

    Returns an honest summary: the route, per-plugin statuses, and the artifact
    count. Never raises for plugin failures (the host isolates those into
    per-run `error` records); raises only on a truly empty meeting.

    ``admission`` (HS-131-08) is a
    :class:`~holdspeak.meeting_session.deferred_admission.DeferredIntelJob`. When
    supplied, each EXECUTED plugin runs as one trusted child of that job parent
    and its run record + synthesized artifacts are staged projections written
    only from the winning receipt. Route order, the exact
    ``build_idempotency_key`` dedup, injected faults, and every persisted field
    are unchanged; deduped/skipped/faulted plugins still issue no child.
    """
    from .plugins.router import DEFAULT_INTENT_THRESHOLD, preview_route_from_transcript
    from .plugins.synthesis import synthesize_meeting_artifacts

    meeting_id = str(getattr(meeting, "id", "") or "").strip()
    transcript = _meeting_transcript(meeting)
    if not meeting_id or not transcript:
        raise ValueError("meeting has no id or no transcript to route")

    tags = _meeting_tags(meeting)
    effective_threshold = (
        DEFAULT_INTENT_THRESHOLD if threshold is None else float(threshold)
    )
    route = preview_route_from_transcript(
        profile=profile,
        transcript=transcript,
        tags=tags,
        threshold=effective_threshold,
        override_intents=override_intents,
    )
    route_payload = route.to_dict()
    window_id = f"{meeting_id}:{window_suffix}"
    transcript_hash = hashlib.sha256(transcript.encode("utf-8")).hexdigest()

    duration = float(getattr(meeting, "duration", 0.0) or 0.0)
    # A reroute caller records its own window (with the manual-override
    # provenance); this seam then executes against that same window id.
    if record_window:
        db.plugins.record_intent_window(
            meeting_id=meeting_id,
            window_id=window_id,
            start_seconds=0.0,
            end_seconds=duration,
            transcript_hash=transcript_hash,
            transcript_excerpt=transcript[:400],
            profile=str(route_payload.get("profile") or "balanced"),
            threshold=float(route_payload.get("threshold") or effective_threshold),
            active_intents=[
                str(i).strip().lower()
                for i in (route_payload.get("active_intents") or [])
                if str(i).strip()
            ],
            intent_scores={
                str(k).strip().lower(): float(v)
                for k, v in dict(route_payload.get("intent_scores") or {}).items()
                if str(k).strip()
            },
            override_intents=[
                str(i).strip().lower()
                for i in (override_intents or [])
                if str(i).strip()
            ],
            tags=tags,
            metadata={"source": "meeting_plugins", "window": window_suffix},
        )

    # DB-backed idempotency (the host's in-memory cache dies with the process,
    # and LLM-shaped plugin outputs vary per execution, which would mint new
    # artifact ids every rerun): when every planned key for THIS transcript
    # already has a persisted run, nothing changed — dedup instead of stacking.
    from .plugins.host import build_idempotency_key

    plugin_chain = list(route_payload.get("plugin_chain") or [])
    planned_keys = {
        plugin_id: build_idempotency_key(
            meeting_id=meeting_id,
            window_id=window_id,
            plugin_id=plugin_id,
            transcript_hash=transcript_hash,
        )
        for plugin_id in plugin_chain
    }
    existing_completed_keys = {
        str(run.idempotency_key)
        for run in db.plugins.list_plugin_runs(meeting_id, limit=5000)
        if (
            str(getattr(run, "window_id", "")) == window_id
            and run.idempotency_key
            and str(getattr(run, "status", "")).strip().lower()
            in COMPLETED_PLUGIN_STATUSES
        )
    }
    remaining_chain = [
        plugin_id
        for plugin_id in plugin_chain
        if planned_keys[plugin_id] not in existing_completed_keys
    ]
    if plugin_chain and not remaining_chain:
        artifacts_existing = db.plugins.list_artifacts(meeting_id)
        summary = {
            "meeting_id": meeting_id,
            "window_id": window_id,
            "profile": route_payload.get("profile"),
            "active_intents": list(route_payload.get("active_intents") or []),
            "plugin_chain": plugin_chain,
            "plugin_statuses": {p: "deduped" for p in plugin_chain},
            "artifacts_saved": 0,
            "deduped": True,
        }
        log.info(
            "meeting_plugins: %s unchanged (window %s) — deduped, %d artifact(s) kept",
            meeting_id, window_id, len(artifacts_existing),
        )
        return summary

    # HS-93-06 fault plane: fail exactly the plugin keys named via
    # ``HOLDSPEAK_FAULT=intel.plugin:<id>``. Each faulted key persists the same
    # `error` run record a real plugin failure persists (keyed by the planned
    # idempotency key, so a later un-faulted retry executes exactly that key),
    # and the rest of the chain proceeds untouched.
    from .faults import FAULT_ENV, PLUGIN_FAULT_PREFIX, faulted_plugin_keys

    injected_faults = sorted(faulted_plugin_keys().intersection(remaining_chain))
    if injected_faults:
        for plugin_id in injected_faults:
            db.plugins.record_plugin_run(
                meeting_id=meeting_id,
                window_id=window_id,
                plugin_id=plugin_id,
                plugin_version="unknown",
                status="error",
                idempotency_key=planned_keys[plugin_id],
                duration_ms=0.0,
                output=None,
                error=f"{FAULT_ENV}={PLUGIN_FAULT_PREFIX}{plugin_id} injected failure",
                deduped=False,
            )
        log.warning(
            "meeting_plugins: %s injected plugin fault(s) for %s",
            meeting_id, ", ".join(injected_faults),
        )
        remaining_chain = [
            plugin_id for plugin_id in remaining_chain
            if plugin_id not in set(injected_faults)
        ]

    if host is None:
        host = _build_host()
    transcript_segments = [
        {
            "text": str(getattr(segment, "text", "") or ""),
            "speaker": str(getattr(segment, "speaker", "") or ""),
            "start_time": float(getattr(segment, "start_time", 0.0)),
            "end_time": float(getattr(segment, "end_time", 0.0)),
        }
        for segment in (getattr(meeting, "segments", []) or [])
    ]
    context = {
        "transcript": transcript,
        "transcript_segments": transcript_segments,
        "tags": tags,
        "active_intents": list(route_payload.get("active_intents") or []),
        "intent_scores": dict(route_payload.get("intent_scores") or {}),
        "profile": route_payload.get("profile"),
        "threshold": route_payload.get("threshold"),
    }
    def _run_chain(chain: list[str], dispatch: Any = None) -> list[Any]:
        return host.execute_chain(
            chain,
            context=context,
            meeting_id=meeting_id,
            window_id=window_id,
            transcript_hash=transcript_hash,
            defer_heavy=False,
            dispatch=dispatch,
        )

    def _execute(chain: list[str], engine: Any = None, cancellation: Any = None) -> list[Any]:
        # HS-131-08 / HS-131-14: under an admitted plugin child, `engine` is the
        # engine built from the deployment revision that child NAMES, and
        # `cancellation` is that child's signal. The host issues ONE dispatch
        # handle over the pair and hands it to exactly this run — no host state,
        # no plugin state, nothing a later child could borrow. An UNADMITTED
        # caller passes neither, and every `llm` plugin refuses by name rather
        # than resolving a provider of its own.
        if engine is None:
            return _run_chain(chain)
        issuer = getattr(host, "issued_dispatch", None)
        if issuer is None:
            # An admitted child names ONE deployment revision. A host that cannot
            # be handed that engine would silently build its own, so it refuses.
            from .plugins.host import PluginEngineNotInjectable

            raise PluginEngineNotInjectable(type(host).__name__)
        with issuer(engine, cancellation) as dispatch:
            return _run_chain(chain, dispatch)

    if admission is None:
        results = _execute(remaining_chain)
        for result in results:
            record = result.to_dict()
            db.plugins.record_plugin_run(
                meeting_id=meeting_id,
                window_id=window_id,
                plugin_id=str(record.get("plugin_id") or ""),
                plugin_version=str(record.get("plugin_version") or "unknown"),
                status=str(record.get("status") or "unknown"),
                idempotency_key=str(record.get("idempotency_key") or "") or None,
                duration_ms=float(record.get("duration_ms") or 0.0),
                output=record.get("output") if isinstance(record.get("output"), dict) else None,
                error=str(record.get("error")) if record.get("error") else None,
                deduped=bool(record.get("deduped")),
            )

        runs = db.plugins.list_plugin_runs(meeting_id, limit=5000)
        artifacts = synthesize_meeting_artifacts(
            meeting_id=meeting_id, plugin_runs=runs, max_artifacts=500
        )
        for artifact in artifacts:
            db.plugins.record_artifact(
                artifact_id=artifact.artifact_id,
                meeting_id=artifact.meeting_id,
                artifact_type=artifact.artifact_type,
                title=artifact.title,
                body_markdown=artifact.body_markdown,
                structured_json=artifact.structured_json,
                confidence=artifact.confidence,
                status=artifact.status,
                plugin_id=artifact.plugin_id,
                plugin_version=artifact.plugin_version,
                sources=[source.to_dict() for source in artifact.sources],
            )
        artifacts_saved = len(artifacts)
    else:
        results, artifacts_saved = _run_admitted_chain(
            db,
            admission,
            remaining_chain,
            execute=_execute,
            meeting_id=meeting_id,
            window_id=window_id,
            transcript_hash=transcript_hash,
            planned_keys=planned_keys,
        )

    summary = {
        "meeting_id": meeting_id,
        "window_id": window_id,
        "profile": route_payload.get("profile"),
        "active_intents": list(route_payload.get("active_intents") or []),
        "plugin_chain": list(route_payload.get("plugin_chain") or []),
        "plugin_statuses": {
            **{
                plugin_id: "deduped"
                for plugin_id in plugin_chain
                if planned_keys[plugin_id] in existing_completed_keys
            },
            **{plugin_id: "error" for plugin_id in injected_faults},
            **{str(r.plugin_id): str(r.status) for r in results},
        },
        "artifacts_saved": artifacts_saved,
    }
    log.info(
        "meeting_plugins: %s ran %d plugin(s), %d artifact(s) synthesized",
        meeting_id, len(results), artifacts_saved,
    )
    return summary


def _run_admitted_chain(
    db: Any,
    admission: Any,
    remaining_chain: list[str],
    *,
    execute: Any,
    meeting_id: str,
    window_id: str,
    transcript_hash: str,
    planned_keys: dict[str, str],
) -> tuple[list[Any], int]:
    """Run the remaining chain IN ORDER, one trusted child per executed plugin.

    A REFUSED plugin (capability absent from the job's frozen plan, an expired or
    cancelled job parent) issues no provider request, so — exactly like an
    injected plugin fault — it persists the same ``error`` run record any other
    unresolved plugin persists, keyed by its exact planned idempotency key. The
    job stays honestly partial and an exact-key retry can still execute it later.

    A plugin whose child ran but never published (cancelled, expired,
    indeterminate) writes NOTHING at all: its output is fenced by the parent
    election, and only its unresolved status reaches the summary.
    """
    from .plugins.host import PluginRunResult

    results: list[Any] = []
    artifacts_saved = 0
    for plugin_id in remaining_chain:
        key = planned_keys.get(plugin_id) or ""
        try:
            _, projection, produced = admission.plugin(
                plugin_id,
                window_id=window_id,
                idempotency_key=key,
                transcript_hash=transcript_hash,
                # The engine the child's frozen revision built is threaded in with
                # that child's cancellation signal, and the whole plugin execution
                # happens INSIDE the child's dispatch — inside its cancellation
                # seam, never beside it.
                execute=lambda engine, cancellation, plugin_id=plugin_id: (
                    (execute([plugin_id], engine, cancellation) or [None])[0].to_dict()
                ),
            )
        except Exception as exc:
            reason = str(getattr(exc, "reason", "") or f"{type(exc).__name__}: {exc}")
            results.append(PluginRunResult(
                plugin_id=plugin_id, plugin_version="unknown", status="error",
                idempotency_key=key, duration_ms=0.0, error=reason,
            ))
            db.plugins.record_plugin_run(
                meeting_id=meeting_id, window_id=window_id, plugin_id=plugin_id,
                plugin_version="unknown", status="error", idempotency_key=key or None,
                duration_ms=0.0, output=None, error=reason, deduped=False,
            )
            log.warning("meeting_plugins: %s refused for %s: %s", plugin_id, meeting_id, reason)
            continue
        if projection is None:
            # Cancelled/expired/indeterminate: nothing was written and nothing may
            # be claimed. The plugin stays unresolved, exactly like a timeout.
            results.append(PluginRunResult(
                plugin_id=plugin_id, plugin_version="unknown", status="error",
                idempotency_key=key, duration_ms=0.0,
                error="Routed plugin did not publish under the deferred job.",
            ))
            continue
        record = dict(produced or {})
        results.append(PluginRunResult(
            plugin_id=str(record.get("plugin_id") or plugin_id),
            plugin_version=str(record.get("plugin_version") or "unknown"),
            status=str(record.get("status") or "unknown"),
            idempotency_key=str(record.get("idempotency_key") or key),
            duration_ms=float(record.get("duration_ms") or 0.0),
            output=record.get("output") if isinstance(record.get("output"), dict) else None,
            error=str(record.get("error")) if record.get("error") else None,
            deduped=bool(record.get("deduped")),
        ))
        artifacts_saved = int(dict(projection).get("artifacts_saved") or artifacts_saved)
    return results, artifacts_saved


def build_bound_meeting_plugin_host() -> Any:
    """Build the C2 installed host without a Config-time capability decision.

    A bound child already owns the selected model route.  The host only needs a
    per-invocation dispatch handle over that child engine, so consulting mutable
    meeting runtime settings here would create a second authority.
    """
    from .plugins.builtin import register_builtin_plugins
    from .plugins.host import PluginHost
    from .plugins.project_detector import ProjectDetectorPlugin

    host = PluginHost(
        default_timeout_seconds=30.0,
        enabled_capabilities={"llm"},
        allow_actuators=False,
    )
    register_builtin_plugins(host)
    detector = ProjectDetectorPlugin()
    try:
        from .db import get_database

        detector.reload_projects(get_database().projects.get_all_projects_for_detector())
    except Exception as exc:  # optional detector context is never routing authority
        log.warning("meeting_plugins: could not load projects for bound host: %s", exc)
    host.register(detector)
    return host


def _bound_plugin_error(
    db: Any,
    *,
    meeting_id: str,
    window_id: str,
    plugin_id: str,
    plugin_version: str,
    idempotency_key: str,
    error: str,
    status: str = "error",
) -> None:
    """Persist a non-model plugin disposition before any child may exist."""
    db.plugins.record_plugin_run(
        meeting_id=meeting_id,
        window_id=window_id,
        plugin_id=plugin_id,
        plugin_version=plugin_version or "unknown",
        status=status,
        idempotency_key=idempotency_key or None,
        duration_ms=0.0,
        output=None,
        error=error,
        deduped=False,
    )


def run_bound_meeting_plugin_chain(
    db: Any,
    meeting: Any,
    *,
    bound: Any,
    job: Any,
    host: Any = None,
) -> dict[str, Any]:
    """Run only C2 descriptor members as receipt-gated routed children.

    The descriptor's frozen route controls the chain.  Dedup, explicit disable,
    and fault injection settle before a child admission.  For an executed child,
    only the plugin's inner ``output`` crosses the semantic adapter; run metadata
    is projection evidence and never a capability result.
    """
    from .faults import FAULT_ENV, PLUGIN_FAULT_PREFIX, faulted_plugin_keys
    from .plugins.host import PluginRunResult, build_idempotency_key

    meeting_id = str(getattr(meeting, "id", "") or "").strip()
    transcript = _meeting_transcript(meeting)
    if not meeting_id or not transcript:
        raise ValueError("meeting has no id or no transcript to route")
    route = dict(getattr(job, "frozen_plugin_route", {}) or {})
    chain = [str(item).strip() for item in route.get("plugin_chain") or [] if str(item).strip()]
    frozen_by_id = {
        str(item.get("plugin_id") or ""): dict(item)
        for item in tuple(getattr(job, "frozen_plugin_members", ()) or ())
        if isinstance(item, Mapping)
    }
    window_id = f"{meeting_id}:{FULL_WINDOW_SUFFIX}"
    transcript_hash = hashlib.sha256(transcript.encode("utf-8")).hexdigest()
    tags = _meeting_tags(meeting)
    db.plugins.record_intent_window(
        meeting_id=meeting_id,
        window_id=window_id,
        start_seconds=0.0,
        end_seconds=float(getattr(meeting, "duration", 0.0) or 0.0),
        transcript_hash=transcript_hash,
        transcript_excerpt=transcript[:400],
        profile=str(route.get("profile") or "balanced"),
        threshold=float(route.get("threshold") or 0.0),
        active_intents=[str(item) for item in route.get("active_intents") or []],
        intent_scores={str(key): float(value) for key, value in dict(route.get("intent_scores") or {}).items()},
        override_intents=[],
        tags=tags,
        metadata={"source": "meeting_plugins_bound", "window": FULL_WINDOW_SUFFIX},
    )
    keys = {
        plugin_id: build_idempotency_key(
            meeting_id=meeting_id,
            window_id=window_id,
            plugin_id=plugin_id,
            transcript_hash=transcript_hash,
        )
        for plugin_id in chain
    }
    complete = {
        str(run.idempotency_key)
        for run in db.plugins.list_plugin_runs(meeting_id, limit=5000)
        if str(getattr(run, "window_id", "")) == window_id
        and str(getattr(run, "status", "")).strip().lower() in COMPLETED_PLUGIN_STATUSES
        and getattr(run, "idempotency_key", None)
    }
    statuses: dict[str, str] = {
        plugin_id: "deduped" for plugin_id in chain if keys[plugin_id] in complete
    }
    remaining = [plugin_id for plugin_id in chain if plugin_id not in statuses]

    # Fault injection is an explicit non-model disposition.  It must precede host
    # validation and child admission, so faulted work cannot mint a model child.
    faults = set(faulted_plugin_keys()).intersection(remaining)
    for plugin_id in sorted(faults):
        frozen = frozen_by_id.get(plugin_id, {})
        _bound_plugin_error(
            db,
            meeting_id=meeting_id,
            window_id=window_id,
            plugin_id=plugin_id,
            plugin_version=str(frozen.get("plugin_definition_revision") or "unknown"),
            idempotency_key=keys[plugin_id],
            error=f"{FAULT_ENV}={PLUGIN_FAULT_PREFIX}{plugin_id} injected failure",
        )
        statuses[plugin_id] = "error"
    remaining = [plugin_id for plugin_id in remaining if plugin_id not in faults]

    if host is None:
        host = build_bound_meeting_plugin_host()
    disabled = {
        str(item).strip()
        for item in (getattr(host, "disabled_plugins", ()) or ())
        if str(item).strip()
    }
    context = {
        "transcript": transcript,
        "transcript_segments": [
            {
                "text": str(getattr(segment, "text", "") or ""),
                "speaker": str(getattr(segment, "speaker", "") or ""),
                "start_time": float(getattr(segment, "start_time", 0.0)),
                "end_time": float(getattr(segment, "end_time", 0.0)),
            }
            for segment in (getattr(meeting, "segments", []) or [])
        ],
        "tags": tags,
        "active_intents": list(route.get("active_intents") or []),
        "intent_scores": dict(route.get("intent_scores") or {}),
        "profile": route.get("profile"),
        "threshold": route.get("threshold"),
    }
    artifacts_saved = 0
    for plugin_id in remaining:
        frozen = frozen_by_id.get(plugin_id)
        key = keys[plugin_id]
        if frozen is None:
            _bound_plugin_error(
                db, meeting_id=meeting_id, window_id=window_id, plugin_id=plugin_id,
                plugin_version="unknown", idempotency_key=key,
                error="frozen_plugin_descriptor_member_missing",
            )
            statuses[plugin_id] = "refused"
            continue
        expected_version = str(frozen["plugin_definition_revision"])
        if plugin_id in disabled:
            _bound_plugin_error(
                db, meeting_id=meeting_id, window_id=window_id, plugin_id=plugin_id,
                plugin_version=expected_version, idempotency_key=key,
                error="disabled for this project", status="skipped",
            )
            statuses[plugin_id] = "skipped"
            continue
        plugin = getattr(host, "get_plugin", lambda _plugin_id: None)(plugin_id)
        if (
            plugin is None
            or str(getattr(plugin, "id", "") or "") != plugin_id
            or str(getattr(plugin, "version", "") or "") != expected_version
        ):
            _bound_plugin_error(
                db, meeting_id=meeting_id, window_id=window_id, plugin_id=plugin_id,
                plugin_version=expected_version, idempotency_key=key,
                error="installed_plugin_host_revision_drift",
            )
            statuses[plugin_id] = "refused"
            continue
        try:
            # All descriptor/bundle/frozen-capability checks complete before the
            # child exists.  This is the no-child line for unknown/drift work.
            bound.require_frozen_plugin_member(frozen)
        except Exception as exc:
            _bound_plugin_error(
                db, meeting_id=meeting_id, window_id=window_id, plugin_id=plugin_id,
                plugin_version=expected_version, idempotency_key=key,
                error=str(getattr(exc, "reason", "") or "frozen_plugin_bundle_drift"),
            )
            statuses[plugin_id] = "refused"
            continue

        record_box: dict[str, Any] = {}

        def call(engine: Any, _payload: Mapping[str, Any], cancellation: Any, *, _plugin_id: str = plugin_id) -> Mapping[str, Any]:
            issuer = getattr(host, "issued_dispatch", None)
            if issuer is None:
                raise RuntimeError("plugin_host_dispatch_unavailable")
            with issuer(engine, cancellation) as dispatch:
                runs = host.execute_chain(
                    [_plugin_id], context=dict(context), meeting_id=meeting_id,
                    window_id=window_id, transcript_hash=transcript_hash,
                    defer_heavy=False, dispatch=dispatch,
                )
            record = (runs or [PluginRunResult(
                plugin_id=_plugin_id, plugin_version=expected_version, status="error",
                idempotency_key=key, duration_ms=0.0, error="plugin returned no record",
            )])[0].to_dict()
            record_box.update(record)
            output = record.get("output")
            if not isinstance(output, dict):
                raise ValueError("plugin did not return an inner output mapping")
            return output

        try:
            projection, routed = bound.execute(
                capability=str(frozen["capability_id"]),
                operation_suffix=f"plugin:{plugin_id}:{key}",
                material={
                    "plugin_id": plugin_id,
                    "plugin_definition_revision": expected_version,
                    "window_id": window_id,
                    "idempotency_key": key,
                    "transcript_sha256": "sha256:" + transcript_hash,
                    "template_revision": "1",
                    "transcript_material": transcript,
                },
                call=call,
                projection_kind="meeting-bound-plugin-result",
                projection=lambda output, _frozen=frozen, _plugin_id=plugin_id: {
                    "job_id": str(job.job_id),
                    "meeting_id": meeting_id,
                    "transcript_hash": str(job.transcript_hash),
                    "work_descriptor_sha256": str(job.work_descriptor_sha256 or ""),
                    "executor_lease_token": str(job.executor_lease_token or ""),
                    "executor_lease_epoch": int(job.executor_lease_epoch or 0),
                    "window_id": window_id,
                    "plugin_id": _plugin_id,
                    "plugin_version": str(_frozen["plugin_definition_revision"]),
                    "plugin_definition_revision": str(_frozen["plugin_definition_revision"]),
                    "capability_id": str(_frozen["capability_id"]),
                    "capability_revision": int(_frozen["capability_revision"]),
                    "capability_schema_sha256": str(_frozen["schema_sha256"]),
                    "status": str(record_box.get("status") or "success"),
                    "idempotency_key": str(record_box.get("idempotency_key") or key),
                    "duration_ms": float(record_box.get("duration_ms") or 0.0),
                    "output": dict(output),
                    "error": "",
                    "deduped": False,
                },
            )
        except Exception as exc:
            reason = str(getattr(exc, "reason", "") or f"{type(exc).__name__}: {exc}")
            log.warning("meeting_plugins: bound %s failed before publication: %s", plugin_id, reason)
            _bound_plugin_error(
                db, meeting_id=meeting_id, window_id=window_id, plugin_id=plugin_id,
                plugin_version=expected_version, idempotency_key=key,
                error=reason,
            )
            statuses[plugin_id] = "error"
            continue
        if projection is None:
            statuses[plugin_id] = "error"
            continue
        statuses[plugin_id] = str(record_box.get("status") or "success")
        artifacts_saved = int(dict(projection).get("artifacts_saved") or artifacts_saved)

    return {
        "meeting_id": meeting_id,
        "window_id": window_id,
        "profile": route.get("profile"),
        "active_intents": list(route.get("active_intents") or []),
        "plugin_chain": chain,
        "plugin_statuses": statuses,
        "artifacts_saved": artifacts_saved,
    }
