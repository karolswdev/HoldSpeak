"""Skill injection into agent prompts (HS-116-06).

Assembles active skills for a recipe into a bounded text block
injected between the recipe's system prompt and the task content.
"""
from __future__ import annotations

from typing import Optional

from .logging_config import get_logger

log = get_logger("skill_injection")

SKILL_BUDGET_BYTES = 8192


def skills_for_recipe(recipe_id: Optional[str]) -> str:
    """Return the assembled skills text for a recipe, or empty string."""
    if not recipe_id:
        return ""
    try:
        from .db import get_database
        db = get_database()
        skills = db.skills.list_for_recipe(recipe_id, active_only=True)
    except Exception:
        return ""
    if not skills:
        return ""
    parts: list[str] = []
    dropped: list[str] = []
    total = 0
    for skill in skills:
        entry = f"## {skill.title}\n{skill.body}"
        entry_bytes = len(entry.encode("utf-8"))
        if total + entry_bytes > SKILL_BUDGET_BYTES:
            dropped.append(skill.title)
            continue
        parts.append(entry)
        total += entry_bytes
    if dropped:
        log.warning(
            f"Skills dropped for recipe {recipe_id} (budget {SKILL_BUDGET_BYTES}B): "
            + ", ".join(dropped)
        )
    if not parts:
        return ""
    return "# Skills\n\n" + "\n\n".join(parts)


def inject_skills(system_prompt: str, recipe_id: Optional[str]) -> str:
    """Append skill text to a system prompt, bounded by budget."""
    skills_text = skills_for_recipe(recipe_id)
    if not skills_text:
        return system_prompt
    if system_prompt:
        return system_prompt + "\n\n" + skills_text
    return skills_text
