"""Narrow GitHub PR comment/status connectors for PR follow-through.

The proposal is the consent record.  These connectors can execute only the
stored, approved payload and only as ``gh pr comment`` or one commit-status
POST.  They never merge, close, push, or approve a review.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from ..actuator_executor import Connector
from ..gated_connector import GatedOperation, WriteConnectorManifest, build_gated_connector

_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SHA = re.compile(r"^[0-9a-f]{7,64}$")

GITHUB_PR_COMMENT_MANIFEST = WriteConnectorManifest(
    connector_id="github_pr_comment_writer",
    permission="shell:exec",
    label="GitHub PR comment",
    description="Runs gh pr comment only.",
    allowed_argv_prefixes=(("gh", "pr", "comment"),),
)
GITHUB_PR_STATUS_MANIFEST = WriteConnectorManifest(
    connector_id="github_pr_status_writer",
    permission="shell:exec",
    label="GitHub commit status",
    description="Runs one gh api commit-status POST only.",
    allowed_argv_prefixes=(("gh", "api", "--method", "POST"),),
)


def _comment_plan(proposal: Any) -> GatedOperation:
    payload = dict(getattr(proposal, "payload", None) or {})
    repo = str(payload.get("repo") or "").strip()
    number = int(payload.get("number") or 0)
    body = str(payload.get("body") or "")
    if not _REPO.fullmatch(repo) or number < 1 or not body.strip():
        raise ValueError("github_pr_comment_payload_invalid")
    return GatedOperation.subprocess(
        ["gh", "pr", "comment", str(number), "--repo", repo, "--body", body],
        capture_output=True,
        text=True,
        timeout=30.0,
    )


def _status_plan(proposal: Any) -> GatedOperation:
    payload = dict(getattr(proposal, "payload", None) or {})
    repo = str(payload.get("repo") or "").strip()
    sha = str(payload.get("sha") or "").strip().lower()
    state = str(payload.get("state") or "").strip().lower()
    context = str(payload.get("context") or "HoldSpeak").strip()[:100]
    description = str(payload.get("description") or "").strip()[:140]
    if (
        not _REPO.fullmatch(repo)
        or not _SHA.fullmatch(sha)
        or state not in {"error", "failure", "pending", "success"}
        or not context
    ):
        raise ValueError("github_pr_status_payload_invalid")
    argv = [
        "gh", "api", "--method", "POST", f"repos/{repo}/statuses/{sha}",
        "-f", f"state={state}", "-f", f"context={context}",
    ]
    if description:
        argv.extend(["-f", f"description={description}"])
    return GatedOperation.subprocess(
        argv, capture_output=True, text=True, timeout=30.0
    )


def _interpret(completed: Any, op: GatedOperation) -> dict[str, Any]:
    if getattr(completed, "returncode", None) != 0:
        detail = str(getattr(completed, "stderr", "") or getattr(completed, "stdout", "") or "no output").strip()
        raise RuntimeError(f"GitHub write failed: {detail[:240]}")
    output = str(getattr(completed, "stdout", "") or "").strip()
    return {"output": output[-500:]}


def build_github_pr_connector(action: str, *, runner: Optional[Any] = None) -> Connector:
    if action == "comment":
        return build_gated_connector(
            GITHUB_PR_COMMENT_MANIFEST,
            plan=_comment_plan,
            interpret=_interpret,
            runner=runner,
        )
    if action == "status":
        return build_gated_connector(
            GITHUB_PR_STATUS_MANIFEST,
            plan=_status_plan,
            interpret=_interpret,
            runner=runner,
        )
    raise ValueError("github_pr_action_invalid")
