"""Deferred meeting-intelligence queue command."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
import sys
from typing import Any, Optional

from ..config import Config
from ..db import IntelJob, get_database
from ..intel import get_intel_runtime_status
from ..intel_queue import drain_intel_queue
from ..plugins.router import (
    DEFAULT_INTENT_THRESHOLD,
    SUPPORTED_INTENTS,
    available_profiles,
    normalize_override_intents,
    preview_route_from_transcript,
)


def run_intel_command(args) -> int:
    """Handle the `intel` subcommand."""
    db = get_database()

    route_dry_run_meeting_id = str(getattr(args, "route_dry_run", "") or "").strip()
    reroute_meeting_id = str(getattr(args, "reroute", "") or "").strip()
    if route_dry_run_meeting_id:
        return _run_mir_route_command(
            db=db,
            meeting_id=route_dry_run_meeting_id,
            profile_arg=getattr(args, "profile", None),
            threshold_arg=getattr(args, "threshold", None),
            override_arg=getattr(args, "override_intents", None),
            persist=False,
        )

    if reroute_meeting_id:
        profile_arg = str(getattr(args, "profile", "") or "").strip()
        if not profile_arg:
            print("`--reroute` requires `--profile`.", file=sys.stderr)
            return 2
        return _run_mir_route_command(
            db=db,
            meeting_id=reroute_meeting_id,
            profile_arg=profile_arg,
            threshold_arg=getattr(args, "threshold", None),
            override_arg=getattr(args, "override_intents", None),
            persist=True,
        )

    if args.retry:
        ok = db.requeue_intel_job(
            args.retry,
            reason="Manual retry requested from CLI.",
        )
        if not ok:
            print(f"Meeting not found or transcript is empty: {args.retry}", file=sys.stderr)
            return 1
        print(f"Requeued deferred intelligence for meeting {args.retry}.")
        return 0

    if args.retry_failed:
        failed_jobs = db.list_intel_jobs(status="failed", limit=args.limit)
        if not failed_jobs:
            print("No failed deferred-intel jobs found.")
            return 0

        requeued = 0
        for job in failed_jobs:
            if db.requeue_intel_job(job.meeting_id, reason="Manual retry requested from CLI."):
                requeued += 1

        print(f"Requeued {requeued} failed deferred-intel job(s).")
        return 0

    config = Config.load()
    meeting_cfg = config.meeting
    model_path = meeting_cfg.intel_realtime_model
    provider = meeting_cfg.intel_provider
    cloud_model = meeting_cfg.intel_cloud_model
    cloud_api_key_env = meeting_cfg.intel_cloud_api_key_env
    cloud_base_url = meeting_cfg.intel_cloud_base_url
    cloud_reasoning_effort = meeting_cfg.intel_cloud_reasoning_effort
    cloud_store = meeting_cfg.intel_cloud_store
    retry_base_seconds = meeting_cfg.intel_retry_base_seconds
    retry_max_seconds = meeting_cfg.intel_retry_max_seconds
    retry_max_attempts = meeting_cfg.intel_retry_max_attempts

    if args.process:
        retry_mode = str(getattr(args, "retry_mode", "respect-backoff")).strip().lower()
        include_scheduled = retry_mode == "retry-now"
        runtime_ok, runtime_reason = get_intel_runtime_status(
            model_path,
            provider=provider,
            cloud_model=cloud_model,
            cloud_api_key_env=cloud_api_key_env,
            cloud_base_url=cloud_base_url,
        )
        if not runtime_ok:
            print(f"Deferred-intel runtime unavailable: {runtime_reason}", file=sys.stderr)
            return 1

        processed = drain_intel_queue(
            model_path,
            provider=provider,
            cloud_model=cloud_model,
            cloud_api_key_env=cloud_api_key_env,
            cloud_base_url=cloud_base_url,
            cloud_reasoning_effort=cloud_reasoning_effort,
            cloud_store=cloud_store,
            retry_base_seconds=retry_base_seconds,
            retry_max_seconds=retry_max_seconds,
            retry_max_attempts=retry_max_attempts,
            include_scheduled=include_scheduled,
            max_jobs=args.max_jobs,
        )
        if processed == 0:
            print("No queued deferred-intel jobs found.")
            return 0

        print(f"Processed {processed} deferred-intel job(s).")
        return 0

    jobs = db.list_intel_jobs(status=args.status, limit=args.limit)
    _print_runtime_status(
        model_path,
        provider=provider,
        cloud_model=cloud_model,
        cloud_api_key_env=cloud_api_key_env,
        cloud_base_url=cloud_base_url,
    )
    _print_jobs(jobs, status=args.status)
    return 0


def _run_mir_route_command(
    *,
    db: Any,
    meeting_id: str,
    profile_arg: Optional[str],
    threshold_arg: Optional[float],
    override_arg: Optional[str],
    persist: bool,
) -> int:
    config = Config.load()
    default_profile = str(getattr(config.meeting, "mir_profile", "balanced") or "balanced")
    profile, profile_error = _resolve_profile(profile_arg, default_profile=default_profile)
    if profile_error is not None:
        print(profile_error, file=sys.stderr)
        return 2

    threshold_value = DEFAULT_INTENT_THRESHOLD
    if threshold_arg is not None:
        try:
            threshold_value = float(threshold_arg)
        except Exception:
            print(f"Invalid threshold: {threshold_arg!r}", file=sys.stderr)
            return 2
        if threshold_value < 0.0 or threshold_value > 1.0:
            print("`--threshold` must be between 0.0 and 1.0.", file=sys.stderr)
            return 2

    override_intents, override_error = _parse_override_intents(override_arg)
    if override_error is not None:
        print(override_error, file=sys.stderr)
        return 2

    meeting = db.get_meeting(meeting_id)
    if meeting is None:
        print(f"Meeting not found: {meeting_id}", file=sys.stderr)
        return 1

    transcript = _build_meeting_transcript(meeting)
    if not transcript.strip():
        print(f"Meeting transcript is empty: {meeting_id}", file=sys.stderr)
        return 1

    tags = _normalize_tags(getattr(meeting, "tags", []))
    route = preview_route_from_transcript(
        profile=profile,
        transcript=transcript,
        tags=tags,
        threshold=threshold_value,
        override_intents=override_intents or None,
    )
    route_payload = route.to_dict()

    result_payload: dict[str, Any] = {
        "success": True,
        "mode": "reroute" if persist else "dry_run",
        "meeting_id": str(getattr(meeting, "id", meeting_id) or meeting_id),
        "meeting_title": str(getattr(meeting, "title", "") or ""),
        "meeting_tags": tags,
        "segment_count": len(getattr(meeting, "segments", []) or []),
        "transcript_chars": len(transcript),
        "route": route_payload,
    }

    if persist:
        window_id = _persist_cli_reroute(
            db=db,
            meeting=meeting,
            route_payload=route_payload,
            transcript=transcript,
            tags=tags,
        )
        result_payload["persisted_window_id"] = window_id

    print(json.dumps(result_payload, indent=2, sort_keys=True))
    return 0


def _resolve_profile(profile_arg: Optional[str], *, default_profile: str) -> tuple[str, Optional[str]]:
    available = set(available_profiles())
    candidate = str(profile_arg or "").strip().lower()
    if not candidate:
        normalized_default = str(default_profile or "").strip().lower()
        if normalized_default in available:
            return normalized_default, None
        return "balanced", None
    if candidate in available:
        return candidate, None
    return "balanced", (
        f"Invalid profile: {candidate!r}. "
        f"Valid profiles: {', '.join(sorted(available))}."
    )


def _parse_override_intents(raw_value: Optional[str]) -> tuple[list[str], Optional[str]]:
    raw = str(raw_value or "").strip()
    if not raw:
        return [], None

    requested = [item.strip().lower() for item in raw.split(",") if item.strip()]
    normalized = normalize_override_intents(requested)
    if requested and not normalized:
        return [], (
            "No valid override intents provided. "
            f"Supported intents: {', '.join(SUPPORTED_INTENTS)}."
        )

    invalid = [intent for intent in requested if intent not in set(SUPPORTED_INTENTS)]
    if invalid:
        return [], (
            f"Invalid override intents: {', '.join(sorted(set(invalid)))}. "
            f"Supported intents: {', '.join(SUPPORTED_INTENTS)}."
        )

    return normalized, None


def _normalize_tags(raw_tags: object) -> list[str]:
    if not isinstance(raw_tags, list):
        return []
    tags: list[str] = []
    for raw in raw_tags:
        tag = str(raw).strip().lower()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def _build_meeting_transcript(meeting: Any) -> str:
    segments = getattr(meeting, "segments", []) or []
    lines: list[str] = []
    for segment in segments:
        text = str(getattr(segment, "text", "") or "").strip()
        if not text:
            continue
        speaker = str(getattr(segment, "speaker", "") or "").strip()
        if speaker:
            lines.append(f"{speaker}: {text}")
        else:
            lines.append(text)
    return "\n".join(lines)


def _persist_cli_reroute(
    *,
    db: Any,
    meeting: Any,
    route_payload: dict[str, Any],
    transcript: str,
    tags: list[str],
) -> str:
    meeting_id = str(getattr(meeting, "id", "") or "").strip()
    window_id = f"{meeting_id}:cli-reroute"
    transcript_hash = _meeting_transcript_hash(meeting, transcript=transcript)
    now_iso = datetime.now().isoformat()

    db.record_intent_window(
        meeting_id=meeting_id,
        window_id=window_id,
        start_seconds=0.0,
        end_seconds=_meeting_duration_seconds(meeting),
        transcript_hash=transcript_hash,
        transcript_excerpt=transcript[:400],
        profile=str(route_payload.get("profile") or "balanced"),
        threshold=float(route_payload.get("threshold") or DEFAULT_INTENT_THRESHOLD),
        active_intents=[
            str(intent).strip().lower()
            for intent in (route_payload.get("active_intents") or [])
            if str(intent).strip()
        ],
        intent_scores={
            str(intent).strip().lower(): float(score)
            for intent, score in dict(route_payload.get("intent_scores") or {}).items()
            if str(intent).strip()
        },
        override_intents=[
            str(intent).strip().lower()
            for intent in (route_payload.get("override_intents") or [])
            if str(intent).strip()
        ],
        tags=tags,
        metadata={
            "source": "cli_reroute",
            "manual_profile_override": True,
            "updated_at": now_iso,
        },
    )
    return window_id


def _meeting_duration_seconds(meeting: Any) -> float:
    duration = getattr(meeting, "duration", None)
    if duration is not None:
        try:
            return max(0.0, float(duration))
        except Exception:
            pass

    segments = getattr(meeting, "segments", []) or []
    if segments:
        try:
            return max(0.0, float(max(getattr(seg, "end_time", 0.0) for seg in segments)))
        except Exception:
            return 0.0
    return 0.0


def _meeting_transcript_hash(meeting: Any, *, transcript: str) -> str:
    transcript_hash_attr = getattr(meeting, "transcript_hash", None)
    if callable(transcript_hash_attr):
        try:
            value = str(transcript_hash_attr() or "").strip()
        except Exception:
            value = ""
        if value:
            return value
    payload = transcript.strip() or str(getattr(meeting, "id", "") or "")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _print_runtime_status(
    model_path: Optional[str],
    *,
    provider: str,
    cloud_model: str,
    cloud_api_key_env: str,
    cloud_base_url: Optional[str],
) -> None:
    runtime_ok, runtime_reason = get_intel_runtime_status(
        model_path or "",
        provider=provider,
        cloud_model=cloud_model,
        cloud_api_key_env=cloud_api_key_env,
        cloud_base_url=cloud_base_url,
    )
    print(f"Provider mode: {provider}")
    if runtime_ok:
        print("Runtime: ready")
    else:
        print(f"Runtime: unavailable ({runtime_reason})")


def _print_jobs(jobs: list[IntelJob], *, status: str) -> None:
    label = status if status != "all" else "deferred"
    if not jobs:
        print(f"No {label} intel jobs found.")
        return

    print(f"{len(jobs)} {label} intel job(s):")
    now = datetime.now()
    for job in jobs:
        title = job.meeting_title or "(untitled)"
        if len(title) > 42:
            title = title[:39] + "..."

        started = job.started_at.strftime("%Y-%m-%d") if job.started_at else "unknown-date"
        print(
            f"- {job.meeting_id} [{job.status}] attempts={job.attempts} "
            f"requested={job.requested_at.strftime('%Y-%m-%d %H:%M')} {started} {title}"
        )

        detail = job.last_error or job.intel_status_detail
        if detail:
            print(f"  {detail}")
        if job.status == "queued" and job.last_error and job.requested_at > now:
            print(f"  Next retry: {job.requested_at.strftime('%Y-%m-%d %H:%M:%S')}")
