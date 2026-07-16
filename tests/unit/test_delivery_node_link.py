"""The authenticated node link — hub-side state (HS-94-03).

PLATFORM-CONTRACT §6/§12 behaviors, proven with injected monotonic
clocks and a temp token store:

- token custody: create/rotate/revoke by name, browser-token
  distinctness, 0600 file, no token material in any wire view;
- liveness: live → stale (15 s) → offline (30 s) with last-seen
  retained; explicit disconnect; heartbeat revival;
- capability/protocol scoping: commands refuse, observation flows;
- cursor discipline: in-order accept, duplicate skip, gap → resync;
- the metadata allow-list: a non-allow-listed field refuses the
  event (no body-content smuggling);
- ONE behavior suite that both the embedded local adapter and the
  remote HTTP path must pass (§2 rule 14).
"""

from __future__ import annotations

import json
import stat

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.delivery.node_link import (
    NODE_PROTOCOL,
    LocalNodeAdapter,
    NodeLinkError,
    NodeLinkState,
    NodeTokenStore,
    validate_node_event,
)
from holdspeak.web.context import WebContext
from holdspeak.web.routes.delivery_node import build_delivery_node_router

WEB_TOKEN = "browser-token-for-humans"
FULL_CAPS = ["delivery.source", "coder.steering"]


class Clock:
    def __init__(self) -> None:
        self.t = 100.0

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


@pytest.fixture
def store(tmp_path) -> NodeTokenStore:
    return NodeTokenStore(tmp_path / "node_auth_tokens.json")


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def state(store, clock) -> NodeLinkState:
    return NodeLinkState(store, web_token=WEB_TOKEN, clock=clock)


def _event(seq: int, **extra):
    return {"seq": seq, "kind": "rail.cursor", **extra}


# ── token custody ────────────────────────────────────────────────────


class TestNodeTokens:
    def test_create_verify_roundtrip(self, store):
        node_id, token = store.create("studio-mac")
        assert store.verify("studio-mac", token) == node_id

    def test_rotate_kills_old_token_keeps_identity(self, store):
        node_id, old = store.create("studio-mac")
        new = store.rotate("studio-mac")
        assert new != old
        assert store.verify("studio-mac", new) == node_id  # same node_id
        with pytest.raises(NodeLinkError) as err:
            store.verify("studio-mac", old)
        assert err.value.reason == "token_rejected"

    def test_revoke_refuses_by_name(self, store):
        _, token = store.create("studio-mac")
        store.revoke("studio-mac")
        with pytest.raises(NodeLinkError) as err:
            store.verify("studio-mac", token)
        assert err.value.reason == "node_revoked"
        assert "studio-mac" in str(err.value)

    def test_repair_after_revoke_mints_new_identity(self, store):
        node_id, _ = store.create("studio-mac")
        store.revoke("studio-mac")
        node_id_2, _ = store.create("studio-mac")
        assert node_id_2 != node_id

    def test_second_create_refuses(self, store):
        store.create("studio-mac")
        with pytest.raises(NodeLinkError) as err:
            store.create("studio-mac")
        assert err.value.reason == "already_paired"

    def test_ensure_is_idempotent_but_honors_revocation(self, store):
        first = store.ensure("local")
        assert store.ensure("local") == first
        store.revoke("local")
        with pytest.raises(NodeLinkError) as err:
            store.ensure("local")
        assert err.value.reason == "node_revoked"

    def test_web_token_never_authenticates_as_node(self, store):
        store.create("studio-mac")
        # Even a store poisoned with the browser token must refuse it.
        store._nodes["studio-mac"]["token"] = WEB_TOKEN
        with pytest.raises(NodeLinkError) as err:
            store.verify("studio-mac", WEB_TOKEN, web_token=WEB_TOKEN)
        assert err.value.reason == "node_token_required"

    def test_store_file_is_owner_only(self, store, tmp_path):
        store.create("studio-mac")
        mode = stat.S_IMODE((tmp_path / "node_auth_tokens.json").stat().st_mode)
        assert mode == 0o600

    def test_status_rows_carry_no_token_material(self, store):
        _, token = store.create("studio-mac")
        dumped = json.dumps(store.status_rows())
        assert token not in dumped

    def test_persistence_across_instances(self, store, tmp_path):
        node_id, token = store.create("studio-mac")
        reloaded = NodeTokenStore(tmp_path / "node_auth_tokens.json")
        assert reloaded.verify("studio-mac", token) == node_id


# ── liveness ─────────────────────────────────────────────────────────


class TestLiveness:
    def _hello(self, state, store, caps=None):
        _, token = store.create("far-node")
        state.hello(
            "far-node",
            token,
            node_protocol=NODE_PROTOCOL,
            instance_id="inst-1",
            capabilities=caps if caps is not None else FULL_CAPS,
        )
        return token

    def test_live_stale_offline_timeline(self, state, store, clock):
        self._hello(state, store)
        assert state.status_of("far-node") == "live"
        clock.advance(14.9)
        assert state.status_of("far-node") == "live"
        clock.advance(0.2)  # 15.1 s
        assert state.status_of("far-node") == "stale"
        clock.advance(14.8)  # 29.9 s
        assert state.status_of("far-node") == "stale"
        clock.advance(0.2)  # 30.1 s
        assert state.status_of("far-node") == "offline"

    def test_last_seen_retained_when_offline(self, state, store, clock):
        self._hello(state, store)
        row = state.nodes_view()["nodes"][0]
        seen = row["last_seen"]
        assert seen
        clock.advance(3600)
        row = state.nodes_view()["nodes"][0]
        assert row["status"] == "offline"
        assert row["last_seen"] == seen  # truth retained, never erased

    def test_heartbeat_restores_live(self, state, store, clock):
        token = self._hello(state, store)
        clock.advance(31)
        assert state.status_of("far-node") == "offline"
        state.heartbeat("far-node", token)
        assert state.status_of("far-node") == "live"

    def test_explicit_disconnect_is_immediately_offline(self, state, store):
        token = self._hello(state, store)
        state.disconnect("far-node", token)
        assert state.status_of("far-node") == "offline"
        state.heartbeat("far-node", token)
        assert state.status_of("far-node") == "live"

    def test_clock_skew_is_measured_and_surfaced(self, store, clock):
        state = NodeLinkState(
            store,
            web_token=WEB_TOKEN,
            clock=clock,
            wall_clock=lambda: "2026-07-15T12:00:10Z",
        )
        _, token = store.create("far-node")
        response = state.hello(
            "far-node",
            token,
            node_protocol=NODE_PROTOCOL,
            instance_id="i",
            capabilities=FULL_CAPS,
            node_wall_time="2026-07-15T12:00:00Z",
        )
        assert response["clock_skew_seconds"] == pytest.approx(10.0)


# ── capability / protocol scoping ────────────────────────────────────


class TestCommandScoping:
    def test_capability_mismatch_disables_commands_keeps_observation(
        self, state, store
    ):
        _, token = store.create("watcher")
        response = state.hello(
            "watcher",
            token,
            node_protocol=NODE_PROTOCOL,
            instance_id="i",
            capabilities=["delivery.source"],  # no coder.steering
        )
        assert response["commands_enabled"] is False
        assert response["compat"] == "capability_missing"
        with pytest.raises(NodeLinkError) as err:
            state.poll_commands("watcher", token)
        assert err.value.reason == "commands_disabled"
        # Observation still flows: heartbeat + events accepted.
        beat = state.heartbeat("watcher", token, events=[_event(1)])
        assert beat["ok"] is True and beat["cursor"] == 1

    def test_protocol_mismatch_disables_commands_keeps_observation(
        self, state, store
    ):
        _, token = store.create("future")
        response = state.hello(
            "future",
            token,
            node_protocol=99,
            instance_id="i",
            capabilities=FULL_CAPS,
        )
        assert response["commands_enabled"] is False
        assert response["compat"] == "protocol_mismatch"
        assert state.heartbeat("future", token, events=[_event(1)])["cursor"] == 1

    def test_compatible_node_gets_the_command_envelope(self, state, store):
        _, token = store.create("full")
        state.hello(
            "full", token, node_protocol=NODE_PROTOCOL,
            instance_id="i", capabilities=FULL_CAPS,
        )
        envelope = state.poll_commands("full", token)
        assert envelope["commands_schema"] == 1
        assert envelope["commands"] == []


# ── cursor discipline ────────────────────────────────────────────────


class TestCursorResume:
    def _link(self, state, store, name="src-node"):
        _, token = store.create(name)
        state.hello(
            name, token, node_protocol=NODE_PROTOCOL,
            instance_id="i1", capabilities=FULL_CAPS,
        )
        return token

    def test_in_order_accept_and_duplicate_skip(self, state, store):
        token = self._link(state, store)
        beat = state.heartbeat(
            "src-node", token, events=[_event(1), _event(2), _event(3)]
        )
        assert (beat["cursor"], beat["accepted"], beat["resync"]) == (3, 3, False)
        # Replay after a lost ack: duplicates skipped, nothing doubled.
        beat = state.heartbeat("src-node", token, events=[_event(2), _event(3)])
        assert (beat["cursor"], beat["accepted"]) == (3, 0)
        assert [e["seq"] for e in state.events_of("src-node")] == [1, 2, 3]

    def test_gap_requests_resync_instead_of_inventing_continuity(self, state, store):
        token = self._link(state, store)
        state.heartbeat("src-node", token, events=[_event(1)])
        beat = state.heartbeat("src-node", token, events=[_event(2), _event(5)])
        assert beat["resync"] is True
        assert beat["cursor"] == 2  # 2 accepted, the gap refused
        assert [e["seq"] for e in state.events_of("src-node")] == [1, 2]

    def test_node_restart_resumes_from_hub_cursor(self, state, store):
        token = self._link(state, store)
        state.heartbeat("src-node", token, events=[_event(1), _event(2)])
        # Restart: new instance, node's persisted cursor rides hello.
        response = state.hello(
            "src-node", token, node_protocol=NODE_PROTOCOL,
            instance_id="i2", capabilities=FULL_CAPS, resume_cursor=2,
        )
        assert response["cursor"] == 2  # hub record is authoritative
        beat = state.heartbeat("src-node", token, events=[_event(3)])
        assert (beat["cursor"], beat["accepted"]) == (3, 1)
        assert [e["seq"] for e in state.events_of("src-node")] == [1, 2, 3]

    def test_hub_restart_adopts_the_node_cursor(self, store, clock):
        _, token = store.create("src-node")
        fresh_hub = NodeLinkState(store, web_token=WEB_TOKEN, clock=clock)
        response = fresh_hub.hello(
            "src-node", token, node_protocol=NODE_PROTOCOL,
            instance_id="i1", capabilities=FULL_CAPS, resume_cursor=5,
        )
        assert response["cursor"] == 5
        beat = fresh_hub.heartbeat("src-node", token, events=[_event(6)])
        assert (beat["cursor"], beat["accepted"]) == (6, 1)

    def test_events_are_stamped_with_the_opaque_node_id(self, state, store):
        token = self._link(state, store)
        state.heartbeat("src-node", token, events=[_event(1)])
        event = state.events_of("src-node")[0]
        assert event["node_id"].startswith("node_")


# ── the metadata allow-list ──────────────────────────────────────────


class TestEventAllowList:
    def test_non_allow_listed_field_refuses_the_event(self, state, store):
        _, token = store.create("n")
        state.hello(
            "n", token, node_protocol=NODE_PROTOCOL,
            instance_id="i", capabilities=FULL_CAPS,
        )
        smuggle = {"seq": 1, "kind": "rail.cursor", "transcript": "the whole meeting"}
        with pytest.raises(NodeLinkError) as err:
            state.heartbeat("n", token, events=[smuggle])
        assert err.value.reason == "event_field_not_allowed"
        assert "transcript" in str(err.value)
        # Nothing was partially accepted.
        assert state.events_of("n") == []
        assert state.heartbeat("n", token)["cursor"] == 0

    def test_unknown_kind_refused(self):
        with pytest.raises(NodeLinkError) as err:
            validate_node_event({"seq": 1, "kind": "terminal.bytes"})
        assert err.value.reason == "event_kind_unknown"

    def test_nested_detail_refused(self):
        with pytest.raises(NodeLinkError) as err:
            validate_node_event(
                {"seq": 1, "kind": "rail.cursor", "detail": {"payload": {"a": 1}}}
            )
        assert err.value.reason == "event_detail_invalid"

    def test_oversized_detail_refused(self):
        with pytest.raises(NodeLinkError) as err:
            validate_node_event(
                {"seq": 1, "kind": "rail.cursor", "detail": {"note": "x" * 501}}
            )
        assert err.value.reason == "event_detail_invalid"

    def test_seq_must_be_a_positive_integer(self):
        for bad in (0, -1, "1", 1.5, True, None):
            with pytest.raises(NodeLinkError):
                validate_node_event({"seq": bad, "kind": "rail.cursor"})


# ── projections ──────────────────────────────────────────────────────


class TestNodesProjection:
    def test_no_secret_ever_crosses(self, state, store):
        _, token = store.create("n")
        state.hello(
            "n", token, node_protocol=NODE_PROTOCOL,
            instance_id="i", capabilities=FULL_CAPS,
        )
        dumped = json.dumps(state.nodes_view())
        assert token not in dumped
        assert WEB_TOKEN not in dumped

    def test_legacy_direct_nodes_appear_labeled_without_secrets(self, state):
        legacy_env = {
            "HOLDSPEAK_STEER_NODES": json.dumps(
                {"old-box": {"base_url": "http://10.0.0.9:8765", "token": "LEGACY-SECRET"}}
            )
        }
        view = state.nodes_view(legacy_env=legacy_env)
        row = next(r for r in view["nodes"] if r["name"] == "old-box")
        assert row["kind"] == "legacy-direct"
        assert row["status"] == "unknown"  # honest: no liveness truth
        dumped = json.dumps(view)
        assert "LEGACY-SECRET" not in dumped
        assert "10.0.0.9" not in dumped

    def test_linked_node_shadows_its_legacy_row(self, state, store):
        _, token = store.create("old-box")
        state.hello(
            "old-box", token, node_protocol=NODE_PROTOCOL,
            instance_id="i", capabilities=FULL_CAPS,
        )
        legacy_env = {
            "HOLDSPEAK_STEER_NODES": json.dumps({"old-box": {"base_url": "u", "token": "t"}})
        }
        rows = state.nodes_view(legacy_env=legacy_env)["nodes"]
        assert [r["kind"] for r in rows if r["name"] == "old-box"] == ["node-link"]


# ── one behavior suite, two providers (§2 rule 14) ───────────────────


class _LocalDriver:
    """The embedded local node, driven through LocalNodeAdapter."""

    def __init__(self, state: NodeLinkState, name: str) -> None:
        self.state = state
        self.name = name
        self.adapter = LocalNodeAdapter(state, name=name, capabilities=FULL_CAPS)

    def hello(self):
        return self.adapter.start()

    def heartbeat(self, events=None):
        return self.adapter.heartbeat(events)

    def status(self):
        return self.state.status_of(self.name)


class _RemoteDriver:
    """The same verbs over the HTTP router — a remote node's view."""

    def __init__(self, state: NodeLinkState, name: str) -> None:
        self.state = state
        self.name = name
        _, self.token = state.token_store.ensure(name)
        app = FastAPI()
        app.include_router(
            build_delivery_node_router(WebContext(get_state=lambda: {}), link=state)
        )
        self.client = TestClient(app)

    def _call(self, path: str, payload: dict):
        response = self.client.post(
            path, json=payload, headers={"X-HoldSpeak-Node-Token": self.token}
        )
        body = response.json()
        if response.status_code >= 400:
            raise NodeLinkError(str(body.get("error") or "refused"))
        return body

    def hello(self):
        return self._call(
            "/api/delivery/node/hello",
            {
                "node_protocol": NODE_PROTOCOL,
                "name": self.name,
                "instance_id": "remote-inst",
                "capabilities": FULL_CAPS,
                "resume_cursor": 0,
            },
        )

    def heartbeat(self, events=None):
        return self._call(
            "/api/delivery/node/heartbeat",
            {"name": self.name, "events": events or []},
        )

    def status(self):
        return self.state.status_of(self.name)


@pytest.fixture(params=["local", "remote"])
def driver(request, state):
    if request.param == "local":
        return _LocalDriver(state, "local")
    return _RemoteDriver(state, "far-node")


class TestProviderParity:
    """Local and remote providers pass the SAME contract suite."""

    def test_hello_registers_and_goes_live(self, driver):
        response = driver.hello()
        assert response["ok"] is True
        assert response["commands_enabled"] is True
        assert driver.status() == "live"

    def test_event_cursor_and_duplicate_discipline(self, driver):
        driver.hello()
        assert driver.heartbeat([_event(1), _event(2)])["cursor"] == 2
        replay = driver.heartbeat([_event(1), _event(2)])
        assert (replay["cursor"], replay["accepted"]) == (2, 0)

    def test_liveness_decay_and_revival(self, driver, clock):
        driver.hello()
        clock.advance(16)
        assert driver.status() == "stale"
        clock.advance(15)
        assert driver.status() == "offline"
        driver.heartbeat()
        assert driver.status() == "live"

    def test_revocation_takes_effect_immediately(self, driver, state):
        driver.hello()
        state.token_store.revoke(driver.name)
        with pytest.raises(NodeLinkError):
            driver.heartbeat()

    def test_smuggled_field_refused(self, driver):
        driver.hello()
        with pytest.raises(NodeLinkError):
            driver.heartbeat([{"seq": 1, "kind": "rail.cursor", "body": "content"}])
        assert driver.heartbeat()["cursor"] == 0
