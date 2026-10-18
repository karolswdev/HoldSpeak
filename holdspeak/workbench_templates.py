"""Starters for a new automation (Betterment A7), and the parked templates.

A starter is one automation's sentence (DESIGN §4, "Starters"): the
instruction (Do), its sources (About), when it runs (When) and where the
result goes (Put it in). A press makes one automation with that sentence and
no agent: nothing is copied (before A7 each press copied a new recipe). A
blank the starter cannot guess ("which people?") is named in ``blanks``; the
automation window shows it highlighted until he fills it.

The four HS-116-05 templates (TODO, Triage, Meeting Prep, Morning Brief) are
retired as starters: Today and cadence do that work. They stay below, hidden
(``get_template`` still finds them, so an old caller keeps working).
"""
from __future__ import annotations

#: Betterment A7: the four starters, in the order New automation shows them.
#: ``when`` is a When choice (``WorkbenchService.set_when``'s shape); a
#: schedule is stored and stays Off until he turns it On (a starter is not a
#: recurring-inference approval). "When a meeting ends" is not a start the hub
#: can deliver today (``services/automation_when.py``), so Meeting follow-ups
#: runs when he presses Run now, about the meeting he names.
STARTERS = [
    {
        "id": "friday-team-update",
        "name": "Friday team update",
        "description": "Drafts your team update from this week's meetings and notes.",
        "instruction": (
            "Draft my team update for this week: what shipped, what slipped, "
            "and what I need from each person. Name the meeting or note each point comes from."
        ),
        "sources": ["meetings:this_week", "notes:this_week"],
        "when": {"kind": "schedule", "every": "week", "day": 5, "time": "15:00"},
        "output_target": "inbox",
        "blanks": {},
    },
    {
        "id": "meeting-follow-ups",
        "name": "Meeting follow-ups",
        "description": "Lists the decisions and follow-ups of a meeting, with owners and dates.",
        "instruction": (
            "List the decisions and the follow-ups from this meeting. "
            "Give each follow-up an owner and a date when the meeting names them."
        ),
        "sources": [],
        "when": {"kind": "manual"},
        "output_target": "needs_you",
        "blanks": {"about": "which meeting?"},
    },
    {
        "id": "one-on-one-prep",
        "name": "1:1 prep",
        "description": "Prepares your 1:1s: open commitments, the last 1:1, what to raise.",
        "instruction": (
            "For each person: their open commitments, what we said in our last 1:1, "
            "and what I should raise this week."
        ),
        "sources": [],
        "when": {"kind": "schedule", "every": "week", "day": 1, "time": "08:00"},
        "output_target": "inbox",
        "blanks": {"about": "which people?"},
    },
    {
        "id": "summarize-a-drawer",
        "name": "Summarize a drawer",
        "description": "Summarizes what is new in a drawer.",
        "instruction": "Summarize what is new in these notes. Start with what needs me.",
        "sources": [],
        "when": {"kind": "manual"},
        "output_target": "inbox",
        "blanks": {"about": "which drawer?"},
    },
]

TEMPLATES = [
    {
        "id": "todo-agent",
        "name": "TODO",
        "description": "An overnight backlog worker that processes items and leaves receipts.",
        "icon": "⚡",
        "recipe": {
            "name": "TODO Agent",
            "role": "Backlog worker",
            "system_prompt": (
                "You are the TODO Agent. Your job is to work through items on your workbench, "
                "one by one. For each item:\n\n"
                "1. Read the item title, body, and any grounding material.\n"
                "2. Do what the item asks — summarize, draft, review, research, analyze.\n"
                "3. Produce a short, concrete receipt: what you did, what you found, what the owner should know.\n"
                "4. If the item requires an action you cannot take (sending an email, merging a PR, "
                "deploying code), say so clearly and propose the action for the owner to approve.\n\n"
                "Never fabricate. Never execute actions beyond your scope. "
                "Propose, never act. Be concise."
            ),
        },
        "workbench": {
            "schedule": "0 2 * * *",
        },
        "skill_names": ["Systematic Task Processing", "Grounded Citations", "Action Item Extraction"],
        "starter_items": [
            {"title": "Review open PRs", "priority": 2},
            {"title": "Summarize yesterday's meeting notes", "priority": 3},
            {"title": "Draft the weekly status update", "priority": 3},
        ],
    },
    {
        "id": "triage-agent",
        "name": "Triage",
        "description": "Classifies and prioritizes incoming items by urgency.",
        "icon": "◈",
        "recipe": {
            "name": "Triage Agent",
            "role": "Item classifier",
            "system_prompt": (
                "You are the Triage Agent. For each item on your workbench:\n\n"
                "1. Read the item title, body, and any grounding material.\n"
                "2. Classify by urgency: ACT NOW / THIS WEEK / BACKLOG / DISMISS.\n"
                "3. Write a one-line rationale for the classification.\n"
                "4. If the item needs more context to classify, say what's missing.\n\n"
                "Be decisive. Every item gets a classification. "
                "Never leave an item unclassified."
            ),
        },
        "skill_names": ["Structured Summarization", "Action Item Extraction"],
        "workbench": {
            "schedule": None,
        },
        "starter_items": [],
    },
    {
        "id": "meeting-prep-agent",
        "name": "Meeting Prep",
        "description": "Prepares context packs for upcoming meetings.",
        "icon": "▣",
        "recipe": {
            "name": "Meeting Prep Agent",
            "role": "Meeting preparation",
            "system_prompt": (
                "You are the Meeting Prep Agent. For each item on your workbench "
                "(each item represents an upcoming meeting):\n\n"
                "1. Read the meeting title and any grounding material (prior meetings, "
                "artifacts, notes).\n"
                "2. Summarize what happened in prior meetings with the same participants.\n"
                "3. List any open action items from those meetings.\n"
                "4. Identify the likely topics and any decisions that need to be made.\n"
                "5. Produce a concise prep pack the owner can read in 2 minutes.\n\n"
                "Never fabricate attendees, dates, or decisions. If no grounding is "
                "available, say so honestly."
            ),
        },
        "skill_names": ["Meeting Preparation", "Structured Summarization", "Action Item Extraction"],
        "workbench": {
            "schedule": "0 7 * * 1-5",
        },
        "starter_items": [
            {"title": "Monday standup", "priority": 2},
            {"title": "1:1 with manager", "priority": 2},
        ],
    },
    {
        "id": "morning-brief",
        "name": "Morning Brief",
        "description": "Collects overnight signals and delivers a concise morning briefing.",
        "icon": "☀",
        "recipe": {
            "name": "Morning Brief",
            "role": "Daily briefing",
            "system_prompt": (
                "You are the Morning Brief agent. Your job is to prepare a concise "
                "morning briefing for the owner. For each item in your workbench:\n\n"
                "1. Read the item title and any grounding material (meetings, artifacts, notes).\n"
                "2. Produce a structured summary following this format:\n\n"
                "**[Item title]** — [one-line summary]. Action needed: [yes/no].\n\n"
                "After processing all items, end with a **Today's focus** section: "
                "the 1-3 most important things from all items, ranked by urgency.\n\n"
                "Rules:\n"
                "- Never fabricate. If an item has no grounding, say 'no context attached.'\n"
                "- Never propose actions beyond the owner's explicit items.\n"
                "- If nothing material happened overnight, say so in one line. "
                "Do not pad an empty day."
            ),
        },
        "skill_names": ["Structured Summarization", "Action Item Extraction"],
        "workbench": {
            "schedule": "0 7 * * 1-5",
        },
        "starter_items": [
            {"title": "Yesterday's meetings", "body": "Summarize any meetings from the last 24 hours.", "priority": 1},
            {"title": "Open automation receipts", "body": "Summarize what other automations did overnight.", "priority": 2},
            {"title": "Delivery status", "body": "Report the current phase, next story, and any blockers from the delivery roadmap.", "priority": 2},
        ],
    },
]


def list_templates() -> list[dict]:
    """What New automation offers: the starters only (the templates are hidden)."""
    return STARTERS


def get_starter(starter_id: str) -> dict | None:
    return next((s for s in STARTERS if s["id"] == starter_id), None)


def get_template(template_id: str) -> dict | None:
    """A retired template (hidden from New automation; still callable)."""
    for t in TEMPLATES:
        if t["id"] == template_id:
            return t
    return None


def starter_blanks(instruction: str, sources: list[str]) -> dict[str, str]:
    """The blanks still open on an automation made from a starter: its Do is
    still the starter's own and the line is still empty. Edited, it has none."""
    text = str(instruction or "").strip()
    for starter in STARTERS:
        if starter["instruction"] == text:
            return {line: words for line, words in starter["blanks"].items()
                    if not (line == "about" and sources)}
    return {}
