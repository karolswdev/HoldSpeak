"""Live rails grounding (HS-88-01) — real `dw context`, this repo.

Grounds a real open story and the roadmap README through the actual
`dw` CLI and the operator's project map, proving the receipt path end
to end: `dw context` names the file, the hydration reads it, the block
carries provenance. Skips honestly when the map has no rails repo or
`dw` is absent.
"""

from __future__ import annotations

import shutil

import pytest

from holdspeak import missioncontrol_bridge as mc
from holdspeak.grounding_rails import hydrate_rails_refs

pytestmark = pytest.mark.skipif(
    shutil.which("dw") is None
    and not (mc.load_project_map().get("projects")),
    reason="no dw CLI / no rails repo in the project map",
)


def _holdspeak_repo() -> str | None:
    return mc.load_project_map().get("projects", {}).get("holdspeak")


def test_live_story_and_roadmap_ground_as_receipts() -> None:
    if _holdspeak_repo() is None:
        pytest.skip("holdspeak not in the project map on this machine")
    blocks, unknown = hydrate_rails_refs(
        [
            {"repo": "holdspeak", "project": "holdspeak", "kind": "story", "id": "HS-88-01"},
            {"repo": "holdspeak", "project": "holdspeak", "kind": "roadmap", "id": "holdspeak"},
        ]
    )
    assert unknown == [], unknown
    kinds = {b.kind for b in blocks}
    assert kinds == {"rails:story", "rails:roadmap"}
    story = next(b for b in blocks if b.kind == "rails:story")
    # The receipt: the block IS the story file's real contents.
    assert "Rails objects as grounding kinds" in story.text
    assert story.subtitle == "holdspeak/holdspeak"


def test_live_unknown_story_refuses_by_name() -> None:
    if _holdspeak_repo() is None:
        pytest.skip("holdspeak not in the project map on this machine")
    _blocks, unknown = hydrate_rails_refs(
        [{"repo": "holdspeak", "project": "holdspeak", "kind": "story", "id": "HS-404-04"}]
    )
    assert unknown == ["story:HS-404-04"]
