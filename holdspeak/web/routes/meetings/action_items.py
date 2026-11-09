"""The action items of every meeting: produced from their declared operations (``meeting_operations.py``).

HS-132-02: the triage verbs ask the live meeting first (``_declared.registry_for``
binds the runtime's session mutations), then the archive.
"""
from __future__ import annotations

from fastapi import APIRouter

from ...context import WebContext
from . import _declared


def build_action_items_router(ctx: WebContext) -> APIRouter:
    return _declared.router(ctx, ("action_item.list", "action_item.update", "action_item.review"), module=__name__)
