"""The launch nudge: what the runtime prints at the owner on startup.

Carved out of ``web_runtime.py`` by HS-202-02. The core stays boot, run
and config (``tests/unit/test_backend_density_guard.py``); what the
runtime SAYS on launch is runtime behaviour and belongs in a mixin.
"""
from __future__ import annotations

from ..logging_config import get_logger
from ..web_auth import authenticated_browser_url, ensure_web_token

log = get_logger("web_runtime")


class LaunchNudgeMixin:
    """One method: the first-run / setup nudge printed under the URL."""

    def _print_setup_nudge(self) -> None:
        """HS-42-03: point a first-run or hard-blocked user at /setup on launch.

        Uses the cheap (`skip_network`) setup-status read so it never delays
        startup, and is fully defensive — a status failure prints nothing and
        never blocks the runtime. A healthy returning user gets no nudge.
        """
        try:
            from ..db import get_database
            from ..setup_status import build_setup_status

            setup = build_setup_status(database=get_database())
            # HS-202-02 job 2: a printed URL that a browser cannot open is a
            # dead end, not a nudge. The runtime needs `?token=` even on
            # loopback and the token lives in tab-scoped storage, so a bare
            # URL renders `principal_right_required` for a bookmark, a second
            # tab, and tomorrow morning (04-sober-eye.md, rank 1). Every other
            # printed URL in this block already goes through
            # `authenticated_browser_url`; these two now do too.
            token = ensure_web_token(self.config)
            url = self.runtime_url
            unmet = sum(
                1 for s in setup.get("sections", []) if s.get("status") in ("fail", "warn")
            )
            if setup.get("arrival_required"):
                # HS-92-03: first value starts on the Desk; /welcome remains a
                # compatibility route to the same atom, never a wizard loop.
                desk_url = authenticated_browser_url(f"{url}/", token)
                print(f"  → Welcome! Say your first words on the Desk: open {desk_url}")
            elif setup.get("overall") == "blocked":
                suffix = f" — {unmet} thing{'' if unmet == 1 else 's'} need{'s' if unmet == 1 else ''} attention" if unmet else ""
                setup_url = authenticated_browser_url(f"{url}/setup", token)
                print(f"  → Setup needs attention: open {setup_url}{suffix}")
                action = (setup.get("primary_action") or {}).get("label")
                if action:
                    print(f"    Next: {action}")
            elif setup.get("overall") == "needs_attention":
                setup_url = authenticated_browser_url(f"{url}/setup", token)
                print(f"  → Setup ready (some optional items to review): {setup_url}")
        except Exception as exc:  # pragma: no cover - a nudge must never block boot
            log.debug(f"setup nudge skipped: {exc}")
