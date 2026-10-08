"""PHILO-15 16 (B38): a Project knows its repository.

``POST /api/projects/{id}/repository`` is ``project.repository.register``: the
owner's press (the Door's GitHub row, the drawer's Register) names the
Project's repository. Owner only, one admitted kernel operation, one receipt;
nothing is cloned then. The first Hand to agent of an item in the Project
clones it (``project.repository.clone``: ``gh repo clone``, its own receipt)
into the HoldSpeak clone folder, registers the clone as a Delivery Source and
launches in a new worktree beside it. ``gh`` is a fake that makes a real git
clone on disk; git, the kernel and the launch path are real (tmux is the
launch rig's double).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_conductor_k6_agent_mcp import _client, _launch_credential, _reach, hub  # noqa: E402,F401
from tests.unit.test_agent_hand import OWNER, PROJECT, _rig, db  # noqa: E402,F401

from holdspeak.services import project_repository  # noqa: E402
from holdspeak.services.agent_hand_service import AgentHandRefused  # noqa: E402
from holdspeak.services.errors import ServiceError  # noqa: E402
from holdspeak.services.project_repository import (  # noqa: E402
    ProjectRepositories,
    normalize_repository,
)

REPO = "acme/railsproj"


def _git(path: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True)


class FakeGh:
    """``gh repo clone <owner/name> <dir> -- --quiet``: a real git repository
    on disk with the GitHub origin, as the real clone leaves it."""

    def __init__(self, *, fails: bool = False, origin: str | None = None) -> None:
        self.calls: list[list[str]] = []
        self.envs: list[dict[str, str]] = []
        self.fails = fails
        #: The origin the clone ends with (default: the URL it was given).
        self.origin = origin

    def __call__(self, argv: list[str], env: Any) -> Any:
        self.calls.append(list(argv))
        self.envs.append(dict(env))
        if self.fails:
            return SimpleNamespace(returncode=1, stdout="", stderr="repository not found")
        assert argv[:3] == ["gh", "repo", "clone"], argv
        url, target = argv[3], Path(argv[4])
        target.mkdir(parents=True)
        (target / "README.md").write_text("# rehearsal\n", encoding="utf-8")
        _git(target, "init", "-b", "main")
        _git(target, "config", "user.email", "test@example.test")
        _git(target, "config", "user.name", "Test")
        _git(target, "add", "-A")
        _git(target, "commit", "-m", "seed")
        _git(target, "remote", "add", "origin", self.origin or f"{url}.git")
        return SimpleNamespace(returncode=0, stdout="", stderr="")


# ── the name ────────────────────────────────────────────────────────


@pytest.mark.parametrize("given, want", [
    ("acme/railsproj", "acme/railsproj"),
    (" acme/railsproj/ ", "acme/railsproj"),
    ("https://github.com/acme/railsproj.git", "acme/railsproj"),
    ("git@github.com:acme/railsproj.git", "acme/railsproj"),
    ("karolswdev/holdspeak-dayone-rehearsal-1558", "karolswdev/holdspeak-dayone-rehearsal-1558"),
])
def test_the_repository_is_named_owner_slash_name(given: str, want: str) -> None:
    assert normalize_repository(given) == want


@pytest.mark.parametrize("bad", ["", "railsproj", "acme/", "a/b/c", "../etc", "acme/..", "-x/y"])
def test_a_bad_name_is_refused_by_name(bad: str) -> None:
    with pytest.raises(ServiceError) as exc:
        normalize_repository(bad)
    assert exc.value.code == "repository_invalid"


def test_the_clone_folder_is_per_repository(tmp_path: Path) -> None:
    repos = ProjectRepositories(store_path=tmp_path / "r.json", clone_root=tmp_path / "clones")
    assert repos.clone_path(REPO) == tmp_path / "clones" / "acme" / "railsproj" / "railsproj"


# ── the register operation (the hub, the kernel, the route) ─────────


def _project(hub: Any, project_id: str = PROJECT, name: str = "Payments ledger cutover") -> None:
    with hub.db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES (?, ?)", (project_id, name))


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "home"
    path.mkdir()
    monkeypatch.setenv("HOME", str(path))
    return path


def test_the_owner_registers_with_a_receipt_and_nothing_is_cloned(hub, home, monkeypatch) -> None:
    gh = FakeGh()
    monkeypatch.setattr(project_repository, "_gh_clone", gh)
    _project(hub)
    resp = hub.client.post(f"/api/projects/{PROJECT}/repository", json={"repository": REPO})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert (body["repository"], body["registered"], body["cloned"]) == (REPO, True, False)
    assert body["receipt"]["outcome"] == "succeeded" and body["operation_id"]
    assert gh.calls == []  # registered, never cloned at create time
    stored = ProjectRepositories().get(PROJECT)
    assert stored is not None and stored["repository"] == REPO
    assert (home / ".holdspeak" / "project_repositories.json").exists()

    read = hub.client.get(f"/api/projects/{PROJECT}/repository").json()
    assert (read["repository"], read["registered"], read["cloned"], read["host"]) == (REPO, True, False, "github.com")


def test_a_bad_name_or_an_unknown_project_is_refused_with_a_receipt(hub, home) -> None:
    _project(hub)
    bad = hub.client.post(f"/api/projects/{PROJECT}/repository", json={"repository": "not a repo"})
    assert bad.status_code == 400, bad.text
    assert bad.json()["code"] == "repository_invalid" and bad.json()["receipt"]["outcome"] == "repository_invalid"
    unknown = hub.client.post("/api/projects/proj-nope/repository", json={"repository": REPO})
    assert unknown.status_code == 404, unknown.text
    assert unknown.json()["code"] == "project_unknown"
    assert ProjectRepositories().get(PROJECT) is None


def test_an_agent_never_registers(hub, home) -> None:
    _project(hub)
    _reach(hub, False)
    agent = _client(hub, _launch_credential().token)
    assert agent.post(f"/api/projects/{PROJECT}/repository", json={"repository": REPO}).status_code == 403
    assert ProjectRepositories().get(PROJECT) is None


def test_a_room_watch_with_no_registration_is_named_for_the_register_verb(hub, home) -> None:
    import json

    _project(hub)
    with hub.db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches (id, connector_id, query_kind, query_json, project_id) "
            "VALUES ('w1', 'gh', 'pulls', ?, ?)", (json.dumps({"repository": REPO}), PROJECT),
        )
    read = hub.client.get(f"/api/projects/{PROJECT}/repository").json()
    assert (read["registered"], read["repository"], read["watched"]) == (False, None, [REPO])


def test_the_descriptor_is_owner_only_http_only_and_admitted() -> None:
    from holdspeak.agent_operations import PROJECT_REPOSITORY_REGISTER as op
    from holdspeak.kernel.project import OWNER_ONLY_OPERATIONS, REPOSITORY_ADMITTED

    assert op.owner_only and op.owner_press and op.admission.rule == "admitted" and op.admission.enforced
    assert op.exposure == ("http:POST /api/projects/{project_id}/repository",)
    assert REPOSITORY_ADMITTED == {"project.repository.register", "project.repository.clone"}
    assert REPOSITORY_ADMITTED <= OWNER_ONLY_OPERATIONS


# ── the lazy clone on the first hand ────────────────────────────────


def _registered_rig(tmp_path: Path, db: Any, monkeypatch: pytest.MonkeyPatch, gh: FakeGh) -> Any:
    rig = _rig(tmp_path, db, monkeypatch)
    # The Project's name no longer matches the rig's clone: only the
    # registration names its repository.
    with db._connection() as conn:
        conn.execute("UPDATE projects SET name='Payments ledger cutover' WHERE id=?", (PROJECT,))
    rig.hand.repositories = ProjectRepositories(
        store_path=tmp_path / "project_repositories.json", clone_root=tmp_path / "clones", runner=gh,
    )
    project_repository.register(db, rig.hand.repositories, PROJECT, REPO)
    return rig


def test_the_first_hand_clones_the_registered_repository_with_its_receipt(tmp_path, db, monkeypatch) -> None:
    gh = FakeGh()
    rig = _registered_rig(tmp_path, db, monkeypatch, gh)
    clone = tmp_path / "clones" / "acme" / "railsproj" / "railsproj"
    try:
        result = rig.hand.hand(OWNER, "action", "ai_1", profile="claude-default")
    finally:
        rig.tmux.ended = True
    assert result["status"] == "launched", result
    assert gh.calls == [["gh", "repo", "clone", f"https://github.com/{REPO}", str(clone), "--", "--quiet"]]
    assert gh.envs[0]["GIT_TERMINAL_PROMPT"] == "0" and gh.envs[0]["GH_HOST"] == "github.com"
    assert result["clone"]["repository"] == REPO and result["clone"]["host"] == "github.com"
    assert result["clone"]["receipt"]["outcome"] == "succeeded" and result["clone"]["operation_id"]
    # The clone is a Delivery Source; the worktree is its sibling.
    source = rig.registry.get(result["source_id"])
    assert source is not None and Path(source.primary_path) == clone.resolve()
    assert (clone.parent / "hs-action-ai_1" / ".git").exists()
    record = rig.hand.repositories.get(PROJECT)
    assert record["source_id"] == source.source_id and record["cloned_at"]
    state = rig.hand.repository_state(OWNER, PROJECT, registry=rig.registry)
    assert (state["repository"], state["cloned"]) == (REPO, True)


def test_a_second_hand_uses_the_clone_and_clones_nothing(tmp_path, db, monkeypatch) -> None:
    gh = FakeGh()
    rig = _registered_rig(tmp_path, db, monkeypatch, gh)
    try:
        first = rig.hand.hand(OWNER, "action", "ai_1")
        second = rig.hand.hand(OWNER, "decision", "d1")
    finally:
        rig.tmux.ended = True
    assert first["status"] == second["status"] == "launched", (first, second)
    assert len(gh.calls) == 1
    assert "clone" not in second and second["source_id"] == first["source_id"]


def test_a_failed_clone_refuses_the_hand_by_name_with_a_receipt(tmp_path, db, monkeypatch) -> None:
    rig = _registered_rig(tmp_path, db, monkeypatch, FakeGh(fails=True))
    with pytest.raises(AgentHandRefused) as exc:
        rig.hand.hand(OWNER, "action", "ai_1")
    assert exc.value.reason == "clone_failed"
    assert exc.value.context["receipt"]["outcome"] == "clone_failed"
    assert rig.tmux.calls == []
    assert rig.hand.repositories.get(PROJECT).get("source_id") is None


def test_the_preview_names_the_clone_never_no_repository(tmp_path, db, monkeypatch) -> None:
    from holdspeak.services.agent_hand_preview import LaunchReads, preview_hand

    gh = FakeGh()
    rig = _registered_rig(tmp_path, db, monkeypatch, gh)
    reads = LaunchReads(
        profiles_path=tmp_path / "profiles.json", registry_path=tmp_path / "sources.json",
        ledger_path=tmp_path / "launches.json", which=lambda name: f"/bin/{name}",
        runner=lambda argv: SimpleNamespace(returncode=1),
    )
    preview = preview_hand(rig.hand, OWNER, "action", "ai_1", profile="codex-default", reads=reads)
    assert preview["refused"] == [], preview["refused"]
    assert preview["clone"]["repository"] == REPO and preview["clone"]["host"] == "github.com"
    assert preview["repo"] is None and gh.calls == []  # the preview clones nothing


def test_a_watched_repository_nobody_registered_is_named(tmp_path, db, monkeypatch) -> None:
    import json

    from holdspeak.services.agent_hand_preview import LaunchReads, preview_hand

    rig = _rig(tmp_path, db, monkeypatch)
    rig.hand.repositories = ProjectRepositories(
        store_path=tmp_path / "project_repositories.json", clone_root=tmp_path / "clones", runner=FakeGh(),
    )
    with db._connection() as conn:
        conn.execute("UPDATE projects SET name='Payments ledger cutover' WHERE id=?", (PROJECT,))
        conn.execute(
            "INSERT INTO connector_watches (id, connector_id, query_kind, query_json, project_id) "
            "VALUES ('w1', 'gh', 'pulls', ?, ?)", (json.dumps({"repository": "acme/other"}), PROJECT),
        )
    with pytest.raises(AgentHandRefused) as exc:
        rig.hand.hand(OWNER, "action", "ai_1")
    assert exc.value.reason == "repository_not_registered"
    reads = LaunchReads(
        profiles_path=tmp_path / "profiles.json", registry_path=tmp_path / "sources.json",
        ledger_path=tmp_path / "launches.json", which=lambda name: f"/bin/{name}",
        runner=lambda argv: SimpleNamespace(returncode=1),
    )
    assert "repository_not_registered" in preview_hand(rig.hand, OWNER, "action", "ai_1", reads=reads)["refused"]


# ── Astra r1 on #1000 ───────────────────────────────────────────────


def test_an_enterprise_gh_host_cannot_move_the_clone(tmp_path, db, monkeypatch) -> None:
    """Finding 1: GH_HOST=ghe.example in the hub's environment; the clone still
    names https://github.com/<owner>/<name> and GH_HOST=github.com."""
    monkeypatch.setenv("GH_HOST", "ghe.example")
    gh = FakeGh()
    rig = _registered_rig(tmp_path, db, monkeypatch, gh)
    try:
        assert rig.hand.hand(OWNER, "action", "ai_1")["status"] == "launched"
    finally:
        rig.tmux.ended = True
    assert gh.calls[0][3] == f"https://github.com/{REPO}"
    assert gh.envs[0]["GH_HOST"] == "github.com"


def test_a_clone_from_another_host_is_refused_by_name(tmp_path, db, monkeypatch) -> None:
    """Finding 1: a clone whose origin is not the disclosed host is never used."""
    rig = _registered_rig(tmp_path, db, monkeypatch, FakeGh(origin=f"https://ghe.example/{REPO}.git"))
    with pytest.raises(AgentHandRefused) as exc:
        rig.hand.hand(OWNER, "action", "ai_1")
    assert exc.value.reason == "clone_host_mismatch"
    assert not (tmp_path / "clones" / "acme" / "railsproj" / "railsproj").exists()
    assert rig.tmux.calls == []


def _corrupt(path: Path) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"schema": 1, "projects": {"proj-x": {"repository": "acme/rail', encoding="utf-8")
    return path.read_bytes()


def test_a_store_that_cannot_be_read_is_not_read_and_never_overwritten(hub, home) -> None:
    """Finding 2, producer-backed: the hub's own routes over a corrupt file."""
    _project(hub)
    store = home / ".holdspeak" / "project_repositories.json"
    before = _corrupt(store)
    read = hub.client.get(f"/api/projects/{PROJECT}/repository").json()
    assert (read["store"], read["registered"], read["repository"]) == ("not_read", False, None)
    refused = hub.client.post(f"/api/projects/{PROJECT}/repository", json={"repository": REPO})
    assert refused.status_code == 409, refused.text
    body = refused.json()
    assert body["code"] == "repository_store_unreadable"
    assert body["receipt"]["outcome"] == "repository_store_unreadable"
    assert store.read_bytes() == before  # nothing written over it


def test_a_store_that_cannot_be_read_refuses_the_hand_and_names_it_in_the_preview(tmp_path, db, monkeypatch) -> None:
    from holdspeak.services.agent_hand_preview import LaunchReads, preview_hand

    rig = _registered_rig(tmp_path, db, monkeypatch, FakeGh())
    before = _corrupt(rig.hand.repositories.store_path)
    with pytest.raises(AgentHandRefused) as exc:
        rig.hand.hand(OWNER, "action", "ai_1")
    assert exc.value.reason == "repository_store_unreadable"
    reads = LaunchReads(
        profiles_path=tmp_path / "profiles.json", registry_path=tmp_path / "sources.json",
        ledger_path=tmp_path / "launches.json", which=lambda name: f"/bin/{name}",
        runner=lambda argv: SimpleNamespace(returncode=1),
    )
    assert preview_hand(rig.hand, OWNER, "action", "ai_1", reads=reads)["refused"] == ["repository_store_unreadable"]
    assert rig.hand.repositories.store_path.read_bytes() == before


def test_the_persisted_clone_receipt_names_the_host_and_repository(tmp_path, db, monkeypatch) -> None:
    """Finding 3: the durable kernel row and its receipt name the egress."""
    rig = _registered_rig(tmp_path, db, monkeypatch, FakeGh())
    try:
        result = rig.hand.hand(OWNER, "action", "ai_1")
    finally:
        rig.tmux.ended = True
    op = result["clone"]["operation_id"]
    with db._connection() as conn:
        row = conn.execute("SELECT name, target_ref, state FROM kernel_operations WHERE operation_id=?",
                           (op,)).fetchone()
    assert tuple(row) == ("project.repository.clone", f"repository:github.com/{REPO}", "succeeded")
    assert result["clone"]["receipt"]["result_ref"] == f"repository:github.com/{REPO}"


def test_a_clone_survives_a_launch_refusal(tmp_path, db, monkeypatch) -> None:
    """Finding 4: the clone happened; the launch then refuses; the refusal
    still names the clone (CLONED), and the next hand clones nothing."""
    gh = FakeGh()
    rig = _registered_rig(tmp_path, db, monkeypatch, gh)
    rig.hand._max_live = 0
    with pytest.raises(AgentHandRefused) as exc:
        rig.hand.hand(OWNER, "action", "ai_1")
    assert exc.value.reason == "launch_cap_reached"
    clone = exc.value.context["clone"]
    assert (clone["repository"], clone["state"], clone["host"]) == (REPO, "cloned", "github.com")
    assert clone["cloned_at"] and clone["receipt"]["outcome"] == "succeeded"
    assert len(gh.calls) == 1


def test_the_door_count_line_says_no_zero(monkeypatch) -> None:
    """Astra on #1000 (MISSED 4): the Door read "0 open PRs" at 393."""
    from holdspeak.services.project_door_service import ProjectDoorService

    door = ProjectDoorService()
    monkeypatch.setattr(door, "_snapshot_for_key", lambda *a, **k: [])
    answer = door.count(OWNER, "github", REPO, ["open_prs", "ci"])
    assert answer["plain"] == "CI —"
    assert [t["count"] for t in answer["tokens"]] == [0, 0]
    monkeypatch.setattr(door, "_snapshot_for_key", lambda *a, **k: [{"number": 1}, {"number": 2}])
    assert door.count(OWNER, "github", REPO, ["open_prs"])["plain"] == "2 open PRs"
