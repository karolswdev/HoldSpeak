"""Delivery Source registry tests (HS-94-02).

Real scratch git repos in tmp_path (the counterpart-test discipline)
exercised through real git subprocesses: fingerprints from
credential-free canonical metadata, opaque IDs that never collide
across worktrees or clones, wire projections that carry no
filesystem path or credential, and the non-destructive one-time v1
project-map import.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from holdspeak.delivery.registry import (
    DeliveryRegistry,
    RegistryError,
    normalize_git_url,
)

CREDENTIALED_ORIGIN = "https://buildbot:sekret-token-99@example.test/owner/repo.git"
CLEAN_ORIGIN = "https://example.test/owner/repo.git"


def _git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def _make_repo(tmp_path: Path, name: str = "repo", origin: str = CREDENTIALED_ORIGIN) -> Path:
    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.test")
    _git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "seed")
    if origin:
        _git(repo, "remote", "add", "origin", origin)
    return repo


def _registry(tmp_path: Path, name: str = "registry.json") -> DeliveryRegistry:
    return DeliveryRegistry(
        tmp_path / name, map_path=tmp_path / "absent-v1-map.json"
    )


def _walk_strings(node) -> list[str]:
    out: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            out.append(str(key))
            out.extend(_walk_strings(value))
    elif isinstance(node, list):
        for item in node:
            out.extend(_walk_strings(item))
    elif isinstance(node, str):
        out.append(node)
    return out


def assert_wire_clean(payload, tmp_path: Path) -> None:
    """No raw filesystem path, no credential, anywhere in the wire."""
    for text in _walk_strings(payload):
        assert str(tmp_path) not in text, text
        assert "sekret-token-99" not in text, text
        assert "buildbot:" not in text, text


class TestNormalizeGitUrl:
    def test_credentials_are_stripped(self):
        assert normalize_git_url(CREDENTIALED_ORIGIN) == "https://example.test/owner/repo"

    def test_clean_and_credentialed_normalize_identically(self):
        assert normalize_git_url(CLEAN_ORIGIN) == normalize_git_url(CREDENTIALED_ORIGIN)

    def test_scp_like_form(self):
        assert normalize_git_url("git@GitHub.com:owner/repo.git") == "ssh://github.com/owner/repo"

    def test_empty_is_empty(self):
        assert normalize_git_url("") == ""
        assert normalize_git_url("   ") == ""


class TestSourceAndWorktreeIdentity:
    def test_registration_yields_opaque_ids(self, tmp_path):
        repo = _make_repo(tmp_path)
        registry = _registry(tmp_path)
        source, worktree = registry.register(str(repo), label="Demo")
        assert source.source_id.startswith("src_")
        assert worktree.worktree_id.startswith("wt_")
        assert source.label == "Demo"
        assert source.fingerprint.startswith("sha256:")
        assert source.node_id is None  # nullable, reserved for the node link

    def test_multi_worktree_one_source_no_id_collision(self, tmp_path):
        repo = _make_repo(tmp_path)
        wt = tmp_path / "side-wt"
        _git(repo, "worktree", "add", "-b", "side", str(wt))
        registry = _registry(tmp_path)
        source_a, wt_a = registry.register(str(repo))
        source_b, wt_b = registry.register(str(wt))
        assert source_a.source_id == source_b.source_id  # one clone, one source
        assert wt_a.worktree_id != wt_b.worktree_id
        assert len(registry.sources()) == 1
        assert len(registry.sources()[0].worktrees) == 2
        assert wt_b.branch == "side"  # display only

    def test_registration_is_idempotent(self, tmp_path):
        repo = _make_repo(tmp_path)
        registry = _registry(tmp_path)
        _, wt_first = registry.register(str(repo))
        _, wt_again = registry.register(str(repo))
        assert wt_first.worktree_id == wt_again.worktree_id
        assert len(registry.sources()) == 1
        assert len(registry.sources()[0].worktrees) == 1

    def test_two_clones_share_fingerprint_but_not_source_id(self, tmp_path):
        repo = _make_repo(tmp_path)
        clone = tmp_path / "clone"
        subprocess.run(
            ["git", "clone", str(repo), str(clone)],
            check=True, capture_output=True, text=True,
        )
        _git(clone, "remote", "set-url", "origin", CLEAN_ORIGIN)
        registry = _registry(tmp_path)
        source_a, _ = registry.register(str(repo))
        source_b, _ = registry.register(str(clone))
        # Same upstream identity (credential-free URL + root commit)...
        assert source_a.fingerprint == source_b.fingerprint
        # ...but two clones are two sources (§3.1).
        assert source_a.source_id != source_b.source_id

    def test_fingerprint_is_credential_free(self, tmp_path):
        repo = _make_repo(tmp_path)
        registry = _registry(tmp_path)
        source, _ = registry.register(str(repo))
        before = source.fingerprint
        _git(repo, "remote", "set-url", "origin", CLEAN_ORIGIN)
        fresh = DeliveryRegistry(
            tmp_path / "registry-b.json",
            map_path=tmp_path / "absent-v1-map.json",
        )
        source_clean, _ = fresh.register(str(repo))
        assert source_clean.fingerprint == before

    def test_ids_are_stable_across_reload(self, tmp_path):
        repo = _make_repo(tmp_path)
        registry = _registry(tmp_path)
        source, worktree = registry.register(str(repo))
        reloaded = DeliveryRegistry(
            tmp_path / "registry.json", map_path=tmp_path / "absent-v1-map.json"
        )
        again = reloaded.sources()
        assert [s.source_id for s in again] == [source.source_id]
        assert again[0].worktrees[0].worktree_id == worktree.worktree_id

    def test_non_repo_is_a_typed_pathfree_refusal(self, tmp_path):
        loose = tmp_path / "loose"
        loose.mkdir()
        registry = _registry(tmp_path)
        with pytest.raises(RegistryError) as refusal:
            registry.register(str(loose))
        assert str(tmp_path) not in str(refusal.value)
        with pytest.raises(RegistryError):
            registry.register(str(tmp_path / "does-not-exist"))


class TestWireHygiene:
    def test_wire_view_has_no_paths_or_credentials(self, tmp_path):
        repo = _make_repo(tmp_path)
        wt = tmp_path / "wt2"
        _git(repo, "worktree", "add", "-b", "wt2", str(wt))
        registry = _registry(tmp_path)
        registry.register(str(repo), label="Demo")
        registry.register(str(wt))
        wire = registry.to_wire()
        assert wire["registry_schema"] == 1
        assert_wire_clean(wire, tmp_path)
        # The stored file MAY hold paths (server-side); the wire never.
        stored = json.loads((tmp_path / "registry.json").read_text())
        assert str(repo.resolve()) in json.dumps(stored)
        assert "path" not in json.dumps(wire["sources"])


class TestV1MapImport:
    def _v1_map(self, tmp_path: Path, repo: Path) -> Path:
        map_path = tmp_path / "delivery_workbench.json"
        map_path.write_text(
            json.dumps({"projects": {"demo": str(repo)}, "default": str(repo)}),
            encoding="utf-8",
        )
        return map_path

    def test_first_run_imports_each_mapped_path(self, tmp_path):
        repo = _make_repo(tmp_path)
        map_path = self._v1_map(tmp_path, repo)
        registry = DeliveryRegistry(tmp_path / "registry.json", map_path=map_path)
        sources = registry.sources()
        assert len(sources) == 1
        assert sources[0].label == "demo"
        assert sources[0].worktrees[0].path == str(repo.resolve())

    def test_import_is_non_destructive(self, tmp_path):
        repo = _make_repo(tmp_path)
        map_path = self._v1_map(tmp_path, repo)
        original_bytes = map_path.read_bytes()
        DeliveryRegistry(tmp_path / "registry.json", map_path=map_path)
        assert map_path.read_bytes() == original_bytes

    def test_import_runs_once_not_on_every_load(self, tmp_path):
        repo = _make_repo(tmp_path)
        map_path = self._v1_map(tmp_path, repo)
        first = DeliveryRegistry(tmp_path / "registry.json", map_path=map_path)
        source_id = first.sources()[0].source_id
        # The map grows a row the registry must NOT re-import (the
        # registry file exists now; import happened once).
        other = _make_repo(tmp_path, name="other")
        map_path.write_text(
            json.dumps(
                {"projects": {"demo": str(repo), "other": str(other)}},
            ),
            encoding="utf-8",
        )
        second = DeliveryRegistry(tmp_path / "registry.json", map_path=map_path)
        assert [s.source_id for s in second.sources()] == [source_id]

    def test_dead_map_rows_do_not_break_the_import(self, tmp_path):
        repo = _make_repo(tmp_path)
        map_path = tmp_path / "delivery_workbench.json"
        loose = tmp_path / "not-a-repo"
        loose.mkdir()
        map_path.write_text(
            json.dumps(
                {"projects": {"demo": str(repo), "loose": str(loose)}},
            ),
            encoding="utf-8",
        )
        registry = DeliveryRegistry(tmp_path / "registry.json", map_path=map_path)
        assert [s.label for s in registry.sources()] == ["demo"]

    def test_missing_map_yields_an_empty_registry(self, tmp_path):
        registry = _registry(tmp_path)
        assert registry.sources() == []
        assert registry.to_wire() == {"registry_schema": 1, "sources": []}
