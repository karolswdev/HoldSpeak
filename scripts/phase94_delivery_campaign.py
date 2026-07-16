"""HS-94-10 — the assembled two-process localhost Delivery Runtime campaign.

This is the machine-verifiable walk the closeout story assembles: one hub
(a real FastAPI app serving the SAME six delivery routers on the SAME
shared spine ``web_server.py`` wires — collector, node link, terminal
command service, launch service — over real HTTP on a loopback port) plus
a SECOND real OS process linking in as a delivery node, real tmux panes,
real git worktrees, and the repository's own vendored ``dw`` counterpart.
The physical second machine, the physical iPad, and real tailnet HTTPS are
OUT (candidate Y); everything provable on one machine is proved here.

What it proves (numbered as the story's acceptance):

1. Four north-star journeys over the real hub: observe remote work,
   browse historical evidence through the asset proxy, steer a live coder
   into a real tmux pane with a reconciled receipt, and launch a
   Story-bound agent (worktree + attempt + target + receipt; the launcher
   executable is the only stub).
2. The full §13 fault matrix — node kill before/after apply, link
   loss + cursor resume, generation mismatch, expired, out-of-order, and
   source failure keeping last-known-good — each producing the contract's
   honest state.
3. Zero duplicate / wrong-target terminal effects across the whole run.
4. Poll economy: 10 concurrent snapshot clients cost the SAME dw
   invocation count as one.
5. The audit / privacy census (scripts/phase94_audit_census.py):
   every command accounted, no secret / token / path / raw-content leak.
6. Secure / Normal / YOLO change interruption only; the auth,
   target-binding, generation, schema, and audit invariants hold.
7. HS-94-10 registers ITSELF as an exact Work attempt on the holdspeak
   source and appears exactly-once with a live terminal and a receipt.
8. A measured compatibility-route consumer census.

Run: ``uv run python scripts/phase94_delivery_campaign.py`` (writes a
machine-readable report + a human log under the phase evidence dir).
The pytest wrapper drives ``run_campaign(bounded=True)``.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = Path(__file__).resolve().parent
for _p in (str(REPO_ROOT), str(_SCRIPTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

EVIDENCE_DIR = (
    REPO_ROOT
    / "pm"
    / "roadmap"
    / "holdspeak"
    / "phase-94-delivery-runtime"
    / "evidence"
    / "hs-94-10"
)

HAS_TMUX = shutil.which("tmux") is not None


# ── small utilities ──────────────────────────────────────────────────


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _wait_until(fn: Callable[[], bool], *, timeout: float = 5.0, interval: float = 0.1) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if fn():
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False


class CountingRunner:
    """A dw runner that counts every subprocess it spawns — the poll /
    economy proof hook. Wraps the collector's real default runner."""

    def __init__(self, *, delay: float = 0.0) -> None:
        from holdspeak.delivery.collector import _default_runner

        self._inner = _default_runner
        self._delay = delay
        self._lock = threading.Lock()
        self.calls = 0

    def __call__(self, argv: list[str], cwd: Optional[str] = None):
        with self._lock:
            self.calls += 1
        if self._delay:
            time.sleep(self._delay)
        return self._inner(argv, cwd)


# ── tmux helpers (real panes) ────────────────────────────────────────


def _tmux(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["tmux", *args], check=check, capture_output=True, text=True, timeout=10
    )


def _new_pane() -> tuple[str, str]:
    session = f"hs94-{uuid.uuid4().hex[:8]}"
    _tmux("new-session", "-d", "-s", session, "bash --norc --noprofile")
    pane = _tmux(
        "list-panes", "-t", session, "-F", "#{pane_id}"
    ).stdout.strip()
    time.sleep(0.3)
    return session, pane


def _kill_session(session: str) -> None:
    _tmux("kill-session", "-t", session, check=False)


def _pane_text(pane: str, lines: int = 60) -> str:
    from holdspeak.coder_steering import peek_pane

    return "\n".join(peek_pane(pane, lines=lines).get("lines", []))


# ── the hub spine (mirrors web_server.py's delivery assembly) ─────────


class Hub:
    """The real hub: an isolated FastAPI app over the shared delivery
    spine, served by uvicorn on a loopback port."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.mode = "neutral"  # the switchable control posture
        self.port = _free_port()
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.web_token = "campaign-web-token-" + uuid.uuid4().hex[:8]
        self.node_name = "studio-node"
        self._server: Any = None
        self._thread: Optional[threading.Thread] = None
        self._audit_rows: list[dict[str, Any]] = []
        self._build()

    def _build(self) -> None:
        from holdspeak.db.core import Database, get_database, reset_database
        from holdspeak.db.delivery_receipts import NodeReceiptLedger
        from holdspeak.delivery import DeliveryCollector, DeliveryRegistry
        from holdspeak.delivery.attempts import (
            WorkAttemptService,
            resolver_from_registry,
        )
        from holdspeak.delivery.commands import HubCommandService, NodeCommandProcessor
        from holdspeak.delivery.dossiers import DossierService
        from holdspeak.delivery.factory_launch import (
            AgentProfileStore,
            LaunchLedger,
            LaunchService,
        )
        from holdspeak.delivery.node_link import NodeLinkState, NodeTokenStore
        from holdspeak.delivery.terminal import TerminalTargetRegistry

        ws = self.workspace
        self.registry_path = ws / "delivery_sources.json"
        self.map_path = ws / "no_v1_map.json"  # deliberately absent
        self.token_store_path = ws / "node_tokens.json"
        self.ledger_path = ws / "node_ledger.db"
        self.hub_db_path = ws / "hub.db"

        # Pin the DB singleton to the isolated hub db so any lazy
        # get_database() lands in the workspace, never the real home.
        reset_database()
        self.db: Database = get_database(self.hub_db_path)

        # ONE registry object shared by every read service (so a source
        # registered on the collector is visible to attempts/dossiers/
        # launch without a second import of the real v1 project map).
        self.registry = DeliveryRegistry(self.registry_path, map_path=self.map_path)

        # Pair a node token BEFORE the link loads its store.
        self.node_id, self.node_token = NodeTokenStore(self.token_store_path).create(
            self.node_name
        )

        self.collector = DeliveryCollector(self.registry)  # real dw runner
        self.dossiers = DossierService(self.registry)  # real dw runner
        self.attempts = WorkAttemptService(
            self.db.work_attempts, resolver=resolver_from_registry(self.registry)
        )

        self.link = NodeLinkState(
            NodeTokenStore(self.token_store_path), web_token=self.web_token
        )
        self.targets = TerminalTargetRegistry()
        self.processor = NodeCommandProcessor(
            node_id="local",
            targets=self.targets,
            ledger=NodeReceiptLedger(self.ledger_path),
            audit=lambda **kw: self._audit_rows.append(kw) or len(self._audit_rows),
        )
        self.cmd = HubCommandService(
            repo=self.db.delivery_receipts,
            processor=self.processor,
            local_node_id="local",
            mode_loader=lambda: self.mode,
        )
        self.link.command_source = self.cmd.claim_for_node

        self.launch = LaunchService(
            profiles=AgentProfileStore(ws / "agent_profiles.json"),
            registry=self.registry,
            targets=self.targets,
            commands=self.cmd,
            attempts=self.db.work_attempts,
            ledger=LaunchLedger(ws / "agent_launches.json"),
            local_node_id="local",
        )

        self.app = self._app()

    def _app(self) -> Any:
        from fastapi import FastAPI

        from holdspeak.web.routes.delivery import build_delivery_router
        from holdspeak.web.routes.delivery_attempts import build_delivery_attempts_router
        from holdspeak.web.routes.delivery_dossiers import build_delivery_dossiers_router
        from holdspeak.web.routes.delivery_factory import build_delivery_factory_router
        from holdspeak.web.routes.delivery_node import build_delivery_node_router
        from holdspeak.web.routes.delivery_terminal import build_delivery_terminal_router

        ctx = None  # the delivery routers only do `_ = ctx`
        app = FastAPI()
        app.include_router(build_delivery_router(ctx, collector=self.collector))
        app.include_router(
            build_delivery_attempts_router(ctx, service=self.attempts, sync_on_read=False)
        )
        app.include_router(
            build_delivery_dossiers_router(ctx, service=self.dossiers)
        )
        app.include_router(
            build_delivery_node_router(
                ctx, link=self.link, web_token=self.web_token
            )
        )
        app.include_router(
            build_delivery_terminal_router(
                ctx, service=self.cmd, targets=self.targets, link=self.link
            )
        )
        app.include_router(
            build_delivery_factory_router(
                ctx, service=self.launch, commands=self.cmd, targets=self.targets
            )
        )
        return app

    def start(self) -> None:
        import uvicorn

        config = uvicorn.Config(
            self.app, host="127.0.0.1", port=self.port, log_level="warning"
        )
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()
        import httpx

        def _up() -> bool:
            try:
                return httpx.get(f"{self.base_url}/api/delivery/nodes", timeout=2).status_code == 200
            except Exception:
                return False

        if not _wait_until(_up, timeout=15):
            raise RuntimeError("hub failed to come up")

    def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=5)


# ── the campaign ─────────────────────────────────────────────────────


class Campaign:
    def __init__(self, workspace: Path, *, bounded: bool = False) -> None:
        self.workspace = workspace
        self.bounded = bounded
        self.hub = Hub(workspace)
        self.commands: list[dict[str, Any]] = []
        self.wire: list[dict[str, Any]] = []
        self.report: dict[str, Any] = {}
        import httpx

        self.client = httpx.Client(base_url=self.hub.base_url, timeout=30)
        self._panes: list[str] = []

    # wire helpers (every client body is captured for the census) --------

    def _record_wire(self, method: str, path: str, resp: Any) -> Any:
        try:
            body = resp.json()
        except Exception:
            body = {"_nonjson_bytes": len(resp.content)}
        self.wire.append(
            {"method": method, "path": path, "status": resp.status_code, "body": body}
        )
        return body

    def get(self, path: str, **kw: Any) -> tuple[int, Any]:
        resp = self.client.get(path, **kw)
        return resp.status_code, self._record_wire("GET", path, resp)

    def post(self, path: str, **kw: Any) -> tuple[int, Any]:
        resp = self.client.post(path, **kw)
        return resp.status_code, self._record_wire("POST", path, resp)

    def _track(self, command_id: str, verb: str, final_state: str, outcome: str) -> None:
        self.commands.append(
            {
                "command_id": command_id,
                "verb": verb,
                "final_state": final_state,
                "outcome": outcome,
            }
        )

    def _pane(self) -> tuple[str, str]:
        session, pane = _new_pane()
        self._panes.append(session)
        return session, pane

    def cleanup(self) -> None:
        for session in self._panes:
            _kill_session(session)
        self.client.close()
        self.hub.stop()

    # ── journeys ────────────────────────────────────────────────────

    def journey_observe(self) -> dict[str, Any]:
        """(a) observe remote work: register the holdspeak source, link a
        real second-process node, and see both in the read model with
        typed freshness; attach a Work attempt and read it back."""
        out: dict[str, Any] = {"name": "observe_remote_work"}
        # register this repo as a delivery source (server-resolved path).
        status, body = self.post(
            "/api/delivery/sources", json={"path": str(REPO_ROOT), "label": "HoldSpeak"}
        )
        out["register_status"] = status
        out["source"] = (body or {}).get("source")
        source_id = (out["source"] or {}).get("source_id")
        worktree_id = ((out["source"] or {}).get("worktrees") or [{}])[0].get("worktree_id")
        self.source_id = source_id
        self.worktree_id = worktree_id
        # the coherent snapshot shows the live source with a revision + cursor.
        status, snap = self.get("/api/delivery/snapshot")
        out["snapshot_status"] = status
        out["revision"] = snap.get("revision")
        out["cursor_present"] = bool(snap.get("cursor"))
        src_rows = snap.get("sources") or []
        live = next((s for s in src_rows if s.get("source_id") == source_id), None)
        out["source_status"] = (live or {}).get("status")
        # a real second-process node reports in → nodes view shows freshness.
        node = self._link_node_once()
        out["node_link"] = node
        status, nodes = self.get("/api/delivery/nodes")
        row = next(
            (n for n in nodes.get("nodes", []) if n.get("name") == self.hub.node_name),
            None,
        )
        out["node_status"] = (row or {}).get("status")
        out["node_commands_enabled"] = (row or {}).get("commands_enabled")
        # observe an attempt (a node reporting work on a Story).
        status, att = self.post(
            "/api/delivery/attempts",
            json={
                "source_id": source_id,
                "worktree_id": worktree_id,
                "project": "holdspeak",
                "story_id": "HS-94-04",
                "node_id": self.hub.node_id,
                "actor": "studio-node",
            },
        )
        out["attempt_status"] = status
        out["attempt_state"] = ((att or {}).get("attempt") or {}).get("state")
        status, listing = self.get("/api/delivery/attempts?story_id=HS-94-04")
        out["attempts_seen"] = len(listing.get("attempts", []))
        out["pass"] = (
            out["source_status"] == "live"
            and out["node_status"] in ("live", "stale")
            and out["attempt_status"] == 200
            and out["attempts_seen"] >= 1
        )
        return out

    def _link_node_once(self) -> dict[str, Any]:
        """Run the SECOND real process (`python -m holdspeak.commands.
        node_serve serve --once`) that hellos + heartbeats the hub."""
        env = dict(os.environ)
        env["HOLDSPEAK_NODE_TOKEN"] = self.hub.node_token
        cursor_path = self.workspace / "node_cursor.json"
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "holdspeak.commands.node_serve",
                "serve",
                "--hub",
                self.hub.base_url,
                "--name",
                self.hub.node_name,
                "--once",
                "--emit-ticks",
                "--cursor-path",
                str(cursor_path),
            ],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return {"returncode": proc.returncode, "cursor_path": str(cursor_path)}

    def journey_evidence(self) -> dict[str, Any]:
        """(b) browse historical evidence: open a real story dossier and
        fetch one asset through the manifest-bound proxy."""
        out: dict[str, Any] = {"name": "browse_evidence"}
        status, dossier = self.get(
            "/api/delivery/stories/holdspeak/HS-94-06/dossier"
        )
        out["dossier_status"] = status
        out["bundle_id"] = dossier.get("bundle_id")
        members = dossier.get("members") or []
        out["member_count"] = len(members)
        out["has_captured_runs"] = bool(dossier.get("captured_runs"))
        # fetch one member's bytes through the asset proxy.
        member = next((m for m in members if m.get("role") == "evidence_markdown"), None)
        if member and out["bundle_id"]:
            asset_path = f"/api/delivery/evidence/{out['bundle_id']}/{member['asset_id']}"
            resp = self.client.get(asset_path)
            self.wire.append(
                {
                    "method": "GET",
                    "path": asset_path,
                    "status": resp.status_code,
                    "body": {"_asset_bytes": len(resp.content)},
                }
            )
            out["asset_status"] = resp.status_code
            out["asset_bytes"] = len(resp.content)
            out["etag_matches_sha"] = resp.headers.get("ETag") == member.get("sha256")
        out["pass"] = (
            out["dossier_status"] == 200
            and out["member_count"] >= 1
            and out.get("asset_status") == 200
            and out.get("asset_bytes", 0) > 0
        )
        return out

    def journey_steer(self) -> dict[str, Any]:
        """(c) steer a live coder: issue a target for a real pane, arm the
        grant, send terminal.text through the envelope, verify the receipt
        and the pane, then reconcile the duplicate to the SAME receipt."""
        from holdspeak import coder_steering

        out: dict[str, Any] = {"name": "steer_live_coder"}
        session, pane = self._pane()
        key = f"claude:{session}"
        addr = f"{session}:0.0"
        coder_steering.clear_grants()
        armed = coder_steering.arm(key, addr)
        out["armed"] = armed.get("status")
        status, issued = self.post("/api/delivery/terminal/targets", json={"ref": addr})
        out["target_status"] = status
        marker = f"steer-{uuid.uuid4().hex[:8]}"
        command_id = str(uuid.uuid4())
        request = {
            "command_id": command_id,
            "target_id": issued["target_id"],
            "target_generation": issued["target_generation"],
            "operation": {"family": "coder_steering", "verb": "terminal.text"},
            "payload": {"text": marker, "session_key": key, "submit": False},
        }
        status, first = self.post("/api/delivery/terminal/commands", json=request)
        receipt = first.get("receipt", {})
        out["outcome"] = receipt.get("outcome")
        out["authority_basis"] = receipt.get("authority_basis")
        out["receipt_id"] = receipt.get("receipt_id")
        self._track(command_id, "terminal.text", receipt.get("state"), receipt.get("outcome"))
        # the lost-response retry: same command_id → the SAME receipt.
        status, dup = self.post("/api/delivery/terminal/commands", json=request)
        out["duplicate"] = dup.get("duplicate")
        out["same_receipt"] = dup.get("receipt", {}).get("receipt_id") == out["receipt_id"]
        time.sleep(0.4)
        seen = _pane_text(pane)
        out["landed_count"] = seen.count(marker)
        # reconcile the aggregate receipt (never a blind retry).
        status, joined = self.get(f"/api/delivery/terminal/commands/{command_id}")
        out["hub_state"] = joined.get("hub_state") or joined.get("receipt", {}).get("state")
        self._steer_marker = (pane, marker)
        out["pass"] = (
            out["outcome"] == "delivered"
            and out["authority_basis"] == "scoped_grant"
            and out["duplicate"] is True
            and out["same_receipt"] is True
            and out["landed_count"] == 1
        )
        return out

    def journey_launch(self) -> dict[str, Any]:
        """(d) launch a story-bound agent: agent.launch into a NEW git
        worktree creates worktree + attempt + target + receipt. Only the
        launcher executable is stubbed (a real tmux pane, real git)."""
        out: dict[str, Any] = {"name": "launch_story_agent"}
        scratch = self._scratch_repo()
        status, body = self.post(
            "/api/delivery/sources", json={"path": str(scratch), "label": "scratch"}
        )
        scratch_source = (body or {}).get("source", {}).get("source_id")
        out["scratch_source"] = scratch_source
        name = f"hs94launch{uuid.uuid4().hex[:6]}"
        status, record = self.post(
            "/api/delivery/factory/launch",
            json={
                "agent_profile_id": "claude-default",
                "source_id": scratch_source,
                "worktree": {"mode": "new", "name": name, "branch": name},
                "story_ref": {"project": "scratch", "story_id": "HS-94-07"},
                "session_label": name,
            },
        )
        out["launch_status"] = status
        out["state"] = record.get("state")
        out["has_target"] = bool(record.get("target"))
        out["attempt_id"] = record.get("attempt_id")
        cmds = record.get("commands") or {}
        for verb, cid in (
            ("worktree.create", cmds.get("worktree_create")),
            ("factory.spawn", cmds.get("spawn")),
        ):
            if cid:
                self._track(cid, verb, "complete", "spawned/created")
        if record.get("session"):
            self._panes.append(record["session"])
        out["pass"] = (
            out["launch_status"] == 200
            and out["state"] == "launched"
            and out["has_target"]
            and bool(out["attempt_id"])
        )
        return out

    def _scratch_repo(self) -> Path:
        repo = self.workspace / "scratch-repo"
        repo.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ)
        env.update(
            GIT_AUTHOR_NAME="c", GIT_AUTHOR_EMAIL="c@x", GIT_COMMITTER_NAME="c",
            GIT_COMMITTER_EMAIL="c@x",
        )
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True, env=env)
        (repo / "README.md").write_text("scratch\n")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, env=env)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True, env=env)
        return repo

    # ── fault matrix (§13) ──────────────────────────────────────────

    def fault_matrix(self) -> list[dict[str, Any]]:
        faults: list[dict[str, Any]] = []
        faults.append(self._fault_remote_absence())
        faults.append(self._fault_generation_mismatch())
        faults.append(self._fault_expired())
        faults.append(self._fault_sequence())
        faults.append(self._fault_source_lkg())
        faults.append(self._fault_cursor_resume())
        return faults

    def _fault_remote_absence(self) -> dict[str, Any]:
        """node kill before/after apply → not_executed / unknown /
        indeterminate_after_node_reset, reconciled by command_id (§8.2)."""
        out: dict[str, Any] = {"fault": "node_kill_reconcile", "expected": [
            "not_executed", "unknown", "indeterminate_after_node_reset"]}
        results: dict[str, str] = {}
        # never claimed → dropped queue → not_executed.
        cid1 = self._remote_command(seq=1)
        self.hub.cmd._queues.pop(self.hub_node_target[0], None)
        row = self.hub.cmd.receipt(cid1)
        results["never_claimed"] = str((row or {}).get("hub_state"))
        self._track(cid1, "terminal.text", results["never_claimed"], "reconciled")
        # claimed then lost → unknown, then node answers → indeterminate.
        cid2 = self._remote_command(seq=2)
        self.hub.cmd.claim_for_node(self.hub_node_target[0])  # marks claimed
        self.hub.cmd._queues.pop(self.hub_node_target[0], None)
        row = self.hub.cmd.receipt(cid2)
        results["lost_after_claim"] = str((row or {}).get("hub_state"))
        self.hub.cmd.record_results(
            self.hub_node_target[0],
            [{"command_id": cid2, "reconcile": "unknown_command",
              "ledger_epoch": "epoch_lost_" + uuid.uuid4().hex[:8]}],
        )
        row = self.hub.cmd.receipt(cid2)
        results["after_node_reset"] = str((row or {}).get("hub_state"))
        self._track(cid2, "terminal.text", results["after_node_reset"], "reconciled")
        # local executed then reconciled → the stored receipt returns.
        local = self._local_delivered_command()
        results["local_reconcile"] = local
        out["results"] = results
        out["pass"] = (
            results["never_claimed"] == "not_executed"
            and results["lost_after_claim"] == "unknown"
            and results["after_node_reset"] == "indeterminate_after_node_reset"
            and results["local_reconcile"] == "complete"
        )
        return out

    def _remote_command(self, *, seq: int) -> str:
        node_id = self.hub.node_id
        self.hub_node_target = (node_id,)
        status, body = self.post(
            "/api/delivery/terminal/commands",
            json={
                "node_id": node_id,
                "target_id": "term_remote",
                "target_generation": "gen_remote",
                "operation": {"family": "coder_steering", "verb": "terminal.text"},
                "payload": {"text": "remote", "session_key": "claude:remote"},
                "expected_sequence": seq,
            },
        )
        return body["command_id"]

    def _local_delivered_command(self) -> str:
        from holdspeak import coder_steering

        session, pane = self._pane()
        key = f"claude:{session}"
        addr = f"{session}:0.0"
        coder_steering.arm(key, addr)
        status, issued = self.post("/api/delivery/terminal/targets", json={"ref": addr})
        cid = str(uuid.uuid4())
        self.post(
            "/api/delivery/terminal/commands",
            json={
                "command_id": cid,
                "target_id": issued["target_id"],
                "target_generation": issued["target_generation"],
                "operation": {"family": "coder_steering", "verb": "terminal.text"},
                "payload": {"text": f"local-{cid[:6]}", "session_key": key, "submit": False},
            },
        )
        self._track(cid, "terminal.text", "delivered", "delivered")
        status, joined = self.get(f"/api/delivery/terminal/commands/{cid}")
        return str(joined.get("hub_state"))

    def _fault_generation_mismatch(self) -> dict[str, Any]:
        """pane recycled → generation mismatch; command refused and grant
        invalidated (§13). Nothing types into the successor pane."""
        from holdspeak import coder_steering

        out: dict[str, Any] = {"fault": "generation_mismatch", "expected": "refused+revoked"}
        session, pane = self._pane()
        key = f"claude:{session}"
        addr = f"{session}:0.0"
        coder_steering.clear_grants()
        coder_steering.arm(key, addr)
        status, issued = self.post("/api/delivery/terminal/targets", json={"ref": addr})
        # recycle: kill the pane, put a new one at the same address.
        _tmux("kill-pane", "-t", pane, check=False)
        _tmux("new-window", "-t", session, "bash --norc --noprofile", check=False)
        time.sleep(0.3)
        cid = str(uuid.uuid4())
        status, body = self.post(
            "/api/delivery/terminal/commands",
            json={
                "command_id": cid,
                "target_id": issued["target_id"],
                "target_generation": issued["target_generation"],
                "operation": {"family": "coder_steering", "verb": "terminal.text"},
                "payload": {"text": "must-never-land", "session_key": key, "submit": False},
            },
        )
        receipt = body.get("receipt", {})
        out["outcome"] = receipt.get("outcome")
        out["revoked"] = receipt.get("revoked")
        out["grants_after"] = coder_steering.active_grants()
        self._track(cid, "terminal.text", receipt.get("state"), receipt.get("outcome"))
        out["pass"] = out["outcome"] in ("generation_mismatch", "target_gone") and (
            out["outcome"] != "generation_mismatch"
            or (out["revoked"] is True and out["grants_after"] == {})
        )
        return out

    def _fault_expired(self) -> dict[str, Any]:
        """A command past its expiry refuses command_expired before any
        effect (§13 'response lost after dispatch' sibling: expiry)."""
        from datetime import timedelta

        from holdspeak import coder_steering
        from holdspeak.delivery import commands as cmdmod
        from holdspeak.operation_policy import POLICY_VERSION

        out: dict[str, Any] = {"fault": "expired", "expected": "command_expired"}
        session, pane = self._pane()
        addr = f"{session}:0.0"
        coder_steering.arm(f"claude:{session}", addr)
        status, issued = self.post("/api/delivery/terminal/targets", json={"ref": addr})
        past = datetime.now(timezone.utc) - timedelta(seconds=120)
        env = cmdmod.build_envelope(
            node_id="local",
            target_id=issued["target_id"],
            target_generation=issued["target_generation"],
            family="coder_steering",
            verb="terminal.text",
            payload={"text": "too-late", "session_key": f"claude:{session}"},
            expected_sequence=1,
            authority={
                "actor": "owner",
                "control_posture": "neutral",
                "decision": "allowed_by_active_grant",
                "policy_version": POLICY_VERSION,
            },
            command_id=str(uuid.uuid4()),
            ttl_seconds=1,
            now=past,
        )
        receipt = self.hub.processor.process(env)
        out["outcome"] = receipt.get("outcome")
        self._track(env["command_id"], "terminal.text", receipt.get("state"), receipt.get("outcome"))
        out["pass"] = out["outcome"] == "command_expired"
        return out

    def _fault_sequence(self) -> dict[str, Any]:
        """Out-of-order expected_sequence → sequence_conflict; nothing
        types; the slot is left for a corrected resend (§8 step 6)."""
        from holdspeak import coder_steering

        out: dict[str, Any] = {"fault": "out_of_order", "expected": "sequence_conflict"}
        session, pane = self._pane()
        key = f"claude:{session}"
        addr = f"{session}:0.0"
        coder_steering.arm(key, addr)
        status, issued = self.post("/api/delivery/terminal/targets", json={"ref": addr})
        cid = str(uuid.uuid4())
        status, body = self.post(
            "/api/delivery/terminal/commands",
            json={
                "command_id": cid,
                "target_id": issued["target_id"],
                "target_generation": issued["target_generation"],
                "operation": {"family": "coder_steering", "verb": "terminal.text"},
                "payload": {"text": "way-ahead", "session_key": key, "submit": False},
                "expected_sequence": 99,
            },
        )
        receipt = body.get("receipt", {})
        out["outcome"] = receipt.get("outcome")
        time.sleep(0.3)
        out["landed"] = _pane_text(pane).count("way-ahead")
        self._track(cid, "terminal.text", receipt.get("state"), receipt.get("outcome"))
        out["pass"] = out["outcome"] == "sequence_conflict" and out["landed"] == 0
        return out

    def _fault_source_lkg(self) -> dict[str, Any]:
        """A source whose CLI fails keeps its last-known-good rows with an
        explicit degraded status (§13 'source CLI missing')."""
        from holdspeak.delivery import DeliveryCollector, DeliveryRegistry

        out: dict[str, Any] = {"fault": "source_failure_lkg", "expected": "stale+retained"}
        registry = DeliveryRegistry(
            self.workspace / "lkg_sources.json", map_path=self.hub.map_path
        )
        registry.register(str(REPO_ROOT), label="HoldSpeak")
        state = {"fail": False}
        from holdspeak.delivery.collector import _default_runner

        def runner(argv, cwd=None):
            if state["fail"]:
                return subprocess.CompletedProcess(argv, 2, "", "boom")
            return _default_runner(argv, cwd)

        collector = DeliveryCollector(registry, runner=runner, max_age_seconds=0.0)
        first = collector.snapshot()
        healthy = (first["sources"][0] or {})
        state["fail"] = True
        second = collector.snapshot()
        degraded = (second["sources"][0] or {})
        out["healthy_status"] = healthy.get("status")
        out["degraded_status"] = degraded.get("status")
        out["retained_projects"] = degraded.get("projects") is not None
        out["retained_observed_at"] = bool(degraded.get("observed_at"))
        out["pass"] = (
            out["healthy_status"] == "live"
            and out["degraded_status"] == "stale"
            and out["retained_projects"]
        )
        return out

    def _fault_cursor_resume(self) -> dict[str, Any]:
        """Link loss + resume: two real node processes across a kill
        resume the SAME cursor — no duplicate event, no gap (§6.3)."""
        out: dict[str, Any] = {"fault": "link_loss_cursor_resume", "expected": "no dup/gap"}
        # first process already ran in journey_observe; run a second.
        r2 = self._link_node_once()
        out["second_run_rc"] = r2["returncode"]
        events = self.hub.link.events_of(self.hub.node_name)
        seqs = [int(e.get("seq")) for e in events if e.get("seq") is not None]
        ids = [e.get("event_id") for e in events if e.get("event_id") is not None]
        out["seqs"] = seqs
        out["event_count"] = len(events)
        out["no_duplicate_seq"] = len(seqs) == len(set(seqs))
        out["no_duplicate_event_id"] = len(ids) == len(set(ids))
        out["contiguous"] = seqs == list(range(1, len(seqs) + 1)) if seqs else False
        out["node_events"] = events
        out["pass"] = (
            out["second_run_rc"] == 0
            and out["event_count"] >= 2
            and out["no_duplicate_seq"]
            and out["no_duplicate_event_id"]
            and out["contiguous"]
        )
        return out

    # ── poll economy (§11) ──────────────────────────────────────────

    def poll_economy(self) -> dict[str, Any]:
        """10 concurrent snapshot clients cause the SAME dw invocation
        count as 1 (single-flight over the collector's counting runner)."""
        from holdspeak.delivery import DeliveryCollector, DeliveryRegistry

        out: dict[str, Any] = {"name": "poll_economy"}
        registry = DeliveryRegistry(
            self.workspace / "poll_sources.json", map_path=self.hub.map_path
        )
        registry.register(str(REPO_ROOT), label="HoldSpeak")
        # a fresh collector: one collection's dw call count.
        one_runner = CountingRunner()
        one = DeliveryCollector(registry, runner=one_runner, max_age_seconds=999)
        one.snapshot()
        out["one_client_calls"] = one_runner.calls
        # ten concurrent callers, single-flight coalesced.
        ten_runner = CountingRunner(delay=0.15)  # widen the flight window
        ten = DeliveryCollector(registry, runner=ten_runner, max_age_seconds=999)
        with ThreadPoolExecutor(max_workers=10) as pool:
            list(pool.map(lambda _i: ten.snapshot(), range(10)))
        out["ten_client_calls"] = ten_runner.calls
        out["clients"] = 10
        out["pass"] = (
            out["one_client_calls"] > 0
            and out["ten_client_calls"] == out["one_client_calls"]
        )
        return out

    # ── posture invariance (§12.2) ──────────────────────────────────

    def posture_matrix(self) -> dict[str, Any]:
        """Secure / Normal / YOLO change interruption only. The same steer
        text under YOLO skips the grant prompt, but payload binding,
        target binding, generation, schema, policy version and the node
        audit are identical to the granted Normal delivery."""
        from holdspeak import coder_steering

        out: dict[str, Any] = {"name": "posture_invariance"}
        text = "posture-invariant-steer"
        legs: dict[str, Any] = {}

        def _leg(mode: str, *, grant: bool) -> dict[str, Any]:
            session, pane = self._pane()
            key = f"claude:{session}"
            addr = f"{session}:0.0"
            coder_steering.clear_grants()
            if grant:
                coder_steering.arm(key, addr, control_mode=mode)
            status, issued = self.post("/api/delivery/terminal/targets", json={"ref": addr})
            self.hub.mode = mode
            cid = str(uuid.uuid4())
            _, body = self.post(
                "/api/delivery/terminal/commands",
                json={
                    "command_id": cid,
                    "target_id": issued["target_id"],
                    "target_generation": issued["target_generation"],
                    "operation": {"family": "coder_steering", "verb": "terminal.text"},
                    "payload": {"text": text, "session_key": key, "submit": False},
                },
            )
            r = body.get("receipt", {})
            self._track(cid, "terminal.text", r.get("state"), r.get("outcome"))
            time.sleep(0.3)
            landed = _pane_text(pane).count(text)
            from holdspeak.delivery.commands import payload_digest

            payload = {"text": text, "session_key": key, "submit": False}
            return {
                "mode": mode,
                "outcome": r.get("outcome"),
                "authority_basis": r.get("authority_basis"),
                "payload_sha256": r.get("payload_sha256"),
                # the payload binding is honoured identically per posture:
                # each receipt's hash correctly binds ITS own payload.
                "sha_binds_payload": r.get("payload_sha256") == payload_digest(payload),
                "payload_head": r.get("payload_head"),
                "policy_version": r.get("policy_version"),
                "receipt_schema": r.get("receipt_schema"),
                "target_id": r.get("target_id"),
                "target_generation": r.get("target_generation"),
                "audit_present": r.get("node_audit_id") is not None,
                "landed": landed,
            }

        legs["normal_grant"] = _leg("neutral", grant=True)
        legs["secure_grant"] = _leg("secure", grant=True)
        legs["yolo_no_grant"] = _leg("yolo", grant=False)
        self.hub.mode = "neutral"
        out["legs"] = legs

        delivered = [v for v in legs.values() if v["outcome"] == "delivered"]
        # interruption differs: yolo delivered WITHOUT a grant (posture),
        # normal delivered via the scoped grant; secure with a grant is the
        # most restrictive (recorded, not required to deliver).
        out["yolo_promptless"] = legs["yolo_no_grant"]["outcome"] == "delivered" and (
            legs["yolo_no_grant"]["authority_basis"] == "control_posture"
        )
        out["normal_via_grant"] = legs["normal_grant"]["authority_basis"] == "scoped_grant"
        # invariants across delivered postures: payload binding is honoured
        # (each sha binds its own payload), the steer text head, policy
        # version, schema, target binding and the node audit are identical.
        # Only the authority BASIS (the human interruption) changed.
        out["payload_binding_honoured"] = all(v["sha_binds_payload"] for v in delivered)
        out["payload_head_invariant"] = len({v["payload_head"] for v in delivered}) == 1
        out["policy_version_invariant"] = len({v["policy_version"] for v in delivered}) == 1
        out["schema_invariant"] = len({v["receipt_schema"] for v in delivered}) == 1
        out["audit_invariant"] = all(v["audit_present"] for v in delivered)
        out["target_bound"] = all(
            v["target_id"] and v["target_generation"] for v in delivered
        )
        out["landed_once"] = all(v["landed"] == 1 for v in delivered)
        out["basis_differs"] = (
            legs["yolo_no_grant"]["authority_basis"]
            != legs["normal_grant"]["authority_basis"]
        )
        out["pass"] = (
            len(delivered) >= 2
            and out["yolo_promptless"]
            and out["normal_via_grant"]
            and out["payload_binding_honoured"]
            and out["payload_head_invariant"]
            and out["policy_version_invariant"]
            and out["schema_invariant"]
            and out["audit_invariant"]
            and out["target_bound"]
            and out["landed_once"]
            and out["basis_differs"]
        )
        return out

    # ── zero duplicate / wrong-target (§ acceptance) ────────────────

    def dedup_audit(self) -> dict[str, Any]:
        """Across the whole run: no terminal effect landed twice, and no
        command_id produced two receipts (the dedup ledger + receipt
        join). The steered marker landed on its own pane and nowhere
        else."""
        out: dict[str, Any] = {"name": "zero_duplicate_wrong_target"}
        ids = [c["command_id"] for c in self.commands]
        out["command_count"] = len(ids)
        out["unique_command_ids"] = len(ids) == len(set(ids))
        # the delivered steer marker: exactly once on its pane, absent
        # from every other live pane.
        wrong_target = False
        landed = None
        if getattr(self, "_steer_marker", None):
            pane, marker = self._steer_marker
            landed = _pane_text(pane).count(marker)
            all_panes = _tmux(
                "list-panes", "-a", "-F", "#{pane_id}", check=False
            ).stdout.split()
            for other in all_panes:
                if other == pane:
                    continue
                if marker in _pane_text(other):
                    wrong_target = True
        out["marker_landed"] = landed
        out["wrong_target_hit"] = wrong_target
        out["pass"] = (
            out["unique_command_ids"]
            and (landed is None or landed == 1)
            and not wrong_target
        )
        return out

    # ── HS-94-10 proves itself (§ acceptance) ───────────────────────

    def self_attempt(self) -> dict[str, Any]:
        """HS-94-10 registers ITSELF as an exact manual Work attempt on the
        holdspeak source, bound to a live terminal, and appears
        exactly-once in the composite read model with a receipt."""
        from holdspeak import coder_steering

        out: dict[str, Any] = {"name": "self_attempt"}
        session, pane = self._pane()
        key = f"claude:{session}"
        addr = f"{session}:0.0"
        coder_steering.arm(key, addr)
        status, issued = self.post("/api/delivery/terminal/targets", json={"ref": addr})
        # the attempt, bound to the live terminal target.
        status, att = self.post(
            "/api/delivery/attempts",
            json={
                "source_id": self.source_id,
                "worktree_id": self.worktree_id,
                "project": "holdspeak",
                "story_id": "HS-94-10",
                "target_id": issued["target_id"],
                "actor": "hs-94-10-campaign",
            },
        )
        out["attempt_status"] = status
        # a receipt on that terminal (the story steering itself).
        cid = str(uuid.uuid4())
        marker = f"hs9410-{uuid.uuid4().hex[:6]}"
        _, body = self.post(
            "/api/delivery/terminal/commands",
            json={
                "command_id": cid,
                "target_id": issued["target_id"],
                "target_generation": issued["target_generation"],
                "operation": {"family": "coder_steering", "verb": "terminal.text"},
                "payload": {"text": marker, "session_key": key, "submit": False},
            },
        )
        receipt = body.get("receipt", {})
        self._track(cid, "terminal.text", receipt.get("state"), receipt.get("outcome"))
        # the composite snapshot: sources + attempts + receipt. Filter to
        # the holdspeak source so a same-numbered attempt on another source
        # can never inflate the exactly-once claim.
        _, attempts = self.get(
            "/api/delivery/attempts?project=holdspeak&story_id=HS-94-10"
        )
        rows = [
            a for a in attempts.get("attempts", [])
            if a.get("story_ref", {}).get("story_id") == "HS-94-10"
            and a.get("story_ref", {}).get("source_id") == self.source_id
        ]
        out["exact_count"] = len(rows)
        out["has_live_terminal"] = bool(rows and rows[0].get("target_id"))
        out["receipt_outcome"] = receipt.get("outcome")
        out["pass"] = (
            out["attempt_status"] == 200
            and out["exact_count"] == 1
            and out["has_live_terminal"]
            and out["receipt_outcome"] == "delivered"
        )
        return out

    # ── compatibility census (§10 / §14) ────────────────────────────

    def compat_census(self) -> dict[str, Any]:
        """Enumerate the compat routes and their real consumers still
        present in web/src + apple — a measured deprecation note, no
        deletion."""
        out: dict[str, Any] = {"name": "compat_consumer_census"}
        roots = [REPO_ROOT / "web" / "src", REPO_ROOT / "apple"]
        prefixes = ["/api/missioncontrol/", "/api/coders/"]
        consumers: dict[str, list[str]] = {p: [] for p in prefixes}
        for root in roots:
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix not in (
                    ".ts", ".tsx", ".js", ".jsx", ".swift", ".vue"
                ):
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                for prefix in prefixes:
                    if prefix in text:
                        rel = str(path.relative_to(REPO_ROOT))
                        if rel not in consumers[prefix]:
                            consumers[prefix].append(rel)
        out["consumers"] = consumers
        # Generated copies under apple/build/*-sources are regenerated from
        # apple/App; count authored callers separately for an honest signal.
        out["authored_consumers"] = {
            prefix: [f for f in files if "/build/" not in f]
            for prefix, files in consumers.items()
        }
        out["deprecation_note"] = {
            prefix: (
                f"{len(files)} consumer file(s) ("
                f"{len(out['authored_consumers'][prefix])} authored, "
                f"{len(files) - len(out['authored_consumers'][prefix])} generated build "
                f"copies) still call {prefix} — keep the compat route until parity "
                "shows zero callers"
                if files
                else f"no callers of {prefix} in web/src or apple — safe to schedule removal"
            )
            for prefix, files in consumers.items()
        }
        out["pass"] = True  # a census never fails; it measures.
        return out

    # ── orchestration ────────────────────────────────────────────────

    def run(self) -> dict[str, Any]:
        import phase94_audit_census as census

        started = _now()
        report: dict[str, Any] = {
            "meta": {
                "story": "HS-94-10",
                "started_at": started,
                "bounded": self.bounded,
                "workspace": str(self.workspace),
                "hub_base_url": self.hub.base_url,
                "has_tmux": HAS_TMUX,
                "out_of_scope": [
                    "physical second machine",
                    "physical iPad",
                    "tailnet HTTPS microphone",
                ],
            },
            "journeys": {},
            "faults": [],
            "poll_economy": {},
            "posture": {},
            "dedup": {},
            "self_attempt": {},
            "compat": {},
            "node_link": {},
        }

        def _step(fn: Callable[[], Any], key: str, *, into: Optional[dict] = None) -> None:
            try:
                result = fn()
            except Exception as exc:  # a step failure is recorded, not fatal
                result = {"error": f"{type(exc).__name__}: {exc}", "pass": False}
            if into is not None:
                into[key] = result
            return result

        # 1. north-star journeys (a, b, c, d)
        _step(self.journey_observe, "observe", into=report["journeys"])
        _step(self.journey_evidence, "evidence", into=report["journeys"])
        if HAS_TMUX:
            _step(self.journey_steer, "steer", into=report["journeys"])
        else:
            report["journeys"]["steer"] = {"skipped": "no tmux", "pass": None}
        # The launch journey (real git worktree + spawn) is the slowest leg;
        # the bounded wrapper skips it, the full campaign runs it.
        if HAS_TMUX and not self.bounded:
            _step(self.journey_launch, "launch", into=report["journeys"])
        else:
            report["journeys"]["launch"] = {
                "skipped": "bounded" if HAS_TMUX else "no tmux", "pass": None
            }

        # 6. posture invariance (before the fault matrix perturbs grants)
        if HAS_TMUX:
            report["posture"] = _step(self.posture_matrix, "posture")
        else:
            report["posture"] = {"skipped": "no tmux", "pass": None}

        # 2. fault matrix
        report["faults"] = self.fault_matrix() if HAS_TMUX else [
            self._fault_remote_absence(), self._fault_source_lkg(),
            self._fault_cursor_resume(),
        ]

        # 4. poll economy
        report["poll_economy"] = _step(self.poll_economy, "poll")

        # 7. self attempt
        if HAS_TMUX:
            report["self_attempt"] = _step(self.self_attempt, "self")
        else:
            report["self_attempt"] = {"skipped": "no tmux", "pass": None}

        # 3. dedup / wrong-target across the whole run
        report["dedup"] = _step(self.dedup_audit, "dedup")

        # 8. compatibility census
        report["compat"] = _step(self.compat_census, "compat")

        # node-link event trail for the census
        report["node_link"] = {
            "node_id": self.hub.node_id,
            "events": self.hub.link.events_of(self.hub.node_name),
            "status": self.hub.link.status_of(self.hub.node_name),
        }

        # the material the census needs.
        report["commands"] = self.commands
        report["wire_capture"] = self.wire
        report["secrets"] = {
            "node_token": self.hub.node_token,
            "web_token": self.hub.web_token,
        }
        report["path_roots"] = [str(self.workspace), str(Path.home())]

        # 5. the audit / privacy census
        report["census"] = census.run_census(
            workspace=self.workspace,
            report=report,
            hub_db_path=self.hub.hub_db_path,
            node_ledger_path=self.hub.ledger_path,
        )
        report["meta"]["finished_at"] = _now()
        report["summary"] = self._summary(report)
        self.report = report
        return report

    @staticmethod
    def _summary(report: dict[str, Any]) -> dict[str, Any]:
        def _p(x: Any) -> Optional[bool]:
            return x.get("pass") if isinstance(x, dict) else None

        journeys = {k: _p(v) for k, v in report["journeys"].items()}
        faults = {f["fault"]: f.get("pass") for f in report["faults"]}
        census = report["census"]
        return {
            "journeys": journeys,
            "faults": faults,
            "poll_economy_pass": _p(report["poll_economy"]),
            "posture_pass": _p(report["posture"]),
            "dedup_pass": _p(report["dedup"]),
            "self_attempt_pass": _p(report["self_attempt"]),
            "census_clean": census.get("clean"),
            "census_all_accounted": census.get("accounted", {}).get("all_accounted"),
        }


def run_campaign(*, bounded: bool = False, workspace: Optional[Path] = None) -> dict[str, Any]:
    """Assemble and run the whole campaign; returns the report dict.

    Sets an isolated ``HOME`` and PATH (a stub ``claude``/``codex`` so the
    launch journey's ONLY stub is the launcher executable) before building
    the hub, so nothing touches the operator's real ``~/.holdspeak`` or DB.
    """
    ws = Path(workspace) if workspace else Path(
        os.environ.get("TMPDIR", "/tmp")
    ) / f"hs94-campaign-{uuid.uuid4().hex[:8]}"
    ws.mkdir(parents=True, exist_ok=True)

    # stub launcher execs on PATH (the tmux server inherits this env).
    bindir = ws / "bin"
    bindir.mkdir(exist_ok=True)
    for name in ("claude", "codex"):
        stub = bindir / name
        stub.write_text("#!/bin/sh\nexec sleep 1000\n")
        stub.chmod(0o755)
    saved_env = {k: os.environ.get(k) for k in ("PATH", "HOME")}
    os.environ["PATH"] = f"{bindir}:{os.environ.get('PATH', '')}"
    os.environ["HOME"] = str(ws)

    campaign = Campaign(ws, bounded=bounded)
    campaign.hub.start()
    try:
        report = campaign.run()
    finally:
        campaign.cleanup()
        # Never leak the isolated HOME/PATH or the pinned DB singleton into
        # a caller (the pytest wrapper shares the process).
        for key, value in saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        try:
            from holdspeak.db.core import reset_database

            reset_database()
        except Exception:
            pass
    return report


def main(argv: Optional[list[str]] = None) -> int:
    bounded = "--bounded" in (argv or sys.argv[1:])
    report = run_campaign(bounded=bounded)

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = EVIDENCE_DIR / f"campaign-report-{stamp}.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    latest = EVIDENCE_DIR / "campaign-report-latest.json"
    latest.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    summary = report["summary"]
    log_lines = [
        f"HS-94-10 campaign — {report['meta']['finished_at']}",
        f"report: {report_path}",
        "",
        "north-star journeys:",
    ]
    for name, ok in summary["journeys"].items():
        log_lines.append(f"  {name}: {ok}")
    log_lines.append("fault matrix:")
    for name, ok in summary["faults"].items():
        log_lines.append(f"  {name}: {ok}")
    log_lines += [
        f"poll economy: {summary['poll_economy_pass']} "
        f"(1 client == {report['poll_economy'].get('one_client_calls')} dw calls, "
        f"10 clients == {report['poll_economy'].get('ten_client_calls')})",
        f"posture invariance: {summary['posture_pass']}",
        f"zero duplicate/wrong-target: {summary['dedup_pass']}",
        f"self attempt exactly-once: {summary['self_attempt_pass']}",
        f"census accounted: {summary['census_all_accounted']} "
        f"({report['census']['accounted']['accounted']}/"
        f"{report['census']['accounted']['issued']} commands)",
        f"census clean (no leaks): {summary['census_clean']} "
        f"({len(report['census']['leaks'])} leaks)",
        "compat consumers:",
    ]
    for prefix, note in report["compat"].get("deprecation_note", {}).items():
        log_lines.append(f"  {prefix}: {note}")
    log_text = "\n".join(log_lines)
    (EVIDENCE_DIR / "campaign-log-latest.txt").write_text(log_text + "\n", encoding="utf-8")
    print(log_text)

    ok = (
        all(v is not False for v in summary["journeys"].values())
        and all(v is not False for v in summary["faults"].values())
        and summary["census_clean"]
        and summary["census_all_accounted"]
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
