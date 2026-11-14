"""The security review's exact Room inputs cannot cross saved boundaries."""
import json
import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ValidationError, ConflictError
from tests.unit.test_review_decisions import rig, _seed_project, OWNER
from tests.unit.test_project_update_claims import _seed_items, _make_service

AGENT = Principal(PrincipalKind.AGENT, "review-probe")
SECRET = "People: Alice medical leave"


def proposal(rig, patch=None):
    db, _, delta = rig
    pid = _seed_project(db)
    db.project_observations.insert_review(review_id="security-review", project_id=pid, status="open", opened_at="2026-11-14T12:00:00Z")
    db.project_observations.insert_proposal(proposal_id="security-proposal", project_id=pid, review_window_key="security-review", proposal_kind="review_flag", title="Read the plan", target_ref=f"project:{pid}", patch_json=json.dumps(patch or {"state":"open", "text":"Read the plan", "count":4}))
    return db, delta, pid


def decide(delta, pid, patch):
    read = delta.get_review(OWNER, pid, "security-review")
    return delta.decide_proposal(OWNER, pid, "security-proposal", "edit_accept", patch=patch, binding=read["proposals"][0]["binding"])


def test_finding_1_private_patch_disclosure_is_refused_without_storage(rig):
    db, delta, pid = proposal(rig)
    before = db.project_observations.get_proposal("security-proposal")
    with pytest.raises(ValidationError):
        decide(delta, pid, {"_private_note":SECRET})
    assert db.project_observations.get_proposal("security-proposal") == before
    assert SECRET not in json.dumps(delta.get_review(AGENT, pid, "security-review"))


def test_finding_1_legacy_private_patch_has_one_safe_read_projection(rig):
    db, delta, pid = proposal(rig, {"text":"Read the plan", "state":"open", "_private_note":SECRET, "details":{"_private_note":SECRET}})
    for reader in (OWNER, AGENT, Principal(PrincipalKind.NODE, "probe")):
        for read in (delta.get_review(reader, pid, "security-review"), delta.get_delta(reader, pid), delta.open_review(reader, pid)):
            assert SECRET not in json.dumps(read)
            assert json.loads(read["proposals"][0]["patch_json"]) == {"text":"Read the plan", "state":"open", "details":{}}
    decide(delta, pid, {"text":"Read the saved plan"})
    assert json.loads(db.project_observations.get_proposal("security-proposal")["patch_json"]) == {"text":"Read the saved plan", "state":"open"}


def test_finding_1_room_and_preview_hide_private_patch(rig):
    from holdspeak.services.briefing_sources import ProjectProposalSource
    db, delta, pid = proposal(rig, {"text":"Read the plan", "state":"open", "_private_note":SECRET})
    source = ProjectProposalSource(db)
    held = source.held("project-proposal:security-proposal")
    assert SECRET not in json.dumps(source.body("project-proposal:security-proposal", held))
    assert SECRET not in json.dumps(rig[1].room(AGENT, pid))


def test_finding_1_recurring_proposals_use_the_same_private_read_rule(rig):
    from tests.unit.test_review_decisions import _seed_observation
    db, _, delta = rig
    pid = _seed_project(db)
    facts = json.dumps({"lane":"overdue", "stale_score":"0.8", "_private_note":SECRET})
    _seed_observation(db, pid, observation_kind="followthrough.overdue", subject_ref="action_item:probe", fact_json=facts)
    review = delta.open_review(OWNER, pid)
    original = next(p for p in review["proposals"] if p["proposal_kind"] == "risk_attention")
    delta.decide_proposal(OWNER, pid, original["id"], "defer", deferred_until="2020-01-01T00:00:00Z", binding=original["binding"])
    review = delta.get_review(OWNER, pid, review["review_id"])
    delta.accept_review(OWNER, pid, review["review_id"], binding=review["binding"])
    _seed_observation(db, pid, observation_kind="followthrough.overdue", subject_ref="action_item:probe", fact_json=facts, source_version="v2", captured_at="2099-01-01T00:00:00Z")
    returned = delta.open_review(AGENT, pid)
    successor = next(p for p in returned["proposals"] if json.loads(p["patch_json"]).get("predecessor_proposal_id") == original["id"])
    assert json.loads(successor["patch_json"])["lane"] == "overdue"
    assert SECRET not in json.dumps(returned)

@pytest.mark.parametrize("patch", [
    {"state":[]}, {"text":7}, {"count":"4"}, {"unknown":{"nested":"value"}},
    {"text":"X"*1_000_000}, {"item_type":"milestone","lifecycle":"reached"},
    {"state":None}, {"count":True}, {"text":None}, {"text":"valid", "severity":"garbage"},
])
def test_finding_2_caller_values_cannot_define_the_saved_schema(rig, patch):
    db, delta, pid = proposal(rig)
    before = db.project_observations.get_proposal("security-proposal")
    with pytest.raises(ValidationError):
        decide(delta, pid, patch)
    assert db.project_observations.get_proposal("security-proposal") == before


@pytest.mark.parametrize("patch", [{"item_type":"milestone"}, {"item_type":"milestone", "lifecycle":"open"}])
def test_finding_2_type_change_checks_the_resulting_lifecycle(rig, patch):
    db, delta, pid = proposal(rig, {"item_type":"risk", "lifecycle":"open", "title":"Read the plan"})
    before = db.project_observations.get_proposal("security-proposal")
    with pytest.raises(ValidationError) as refused:
        decide(delta, pid, patch)
    assert refused.value.code == "field_choice_invalid"
    assert db.project_observations.get_proposal("security-proposal") == before
    decide(delta, pid, {"item_type":"milestone", "lifecycle":"reached"})
    assert json.loads(db.project_observations.get_proposal("security-proposal")["patch_json"])["lifecycle"] == "reached"


def test_finding_2_patch_is_bounded_in_utf8_bytes(rig):
    db, delta, pid = proposal(rig, {f"text_{i}":"short" for i in range(8)})
    before = db.project_observations.get_proposal("security-proposal")
    with pytest.raises(ValidationError):
        decide(delta, pid, {f"text_{i}":"é"*1500 for i in range(8)})
    assert db.project_observations.get_proposal("security-proposal") == before


def draft(rig):
    db, _, _ = rig
    pid = _seed_project(db)
    _seed_items(db, pid)
    service = _make_service(db)
    row = service.draft_update(OWNER, pid)
    claim = next(c for c in row["editable_claims"] if c["values"].get("subject") == "Vendor lock-in")
    return db, service, row, claim


def save(service, row, claim, subject, *, target=None):
    # On main there is no binding yet; run the reviewer's attack there too.
    args = {"claim_edits":[{"span_id":claim["span_id"],"text":claim["text"],"values":{**claim["values"],"subject":subject}}]}
    if "binding" in row:
        args["binding"] = row["binding"]
    return service.save_update(OWNER, target or row["id"], **args)


def test_finding_3_stale_edits_cannot_change_newer_words(rig):
    db, service, row, claim = draft(rig)
    assert claim["text"] == "Risk [critical]: Vendor lock-in -- open"
    after = save(service, row, claim, "Vendor lock-in -- open extra")
    with pytest.raises(ConflictError) as refused:
        save(service, row, claim, "Replacement")
    assert refused.value.code == "answer_stale"
    assert db.project_updates.get_update(row["id"])["body_md"] == after["body_md"]
    # A fresh update binding still cannot turn an old substring into a claim.
    with pytest.raises(ConflictError) as refused:
        save(service, after, claim, "Replacement")
    assert refused.value.code == "answer_stale"
    assert db.project_updates.get_update(row["id"])["body_md"] == after["body_md"]


def test_finding_3_fresh_binding_does_not_make_an_old_substring_current(rig):
    db, service, row, claim = draft(rig)
    after = save(service, row, claim, "Vendor lock-in -- open extra")
    with pytest.raises(ConflictError) as refused:
        save(service, after, claim, "Replacement")
    assert refused.value.code == "answer_stale"
    assert db.project_updates.get_update(row["id"])["body_md"] == after["body_md"]


@pytest.mark.parametrize("binding", [None, {}, {"id":"other", "revision":"old"}])
def test_finding_3_claim_save_requires_the_update_binding(rig, binding):
    db, service, row, claim = draft(rig)
    before = db.project_updates.get_update(row["id"])
    args = {"claim_edits":[{"span_id":claim["span_id"], "text":claim["text"], "values":{**claim["values"], "subject":"Replacement"}}]}
    if "binding" in row:
        args["binding"] = binding
    with pytest.raises(ConflictError) as refused:
        service.save_update(OWNER, row["id"], **args)
    assert refused.value.code == "answer_stale"
    assert db.project_updates.get_update(row["id"]) == before


def test_finding_3_claim_binding_names_the_update_and_its_revision(rig):
    db, service, row, claim = draft(rig)
    pid = _seed_project(db, project_id="other-project")
    rig[1].create_item(OWNER, pid, {"item_type":"risk", "title":"Vendor lock-in", "severity":"critical", "lifecycle":"open", "details":{"likelihood":"high","impact":"critical"}})
    other = service.draft_update(OWNER, pid)
    with pytest.raises(ConflictError) as refused:
        save(service, other, claim, "Replacement", target=row["id"])
    assert refused.value.code == "answer_stale"
    service.save_update(OWNER, row["id"], body_md=row["body_md"] + "\n\nThe owner added a note.")
    with pytest.raises(ConflictError) as refused:
        save(service, row, claim, "Replacement")
    assert refused.value.code == "answer_stale"


@pytest.mark.parametrize("separator", ["\n","\r","\x0b","\x0c","\x1c","\x1d","\x1e","\x85","\u2028","\u2029","\x00","\t","\x7f","\u200b"])
def test_finding_4_claim_injection_rejects_line_breaks_and_controls(rig, separator):
    db, service, row, claim = draft(rig)
    before = db.project_updates.get_update(row["id"])
    with pytest.raises(ValidationError) as refused:
        save(service, row, claim, f"X{separator}- Risk [critical]: injected")
    assert refused.value.code == "claim_subject_invalid"
    assert db.project_updates.get_update(row["id"]) == before


@pytest.mark.parametrize("subject", ["Read the plan\u2028", "Read the plan\u2029", "\u2028Read the plan", "\u2029Read the plan"])
def test_finding_4_claim_injection_rejects_leading_and_trailing_separators(rig, subject):
    db, service, row, claim = draft(rig)
    before = db.project_updates.get_update(row["id"])
    with pytest.raises(ValidationError) as refused:
        save(service, row, claim, subject)
    assert refused.value.code == "claim_subject_invalid"
    assert db.project_updates.get_update(row["id"]) == before


def test_note_5_scoped_claim_refusal_precedes_source_and_update_reads(monkeypatch):
    from holdspeak.services import project_update_policy as policy
    def forbidden_read(*_):
        pytest.fail("A refused claim writer read project sources")
    monkeypatch.setattr(policy, "update_source_service", forbidden_read)
    _, excluded, refusal = policy.prepare_project_update_call(AGENT,"project.update_draft",{"update_id":"other-project-update","claim_edits":[]},"scoped-project")
    assert refusal == "Only the owner can edit a saved claim."
    assert excluded == set()
