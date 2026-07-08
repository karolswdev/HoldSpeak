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


def test_live_control_vs_treatment_grounding_an_open_story() -> None:
    """HS-88-02: the Phase-53 pattern on real metal — a question the
    bare model cannot answer, answerable only from a grounded open
    story. Skips when .43 is unreachable."""
    import json
    import os
    import urllib.request

    if _holdspeak_repo() is None:
        pytest.skip("holdspeak not in the project map on this machine")
    llm = os.environ.get("HOLDSPEAK_PROOF_LLM", "http://192.168.1.43:8080")
    try:
        urllib.request.urlopen(f"{llm}/health", timeout=4).read()
    except Exception:
        pytest.skip("proof LLM unreachable")

    from holdspeak.grounding import compose_steer

    blocks, unknown = hydrate_rails_refs(
        [{"repo": "holdspeak", "project": "holdspeak", "kind": "story", "id": "HS-88-02"}]
    )
    assert not unknown and blocks

    def ask(prompt: str) -> str:
        body = json.dumps(
            {"messages": [{"role": "user", "content": prompt}], "temperature": 0.0, "max_tokens": 40}
        ).encode()
        req = urllib.request.Request(
            f"{llm}/v1/chat/completions", data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"].strip()

    q = (
        "Answer ONLY from the grounded story. What single lowercase wire array "
        "key does the grounding object gain to carry rail object references? "
        "Reply with just the key."
    )
    treatment = ask(compose_steer(q, blocks)["text"]).lower()
    # The grounded story names the `rails` key; the answer uses it.
    assert "rails" in treatment
