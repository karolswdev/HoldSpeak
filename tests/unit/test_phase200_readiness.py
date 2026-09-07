"""HS-200-04 — model readiness: named repair states, the task probe, and the
frozen-route contract under failure.

Three seams, one story:

* `concierge_service.repairs` turns the setup verdict's word `needs_attention`
  into four named states, each carrying ONE verb and the existing control that
  verb opens.
* `route_probe` runs the smallest REAL request through the frozen route the
  assignment resolves to, and records the model that actually served it and the
  boundary it actually crossed.
* The frozen-route contract holds under failure: the controller walks only the
  frozen legs, never substitutes a provider that was not planned, and the
  failure names the route.

The coordinator, controller, runner, route planner and assignment service are
all the real product objects.  The one substituted thing is the physical engine
leaf (`broker.inference_runner._engine_factory`) — the house pattern recorded in
tests/unit/test_one_path_cardinality.py.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.kernel.provider_signals import ProviderPermanentNoGeneration
from holdspeak.kernel.runtime import _configure
from holdspeak.services import concierge_service as cs
from holdspeak.services import route_probe
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from tests.unit.test_phase143_inference_assignments import OWNER, _profile

PROBE_CAPABILITY = route_probe.DEFAULT_PROBE_CAPABILITY


# ── Repair states ────────────────────────────────────────────────────


class _FakeProfiles:
    def __init__(self, rows: dict[str, Any]) -> None:
        self._rows = rows

    def get(self, pid: str) -> Any:
        return self._rows.get(pid)

    def list(self) -> list[Any]:
        return list(self._rows.values())


class _FakeAutomations:
    def __init__(self, connections: list[dict[str, Any]]) -> None:
        self._connections = connections

    def list_provider_connections(self, **_kwargs: Any) -> list[dict[str, Any]]:
        return list(self._connections)


class _FakeDb:
    def __init__(self, profiles: dict[str, Any], connections: list[dict[str, Any]] | None = None) -> None:
        self.profiles = _FakeProfiles(profiles)
        self.automations = _FakeAutomations(connections or [])


class _FakeAssignments:
    """The seven-row owner roster, exactly as the real service shapes it."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def assignment_summary(self, _principal: Any) -> dict[str, Any]:
        return {"rows": self._rows}


def _profile_row(
    profile_id: str,
    *,
    name: str,
    base_url: str = "",
    model_file: str = "",
    requires_key: bool = False,
) -> Any:
    return SimpleNamespace(
        id=profile_id,
        name=name,
        base_url=base_url,
        model_file=model_file,
        requires_key=requires_key,
        node="",
        deleted=False,
        model="",
        kind="openAICompatible",
    )


def _group_row(group: str, profile_id: str, *, label: str, issues: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "id": group,
        "label": group,
        "assignment": {
            "entries": [
                {
                    "profile_id": profile_id,
                    "profile_revision": 1,
                    "label": label,
                    "boundary": "local",
                    "readiness": "ready",
                }
            ],
            "issues": issues or [],
        },
        "status": "assigned",
    }


def test_an_unset_key_on_an_assigned_route_is_credential_expired_with_the_connections_verb(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The owner's live condition: the assigned route needs a key that is unset."""
    monkeypatch.setattr(
        "holdspeak.inference_targets._profile_key_present", lambda _pid: False
    )
    db = _FakeDb(
        {
            "legacy-intel": _profile_row(
                "legacy-intel",
                name="Migrated intel endpoint",
                base_url="https://api.openai.com/v1",
                requires_key=True,
            )
        }
    )
    assignments = _FakeAssignments(
        [
            _group_row("thoughts_notes", "legacy-intel", label="Migrated intel endpoint"),
            # The same engine on a second group must NOT become a second row.
            _group_row("writing_dictation", "legacy-intel", label="Migrated intel endpoint"),
        ]
    )

    rows = cs.repairs(db=db, assignment_service=assignments, principal=OWNER)

    assert [r["token"] for r in rows] == [cs.REPAIR_CREDENTIAL_EXPIRED]
    row = rows[0]
    assert row["subject"] == "Migrated intel endpoint"
    assert row["verb"] == "Connections"
    assert row["control"] == "connections"
    assert row["host"] == "api.openai.com"
    assert row["scope"] == "cloud"
    # One row naming both groups, never one row per group.
    assert row["groups"] == ["thoughts_notes", "writing_dictation"]
    assert row["groupLabels"] == ["Thoughts & notes", "Writing & dictation"]


def test_a_missing_model_file_on_an_assigned_route_names_the_model_library_verb(
    tmp_path: Path,
) -> None:
    db = _FakeDb(
        {
            "local-gguf": _profile_row(
                "local-gguf",
                name="Qwen 3.5 0.8B",
                model_file=str(tmp_path / "not-here.gguf"),
            )
        }
    )
    assignments = _FakeAssignments(
        [_group_row("writing_dictation", "local-gguf", label="Qwen 3.5 0.8B")]
    )

    rows = cs.repairs(db=db, assignment_service=assignments, principal=OWNER)

    assert [r["token"] for r in rows] == [cs.REPAIR_MODEL_FILE_MISSING]
    assert rows[0]["verb"] == "Download"
    assert rows[0]["control"] == "model_library"
    assert rows[0]["host"] == "THIS DEVICE"


def test_a_present_model_file_produces_no_repair_row(tmp_path: Path) -> None:
    """No counter of zero, and no warning about a route that actually works."""
    artifact = tmp_path / "present.gguf"
    artifact.write_bytes(b"0")
    db = _FakeDb(
        {"local-gguf": _profile_row("local-gguf", name="Qwen", model_file=str(artifact))}
    )
    assignments = _FakeAssignments(
        [_group_row("writing_dictation", "local-gguf", label="Qwen")]
    )

    assert cs.repairs(db=db, assignment_service=assignments, principal=OWNER) == []


def test_an_unreachable_assigned_endpoint_names_the_endpoint_editor_verb() -> None:
    db = _FakeDb(
        {
            "lan-box": _profile_row(
                "lan-box", name="Qwen3.6 35B", base_url="http://192.168.1.43:8080/v1"
            )
        }
    )
    assignments = _FakeAssignments(
        [_group_row("meetings", "lan-box", label="Qwen3.6 35B")]
    )

    def _refuse(*_args: Any, **_kwargs: Any) -> tuple[int, bytes]:
        raise OSError("connection refused")

    rows = cs.repairs(
        db=db, assignment_service=assignments, principal=OWNER, http_get=_refuse
    )

    assert [r["token"] for r in rows] == [cs.REPAIR_ENDPOINT_UNREACHABLE]
    assert rows[0]["verb"] == "Check"
    assert rows[0]["control"] == "endpoint_editor"
    # The verb needs the endpoint to open the editor ON.
    assert rows[0]["baseUrl"] == "http://192.168.1.43:8080/v1"
    assert rows[0]["host"] == "192.168.1.43"


def test_a_reachable_assigned_endpoint_produces_no_repair_row() -> None:
    db = _FakeDb(
        {
            "lan-box": _profile_row(
                "lan-box", name="Qwen3.6 35B", base_url="http://192.168.1.43:8080/v1"
            )
        }
    )
    assignments = _FakeAssignments(
        [_group_row("meetings", "lan-box", label="Qwen3.6 35B")]
    )

    def _ok(*_args: Any, **_kwargs: Any) -> tuple[int, bytes]:
        return (200, b'{"data": [{"id": "qwen"}]}')

    assert cs.repairs(
        db=db, assignment_service=assignments, principal=OWNER, http_get=_ok
    ) == []


def test_a_cloud_endpoint_with_its_key_set_is_never_read_without_his_verb(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The repair list may not quietly reach a paid host to decide a row."""
    monkeypatch.setattr(
        "holdspeak.inference_targets._profile_key_present", lambda _pid: True
    )
    db = _FakeDb(
        {
            "cloud": _profile_row(
                "cloud",
                name="OpenRouter",
                base_url="https://openrouter.ai/api/v1",
                requires_key=True,
            )
        }
    )
    assignments = _FakeAssignments([_group_row("meetings", "cloud", label="OpenRouter")])

    def _forbidden(*_args: Any, **_kwargs: Any) -> tuple[int, bytes]:
        raise AssertionError("a repair read must not touch a cloud endpoint")

    assert cs.repairs(
        db=db, assignment_service=assignments, principal=OWNER, http_get=_forbidden
    ) == []


def test_a_blocking_compatibility_issue_is_tool_incompatible_with_the_picker_verb() -> None:
    db = _FakeDb({"lan-box": _profile_row("lan-box", name="Qwen3.6 35B")})
    assignments = _FakeAssignments(
        [
            _group_row(
                "agents_tools",
                "lan-box",
                label="Qwen3.6 35B",
                issues=[
                    {"code": "capability_tools_unsupported", "severity": "blocking"},
                    {"code": "cosmetic", "severity": "advisory"},
                ],
            )
        ]
    )

    rows = cs.repairs(db=db, assignment_service=assignments, principal=OWNER)

    assert [r["token"] for r in rows] == [cs.REPAIR_TOOL_INCOMPATIBLE]
    assert rows[0]["verb"] == "Choose"
    assert rows[0]["control"] == "engine_picker"
    assert rows[0]["groups"] == ["agents_tools"]
    assert rows[0]["detail"] == "capability_tools_unsupported"


def test_a_source_connection_needing_the_owner_is_a_credential_repair() -> None:
    db = _FakeDb(
        {},
        connections=[
            {"provider_id": "jira", "state": "owner_action_required", "last_error_code": "auth_expired"},
            {"provider_id": "github", "state": "connected", "last_error_code": ""},
        ],
    )

    rows = cs.repairs(db=db, assignment_service=None, principal=None)

    assert [(r["token"], r["subject"]) for r in rows] == [
        (cs.REPAIR_CREDENTIAL_EXPIRED, "jira")
    ]
    assert rows[0]["verb"] == "Connections"
    assert rows[0]["control"] == "connections"


def test_every_repair_state_carries_exactly_one_verb_and_a_named_control() -> None:
    """The four states of the story, and no fifth verb invented on the face."""
    assert set(cs._REPAIR_VERBS) == {
        cs.REPAIR_MODEL_FILE_MISSING,
        cs.REPAIR_ENDPOINT_UNREACHABLE,
        cs.REPAIR_TOOL_INCOMPATIBLE,
        cs.REPAIR_CREDENTIAL_EXPIRED,
    }
    for token, (verb, control) in cs._REPAIR_VERBS.items():
        assert verb and " " not in verb.strip(), token
        assert control in {
            "model_library",
            "endpoint_editor",
            "engine_picker",
            "connections",
        }


# ── The task probe ───────────────────────────────────────────────────


def _assign(db: Database, capability_id: str, profiles: list[str]) -> None:
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": f"assign-{capability_id}",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": capability_id},
            "entries": [
                {"profile_id": profile_id, "profile_revision": 1}
                for profile_id in profiles
            ],
        },
    )


def _routed_db(tmp_path: Path, name: str, profiles: tuple[str, ...]) -> Database:
    db = Database(tmp_path / name)
    for profile_id in profiles:
        _profile(db, profile_id)
    _assign(db, PROBE_CAPABILITY, list(profiles))
    return db


class _Engine:
    """The one substituted leaf: a physical engine that answers or refuses."""

    active_provider = "fixture"
    active_model = "fixture-model"

    def __init__(self, revision: str, *, failing: set[str] | None = None, seen: list[str] | None = None) -> None:
        self.revision = revision
        self._failing = failing or set()
        self._seen = seen if seen is not None else []

    def run_prompt(self, **_kwargs: Any) -> str:
        self._seen.append(self.revision)
        if self.revision in self._failing:
            raise ProviderPermanentNoGeneration()
        return "ready"


def _engine_factory(broker: Any, *, failing: set[str] | None = None) -> list[str]:
    seen: list[str] = []
    broker.inference_runner._engine_factory = lambda revision, **_kwargs: _Engine(
        revision.id, failing=failing, seen=seen
    )
    return seen


def test_probeable_capabilities_are_a_closed_set(tmp_path: Path) -> None:
    db = _routed_db(tmp_path, "probe-closed.db", ("quick",))
    broker = _configure(db)
    with pytest.raises(Exception) as refused:
        route_probe.preview_route(broker, capability_id="meeting.auto_title")
    assert getattr(refused.value, "code", "") == "route_probe_capability_invalid"


def test_preview_names_the_planned_legs_without_dispatching(tmp_path: Path) -> None:
    db = _routed_db(tmp_path, "probe-preview.db", ("quick", "deep"))
    broker = _configure(db)
    seen = _engine_factory(broker)

    preview = route_probe.preview_route(broker, capability_id=PROBE_CAPABILITY)

    assert [leg["ordinal"] for leg in preview["legs"]] == [1, 2]
    assert {leg["boundary"] for leg in preview["legs"]} == {"local"}
    assert preview["offMachine"] is False and preview["paid"] is False
    # Pure resolution: nothing was sent to any engine.
    assert seen == []


def test_a_real_probe_records_the_model_that_served_and_the_boundary_it_crossed(
    tmp_path: Path,
) -> None:
    db = _routed_db(tmp_path, "probe-real.db", ("quick",))
    broker = _configure(db)
    seen = _engine_factory(broker)

    result = route_probe.task_probe(broker, OWNER, db=db, capability_id=PROBE_CAPABILITY)

    assert result["ok"] is True and result["state"] == "READY"
    assert len(seen) == 1, "the smallest real request is one physical attempt"
    # The model is the deployment that actually served, not an advertised name.
    assert result["model"] == "quick"
    assert result["engine"] == "configured_local_engine"
    assert result["boundary"] == "local"
    assert result["host"] == "THIS DEVICE"
    assert result["routePlanId"].startswith("irp_")
    assert result["executionId"]


def test_a_local_probe_host_is_this_device_and_an_endpoint_host_is_its_hostname() -> None:
    assert route_probe.host_for("local", {"endpoint": "http://192.168.1.43:8080/v1"}) == "THIS DEVICE"
    assert (
        route_probe.host_for("private_network", {"endpoint": "http://192.168.1.43:8080/v1"})
        == "192.168.1.43"
    )
    assert route_probe.host_for("cloud", {"endpoint": "https://api.openai.com/v1"}) == "api.openai.com"
    assert route_probe.host_for("mesh", {"node": "studio"}) == "studio"


def test_an_off_machine_route_refuses_the_probe_until_the_owner_confirms(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No byte leaves the machine, and nothing is frozen, without his verb."""
    db = _routed_db(tmp_path, "probe-cloud.db", ("quick",))
    broker = _configure(db)
    seen = _engine_factory(broker)

    def _cloud_plan(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {
            "entries": [
                {
                    "ordinal": 1,
                    "profile_id": "cloudy",
                    "deployment_revision_id": "dep-cloud",
                    "boundary": "cloud",
                }
            ]
        }

    monkeypatch.setattr(
        broker.inference_adoption_service.plans, "resolve_route_plan", _cloud_plan
    )

    def _never(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("a refused probe must never admit a route")

    monkeypatch.setattr(broker.inference_adoption_service, "admit", _never)

    result = route_probe.task_probe(broker, OWNER, db=db, capability_id=PROBE_CAPABILITY)

    assert result["state"] == "REFUSED"
    assert result["ok"] is False
    assert result["paid"] is True
    assert result["reasonCode"] == "route_probe_off_machine_not_confirmed"
    assert seen == []


# ── The frozen-route contract under failure ──────────────────────────


def test_the_probe_falls_back_only_within_the_frozen_plan_and_names_every_leg(
    tmp_path: Path,
) -> None:
    """Leg 1 fails permanently; the walk continues to leg 2 — and stops there.

    Every deployment the controller considered comes from the frozen plan; no
    provider outside it is ever dispatched.
    """
    db = _routed_db(tmp_path, "probe-fallback.db", ("quick", "deep"))
    broker = _configure(db)
    planned = route_probe.preview_route(broker, capability_id=PROBE_CAPABILITY)
    frozen_deployments = {leg["deploymentRevisionId"] for leg in planned["legs"]}
    first_leg = planned["legs"][0]["deploymentRevisionId"]
    seen = _engine_factory(broker, failing={first_leg})

    result = route_probe.task_probe(broker, OWNER, db=db, capability_id=PROBE_CAPABILITY)

    assert result["ok"] is True
    assert seen[0] == first_leg and len(seen) == 2
    # The winner is the SECOND frozen leg — not a substituted provider.
    assert set(seen) <= frozen_deployments
    considered = {leg["deploymentRevisionId"] for leg in result["legs"]}
    assert considered <= frozen_deployments
    assert result["model"] == "deep"


def test_when_every_frozen_leg_fails_the_probe_names_the_route_and_refuses(
    tmp_path: Path,
) -> None:
    db = _routed_db(tmp_path, "probe-allfail.db", ("quick", "deep"))
    broker = _configure(db)
    planned = route_probe.preview_route(broker, capability_id=PROBE_CAPABILITY)
    every = {leg["deploymentRevisionId"] for leg in planned["legs"]}
    seen = _engine_factory(broker, failing=every)

    result = route_probe.task_probe(broker, OWNER, db=db, capability_id=PROBE_CAPABILITY)

    assert result["ok"] is False and result["state"] == "UNREACHABLE"
    assert result["allModelsFailed"] is True
    # The failure NAMES the route: its plan and every frozen leg considered.
    assert result["routePlanId"].startswith("irp_")
    assert {leg["deploymentRevisionId"] for leg in result["legs"]} == every
    assert set(seen) == every
    # No silent substitution: nothing outside the frozen plan was dispatched.
    assert set(seen) <= every
