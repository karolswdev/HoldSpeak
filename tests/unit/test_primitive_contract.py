"""HS-72-01 — the primitive contract, machine-checked (Phase 72, One Spine).

The Primitive Framework's wire contract used to be prose ("keep this in
lockstep with the mobile/web SyncKind enum"). These tests make it mechanical:

1. **Real hub emissions validate.** A real tmp-path ``Database`` is populated
   with one row per sync kind and ``GET /api/sync/pull`` is validated — every
   record's ``value`` against its kind schema, the whole body against the
   ChangeSet envelope schema, and the hub-emission superset (``last_modified``
   + ``deleted`` inside ``value``) pinned here rather than in the schemas (so
   an iPad push, which omits sync plumbing, still validates against the same
   schemas).
2. **The kind set cannot drift.** ``sync.py``'s ``SYNC_KINDS`` == the schema
   set (each schema's ``x-sync-kind``) == Swift's ``SyncKind`` raw values
   (parsed from ``apple/Sources/Contracts/Sync.swift``).
3. **The web shapes cannot invent fields.** Every required data field on the
   desk-kind interfaces in ``web/src/lib/primitives.ts`` (camelCase → snake)
   must exist in the corresponding schema, with the documented view-model
   exceptions.

Schemas live in ``pm/roadmap/holdspeak-mobile/contracts/schemas`` — the same
files ``contracts/validate.py`` and the Swift fixture tests consume.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

jsonschema = pytest.importorskip("jsonschema")
from jsonschema import Draft202012Validator  # noqa: E402
from referencing import Registry, Resource  # noqa: E402

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_sync_router
from holdspeak.web.routes.sync import SYNC_KINDS

REPO = Path(__file__).parents[2]
SCHEMA_DIR = REPO / "pm/roadmap/holdspeak-mobile/contracts/schemas"
SYNC_SWIFT = REPO / "apple/Sources/Contracts/Sync.swift"
PRIMITIVES_TS = REPO / "web/src/lib/primitives.ts"

# sync kind -> (pull bucket, value schema $id)
KIND_BUCKETS = {
    "note": "notes",
    "kb": "kbs",
    "agent": "agents",
    "chain": "chains",
    "workflow": "workflows",
    "directory": "directories",
    "directory_membership": "directory_memberships",
    "profile": "profiles",
}


def _load_schemas() -> dict[str, dict]:
    """Every committed schema, keyed by $id."""
    out: dict[str, dict] = {}
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        schema = json.loads(path.read_text())
        out[schema["$id"]] = schema
    return out


SCHEMAS = _load_schemas()
REGISTRY = Registry().with_resources(
    [(sid, Resource.from_contents(s)) for sid, s in SCHEMAS.items()]
)


def _schema_for_kind(kind: str) -> dict:
    for schema in SCHEMAS.values():
        if schema.get("x-sync-kind") == kind:
            return schema
    raise AssertionError(f"no schema declares x-sync-kind={kind!r}")


def _validator(schema: dict) -> Draft202012Validator:
    return Draft202012Validator(schema, registry=REGISTRY)


def _errors(schema: dict, instance: object) -> list[str]:
    return [
        f"{'/'.join(map(str, e.path))}: {e.message}"
        for e in _validator(schema).iter_errors(instance)
    ]


@pytest.fixture
def pull_body(tmp_path, monkeypatch):
    """A real /api/sync/pull body over a Database holding one row per kind."""
    reset_database()
    db = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)

    db.notes.upsert(note_id="n1", title="N", body_markdown="b", tags=["t"])
    db.kbs.upsert(kb_id="kb1", name="K", member_ids=["n1"])
    db.agents.upsert(agent_id="a1", name="A", avatar="av", role="r",
                     system_prompt="s", user_template="u", kb_id="kb1")
    db.chains.upsert(chain_id="c1", name="C", steps=["a1"])
    db.workflows.upsert(workflow_id="w1", name="W", prompt="p")
    db.directories.upsert(directory_id="Atlas/Q3", name="Q3", parent_id="Atlas")
    db.directory_memberships.upsert(primitive_id="n1", directory_id="Atlas/Q3")
    db.profiles.upsert(profile_id="p1", name="lan", kind="openAICompatible",
                       base_url="http://example.test/v1", model="m")
    # A tombstone so the envelope's deleted branch is exercised by real data.
    db.notes.upsert(note_id="n-gone", title="gone")
    db.notes.delete("n-gone")

    app = FastAPI()
    app.include_router(build_sync_router(WebContext(get_state=lambda: {})))
    body = TestClient(app).get("/api/sync/pull").json()
    reset_database()
    return body


class TestHubEmissionsValidate:
    def test_every_kind_value_validates_against_its_schema(self, pull_body) -> None:
        for kind, bucket in KIND_BUCKETS.items():
            records = pull_body[bucket]
            assert records, f"pull emitted no {bucket}"
            schema = _schema_for_kind(kind)
            for rec in records:
                if rec["meta"]["deleted"]:
                    continue
                errs = _errors(schema, rec["value"])
                assert not errs, f"{kind} value violates its schema: {errs}"

    def test_pull_body_validates_against_changeset_envelope(self, pull_body) -> None:
        envelope = SCHEMAS["https://holdspeak.dev/contracts/v0/changeset.schema.json"]
        # The pull body also carries meetings/artifacts buckets (empty here) —
        # the envelope covers all ten.
        errs = _errors(envelope, pull_body)
        assert not errs, f"pull body violates the ChangeSet envelope: {errs}"

    def test_hub_emission_carries_the_sync_superset(self, pull_body) -> None:
        """The hub always emits value.last_modified + value.deleted and a
        Z-terminated meta.last_modified — pinned here, not in the schemas."""
        for kind, bucket in KIND_BUCKETS.items():
            for rec in pull_body[bucket]:
                meta = rec["meta"]
                assert meta["kind"] == kind
                assert str(meta["last_modified"]).endswith("Z"), (
                    f"{kind} meta.last_modified is not UTC-Z: {meta['last_modified']!r}")
                if not meta["deleted"]:
                    value = rec["value"]
                    assert "last_modified" in value and "deleted" in value, (
                        f"hub {kind} emission lost its sync superset")

    def test_tombstone_rides_the_wire(self, pull_body) -> None:
        tombstones = [r for r in pull_body["notes"] if r["meta"]["deleted"]]
        assert tombstones, "the deleted note's tombstone did not ride the pull"


class TestKindSetCannotDrift:
    def test_schemas_cover_exactly_sync_kinds(self) -> None:
        schema_kinds = {
            s["x-sync-kind"] for s in SCHEMAS.values() if "x-sync-kind" in s
        }
        assert schema_kinds == set(SYNC_KINDS), (
            f"schema kinds {sorted(schema_kinds)} != hub SYNC_KINDS "
            f"{sorted(SYNC_KINDS)} — a kind was added/removed on one side only")

    def test_swift_sync_kind_matches_hub(self) -> None:
        text = SYNC_SWIFT.read_text()
        enum_body = re.search(
            r"enum SyncKind[^{]*\{(.*?)\n\}", text, re.DOTALL)
        assert enum_body, "SyncKind enum not found in Sync.swift"
        cases = re.findall(
            r"^\s*case\s+(\w+)(?:\s*=\s*\"([^\"]+)\")?",
            enum_body.group(1), re.MULTILINE)
        swift_kinds = {raw or name for name, raw in cases}
        assert swift_kinds == set(SYNC_KINDS), (
            f"Swift SyncKind {sorted(swift_kinds)} != hub SYNC_KINDS "
            f"{sorted(SYNC_KINDS)} — the surfaces drifted")

    def test_changeset_buckets_cover_every_kind(self) -> None:
        envelope = SCHEMAS["https://holdspeak.dev/contracts/v0/changeset.schema.json"]
        buckets = set(envelope["properties"])
        expected = {"meetings", "artifacts"} | set(KIND_BUCKETS.values())
        assert buckets == expected


class TestWebShapesCannotInventFields:
    """primitives.ts may OMIT wire fields (in-app view shapes) but must never
    REQUIRE a data field the hub's contract doesn't have."""

    # TS interface -> sync kind; only the desk-authored kinds are contract-shaped
    # (Meeting/Artifact TS shapes are view models by design).
    TS_KINDS = {
        "Note": "note",
        "Directory": "directory",
        "KB": "kb",
        "Agent": "agent",
        "Chain": "chain",
        "Workflow": "workflow",
    }
    # Documented view-model exceptions: TS fields composed in-app, not wire fields.
    EXCEPTIONS = {
        "directory": {"member_ids"},  # composed from directory_membership edges
    }

    @staticmethod
    def _camel_to_snake(name: str) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()

    def _ts_fields(self, interface: str) -> list[tuple[str, bool]]:
        text = PRIMITIVES_TS.read_text()
        block = re.search(
            rf"export interface {interface} \{{(.*?)\n\}}", text, re.DOTALL)
        assert block, f"interface {interface} not found in primitives.ts"
        fields = re.findall(r"^\s*(\w+)(\?)?:", block.group(1), re.MULTILINE)
        return [(name, optional == "") for name, optional in fields]

    def test_required_ts_fields_exist_in_the_schema(self) -> None:
        problems: list[str] = []
        for interface, kind in self.TS_KINDS.items():
            schema_props = set(_schema_for_kind(kind)["properties"])
            allowed_missing = self.EXCEPTIONS.get(kind, set())
            for name, required in self._ts_fields(interface):
                if name == "kind" or not required:
                    continue  # the TS discriminator / optional view fields
                wire = self._camel_to_snake(name)
                if wire not in schema_props and wire not in allowed_missing:
                    problems.append(
                        f"{interface}.{name} (wire {wire!r}) is required in "
                        f"primitives.ts but absent from the {kind} schema")
        assert not problems, "web invented contract fields:\n  " + "\n  ".join(problems)
