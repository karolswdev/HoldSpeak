"""Shared accessor object the web route modules read from (HS-26-01).

As routes migrate out of `MeetingWebServer._create_app` (where they currently
close over `self`), they instead take a `WebContext` carrying just the accessors
they need. This grows one field per migrated concern; HS-26-06 collapses the
server's 40+ constructor callbacks into this object.

Keep it a plain data holder: route modules import `WebContext`; `WebContext`
imports no route module (so there is no import cycle).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class WebContext:
    """Accessors needed by the migrated route modules.

    Fields are added as each domain's routes move over. HS-26-01 (pilot:
    `/health`, `/api/state`) needs only the meeting-state getter; HS-26-02
    adds the meeting / speaker / intel cluster's accessors. Every field beyond
    `get_state` defaults to ``None`` so partially-wired contexts (e.g. the pilot
    test) stay valid; the server populates the full set in `_create_app`.
    """

    get_state: Callable[[], dict[str, Any]]

    # HS-26-02: meeting-lifecycle + action-item callbacks the meeting routes
    # invoke. The DB-backed read routes (meetings/speakers/intel listings) close
    # over no server state, so they need nothing here.
    broadcast: Optional[Callable[[str, Any], None]] = None
    on_bookmark: Optional[Callable[[str], Any]] = None
    on_start: Optional[Callable[..., Any]] = None
    on_stop: Optional[Callable[[], Any]] = None
    on_meeting_stop: Optional[Callable[[], Any]] = None
    on_update_action_item: Optional[Callable[[str, str], Any]] = None
    on_update_action_item_review: Optional[Callable[[str, str], Any]] = None
    on_edit_action_item: Optional[Callable[..., Any]] = None
    on_update_meeting: Optional[Callable[..., Any]] = None
    on_set_title: Optional[Callable[[str], None]] = None
    on_set_tags: Optional[Callable[[list[str]], None]] = None
