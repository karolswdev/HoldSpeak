"""HS-200-17 (phase200_recipe_catalog): one REAL manual run per recipe.

The unit half (``tests/unit/test_phase200_recipe_catalog.py``) proves the
descriptors and the compiler.  This half proves the binding is not
decorative: for each of the three recipes the plan is compiled, its bound
refs are resolved through :func:`recipe_catalog.resolve_step`, and the
resolved function is CALLED on a real :class:`~holdspeak.db.Database` with
a real Project — producing the real record the descriptor's ``output``
sentence promises.

Nothing is stubbed on the service side.  The two model-capable recipes run
their ``deterministic`` generator so no request leaves the machine; the
descriptors declare that as the route policy, and the run proves it by
composing no broker at all.

The MCP family and the HTTP route are exercised against the same database
through the one composition root, so discoverability is proven on the wire
rather than by reading the source.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition
from holdspeak.services import recipe_catalog as catalog
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.preparation_brief_service import PreparationBriefService
from holdspeak.services.project_delta_service import ProjectDeltaService
from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
from holdspeak.services.project_service import ProjectService
from holdspeak.services.project_update_service import ProjectUpdateService

OWNER = Principal(PrincipalKind.OWNER, "recipe-catalog-test")
NOW = datetime(2026, 9, 18, 9, 0, tzinfo=timezone.utc)
NOW_ISO = "2026-09-18T09:00:00"
PROJECT_ID = "proj_catalog_01"


# ── the rig: a real database, a real Project, real sources ──────────────


@pytest.fixture
def db(tmp_path: Path):
    reset_database()
    database = Database(tmp_path / "recipe_catalog.db")
    _seed(database)
    yield database
    database.close()
    reset_database()


def _seed(db: Database) -> None:
    """One Project with a linked meeting, a decision, a commitment, and a
    Watch that has actually been read once."""
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO projects
               (id, name, description, keywords_json, team_members_json,
                context_json, detection_threshold, revision, created_at, updated_at)
               VALUES (?, 'Cut-over platform', '', '[]', '[]', '{}', 0.4, 3, ?, ?)""",
            (PROJECT_ID, NOW_ISO, NOW_ISO),
        )
        # ``last_success_at`` is written with SQLite's own ``datetime('now')``
        # -- naive UTC -- because that is the ONLY shape production writes
        # (db/automations.py:168 and watch_service.py:875 are the two
        # writers, and both use it). A fixture that invents another shape
        # makes the producer look broken when it is not.
        conn.execute(
            """INSERT INTO connector_watches
               (id, connector_id, query_kind, name, query_json, snapshot_json,
                enabled, last_success_at, project_id, state, created_at, updated_at)
               VALUES ('watch_gh_01', 'gh', 'pull_requests', 'watch_gh_01', ?, ?,
                       1, datetime('now'), ?, '', ?, ?)""",
            (
                json.dumps({"repository": "karolswdev/HoldSpeak"}),
                json.dumps({"entities": {"pr_1": {"state": "open", "title": "Runbook"}}}),
                PROJECT_ID, NOW_ISO, NOW_ISO,
            ),
        )
        conn.execute(
            "INSERT INTO meetings (id, title, started_at, ended_at, created_at)"
            " VALUES ('mtg_catalog_01', 'Cut-over sync', ?, ?, ?)",
            (NOW_ISO, NOW_ISO, NOW_ISO),
        )
        conn.execute(
            "INSERT INTO meeting_projects (meeting_id, project_id) VALUES (?, ?)",
            ("mtg_catalog_01", PROJECT_ID),
        )
        conn.execute(
            """INSERT INTO decision_records
               (id, decision_text, lifecycle, source_type, source_id, created_at, updated_at)
               VALUES ('decrec_catalog_01', 'Cut over on the read replica first',
                       'active', 'meeting', 'mtg_catalog_01', ?, ?)""",
            (NOW_ISO, NOW_ISO),
        )
        conn.execute(
            """INSERT INTO action_items
               (id, meeting_id, task, owner, due, status, created_at)
               VALUES ('act_catalog_01', 'mtg_catalog_01', 'Write the rollback note',
                       'karol', '2026-09-25', 'pending', ?)""",
            (NOW_ISO,),
        )
        # Real Project items: what the Update Factory's deterministic drafter
        # composes its claims from.
        for item_id, item_type, title, lifecycle, severity, due_at, sort_key in (
            ("pitem_catalog_0001", "milestone", "Cut over the read replica",
             "planned", "high", "2026-10-01", 1.0),
            ("pitem_catalog_0002", "risk", "Rollback window is untested",
             "open", "critical", None, 2.0),
        ):
            conn.execute(
                """INSERT INTO project_items
                   (id, project_id, item_type, title, lifecycle, severity,
                    due_at, sort_key, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (item_id, PROJECT_ID, item_type, title, lifecycle, severity,
                 due_at, sort_key, NOW_ISO, NOW_ISO),
            )


def _briefs(db: Database) -> PreparationBriefService:
    return PreparationBriefService(
        db, project_service=ProjectService(db), clock=lambda: NOW
    )


def _updates(db: Database) -> ProjectUpdateService:
    collector = ProjectEvidenceCollector(db)
    delta = ProjectDeltaService(db, collector)
    return ProjectUpdateService(
        db, project_service=ProjectService(db, delta_service=delta),
        delta_service=delta,
    )


def _plan(db: Database, recipe_id: str, **inputs: Any) -> catalog.CompiledPlan:
    """Compile against the REAL observed coverage of the seeded Project."""
    payload: dict[str, Any] = {"project_id": PROJECT_ID}
    payload.update(inputs)
    return catalog.compile_recipe(
        recipe_id,
        version=catalog.get_descriptor(recipe_id).version,
        trigger=catalog.TRIGGER_MANUAL,
        inputs=payload,
        coverage=catalog.observed_coverage(ProjectService(db), OWNER, PROJECT_ID),
    )


# ── the coverage the compiler reads is the coverage that is there ───────


class TestObservedCoverageEqualsTheProducer:
    """Ruling R17-9: the catalog must not re-derive a C4 state.

    Every case below mints its condition through the REAL chain -- rows in
    the shipped tables, read through the REAL ``ProjectService.room``
    projection, mapped by the REAL ``needs_you_aggregate.room_coverage``
    producer -- and then asserts the catalog's answer EQUALS the producer's.
    No hand-written expected state appears on the left of an assertion
    except where the producer's own constant is imported to name it.

    This replaces a fence that asserted the catalog's divergent mapping and
    so proved nothing (``reference_lying_test_doubles``). The three
    conditions it never covered -- ``cant_check``, never-read, and aged past
    the stale horizon -- are each covered here.
    """

    def _producer_states(self, db: Database, project_id: str, now=None) -> dict:
        """Reduce the producer's own rows the way the catalog must."""
        from holdspeak.services.needs_you_aggregate import room_coverage

        room = ProjectService(db).room(OWNER, project_id)
        rows = room_coverage(room, project_id, str(room.get("name") or ""), now=now)
        out: dict[str, str] = {}
        for row in rows:
            kind = str(row["kind"])
            out.setdefault(kind, [])  # type: ignore[arg-type]
            out[kind] = catalog.worst_state(  # type: ignore[assignment]
                [str(r["state"]) for r in rows if r.get("kind") == kind]
            )
        return out

    def _assert_agrees(self, db: Database, project_id: str = PROJECT_ID) -> dict:
        observed = catalog.observed_coverage(ProjectService(db), OWNER, project_id)
        for kind, state in self._producer_states(db, project_id).items():
            assert observed[kind] == state, (
                f"{kind}: catalog says {observed[kind]!r}, the C4 producer "
                f"says {state!r}"
            )
        return observed

    # -- the three conditions the first cut got wrong ----------------

    def test_a_cant_check_watch_is_failed_not_available(self, db: Database) -> None:
        """The P0. A last_error mints cant_check in the real Room."""
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET last_error = ? WHERE id = 'watch_gh_01'",
                ("GitHub rejected the token (401)",),
            )
        room = ProjectService(db).room(OWNER, PROJECT_ID)
        minted = [s["state"] for s in room["sources"]["items"]]
        assert "cant_check" in minted, minted      # the producer's input
        observed = self._assert_agrees(db)
        assert observed["watch"] == "failed"
        assert observed["watch"] != "available"

    def test_a_never_read_watch_is_unavailable_not_stale(self, db: Database) -> None:
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET last_success_at = NULL WHERE id = 'watch_gh_01'"
            )
        observed = self._assert_agrees(db)
        assert observed["watch"] == "unavailable"

    def test_a_watch_read_long_ago_is_stale_not_available(self, db: Database) -> None:
        """Aged past the producer's OWN horizon constant, at any offset.

        Seeded through SQLite's ``datetime('now', '-N seconds')`` -- the
        same naive-UTC clock production writes -- and offset by twice the
        producer's horizon, so no timezone can drag it back across the
        line. (An earlier version seeded an offset-aware stamp and asked
        the producer on a pinned clock; at UTC+14 the absolute assertion
        failed while the equality assertion held.)
        """
        from holdspeak.services.needs_you_aggregate import (
            DEFAULT_SOURCE_STALE_AFTER_S,
        )

        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches "
                "SET last_success_at = datetime('now', ?) WHERE id = 'watch_gh_01'",
                (f"-{int(DEFAULT_SOURCE_STALE_AFTER_S * 2)} seconds",),
            )
        observed = catalog.observed_coverage(ProjectService(db), OWNER, PROJECT_ID)
        producer = self._producer_states(db, PROJECT_ID)
        assert observed["watch"] == producer["watch"] == "stale"

    def test_a_watch_read_moments_ago_is_available(self, db: Database) -> None:
        """Seeded the way production seeds it, and offset-independent.

        An earlier version of this test wrote ``datetime.now().isoformat()``
        -- a LOCAL naive stamp -- and then pinned ``TZ=UTC`` to make it
        pass, and the accompanying docstring blamed a double conversion in
        ``needs_you_aggregate._older_than``. That diagnosis was wrong and
        is retracted. The chain is consistent end to end:

        * Both writers of ``last_success_at`` -- and there are only two,
          ``db/automations.py:168`` and ``watch_service.py:875`` -- use
          SQLite ``datetime('now')``, which is naive **UTC**.
        * ``ProjectService.room`` passes it through ``aware_iso``, which
          labels a naive stamp as UTC. Correct, because it is UTC.
        * ``build_aggregate`` passes a LOCAL ``datetime.now()`` as the
          clock, and ``_older_than`` converts the aware stamp to local
          before comparing. Local against local.

        The only thing that ever needed pinning was the fixture. Seeding
        through SQLite's own clock, as production does, this passes at
        every offset -- measured at UTC, America/Los_Angeles,
        Pacific/Midway, Pacific/Kiritimati and Europe/Warsaw.
        """
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET last_success_at = datetime('now') "
                "WHERE id = 'watch_gh_01'"
            )
        observed = catalog.observed_coverage(ProjectService(db), OWNER, PROJECT_ID)
        producer = self._producer_states(db, PROJECT_ID)
        assert observed["watch"] == producer["watch"] == "available"

    def test_a_paused_watch_follows_the_producer(self, db: Database) -> None:
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET state = 'paused' WHERE id = 'watch_gh_01'"
            )
        observed = self._assert_agrees(db)
        assert observed["watch"] == "unavailable"

    # -- reduction and the absent cases ------------------------------

    def test_many_watches_reduce_to_the_worst_never_the_best(
        self, db: Database
    ) -> None:
        """A healthy source cannot hide a broken one behind it."""
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO connector_watches
                   (id, connector_id, query_kind, name, query_json, snapshot_json,
                    enabled, last_success_at, last_error, project_id, state,
                    created_at, updated_at)
                   VALUES ('watch_broken_01', 'jira', 'issues', 'watch_broken_01',
                           '{}', '{}', 1, datetime('now'),
                           'Jira rejected the token (401)', ?, '', ?, ?)""",
                (PROJECT_ID, NOW_ISO, NOW_ISO),
            )
        observed = self._assert_agrees(db)
        assert observed["watch"] == "failed"

    def test_worst_state_orders_every_c4_state(self) -> None:
        from holdspeak.services.needs_you_aggregate import COVERAGE_STATES

        for state in COVERAGE_STATES:
            assert catalog.worst_state([state]) == state
            if state != "available":
                assert catalog.worst_state([state, "available"]) == state
        assert catalog.worst_state([]) == "unavailable", "no rows is not an all-clear"

    def test_a_project_that_does_not_exist_is_never_available(
        self, db: Database
    ) -> None:
        observed = catalog.observed_coverage(ProjectService(db), OWNER, "proj_nope")
        assert "available" not in set(observed.values())

    def test_a_refused_project_list_is_forbidden_not_unavailable(
        self, db: Database
    ) -> None:
        """The same classification the producer applies to the same read.

        ``unavailable`` means nobody looked. A refusal and a broken read
        are different facts, and flattening them here would disagree with
        ``build_aggregate`` about a C4 state -- which is the P0 in a second
        place.
        """
        from holdspeak.services.needs_you_aggregate import _classify_read_failure

        class _Refusing:
            _db = db

            def list_projects(self, principal):
                raise PermissionError("principal does not permit project reads")

            def room(self, principal, project_id):
                return ProjectService(db).room(principal, project_id)

        expected, _reason = _classify_read_failure(
            PermissionError("principal does not permit project reads")
        )
        assert expected == "forbidden"
        observed = catalog.observed_coverage(_Refusing(), OWNER, PROJECT_ID)
        assert observed["project"] == expected

    def test_a_broken_project_list_is_failed_not_unavailable(
        self, db: Database
    ) -> None:
        from holdspeak.services.needs_you_aggregate import _classify_read_failure

        class _Broken:
            _db = db

            def list_projects(self, principal):
                raise RuntimeError("database is locked")

            def room(self, principal, project_id):
                return ProjectService(db).room(principal, project_id)

        expected, _reason = _classify_read_failure(RuntimeError("database is locked"))
        assert expected == "failed"
        observed = catalog.observed_coverage(_Broken(), OWNER, PROJECT_ID)
        assert observed["project"] == expected
        assert observed["project"] != "unavailable"

    def test_an_archived_project_is_not_an_available_source(
        self, db: Database
    ) -> None:
        """The Room still reads; the expected-source set no longer names it.

        ``list_projects`` is what the arrival aggregate iterates, and it
        excludes an archived Project, so the catalog must not call it
        available merely because its Room came back.
        """
        with db._connection() as conn:
            conn.execute(
                "UPDATE projects SET is_archived = 1 WHERE id = ?", (PROJECT_ID,)
            )
        room = ProjectService(db).room(OWNER, PROJECT_ID)
        assert room["needsYou"]["state"] == "ok", "the Room itself still reads"
        assert PROJECT_ID not in {
            p["id"] for p in ProjectService(db).list_projects(OWNER)
        }
        observed = catalog.observed_coverage(ProjectService(db), OWNER, PROJECT_ID)
        assert observed["project"] == "unavailable"
        plan = _plan(db, catalog.RECIPE_WEEKLY_UPDATE)
        assert not plan.ready
        assert [g["subject"] for g in plan.gaps] == ["project"]

    def test_the_seeded_project_agrees_with_the_producer_on_every_kind(
        self, db: Database
    ) -> None:
        observed = self._assert_agrees(db)
        assert observed["project"] == "available"


# ── AC: one real manual run per recipe, through the compiled plan ───────


class TestRealManualRuns:
    def test_preparation_brief_runs_and_writes_a_real_brief(
        self, db: Database
    ) -> None:
        plan = _plan(
            db, catalog.RECIPE_PREPARATION_BRIEF,
            purpose="Agree the cut-over order",
            generator="deterministic",
        )
        assert plan.ready, plan.gaps

        service = _briefs(db)
        fn = catalog.resolve_step(
            catalog.get_descriptor(plan.recipe_id).steps[0]
        )
        brief = fn(service, OWNER, **catalog.call_arguments(plan, "prepare"))

        # The record the descriptor's `output` sentence promises.
        assert brief["project_id"] == PROJECT_ID
        assert brief["purpose"] == "Agree the cut-over order"
        assert brief["lifecycle"] == "draft"
        assert brief["manifest"]["sources"], "the manifest binds what was read"
        # It is durable: a second service instance reads it back.
        again = _briefs(db).get_brief(OWNER, brief["id"])
        assert again["id"] == brief["id"]
        # And it obeys the limits the plan compiled off the real constants.
        outline = brief["outline"]
        assert len(outline["priorities"]) <= plan.limits["max_priorities"]
        assert len(outline["questions"]) <= plan.limits["max_questions"]
        assert len(outline["obligations"]) <= plan.limits["max_obligations"]

    def test_decision_review_runs_all_three_steps_and_reads_only(
        self, db: Database
    ) -> None:
        plan = _plan(db, catalog.RECIPE_DECISION_REVIEW)
        assert plan.ready, plan.gaps
        descriptor = catalog.get_descriptor(plan.recipe_id)
        by_name = {step.name: step for step in descriptor.steps}

        def before() -> tuple[int, int]:
            with db._connection() as conn:
                return (
                    conn.execute("SELECT COUNT(*) c FROM decision_records").fetchone()["c"],
                    conn.execute("SELECT COUNT(*) c FROM action_items").fetchone()["c"],
                )

        counts = before()

        board = catalog.resolve_step(by_name["obligations"])(
            FollowThroughService(db), OWNER,
            **catalog.call_arguments(plan, "obligations"),
        )
        decisions = catalog.resolve_step(by_name["decisions"])(
            DecisionRecordService(db), OWNER,
            **catalog.call_arguments(plan, "decisions"),
        )
        manifest = catalog.resolve_step(by_name["coverage"])(
            _briefs(db), OWNER, **catalog.call_arguments(plan, "coverage"),
        )

        # Current decisions.
        assert [r["id"] for r in decisions] == ["decrec_catalog_01"]
        # Unresolved obligations, on a lane of the real board.
        cards = board.now + board.waiting + board.unassigned + board.overdue
        assert any(card.id.endswith("act_catalog_01") or "rollback" in card.title.lower()
                   for card in cards), [c.title for c in cards]
        # Evidence gaps, in the C4 vocabulary.
        from holdspeak.services.needs_you_aggregate import COVERAGE_STATES

        assert manifest["sources"]
        for source in manifest["sources"]:
            assert source["state"] in COVERAGE_STATES, source

        # "Reads only" is in the descriptor's effects; prove it.
        assert before() == counts
        assert catalog.get_descriptor(plan.recipe_id).effects[0].startswith("Reads only")

    def test_weekly_update_runs_and_writes_a_real_draft(self, db: Database) -> None:
        plan = _plan(db, catalog.RECIPE_WEEKLY_UPDATE, generator="deterministic")
        assert plan.ready, plan.gaps

        service = _updates(db)
        fn = catalog.resolve_step(catalog.get_descriptor(plan.recipe_id).steps[0])
        draft = fn(service, OWNER, **catalog.call_arguments(plan, "draft"))

        assert draft["project_id"] == PROJECT_ID
        assert draft["lifecycle"] == "draft"
        assert draft["generator"] == "deterministic"
        # Nothing left the machine: the deterministic drafter records no
        # generator host or model, which is the route policy the descriptor
        # declares.
        assert not draft["generator_host"] and not draft["generator_model"]
        claims = json.loads(draft["claims_json"] or "[]")
        assert claims, "the draft carries claim entries"
        # C2: kind and support are independent axes, and both are present.
        from holdspeak.services.project_update_service import (
            CLAIM_KINDS,
            SUPPORT_STATES,
        )

        for claim in claims:
            assert claim["kind"] in CLAIM_KINDS, claim
            assert claim["support"] in SUPPORT_STATES, claim

    def test_a_plan_that_is_not_ready_is_never_run_blind(self, db: Database) -> None:
        """The compiler is the fence: a missing required input yields a gap,
        and the bound call would refuse on the same field."""
        plan = catalog.compile_recipe(
            catalog.RECIPE_PREPARATION_BRIEF,
            inputs={"project_id": PROJECT_ID},
            coverage=catalog.observed_coverage(ProjectService(db), OWNER, PROJECT_ID),
        )
        assert not plan.ready
        assert [g["subject"] for g in plan.gaps] == ["purpose"]
        assert "purpose" not in plan.inputs
        with pytest.raises(catalog.CatalogError, match="purpose"):
            catalog.call_arguments(plan, "prepare")


# ── the same definition, reached by a scheduled firing ──────────────────


class TestOneDefinitionSharedWithASchedule:
    @pytest.mark.parametrize(
        "recipe_id",
        [
            catalog.RECIPE_PREPARATION_BRIEF,
            catalog.RECIPE_DECISION_REVIEW,
            catalog.RECIPE_WEEKLY_UPDATE,
        ],
    )
    def test_the_scheduled_plan_would_call_the_identical_bound_functions(
        self, db: Database, recipe_id: str
    ) -> None:
        inputs = {"project_id": PROJECT_ID, "purpose": "Agree the cut-over order"}
        coverage = catalog.observed_coverage(ProjectService(db), OWNER, PROJECT_ID)
        manual = catalog.compile_recipe(
            recipe_id, trigger=catalog.TRIGGER_MANUAL, inputs=inputs, coverage=coverage
        )
        scheduled = catalog.compile_recipe(
            recipe_id, trigger=catalog.TRIGGER_SCHEDULED, inputs=inputs,
            coverage=coverage,
        )
        assert manual.plan_id == scheduled.plan_id
        assert manual.recipe_version == scheduled.recipe_version

        descriptor = catalog.get_descriptor(recipe_id)
        for step in descriptor.steps:
            assert catalog.resolve_step(step) is catalog.resolve_step(step)
            assert catalog.call_arguments(manual, step.name) == catalog.call_arguments(
                scheduled, step.name
            )

        # Manual is ready; scheduled is honestly blocked on its owner.
        assert manual.ready, manual.gaps
        assert not scheduled.ready
        blocked = [g for g in scheduled.gaps if g["reason"] == "trigger_owner_not_wired"]
        assert len(blocked) == 1
        assert blocked[0]["supplied_by"].strip()


class TestTheScheduledOwnerReallyFires:
    """Ruling R17-8: the declared trigger owner is not a stub.

    No sweep step invokes a prepared recipe yet (HS-200-21/33/35 add them),
    and the descriptors say so as a typed gap.  What is proven here is the
    other half: the owner the descriptors NAME is a clock that really runs
    on this database, so the gap closes by adding a step rather than by
    inventing a scheduler.
    """

    def test_the_heartbeat_sweep_runs_for_real_and_returns_a_receipt(
        self, db: Database
    ) -> None:
        from holdspeak.services.heartbeat_service import HeartbeatService

        receipt = HeartbeatService(db).run_sweep(OWNER, owner_hand=True)
        assert isinstance(receipt, dict)
        assert "duration_ms" in receipt and "watches" in receipt
        assert receipt.get("held") in (False, None), receipt

    def test_every_link_of_the_declared_owner_chain_exists(self) -> None:
        """Ruling R17-12, asserted link by link on real objects.

        The descriptors name a specific adapter chain, not "the sweep". If
        any link is renamed or removed, the descriptors are describing
        something that no longer exists and this goes red.
        """
        import inspect as _inspect

        from holdspeak.db import schema
        from holdspeak.services.heartbeat_service import HeartbeatService
        from holdspeak.services.project_steward_service import ProjectStewardService
        from holdspeak.services.watch_service import WatchService
        from holdspeak.watch_validation import ACTION_KINDS

        chain = catalog.SCHEDULED_TRIGGER_OWNER

        # 1. the interval columns on the watch row
        watches = schema.SCHEMA_SQL.split(
            "CREATE TABLE IF NOT EXISTS connector_watches"
        )[1].split(");")[0]
        assert "evaluation_cadence_minutes" in watches
        assert "next_evaluation_at" in watches
        assert "connector_watches interval" in chain

        # 2. the wall clock and the due evaluation
        assert callable(getattr(HeartbeatService, "run_sweep", None))
        assert callable(getattr(WatchService, "evaluate_due", None))
        assert "HeartbeatService.run_sweep" in chain
        assert "WatchService.evaluate_due" in chain

        # 3. the effect kind, read off the real registry
        assert "project.steward.run_once" in ACTION_KINDS
        assert "project.steward.run_once" in chain

        # 4. the drain, and its opt-in gate
        assert callable(getattr(ProjectStewardService, "run_due", None))
        assert "ProjectStewardService.run_due" in chain
        drain = _inspect.getsource(ProjectStewardService.run_due)
        assert "unattended_enabled" in drain, (
            "the drain must stay gated by the per-project opt-in"
        )

    def test_the_sweep_is_driven_by_a_wall_clock_loop(self) -> None:
        """Asserted on the compiled code object, not the source text.

        Counsel's P2-4: the first cut matched substrings like
        ``"sweep_interval" in driver``, which a reformat breaks and a
        gutted loop survives. Bytecode names and constants survive
        reformatting, comments and local renames, and disappear the moment
        the loop stops doing the thing.
        """
        from holdspeak.runtime.heartbeat import HeartbeatMixin

        loop = HeartbeatMixin._heartbeat_loop
        names = set(loop.__code__.co_names)
        # It reads the interval, decides, and sweeps.
        assert "get_settings" in names
        assert "run_sweep" in names
        # It is a loop over a stop event, not a one-shot call.
        assert {"is_set", "wait"} <= names
        # The tick is a real number of seconds.
        ticks = [
            c for c in loop.__code__.co_consts
            if isinstance(c, int) and not isinstance(c, bool) and c >= 10
        ]
        assert ticks, loop.__code__.co_consts

        # And a thread is actually started on it.
        starter = HeartbeatMixin._start_heartbeat_thread
        assert "Thread" in set(starter.__code__.co_names)
        assert "_heartbeat_loop" in set(
            starter.__code__.co_names
        ) | set(starter.__code__.co_consts)

    def test_no_sweep_module_invokes_a_prepared_recipe_yet(self) -> None:
        """Counsel's P2-1, as a direct check rather than a self-reference.

        The descriptors claim no scheduled firing exists. Prove it by the
        event that would make it false: a sweep module importing the
        catalog.
        """
        import importlib

        for module_name in (
            "holdspeak.runtime.heartbeat",
            "holdspeak.services.heartbeat_service",
            "holdspeak.services.watch_service",
            "holdspeak.services.project_steward_service",
        ):
            source = __import__("inspect").getsource(
                importlib.import_module(module_name)
            )
            assert "recipe_catalog" not in source, (
                f"{module_name} now reaches the prepared-recipe catalog: a "
                "scheduled firing may exist, so the descriptors' "
                "available=False and the USER_GUIDE sentence must be "
                "revisited in this same commit"
            )

    def test_the_definition_a_sweep_would_run_is_the_one_a_manual_run_ran(
        self, db: Database
    ) -> None:
        """Same descriptor, same version, same bound call, same record.

        The manual leg actually executes; the scheduled leg compiles to a
        byte-identical call.  That is the whole of the acceptance criterion
        that can be honestly proven before a sweep step exists.
        """
        inputs = {"project_id": PROJECT_ID, "generator": "deterministic"}
        coverage = catalog.observed_coverage(ProjectService(db), OWNER, PROJECT_ID)
        manual = catalog.compile_recipe(
            catalog.RECIPE_WEEKLY_UPDATE, trigger=catalog.TRIGGER_MANUAL,
            inputs=inputs, coverage=coverage,
        )
        scheduled = catalog.compile_recipe(
            catalog.RECIPE_WEEKLY_UPDATE, trigger=catalog.TRIGGER_SCHEDULED,
            inputs=inputs, coverage=coverage,
        )
        step = catalog.get_descriptor(catalog.RECIPE_WEEKLY_UPDATE).steps[0]
        fn = catalog.resolve_step(step)
        args = catalog.call_arguments(manual, step.name)
        assert args == catalog.call_arguments(scheduled, step.name)

        draft = fn(_updates(db), OWNER, **args)
        assert draft["project_id"] == PROJECT_ID
        assert draft["lifecycle"] == "draft"
        assert manual.recipe_version == scheduled.recipe_version == 1


# ── discoverability on the real wires ───────────────────────────────────


@pytest.fixture
def root(db: Database):
    """Install a bare composition root over the test database."""
    composition.install(composition.bare(db, label="recipe-catalog-test"))
    yield
    composition.uninstall()


class TestMcpWire:
    def test_list_returns_the_three_descriptors(self, root: None) -> None:
        from holdspeak.mcp import tools

        payload = tools.dispatch("practice_recipe.list", {}, OWNER)
        assert [r["recipe_id"] for r in payload["recipes"]] == [
            catalog.RECIPE_PREPARATION_BRIEF,
            catalog.RECIPE_DECISION_REVIEW,
            catalog.RECIPE_WEEKLY_UPDATE,
        ]

    def test_get_returns_one_descriptor(self, root: None) -> None:
        from holdspeak.mcp import tools

        payload = tools.dispatch(
            "practice_recipe.get", {"recipe_id": catalog.RECIPE_WEEKLY_UPDATE}, OWNER
        )
        assert payload["recipe_id"] == catalog.RECIPE_WEEKLY_UPDATE
        assert payload["steps"][0]["qualified_ref"].endswith("draft_update")

    def test_compile_reads_the_real_project_through_the_one_root(
        self, root: None
    ) -> None:
        from holdspeak.mcp import tools

        plan = tools.dispatch(
            "practice_recipe.compile",
            {
                "recipe_id": catalog.RECIPE_WEEKLY_UPDATE,
                "project_id": PROJECT_ID,
            },
            OWNER,
        )
        assert plan["ready"] is True, plan["gaps"]
        assert [r["state"] for r in plan["source_scope"] if r["kind"] == "project"] == [
            "available"
        ]

    def test_compile_on_an_absent_project_reports_a_typed_gap(
        self, root: None
    ) -> None:
        from holdspeak.mcp import tools

        plan = tools.dispatch(
            "practice_recipe.compile",
            {"recipe_id": catalog.RECIPE_WEEKLY_UPDATE, "project_id": "proj_nope"},
            OWNER,
        )
        assert plan["ready"] is False
        gap = [g for g in plan["gaps"] if g["subject"] == "project"][0]
        assert gap["state"] == "unavailable"
        assert gap["missing"] and gap["supplied_by"]

    def test_compile_under_a_stale_version_reports_it_on_the_wire(
        self, root: None
    ) -> None:
        from holdspeak.mcp import tools

        plan = tools.dispatch(
            "practice_recipe.compile",
            {
                "recipe_id": catalog.RECIPE_WEEKLY_UPDATE,
                "project_id": PROJECT_ID,
                "version": 99,
            },
            OWNER,
        )
        assert [g["kind"] for g in plan["gaps"]] == [catalog.GAP_STALE_DESCRIPTOR]

    def test_an_unsupported_trigger_comes_back_typed_not_silently_ignored(
        self, root: None
    ) -> None:
        """Two fences, and the family owns the second.

        The published schema pins ``trigger`` to the two supported tokens, so
        a schema-validating MCP client is refused before the call. Families
        dispatch ahead of ``_validate_tool_arguments`` (``tools.py:655-664``),
        so the family must ALSO answer honestly for a caller that skips it --
        and it does: a typed ``unsupported_trigger`` gap, never a silent
        fallback to ``manual``.
        """
        from holdspeak.mcp import tools
        from holdspeak.mcp.families.practice_recipe import TOOLS as FAMILY_TOOLS

        schema = [t for t in FAMILY_TOOLS if t["name"] == "practice_recipe.compile"][0]
        assert schema["inputSchema"]["properties"]["trigger"]["enum"] == list(
            catalog.TRIGGERS
        )

        plan = tools.dispatch(
            "practice_recipe.compile",
            {
                "recipe_id": catalog.RECIPE_WEEKLY_UPDATE,
                "project_id": PROJECT_ID,
                "trigger": "on_commit",
            },
            OWNER,
        )
        assert plan["ready"] is False
        assert plan["trigger"] == "on_commit"
        assert catalog.GAP_UNSUPPORTED_TRIGGER in {g["kind"] for g in plan["gaps"]}


class TestWebWire:
    """The same three reads over HTTP, on the existing automations router."""

    @pytest.fixture
    def client(self, db: Database):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from holdspeak.services.reaction_service import ReactionService
        from holdspeak.web.routes import automations as automation_routes

        class _Ctx:
            reaction_service = ReactionService(db)

        app = FastAPI()
        app.include_router(automation_routes.build_automations_router(_Ctx()))
        return TestClient(app)

    def test_the_catalog_lists(self, client) -> None:
        response = client.get("/api/automations/practice-recipes")
        assert response.status_code == 200
        body = response.json()
        assert [r["recipe_id"] for r in body["recipes"]] == [
            catalog.RECIPE_PREPARATION_BRIEF,
            catalog.RECIPE_DECISION_REVIEW,
            catalog.RECIPE_WEEKLY_UPDATE,
        ]
        assert body["coverage_states"] == list(
            __import__(
                "holdspeak.services.needs_you_aggregate", fromlist=["COVERAGE_STATES"]
            ).COVERAGE_STATES
        )

    def test_one_descriptor_reads(self, client) -> None:
        response = client.get(
            f"/api/automations/practice-recipes/{catalog.RECIPE_DECISION_REVIEW}"
        )
        assert response.status_code == 200
        assert len(response.json()["steps"]) == 3

    def test_an_unknown_recipe_is_404_by_name(self, client) -> None:
        response = client.get("/api/automations/practice-recipes/weekly_standup")
        assert response.status_code == 404
        assert response.json()["code"] == "unknown_recipe"

    def test_the_plan_compiles_against_the_real_project(self, client) -> None:
        response = client.get(
            f"/api/automations/practice-recipes/{catalog.RECIPE_PREPARATION_BRIEF}/plan",
            params={"project_id": PROJECT_ID, "purpose": "Agree the cut-over order"},
        )
        assert response.status_code == 200
        plan = response.json()
        assert plan["ready"] is True, plan["gaps"]
        assert plan["recipe_version"] == 1
        assert plan["limits"]["max_priorities"] >= 1

    def test_the_plan_reports_typed_gaps_rather_than_failing(self, client) -> None:
        response = client.get(
            f"/api/automations/practice-recipes/{catalog.RECIPE_PREPARATION_BRIEF}/plan",
            params={"project_id": "proj_nope", "trigger": catalog.TRIGGER_SCHEDULED},
        )
        assert response.status_code == 200
        plan = response.json()
        assert plan["ready"] is False
        kinds = {g["kind"] for g in plan["gaps"]}
        assert catalog.GAP_MISSING_INPUT in kinds          # no purpose
        assert catalog.GAP_UNAVAILABLE_PREREQUISITE in kinds  # no project, no schedule
        for row in plan["gaps"]:
            assert row["missing"] and row["supplied_by"]
