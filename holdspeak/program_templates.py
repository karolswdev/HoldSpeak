"""Program templates (2026-10-28, design §10): a starting shape, no YAML.

A template is a Python descriptor, like ``workbench_templates.AGENT_STARTERS``.
``program.create`` with ``template`` copies the template's Program fields
(Control level, reviewer, default Runs on, when idle; a template with no
level takes the desk's Control mode) onto the new Program;
``program.plan`` with the same template applies its step shape to each brief
he pastes (one step per brief; Race gives one brief two contenders). Every
value can be changed afterwards on the Program or on the row.

PG-REQ (2026-10-31, §10): each template ships its requirements
(``{text, kind, each_step, required}``), planted on the Program it makes as
``by = template``; he edits or waives each. A Review requirement is planted
only where the template's steps are reviewed (``step.gate_review``): a
Review needs the reviewer the step already has (§2, "not a second
reviewer"), so Fast cycle, Race and From the desk keep their list here and
plant it when he turns the review on (``requirements_for``).
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
DREAMING = "dreaming"
AUDIT = "audit"
#: Dreaming's bounds (PG-LANG §5.5): the folders a night may own; a template
#: plants the ones its repository has.
DREAMING_WITHIN = ("web/src/desk/", "docs/", "tests/unit/")

#: The one sentence every template ships on every step (decision 8).
ONLY_THE_BRIEF = "The change does only what its brief says."
#: Build and review adds this one.
HAS_A_TEST = "Each new behaviour has a test."
#: From the desk: one per step, from the step's origin (the action's title).
FROM_ACTION = "The change does what its action asks: {title}"

TEMPLATES: list[dict[str, Any]] = [
    {
        "id": FAST_CYCLE,
        "name": "Fast cycle",
        "description": "One step per brief. The repository's check gates each step. The desk's Control mode decides the merge.",
        "program": {"reviewer_profile": None, "default_profile": "claude-default"},
        "step": {"gate_check": True, "gate_review": False, "gate_merge": "level", "race": 0},
        "requirements": [{"text": ONLY_THE_BRIEF, "kind": "review", "each_step": True, "required": True}],
    },
    {
        "id": BUILD_AND_REVIEW,
        "name": "Build and review",
        "description": "One step per brief. The check, then Codex reviews the change. The desk's Control mode decides the merge.",
        "program": {"reviewer_profile": "codex-default", "default_profile": "claude-default"},
        "step": {"gate_check": True, "gate_review": True, "review_depth": "delta", "gate_merge": "level", "race": 0},
        "requirements": [{"text": ONLY_THE_BRIEF, "kind": "review", "each_step": True, "required": True},
                         {"text": HAS_A_TEST, "kind": "review", "each_step": True, "required": True}],
    },
    {
        "id": RACE,
        "name": "Race",
        "description": "One brief, two agents (Claude Code and Codex). The first green and reviewed branch wins.",
        "program": {"reviewer_profile": None, "default_profile": "claude-default"},
        "step": {"gate_check": True, "gate_review": False, "gate_merge": "level", "race": 2},
        "requirements": [{"text": ONLY_THE_BRIEF, "kind": "review", "each_step": True, "required": True}],
    },
    {
        "id": FROM_THE_DESK,
        "name": "From the desk",
        "description": "One step per open action of a project. The check gates each step.",
        "program": {"reviewer_profile": None, "default_profile": "claude-default"},
        "step": {"gate_check": True, "gate_review": False, "gate_merge": "level", "race": 0},
        "requirements": [],
        #: One per step, from the step's origin (``action:<id>``).
        "step_requirements": [{"text": FROM_ACTION, "kind": "review", "required": True}],
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
            # Phone (2026-10-28): overnight, the engine may call him where the
            # Reach rules allow it (a core question at YOLO rings at once).
            "may_call": True,
        },
        "step": {"gate_check": True, "gate_review": True, "review_depth": "delta", "gate_merge": "level", "race": 0},
        "requirements": [{"text": ONLY_THE_BRIEF, "kind": "review", "each_step": True, "required": True},
                         {"text": HAS_A_TEST, "kind": "review", "each_step": True, "required": True}],
    },
    {
        # PG-LANG §5.5 and journey J2 (LANG12): small fixes from the backlog,
        # at night, on the idle home engine, planned by the cheap planner.
        "id": DREAMING,
        "name": "Dreaming",
        "description": (
            "At night, 23:30 to 07:00: the backlog becomes tiny steps that fit 64k. pi builds on the home "
            "engine when it is idle; Claude Code reviews at a glance. YOLO: a green, reviewed step merges. "
            "At most 8 steps a night."
        ),
        "program": {
            "control": "yolo", "reviewer_profile": "claude-default", "reviewer_engine": None,
            "default_profile": "pi-default", "default_engine": HOME_ENGINE_PROFILE, "prefer_idle": True,
        },
        #: The Program lines (``ProgramService._update_language_fields``); the
        #: planner is the home engine when the library has it (it costs
        #: nothing), else the desk's ``agent.plan``; ``within`` keeps the
        #: folders the repository has.
        "language": {
            "review_depth": "glance", "budget_tokens": "64k", "night": "23:30–07:00 · at most 8 steps",
            "within": list(DREAMING_WITHIN), "planner_engine": HOME_ENGINE_PROFILE,
        },
        "step": {"gate_check": True, "gate_review": True, "review_depth": "glance", "gate_merge": "level", "race": 0},
        "requirements": [{"text": ONLY_THE_BRIEF, "kind": "review", "each_step": True, "required": True}],
    },
    {
        # PG-LANG §13b JRN8 and journey J7: a reviewer-only program. Each step
        # reads one surface and reports findings; nothing is built, checked,
        # reviewed or merged (``services/program_audit.py``).
        "id": AUDIT,
        "name": "Audit",
        "description": (
            "One step per surface (windows of the desk, the routes of a change). The agent reads and changes "
            "nothing; each finding becomes a Door task. The MUST findings can become a fix program."
        ),
        "program": {"reviewer_profile": None, "default_profile": "claude-default"},
        "step": {"gate_check": False, "gate_review": False, "gate_merge": "none", "race": 0},
        "requirements": [],
    },
]

TEMPLATE_IDS = tuple(template["id"] for template in TEMPLATES)


def get_template(template_id: Optional[str]) -> Optional[dict[str, Any]]:
    key = str(template_id or "").strip().lower()
    return next((dict(template) for template in TEMPLATES if template["id"] == key), None)


def reviewed(template: Optional[dict[str, Any]]) -> bool:
    """The template's steps are reviewed (their Review requirements plant)."""
    return bool(((template or {}).get("step") or {}).get("gate_review"))


def requirements_for(template: Optional[dict[str, Any]], *, review: Optional[bool] = None) -> list[dict[str, Any]]:
    """The template's Program-wide requirements that plant: a Review only
    where its steps are reviewed (``review`` overrides the template's gate)."""
    on = reviewed(template) if review is None else bool(review)
    return [dict(item) for item in (template or {}).get("requirements") or [] if item.get("kind") != "review" or on]


__all__ = [
    "BUILD_AND_REVIEW", "DREAMING", "DREAMING_WITHIN", "FAST_CYCLE", "FROM_THE_DESK", "HOME_ENGINE_PROFILE",
    "OVERNIGHT", "RACE",
    "FROM_ACTION", "HAS_A_TEST", "ONLY_THE_BRIEF", "TEMPLATES", "TEMPLATE_IDS", "get_template", "requirements_for",
    "reviewed",
]
