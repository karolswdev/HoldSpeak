"""Review 10b: host binding, every native edge, and durable uncertain removal."""
from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import _boot
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition
from holdspeak.services.errors import ServiceError

OWNER = Principal(PrincipalKind.OWNER, "review-owner")
AGENT = Principal(PrincipalKind.AGENT, "review-agent")


class Native:
    def __init__(self, *, failure=None):
        self.calls = []
        self.failure = failure

    def __call__(self, argv, *args, **kwargs):
        self.calls.append(list(argv))
        if argv[1:3] == ["auth", "status"]:
            host = argv[argv.index("--hostname") + 1] if "--hostname" in argv else "enterprise.example"
            return subprocess.CompletedProcess(argv, 0, f"Logged in to {host} account alice (keyring)", "")
        if argv[1:3] == ["auth", "logout"] and self.failure:
            raise self.failure
        return subprocess.CompletedProcess(argv, 0, "[]", "")


@pytest.fixture
def hub(tmp_path, monkeypatch):
    from holdspeak.db import reset_database
    result = _boot(tmp_path, monkeypatch)
    native = Native()
    monkeypatch.setattr(result.root.github_provider, "_runner", native)
    checked = check(result)
    assert checked.status_code == 200, checked.text
    assert checked.json()["state"] == "connected", checked.text
    result.native = native
    yield result
    reset_database()
    composition.install(composition.bare(label="pytest"))


def check(hub, host="github.com"):
    return hub.client.post("/api/connections/github/recheck", json={"ref": host})


def body(hub, key="remove"):
    row = hub.db.automations.get_provider_connection("wpc_github")
    return {"connection_ref": row["external_connection_ref"], "expected_checked_at": row["last_checked_at"], "command_id": key}


def remove(hub, **changes):
    args = {**body(hub), **changes}
    return hub.client.request("DELETE", "/api/providers/github/connection", json=args)


def removed(hub):
    response = remove(hub)
    assert response.status_code == 200, response.text
    hub.native.calls.clear()


def refused(call):
    with pytest.raises(ServiceError) as error:
        call()
    assert error.value.code == "github_sign_in_required"


@pytest.mark.parametrize("read", ["discover", "validate", "pr"])
def test_removed_adapter_read_never_starts_gh(hub, read):
    removed(hub)
    adapter = hub.root.github_provider
    calls = {
        "discover": lambda: adapter.discover(OWNER),
        "validate": lambda: adapter.validate_repo(OWNER, "team/project"),
        "pr": lambda: adapter.pr_get(OWNER, owner_repo="team/project", number=1),
    }
    # The provider may map its named refusal to its existing error envelope.
    try:
        result = calls[read]()
        assert result.get("error_code") == "github_sign_in_required", result
    except ServiceError as error:
        assert error.code == "github_sign_in_required"
    assert hub.native.calls == []


@pytest.mark.parametrize("kind", ["pull_requests", "issues", "branch_ci"])
@pytest.mark.parametrize("source", ["direct", "adapter"])
def test_removed_direct_snapshot_never_starts_gh(hub, kind, source):
    from holdspeak.services.watch_sources import GitHubWatchSource
    removed(hub)
    query = {"repository": "team/project", "base": "main"}
    if source == "adapter":
        refused(lambda: hub.root.github_provider.snapshot(OWNER, {"query_kind": kind, "query": query}))
    else:
        refused(lambda: GitHubWatchSource(runner=hub.native).snapshot(OWNER, query_kind=kind, query=query))
    assert hub.native.calls == []


@pytest.mark.parametrize("verb", ["poll", "view", "branch"])
def test_removed_pr_receipts_never_starts_gh(hub, verb):
    from holdspeak.delivery.pr_receipts import PrReceiptsService
    from test_pr_receipts import FakeSource, FakeRegistry, FakeWorktree
    source = FakeSource(worktrees=[FakeWorktree(path="/tmp/review-worktree", branch="main")])
    cache = PrReceiptsService(FakeRegistry(source), runner=hub.native, gh_available=lambda: True)
    removed(hub)
    if verb == "poll":
        call = lambda: cache._refresh_source(source, [])
    elif verb == "view":
        call = lambda: cache.view_pr(source.source_id, "https://github.com/team/project/pull/1")
    else:
        call = lambda: cache.list_branch_prs(source.source_id, "topic")
    refused(call)
    assert hub.native.calls == []


@pytest.mark.parametrize("verb", ["create", "merge"])
def test_removed_program_pr_write_never_starts_gh(hub, monkeypatch, verb):
    from holdspeak.services.program_runner import ProgramRunner
    from holdspeak.services.program_service import ProgramService
    runner = ProgramRunner(ProgramService(hub.db), run=hub.native)
    monkeypatch.setattr(runner, "_on_github", lambda _path: True)
    program = {"id": "p", "title": "Program", "repo_root": "/tmp/review-worktree"}
    step = {"id": "s", "title": "Step", "ordinal": 1, "worktree": "/tmp/review-worktree",
            "branch": "topic", "pr_number": 1}
    removed(hub)
    refused(lambda: runner.open_pr(program, step) if verb == "create" else runner.merge(program, step, by="owner"))
    assert not any(argv[0] == "gh" for argv in hub.native.calls)


def test_removed_clone_never_starts_gh(hub, tmp_path):
    from holdspeak.services.project_repository import ProjectRepositories
    repos = ProjectRepositories(store_path=tmp_path / "repos.json", clone_root=tmp_path / "clones", runner=hub.native)
    removed(hub)
    refused(lambda: repos.clone("team/project"))
    assert hub.native.calls == []


def test_removed_send_identity_probe_never_starts_gh(hub, monkeypatch):
    from holdspeak.services import channel_cli
    monkeypatch.setattr(channel_cli, "CLI_RUNNER", hub.native)
    removed(hub)
    refused(lambda: channel_cli.GitHubChannel.login("github.com", OWNER))
    assert hub.native.calls == []


def test_only_explicit_successful_owner_check_releases_removal(hub):
    removed(hub)
    adapter = hub.root.github_provider
    refused(lambda: adapter.connection_status(OWNER))
    with pytest.raises(ServiceError) as error:
        hub.root.connections_service.recheck(AGENT, "github", ref="github.com")
    assert error.value.code == "owner_required"
    assert hub.native.calls == []
    from holdspeak.db.github_access import removal
    assert removal(hub.db)
    result = check(hub)
    assert result.status_code == 200, result.text
    assert result.json()["state"] == "connected"
    assert removal(hub.db) is None
    assert adapter.discover(OWNER)["items"] == []
    assert any(argv[1:3] == ["repo", "list"] for argv in hub.native.calls)


def test_enterprise_check_saves_host_with_login_and_never_logs_out_github_com(hub):
    adapter = hub.root.github_provider
    checked = check(hub, "enterprise.example")
    assert checked.status_code == 200, checked.text
    saved = hub.db.automations.get_provider_connection("wpc_github")
    assert saved["external_connection_ref"] == "enterprise.example:alice"
    response = remove(hub)
    assert response.status_code == 200, response.text
    logout = next(argv for argv in hub.native.calls if argv[1:3] == ["auth", "logout"])
    assert logout[logout.index("--hostname") + 1] == "enterprise.example"
    assert logout[logout.index("--user") + 1] == "alice"
    assert all("--hostname" in argv for argv in hub.native.calls if argv[1:3] == ["auth", "status"])


def test_legacy_bare_login_never_logs_out_on_a_host_guess(hub):
    with hub.db._connection() as conn:
        conn.execute("UPDATE watch_provider_connections SET external_connection_ref='alice' WHERE id='wpc_github'")
    hub.native.calls.clear()
    response = remove(hub)
    assert response.status_code == 400, response.text
    assert response.json()["code"] == "github_connection_changed"
    assert hub.native.calls == []


def test_status_from_another_host_cannot_release_removal(hub, monkeypatch):
    removed(hub)
    monkeypatch.setattr(hub.root.github_provider, "_runner", lambda argv, **kw: subprocess.CompletedProcess(
        argv, 0, "Logged in to other.example account alice", ""))
    result = check(hub)
    assert result.json()["state"] != "connected"
    from holdspeak.db.github_access import removal
    assert removal(hub.db)
    refused(lambda: hub.root.github_provider.discover(OWNER))


def test_removal_claim_is_committed_before_native_logout(hub, monkeypatch):
    original = hub.native.__call__
    seen = []
    def run(argv, *args, **kwargs):
        if argv[1:3] == ["auth", "logout"]:
            assert hub.db.automations.get_provider_connection("wpc_github")["state"] == "owner_action_required"
            with sqlite3.connect(hub.db.db_path) as conn:
                seen.append(conn.execute("SELECT state FROM github_connection_removals").fetchone()[0])
            with pytest.raises(ServiceError) as error:
                hub.root.github_provider.connection_status(OWNER, hostname="github.com", _owner_check=True)
            assert error.value.code == "github_removal_pending"
        return original(argv, *args, **kwargs)
    monkeypatch.setattr(hub.root.github_provider, "_runner", run)
    response = remove(hub)
    assert response.status_code == 200, response.text
    assert seen == ["pending"]


def test_timeout_keeps_access_refused_and_requires_check_before_second_logout(hub):
    hub.native.failure = subprocess.TimeoutExpired(["gh", "auth", "logout"], 10)
    args = body(hub)
    response = hub.client.request("DELETE", "/api/providers/github/connection", json=args)
    assert response.status_code == 503, response.text
    assert hub.db.automations.get_provider_connection("wpc_github")["state"] == "owner_action_required"
    from holdspeak.db.github_access import removal
    assert removal(hub.db)["state"] == "uncertain"
    refused(lambda: hub.root.github_provider.discover(OWNER))
    again = hub.client.request("DELETE", "/api/providers/github/connection", json={**args, "command_id": "another"})
    assert again.json()["code"] == "github_sign_in_required", again.text
    assert len([a for a in hub.native.calls if a[1:3] == ["auth", "logout"]]) == 1
    hub.native.failure = None
    assert check(hub).status_code == 200
    stale = hub.client.request("DELETE", "/api/providers/github/connection", json={**args, "command_id": "stale"})
    assert stale.json()["code"] == "github_connection_changed"



def block_settlement(db):
    # Both implementations clear the saved account after logout. A real SQLite
    # failure there must roll back the receipt while retaining the prior claim.
    with db._connection() as conn:
        conn.execute("""CREATE TRIGGER fail_github_settlement BEFORE UPDATE ON watch_provider_connections
                        WHEN OLD.id='wpc_github' AND NEW.external_connection_ref=''
                        BEGIN SELECT RAISE(ABORT,'injected connection settlement failure'); END""")


def unblock_settlement(db):
    with db._connection() as conn:
        conn.execute("DROP TRIGGER fail_github_settlement")


def test_database_failure_after_logout_keeps_pending_claim_and_prevents_repeated_logout(hub):
    args = body(hub)
    block_settlement(hub.db)
    response = hub.client.request("DELETE", "/api/providers/github/connection", json=args)
    assert response.status_code == 500, response.text
    assert hub.db.automations.get_provider_connection("wpc_github")["state"] == "owner_action_required"
    from holdspeak.db.github_access import removal
    marker = removal(hub.db)
    assert marker["state"] == "pending"
    with hub.db._connection() as conn:
        assert conn.execute("SELECT 1 FROM kernel_receipts WHERE operation_id=?", (marker["operation_id"],)).fetchone() is None
    refused(lambda: hub.root.github_provider.discover(OWNER))
    unblock_settlement(hub.db)
    replay = hub.client.request("DELETE", "/api/providers/github/connection", json=args)
    assert replay.status_code != 200
    assert removal(hub.db)["state"] == "uncertain"
    assert len([a for a in hub.native.calls if a[1:3] == ["auth", "logout"]]) == 1


def test_startup_reconciles_pending_connection_and_receipt_together(hub):
    from holdspeak.db import Database
    from holdspeak.services.github_provider import GitHubProviderAdapter
    from holdspeak.services.steward_contract import StewardContract
    args = body(hub)
    block_settlement(hub.db)
    assert hub.client.request("DELETE", "/api/providers/github/connection", json=args).status_code == 500
    reopened = Database(hub.db.db_path)
    cold = GitHubProviderAdapter(db=reopened, runner=hub.native)
    refused(lambda: cold.discover(OWNER))
    from holdspeak.db.github_access import removal
    marker = removal(reopened)
    recovery = SimpleNamespace(_db=reopened, _run_for_operation=lambda _id: None, recover_on_startup=lambda: [])
    with pytest.raises(sqlite3.IntegrityError, match="injected connection settlement failure"):
        StewardContract.recover_admitted_on_startup(recovery)
    assert removal(reopened)["state"] == "pending"
    with reopened._connection() as conn:
        assert conn.execute("SELECT 1 FROM kernel_receipts WHERE operation_id=?", (marker["operation_id"],)).fetchone() is None
    unblock_settlement(reopened)
    StewardContract.recover_admitted_on_startup(recovery)
    assert removal(reopened)["state"] == "uncertain"
    with reopened._connection() as conn:
        assert conn.execute("SELECT 1 FROM kernel_receipts WHERE operation_id=?", (marker["operation_id"],)).fetchone()
        assert conn.execute("SELECT state FROM watch_provider_connections WHERE id='wpc_github'").fetchone()[0] == "owner_action_required"
    refused(lambda: cold.discover(OWNER))
    assert len([a for a in hub.native.calls if a[1:3] == ["auth", "logout"]]) == 1


def test_default_check_does_not_bind_another_hosts_login(hub, monkeypatch):
    monkeypatch.setattr(hub.root.github_provider, "_runner", lambda argv, **kw: subprocess.CompletedProcess(
        argv, 0, "Logged in to enterprise.example account alice", ""))
    checked = hub.root.github_provider.connection_status(OWNER)
    assert checked["state"] != "connected"
    hub.native.calls.clear()
    response = remove(hub)
    assert response.status_code != 200
    assert hub.native.calls == []


def test_existing_database_adds_removal_claim_without_changing_saved_account(hub):
    from holdspeak.db import Database
    saved = hub.db.automations.get_provider_connection("wpc_github")
    with hub.db._connection() as conn:
        conn.execute("DROP TABLE github_connection_removals")
    reopened = Database(hub.db.db_path)
    assert reopened.automations.get_provider_connection("wpc_github") == saved
    from holdspeak.db.github_access import removal
    assert removal(reopened) is None


@pytest.mark.parametrize("during_admission", [False, True])
def test_kernel_github_dispatch_rechecks_at_native_boundary(hub, during_admission):
    from holdspeak.kernel import runtime
    from holdspeak.kernel.subprocess_exec import EXECUTIONS, run_subprocess_operation
    broker = runtime._configure(hub.db)

    class RemoveBeforeDispatch:
        store = broker.store

        def __getattr__(self, name):
            return getattr(broker, name)

        def decide(self, *args, **kwargs):
            removed(hub)
            return broker.decide(*args, **kwargs)

    if not during_admission:
        removed(hub)
    refused(lambda: run_subprocess_operation(
        ["gh", "issue", "create", "--repo", "team/project", "--title", "Test"],
        connector_id="review-github-write", declared_permissions=("shell:exec",),
        principal=OWNER, broker=RemoveBeforeDispatch() if during_admission else broker, runner=hub.native))
    assert hub.native.calls == []
    if during_admission:
        evidence = list(EXECUTIONS._results.values())[-1]
        assert evidence["process_outcome"] == "not_started"
        assert broker.store.receipt(evidence["operation_id"])["outcome"] == "failed"



def test_owner_browser_signin_does_not_release_removal(hub, monkeypatch):
    import shutil
    from holdspeak import coder_factory
    from holdspeak.services.connection_signin_service import ConnectionSigninService, SignInRefused
    removed(hub)
    monkeypatch.setattr(shutil, "which", lambda binary: f"/bin/{binary}")
    spawned = []

    def spawn(name, *, command):
        spawned.append(command)
        return {"status": "spawned", "pane_id": "%77"}

    monkeypatch.setattr(coder_factory, "spawn", spawn)
    service = ConnectionSigninService(
        target_provider=lambda: SimpleNamespace(issue=lambda ref: {
            "status": "issued", "target_id": "term_review", "target_generation": "gen_review"}),
        runner=lambda argv, **kw: subprocess.CompletedProcess(argv, 0, "--web --hostname", ""))
    with pytest.raises(SignInRefused) as error:
        service.start_sign_in(AGENT, "github", "github.com")
    assert error.value.reason == "owner_required"
    assert spawned == []
    assert service.start_sign_in(OWNER, "github", "github.com")["status"] == "started"
    assert "auth login --web --hostname github.com" in spawned[0]
    refused(lambda: hub.root.github_provider.discover(OWNER))
    assert hub.native.calls == []
