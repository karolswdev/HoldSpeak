"""HS-131-15 hostile proofs for synthetic-text dictation entrances.

The real session planner, kernel parent, fence, and pipeline stay in the test.
Only the physical provider wire is absent: the concern here is whether browser
and CLI side doors can reach that wire before they own a fresh finite admission.
"""

from __future__ import annotations

import asyncio
import sqlite3
import threading
from datetime import datetime
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.kernel.model import KernelRefused
from holdspeak.kernel.runtime import _configure
from holdspeak.plugins.dictation.contracts import Utterance
from holdspeak.plugins.dictation.pipeline import DictationPipeline
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.speech_session import (
    AIM_BROWSER_REHEARSE,
    AIM_JOURNAL_REPLAY,
    CAPABILITY_INTENT_CLASSIFY,
    CAPABILITY_REWRITE,
    CAPABILITY_WHISPER_PRELOAD,
    CAPABILITY_WHISPER_TRANSCRIBE,
    ENTRY_CHILD_BUDGET,
    ENTRY_DEADLINE_SECONDS,
    OUTCOME_INDETERMINATE,
    ProviderAdmission,
    SpeechEntry,
    SpeechProviderFailure,
    SpeechSessionRefused,
    admit_text_entry_session,
    cli_owner_principal,
    configured_pipeline_egress_boundary,
    pipeline_provider_capabilities,
    require_entry_admission,
)
from holdspeak.speech_session.plan import (
    CONTRACT_INTENT_CLASSIFY,
    ENTRY_SESSION_REQUIRED,
    SESSION_CLOSED,
    SESSION_REVOKED,
)


OWNER = Principal(PrincipalKind.OWNER, "hs-131-15-side-door")


def _provider_config() -> Config:
    config = Config()
    config.dictation.pipeline.enabled = True
    config.dictation.pipeline.stages = ["intent-router"]
    config.dictation.runtime.profile_id = "side-door-provider"
    return config


def _entry(
    tmp_path, monkeypatch: pytest.MonkeyPatch, *, aim: str = AIM_BROWSER_REHEARSE
) -> tuple[Database, Config, SpeechEntry]:
    """Open a real provider-bearing synthetic-text entry over a fresh database."""
    database = Database(tmp_path / f"{aim}.db")
    database.profiles.upsert(
        profile_id="side-door-provider",
        name="side-door-provider",
        kind="openAICompatible",
        base_url="http://127.0.0.1:19191/v1",
        model="side-door-model",
    )
    monkeypatch.setattr("holdspeak.db.get_database", lambda: database)
    _configure(database)
    config = _provider_config()
    session = admit_text_entry_session(
        principal=OWNER,
        insertion_aim=aim,
        config_snapshot=config,
        registry_snapshot=database,
    )
    return database, config, SpeechEntry(session)


def test_text_entry_is_fresh_bounded_and_never_plans_mic_capabilities(
    tmp_path, monkeypatch
) -> None:
    """A browser rehearsal is a 90-second/12-child text session, not open-mic work."""
    _database, _config, entry = _entry(tmp_path, monkeypatch)

    plan = require_entry_admission(entry.provider, entry.fence)

    assert plan.insertion_aim == AIM_BROWSER_REHEARSE
    assert plan.deadline_at - plan.created_at == pytest.approx(ENTRY_DEADLINE_SECONDS)
    assert plan.child_budget == ENTRY_CHILD_BUDGET
    assert plan.has(CAPABILITY_INTENT_CLASSIFY)
    assert not plan.has(CAPABILITY_WHISPER_TRANSCRIBE)
    assert not plan.has(CAPABILITY_WHISPER_PRELOAD)
    assert entry.session.kind == "dictation.session"


def test_browser_egress_disclosure_and_execution_proof_share_the_resolver(
    tmp_path, monkeypatch
) -> None:
    """The pre-action badge and frozen plan both classify the selected LAN leg."""
    database = Database(tmp_path / "entry-egress.db")
    database.profiles.upsert(
        profile_id="side-door-provider",
        name="side-door-provider",
        kind="openAICompatible",
        base_url="http://192.168.1.43:8080/v1",
        model="side-door-model",
    )
    monkeypatch.setattr("holdspeak.db.get_database", lambda: database)
    _configure(database)
    config = _provider_config()

    assert configured_pipeline_egress_boundary(config, database) == "private_network"
    entry = SpeechEntry(
        admit_text_entry_session(
            principal=OWNER,
            insertion_aim=AIM_BROWSER_REHEARSE,
            config_snapshot=config,
            registry_snapshot=database,
        )
    )
    assert entry.provider.egress_boundary == "private_network"
    entry.cancel()


def test_entry_admission_refuses_missing_cross_session_and_ended_handles_before_build(
    tmp_path, monkeypatch
) -> None:
    """A helper cannot borrow, forge, or revive another entry's provider handle."""
    database, config, first = _entry(tmp_path, monkeypatch)
    second = SpeechEntry(
        admit_text_entry_session(
            principal=OWNER,
            insertion_aim=AIM_JOURNAL_REPLAY,
            config_snapshot=config,
            registry_snapshot=database,
        )
    )

    with pytest.raises(SpeechSessionRefused) as missing:
        require_entry_admission(None, None)
    assert missing.value.reason == ENTRY_SESSION_REQUIRED

    with pytest.raises(SpeechSessionRefused) as crossed:
        require_entry_admission(first.provider, second.fence)
    assert crossed.value.reason == ENTRY_SESSION_REQUIRED

    # Object identity on ``admission.fence`` is not enough: an internal caller
    # could otherwise pair that live fence with a different parent's dispatch
    # context. The durable parent id must bind all three carriers.
    mismatched_parent = ProviderAdmission(
        broker=first.provider.broker,
        principal=first.provider.principal,
        plan=first.provider.plan,
        parent=second.session.parent,
        fence=first.fence,
    )
    with pytest.raises(SpeechSessionRefused) as forged:
        require_entry_admission(mismatched_parent, first.fence)
    assert forged.value.reason == ENTRY_SESSION_REQUIRED

    mismatched_plan = ProviderAdmission(
        broker=first.provider.broker,
        principal=first.provider.principal,
        plan=second.plan,
        parent=first.session.parent,
        fence=first.fence,
    )
    with pytest.raises(SpeechSessionRefused) as retargeted:
        require_entry_admission(mismatched_plan, first.fence)
    assert retargeted.value.reason == ENTRY_SESSION_REQUIRED

    first.close("succeeded")
    with pytest.raises(SpeechSessionRefused) as ended:
        require_entry_admission(first.provider, first.fence)
    assert ended.value.reason == SESSION_CLOSED


def test_provider_pre_fence_preserves_the_exact_revocation_reason(
    tmp_path, monkeypatch
) -> None:
    """A durable revocation is not rewritten to the generic provider fence."""
    database, _config, entry = _entry(tmp_path, monkeypatch)
    with database._connection() as conn:
        conn.execute(
            "UPDATE kernel_operations SET warrant_revoked=1 WHERE operation_id=?",
            (entry.session.operation_id,),
        )

    reached: list[str] = []
    with pytest.raises(SpeechSessionRefused) as refusal:
        entry.provider.child(
            capability=CAPABILITY_INTENT_CLASSIFY,
            contract=CONTRACT_INTENT_CLASSIFY,
            material={"probe": "fixed-control-only"},
            call=lambda *_args: reached.append("provider"),
            seed="revoked-before-child",
        )

    assert refusal.value.reason == SESSION_REVOKED
    assert reached == []
    with database._connection() as conn:
        children = conn.execute(
            "SELECT operation_id FROM kernel_operations WHERE name='inference.invoke'"
        ).fetchall()
    assert children == []


def test_post_claim_kernel_refusal_returns_through_the_safe_named_channel(
    tmp_path, monkeypatch
) -> None:
    """A context/revision control refusal stays named after child claim."""
    database, _config, entry = _entry(tmp_path, monkeypatch)
    entry.session.broker.inference_runner._engine_factory = (
        lambda *_args, **_kwargs: SimpleNamespace()
    )

    def refuse_after_claim(*_args: Any) -> None:
        raise KernelRefused("adapter_context_mismatch")

    with pytest.raises(SpeechSessionRefused) as refusal:
        with entry:
            entry.provider.child(
                capability=CAPABILITY_INTENT_CLASSIFY,
                contract=CONTRACT_INTENT_CLASSIFY,
                material={"probe": "fixed-control-only"},
                call=refuse_after_claim,
                seed="post-claim-refusal",
            )

    assert refusal.value.reason == "adapter_context_mismatch"
    with database._connection() as conn:
        child = conn.execute(
            "SELECT operation_id FROM kernel_operations WHERE name='inference.invoke'"
        ).fetchone()
    assert child is not None
    assert entry.session.broker.store.receipt(child["operation_id"])["outcome"] == "refused"


def test_shared_helper_refuses_before_the_runtime_factory_can_be_reached(
    monkeypatch, tmp_path
) -> None:
    """`admission=None` is a named refusal, never an HTTP construction seam."""
    import holdspeak.plugins.dictation.assembly as assembly
    from holdspeak.web.routes.dictation import _helpers

    built: list[dict[str, Any]] = []

    def forbidden_build(*_args: Any, **kwargs: Any) -> Any:
        built.append(dict(kwargs))
        raise AssertionError("unadmitted browser helper constructed a runtime")

    monkeypatch.setattr(assembly, "build_pipeline", forbidden_build)

    with pytest.raises(SpeechSessionRefused) as refusal:
        config = Config()
        config.dictation.pipeline.enabled = True
        config.dictation.pipeline.stages = ["intent-router"]
        _helpers._run_dictation_dry_run_text(
            "SIDE_DOOR_UNADMITTED_TEXT",
            str(tmp_path),
            suggestions={},
            config_snapshot=config,
            admission=None,
            fence=None,
        )

    assert refusal.value.reason == ENTRY_SESSION_REQUIRED
    assert built == []


def test_open_text_entry_uses_only_the_middleware_principal_and_one_snapshot(
    monkeypatch
) -> None:
    """Payload-shaped attributes cannot choose authority or cause a second config read."""
    from holdspeak.web.routes.dictation import _helpers
    import holdspeak.speech_session as speech_session

    config = Config()
    middleware_principal = Principal(PrincipalKind.OWNER, "credential-owner")
    payload_principal = Principal(PrincipalKind.OWNER, "forged-payload-owner")
    registry = object()
    session = object()
    seen: dict[str, Any] = {}

    class CapturedEntry:
        def __init__(self, value: Any) -> None:
            self.session = value

    def admit(**kwargs: Any) -> Any:
        seen.update(kwargs)
        return session

    monkeypatch.setattr(Config, "load", classmethod(lambda _cls: config))
    monkeypatch.setattr("holdspeak.db.get_database", lambda: registry)
    monkeypatch.setattr(speech_session, "admit_text_entry_session", admit)
    monkeypatch.setattr(speech_session, "SpeechEntry", CapturedEntry)

    request = SimpleNamespace(
        state=SimpleNamespace(principal=middleware_principal),
        payload={"principal": payload_principal, "parent_id": "forged-parent"},
    )
    snapshot, entry = _helpers._open_text_entry(request, AIM_BROWSER_REHEARSE)

    assert snapshot is config
    assert entry.session is session
    assert seen == {
        "principal": middleware_principal,
        "insertion_aim": AIM_BROWSER_REHEARSE,
        "config_snapshot": config,
        "registry_snapshot": registry,
    }


def test_session_fence_is_built_once_before_the_session_is_published(
    tmp_path, monkeypatch
) -> None:
    """Wake/browser cancellation can never race first access into split carriers."""
    import holdspeak.speech_session.fence as fence_module

    real_fence = fence_module.SessionFence
    created: list[Any] = []

    class CountingFence(real_fence):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            created.append(self)

    monkeypatch.setattr(fence_module, "SessionFence", CountingFence)
    _database, _config, entry = _entry(tmp_path, monkeypatch)

    assert created == [entry.session.fence]
    assert entry.session._fence is entry.session.fence
    entry.cancel()


def test_browser_lexical_preview_mints_no_speech_parent(monkeypatch) -> None:
    from holdspeak.web.routes.dictation import _helpers

    config = Config()
    config.dictation.pipeline.enabled = False
    monkeypatch.setattr(Config, "load", classmethod(lambda _cls: config))
    monkeypatch.setattr(
        _helpers,
        "_open_text_entry",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("lexical preview admitted a speech parent")
        ),
    )
    seen: list[tuple[Any, Any]] = []

    def work(snapshot: Any, entry: Any) -> dict[str, bool]:
        seen.append((snapshot, entry))
        return {"lexical": True}

    result = asyncio.run(
        _helpers._run_cancellable_entry(
            SimpleNamespace(), AIM_BROWSER_REHEARSE, work
        )
    )

    assert result == {"lexical": True}
    assert seen == [(config, None)]


def test_disconnect_watcher_cancels_preview_and_late_publication_loses(
    tmp_path, monkeypatch
) -> None:
    """A real disconnect closes the parent before a slow replay can publish."""
    from holdspeak.web.routes.dictation import _helpers

    database, _config, entry = _entry(tmp_path, monkeypatch, aim=AIM_JOURNAL_REPLAY)
    monkeypatch.setattr(_helpers, "_DISCONNECT_POLL_SECONDS", 0)

    class DisconnectingRequest:
        probes = 0

        async def is_disconnected(self) -> bool:
            self.probes += 1
            return self.probes >= 2

    asyncio.run(_helpers._watch_disconnect(DisconnectingRequest(), entry))

    late_publications: list[str] = []
    won, value = entry.fence.publish(
        "late replay response", lambda: late_publications.append("replay")
    )
    assert (won, value) == (False, None)
    assert late_publications == []
    assert entry.session.broker.store.receipt(entry.session.operation_id)["outcome"] == "cancelled"
    assert entry.session.broker.database is database


def test_publication_fence_has_one_winner_in_both_cancellation_orderings(
    tmp_path, monkeypatch
) -> None:
    """Cancellation-first discards; publication-first completes its bounded callback."""
    _database, _config, cancelled_first = _entry(tmp_path, monkeypatch)
    cancelled_first.fence.cancel()
    discarded: list[str] = []
    assert cancelled_first.fence.publish(
        "journal after cancellation", lambda: discarded.append("journal")
    ) == (False, None)
    assert discarded == []

    _database, _config, published_first = _entry(
        tmp_path, monkeypatch, aim=AIM_JOURNAL_REPLAY
    )
    callback_entered = threading.Event()
    release_callback = threading.Event()
    cancellation_finished = threading.Event()
    published: list[str] = []
    result: list[tuple[bool, str | None]] = []

    def callback() -> str:
        callback_entered.set()
        assert release_callback.wait(5), "test never released the elected publication"
        published.append("response-and-journal")
        return "published"

    publisher = threading.Thread(
        target=lambda: result.append(
            published_first.fence.publish("replay publication", callback)
        )
    )
    publisher.start()
    assert callback_entered.wait(5), "publication never acquired the election"

    canceller = threading.Thread(
        target=lambda: (
            published_first.fence.cancel(), cancellation_finished.set()
        )
    )
    canceller.start()
    assert not cancellation_finished.wait(0.1), "cancellation bypassed the election"
    release_callback.set()
    publisher.join(5)
    canceller.join(5)

    assert not publisher.is_alive() and not canceller.is_alive()
    assert result == [(True, "published")]
    assert published == ["response-and-journal"]
    assert cancellation_finished.is_set()
    assert published_first.fence.publish("late suggestion", lambda: "late") == (False, None)


def test_schema_v57_upgrades_publication_claim_before_installing_triggers(
    tmp_path
) -> None:
    """An existing Phase-131 database upgrades without trigger/column skew."""
    path = tmp_path / "schema-v57-publication.db"
    original = Database(path)
    with original._connection() as conn:
        conn.execute("DROP TRIGGER kernel_parent_publication_blocks_transition")
        conn.execute(
            "DROP TRIGGER kernel_parent_publication_blocks_warrant_revocation"
        )
        conn.execute(
            "ALTER TABLE kernel_parent_runs DROP COLUMN publication_claimed_at"
        )
        conn.execute(
            "ALTER TABLE kernel_parent_runs DROP COLUMN publication_claim_id"
        )
        conn.execute("DELETE FROM schema_version")
        conn.execute("INSERT INTO schema_version(version) VALUES(57)")
    original.close()

    migrated = Database(path)
    with migrated._connection() as conn:
        columns = {
            str(row["name"])
            for row in conn.execute("PRAGMA table_info(kernel_parent_runs)")
        }
        triggers = {
            str(row["name"])
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger' "
                "AND name LIKE 'kernel_parent_publication_%'"
            )
        }
    migrated.close()

    assert {"publication_claim_id", "publication_claimed_at"} <= columns
    assert triggers == {
        "kernel_parent_publication_blocks_transition",
        "kernel_parent_publication_blocks_warrant_revocation",
    }


def test_durable_publication_claim_blocks_direct_cross_process_mutations(
    tmp_path, monkeypatch
) -> None:
    """Raw durable revoke/cancel cannot commit behind the fence's liveness read."""
    database, _config, entry = _entry(tmp_path, monkeypatch)
    entered = threading.Event()
    release = threading.Event()
    published: list[str] = []

    def callback() -> None:
        entered.set()
        assert release.wait(5), "test never released durable publication"
        published.append("published")
        entry.close("succeeded")

    publisher = threading.Thread(
        target=lambda: entry.fence.publish("durable publication", callback)
    )
    publisher.start()
    assert entered.wait(5), "publication never acquired its durable claim"

    with pytest.raises(KernelRefused) as child_refusal:
        entry.session.broker.parent_run_controller.reserve_child(
            entry.session.context,
            OWNER,
            planned_node="forbidden-after-publication-claim",
            invocation_id="forbidden-publication-child",
        )
    assert child_refusal.value.reason == "parent_publication_in_progress"

    peer = Database(database.db_path)
    with pytest.raises(sqlite3.IntegrityError, match="publication_in_progress"):
        with peer._connection() as conn:
            conn.execute(
                "UPDATE kernel_operations SET warrant_revoked=1 WHERE operation_id=?",
                (entry.session.operation_id,),
            )
    with pytest.raises(sqlite3.IntegrityError, match="publication_in_progress"):
        with peer._connection() as conn:
            conn.execute(
                "UPDATE kernel_parent_runs SET state='CANCELLING' WHERE operation_id=?",
                (entry.session.operation_id,),
            )

    release.set()
    publisher.join(5)
    peer.close()

    assert not publisher.is_alive()
    assert published == ["published"]
    with database._connection() as conn:
        row = conn.execute(
            "SELECT p.state,p.publication_claim_id,o.warrant_revoked "
            "FROM kernel_parent_runs p JOIN kernel_operations o "
            "ON o.operation_id=p.operation_id WHERE p.operation_id=?",
            (entry.session.operation_id,),
        ).fetchone()
    assert dict(row) == {
        "state": "SUCCEEDED",
        "publication_claim_id": "",
        "warrant_revoked": 0,
    }


def test_failed_publication_release_recovers_in_the_live_process(
    tmp_path, monkeypatch
) -> None:
    """A transient release write cannot strand an OPEN parent until restart."""
    database, _config, entry = _entry(tmp_path, monkeypatch)
    fence_type = type(entry.fence)
    release_once = fence_type._release_publication_once
    recovered = threading.Event()
    attempts: list[str] = []

    def fail_once_then_release(self, claim_id: str) -> None:
        attempts.append(claim_id)
        if len(attempts) == 1:
            raise sqlite3.OperationalError("injected publication release failure")
        release_once(self, claim_id)
        recovered.set()

    monkeypatch.setattr(
        fence_type, "_release_publication_once", fail_once_then_release
    )

    assert entry.fence.publish(
        "release recovery", lambda: "published-once"
    ) == (True, "published-once")
    assert recovered.wait(5), "live release recovery never cleared the claim"

    with database._connection() as conn:
        row = conn.execute(
            "SELECT state,publication_claim_id FROM kernel_parent_runs "
            "WHERE operation_id=?",
            (entry.session.operation_id,),
        ).fetchone()
    assert dict(row) == {"state": "OPEN", "publication_claim_id": ""}
    assert len(attempts) >= 2
    entry.cancel()


def test_expiry_reaper_defers_across_a_live_publication_claim(
    tmp_path, monkeypatch
) -> None:
    """Supported liveness never leaks the claim trigger's SQLite exception."""
    _database, _config, entry = _entry(tmp_path, monkeypatch)
    entered = threading.Event()
    release = threading.Event()
    published: list[str] = []

    def callback() -> None:
        entered.set()
        assert release.wait(5), "test never released durable publication"
        published.append("published")

    publisher = threading.Thread(
        target=lambda: entry.fence.publish("expiry race", callback)
    )
    publisher.start()
    assert entered.wait(5), "publication never acquired its durable claim"

    operation = entry.session.broker.store.operation(entry.session.operation_id)
    assert operation is not None
    execution_expiry = float(operation["warrant"]["execution_expires_at"])
    monkeypatch.setattr(entry.session.broker, "_clock", lambda: execution_expiry + 1.0)
    monkeypatch.setattr(
        entry.session.broker.store, "_publication_wait_seconds", 0.05
    )

    assert entry.session.broker.reap_expired() == {"reaped": [], "count": 0}
    assert publisher.is_alive(), "reaper bypassed the live publication claim"

    release.set()
    publisher.join(5)
    assert not publisher.is_alive()
    assert published == ["published"]
    assert entry.session.broker.reap_expired() == {
        "reaped": [
            {
                "operation_id": entry.session.operation_id,
                "state": "indeterminate",
                "outcome": "execution_liveness_expired",
            }
        ],
        "count": 1,
    }


def test_warrant_revocation_waits_for_durable_publication_release(
    tmp_path, monkeypatch
) -> None:
    """The supported revocation path commits after, never inside, publication."""
    _database, _config, entry = _entry(tmp_path, monkeypatch)
    entered = threading.Event()
    release = threading.Event()
    revoke_started = threading.Event()
    revoke_finished = threading.Event()
    order: list[str] = []

    def callback() -> None:
        entered.set()
        assert release.wait(5), "test never released durable publication"
        order.append("published")

    publisher = threading.Thread(
        target=lambda: entry.fence.publish("durable intermediate publication", callback)
    )
    publisher.start()
    assert entered.wait(5), "publication never acquired its durable claim"

    def revoke() -> None:
        revoke_started.set()
        entry.session.broker.store.revoke_warrant(entry.session.operation_id)
        order.append("revoked")
        revoke_finished.set()

    revoker = threading.Thread(target=revoke)
    revoker.start()
    assert revoke_started.wait(5)
    assert not revoke_finished.wait(0.1), "revocation bypassed the durable claim"
    release.set()
    publisher.join(5)
    revoker.join(5)

    assert not publisher.is_alive() and not revoker.is_alive()
    assert order == ["published", "revoked"]
    assert entry.fence.reason() == SESSION_REVOKED


def test_durable_publication_claim_serializes_controller_cancellation(
    tmp_path, monkeypatch
) -> None:
    """A broker without the local fence still observes publication-first success."""
    _database, _config, entry = _entry(tmp_path, monkeypatch)
    entered = threading.Event()
    release = threading.Event()
    cancel_started = threading.Event()
    cancel_finished = threading.Event()
    outcomes: list[str] = []

    def callback() -> None:
        entered.set()
        assert release.wait(5), "test never released durable publication"
        entry.close("succeeded")

    publisher = threading.Thread(
        target=lambda: entry.fence.publish("durable terminal publication", callback)
    )
    publisher.start()
    assert entered.wait(5), "publication never acquired its durable claim"

    def cancel_from_controller() -> None:
        cancel_started.set()
        outcomes.append(
            entry.session.broker.parent_run_controller.cancel_by_operation_id(
                OWNER, entry.session.operation_id
            )
        )
        cancel_finished.set()

    canceller = threading.Thread(target=cancel_from_controller)
    canceller.start()
    assert cancel_started.wait(5)
    assert not cancel_finished.wait(0.1), "durable cancellation bypassed the claim"
    release.set()
    publisher.join(5)
    canceller.join(5)

    assert not publisher.is_alive() and not canceller.is_alive()
    assert outcomes == ["succeeded"]
    assert entry.session.broker.store.receipt(entry.session.operation_id)["outcome"] == "succeeded"


def test_final_preview_publication_settles_success_before_disconnect_can_cancel(
    tmp_path, monkeypatch
) -> None:
    """Publication-first cannot return success over a parent cancelled in the gap."""
    from holdspeak.web.routes.dictation import _helpers

    database = Database(tmp_path / "publication-terminal-race.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: database)
    _configure(database)
    config = Config()
    config.dictation.pipeline.enabled = False
    # Exercise the admitted publication/terminal election even though the helper
    # takes its deterministic pipeline-disabled branch.
    monkeypatch.setattr(
        "holdspeak.speech_session.pipeline_provider_capabilities",
        lambda _snapshot: (CAPABILITY_INTENT_CLASSIFY,),
    )
    entry = SpeechEntry(
        admit_text_entry_session(
            principal=OWNER,
            insertion_aim=AIM_JOURNAL_REPLAY,
            config_snapshot=config,
            registry_snapshot=database,
        )
    )
    monkeypatch.setattr(
        _helpers,
        "_open_text_entry",
        lambda _request, _aim, **_kwargs: (config, entry),
    )
    monkeypatch.setattr(_helpers, "_DISCONNECT_POLL_SECONDS", 0)

    publication_entered = threading.Event()
    cancellation_started = threading.Event()
    release_publication = threading.Event()
    original_cancel = SpeechEntry.cancel

    def observed_cancel(candidate: SpeechEntry) -> str:
        cancellation_started.set()
        return original_cancel(candidate)

    monkeypatch.setattr(SpeechEntry, "cancel", observed_cancel)

    class Journal:
        def record(self, *_args: Any, **_kwargs: Any) -> Any:
            publication_entered.set()
            assert release_publication.wait(5), "publication was never released"
            return SimpleNamespace(id=17)

    class Request:
        async def is_disconnected(self) -> bool:
            return publication_entered.is_set()

    def work(config_snapshot: Any, owned: SpeechEntry) -> dict[str, Any]:
        return _helpers._run_dictation_dry_run_text(
            "PUBLICATION_TERMINAL_RACE_TEXT",
            None,
            suggestions={},
            config_snapshot=config_snapshot,
            admission=owned.provider,
            fence=owned.fence,
            terminal_entry=owned,
            journal=Journal(),
        )

    def release_after_cancel_contends() -> None:
        assert publication_entered.wait(5), "publication never won"
        assert cancellation_started.wait(5), "disconnect never attempted cancellation"
        release_publication.set()

    releaser = threading.Thread(target=release_after_cancel_contends)
    releaser.start()
    payload = asyncio.run(
        _helpers._run_cancellable_entry(Request(), AIM_JOURNAL_REPLAY, work)
    )
    releaser.join(5)

    assert not releaser.is_alive()
    assert cancellation_started.is_set()
    assert payload["journal_id"] == 17
    assert payload["egress_boundary"] == "local"
    assert "session_terminal" not in payload
    assert entry.terminal == "succeeded"
    assert entry.session.broker.store.receipt(entry.session.operation_id)["outcome"] == "succeeded"


def test_cli_derives_the_provided_bearer_against_the_hub_credential_only(
    monkeypatch
) -> None:
    """The CLI cannot compare config to itself or mint an owner for missing input."""
    config = Config()
    config.meeting.web_auth_token = "hub-owner-token"

    monkeypatch.delenv("HOLDSPEAK_TOKEN", raising=False)
    assert cli_owner_principal(config) is None

    monkeypatch.setenv("HOLDSPEAK_TOKEN", "wrong-token")
    assert cli_owner_principal(config) is None

    monkeypatch.setenv("HOLDSPEAK_TOKEN", "hub-owner-token")
    assert cli_owner_principal(config) == Principal(PrincipalKind.OWNER, "owner-session")


def test_top_level_cli_threads_one_snapshot_through_auth_and_execution(
    monkeypatch,
) -> None:
    """Authentication and execution cannot observe different configuration reads."""
    import holdspeak.main as main_module

    config = _provider_config()
    config.meeting.web_auth_token = "one-snapshot-owner-token"
    monkeypatch.setenv("HOLDSPEAK_TOKEN", "one-snapshot-owner-token")
    loads: list[Config] = []

    def load(_cls) -> Config:
        loads.append(config)
        return config

    seen: dict[str, Any] = {}

    def dispatch(args: Any, **kwargs: Any) -> int:
        seen["action"] = args.dictation_action
        seen.update(kwargs)
        return 0

    monkeypatch.setattr(main_module.Config, "load", classmethod(load))
    monkeypatch.setattr(main_module, "run_dictation_command", dispatch)
    monkeypatch.setattr(
        "sys.argv", ["holdspeak", "dictation", "dry-run", "one snapshot"]
    )

    with pytest.raises(SystemExit) as exited:
        main_module.main()

    assert exited.value.code == 0
    assert loads == [config]
    assert seen["action"] == "dry-run"
    assert seen["config_snapshot"] is config
    assert seen["principal"] == Principal(PrincipalKind.OWNER, "owner-session")


def test_frozen_endpoint_construction_ignores_mutated_runtime_placement() -> None:
    """Construction itself receives the admitted endpoint/model/key, not current config."""
    from holdspeak.plugins.dictation.assembly import _try_build_runtime

    config = _provider_config()
    config.dictation.runtime.backend = "llama_cpp"
    config.dictation.runtime.mlx_model = "/mutable-before"
    config.dictation.runtime.llama_cpp_model_path = "/mutable-before.gguf"
    config.dictation.runtime.warm_on_start = True
    frozen = SimpleNamespace(
        engine="openai_compatible",
        endpoint="https://frozen.example.test/v1",
        model="frozen-model",
        secret_slot="FROZEN_KEY_SLOT",
        node="",
    )

    class FrozenPlan:
        def deployment(self, revision: str) -> Any:
            assert revision == "revision-frozen"
            return frozen

    class Admission:
        plan = FrozenPlan()

        def declares(self, capability: str) -> bool:
            return capability == CAPABILITY_REWRITE

        def revision(self, capability: str) -> str:
            assert capability == CAPABILITY_REWRITE
            return "revision-frozen"

    # This is the hostile timing: the same mutable config is changed after
    # admission, before `_try_build_runtime` receives it.
    config.dictation.runtime.backend = "mlx"
    config.dictation.runtime.mlx_model = "/retargeted-after-admission"
    config.dictation.runtime.llama_cpp_model_path = "/retargeted-after-admission.gguf"
    seen: dict[str, Any] = {}

    class Runtime:
        backend = "openai_compatible"

    def factory(**kwargs: Any) -> Runtime:
        seen.update(kwargs)
        return Runtime()

    runtime, status, _detail = _try_build_runtime(
        config.dictation, factory, Admission()
    )

    assert isinstance(runtime, Runtime)
    assert status == "loaded"
    assert seen["backend"] == "openai_compatible"
    assert seen["endpoint_base_url"] == "https://frozen.example.test/v1"
    assert seen["endpoint_model"] == "frozen-model"
    assert seen["endpoint_api_key_env"] == "FROZEN_KEY_SLOT"
    assert seen["warm_on_start"] is False


def test_keyless_frozen_endpoint_does_not_reintroduce_a_profile_secret_slot() -> None:
    """A blank frozen slot means no credential, even if the profile id has a slot."""
    from holdspeak.plugins.dictation.assembly import _try_build_runtime

    config = _provider_config()
    frozen = SimpleNamespace(
        engine="openai_compatible",
        endpoint="https://keyless.example.test/v1",
        model="keyless-model",
        secret_slot="",
        destination_id="keyless-profile",
        node="",
    )

    class FrozenPlan:
        def deployment(self, _revision: str) -> Any:
            return frozen

    class Admission:
        plan = FrozenPlan()

        def declares(self, capability: str) -> bool:
            return capability == CAPABILITY_REWRITE

        def revision(self, _capability: str) -> str:
            return "revision-keyless"

    seen: dict[str, Any] = {}

    class Runtime:
        backend = "openai_compatible"

    def factory(**kwargs: Any) -> Runtime:
        seen.update(kwargs)
        return Runtime()

    runtime, status, _detail = _try_build_runtime(
        config.dictation, factory, Admission()
    )

    assert isinstance(runtime, Runtime)
    assert status == "loaded"
    assert seen["endpoint_api_key_env"] == ""


def test_local_construction_freezes_the_dictation_artifact_not_mutated_config(
    tmp_path, monkeypatch
) -> None:
    """A blank profile still freezes the dictation model, not the meeting dial."""
    from holdspeak.plugins.dictation.assembly import _try_build_runtime

    database = Database(tmp_path / "local-artifact.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: database)
    _configure(database)
    config = Config()
    config.dictation.pipeline.enabled = True
    config.dictation.pipeline.stages = ["intent-router"]
    config.dictation.runtime.profile_id = ""
    config.dictation.runtime.backend = "llama_cpp"
    config.dictation.runtime.llama_cpp_model_path = "/frozen-dictation-model.gguf"
    config.meeting.intel_realtime_model = "/unrelated-meeting-model.gguf"
    monkeypatch.setattr(Config, "load", classmethod(lambda _cls: config))
    entry = SpeechEntry(
        admit_text_entry_session(
            principal=OWNER,
            insertion_aim=AIM_BROWSER_REHEARSE,
            config_snapshot=config,
            registry_snapshot=database,
        )
    )
    revision = entry.plan.deployment(entry.plan.primary(CAPABILITY_INTENT_CLASSIFY))
    assert revision.model_path == "/frozen-dictation-model.gguf"

    config.dictation.runtime.llama_cpp_model_path = "/retargeted-after-admission.gguf"
    seen: dict[str, Any] = {}

    class Runtime:
        backend = "llama_cpp"
        model_path = "/frozen-dictation-model.gguf"

    def factory(**kwargs: Any) -> Runtime:
        seen.update(kwargs)
        return Runtime()

    try:
        runtime, status, _detail = _try_build_runtime(
            config.dictation, factory, entry.provider
        )
    finally:
        entry.cancel()

    assert isinstance(runtime, Runtime)
    assert status == "loaded"
    assert seen["llama_cpp_model_path"] == "/frozen-dictation-model.gguf"


def test_concrete_local_revision_rejects_a_different_loader_on_the_same_path() -> None:
    from holdspeak.speech_session.revision_target import agrees

    runtime = SimpleNamespace(backend="llama_cpp", model_path="/models/shared")
    revision = SimpleNamespace(
        engine="mlx", model_path="/models/shared", endpoint="", model="shared"
    )

    assert agrees(runtime, revision) is False


def test_generic_local_profile_binds_an_existing_dotted_mlx_directory(tmp_path) -> None:
    """An onDevice profile says `local`; artifact shape freezes the real loader."""
    from holdspeak.plugins.dictation.assembly import _frozen_local_target

    artifact = tmp_path / "Qwen3.5-8B-MLX-4bit"
    artifact.mkdir()

    backend, mlx_model, llama_model = _frozen_local_target(
        "local", str(artifact), CAPABILITY_REWRITE
    )

    assert backend == "mlx"
    assert mlx_model == str(artifact)
    assert llama_model == ""


def test_local_identity_preserves_a_dotted_mlx_artifact_name() -> None:
    """The frozen engine, not a filename suffix guess, identifies an MLX model."""
    from holdspeak.speech_session.plan import dictation_local_deployment_identity

    artifact = "~/Models/mlx/Qwen3.5-8B-MLX-4bit"
    identity = dictation_local_deployment_identity(
        {
            "runtime_backend": "mlx",
            "runtime_mlx_model": artifact,
            "runtime_llama_cpp_model_path": "/unused.gguf",
        }
    )

    assert identity is not None
    assert identity.engine == "mlx"
    assert identity.model_path == artifact
    assert identity.model == "Qwen3.5-8B-MLX-4bit"


@pytest.mark.parametrize(
    ("system", "machine", "mlx_present", "expected_engine", "expected_artifact"),
    [
        pytest.param(
            "Darwin",
            "arm64",
            True,
            "mlx",
            "/frozen-auto-mlx",
            id="apple-mlx",
        ),
        pytest.param(
            "Darwin",
            "arm64",
            False,
            "llama_cpp",
            "/frozen-auto-llama.gguf",
            id="apple-import-failure-falls-back",
        ),
        pytest.param(
            "Linux",
            "x86_64",
            False,
            "llama_cpp",
            "/frozen-auto-llama.gguf",
            id="llama-fallback",
        ),
    ],
)
def test_auto_local_identity_freezes_one_deterministic_engine_and_artifact(
    system,
    machine,
    mlx_present,
    expected_engine,
    expected_artifact,
    monkeypatch,
) -> None:
    """`auto` is resolved once in the plan and construction cannot choose again."""
    import importlib
    import platform

    from holdspeak.speech_session.plan import dictation_local_deployment_identity

    monkeypatch.setattr(platform, "system", lambda: system)
    monkeypatch.setattr(platform, "machine", lambda: machine)

    real_import = importlib.import_module

    def import_optional(name, package=None):
        if name == "mlx_lm":
            if mlx_present:
                return object()
            raise ImportError("mlx_lm import failed")
        return real_import(name, package)

    monkeypatch.setattr(importlib, "import_module", import_optional)
    identity = dictation_local_deployment_identity(
        {
            "runtime_backend": "auto",
            "runtime_mlx_model": "/frozen-auto-mlx",
            "runtime_llama_cpp_model_path": "/frozen-auto-llama.gguf",
        }
    )

    assert identity is not None
    assert identity.engine == expected_engine
    assert identity.model_path == expected_artifact


def test_provider_capability_map_plans_target_detection_as_rewrite_and_no_whisper() -> None:
    """The model target detector physically calls `rewrite`, not `classify`."""
    config = Config()
    config.dictation.pipeline.enabled = True
    config.dictation.pipeline.stages = ["kb-enricher"]
    config.dictation.pipeline.target_detect_llm_enabled = True

    assert pipeline_provider_capabilities(config) == (CAPABILITY_REWRITE,)
    assert CAPABILITY_WHISPER_TRANSCRIBE not in pipeline_provider_capabilities(config)
    assert CAPABILITY_WHISPER_PRELOAD not in pipeline_provider_capabilities(config)


class _FatalStage:
    id = "fatal-stage"
    requires_llm = True

    def run(self, _utterance: Utterance, _previous: list[Any]) -> Any:
        raise SpeechSessionRefused("speech_child_budget_exhausted")


class _OrdinaryFailureStage:
    id = "ordinary-stage"
    requires_llm = False

    def run(self, _utterance: Utterance, _previous: list[Any]) -> Any:
        raise RuntimeError("bad plugin stage")


def test_fatal_speech_signals_escape_but_ordinary_stage_failures_are_degraded() -> None:
    """DIR-F-003 remains for plugin errors, never for denied provider authority."""
    utterance = Utterance(
        raw_text="SIDE_DOOR_PIPELINE_TEXT",
        audio_duration_s=0.0,
        transcribed_at=datetime.now(),
    )

    with pytest.raises(SpeechSessionRefused) as fatal:
        DictationPipeline([_FatalStage()]).run(utterance)
    assert fatal.value.reason == "speech_child_budget_exhausted"

    ordinary = DictationPipeline([_OrdinaryFailureStage()]).run(utterance)
    assert ordinary.final_text == utterance.raw_text
    assert ordinary.short_circuited is True
    assert ordinary.stage_results[0].metadata == {"failed": True}
    assert ordinary.warnings == ["ordinary-stage: RuntimeError: bad plugin stage"]


def test_model_target_detector_preserves_provider_failure_reason() -> None:
    """The target-profile broad catch cannot turn a provider refusal into success."""
    from holdspeak.target_profile import apply_model_assisted_target, detect_target_profile

    class RefusingRuntime:
        def rewrite(self, *_args: Any, **_kwargs: Any) -> str:
            raise SpeechProviderFailure(
                "dictation.rewrite", reason="provider_budget_refused"
            )

    with pytest.raises(SpeechProviderFailure) as failure:
        apply_model_assisted_target(
            detect_target_profile({"app": "Safari"}),
            runtime=RefusingRuntime(),
            text="SIDE_DOOR_TARGET_TEXT",
            enabled=True,
            below_confidence=0.8,
        )
    assert failure.value.contract == "dictation.rewrite"
    assert failure.value.reason == "provider_budget_refused"


def test_cancel_after_text_processing_prevents_the_voice_command_effect(
    tmp_path, monkeypatch
) -> None:
    """The live command gap is fenced after `text_processor.process`, not before it."""
    from holdspeak.runtime.dictation_capture import DictationCaptureMixin

    _database, _config, entry = _entry(tmp_path, monkeypatch)
    effects: list[str] = []

    class Transcriber:
        def transcribe(self, _audio: Any, *, admission: Any) -> str:
            assert admission is not None
            return "voice command"

    class CancellingProcessor:
        def process(self, text: str) -> str:
            entry.fence.cancel()
            return text

    capture = object.__new__(DictationCaptureMixin)
    capture.transcription_lock = threading.RLock()
    capture.text_processor = CancellingProcessor()
    capture._ensure_transcriber_loaded = lambda: Transcriber()
    capture._maybe_dispatch_voice_command = lambda *_args: effects.append("typed")
    capture._set_voice_state = lambda *_args, **_kwargs: None

    try:
        assert capture._transcribe_and_type(np.zeros(1600), session=entry.session) is None
    finally:
        entry.cancel()
    assert effects == []


@pytest.mark.parametrize("preview", [True, False], ids=["preview", "desktop-typing"])
def test_cancel_before_live_publication_suppresses_preview_typing_and_callback(
    preview, tmp_path, monkeypatch
) -> None:
    """The final live handoff is a callback election, never check-then-effect."""
    from holdspeak.runtime.dictation_capture import DictationCaptureMixin

    _database, config, entry = _entry(tmp_path, monkeypatch)
    config.dictation.preview_before_type = preview
    effects: list[str] = []
    callbacks: list[str] = []

    class Transcriber:
        def transcribe(self, _audio: Any, *, admission: Any) -> str:
            assert admission is not None
            return "processed text"

    capture = object.__new__(DictationCaptureMixin)
    capture.transcription_lock = threading.RLock()
    capture.state_lock = threading.RLock()
    capture.runtime_status = {}
    capture.config = config
    capture.typer = object()
    capture.text_processor = SimpleNamespace(process=lambda text: text)
    capture._ensure_transcriber_loaded = lambda: Transcriber()
    capture._maybe_dispatch_voice_command = lambda *_args: None
    capture._set_runtime_activity = lambda *_args, **_kwargs: None
    capture._set_voice_state = lambda *_args, **_kwargs: None
    capture._mark_first_dictation = lambda: None
    capture._arm_dictation_preview = lambda _text: effects.append("preview")
    capture._try_tmux_agent_reply = lambda *_args: False
    capture._paste_target_profile = lambda *_args: None

    def cancel_after_pipeline(*_args: Any, **_kwargs: Any) -> str:
        entry.fence.cancel()
        return "processed text"

    capture._maybe_run_dictation_pipeline = cancel_after_pipeline
    monkeypatch.setattr(
        "holdspeak.desktop_typing.type_text_from_owner_gesture",
        lambda *_args, **_kwargs: effects.append("typed"),
    )

    try:
        assert capture._transcribe_and_type(
            np.zeros(1600),
            session=entry.session,
            on_complete=lambda text: callbacks.append(text),
        ) is None
    finally:
        entry.cancel()

    assert effects == []
    assert callbacks == []
    assert capture.runtime_status.get("last_transcription") is None


def test_entry_exposes_indeterminate_terminal_state_instead_of_a_success_string() -> None:
    """Terminal bookkeeping uncertainty remains visible to every route/CLI owner."""
    plan = SimpleNamespace(insertion_aim=AIM_BROWSER_REHEARSE)

    class Fence:
        def __init__(self) -> None:
            self.election = threading.RLock()
            self.cancel_calls = 0

        def cancel(self) -> None:
            self.cancel_calls += 1

    class UnrecordableSession:
        def __init__(self) -> None:
            self.plan = plan
            self.fence = Fence()
            self.close_calls = 0
            self.cancel_calls = 0

        def provider(self) -> Any:
            return SimpleNamespace(fence=self.fence)

        def close(self, _outcome: str) -> str:
            self.close_calls += 1
            return OUTCOME_INDETERMINATE

        def cancel_and_close(self) -> str:
            self.cancel_calls += 1
            return OUTCOME_INDETERMINATE

        @property
        def operation_id(self) -> str:
            return "unrecordable-session"

    session = UnrecordableSession()
    entry = SpeechEntry(session)
    assert entry.close("succeeded") == OUTCOME_INDETERMINATE
    assert entry.indeterminate is True
    # Unknown persistence is not terminal ownership: later cancellation must
    # fence/retry rather than becoming a permanent `_closed` no-op.
    assert entry.cancel() == OUTCOME_INDETERMINATE
    assert session.close_calls == 1
    assert session.cancel_calls == 1
    assert session.fence.cancel_calls == 2
