"""Program templates (2026-10-28, design §10): a starting shape, no YAML.

A template is a Python descriptor, like ``workbench_templates.AGENT_STARTERS``.
``program.create`` with ``template`` copies the template's Program fields
(Control level, reviewer, default Runs on, when idle; a template with no
level takes the desk's Control mode) onto the new Program;
``program.plan`` with the same template applies its step shape to each brief
he pastes (one step per brief; Race gives one brief two contenders). Every
value can be changed afterwards on the Program or on the row.
"""
from __future__ import annotations

from typing import Any, Optional

#: The home box over Tailscale (the Calls default engine): the Overnight
#: template's builder engine when the library has it; else the desk's
#: ``agent.code`` assignment.
HOME_ENGINE_PROFILE = "engine-tailscale-karol-8080"

FAST_CYCLE = "fast-cycle"
BUILD_AND_REVIEW = "build-and-review"
RACE = "race"
FROM_THE_DESK = "from-the-desk"
OVERNIGHT = "overnight"

TEMPLATES: list[dict[str, Any]] = [
    {
        "id": FAST_CYCLE,
        "name": "Fast cycle",
        "description": "One step per brief. The repository's check gates each step. The desk's Control mode decides the merge.",
        "program": {"reviewer_profile": None, "default_profile": "claude-default"},
        "step": {"gate_check": True, "gate_review": False, "gate_merge": "level", "race": 0},
    },
    {
        "id": BUILD_AND_REVIEW,
        "name": "Build and review",
        "description": "One step per brief. The check, then Codex reviews the change. The desk's Control mode decides the merge.",
        "program": {"reviewer_profile": "codex-default", "default_profile": "claude-default"},
        "step": {"gate_check": True, "gate_review": True, "review_depth": "delta", "gate_merge": "level", "race": 0},
    },
    {
        "id": RACE,
        "name": "Race",
        "description": "One brief, two agents (Claude Code and Codex). The first green and reviewed branch wins.",
        "program": {"reviewer_profile": None, "default_profile": "claude-default"},
        "step": {"gate_check": True, "gate_review": False, "gate_merge": "level", "race": 2},
    },
    {
        "id": FROM_THE_DESK,
        "name": "From the desk",
        "description": "One step per open action of a project. The check gates each step.",
        "program": {"reviewer_profile": None, "default_profile": "claude-default"},
        "step": {"gate_check": True, "gate_review": False, "gate_merge": "level", "race": 0},
    },
    {
        "id": OVERNIGHT,
        "name": "Overnight on the home box",
        "description": (
            "One step per brief. pi builds on the home engine when it is idle; Claude Code reviews. "
            "It runs at YOLO: a green, reviewed step merges without you."
        ),
        "program": {
            "control": "yolo", "reviewer_profile": "claude-default", "reviewer_engine": None,
            "default_profile": "pi-default", "default_engine": HOME_ENGINE_PROFILE, "prefer_idle": True,
        },
        "step": {"gate_check": True, "gate_review": True, "review_depth": "delta", "gate_merge": "level", "race": 0},
    },
]

TEMPLATE_IDS = tuple(template["id"] for template in TEMPLATES)


def get_template(template_id: Optional[str]) -> Optional[dict[str, Any]]:
    key = str(template_id or "").strip().lower()
    return next((dict(template) for template in TEMPLATES if template["id"] == key), None)


__all__ = [
    "BUILD_AND_REVIEW", "FAST_CYCLE", "FROM_THE_DESK", "HOME_ENGINE_PROFILE", "OVERNIGHT", "RACE",
    "TEMPLATES", "TEMPLATE_IDS", "get_template",
]
