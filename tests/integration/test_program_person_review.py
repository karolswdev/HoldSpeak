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


# ── HS-S25 (G25 branch A): the current review decides, not the remembered one ──

import pytest  # noqa: E402

from holdspeak.services.program_service import ProgramRefused  # noqa: E402


def _review(login: str, state: str, at: str, body: str = "") -> dict:
    """One member of gh's raw ``latestReviews``."""
    return {"author": {"login": login}, "state": state, "body": body, "submittedAt": at}


def _facts(rig, step) -> dict:
    """The step's stored facts (the program view does not show them)."""
    return rig.service.store.get_step(step["id"])["facts"]


def _merges(rig) -> list:
    return [call for call in rig.gh.calls if call[1:3] == ["pr", "merge"]]


def test_a_later_change_request_holds_the_merge_after_an_approval(tmp_path) -> None:
    """C25-04/05/07: Alice approves while his word holds the merge; then she
    asks for changes. His Met no longer merges: the change request holds the
    gate, also after the round and when the work returns to the same PR.
    Only her newer approval lets it merge. Fails on main: the old latch kept
    ``person_approved`` and stopped reading her reviews."""
    rig, pid = _alice(tmp_path)
    step = rig.step(pid, 1)
    number = step["pr"]["number"]
    review = next(row for row in step["requirements"] if row["kind"] == "review")
    rig.gh.prs[number]["latest_reviews"] = [_review("alice-gh", "APPROVED", "2026-11-01T09:00:00Z")]
    rig.tick(2)
    step = rig.step(pid, 1)
    assert step["state"] == "pr_open" and _facts(rig, step)["person_approved"] is True
    assert _facts(rig, step)["person_review"]["state"] == "approved"
    # She changes her mind before his word.
    rig.gh.prs[number]["latest_reviews"] = [
        _review("alice-gh", "CHANGES_REQUESTED", "2026-11-01T10:00:00Z", "Keep the headings as H2.")]
    rig.tick()
    step = rig.step(pid, 1)
    assert step["state"] == "working" and step["rounds"] == 1
    assert _facts(rig, step)["person_approved"] is True, "history is not rewritten"
    # The agent fixes it on the same branch; the PR is the same; her review is unchanged.
    rig.agent.finish(step["launch_id"], {"b.txt": "b2\n"})
    rig.tick(3)
    step = rig.step(pid, 1)
    assert step["state"] == "pr_open", step["state"]
    assert step["rounds"] == 1, "the same review is one round"
    assert _facts(rig, step)["person_review"]["state"] == "changes"
    rig.service.decide_requirement(OWNER, pid, review["id"], "met")
    rig.tick(2)
    assert rig.step(pid, 1)["state"] == "pr_open"
    assert _merges(rig) == []
    with pytest.raises(ProgramRefused) as refused:
        rig.service.decide(OWNER, pid, step["id"], kind="merge", choice="merge")
    assert refused.value.code == "person_review_missing"
    assert "Alice asked for changes" in str(refused.value)
    assert _merges(rig) == []
    # Another alias of hers approving does not override her change request.
    rig.gh.prs[number]["latest_reviews"] = [
        _review("alice-gh", "CHANGES_REQUESTED", "2026-11-01T10:00:00Z", "Keep the headings as H2."),
        _review("Alice Smith", "APPROVED", "2026-11-01T11:00:00Z")]
    rig.tick(2)
    assert rig.step(pid, 1)["state"] == "pr_open" and _merges(rig) == []
    # Her newer approval (gh shows only her latest review) lets it merge.
    rig.gh.prs[number]["latest_reviews"] = [_review("alice-gh", "APPROVED", "2026-11-01T12:00:00Z")]
    rig.tick(2)
    assert rig.step(pid, 1)["state"] in ("merged", "done")
    merges = _merges(rig)
    assert len(merges) == 1 and merges[0][3] == step["pr"]["url"], "the person merge names the PR by its URL"


def _secure_alice(tmp_path):
    rig = Rig(tmp_path, people=lambda: People())
    pid = rig.service.create(OWNER, title="For Alice", goal="Export the brief.", repository=str(rig.repo),
                             check_command=f"sh {FAKE_CHECK}", template="fast-cycle", control="secure",
                             for_person_id="p-alice")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Export the brief", "brief": "x", "gate_review": "person"}])
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"b.txt": "b\n"})
    rig.tick(2)
    step = rig.step(pid, 1)
    rig.gh.prs[step["pr"]["number"]]["latest_reviews"] = [_review("alice-gh", "APPROVED", "2026-11-01T09:00:00Z")]
    rig.tick(2)
    assert rig.step(pid, 1)["state"] == "merge_ask", rig.step(pid, 1)["state"]
    return rig, pid


def test_an_unreadable_review_withdraws_the_merge_question(tmp_path) -> None:
    """C25-08/12: the review read fails after her approval. Merge? goes back to
    PR open, his press is refused, nothing asks her again, and the report
    says the read failed, not that the review did not run."""
    rig, pid = _secure_alice(tmp_path)
    step = rig.step(pid, 1)
    assert [item["kind"] for item in rig.service.needs_you_items()] == ["merge"]
    rig.gh.read_state = "gh_failed"
    rig.tick()
    step = rig.step(pid, 1)
    assert step["state"] == "pr_open"
    assert _facts(rig, step)["person_review"] == {"state": "unverified", "reason": "read_unavailable",
                                              "number": step["pr"]["number"], "head": ""}
    assert _facts(rig, step)["person_approved"] is True
    assert any(row["line"].startswith("Merge withdrawn: HoldSpeak could not read the latest review")
               for row in rig.program(pid)["checkpoints"])
    assert rig.service.needs_you_items() == [], "no Merge and no automatic ask"
    with pytest.raises(ProgramRefused) as refused:
        rig.service.decide(OWNER, pid, step["id"], kind="merge", choice="merge")
    assert refused.value.code == "person_review_missing"
    assert _merges(rig) == []
    # The read works again: the Merge question comes back.
    rig.gh.read_state = "live"
    rig.tick()
    assert rig.step(pid, 1)["state"] == "merge_ask"


def test_a_requested_merge_is_never_dispatched_twice(tmp_path, monkeypatch) -> None:
    """C25-09/10: his press reaches the runner's own gate; gh accepts the
    request but the PR stays open (queued). A second press or a direct runner
    call issues no second command and no second success checkpoint."""
    rig, pid = _secure_alice(tmp_path)
    step = rig.step(pid, 1)
    number = step["pr"]["number"]
    real_call = rig.gh.__class__.__call__

    def queued(self, argv, cwd=None, **kwargs):
        if argv[1:3] == ["pr", "merge"]:
            self.calls.append(list(argv))
            return type("P", (), {"returncode": 0, "stdout": "queued", "stderr": ""})()
        return real_call(self, argv, cwd, **kwargs)

    monkeypatch.setattr(rig.gh.__class__, "__call__", queued)
    rig.service.decide(OWNER, pid, step["id"], kind="merge", choice="merge")
    assert len(_merges(rig)) == 1 and _merges(rig)[0][3] == rig.gh.prs[number]["url"]
    step = rig.step(pid, 1)
    assert _facts(rig, step).get("merge_requested_at")
    with pytest.raises(ProgramRefused) as refused:
        rig.service.decide(OWNER, pid, step["id"], kind="merge", choice="merge")
    assert refused.value.code in ("merge_requested", "not_mergeable")
    with pytest.raises(ProgramRefused) as direct:
        rig.service.runner().merge(rig.service.store.get_program(pid), rig.service.store.get_step(step["id"]), by="owner")
    assert direct.value.code == "merge_requested"
    rig.tick(2)
    assert len(_merges(rig)) == 1
    lines = [row["line"] for row in rig.program(pid)["checkpoints"]]
    assert sum(line.startswith(f"Merged PR #{number}") for line in lines) == 1


def test_a_remembered_approval_without_a_current_read_does_not_merge(tmp_path) -> None:
    """C25-08: legacy ``person_approved`` with no review observation on the
    launch: the runner's own gate refuses a direct merge; no gh merge runs."""
    rig, pid = _alice(tmp_path)
    step = rig.service.store.get_step(rig.step(pid, 1)["id"])
    step["facts"] = {**(step.get("facts") or {}), "person_approved": True}
    rig.service.save_step(step)
    record = rig.ledger.get(step["launch_id"])
    follow = {key: value for key, value in (record.get("follow_through") or {}).items() if key != "review"}
    rig.ledger.update(step["launch_id"], follow_through=follow)
    runner = rig.service.runner()
    review = runner.person_review(rig.service.store.get_program(pid), step)
    assert (review["state"], review["reason"], review["eligible"]) == ("unverified", "not_observed", False)
    with pytest.raises(ProgramRefused) as refused:
        runner.merge(rig.service.store.get_program(pid), step, by="engine")
    assert refused.value.code == "person_review_missing"
    assert _merges(rig) == []


def test_a_step_without_a_person_gate_merges_by_number_as_before(tmp_path) -> None:
    """C25-13: the non-person path is unchanged (its command names the number)."""
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Plain", goal="x", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="fast-cycle", control="yolo")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "x"}])
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"c.txt": "c\n"})
    rig.tick(3)
    step = rig.step(pid, 1)
    assert step["state"] in ("merged", "done")
    assert _merges(rig)[0][3] == str(step["pr"]["number"])
    assert "person_review" not in (step.get("facts") or {})
