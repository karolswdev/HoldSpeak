"""HS-200-05 — what this machine actually lets the desk do, said honestly.

The owner's dictation needs three separate macOS grants, and any of them can
be missing with no signal at all:

* **Microphone** — the audio capture itself (`sounddevice`).
* **Input Monitoring** — the global hotkey listener (`holdspeak/hotkey.py`
  observes Right Option through `pynput.keyboard.Listener` while another app
  is focused).
* **Accessibility** — the synthetic typing that delivers the words
  (`privileged_effects/desktop_driver.py`'s `pynput.keyboard.Controller`) and
  the `System Events` query that names the frontmost app
  (`target_profile.py::_collect_macos_hints`).

The defect this module answers: `web_runtime.py` recorded
`global_hotkey_available` / `global_hotkey_error` and NOTHING read them, so a
denied permission was a silent failure — the key did nothing and the desk
never said why.

Two laws hold everywhere below.

1. **Checking never prompts.** Every API used here is the *query* half of its
   pair; the *requesting* half (`AXIsProcessTrustedWithOptions` with
   `kAXTrustedCheckOptionPrompt`, `IOHIDRequestAccess`,
   `requestAccessForMediaType:completionHandler:`) is never called, so opening
   the desk can never raise a surprise system dialog.
2. **An honest `unknown` beats a cheerful `granted`.** Off macOS, with the
   framework missing, or when the symbol is not there, the state is
   `unknown` with the reason named — never a state we did not read.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass
from typing import Any, Optional

# ── the four honest states ───────────────────────────────────────────────────
#
# `not_determined` is a real, distinct answer from both macOS APIs that offer
# it (`kIOHIDAccessTypeUnknown`, `AVAuthorizationStatusNotDetermined`): the
# grant was never asked for, so the app may not even be listed in the pane
# yet. Collapsing it into `denied` or `granted` would be a claim we cannot
# make, so it keeps its own name.
GRANTED = "granted"
DENIED = "denied"
NOT_DETERMINED = "not_determined"
UNKNOWN = "unknown"

#: Every state except `granted` means the capability does not work today.
def is_satisfied(state: str) -> bool:
    return state == GRANTED


# ── the three permissions this product actually needs ────────────────────────

MICROPHONE = "microphone"
INPUT_MONITORING = "input_monitoring"
ACCESSIBILITY = "accessibility"

#: `System Settings -> Privacy & Security -> <pane>`, carried as PATH TOKENS so
#: the face can draw a row instead of a sentence (UX canon A3: no prose).
_PANE_TOKENS: dict[str, list[str]] = {
    MICROPHONE: ["SYSTEM SETTINGS", "PRIVACY & SECURITY", "MICROPHONE"],
    INPUT_MONITORING: ["SYSTEM SETTINGS", "PRIVACY & SECURITY", "INPUT MONITORING"],
    ACCESSIBILITY: ["SYSTEM SETTINGS", "PRIVACY & SECURITY", "ACCESSIBILITY"],
}

#: The macOS deep link to the exact pane. Carried on the wire and NOT yet spent
#: by a verb: opening a URL from the hub crosses the privileged-effect
#: boundary, and that ruling is the orchestrator's, not this module's.
_PANE_URLS: dict[str, str] = {
    MICROPHONE: "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone",
    INPUT_MONITORING: "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent",
    ACCESSIBILITY: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
}

_LABELS: dict[str, str] = {
    MICROPHONE: "MICROPHONE",
    INPUT_MONITORING: "INPUT MONITORING",
    ACCESSIBILITY: "ACCESSIBILITY",
}

#: What stops working when this grant is missing — ONE token, not a sentence.
_NEEDED_FOR: dict[str, str] = {
    MICROPHONE: "CAPTURE",
    INPUT_MONITORING: "HOTKEY",
    ACCESSIBILITY: "TYPING",
}

ORDER = (MICROPHONE, INPUT_MONITORING, ACCESSIBILITY)


@dataclass(frozen=True)
class DesktopPermission:
    """One permission's honestly-read state."""

    id: str
    label: str
    state: str
    #: How we know — the API that answered, or why it could not be asked.
    source: str
    needed_for: str
    path: list[str]
    settings_url: str

    @property
    def satisfied(self) -> bool:
        return is_satisfied(self.state)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "state": self.state,
            "source": self.source,
            "needed_for": self.needed_for,
            "path": list(self.path),
            "settings_url": self.settings_url,
            "satisfied": self.satisfied,
        }


# ── the raw platform probes ──────────────────────────────────────────────────
#
# Each returns the platform's own value, or raises. They are module-level so a
# test can substitute one (including "the API is not there") without a mac.


def _is_macos() -> bool:
    return platform.system() == "Darwin"


def _ax_is_process_trusted() -> bool:
    """`AXIsProcessTrusted()` — the NON-prompting half of the Accessibility pair.

    `AXIsProcessTrustedWithOptions(kAXTrustedCheckOptionPrompt: True)` is the
    one that raises a system dialog; it is deliberately not used here.
    """
    from ApplicationServices import AXIsProcessTrusted  # type: ignore[import-not-found]

    return bool(AXIsProcessTrusted())


#: `IOHIDRequestType`: post = 0, listen = 1. The hotkey listener *observes*
#: keys typed into another app, which is the listen right.
_kIOHIDRequestTypeListenEvent = 1


def _iohid_check_access() -> int:
    """`IOHIDCheckAccess(kIOHIDRequestTypeListenEvent)` — Input Monitoring.

    `IOHIDCheckAccess` only reports; `IOHIDRequestAccess` is the prompting
    sibling and is never called. PyObjC ships no wrapper for this symbol, so
    it is reached through the IOKit framework binary directly.
    """
    import ctypes

    iokit = ctypes.cdll.LoadLibrary(
        "/System/Library/Frameworks/IOKit.framework/IOKit"
    )
    fn = iokit.IOHIDCheckAccess
    fn.restype = ctypes.c_int
    fn.argtypes = [ctypes.c_uint32]
    return int(fn(_kIOHIDRequestTypeListenEvent))


#: `AVMediaTypeAudio` is the four-character code `soun`.
_AVMediaTypeAudio = "soun"

_av_capture_device: Any = None


def _av_authorization_status() -> int:
    """`+[AVCaptureDevice authorizationStatusForMediaType:]` — Microphone.

    A pure read: `requestAccessForMediaType:completionHandler:` is the half
    that prompts, and is never called. `pyobjc-framework-AVFoundation` is not
    a HoldSpeak dependency, so the framework is loaded through the Objective-C
    runtime that `pyobjc-core` already provides (the class handle is cached;
    the STATUS never is, because a grant can change while the hub runs).
    """
    global _av_capture_device
    if _av_capture_device is None:
        import ctypes

        import objc  # type: ignore[import-not-found]

        ctypes.CDLL("/System/Library/Frameworks/AVFoundation.framework/AVFoundation")
        _av_capture_device = objc.lookUpClass("AVCaptureDevice")
    return int(
        _av_capture_device.authorizationStatusForMediaType_(_AVMediaTypeAudio)
    )


# ── the honest mapping from a platform value to a state ──────────────────────


def _not_a_mac() -> tuple[str, str]:
    return UNKNOWN, f"not macOS ({platform.system() or 'unknown platform'})"


def accessibility_state() -> tuple[str, str]:
    """Synthetic typing + the frontmost-app query."""
    if not _is_macos():
        return _not_a_mac()
    try:
        trusted = _ax_is_process_trusted()
    except Exception as exc:
        return UNKNOWN, f"AXIsProcessTrusted unavailable: {type(exc).__name__}"
    # The API is a single bool: there is no way to tell "switched off" from
    # "never listed". Report the effect (not trusted) rather than invent a
    # distinction the platform does not offer.
    return (GRANTED if trusted else DENIED), "AXIsProcessTrusted"


def input_monitoring_state() -> tuple[str, str]:
    """The global hotkey listener's right to observe keys."""
    if not _is_macos():
        return _not_a_mac()
    try:
        value = _iohid_check_access()
    except Exception as exc:
        return UNKNOWN, f"IOHIDCheckAccess unavailable: {type(exc).__name__}"
    # kIOHIDAccessType: granted = 0, denied = 1, unknown (= never asked) = 2.
    mapped = {0: GRANTED, 1: DENIED, 2: NOT_DETERMINED}.get(value)
    if mapped is None:
        return UNKNOWN, f"IOHIDCheckAccess returned {value}"
    return mapped, "IOHIDCheckAccess"


def microphone_state() -> tuple[str, str]:
    """Audio capture."""
    if not _is_macos():
        return _not_a_mac()
    try:
        value = _av_authorization_status()
    except Exception as exc:
        return UNKNOWN, f"AVCaptureDevice unavailable: {type(exc).__name__}"
    # AVAuthorizationStatus: notDetermined 0, restricted 1, denied 2,
    # authorized 3. `restricted` (an MDM/parental policy) is not a grant the
    # owner can flip, but it is honestly a refusal, so it reads denied.
    mapped = {0: NOT_DETERMINED, 1: DENIED, 2: DENIED, 3: GRANTED}.get(value)
    if mapped is None:
        return UNKNOWN, f"authorizationStatusForMediaType returned {value}"
    return mapped, "AVCaptureDevice.authorizationStatusForMediaType"


_PROBES = {
    MICROPHONE: microphone_state,
    INPUT_MONITORING: input_monitoring_state,
    ACCESSIBILITY: accessibility_state,
}


def permission(kind: str) -> DesktopPermission:
    """Read ONE permission's state now (never cached — a grant can change)."""
    probe = _PROBES.get(kind)
    if probe is None:
        raise ValueError(f"unknown permission: {kind}")
    state, source = probe()
    return DesktopPermission(
        id=kind,
        label=_LABELS[kind],
        state=state,
        source=source,
        needed_for=_NEEDED_FOR[kind],
        path=list(_PANE_TOKENS[kind]),
        settings_url=_PANE_URLS[kind],
    )


def permissions() -> list[DesktopPermission]:
    """Read all three, in the order the dictation path needs them."""
    return [permission(kind) for kind in ORDER]


# ── the reason a listener failed, as a token rather than a stack ─────────────


def hotkey_failure_token(error: str) -> str:
    """Classify a listener install failure into ONE face-safe token.

    UX canon A10 wants a plain reason, never a stack. The raw string still
    travels on the wire for the RAW lane; this is what a chip may say.
    """
    text = (error or "").lower()
    if not text:
        return ""
    if "pynput" in text:
        return "PYNPUT MISSING"
    if "display" in text or "gui session" in text:
        return "NO GUI SESSION"
    if "permission" in text or "denied" in text or "not trusted" in text:
        return "PERMISSION REFUSED"
    return "LISTENER FAILED"


def hotkey_custody(
    *,
    listener_available: Optional[bool],
    listener_error: str = "",
    key: str = "",
    display: str = "",
) -> dict[str, Any]:
    """The whole custody answer for one wire payload.

    `listener_available=None` means the reader has no runtime to ask (a bare
    test server, a dry-run app): the face must say UNKNOWN, never "working".
    """
    rows = [p.to_dict() for p in permissions()]
    missing = [r["id"] for r in rows if not r["satisfied"]]
    return {
        "platform": platform.system().lower(),
        "supported": _is_macos(),
        "key": key,
        "display": display,
        "available": listener_available,
        "error": listener_error or "",
        "reason": hotkey_failure_token(listener_error),
        "permissions": rows,
        "missing": missing,
        # The face draws the block when the listener is not proven up OR any
        # grant is not proven granted. `False` here means: nothing to say.
        "needs_attention": bool(missing) or listener_available is not True,
    }
