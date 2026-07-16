"""Work attempt correlation service (HS-94-04).

The hub-side orchestration over the durable
:class:`~holdspeak.db.delivery_attempts.WorkAttemptRepository`:

- **manual** — a person attaches work through the hub API; provenance
  is ``manual`` and can never masquerade as a rider or launch claim;
- **rider_claim** — sessions whose hooks emitted an explicit Story
  claim (``story_claim`` in the agent-session registry) resolve to
  exact attempts. The hub resolves the rider's repo root against the
  Delivery Source registry before marking anything exact — a claim
  the registry cannot place stays out rather than guessed in;
- **heuristic** — the legacy repo-wide ``dw sessions`` correlation
  ingests as clearly-labeled, non-exact rows (capped), and is skipped
  entirely for any session that already holds an exact attempt, so an
  exact binding is never downgraded or shadowed.

Resilience is state, not deletion: worktree removal abandons the
worktree's live attempts, a node going offline moves its attempts to
``unknown``, and stale attempts time out to ``abandoned`` — each with
its transition recorded in the attempt's replayable history.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from ..db.delivery_attempts import (
    ATTEMPTS_SCHEMA,
    AttemptConflict,
    AttemptError,
    AttemptTransitionError,
    WorkAttempt,
    WorkAttemptRepository,
)

#: Ceiling on heuristic rows created per ingest — the old guessing
#: stays available but bounded, never a flood of ambiguous cards.
DEFAULT_HEURISTIC_CAP = 25

#: A live attempt with no session/rider motion for this long is no
#: longer honestly "working"; it abandons with history preserved.
DEFAULT_STALE_ATTEMPT_SECONDS = 24 * 60 * 60

#: agent-session lifecycle -> attempt state. Identical vocabularies
#: by design (HSM-17-02 lifecycle feeds §4.2 states directly).
_ATTEMPT_STATE_BY_LIFECYCLE = {
    "working": "working",
    "waiting": "waiting",
    "idle": "idle",
    "ended": "ended",
}

WorktreeResolver = Callable[[Optional[str]], Optional[dict[str, Any]]]


def resolver_from_registry(registry: Any) -> WorktreeResolver:
    """Resolve a rider-reported repo root to registry identity.

    Builds ``resolved path -> {source_id, worktree_id, node_id}`` from
    a :class:`~holdspeak.delivery.registry.DeliveryRegistry`. Paths are
    resolution INPUT only — the returned identities are the opaque IDs
    that may cross to clients; the path never does.
    """
    mapping: dict[str, dict[str, Any]] = {}
    for source in registry.sources():
        for worktree in source.worktrees:
            try:
                resolved = str(Path(worktree.path).expanduser().resolve())
            except OSError:
                resolved = str(Path(worktree.path).expanduser().absolute())
            mapping[resolved] = {
                "source_id": source.source_id,
                "worktree_id": worktree.worktree_id,
                "node_id": source.node_id,
            }

    def resolve(path_text: Optional[str]) -> Optional[dict[str, Any]]:
        text = str(path_text or "").strip()
        if not text:
            return None
        candidate = Path(text).expanduser()
        try:
            resolved = str(candidate.resolve())
        except OSError:
            resolved = str(candidate.absolute())
        return mapping.get(resolved)

    return resolve


class WorkAttemptService:
    """Creation paths, projection, and resilience for Work attempts."""

    def __init__(
        self,
        repository: WorkAttemptRepository,
        *,
        resolver: Optional[WorktreeResolver] = None,
    ) -> None:
        self._repo = repository
        self._resolve = resolver or (lambda _path: None)

    # ── manual attach (POST /api/delivery/attempts) ──────────────

    def manual_attach(
        self,
        *,
        source_id: str,
        worktree_id: str,
        project: str,
        story_id: str,
        session_id: Optional[str] = None,
        node_id: Optional[str] = None,
        target_id: Optional[str] = None,
        actor: str = "desk-owner",
        now: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """A person attaches work explicitly. Provenance is always
        ``manual`` — the route cannot mint launch/rider/contract
        provenance on a client's word. Binding a session that already
        holds a live exact attempt refuses (`AttemptConflict`) instead
        of silently double-pinning."""
        attempt = self._repo.create(
            source_id=source_id,
            worktree_id=worktree_id,
            project=project,
            story_id=story_id,
            session_id=session_id,
            node_id=node_id,
            target_id=target_id,
            kind="manual",
            exact=True,
            claimed_by=str(actor or "desk-owner"),
            state="starting",
            now=now,
        )
        return self._wire(attempt)

    # ── rider claims (exact) ─────────────────────────────────────

    def sync_rider_claims(
        self,
        claims: Optional[list[Mapping[str, Any]]] = None,
        *,
        state_path: Optional[Path] = None,
        now: Optional[datetime] = None,
    ) -> dict[str, int]:
        """Resolve emitted rider claims into durable exact attempts.

        Idempotent per (session, story, worktree): a heartbeat updates
        the live attempt's state; a claim for a NEW Story ends the old
        attempt and creates a fresh one (fresh ``attempt_id`` — never
        reused across sequential Stories). A claim whose repo root the
        source registry cannot place is skipped, not guessed.
        """
        if claims is None:
            from ..agent_context.sessions import list_agent_story_claims

            claims = list_agent_story_claims(state_path=state_path, now=now)
        summary = {"created": 0, "updated": 0, "ended": 0, "skipped": 0}
        for row in claims:
            claim = row.get("story_claim")
            if not isinstance(claim, Mapping):
                summary["skipped"] += 1
                continue
            project = str(claim.get("project") or "").strip()
            story_id = str(claim.get("story_id") or "").strip()
            session_key = str(row.get("session_key") or "").strip()
            if not project or not story_id or not session_key:
                summary["skipped"] += 1
                continue
            identity = self._resolve(row.get("repo_root")) or self._resolve(
                row.get("cwd")
            )
            if identity is None:
                summary["skipped"] += 1
                continue
            state = _ATTEMPT_STATE_BY_LIFECYCLE.get(
                str(row.get("lifecycle") or ""), "working"
            )
            current = next(
                iter(self._repo.find_active(session_id=session_key, exact=True)),
                None,
            )
            same_binding = current is not None and (
                current.project,
                current.story_id,
                current.source_id,
                current.worktree_id,
            ) == (
                project,
                story_id,
                identity["source_id"],
                identity["worktree_id"],
            )
            if same_binding:
                assert current is not None
                if state == current.state:
                    continue
                reason = (
                    "session_ended" if state == "ended" else "rider_heartbeat"
                )
                self._repo.transition(
                    current.attempt_id, state, reason=reason, now=now
                )
                summary["ended" if state == "ended" else "updated"] += 1
                continue
            if current is not None:
                self._repo.transition(
                    current.attempt_id,
                    "ended",
                    reason="superseded_by_new_claim",
                    now=now,
                )
                summary["ended"] += 1
            if state == "ended":
                # The session tombstoned before the hub ever bound it;
                # recording a born-dead exact attempt helps nobody.
                summary["skipped"] += 1
                continue
            self._repo.create(
                source_id=identity["source_id"],
                worktree_id=identity["worktree_id"],
                node_id=identity.get("node_id"),
                project=project,
                story_id=story_id,
                session_id=session_key,
                target_id=row.get("tmux_pane"),
                kind="rider_claim",
                exact=True,
                claimed_by=str(claim.get("claimed_by") or f"rider:{row.get('agent')}"),
                claimed_at=claim.get("claimed_at"),
                state=state,
                now=now,
            )
            summary["created"] += 1
        return summary

    # ── the legacy heuristic (labeled, never exact) ──────────────

    def ingest_heuristic(
        self,
        sessions_doc: Mapping[str, Any],
        *,
        cap: int = DEFAULT_HEURISTIC_CAP,
        now: Optional[datetime] = None,
    ) -> dict[str, int]:
        """Port of the repo-wide ``dw sessions --json`` guess.

        Every row lands as ``association.kind='heuristic'`` with
        ``exact=false`` — including the single-in-progress-story case
        the old join called exact. A session that already holds an
        exact attempt is skipped entirely: the heuristic can never
        downgrade or shadow an exact binding, and one session showing
        on several Story cards is visibly ambiguous data, not truth.
        """
        summary = {"created": 0, "skipped": 0}
        rows = sessions_doc.get("sessions") if isinstance(sessions_doc, Mapping) else None
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, Mapping):
                continue
            if row.get("correlation") not in {"on_story", "ambiguous"}:
                continue
            session_key = str(row.get("key") or "").strip()
            identity = self._resolve(row.get("repo_root"))
            if not session_key or identity is None:
                summary["skipped"] += 1
                continue
            if self._repo.find_active(session_id=session_key, exact=True):
                summary["skipped"] += 1
                continue
            if row.get("stale"):
                state = "idle"
            elif row.get("awaiting_response"):
                state = "waiting"
            else:
                state = "working"
            for story in row.get("stories") or []:
                if summary["created"] >= max(0, int(cap)):
                    return summary
                if not isinstance(story, Mapping):
                    continue
                project = str(story.get("project") or "").strip()
                story_id = str(story.get("story_id") or "").strip()
                if not project or not story_id:
                    continue
                existing = self._repo.find_active(
                    session_id=session_key,
                    source_id=identity["source_id"],
                    worktree_id=identity["worktree_id"],
                    project=project,
                    story_id=story_id,
                )
                if existing:
                    if existing[0].state != state:
                        self._repo.transition(
                            existing[0].attempt_id,
                            state,
                            reason="heuristic_refresh",
                            now=now,
                        )
                    continue
                self._repo.create(
                    source_id=identity["source_id"],
                    worktree_id=identity["worktree_id"],
                    node_id=identity.get("node_id"),
                    project=project,
                    story_id=story_id,
                    session_id=session_key,
                    kind="heuristic",
                    exact=False,
                    claimed_by="dw-sessions",
                    state=state,
                    now=now,
                )
                summary["created"] += 1
        return summary

    # ── resilience ───────────────────────────────────────────────

    def mark_worktree_removed(
        self, worktree_id: str, *, now: Optional[datetime] = None
    ) -> int:
        """Worktree gone: its live attempts abandon, history intact."""
        moved = 0
        for attempt in self._repo.find_active(worktree_id=worktree_id):
            self._repo.transition(
                attempt.attempt_id, "abandoned", reason="worktree_removed", now=now
            )
            moved += 1
        return moved

    def mark_node_offline(
        self, node_id: str, *, now: Optional[datetime] = None
    ) -> int:
        """Node offline: honest `unknown`, recoverable when it returns."""
        moved = 0
        for attempt in self._repo.find_active(node_id=node_id):
            self._repo.transition(
                attempt.attempt_id, "unknown", reason="node_offline", now=now
            )
            moved += 1
        return moved

    def abandon_stale(
        self,
        *,
        max_age_seconds: int = DEFAULT_STALE_ATTEMPT_SECONDS,
        now: Optional[datetime] = None,
    ) -> int:
        """Timeout: attempts nothing has touched abandon with history."""
        moment = now or datetime.now(timezone.utc)
        moved = 0
        for attempt in self._repo.find_active():
            updated = _parse_ts(attempt.updated_at)
            if updated is None:
                continue
            if (moment - updated).total_seconds() > max_age_seconds:
                self._repo.transition(
                    attempt.attempt_id, "abandoned", reason="stale_timeout", now=now
                )
                moved += 1
        return moved

    # ── projection (GET /api/delivery/attempts) ──────────────────

    def list_attempts(
        self,
        *,
        source_id: Optional[str] = None,
        project: Optional[str] = None,
        story_id: Optional[str] = None,
        session_id: Optional[str] = None,
        active_only: bool = False,
        include_history: bool = True,
        limit: int = 200,
    ) -> dict[str, Any]:
        attempts = self._repo.list(
            source_id=source_id,
            project=project,
            story_id=story_id,
            session_id=session_id,
            active_only=active_only,
            limit=limit,
        )
        return {
            "attempts_schema": ATTEMPTS_SCHEMA,
            "attempts": [
                self._wire(attempt, include_history=include_history)
                for attempt in attempts
            ],
        }

    def _wire(
        self, attempt: WorkAttempt, *, include_history: bool = True
    ) -> dict[str, Any]:
        record = attempt.to_wire()
        if include_history:
            record["history"] = self._repo.events(attempt.attempt_id)
        return record


def _parse_ts(text: str) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


__all__ = [
    "ATTEMPTS_SCHEMA",
    "AttemptConflict",
    "AttemptError",
    "AttemptTransitionError",
    "DEFAULT_HEURISTIC_CAP",
    "DEFAULT_STALE_ATTEMPT_SECONDS",
    "WorkAttemptService",
    "resolver_from_registry",
]
