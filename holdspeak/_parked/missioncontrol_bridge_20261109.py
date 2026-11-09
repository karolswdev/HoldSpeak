# PARKED 20261109 (lane subtract/mission-control): the Mission control belt's reads
# (sessions, PR receipts, story evidence) and its `dw story` writer. The state feed
# stays live for the iPad belt (apple/App/MeetingCapture/DeskBelt.swift).
# Programs own delivery now. Not imported. Restore with git revert of the parking commit.
"""Parked from ``holdspeak/missioncontrol_bridge.py``."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Optional

from ..connector_runtime import ReadSubprocessDenied
from ..missioncontrol_bridge import (
    DW_TIMEOUT_SECONDS,
    Runner,
    _default_runner,
    _fetch_document,
    _run_read,
    dw_argv_base,
)
from ..principals import Principal

# The schema versions this client is proven against (declared per
# the counterpart's §5; drift is a compatibility note, not a break).
SESSIONS_SCHEMA_PROVEN = 1

def sessions_payload(
    project_map: dict[str, Any],
    runner: Optional[Runner] = None,
    *,
    principal: Principal,
) -> dict[str, Any]:
    """The correlation document is desk-global; one relay via the
    default repo's CLI."""
    default = project_map.get("default")
    if not default:
        return {"status": "unavailable", "detail": "no rails repo configured"}
    doc, status, detail = _fetch_document(
        Path(default), ["sessions", "--json"], runner, principal=principal
    )
    if doc is None:
        return {"status": status, "detail": detail}
    if (
        not isinstance(doc, dict)
        or doc.get("sessions_schema") != SESSIONS_SCHEMA_PROVEN
    ):
        found = doc.get("sessions_schema") if isinstance(doc, dict) else None
        return {
            "status": "compatibility",
            "detail": (
                f"sessions_schema {found!r} is not the schema this desk "
                f"was proven against ({SESSIONS_SCHEMA_PROVEN})"
            ),
        }
    return {"status": "live", "sessions": doc}


def receipts_entry(
    name: str,
    repo_path: str,
    runner: Optional[Runner] = None,
    *,
    principal: Principal,
) -> dict[str, Any]:
    """One repo's GitHub receipts (HS-86-03): open PRs with their
    check rollups, via the gh CLI with cwd inside the repo — the
    belt's PR and CI station lights. gh missing, failing, or
    answering non-JSON is a typed ``unavailable``, never an
    exception; the belt renders absence honestly."""
    entry: dict[str, Any] = {"name": name, "path": repo_path}
    run = runner or _default_runner
    if runner is None:
        gh = shutil.which("gh")
        if gh is None:
            return {**entry, "status": "unavailable", "detail": "gh CLI is not installed"}
    else:
        gh = "gh"
    argv = [
        gh, "pr", "list", "--json",
        "number,title,url,headRefName,statusCheckRollup",
    ]
    try:
        proc = _run_read(run, argv, str(repo_path), principal)
    except ReadSubprocessDenied:
        raise
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {**entry, "status": "unavailable", "detail": f"gh failed to run: {exc}"}
    if proc.returncode != 0:
        lines = (proc.stderr or proc.stdout or "").strip().splitlines()
        tail = lines[-1] if lines else "unknown gh error"
        return {**entry, "status": "unavailable", "detail": f"gh exited {proc.returncode}: {tail[:300]}"}
    try:
        prs = json.loads(proc.stdout)
    except (json.JSONDecodeError, ValueError):
        return {**entry, "status": "unavailable", "detail": "gh did not return JSON"}
    if not isinstance(prs, list):
        return {**entry, "status": "unavailable", "detail": "gh returned an unexpected shape"}
    return {**entry, "status": "live", "prs": prs}


def receipts_payload(
    project_map: dict[str, Any],
    runner: Optional[Runner] = None,
    *,
    principal: Principal,
) -> dict[str, Any]:
    return {
        "repos": [
            receipts_entry(name, repo, runner, principal=principal)
            for name, repo in sorted(project_map["projects"].items())
        ]
    }


def story_evidence_payload(
    project_map: dict[str, Any],
    repo_name: str,
    project_slug: str,
    story_id: str,
    runner: Optional[Runner] = None,
    *,
    principal: Principal,
) -> dict[str, Any]:
    """Evidence content for one story (HS-86-04) — the desk opens the
    filed object in place. The path comes from the repo's own CLI
    (`dw context`), never from re-parsing the roadmap; the read is
    contained to the repo's roadmap tree — `pm/roadmap/**/*.md` or
    Delivery Workbench's self-hosted `pmo-roadmap/pm/roadmap/**/*.md`
    (HS-94-01). Both containment roots are fixed relative to the
    mapped repo, so no CLI document can widen them. Display-only:
    state is never derived from this document."""
    repo_path = project_map["projects"].get(repo_name)
    if not repo_path:
        return {"status": "refused", "detail": f"repo {repo_name!r} is not in the project map"}
    doc, status, detail = _fetch_document(
        Path(repo_path),
        ["context", project_slug, "--compact"],
        runner,
        principal=principal,
    )
    if doc is None:
        return {"status": status, "detail": detail}
    rel = ""
    for project in (doc.get("projects") or []) if isinstance(doc, dict) else []:
        if project.get("slug") != project_slug:
            continue
        for phase in project.get("phases") or []:
            for story in phase.get("stories") or []:
                if story.get("story_id") == story_id:
                    rel = str(story.get("evidence_path") or "")
    if not rel:
        return {"status": "absent", "detail": f"no evidence path for {story_id}"}
    root = Path(repo_path).resolve()
    target = (root / rel).resolve()
    roadmap_roots = (
        str((root / "pm" / "roadmap").resolve()) + os.sep,
        str((root / "pmo-roadmap" / "pm" / "roadmap").resolve()) + os.sep,
    )
    contained = any(str(target).startswith(allowed) for allowed in roadmap_roots)
    if target.suffix != ".md" or not contained:
        return {"status": "refused", "detail": "evidence path escapes the roadmap tree or is not markdown"}
    if not target.is_file():
        return {"status": "absent", "detail": f"{rel} does not exist"}
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {"status": "unavailable", "detail": f"unreadable: {exc}"}
    return {"status": "live", "story_id": story_id, "path": rel, "text": text[:200_000]}


ALLOWED_STORY_STATUSES = ("backlog", "ready", "in-progress", "blocked", "done")


def build_story_preview(payload: dict[str, Any], story_title: str = "", from_status: str = "") -> str:
    """The proposal preview — names the act and the standing truth."""
    if payload.get("verb") == "status":
        return (
            f"Flip {payload['story']}"
            + (f" ({story_title})" if story_title else "")
            + (f" from [{from_status}]" if from_status else "")
            + f" to [{payload['status']}] in {payload['project']} "
            f"at {payload['repo']}. The dw gate still applies — a "
            "done-flip without evidence will be refused."
        )
    return (
        f"Create a new story {payload.get('title')!r} in "
        f"{payload['project']} phase {payload['phase']} at {payload['repo']}."
    )


def build_dw_story_connector(repo: Path, *, runner: Optional[Runner] = None):
    """The write half (HS-82-05): a gated connector admitting exactly
    the two ``dw story`` argv shapes — the Phase-12 pack's manifest,
    now native. argv is built here from the STORED payload at egress
    time, never from anything the UI sent at approval time; a payload
    naming a different repo refuses before planning completes; a dw
    refusal (the gate's banner) rides back verbatim as the error."""
    from ..plugins.gated_connector import (
        GatedOperation,
        WriteConnectorManifest,
        build_gated_connector,
    )

    base = dw_argv_base(repo)
    if base is None:
        raise ValueError(f"no dw CLI for {repo}")
    manifest = WriteConnectorManifest(
        connector_id="dw_story_writer",
        permission="shell:exec",
        label="Delivery Workbench story writer",
        description="Runs the two allow-listed dw story verbs.",
        allowed_argv_prefixes=(
            (*base, "story", "status"),
            (*base, "story", "create"),
        ),
    )

    def plan(proposal) -> GatedOperation:
        payload = dict(proposal.payload or {})
        if str(payload.get("repo") or "") != str(repo):
            raise ValueError(
                f"proposal targets repo {payload.get('repo')!r}, connector "
                f"is bound to {repo}"
            )
        verb = str(payload.get("verb") or "")
        if verb == "status":
            argv = [
                *base, "story", "status",
                str(payload["project"]), str(payload["phase"]),
                str(payload["story"]), str(payload["status"]),
            ]
        elif verb == "create":
            argv = [
                *base, "story", "create",
                str(payload["project"]), str(payload["phase"]),
                str(payload["title"]),
            ]
        else:
            # An unknown verb plans an argv the manifest cannot admit,
            # so refusal happens at the gate rather than silently here.
            argv = [*base, "story", verb]
        return GatedOperation.subprocess(
            argv,
            capture_output=True,
            text=True,
            timeout=DW_TIMEOUT_SECONDS,
            cwd=str(repo),
        )

    def interpret(raw, op) -> dict[str, Any]:
        returncode = getattr(raw, "returncode", None)
        stdout = (getattr(raw, "stdout", "") or "").strip()
        stderr = (getattr(raw, "stderr", "") or "").strip()
        if returncode != 0:
            # The dw refusal banner rides stdout/stderr; keep it
            # verbatim so the belt shows exactly what the rails said.
            raise RuntimeError(
                f"dw exited {returncode}: {stdout}\n{stderr}".strip()
            )
        return {"argv": list(op.argv), "stdout": stdout}

    return build_gated_connector(
        manifest,
        plan=plan,
        interpret=interpret,
        gate=manifest.build_gate(),
        runner=runner,
    )


