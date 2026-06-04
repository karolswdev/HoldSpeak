"""GitHub issue write connector + actuator (Phase 38, HS-38-02).

The first **real** write connector on the HS-38-01 framework: turn an approved
proposal into an actual GitHub issue via ``gh issue create``. The existing
`connector_packs.github_cli` pack is **read-only** (`gh pr/issue view`); this adds
a *write* path that is narrowly gated so it can do exactly one thing and nothing
else.

Two halves, the same safety split as Phase-37's `followup_ticket_actuator`:

  - `GithubIssueActuator` (the plugin) — `run(context)` reads the meeting's action
    items and, for the first one **without an owner**, returns an `ActuatorProposal`
    whose payload carries the `repo` / `title` / `body` of the issue it *would*
    file. It never reaches out — building a proposal is all an actuator's `run()`
    ever does.

  - `build_github_issue_connector(...)` (the connector) — built with
    `build_gated_connector` (HS-38-01): permission `shell:exec` via
    `PermissionGate.run_subprocess`, manifest allow-listed to **`gh issue create`
    only**. The argv is built from the *stored* payload (`--repo`/`--title`/
    `--body`); a non-zero `gh` exit raises so the executor records `failed` + audit.
    The created issue URL is returned as the result.

Decision (this story): the GitHub connector is a **host-side gated connector** the
executor injects — mirroring Phase-37's `build_outbox_connector` — not a discovered
connector pack. Auth is the operator's already-authenticated local `gh`; this
connector manages no tokens.

Both the actuator and the connector are **opt-in**: the actuator is registered via
`register_github_issue_actuator` (NOT in `register_builtin_plugins`) and is
capability-blocked behind `actuator` until an operator enables it, and the
connector is only ever reached after approval + the policy/parity gates +
`shell:exec`. The default plugin set + routing are unchanged.

Because the argv is an explicit list (`["gh", "issue", "create", "--repo", repo,
…]`) run without a shell, a payload value can only ever be an *argument* to
`gh issue create` — it can never change the subcommand or inject a second command.
The manifest allow-check refuses anything whose argv is not `gh issue create …`
**before** any egress.
"""
from __future__ import annotations

import re
from typing import Any, Optional
from urllib.parse import urlparse

from ...logging_config import get_logger
from ..actuator_executor import Connector
from ..gated_connector import (
    GatedOperation,
    WriteConnectorManifest,
    build_gated_connector,
)

log = get_logger("plugins.github_issue_actuator")

# Owner strings that actually mean "no owner" (mirrors followup_ticket_actuator).
_UNASSIGNED = {"", "null", "none", "n/a", "na", "unassigned", "unknown", "tbd", "?"}

# Per-command wall-clock timeout for the `gh` subprocess.
DEFAULT_TIMEOUT_SECONDS: float = 30.0

# The narrow write manifest: `gh issue create` and nothing else.
GITHUB_ISSUE_MANIFEST = WriteConnectorManifest(
    connector_id="github_issue_writer",
    permission="shell:exec",
    label="GitHub issue writer",
    description="Runs `gh issue create` only; repo/title/body from the approved proposal.",
    allowed_argv_prefixes=(("gh", "issue", "create"),),
)


def _is_unowned(owner: Any) -> bool:
    return str(owner or "").strip().lower() in _UNASSIGNED


class GithubIssueActuator:
    """Proposes a GitHub issue for the first unowned action item."""

    id: str = "github_issue_actuator"
    version: str = "0.1.0"
    kind: str = "actuator"
    execution_mode: str = "inline"
    required_capabilities: list[str] = ["actuator"]

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        items = context.get("action_items") or []
        if not isinstance(items, list):
            items = []
        unowned = next(
            (it for it in items if isinstance(it, dict) and _is_unowned(it.get("owner"))),
            None,
        )
        if unowned is None:
            # Nothing to propose — raise so the host records a plain `error`
            # (no proposal, no side effect), never a half-formed proposal.
            raise ValueError("no unowned action item to file a GitHub issue for")

        repo = str(context.get("github_repo") or "").strip()
        if not repo:
            # An issue needs a target repo; without one we cannot build a faithful
            # proposal, so this is an `error`, not a half-formed proposal.
            raise ValueError("no github_repo in context to file the issue against")

        task = str(unowned.get("task") or "").strip() or "Unspecified action item"
        meeting_title = str(
            context.get("meeting_title") or context.get("title") or "meeting"
        ).strip()
        due = str(unowned.get("due") or "").strip()

        title = f"Follow up: {task}"
        body = "\n".join(
            [
                f"Raised in **{meeting_title}** with no owner assigned.",
                "",
                f"- **Task:** {task}",
                "- **Owner:** _unassigned_",
                f"- **Due:** {due or '_not stated_'}",
            ]
        )

        return {
            "target": "github",
            "action": "create_issue",
            "preview": f"Open a GitHub issue in {repo}: “{title}”",
            "payload": {"repo": repo, "title": title, "body": body},
            "reversible": False,  # a filed issue can be closed but not trivially undone
            "required_capabilities": ["actuator"],
        }


def _plan(proposal: Any, *, timeout_seconds: float) -> GatedOperation:
    """Build the `gh issue create` argv from the proposal's stored payload.

    The subcommand is hard-coded; only the *values* of `--repo`/`--title`/`--body`
    come from the payload, so a payload can never change the operation — the
    manifest allow-check confirms the argv is `gh issue create …` before egress.
    """
    payload = getattr(proposal, "payload", None) or {}
    repo = str(payload.get("repo") or "").strip()
    title = str(payload.get("title") or "").strip()
    body = str(payload.get("body") or "")
    argv = [
        "gh",
        "issue",
        "create",
        "--repo",
        repo,
        "--title",
        title,
        "--body",
        body,
    ]
    return GatedOperation.subprocess(
        argv, capture_output=True, text=True, timeout=timeout_seconds
    )


def _issue_number(url: str) -> Optional[int]:
    """Parse the trailing issue number out of a `gh`-printed issue URL."""
    match = re.search(r"/issues/(\d+)\b", urlparse(url).path or url)
    return int(match.group(1)) if match else None


def _interpret(completed: Any, op: GatedOperation) -> dict[str, Any]:
    """Map the `gh` result into the executor's result dict (or raise → `failed`)."""
    returncode = getattr(completed, "returncode", None)
    stdout = (getattr(completed, "stdout", "") or "").strip()
    stderr = (getattr(completed, "stderr", "") or "").strip()
    if returncode != 0:
        raise RuntimeError(
            f"gh issue create failed (exit {returncode}): {stderr or stdout or 'no output'}"
        )
    # `gh issue create` prints the URL of the new issue to stdout (last line).
    url = stdout.splitlines()[-1].strip() if stdout else ""
    log.info("actuator created GitHub issue: %s", url or "(no url in output)")
    return {"url": url, "issue": _issue_number(url)}


def build_github_issue_connector(
    *,
    runner: Optional[Any] = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> Connector:
    """A connector that files a proposal's GitHub issue via `gh issue create`.

    Returns the `connector(proposal) -> result` callable for `ActuatorExecutor`,
    gated by HS-38-01: the manifest admits only `gh issue create`, and the call
    routes through `PermissionGate.run_subprocess` (`shell:exec`). `runner`
    defaults to `subprocess.run` in production; tests inject a fake (no real `gh`).
    """
    return build_gated_connector(
        GITHUB_ISSUE_MANIFEST,
        plan=lambda proposal: _plan(proposal, timeout_seconds=timeout_seconds),
        interpret=_interpret,
        runner=runner,
    )


def register_github_issue_actuator(host: Any) -> str:
    """Register the GitHub issue actuator on a host (behind the actuator gate).

    Explicit + opt-in: NOT part of `register_builtin_plugins`, so the default
    plugin set + routing chains are unchanged. The host capability-blocks it
    unless `actuator` is in `enabled_capabilities`.
    """
    host.register(GithubIssueActuator())
    return GithubIssueActuator.id


__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "GITHUB_ISSUE_MANIFEST",
    "GithubIssueActuator",
    "build_github_issue_connector",
    "register_github_issue_actuator",
]
