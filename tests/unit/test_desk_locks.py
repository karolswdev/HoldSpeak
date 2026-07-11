"""The Desk's mechanical locks (HS-73-09).

Phase 73 ended the web desk's modal era and made the Desk the front door.
These greps keep the owner-ratified rules from regressing silently:

- No dialog takeovers on the desk (create/edit/open happen in the world).
- No browser microphone on the desk (the orb drives the HUB's recorder).
- No privacy narration in desk UI surfaces (the egress badge is the ONE
  trust answer — POSITIONING canon; the badge's own canonical strings
  live in ``setup.ts`` and are the single allowed home).
- The positions contract stays byte-compatible (the bare
  ``hs.diorama.pos`` map; never a persist-middleware envelope).
- The front door stays the Desk with the first-run guard inline.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DESK = REPO / "web" / "src" / "desk"


def _tree(root: Path) -> dict[str, str]:
    return {
        str(p.relative_to(REPO)): p.read_text(encoding="utf-8")
        for p in sorted(root.rglob("*"))
        if p.suffix in {".ts", ".tsx", ".css"} and p.is_file()
    }


def test_no_dialog_takeovers_on_the_desk() -> None:
    for name, text in _tree(DESK).items():
        assert "aria-modal" not in text, f"dialog takeover pattern in {name}"
        assert 'role="dialog"' not in text, f"dialog takeover pattern in {name}"


def test_the_orb_never_uses_the_browser_microphone() -> None:
    """The rule's real intent (re-scoped in HS-78-02, owner steer "just
    talk to this stuff"): MEETING RECORDING always runs on the hub — the
    orb must never reach for the browser mic. Speak-to-fill capture
    (Phase 78) is exactly what the browser mic is for, and its shared
    helper lives outside the desk tree (web/src/lib/speakToFill.ts);
    desk components may import it but never call getUserMedia directly."""
    for name, text in _tree(DESK).items():
        assert "getUserMedia" not in text, (
            f"direct browser-mic call in {name} — capture lives in the "
            "shared speak-to-fill helper; the orb drives the hub recorder"
        )
        if name.endswith("RecordOrb.tsx"):
            assert "speak-to-fill" not in text and "speakToFill" not in text, (
                "the orb records via the hub, never the browser mic"
            )


def test_no_privacy_narration_in_desk_ui() -> None:
    banned = (
        "leaves your machine",
        "leave your machine",
        "stays on this machine",
        "stays on your machine",
    )
    for name, text in _tree(DESK).items():
        if name.endswith("desk/setup.ts"):
            continue  # the canonical egress-badge strings live here
        low = text.lower()
        for phrase in banned:
            assert phrase not in low, (
                f"privacy narration in {name} ({phrase!r}) — the egress "
                "badge is the answer"
            )


def test_positions_contract_stays_bare() -> None:
    store = (DESK / "store.ts").read_text(encoding="utf-8")
    assert '"hs.diorama.pos"' in store, "the legacy positions key is gone"
    assert "zustand/middleware" not in store, (
        "persist middleware would envelope the positions map and break the "
        "legacy contract"
    )


def test_the_front_door_is_the_desk_with_the_guard() -> None:
    routes = (REPO / "web/src/routes.tsx").read_text(encoding="utf-8")
    desk = (REPO / "web/src/desk/DeskApp.tsx").read_text(encoding="utf-8")
    assert 'path: "/"' in routes and 'label: "Desk"' in routes
    assert "setup?.arrival_required" in desk, "the first-value state left the front door"
    assert "arrivalRequired" in desk
    assert 'navigate("/welcome"' not in desk
