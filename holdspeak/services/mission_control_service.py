"""Principal-aware mission-control operations.

The service owns durable rails-journal reads and Delivery Workbench proposal
lifecycle work. HTTP adapters supply only composition-time collaborators such
as the project-map path, subprocess runner, and broadcast callback.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from ..db.core import Database
from ..principals import Principal
from .errors import NotFound, ValidationError

MC_PLUGIN_ID = "missioncontrol_desk"
MC_PLUGIN_VERSION = "0.1.0"


class MissionControlService:
    def __init__(self, db: Database) -> None:
        self._db = db

    def list_rails_journal(self, principal: Principal, *, limit: int = 50) -> list[Any]:
        from ..rails_observer import list_journal

        return list_journal(self._db, limit=limit)

    def propose_story(
        self,
        principal: Principal,
        payload: Any,
        *,
        project_map: dict[str, Any],
        runner: Any = None,
    ) -> Any:
        from ..missioncontrol_bridge import (
            ALLOWED_STORY_STATUSES,
            build_story_preview,
            state_entry,
        )

        repo_name = str(getattr(payload, "repo", "") or "")
        repo_path = project_map["projects"].get(repo_name)
        if not repo_path:
            raise ValidationError(f"repo {repo_name!r} is not in the project map")
        entry = state_entry(repo_name, repo_path, runner, principal=principal)
        if entry.get("status") != "live":
            raise ValidationError(f"rails unreadable: {entry.get('detail')}")
        project_name = str(getattr(payload, "project", "") or "")
        projects = {p.get("slug"): p for p in entry["feed"].get("projects") or []}
        project = projects.get(project_name)
        if project is None:
            raise ValidationError(f"project {project_name!r} is not on the roadmap")

        verb = str(getattr(payload, "verb", "") or "").strip()
        if verb == "status":
            story_id = getattr(payload, "story", None)
            story = next(
                (s for s in project.get("stories") or [] if s.get("story_id") == story_id),
                None,
            )
            if story is None:
                raise ValidationError(
                    f"story {story_id!r} is not on the {project_name} roadmap"
                )
            status = str(getattr(payload, "status", "") or "").strip().lower()
            if status not in ALLOWED_STORY_STATUSES:
                raise ValidationError(
                    f"status {status!r} is not one of {', '.join(ALLOWED_STORY_STATUSES)}"
                )
            proposal_payload = {
                "repo": repo_path,
                "verb": "status",
                "project": project_name,
                "phase": str(story.get("phase")),
                "story": story_id,
                "status": status,
            }
            preview = build_story_preview(
                proposal_payload, story.get("title") or "", story.get("status") or ""
            )
            action = "dw_story_status"
        elif verb == "create":
            phases = {str(p.get("number")) for p in project.get("phases") or []}
            phase = str(getattr(payload, "phase", "") or "").strip()
            title = str(getattr(payload, "title", "") or "").strip()
            if phase not in phases:
                raise ValidationError(
                    f"phase {phase!r} is not on the {project_name} roadmap"
                )
            if not title:
                raise ValidationError("a story create needs a title")
            proposal_payload = {
                "repo": repo_path,
                "verb": "create",
                "project": project_name,
                "phase": phase,
                "title": title,
            }
            preview = build_story_preview(proposal_payload)
            action = "dw_story_create"
        else:
            raise ValidationError(
                f"verb {verb!r} is not an allow-listed story verb"
            )

        payload_key = hashlib.sha256(
            json.dumps(proposal_payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
        return self._db.actuators.record_proposal(
            meeting_id=None,
            origin="desk",
            window_id="desk:missioncontrol",
            plugin_id=MC_PLUGIN_ID,
            plugin_version=MC_PLUGIN_VERSION,
            idempotency_key=f"mc-story:{payload_key}",
            target="delivery-workbench",
            action=action,
            preview=preview,
            payload=proposal_payload,
            reversible=True,
            required_capabilities=["actuator"],
        )

    def decide_proposal(
        self,
        principal: Principal,
        proposal_id: str,
        *,
        decision: str,
        actor: str,
        map_path: Path | None = None,
        runner: Any = None,
        broadcast: Callable[[str, Any], None] | None = None,
    ) -> Any:
        clean = str(decision or "").strip().lower()
        if clean not in ("approved", "rejected"):
            raise ValidationError(f"Invalid decision: {decision!r}")
        existing = self._db.actuators.get_proposal(proposal_id)
        if (
            existing is None
            or getattr(existing, "origin", "") != "desk"
            or existing.target != "delivery-workbench"
        ):
            raise NotFound("proposal", proposal_id)
        try:
            policy_snapshot = None
            if clean == "approved":
                from ..operation_policy import operation_for_proposal, resolve_policy

                operation = operation_for_proposal(existing, actor=actor)
                captured = dict(getattr(existing, "policy_snapshot", {}) or {})
                if captured.get("outcome") == "refused":
                    raise ValueError(
                        "captured operation policy refuses this unregistered effect"
                    )
                policy_decision = resolve_policy(
                    operation,
                    mode=str(captured.get("mode") or "neutral"),
                    source=str(captured.get("source") or "config"),
                    explicit_authorization=True,
                )
                if policy_decision.outcome != "allowed":
                    raise ValueError(
                        "captured operation policy does not authorize this effect"
                    )
                policy_snapshot = policy_decision.to_dict()
            updated = self._db.actuators.transition_proposal(
                proposal_id,
                to_status=clean,
                actor=actor,
                policy_snapshot=policy_snapshot,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        if clean == "rejected":
            self._broadcast_result(updated, broadcast)
            return updated
        return self._execute_dw_proposal(
            principal,
            updated,
            actor=actor,
            map_path=map_path,
            runner=runner,
            broadcast=broadcast,
        )

    def _execute_dw_proposal(
        self,
        principal: Principal,
        proposal: Any,
        *,
        actor: str,
        map_path: Path | None,
        runner: Any,
        broadcast: Callable[[str, Any], None] | None,
    ) -> Any:
        from ..missioncontrol_bridge import build_dw_story_connector, load_project_map
        from ..plugins.actuator_executor import ActuatorExecutor

        payload = dict(proposal.payload or {})
        repo_path = str(payload.get("repo") or "")
        allowed = set(load_project_map(map_path)["projects"].values())
        if repo_path not in allowed:
            updated = self._db.actuators.transition_proposal(
                proposal.id,
                to_status="failed",
                actor=actor,
                detail="mission control: repo not in the project map at execution time",
                error=f"repo {repo_path!r} is not in the operator's project map",
            )
            self._broadcast_result(updated, broadcast)
            return updated
        executor = ActuatorExecutor(
            self._db,
            connector=build_dw_story_connector(Path(repo_path), runner=runner),
            allow_actuators=True,
            actor=actor,
            on_result=lambda event: broadcast and broadcast("actuator_result", event),
        )
        return executor.execute(proposal.id)

    @staticmethod
    def _broadcast_result(
        proposal: Any, broadcast: Callable[[str, Any], None] | None
    ) -> None:
        if broadcast is None:
            return
        broadcast(
            "actuator_result",
            {
                "id": proposal.id,
                "meeting_id": proposal.meeting_id,
                "status": proposal.status,
                "target": proposal.target,
                "action": proposal.action,
                "preview": proposal.preview,
                "reversible": bool(proposal.reversible),
                "policy": getattr(proposal, "policy_snapshot", {}),
                "error": proposal.error,
            },
        )
