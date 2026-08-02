"""Read-only Delivery Workbench roadmap routes (HS-113-07)."""
from __future__ import annotations

import asyncio
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..context import WebContext

_PHASE = re.compile(r"^phase-(\d+)(?:-(.*))?$")
_STORY = re.compile(r"^story-(\d+)(?:-(.*))?\.md$")
_STATUS = re.compile(r"^(?:-\s*)?\*\*Status:\*\*\s*(.+?)\s*$", re.MULTILINE | re.IGNORECASE)
_H1 = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_CURRENT = re.compile(r"\*\*Current phase:\*\*[^\n]*?phase-(\d+)", re.IGNORECASE)
_ANY_PHASE = re.compile(r"phase-(\d+)(?:-([a-z0-9-]+))?", re.IGNORECASE)
_ERROR = re.compile(r"^(?:ERROR\s+)?(?:(?P<path>[^:]+):\s+)?(?P<issue>.+)$")


def _safe_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def _title(value: str) -> str:
    return value.replace("-", " ").strip().title()


def _status(path: Path) -> str:
    match = _STATUS.search(_safe_text(path))
    value = match.group(1).strip().lower() if match else "backlog"
    if value in {"complete", "closed", "shipped"}:
        return "done"
    return value if value in {"backlog", "ready", "in-progress", "blocked", "done"} else "backlog"


def _run(repo_root: Path, *args: str) -> tuple[int, str]:
    try:
        result = subprocess.run(
            [str(repo_root / ".githooks" / "dw"), *args],
            cwd=repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20,
            check=False,
        )
        return result.returncode, result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 2, str(exc)


def _issues(output: str) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.lower() == "dw check: ok":
            continue
        match = _ERROR.match(line)
        if match:
            found.append(
                {
                    "severity": "error" if line.startswith("ERROR") else "warn",
                    "path": (match.group("path") or "").strip(),
                    "issue": match.group("issue").strip(),
                }
            )
    return found


def _phase(phase_dir: Path) -> dict[str, Any] | None:
    match = _PHASE.match(phase_dir.name)
    if not match:
        return None
    number = int(match.group(1))
    title = _title(match.group(2) or "")
    stories: list[dict[str, Any]] = []
    for story_path in sorted(phase_dir.glob("story-*.md")):
        story_match = _STORY.match(story_path.name)
        if not story_match:
            continue
        text = _safe_text(story_path)
        heading = _H1.search(text)
        story_title = heading.group(1).strip() if heading else _title(story_match.group(2) or "")
        story_id_match = re.search(r"\b([A-Z][A-Z0-9]+-\d+-\d+)\b", text)
        story_id = story_id_match.group(1) if story_id_match else f"{number}-{story_match.group(1)}"
        evidence = phase_dir / f"evidence-story-{story_match.group(1)}.md"
        stories.append(
            {
                "id": story_id,
                "title": story_title,
                "status": _status(story_path),
                "hasEvidence": evidence.is_file(),
                "phase": number,
            }
        )
    done = sum(story["status"] == "done" for story in stories)
    status_file = phase_dir / "current-phase-status.md"
    return {
        "number": number,
        "title": title,
        "storiesDone": done,
        "storiesTotal": len(stories),
        "status": "closed" if stories and done == len(stories) else ("active" if status_file.exists() else "not-started"),
        "stories": stories,
    }


def _project_root(repo_root: Path) -> Path:
    return repo_root / "pm" / "roadmap"


def _project_path(repo_root: Path, slug: str) -> Path | None:
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", slug):
        return None
    root = _project_root(repo_root) / slug
    return root if root.is_dir() and (root / "README.md").is_file() else None


def _project(repo_root: Path, slug: str, include_phases: bool = True) -> dict[str, Any] | None:
    root = _project_path(repo_root, slug)
    if root is None:
        return None
    readme = root / "README.md"
    phases = [p for d in root.iterdir() if d.is_dir() if (p := _phase(d)) is not None]
    phases.sort(key=lambda phase: phase["number"], reverse=True)
    readme_text = _safe_text(readme)
    name_match = _H1.search(readme_text)
    current_match = _CURRENT.search(readme_text) or _ANY_PHASE.search(readme_text)
    current_number = int(current_match.group(1)) if current_match else (phases[0]["number"] if phases else 0)
    current = next((phase for phase in phases if phase["number"] == current_number), phases[0] if phases else None)
    exit_code, check_output = _run(repo_root, "check", slug)
    issues = _issues(check_output)
    health = "green" if exit_code == 0 else ("warn" if exit_code == 1 else "red")
    _, next_output = _run(repo_root, "next", slug, "--json")
    try:
        next_data = json.loads(next_output)
    except (TypeError, json.JSONDecodeError):
        next_data = {}
    next_story = next_data.get("story_id") or next_data.get("id") or next_data.get("next_story", {}).get("story_id")
    result: dict[str, Any] = {
        "slug": slug,
        "name": name_match.group(1).strip() if name_match else _title(slug),
        "phaseCount": len(phases),
        "currentPhase": current["number"] if current else current_number,
        "currentPhaseTitle": current["title"] if current else "",
        "storiesDone": current["storiesDone"] if current else 0,
        "storiesTotal": current["storiesTotal"] if current else 0,
        "health": health,
        "issues": [issue["issue"] for issue in issues],
        "nextStoryId": str(next_story) if next_story else None,
    }
    if include_phases:
        result["phases"] = phases
        result["healthIssues"] = issues
    return result


def build_roadmaps_router(ctx: WebContext, *, repo_root: Path | None = None) -> APIRouter:
    """Build the read-only roadmap API. ``repo_root`` is a test seam."""
    _ = ctx
    router = APIRouter()
    root = repo_root or Path(__file__).resolve().parents[3]

    @router.get("/api/roadmaps")
    async def api_roadmaps() -> Any:
        def read() -> list[dict[str, Any]]:
            roadmap_root = _project_root(root)
            if not roadmap_root.is_dir():
                return []
            projects = []
            for directory in sorted(roadmap_root.iterdir()):
                project = _project(root, directory.name, include_phases=False)
                if project:
                    projects.append(project)
            return projects

        return JSONResponse({"roadmaps": await asyncio.to_thread(read)})

    @router.get("/api/roadmaps/{slug}")
    async def api_roadmap(slug: str) -> Any:
        project = await asyncio.to_thread(_project, root, slug)
        if project is None:
            return JSONResponse({"error": "Roadmap not found"}, status_code=404)
        return JSONResponse(project)

    @router.get("/api/roadmaps/{slug}/health")
    async def api_roadmap_health(slug: str) -> Any:
        if _project_path(root, slug) is None:
            return JSONResponse({"error": "Roadmap not found"}, status_code=404)
        code, output = await asyncio.to_thread(_run, root, "check", slug)
        return JSONResponse({"health": "green" if code == 0 else ("warn" if code == 1 else "red"), "issues": _issues(output)})

    @router.get("/api/roadmaps/{slug}/next")
    async def api_roadmap_next(slug: str) -> Any:
        if _project(root, slug, include_phases=False) is None:
            return JSONResponse({"error": "Roadmap not found"}, status_code=404)
        code, output = await asyncio.to_thread(_run, root, "next", slug, "--json")
        try:
            data = json.loads(output)
        except (TypeError, json.JSONDecodeError):
            data = None
        return JSONResponse({"next": data if code == 0 and isinstance(data, dict) else None})

    return router
