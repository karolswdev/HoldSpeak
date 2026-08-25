"""HS-131-16 — the mesh protocol across two REAL processes on loopback.

Everything else in this story is proved in-process, where it is easy to hold both
sides of the protocol in one hand. That is exactly why this test exists: the
receiver's whole problem was that a process boundary looked like an exemption, so
at least one proof has to actually cross one.

A real hub process serves HTTP over loopback with its own SQLite database and its
own kernel. A real worker process, with a DIFFERENT database and its own kernel,
pairs against it, verifies the signed dispatch offer, admits the physical attempt
locally against an injected fake engine, and reports. Afterwards both databases
are inspected from the test: two separate kernels, two separate receipts, one
independent hub settlement.

No LAN and no model: HS-131-12 owns the assembled `.43` walk. What this pins is
the process boundary itself.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

TIMEOUT_SECONDS = 180

HUB_SCRIPT = '''
import json, sys, threading, time
from pathlib import Path

base, port = Path(sys.argv[1]), int(sys.argv[2])

from holdspeak.db import get_database
db = get_database(base / "hub.db")

from holdspeak.commands.node_serve import main as node_main
from holdspeak.delivery.node_link import NodeTokenStore

# The PRODUCT pairing path, run as the operator runs it, in this process's own
# HOME: create the pairing, then export it as one owner-only transfer document.
# Nothing here hand-builds a pin (repair R2).
assert node_main(["token", "create", "--name", "edge"]) == 0
assert node_main(
    ["token", "export", "--name", "edge", "--out", str(base / "pairing.json")]
) == 0

# The DEFAULT custody path, exactly as production uses it: the relay engine
# resolves a destination binding through the same default store the edge
# authenticates against.
store = NodeTokenStore()
node_id = store.pairing("edge").node_id

exported = (base / "pairing.json").read_text()
signing = store.signing_snapshot("edge")
assert signing.offer_private_key and signing.offer_private_key not in exported, (
    "the hub's offer private key must never leave this machine"
)
assert store.bearer_token("edge") in exported, "the transfer must carry the token"

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind, UNAUTHENTICATED
from holdspeak.services.mesh_service import MeshService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.mesh import build_mesh_router

broker = _configure(db)
app = FastAPI()

@app.middleware("http")
async def auth(request: Request, call_next):
    """The production edge derivation, reduced to the node leg."""
    snapshot = store.identify(request.headers.get("x-holdspeak-node-token"))
    request.state.principal = (
        Principal(PrincipalKind.NODE, snapshot.node_id) if snapshot else UNAUTHENTICATED
    )
    request.state.node_credential = snapshot
    return await call_next(request)

app.include_router(build_mesh_router(WebContext(
    get_state=lambda: {},
    mesh_service=MeshService(db, kernel=broker, token_store=store),
)))

import uvicorn
server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
threading.Thread(target=server.run, daemon=True).start()
while not server.started:
    time.sleep(0.05)
(base / "hub_ready").write_text("ready")

# The hub's OWN admitted attempt: a mesh destination, resolved and frozen, then
# dispatched through the one admission path. Its engine is the relay.
db.profiles.upsert(
    profile_id="edge-profile", name="Edge", kind="meshNode", node="edge",
    base_url="http://127.0.0.1:8/v1", model="fake-model",
)
from holdspeak.deployment_revisions import capture_deployment_revision
from holdspeak.inference_targets import resolve_inference_target
from holdspeak.kernel.inference_runner import InvocationRequest, ServiceContract
from holdspeak.kernel.prompt_adapter import CanonicalPromptAdapter
from holdspeak.kernel.runtime import _as_principal

# Liveness is asked for by EXACT identity and generation, the same way the
# production relay engine asks before it enqueues anything (repair R8).
pairing = store.pairing("edge")
deadline = time.time() + 120
while time.time() < deadline and not db.mesh_relay.node_live(
    pairing.node_id, pairing.generation, 15
):
    time.sleep(0.1)
assert db.mesh_relay.node_live(pairing.node_id, pairing.generation, 15)
assert not db.mesh_relay.node_live(pairing.node_id, pairing.generation + 1, 15)

target = resolve_inference_target(db, "edge-profile")
revision = capture_deployment_revision(db, target)
payload = {"system_prompt": "", "user_prompt": "TWO-PROCESS-PROMPT",
           "temperature": None, "max_tokens": None}
captured = {}

def publish(result):
    captured["output"] = str(dict(result).get("output") or "")
    return "mesh-result:hub-two-process"

request = InvocationRequest(
    revision.id,
    ServiceContract.for_payload("holdspeak.two-process", "1", payload),
    time.time() + 120, payload, "hub_two_process_1",
)
owner = Principal(PrincipalKind.OWNER, "owner-session")
with _as_principal(owner):
    outcome = broker.inference_runner.invoke(request, CanonicalPromptAdapter(), publish=publish)

receipt = broker.store.receipt(outcome.operation_id) or {}
(base / "hub_result.json").write_text(json.dumps({
    "outcome": outcome.outcome,
    "result_ref": outcome.result_ref,
    "captured": captured.get("output", ""),
    "hub_operation_id": outcome.operation_id,
    "hub_receipt_id": receipt.get("receipt_id", ""),
    "hub_receipt_outcome": receipt.get("outcome", ""),
    "relay_revision_id": revision.id,
    "node_id": node_id,
    "home": str(Path.home()),
    "token_store": str(Path.home() / ".holdspeak" / "node_auth_tokens.json"),
}))
server.should_exit = True
'''

WORKER_SCRIPT = '''
import json, sys, time
from pathlib import Path

base, port = Path(sys.argv[1]), int(sys.argv[2])

from holdspeak.db import get_database
db = get_database(base / "worker.db")

from holdspeak.commands.mesh_serve import MeshServeWorker
from holdspeak.commands.node_serve import main as node_main
from holdspeak.delivery.node_credentials import load_hub_pin
from holdspeak.delivery.node_link import NodeTokenStore

# The PRODUCT import, in THIS machine's own HOME, followed by the PRODUCT
# loader. The pin and the bearer token both come out of local custody; nothing
# in this file constructs either (repair R2).
assert node_main(["pair", "--from", str(base / "pairing.json")]) == 0
pin = load_hub_pin()
assert pin is not None and pin.node_token, "the import left no usable pairing"

# This machine is a WORKER: it holds no hub pairing custody of its own, so it
# could not sign an offer even if it wanted to.
assert NodeTokenStore().status_rows() == []


class FakeEngine:
    """The injected provider. It is the ONLY thing that is not real here."""

    active_provider = "fake"
    model = "fake-model"

    def __init__(self):
        self.calls = 0

    def run_prompt(self, *, system_prompt="", user_prompt="", temperature=None, max_tokens=None):
        self.calls += 1
        Path(base / "engine_calls.txt").write_text(str(self.calls))
        return "TWO-PROCESS-ANSWER"


engine = FakeEngine()
worker = MeshServeWorker(
    hub_url=f"http://127.0.0.1:{port}",
    pin=pin,
    token=pin.node_token,
    database=db,
    engine_factory=lambda revision, **kw: engine,
    sleep=time.sleep,
)

deadline = time.time() + 150
did_work = False
while time.time() < deadline and not did_work:
    did_work = worker.poll_step()
    if not did_work:
        time.sleep(0.2)

rows = []
with db._connection() as conn:
    for row in conn.execute(
        "SELECT operation_id, native_id, principal_identity, target_ref, state"
        " FROM kernel_operations ORDER BY created_at"
    ):
        rows.append(dict(row))
    receipts = [dict(r) for r in conn.execute(
        "SELECT receipt_id, operation_id, outcome FROM kernel_receipts"
    )]
    reservations = [dict(r) for r in conn.execute(
        "SELECT hub_key_id, hub_operation_id, first_ordinal, state FROM mesh_worker_reservations"
    )]
    revisions = [dict(r) for r in conn.execute(
        "SELECT id, kind, engine, endpoint FROM deployment_revisions"
    )]

(base / "worker_result.json").write_text(json.dumps({
    "did_work": did_work,
    "engine_calls": engine.calls,
    "operations": rows,
    "receipts": receipts,
    "reservations": reservations,
    "revisions": revisions,
    "home": str(Path.home()),
    "pinned_node_id": pin.node_id,
    "pinned_generation": pin.generation,
    "pin_document": str(Path.home() / ".holdspeak" / "mesh_hub_pin.json"),
}))
'''


#: Two ORDINARY `holdspeak mesh serve` processes over one worker HOME and one
#: worker database (repair R2.2). The first holds the database open with the
#: owner lock and waits; the second runs the same command and must refuse before
#: it touches a reservation. Neither is a test seam — both go through
#: `run_mesh_serve_command`, the function the CLI dispatches to.
OWNER_SCRIPT = '''
import json, sys, time
from pathlib import Path
from types import SimpleNamespace

base, mode = Path(sys.argv[1]), sys.argv[2]

from holdspeak.db import get_database
db = get_database(base / "worker.db")

from holdspeak.commands.node_serve import main as node_main
from holdspeak.commands import mesh_serve
from holdspeak.commands.mesh_serve import run_mesh_serve_command

assert node_main(["pair", "--from", str(base / "pairing.json")]) == 0

# A reservation this "previous life" left open. A second owner must not touch
# it, and must not reconcile it while the first owner is still alive.
if mode == "first":
    db.mesh_worker.reserve(
        hub_key_id="k", hub_operation_id="op_in_flight", first_ordinal=1
    )

args = SimpleNamespace(hub="http://127.0.0.1:1", token_env="HOLDSPEAK_NODE_TOKEN", once=True)

if mode == "first":
    # Hold the database the way a live serving process does, then say so.
    with db.mesh_worker.owner_lock():
        (base / "owner_holding").write_text("held")
        while not (base / "second_done").exists():
            time.sleep(0.05)
    (base / "owner_released").write_text("released")
else:
    code = run_mesh_serve_command(args)
    row = db.mesh_worker.get(
        hub_key_id="k", hub_operation_id="op_in_flight", first_ordinal=1
    )
    (base / "second_result.json").write_text(json.dumps({
        "code": code,
        "reservation_state": (row or {}).get("state"),
        "home": str(Path.home()),
    }))
    (base / "second_done").write_text("done")
'''


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _wait_for(path: Path, deadline: float, producer: subprocess.Popen) -> None:
    """Wait for the file PRODUCER writes, and fail fast if producer dies first.

    Only the producing process is monitored: the worker legitimately finishes
    and exits before the hub records its own result, so treating any exit as
    fatal would make this test race itself.
    """
    while time.time() < deadline:
        if path.exists():
            return
        if producer.poll() is not None:
            out, err = producer.communicate()
            raise AssertionError(
                f"{path.name} never appeared; its process exited "
                f"{producer.returncode}\nSTDOUT:\n{out}\nSTDERR:\n{err}"
            )
        time.sleep(0.1)
    raise AssertionError(f"timed out waiting for {path.name}")


@pytest.mark.timeout(TIMEOUT_SECONDS)
def test_two_ordinary_serve_processes_cannot_share_one_worker_ledger(tmp_path) -> None:
    """Repair R2.2: `mesh serve --once` is a production mode, under the lock.

    Two ORDINARY CLI processes, one worker HOME, one worker database. The first
    holds the database the way a live serving process does; the second runs
    `holdspeak mesh serve --once` and must refuse before it claims, reserves, or
    reconciles anything. Before this repair the lock covered only `run_forever`,
    so `--once` walked straight past a live owner into its reservations — and
    startup reconciliation would have declared the running worker's in-flight
    attempt indeterminate.
    """
    from holdspeak.delivery.node_credentials import write_pairing_transfer
    from holdspeak.delivery.node_link import NodeTokenStore

    base = tmp_path / "owner"
    base.mkdir()
    repo = Path(__file__).resolve().parents[2]

    # One pairing, exported the product way, imported by BOTH processes — they
    # are the same machine, serving the same node, which is the whole point.
    hub_store = NodeTokenStore(base / "hub_nodes.json")
    _node_id, token, snapshot = hub_store.pair("edge")
    write_pairing_transfer(base / "pairing.json", snapshot, token)

    home = base / "worker_home"
    home.mkdir()
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["PYTHONPATH"] = str(repo)
    env.pop("HOLDSPEAK_HUB_TOKEN", None)
    env.pop("HOLDSPEAK_NODE_TOKEN", None)
    (base / "owner_main.py").write_text(OWNER_SCRIPT)

    first = subprocess.Popen(
        [sys.executable, str(base / "owner_main.py"), str(base), "first"],
        cwd=str(repo), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    second = None
    try:
        deadline = time.time() + TIMEOUT_SECONDS - 30
        _wait_for(base / "owner_holding", deadline, first)

        second = subprocess.Popen(
            [sys.executable, str(base / "owner_main.py"), str(base), "second"],
            cwd=str(repo), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        _wait_for(base / "second_result.json", deadline, second)
        _wait_for(base / "owner_released", deadline, first)
    finally:
        for proc in (first, second):
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=20)
                except subprocess.TimeoutExpired:  # pragma: no cover - cleanup
                    proc.kill()

    result = json.loads((base / "second_result.json").read_text())
    assert result["code"] == 1, "the second ordinary serve must refuse"
    assert result["home"] == str(home), "both processes shared one worker HOME"
    # The live owner's in-flight reservation is EXACTLY as it was: the refusing
    # process reconciled nothing.
    assert result["reservation_state"] == "reserved"


@pytest.mark.timeout(TIMEOUT_SECONDS + 60)
def test_two_real_processes_keep_two_separate_kernels(tmp_path) -> None:
    base = tmp_path / "mesh"
    base.mkdir()
    port = _free_port()
    repo = Path(__file__).resolve().parents[2]

    # SEPARATE homes, one per machine (repair R2). The hub's pairing custody and
    # the worker's imported pin are different files on different "machines", and
    # neither process may touch the owner's real database or custody. Both open
    # their databases by EXPLICIT path anyway.
    hub_home = base / "hub_home"
    worker_home = base / "worker_home"
    hub_home.mkdir()
    worker_home.mkdir()

    def environment(home: Path) -> dict:
        env = dict(os.environ)
        env["HOME"] = str(home)
        env["PYTHONPATH"] = str(repo)
        env.pop("HOLDSPEAK_HUB_TOKEN", None)
        env.pop("HOLDSPEAK_NODE_TOKEN", None)
        return env

    (base / "hub_main.py").write_text(HUB_SCRIPT)
    (base / "worker_main.py").write_text(WORKER_SCRIPT)

    hub = subprocess.Popen(
        [sys.executable, str(base / "hub_main.py"), str(base), str(port)],
        cwd=str(repo), env=environment(hub_home),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    worker = None
    try:
        deadline = time.time() + TIMEOUT_SECONDS
        _wait_for(base / "hub_ready", deadline, hub)
        _wait_for(base / "pairing.json", deadline, hub)

        worker = subprocess.Popen(
            [sys.executable, str(base / "worker_main.py"), str(base), str(port)],
            cwd=str(repo), env=environment(worker_home),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        _wait_for(base / "hub_result.json", deadline, hub)
        _wait_for(base / "worker_result.json", deadline, worker)
    finally:
        for proc in (hub, worker):
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=20)
                except subprocess.TimeoutExpired:  # pragma: no cover - cleanup
                    proc.kill()

    hub_result = json.loads((base / "hub_result.json").read_text())
    worker_result = json.loads((base / "worker_result.json").read_text())

    # ── the hub's own admitted attempt succeeded, through the relay ──
    assert hub_result["outcome"] == "succeeded"
    assert hub_result["captured"] == "TWO-PROCESS-ANSWER"
    assert hub_result["hub_receipt_outcome"] == "succeeded"

    # ── the worker did its own physical work, exactly once ──
    assert worker_result["did_work"] is True
    assert worker_result["engine_calls"] == 1

    # ── two SEPARATE kernels: the worker's ledger is its own ──
    invokes = [
        row for row in worker_result["operations"]
        if row["native_id"].startswith("mesh_")
    ]
    assert len(invokes) == 1, worker_result["operations"]
    local = invokes[0]
    assert local["operation_id"] != hub_result["hub_operation_id"]
    assert local["principal_identity"].startswith("mesh-receiver:")
    # Terminal on the worker's own ledger: the local attempt closed there,
    # not because the hub said so.
    assert local["state"] == "succeeded"

    receipts = {r["operation_id"]: r for r in worker_result["receipts"]}
    assert receipts[local["operation_id"]]["outcome"] == "succeeded"
    assert hub_result["hub_receipt_id"] not in receipts

    # ── the worker ran its DERIVED revision, not the hub's relay revision ──
    kinds = {r["id"]: r for r in worker_result["revisions"]}
    assert hub_result["relay_revision_id"] not in kinds
    # Startup can lawfully create its own local speech deployment first. Assert
    # the actual operation target, rather than assuming the first non-mesh row
    # is the derived revision used for this offer.
    executed_id = str(local["target_ref"]).removeprefix("deployment-revision:")
    assert executed_id in kinds
    assert kinds[executed_id]["kind"] != "mesh_node"

    # ── the reservation is spent, and settled ──
    assert len(worker_result["reservations"]) == 1
    reservation = worker_result["reservations"][0]
    assert reservation["hub_operation_id"] == hub_result["hub_operation_id"]
    assert reservation["state"] == "settled"

    # ── the two databases are genuinely different files ──
    assert (base / "hub.db").exists() and (base / "worker.db").exists()
    assert (base / "hub.db").read_bytes() != (base / "worker.db").read_bytes()

    # ── and so are the two machines' custodies (repair R2) ──
    assert hub_result["home"] == str(hub_home) != worker_result["home"]
    assert worker_result["home"] == str(worker_home)
    # The hub holds pairing custody; the worker holds only what was transferred.
    assert Path(hub_result["token_store"]).exists()
    assert not (worker_home / ".holdspeak" / "node_auth_tokens.json").exists()
    assert Path(worker_result["pin_document"]).exists()
    assert worker_result["pinned_node_id"] == hub_result["node_id"]
    assert worker_result["pinned_generation"] == 1

    # The transfer that made this work carries the token and the PUBLIC key, and
    # is owner-only. The hub's private signing key stayed on the hub — the hub
    # process asserted that against its own live key before serving.
    transfer = json.loads((base / "pairing.json").read_text())
    assert set(transfer) == {
        "mesh_pairing_transfer_schema", "node_name", "node_id", "generation",
        "key_id", "offer_public_key", "node_token",
    }
    assert (base / "pairing.json").stat().st_mode & 0o077 == 0
    hub_store = json.loads((hub_home / ".holdspeak" / "node_auth_tokens.json").read_text())
    private_key = hub_store["nodes"]["edge"]["offer_private_key"]
    assert private_key and private_key not in (base / "pairing.json").read_text()
