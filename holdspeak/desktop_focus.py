"""Platform focus identity used by desktop-input admission and execution."""
from __future__ import annotations

import platform


def focused_signature() -> str:
    """Return a content-free identity for the currently focused app/window."""
    system = platform.system()
    if system == "Darwin":
        try:
            import AppKit

            app = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
            if app is None:
                return ""
            pid = int(app.processIdentifier())
            window_id = ""
            try:
                import Quartz

                options = (
                    Quartz.kCGWindowListOptionOnScreenOnly
                    | Quartz.kCGWindowListExcludeDesktopElements
                )
                windows = Quartz.CGWindowListCopyWindowInfo(
                    options, Quartz.kCGNullWindowID
                )
                window_id = next(
                    (
                        str(item.get(Quartz.kCGWindowNumber) or "")
                        for item in windows
                        if int(item.get(Quartz.kCGWindowOwnerPID) or -1) == pid
                        and int(item.get(Quartz.kCGWindowLayer) or -1) == 0
                    ),
                    "",
                )
            except Exception:
                pass
            return ":".join(
                ("mac", str(pid), str(app.bundleIdentifier() or ""), window_id)
            )
        except Exception:
            return ""
    if system == "Linux":
        try:
            from .target_profile import collect_active_target_hints

            hints = collect_active_target_hints()
            return ":".join(
                (
                    "linux",
                    str(hints.get("pid") or ""),
                    str(hints.get("window_title") or ""),
                )
            ).rstrip(":")
        except Exception:
            return ""
    return ""


__all__ = ["focused_signature"]
