"""Built-in skill library for HoldSpeak workbenches (HS-116-19).

Ships 10 production skills adapted from the Hermes Agent ecosystem (MIT)
and original HoldSpeak skills. Seeded into the DB on first run.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

SKILLS_DIR = Path(__file__).parent


def _parse_skill(text: str) -> dict[str, Any]:
    """Parse a skill markdown file with YAML-like front matter."""
    meta: dict[str, Any] = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                m = re.match(r'^(\w+):\s*"?(.+?)"?\s*$', line.strip())
                if m:
                    meta[m.group(1)] = m.group(2)
                elif re.match(r'^(\w+):\s*\[', line.strip()):
                    key = line.strip().split(":")[0]
                    val = re.findall(r'[\w-]+', line.split("[", 1)[1])
                    meta[key] = val
            body = parts[2].strip()
    return {
        "name": meta.get("name", "unnamed"),
        "title": meta.get("name", "Unnamed Skill").replace("-", " ").title(),
        "description": meta.get("description", ""),
        "version": meta.get("version", "1.0.0"),
        "source": meta.get("source", "original"),
        "tags": meta.get("tags", []),
        "body": body,
    }


def list_builtin_skills() -> list[dict[str, Any]]:
    """Return all built-in skills as parsed dicts."""
    skills = []
    for path in sorted(SKILLS_DIR.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
            skill = _parse_skill(text)
            skill["filename"] = path.name
            skills.append(skill)
        except (OSError, ValueError):
            continue
    return skills


def seed_skills_if_empty() -> int:
    """Seed the skills table from built-in library if it's empty. Returns count seeded."""
    try:
        from ..db import get_database
        from ..web.routes.primitives._shared import _new_id
        db = get_database()
        existing = db.skills.list()
        if existing:
            return 0
        builtin = list_builtin_skills()
        for skill in builtin:
            db.skills.upsert(
                skill_id=_new_id("skill"),
                title=skill["title"],
                body=skill["body"],
                source="owner-authored",
                status="active",
                recipe_ids=[],
                created_by=f"library:{skill['filename']}",
            )
        return len(builtin)
    except Exception:
        return 0
