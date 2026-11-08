"""Parked 2026-11-08 (Lane I): guards of the Models chain (settings/Models.tsx,
frontDoor, ModelLibraryCore) and ConciergeCore, which no entry point reached
and which are parked under web/src/**/_parked/. Kept, not run."""
from __future__ import annotations

from pathlib import Path

from tests.unit.test_interior_canon_guard import WEB_SRC  # noqa: F401
from tests.unit.test_ux_canon_scan import _load_scanner  # noqa: F401


def test_runs_on_room_stays_folded_into_the_models_module() -> None:
    """HS-112-01 — the standalone Runs-on room stays retired.

    Story 143-12 lawfully replaced the old target-CRUD Models body with a thin
    `settings/Models.tsx` host adapter to ModelLibraryCore. The technical
    placement facts now live in its folded Runs on disclosure, beside folded
    RAW facts; the library may never recreate a raw Field/Select editor or
    reopen the retired target route.
    """
    assert not (WEB_SRC / "pages" / "cores" / "ProfilesCore.tsx").exists(), (
        "HS-112-01 regression: the standalone Runs-on room must stay retired."
    )
    adapter = (WEB_SRC / "pages" / "cores" / "settings" / "Models.tsx").read_text(
        encoding="utf-8"
    )
    door = (WEB_SRC / "pages" / "cores" / "frontDoor.tsx").read_text(
        encoding="utf-8"
    )
    core = (WEB_SRC / "pages" / "cores" / "ModelLibraryCore.tsx").read_text(
        encoding="utf-8"
    )
    client = (WEB_SRC / "pages" / "cores" / "modelLibrary.ts").read_text(
        encoding="utf-8"
    )
    # HS-156-04: the adapter hosts the front door, which hosts the library
    # in its Advanced fold. The composition chain: settings/Models -> FrontDoorView -> ModelLibraryCore.
    assert "FrontDoorView" in adapter and "/api/inference-targets" not in adapter, (
        "HS-156-04 regression: the Models slot adapter must host the front "
        "door, never revive target CRUD."
    )
    assert "ModelLibraryCore" in door and "/api/inference-targets" not in door, (
        "HS-156-04 regression: the front door must host the Model Library "
        "in its Advanced fold, never revive target CRUD."
    )
    assert 'FoldGadget title="Where it runs"' in core and "SurfaceFacts" in core, (
        "HS-112-01 regression: Where it runs technical facts must remain folded in "
        "the one Models/Model Library surface."
    )
    assert "<Field" not in core and "<Select" not in core, (
        "HS-112-01 regression: Model Library must not recreate a raw "
        "label-over-input target editor."
    )
    assert "/api/inference-targets" not in core + client, (
        "HS-143-12 regression: Model Library must not reopen the retired "
        "inference-target writer."
    )
    assert "/api/inference/model-library" in client, (
        "HS-143-12 regression: the one availability authority transport is missing."
    )




def test_the_real_concierge_address_well_is_not_blind() -> None:
    """Astra's in-memory check: opt the real address well out of its mic."""
    scanner = _load_scanner()
    path = Path(__file__).resolve().parents[2] / "web/src/features/concierge/ConciergeCore.tsx"
    content = path.read_text()
    rel = "features/concierge/ConciergeCore.tsx"
    assert scanner.scan_mic(rel, content, content.splitlines()) == []
    hole = content.replace('label="Server address"', 'label="Server address"\n              mic={false}', 1)
    assert len(scanner.scan_mic(rel, hole, hole.splitlines())) == 1


