"""Project knowledge-base detector plugin.

Scores each transcript window against user-defined projects and returns
matched projects with confidence scores. Designed to run as the first
plugin in every MIR chain.
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from typing import Any


def _normalize(text: str) -> str:
    """Lowercase and collapse whitespace."""
    return re.sub(r"\s+", " ", text.strip().lower())


def _score_project(
    haystack: str, project: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """Score a single project against a normalized transcript.

    Returns (score, keyword_hits, member_hits).
    """
    keywords: list[str] = project.get("keywords") or []
    members: list[str] = project.get("team_members") or []
    name = str(project.get("name") or "")

    # Keyword hits
    keyword_hits = [kw for kw in keywords if kw.lower() in haystack]

    # Project name term hits (words > 2 chars)
    name_terms = [t for t in name.lower().split() if len(t) > 2]
    name_hits = [t for t in name_terms if t in haystack]

    # Team member hits
    member_hits = [m for m in members if m.lower() in haystack]

    score = min(
        1.0,
        (0.15 * len(keyword_hits))
        + (0.10 * len(name_hits))
        + (0.12 * len(member_hits)),
    )
    return score, keyword_hits, member_hits


@dataclass
class ProjectDetectorPlugin:
    """Scores transcript windows against project knowledge bases.

    Implements the HostPlugin protocol (id, version, run).
    """

    id: str = "project_detector"
    version: str = "0.1.0"
    _projects: list[dict[str, Any]] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def reload_projects(self, projects: list[dict[str, Any]]) -> None:
        """Replace the in-memory project snapshot (thread-safe)."""
        snapshot = list(projects)
        with self._lock:
            self._projects = snapshot

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Score transcript against all active projects."""
        transcript = str(context.get("transcript") or "").strip()
        active_intents = list(context.get("active_intents") or [])

        with self._lock:
            projects = list(self._projects)

        if not transcript or not projects:
            return {
                "plugin_id": self.id,
                "kind": "detector",
                "summary": "No projects configured or empty transcript.",
                "matched_projects": [],
                "token_count": 0,
                "active_intents": active_intents,
                "confidence_hint": 0.0,
            }

        haystack = _normalize(transcript)
        matches: list[dict[str, Any]] = []
        for project in projects:
            score, keyword_hits, member_hits = _score_project(haystack, project)
            if score > 0:
                matches.append({
                    "project_id": project["id"],
                    "project_name": project["name"],
                    "score": round(score, 4),
                    "keyword_hits": keyword_hits,
                    "member_hits": member_hits,
                    "detection_threshold": project.get("detection_threshold", 0.4),
                })

        matches.sort(key=lambda m: -m["score"])
        return {
            "plugin_id": self.id,
            "kind": "detector",
            "summary": f"Detected {len(matches)} project(s)." if matches else "No project matches.",
            "matched_projects": matches,
            "token_count": len(transcript.split()),
            "active_intents": active_intents,
            "confidence_hint": round(matches[0]["score"], 3) if matches else 0.0,
        }
