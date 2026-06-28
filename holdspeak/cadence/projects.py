"""resolve_project (CAD-1-02) — the ONE project-identity normalizer (chart §3.7).

Phase 1 is deliberately simple: prefer an explicit project, else a meeting label,
else a repo-root basename, else a domain. One function so later sources (activity,
agents) sharpen grouping in one place rather than scattering heuristics.
"""
from __future__ import annotations

import os
from typing import Optional


def resolve_project(
    *,
    explicit: Optional[str] = None,
    meeting_label: Optional[str] = None,
    repo_root: Optional[str] = None,
    domain: Optional[str] = None,
) -> Optional[str]:
    for candidate in (explicit, meeting_label):
        if candidate and candidate.strip():
            return candidate.strip()
    if repo_root and repo_root.strip():
        return os.path.basename(repo_root.rstrip("/")) or None
    if domain and domain.strip():
        return domain.strip()
    return None
