"""Rails objects as grounding kinds (HS-88-01).

An open phase, a story, an evidence file, the roadmap README become
grounding material — hydrated into the SAME `GroundingBlock` the
meeting/artifact path returns (Phase 87), so ask, steer, recipe, and
chain ground rails identically.

The receipt rule: a grounded rail object is a RECEIPT, not a scrape.
`dw context` (the `missioncontrol_bridge` posture) NAMES the file path
per repo; the hydration reads that contained file as opaque text and
headers it with provenance. Rail STATE (a story's status, a session's
correlation) is NEVER re-parsed from the markdown body — if a run
needs status, it comes from `dw state`/`dw sessions`, the same
three-document client contract the belt honors.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from . import missioncontrol_bridge as mc
from .grounding import GROUNDING_TRANSCRIPT_CAP, GroundingBlock

RAILS_KINDS = ("phase", "story", "evidence", "roadmap")


def _context_doc(
    repo_path: str, runner: Optional[mc.Runner]
) -> tuple[Optional[dict[str, Any]], str]:
    """The repo's `dw context` document (all its projects), or a typed
    unavailable. One fetch per repo — the caller caches."""
    doc, status, detail = mc._fetch_document(
        Path(repo_path), ["context", "--compact"], runner
    )
    if doc is None or not isinstance(doc, dict):
        return None, detail or status
    return doc, ""


def _find_project(doc: dict[str, Any], project: str) -> Optional[dict[str, Any]]:
    for entry in doc.get("projects", []):
        if isinstance(entry, dict) and str(entry.get("slug") or "") == project:
            return entry
    return None


def _resolve(
    proj: dict[str, Any], kind: str, rid: str
) -> Optional[tuple[str, str, str]]:
    """(relative_path, title, subtitle_kind) for a ref, or None.

    The path is NAMED by `dw context` — a trace entry or a project
    file — never composed from a slug guess.
    """
    if kind == "roadmap":
        readme = proj.get("readme")
        return (str(readme), "Roadmap README", "roadmap") if readme else None
    if kind == "phase":
        for phase in proj.get("phases", []):
            if str(phase.get("number")) == str(rid):
                path = phase.get("status_file")
                if path:
                    title = f"Phase {phase.get('number')} — {phase.get('slug') or ''}".strip(" —")
                    return (str(path), title, "phase")
        return None
    if kind in ("story", "evidence"):
        for phase in proj.get("phases", []):
            for story in phase.get("stories", []):
                if str(story.get("story_id") or "") == str(rid):
                    trace = story.get("trace") or {}
                    path = trace.get("story" if kind == "story" else "evidence")
                    if path:
                        title = f"{story.get('story_id')} {story.get('title') or ''}".strip()
                        return (str(path), title, kind)
        return None
    return None


def _read_capped(full: Path) -> Optional[str]:
    """The file as opaque text, capped + cut-marked (the transcript
    posture). None when the file cannot be read — a receipt that
    names a path the repo does not hold is not a best-effort block."""
    try:
        text = full.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if len(text) > GROUNDING_TRANSCRIPT_CAP:
        text = (
            text[:GROUNDING_TRANSCRIPT_CAP]
            + f"\n[rail object cut at {GROUNDING_TRANSCRIPT_CAP} chars]"
        )
    return text


def hydrate_rails_refs(
    refs: list[dict[str, Any]],
    *,
    project_map: Optional[dict[str, Any]] = None,
    runner: Optional[mc.Runner] = None,
) -> tuple[list[GroundingBlock], list[str]]:
    """Hydrate rails refs into GroundingBlocks; return (blocks, unknown).

    Each ref is ``{repo, project, kind, id}`` with
    ``kind in RAILS_KINDS``. `repo` is the project-map NAME; the repo
    PATH comes from the map. Unknown/unreachable refs come back as
    ``"<kind>:<id>"`` strings, refused by the caller.
    """
    pm = project_map or mc.load_project_map()
    projects_map = pm.get("projects", {})
    blocks: list[GroundingBlock] = []
    unknown: list[str] = []
    doc_cache: dict[str, Optional[dict[str, Any]]] = {}

    for ref in refs:
        if not isinstance(ref, dict):
            unknown.append(str(ref))
            continue
        repo_name = str(ref.get("repo") or "")
        project = str(ref.get("project") or "")
        kind = str(ref.get("kind") or "")
        rid = str(ref.get("id") or "")
        token = f"{kind}:{rid}"
        if kind not in RAILS_KINDS:
            unknown.append(token)
            continue
        repo_path = projects_map.get(repo_name)
        if not repo_path:
            unknown.append(token)
            continue
        if repo_path not in doc_cache:
            doc_cache[repo_path], _ = _context_doc(repo_path, runner)
        doc = doc_cache[repo_path]
        if doc is None:
            unknown.append(token)
            continue
        proj = _find_project(doc, project)
        if proj is None:
            unknown.append(token)
            continue
        resolved = _resolve(proj, kind, rid)
        if resolved is None:
            unknown.append(token)
            continue
        rel_path, title, subtitle_kind = resolved
        text = _read_capped(Path(repo_path) / rel_path)
        if text is None:
            unknown.append(token)
            continue
        blocks.append(
            GroundingBlock(
                kind=f"rails:{subtitle_kind}",
                ref=rid or rel_path,
                title=title,
                subtitle=f"{repo_name}/{project}",
                text=text,
            )
        )
    return blocks, unknown


__all__ = ["RAILS_KINDS", "hydrate_rails_refs"]
