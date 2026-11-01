"""The live audit proof (2026-11-01): the fix Program's Codex reviewer could
not start ("Codex will not run the HoldSpeak hooks. Press Install hooks on
the Agents card."). That MUST went back to the builder every tick (the
builder cannot fix a desk setting): 30 "Round 1" lines and a builder prompted
each tick. Now the step parks once with the words; it is his row."""
from __future__ import annotations

from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig

WORDS = "Codex will not run the HoldSpeak hooks. Press Install hooks on the Agents card."


def test_a_reviewer_that_cannot_start_parks_the_step_once_with_its_words(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)

    def cannot(*_args, **_kwargs):
        raise RuntimeError(WORDS)

    monkeypatch.setattr(rig.review, "_start_reviewer", cannot)
    pid = rig.service.create(OWNER, title="Fix", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="build-and-review", control="yolo", reviewer_profile="codex-default")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Fix the README", "brief": "Fix it."}])
    rig.service.start(OWNER, pid)
    rig.tick()
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"README.md": "# app\nfixed\n"})
    rig.tick(6)
    step = rig.step(pid, 1)
    assert step["state"] == "parked" and step["parked_reason"] == f"Reviewer could not start: {WORDS}", step
    lines = [row["line"] for row in rig.service.store.list_checkpoints(pid)]
    assert not [line for line in lines if "the REQUIRED findings go back to the builder" in line], lines
    assert lines.count(f"Parked: Reviewer could not start: {WORDS}") == 1
    assert not [prompt for prompt in rig.prompts if "Fix the MUST findings" in prompt[1]]
    [row] = [item for item in rig.program(pid)["your_turn_items"] if item["kind"] == "parked"]
    assert WORDS in row["title"] or "could not start" in row["title"].lower()
