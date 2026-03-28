"""Deferred meeting-intelligence queue command."""

from __future__ import annotations

import sys
from typing import Optional

from ..config import Config
from ..db import IntelJob, get_database
from ..intel import get_intel_runtime_status
from ..intel_queue import drain_intel_queue


def run_intel_command(args) -> int:
    """Handle the `intel` subcommand."""
    db = get_database()

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

    if args.process:
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
