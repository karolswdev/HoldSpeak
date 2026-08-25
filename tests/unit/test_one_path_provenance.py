"""HS-131-10 §3 — child provenance, journal hygiene, and terminal immutability.

The census (``test_one_path_census.py``) proves there is only one door; the spine
(``test_one_path_spine.py``) proves every surface walks through it; the
cardinality harness (``test_one_path_cardinality.py``) proves the counts
reconcile. This module proves the remaining three properties of what the door
WROTE DOWN: that every admitted child carries real provenance, that no content
ever reaches a journal field, and that a terminal receipt is final even when a
blocked adapter comes back afterwards.

DESIGN-HS-131-10.md §3 is explicit that this suite must **extend** the kernel's
existing assertions rather than restate them. The existing coverage was mapped
before a line was written here, and the following criteria are DISCHARGED
ELSEWHERE and deliberately not repeated:

* claim/terminal/cancellation/reaper lifecycle — ``test_inference_kernel.py``
  (``test_reaper_terminalizes_claimed_inference_cancel_child``:185,
  ``test_hub_restart_projects_claimed_run_and_desk_state_as_unknown``:291).
* no-late-publication after cancellation — ``test_inference_runner.py``
  (``test_cancellation_reaches_adapter_and_blocks_late_publication``:159,
  ``test_canceller_wins_before_publisher_transition``:386,
  ``test_timeout_late_cancel_daemon_cannot_mutate_durable_closure_or_publish``
  :1205, which already re-reads its receipts byte-for-byte).
* identical-receipt replay equality and the ``receipt_immutable`` refusal on a
  CHANGED outcome — ``test_inference_runner.py::
  test_each_terminal_outcome_has_one_immutable_receipt``:63 and
  ``test_kernel_broker.py::test_claim_receipt_reconcile_and_cursor_projection``
  :268.
* content-key admission refusal (``journal_content_forbidden``) —
  ``test_inference_kernel.py::test_token_stream_is_refused_before_any_native_invocation``
  :100 and ``test_kernel_broker.py``:96.
* per-surface slices of child provenance — the dictation, meeting, sequence and
  workflow admission suites each assert their own subset.
* the runner's dispatch-context requirement, end to end —
  ``test_one_path_context.py`` (Stage A).

What is genuinely NEW here, and why each one is not already covered:

1. **One consolidated provenance row, across surfaces.** Every existing test
   asserts a SUBSET of the child's provenance. Nothing asserts causation,
   frozen revision, derived placement, authority basis, principal, envelope
   digest and terminal outcome TOGETHER on one row — which is what makes a
   missing field impossible to hide behind a sibling test.
2. **The ``inference.invoke`` codec's own placement/target refusal.**
   ``inference_invoke_prerequisite_failed`` and
   ``inference_deployment_revision_unknown`` (``kernel/inference_invoke.py``
   :69,94) had NO test at all. ``test_inference_kernel.py``:73 proves the
   forged-placement rule for ``inference.run``; the child codec is a different
   validator and was unproven.
3. **A value-side journal scan on the runner path.**
   ``holdspeak/kernel/model.py:forbidden_content`` is KEY-NAME based — it
   cannot see a token stream smuggled under an innocent key — and
   ``test_inference_runner.py``:376 only stringifies ``broker.events``, never
   the tables. This scans the real rows for all five forbidden bodies.
4. **The design's one sanctioned race fixture:** a blocked adapter that
   completes AFTER its operation was already terminalized by the liveness
   reaper (the restart/indeterminate shape, not the cancel shape), proving no
   publication and a byte-for-byte unchanged first receipt.
"""

from __future__ import annotations

import json
import threading
import time
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.deployment_revisions import resolve_deployment_revision
from holdspeak.kernel.inference_runner import InvocationRequest
from holdspeak.kernel.inference_shared import executor_identity
from holdspeak.kernel.model import KernelRefused
from holdspeak.principals import Principal, PrincipalKind

# The cardinality module already owns the store readers and the bare rig this
# story's assertions are written against. Importing them keeps ONE definition of
# "what an inference.invoke child row is" across the fence, instead of a fourth
# private copy that could drift away from the cohort the counts reconcile.
from tests.unit.test_one_path_cardinality import (
    _Adapter,
    _bare_request,
    _bare_rig,
    _bare_runner,
    _invoke_children,
    _operation,
    _receipt,
)

# The spine module already owns the fifteen REAL surface drivers, and each one
# now hands back the database it used, the principal it authenticated as, the
# parent it ran under, and the destination its plan froze (``SurfaceRun``).
# Importing them is what makes this suite's provenance row assertion executable
# for all fifteen named forms instead of a hand-picked three: the surfaces the
# spine proves reach the door are exactly the surfaces whose rows are read here.
from tests.unit.test_one_path_spine import (
    CHILD_SHAPED_SURFACES,
    ROOT_SHAPED_SURFACES,
    SURFACE_DRIVERS,
)

pytestmark = pytest.mark.timeout(90, method="signal")

OWNER = Principal(PrincipalKind.OWNER, "provenance-owner")

#: The basis the kernel stamps for an ordinary authenticated caller
#: (``kernel/broker.py``:98 and ``kernel/trusted_child.py``:79). Two surfaces
#: legitimately differ, and the test below demands the RIGHT one of the three
#: rather than merely a nonempty string:
#:   * Rails carries its own narrow ``Principal.authority_basis``;
#:   * the scheduler's basis names the live delegation it is acting under.
AUTHENTICATED_BASIS = (
    "authenticated_principal+declared_capability+hard_prerequisites+interruption_policy"
)


def _rows(db: Database, table: str) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [dict(row) for row in conn.execute(f"SELECT * FROM {table}").fetchall()]


# ===========================================================================
# 1. Cross-surface child provenance: every fact, on one row, at once
# ===========================================================================


def _parent_run_kind(db: Database, operation_id: str) -> str | None:
    with db._connection() as conn:
        row = conn.execute(
            "SELECT kind FROM kernel_parent_runs WHERE operation_id=?", (operation_id,)
        ).fetchone()
    return None if row is None else row[0]


def _assert_expected_authority_basis(surface: str, child: dict[str, Any], run: Any) -> None:
    """The basis must be the RIGHT one for this surface's authenticated actor.

    Three legitimate shapes exist, and "nonempty" would accept a regression
    that collapsed them into one another — a scheduled run silently acquiring
    an owner's basis is precisely the failure this fence exists to catch.
    """
    basis = child["authority_basis"]
    assert basis, f"{surface}: child carries no authority basis"
    assert basis != "refused_at_admission", f"{surface}: child was never really admitted"
    if run.principal.authority_basis:
        # A principal that declares its own narrow basis keeps it verbatim.
        assert basis == run.principal.authority_basis
    elif run.principal.kind is PrincipalKind.SCHEDULER:
        # A delegated run's basis names the live delegation and its exact terms.
        delegation_id, _, terms = basis.partition(":")[2].partition(":")
        assert basis.startswith("schedule-delegation:"), basis
        assert delegation_id and terms, f"{surface}: delegation basis is unbound: {basis}"
    else:
        assert basis == AUTHENTICATED_BASIS, f"{surface}: {basis}"


@pytest.mark.parametrize("surface", sorted(SURFACE_DRIVERS), ids=sorted(SURFACE_DRIVERS))
def test_every_child_carries_causation_revision_placement_and_basis(
    surface, tmp_path, monkeypatch
) -> None:
    """EVERY provenance fact, on EVERY child row, for all FIFTEEN surfaces.

    Charter AC: "Every invocation child has causation, deployment revision, and
    authority basis; no caller-supplied placement or owner principal survives
    validation." Asserting the facts TOGETHER is what makes an omission visible
    — a per-surface subset test cannot tell the difference between "this field
    is absent" and "some other test covers it". Asserting them across all
    fifteen named entry forms is what stops a single unmigrated surface from
    hiding behind the twelve that were checked.

    Each surface runs its real driver from ``test_one_path_spine.py``: the same
    production admission path the spine test traces, so the rows read back here
    are the rows that path actually wrote. Nothing is asserted about test node
    ids or a comment map; every fact below comes from a stored
    ``kernel_operations`` / ``kernel_receipts`` row.
    """
    run = SURFACE_DRIVERS[surface](tmp_path, monkeypatch)
    db = run.db

    # Every child this exercise emitted -- read GLOBALLY, then reconciled against
    # the parent-scoped cohort. A surface that emits a child outside its own
    # parent scope would otherwise escape inspection entirely, and a parent or
    # session row can never stand in for one: the cohort is `inference.invoke`
    # rows only, by name.
    children = _invoke_children(db)
    assert children, f"{surface}: no admitted inference.invoke child was recorded"
    assert len(children) == run.expected_children, (
        f"{surface}: expected {run.expected_children} inference.invoke child(ren), "
        f"got {len(children)} -- every emitted child must be inspected"
    )
    if run.parent_operation_id is not None:
        scoped = _invoke_children(db, run.parent_operation_id)
        assert [row["operation_id"] for row in scoped] == [
            row["operation_id"] for row in children
        ], f"{surface}: a child was emitted outside its declared parent scope"

    for child in children:
        # --- causation: a real, live parent/session, not a placeholder --------
        assert child["correlation_id"], f"{surface}: child carries no correlation id"
        if surface in ROOT_SHAPED_SURFACES:
            # A root-shaped admission has no parent run; its causal thread is
            # its own correlation id. Declaring the shape (and cross-checking it
            # against the spine module's sets) is what stops a surface from
            # silently losing its parent and still passing.
            assert run.parent_operation_id is None
            assert not child["parent_operation_id"], (
                f"{surface}: declared root-shaped but ran under a parent"
            )
            assert child["correlation_id"] == child["operation_id"]
        else:
            assert surface in CHILD_SHAPED_SURFACES
            assert child["parent_operation_id"] == run.parent_operation_id
            parent = _operation(db, run.parent_operation_id)
            assert parent is not None, f"{surface}: the named parent does not exist"
            assert parent["name"] != "inference.invoke", (
                f"{surface}: a sibling invocation cannot serve as the parent"
            )
            assert _parent_run_kind(db, run.parent_operation_id) == run.parent_kind
            assert child["correlation_id"] in {
                parent["correlation_id"], parent["operation_id"],
            }, f"{surface}: child left its parent's causal thread"

        # --- the frozen deployment revision, resolvable and immutable ---------
        assert child["target_ref"].startswith("deployment-revision:"), child["target_ref"]
        revision_id = child["target_ref"].split(":", 1)[1]
        revision = resolve_deployment_revision(db, revision_id)
        assert revision is not None, f"{surface}: child names a revision that does not resolve"
        # It came from the surface's own frozen plan, not from anything a caller
        # said at dispatch time.
        assert revision.destination_id == run.destination_id, (
            f"{surface}: child ran against {revision.destination_id!r}, "
            f"not the planned {run.destination_id!r}"
        )

        # --- placement is DERIVED by the kernel from that frozen revision -----
        assert child["placement"] == f"node:{executor_identity(revision.destination_id)}"

        # --- an authenticated authority basis and the REAL principal ----------
        _assert_expected_authority_basis(surface, child, run)
        assert child["principal_kind"] == run.principal.kind.value
        assert child["principal_identity"] == run.principal.identity

        # --- a warrant bound to THIS operation, revision, and placement -------
        # A signature alone proves nothing if the warrant could have been minted
        # for some other child; these bindings are what tie it to this row.
        warrant = json.loads(child["warrant_json"])
        assert warrant.get("signature"), f"{surface}: child warrant is unsigned"
        assert not child["warrant_revoked"]
        assert warrant["operation_id"] == child["operation_id"]
        assert warrant["target_binding"] == child["target_ref"]
        assert warrant["placement"] == child["placement"]

        # --- content-free envelope digest + exactly one terminal outcome ------
        assert child["envelope_sha256"]
        assert child["envelope_sha256"] == warrant["envelope_sha256"]
        receipt = _receipt(db, child["operation_id"])
        assert receipt is not None, f"{surface}: child has no terminal receipt"
        assert child["state"] == receipt["state"]
        # These fifteen fixtures are all the SUCCESS path; the refusal, failure,
        # cancellation, retry and indeterminate cohorts are proven per-scenario
        # in ``test_one_path_cardinality.py``. Pinning the outcome here keeps a
        # surface from degrading into a quietly-failed dispatch that still has a
        # perfectly well-formed receipt.
        assert receipt["state"] == "succeeded", (
            f"{surface}: child terminalized as {receipt['state']}/{receipt['outcome']}"
        )


@pytest.mark.parametrize("surface", ("manual Workbench", "voice"))
def test_adopted_workbench_family_children_link_parent_route_operation_and_receipt(
    surface: str, tmp_path, monkeypatch
) -> None:
    """The Slice-3 callers retain one frozen route through the Runner receipt."""
    run = SURFACE_DRIVERS[surface](tmp_path, monkeypatch)
    children = _invoke_children(run.db, run.parent_operation_id)
    assert children
    for child in children:
        with run.db._connection() as conn:
            row = conn.execute(
                """SELECT attempt.child_operation_id,attempt.child_receipt_sha256,
                          execution.route_plan_id execution_route_id,
                          operation.route_plan_id operation_route_id,
                          member.route_plan_id parent_route_id
                     FROM inference_route_attempts attempt
                     JOIN inference_route_executions execution ON execution.id=attempt.execution_id
                     JOIN inference_operation_route_request_plans operation ON operation.id=execution.operation_plan_id
                     JOIN inference_parent_route_bundles bundle ON bundle.parent_operation_id=?
                     JOIN inference_parent_route_bundle_members member ON member.bundle_id=bundle.id
                    WHERE attempt.child_operation_id=?""",
                (run.parent_operation_id, child["operation_id"]),
            ).fetchone()
        assert row is not None, f"{surface}: child is missing frozen route evidence"
        assert row["child_operation_id"] == child["operation_id"]
        assert row["child_receipt_sha256"]
        assert row["parent_route_id"] == row["operation_route_id"] == row["execution_route_id"]


def test_the_provenance_matrix_covers_every_named_surface() -> None:
    """The parametrization above is the whole fence, not a sample of it.

    DESIGN-HS-131-10.md §2 and Sol's open-question ruling 3 require all FIFTEEN
    named entry forms. This is the guard against the matrix quietly shrinking
    back to a convenient subset.
    """
    assert len(SURFACE_DRIVERS) == 16
    assert ROOT_SHAPED_SURFACES | CHILD_SHAPED_SURFACES == set(SURFACE_DRIVERS)
    assert set(SURFACE_DRIVERS) == {
        "Ask", "Recipe run", "Recipe chat", "Sequence", "Workflow",
        "manual Workbench", "scheduled Workbench", "memory writeback", "Rails",
        "Decision promotion", "Delivery review", "voice", "meeting live",
        "meeting deferred", "dictation pipeline",
        # HS-131-13's migration; the story's other two families were deleted as
        # duplicates of "Decision promotion" and "Delivery review" above.
        "cadence next action",
    }


# ===========================================================================
# 2. No caller-supplied placement, target, or envelope field survives
# ===========================================================================


def _assert_refused_without_executing(
    db: Database, refused: dict[str, Any], reason: str, forged: str = ""
) -> None:
    """A refused admission is JOURNALLED (honestly) but never executed.

    The kernel records the refused attempt as an ``inference.invoke`` row with
    ``authority_basis='refused_at_admission'`` — that is the audit trail working,
    not a leak. What must be true is that the attempt never became runnable and
    that nothing the caller asserted was stored as fact.
    """
    assert refused["state"] == "refused"
    assert refused["receipt"]["outcome"] == reason
    row = _operation(db, refused["operation_id"])
    assert row is not None
    assert row["state"] == "refused"
    assert row["authority_basis"] == "refused_at_admission"
    assert row["claimed_by"] is None, "a refused attempt was claimable"
    # The forged value never became stored fact.
    if forged:
        assert forged not in (row["placement"], row["target_ref"])
    # No child ever reached a live, executable state.
    assert [child for child in _invoke_children(db) if child["state"] != "refused"] == []


def _invoke_envelope(revision_id: str, **overrides: Any) -> dict[str, Any]:
    """A well-formed raw ``inference.invoke`` envelope, before any forgery."""
    invocation_id = "forge_" + str(int(time.time() * 1_000_000))
    envelope: dict[str, Any] = {
        "request_schema": 1,
        "request_id": "request_" + invocation_id,
        "idempotency_key": invocation_id,
        "operation": {"name": "inference.invoke", "version": 1},
        "target": {},
        "arguments": {
            "invocation_id": invocation_id,
            "deployment_revision": revision_id,
            "definition_origin": {
                "kind": "service", "contract": "provenance-probe", "revision": "v1",
                "payload_hash": "sha256:" + "0" * 64,
            },
            "deadline_at": time.time() + 30,
            "attempt_ordinal": 1,
        },
    }
    envelope.update(overrides)
    return envelope


FORGERIES: tuple[tuple[str, dict[str, Any], str], ...] = (
    (
        "placement",
        {"placement": "node:client-chose-this"},
        "inference_invoke_prerequisite_failed",
    ),
    (
        "target ref",
        {"target": {"ref": "profile:somewhere-else"}},
        "inference_invoke_prerequisite_failed",
    ),
)


@pytest.mark.parametrize("what,override,reason", FORGERIES, ids=[f[0] for f in FORGERIES])
def test_a_caller_cannot_choose_where_its_child_runs(what, override, reason, tmp_path) -> None:
    """The child codec refuses a client-set placement or target BY NAME.

    ``test_inference_kernel.py``:73 proves this rule for ``inference.run``.
    ``inference.invoke`` is validated by a DIFFERENT codec
    (``kernel/inference_invoke.py``:69) whose refusal had no test at all — so
    until now the one path's OWN envelope was the unproven one.
    """
    db, broker, revision = _bare_rig(tmp_path)

    refused = broker.submit(_invoke_envelope(revision.id, **override), OWNER)

    forged = str(override.get("placement") or (override.get("target") or {}).get("ref") or "")
    _assert_refused_without_executing(db, refused, reason, forged=forged)


def test_an_extra_envelope_argument_is_refused_rather_than_ignored(tmp_path) -> None:
    """The argument set is exact (``set(args) != _INVOKE_FIELDS``).

    A silently-ignored extra field is how a caller smuggles intent past a codec.
    """
    db, broker, revision = _bare_rig(tmp_path)
    envelope = _invoke_envelope(revision.id)
    envelope["arguments"]["owner_principal"] = "owner:someone-else"

    refused = broker.submit(envelope, OWNER)

    _assert_refused_without_executing(db, refused, "inference_invoke_prerequisite_failed")
    # The smuggled owner never became the operation's principal.
    assert _operation(db, refused["operation_id"])["principal_identity"] != "owner:someone-else"


def test_a_revision_the_kernel_cannot_resolve_is_refused(tmp_path) -> None:
    """``inference_deployment_revision_unknown`` — also previously untested.

    Placement is derived FROM the revision, so an unresolvable revision must
    refuse rather than fall back to any default node.
    """
    db, broker, _revision = _bare_rig(tmp_path)

    refused = broker.submit(_invoke_envelope("rev_does_not_exist"), OWNER)

    _assert_refused_without_executing(db, refused, "inference_deployment_revision_unknown")
    assert not _operation(db, refused["operation_id"])["placement"]


def test_the_kernel_derives_the_placement_the_caller_was_forbidden_to_set(tmp_path) -> None:
    """The positive control for the two refusals above.

    Same envelope, no forgery: the operation is admitted and the kernel fills in
    placement and target itself, from the frozen revision.
    """
    db, broker, revision = _bare_rig(tmp_path)

    submitted = broker.submit(_invoke_envelope(revision.id), OWNER)

    assert submitted["state"] != "refused"
    row = _operation(db, submitted["operation_id"])
    assert row is not None
    assert row["placement"] == f"node:{executor_identity(revision.destination_id)}"
    assert row["target_ref"] == f"deployment-revision:{revision.id}"


# ===========================================================================
# 3. Journal hygiene — the VALUE side, on the real tables
# ===========================================================================

PROMPT_SENTINEL = "PINEAPPLEQUARTERLYSECRET"
TOKEN_SENTINEL = "ELDERBERRYTOKENSTREAMCHUNK"
TRANSCRIPT_SENTINEL = "MULBERRYTRANSCRIPTBODY"
DICTATION_SENTINEL = "PERSIMMONDICTATEDTEXT"
AUDIO_SENTINEL = 0.4242424

#: Every table the kernel journals into. ``kernel_projection_stages`` is
#: included deliberately: the staged projection legitimately carries the
#: provider's OUTPUT, so the fixture below keeps the output distinct from every
#: sentinel — which means a sentinel appearing there is a real leak, not a
#: false positive.
JOURNAL_TABLES = (
    "kernel_operations",
    "kernel_receipts",
    "kernel_journal",
    "kernel_projection_stages",
    "kernel_parent_runs",
)


def test_no_prompt_token_transcript_dictation_or_audio_reaches_a_journal_field(tmp_path) -> None:
    """All five forbidden bodies, carried as VALUES, on the runner path.

    ``holdspeak/kernel/model.py:forbidden_content`` only inspects argument KEY
    names, so a caller that names its field ``source_text`` rather than
    ``tokens`` sails through admission. That is by design — the kernel's real
    defence is that it journals a DIGEST of the payload and never the payload —
    but nothing tested it on the runner path against the actual tables
    (``test_inference_runner.py``:376 stringifies ``broker.events`` only).

    The provider's output is deliberately sentinel-free, so this holds
    ``kernel_projection_stages`` to the same standard as the journal proper.
    """
    db, broker, revision = _bare_rig(tmp_path)
    runner = _bare_runner(broker, db)

    payload = {
        "system_prompt": PROMPT_SENTINEL,
        "user_prompt": f"{PROMPT_SENTINEL} / {DICTATION_SENTINEL}",
        "source_text": TRANSCRIPT_SENTINEL,
        "stream_echo": [TOKEN_SENTINEL, TOKEN_SENTINEL],
        "frames": [AUDIO_SENTINEL, AUDIO_SENTINEL, AUDIO_SENTINEL],
    }
    request = InvocationRequest(**{
        **_bare_request(revision).__dict__,
        "payload": payload,
        "invocation_id": "provenance_hygiene",
    })
    from holdspeak.kernel.inference_runner import ServiceContract

    request = InvocationRequest(**{
        **request.__dict__,
        "definition_origin": ServiceContract.for_payload("provenance-probe", "v1", payload),
    })

    outcome = runner.invoke(request, _Adapter(result="clean provider output"))
    assert outcome.outcome == "succeeded"
    assert _invoke_children(db), "nothing was journalled, so this proves nothing"

    text_sentinels = (
        PROMPT_SENTINEL, TOKEN_SENTINEL, TRANSCRIPT_SENTINEL, DICTATION_SENTINEL,
    )
    audio_bytes = str(AUDIO_SENTINEL).encode("utf-8")
    for table in JOURNAL_TABLES:
        for row in _rows(db, table):
            blob = "|".join(str(value) for value in row.values())
            for sentinel in text_sentinels:
                assert sentinel not in blob, f"{sentinel} leaked into {table}: {row}"
            assert audio_bytes not in blob.encode("utf-8", "replace"), f"audio leaked into {table}"

    # The event stream the desk reads is the same story.
    rendered = str(broker.events(0, {}, OWNER)["events"])
    for sentinel in text_sentinels:
        assert sentinel not in rendered

    # ...and the payload really WAS carried (otherwise the scan is vacuous):
    # its digest is bound into the child's envelope hash.
    assert _invoke_children(db)[0]["envelope_sha256"]


# ===========================================================================
# 4. The one sanctioned race: a reaped child whose adapter returns late
# ===========================================================================


def test_a_reaped_child_whose_adapter_returns_late_publishes_nothing(tmp_path) -> None:
    """The restart/indeterminate shape of the late-completion race.

    DESIGN-HS-131-10.md §3 sanctions exactly ONE new race fixture: "completes a
    blocked adapter after cancellation/restart and proves no projection/publish
    occurs and the first terminal receipt is unchanged". The CANCELLATION half
    of that shape is already proven at ``test_inference_runner.py``:159/:1205;
    the RESTART half — a child terminalized by the liveness reaper (exactly what
    a hub restart leaves behind) while its adapter is still blocked — was not
    covered for an ``inference.invoke`` child with a real publisher attached.

    Materialization is a landmine: if the late result ever became a domain
    write, this fails loudly rather than by a missing assertion.
    """
    db, broker, revision = _bare_rig(tmp_path)
    materialized: list[Any] = []
    broker.projection_stager.register(
        "provenance-late", lambda projection, permit: materialized.append(projection)
    )

    started, release = threading.Event(), threading.Event()

    class _Blocked(_Adapter):
        def dispatch(self, engine: Any, payload: Any, cancellation: Any) -> Any:
            started.set()
            assert release.wait(5), "release was never set"
            return "late output that must never publish"

    runner = _bare_runner(broker, db)
    invocation_id = "provenance_reaped"
    publisher = broker.projection_stager.publisher(
        invocation_id, "provenance-late", lambda output: {"text": str(output)}
    )
    results: list[Any] = []
    errors: list[BaseException] = []

    def _run() -> None:
        try:
            results.append(
                runner.invoke(
                    InvocationRequest(**{
                        **_bare_request(revision).__dict__, "invocation_id": invocation_id,
                    }),
                    _Blocked(),
                    publish=publisher,
                )
            )
        except BaseException as exc:  # the closure may legitimately fail loudly
            errors.append(exc)

    worker = threading.Thread(target=_run)
    worker.start()
    assert started.wait(5), "dispatch never started"

    # The hub "restarts": liveness expires while the adapter is still blocked,
    # and the reaper writes the child's ONE terminal receipt.
    child = _invoke_children(db)[0]
    broker._clock = lambda: time.time() + 3601
    reaped = broker.reap_expired()["reaped"]
    assert any(entry["operation_id"] == child["operation_id"] for entry in reaped), reaped
    first_receipt = _receipt(db, child["operation_id"])
    assert first_receipt is not None and first_receipt["state"] == "indeterminate"

    # Only NOW does the provider come back.
    release.set()
    worker.join(5)
    assert not worker.is_alive()

    # No domain result was ever materialized from the late output...
    assert materialized == []
    stage = broker.projection_stager.get(invocation_id)
    assert stage is None or stage.state != "PUBLISHED", stage

    # ...and the first terminal receipt is unchanged, byte for byte.
    assert _receipt(db, child["operation_id"]) == first_receipt

    # A second, DIFFERENT terminal for the same child refuses by name.
    node = Principal(PrincipalKind.NODE, executor_identity(revision.destination_id))
    with pytest.raises(KernelRefused) as second:
        broker.receipt(child["operation_id"], "succeeded", "inference-result:late", node)
    assert second.value.reason == "receipt_immutable"
    assert _receipt(db, child["operation_id"]) == first_receipt

    # The journal's own hash chain still verifies after the whole race.
    assert broker.store.verify()["ok"] is True
