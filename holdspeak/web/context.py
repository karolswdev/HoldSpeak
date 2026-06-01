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
from typing import Any, Callable


@dataclass
class WebContext:
    """Accessors needed by the migrated route modules.

    Fields are added as each domain's routes move over. HS-26-01 (pilot:
    `/health`, `/api/state`) needs only the meeting-state getter.
    """

    get_state: Callable[[], dict[str, Any]]
