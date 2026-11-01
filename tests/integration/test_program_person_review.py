"""JRN14 (PROGRAM-JOURNEYS J4; PROGRAM-LANGUAGE §13b): the person gate.

1. A step whose review is a person's has no agent reviewer: its Review
   requirements are his word at MERGE (a ``requirement_word`` row with Met /
   Unmet), and the merge waits for his Met as well as for her approval.
2. Her "changes requested" on GitHub goes to the builder as one round of
   REQUIRED findings on the same branch and PR (her words, once per review);
   her approval then lets it merge.
"""
from __future__ import annotations

from holdspeak.delivery.pr_receipts import _changes_requested
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig


class People:
    def display_names(self):
        return {"p-alice": "Alice"}

    def get_relationship(self, principal, person_id):
        return {"display_name": "Alice Smith", "owner_aliases": ["alice-gh"]}


def _alice(tmp_path):
    rig = Rig(tmp_path, people=lambda: People())
    pid = rig.service.create(OWNER, title="For Alice", goal="Export the 1:1 brief as Markdown.", repository=str(rig.repo),
                             check_command=f"sh {FAKE_CHECK}", template="fast-cycle", control="normal",
                             for_person_id="p-alice")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Export the brief", "brief": "x", "gate_review": "person"}])
    step = rig.step(pid, 1)
    rig.service.require(OWNER, pid, text="The change does what its action asks: the 1:1 brief exports as Markdown.",
                        kind="review", step_id=step["id"])
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"b.txt": "b\n"})
    rig.tick(2)
    return rig, pid


def test_a_person_gate_makes_the_review_requirement_his_word_at_merge(tmp_path) -> None:
    rig, pid = _alice(tmp_path)
    step = rig.step(pid, 1)
    assert step["state"] == "pr_open", step
    review = next(row for row in step["requirements"] if row["kind"] == "review")
    assert set(review["choices"]) >= {"met", "unmet"}
    items = [item for item in rig.program(pid)["your_turn_items"] if item["kind"] == "requirement_word"]
    assert [item["requirement_id"] for item in items] == [review["id"]]
    # Alice approves; the merge still waits for his Met.
    rig.gh.prs[step["pr"]["number"]]["approved_by"] = ["Alice-GH"]
    rig.tick(2)
    assert rig.step(pid, 1)["state"] == "pr_open"
    rig.service.decide_requirement(OWNER, pid, review["id"], "met")
    rig.tick(2)
    assert rig.step(pid, 1)["state"] in ("merged", "done")


def test_her_changes_requested_go_to_the_builder_as_one_round(tmp_path) -> None:
    rig, pid = _alice(tmp_path)
    step = rig.step(pid, 1)
    number = step["pr"]["number"]
    rig.gh.prs[number]["changes_requested"] = [
        {"login": "alice-gh", "body": "Keep the headings as H2; the export drops them.", "at": "2026-11-01T10:00:00Z"}]
    typed_before = len(rig.prompts)
    rig.tick()
    step = rig.step(pid, 1)
    assert step["state"] == "working", step["state"]
    assert [row["text"] for row in step["findings"]] == ["Keep the headings as H2; the export drops them."]
    assert step["rounds"] == 1
    assert any("Alice asked for changes on GitHub; round 1 goes back to the agent" == row["line"]
               for row in rig.program(pid)["checkpoints"])
    typed = rig.prompts[typed_before:]
    assert len(typed) == 1 and "Alice asked for changes on PR" in typed[0][1]
    assert "Keep the headings as H2" in typed[0][1]
    # The same review is one round, not one per tick.
    rig.tick()
    assert rig.step(pid, 1)["rounds"] == 1


def test_the_receipt_reads_who_asked_for_changes_and_their_words() -> None:
    # gh pr list --json latestReviews: {author: {login}, body, state, submittedAt}.
    reviews = [
        {"author": {"login": "alice-gh"}, "body": "Keep the headings.", "state": "CHANGES_REQUESTED",
         "submittedAt": "2026-11-01T10:00:00Z"},
        {"author": {"login": "bob"}, "body": "", "state": "APPROVED", "submittedAt": "2026-11-01T09:00:00Z"},
    ]
    assert _changes_requested(reviews) == [{"login": "alice-gh", "body": "Keep the headings.", "at": "2026-11-01T10:00:00Z"}]
    assert _changes_requested(None) == []
