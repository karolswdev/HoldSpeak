"""Pre-built Workbench templates (HS-116-05).

Each template ships a recipe (the agent persona), a workbench config,
and optional starter items. The user picks a template, picks a target,
and they're running in thirty seconds.
"""
from __future__ import annotations

TEMPLATES = [
    {
        "id": "todo-agent",
        "name": "TODO Agent",
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
        "name": "Triage Agent",
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
        "name": "Meeting Prep Agent",
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
            {"title": "Open workbench receipts", "body": "Summarize what other workbenches did overnight.", "priority": 2},
            {"title": "Delivery status", "body": "Report the current phase, next story, and any blockers from the delivery roadmap.", "priority": 2},
        ],
    },
]


def list_templates() -> list[dict]:
    return TEMPLATES


def get_template(template_id: str) -> dict | None:
    for t in TEMPLATES:
        if t["id"] == template_id:
            return t
    return None
