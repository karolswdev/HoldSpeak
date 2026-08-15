"""`holdspeak mesh serve` — the mesh-edge worker (HS-85-03, admitted in HS-131-16).

Turns THIS machine into a mesh edge: polls the hub's relay queue (HS-85-01),
executes each claimed run on this node's OWN provider (its engine, its profiles,
its keys — nothing transits the mesh), and posts the result back.

HS-131-16 closes the side door this loop used to be. It no longer builds an
engine or calls a provider at all. Instead:

1. It authenticates to the hub with its own paired NODE token — never the browser
   owner token — and sends a fresh nonce with every claim.
2. The hub answers with one Ed25519-signed dispatch offer. The worker verifies it
   against the public key it pinned at pairing, and against its own nonce,
   identity, payload, revisions, ordinal budget, and monotonic freshness. Nothing
   about a job is authority until that signature verifies.
3. It reserves the offer atomically in its own database, so a replay, a second
   worker, or a restart cannot execute it twice.
4. Its own kernel derives the principal and admits every physical attempt through
   the worker-local ``InferenceRunner``, which ends each one in an immutable
   receipt.
5. It reports a content-free, MACed terminal report naming those receipts. The
   hub revalidates everything independently; worker success cannot force hub
   acceptance.

Running the command IS the consent (the voice-macro posture: configuring is
consent; nothing serves unless started). The token rides an env var — never a
flag — so credentials stay out of shell history. Every claim poll stamps this
node's liveness on the hub; that polling is the mesh's only heartbeat.

Deliberately a reference implementation: synchronous, one job at a time.
"""
from __future__ import annotations

import json
import os
import random
import secrets
import signal
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Optional

from ..logging_config import get_logger
from ..mesh_authority import (
    MeshAuthorityRefused,
    build_report,
    canonical_job_payload,
    report_digest,
    report_mac,
    verify_offer,
)
from ..mesh_authority.offer import OPAQUE_ID_PATTERN
from ..mesh_authority.refusals import (
    ACK_INVALID,
    HUB_UNAVAILABLE,
    PUBLICATION_STOPPED,
    RESERVATION_LOST,
    WORKER_OWNER_LOCKED,
)

log = get_logger("mesh.serve")

DEFAULT_POLL_INTERVAL_SECONDS = 3.0
BACKOFF_BASE_SECONDS = 1.0
BACKOFF_MAX_SECONDS = 30.0
#: The node's OWN credential. The shared-owner `HOLDSPEAK_HUB_TOKEN` posture is
#: removed rather than kept as a fallback: a browser token cannot serve the mesh.
DEFAULT_TOKEN_ENV = "HOLDSPEAK_NODE_TOKEN"
#: How long the worker waits between re-sends of the SAME terminal bytes, and how
#: many transport attempts it makes. The signed monotonic window is the outer
#: bound; the count is what keeps a stalled clock from spinning forever.
REPORT_RETRY_SECONDS = 1.0
REPORT_RETRY_LIMIT = 5

#: The strict structured error body the hub's own edge returns (`web/routes/mesh`).
#: A 4xx that speaks it names the rule that refused; anything else is simply a
#: refused delivery, and neither one is retried (repair R2.8).
ERROR_BODY_FIELDS = ("error", "code")

#: The EXACT shape of a hub acknowledgement. Anything else — a field missing, a
#: field added, an acknowledgement for another report — does not end
#: retransmission (repair R9).
ACK_FIELDS = ("success", "duplicate", "job_id", "offer_id", "report_digest")


class MeshServeRefused(RuntimeError):
    """A fixed, named refusal. Carries no prompt, credential, or provider text."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _default_http_post(
    url: str, payload: dict[str, Any], *, token: str, timeout: float
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        # The NODE credential header. Deliberately not `X-HoldSpeak-Token`: the
        # edge derives an owner principal from that one, and a node is not an
        # owner.
        headers["X-HoldSpeak-Node-Token"] = token
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - the paired hub
        raw = resp.read().decode("utf-8")
    return json.loads(raw) if raw else {}


class MeshServeWorker:
    """The poll → verify → admit → report loop, factored for tests."""

    def __init__(
        self,
        *,
        hub_url: str,
        pin: Any,
        token: str = "",
        poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
        http_post: Optional[Callable[..., dict[str, Any]]] = None,
        engine_factory: Optional[Callable[..., Any]] = None,
        database: Any = None,
        local_runner: Any = None,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.hub_url = str(hub_url or "").rstrip("/")
        self.pin = pin
        self.node = str(getattr(pin, "node_name", "") or "")
        self.token = token
        self.poll_interval = max(0.5, float(poll_interval_seconds))
        self._http_post = http_post or _default_http_post
        self._sleep = sleep
        self._monotonic = monotonic
        self._timeout = timeout_seconds
        self._stop = False
        self._backoff = BACKOFF_BASE_SECONDS
        self._database = database
        self._nonce = ""
        self._claim_started = 0.0
        self._engine_factory = engine_factory
        # Re-entrant on purpose: `stop` arrives as a SIGNAL handler, on this same
        # thread, and may interrupt the very lazy construction it has to reach.
        self._election = threading.RLock()
        self._local_runner = local_runner
        #: Repair R2.3: the terminal-publication election. `stop` and the first
        #: `/complete` or `/fail` send race for this ONE flag under the same
        #: lock, so exactly one of them wins and the loser has no say.
        self._publishing = False

    # ── wiring ───────────────────────────────────────────────────────

    def _db(self) -> Any:
        if self._database is None:
            from ..db import get_database

            self._database = get_database()
        return self._database

    def _runner(self) -> Any:
        """The worker-local runner, built once, and STOPPED if stop already won.

        Repair R7: a stop that arrives before the runner exists used to be lost —
        there was nothing to cancel yet, and the runner built afterwards knew
        nothing about it. The election covers construction, so a runner born
        after a stop inherits it before `execute` can admit anything.
        """
        from ..kernel.mesh_local_runner import MeshLocalRunner

        with self._election:
            if self._local_runner is None:
                self._local_runner = MeshLocalRunner(
                    self._db(),
                    engine_factory=self._engine_factory,
                    monotonic=self._monotonic,
                )
            runner, stopped = self._local_runner, self._stop
        if stopped:
            runner.stop()
        return runner

    # ── the steps ────────────────────────────────────────────────────

    def stop(self, *_args: Any) -> None:
        """Stop serving, and cancel any physical attempt already in flight.

        Repair R2.3: stopping does NOT unsend a terminal report whose first
        publication already won the election. Once the hub has been told, the
        truth is out; retracting it would leave the two nodes disagreeing about
        work that physically happened.
        """
        with self._election:
            self._stop = True
            runner = self._local_runner
        if runner is not None:
            runner.stop()

    def _claim_publication(self) -> bool:
        """Elect publication against stop, once, under the one lock (repair R2.3).

        ``True`` means this delivery owns the wire from here on: a later stop
        cannot discard or unsend the fixed bytes, and bounded byte-identical
        retransmission continues. ``False`` means stop got here first, so the
        body is discarded and nothing is ever sent.
        """
        with self._election:
            if self._stop and not self._publishing:
                return False
            self._publishing = True
            return True

    @property
    def publishing(self) -> bool:
        """Has terminal publication won the election for the current job?"""
        with self._election:
            return self._publishing

    def _post(
        self, path: str, payload: dict[str, Any], *, timeout: Optional[float] = None
    ) -> dict[str, Any]:
        """One request, never given more time than the signed budget has left.

        Repair R8 / R2.4: the transport timeout is the remaining monotonic
        window, so a hub that accepts a connection and then goes quiet cannot
        stretch this worker past the authority it holds. There is no floor: a
        remainder under the old 50 ms minimum used to BUY 50 ms of unauthorized
        time, and an exhausted remainder must start no request at all.
        """
        if timeout is None:
            budget = self._timeout
        else:
            budget = min(self._timeout, float(timeout))
            if budget <= 0:
                raise MeshServeRefused(HUB_UNAVAILABLE)
        return self._http_post(
            f"{self.hub_url}{path}", payload, token=self.token, timeout=budget
        )

    def claim_once(self) -> Optional[tuple[dict[str, Any], Any]]:
        """One authenticated claim poll (this stamps the node's liveness hub-side).

        Returns the job and the VERIFIED offer, or ``None``. A hub answer whose
        offer does not verify is not work — it refuses by name here, before any
        reservation, revision, runner, engine, or provider exists.
        """
        self._nonce = secrets.token_urlsafe(18)
        self._claim_started = self._monotonic()
        data = self._post("/api/mesh/relay/claim", {"claim_nonce": self._nonce})
        job = data.get("job")
        if not isinstance(job, dict):
            return None
        offer = verify_offer(
            data.get("dispatch_offer"),
            pinned_key_id=self.pin.key_id,
            pinned_public_key=self.pin.public_key_bytes,
            node_name=self.pin.node_name,
            node_id=self.pin.node_id,
            credential_generation=self.pin.generation,
            claim_nonce=self._nonce,
            job=job,
            # Repair R2.1: the hub's independently derived live-authority
            # projection. Its hash is inside the signature, and every semantic
            # field of it is compared here — before the reservation, before the
            # revision, before the runner, and before any provider.
            authority_expectation=data.get("authority_expectation"),
            claim_started_monotonic=self._claim_started,
            monotonic=self._monotonic(),
        )
        return job, offer

    def execute(self, job: dict[str, Any], offer: Any) -> bool:
        """Admit, run, receipt, and report ONE verified offer."""
        from ..kernel.mesh_local_authority import (
            derive_local_authority,
            reserve_local_execution,
        )

        database = self._db()
        # Repair R2.3: a NEW job publishes nothing yet. The flag belongs to one
        # terminal report, so it is reset here rather than carried across jobs.
        with self._election:
            self._publishing = False
        # The reservation is the election, and it happens BEFORE the execution
        # revision is persisted or any runner is built. A duplicate refuses here
        # having reached no provider.
        reservation = reserve_local_execution(database, offer)
        authority = derive_local_authority(offer, reservation)
        payload = canonical_job_payload(job)
        started = self._monotonic()
        try:
            outcome = self._runner().execute(authority, payload)
        except MeshAuthorityRefused:
            # Ruling 8 / repair R2.2: EVERY terminal path closes the reservation
            # with a compare-and-set, and every failed CAS is lost ledger
            # authority. A local refusal is no exception — a process that cannot
            # account for its own reservation must stop serving, not carry on.
            if not self._close_reservation(database, offer, "refused"):
                raise MeshServeRefused(RESERVATION_LOST) from None
            raise
        log.info(
            "job %s %s on node %s in %.1fs across %d admitted attempt(s)",
            offer.job_id, outcome.terminal_outcome.upper(), self.node,
            self._monotonic() - started, len(outcome.attempts),
        )

        # Ruling 8: losing the reservation means this process no longer owns the
        # ledger row. It may not classify the cohort as recorded, and it stops
        # serving rather than continuing to claim work it cannot account for.
        if not self._close_reservation(database, offer, outcome.terminal_outcome):
            raise MeshServeRefused(RESERVATION_LOST)

        report = build_report(
            offer=offer,
            local_attempts=outcome.attempts,
            terminal_outcome=outcome.terminal_outcome,
            result=outcome.result,
            failure_class=outcome.failure_class,
        )
        return self._deliver(offer, report, outcome)

    def _close_reservation(self, database: Any, offer: Any, terminal_outcome: str) -> bool:
        """Close this cohort's reservation, and HALT serving if the CAS failed.

        Repair R2.2 / ruling 8. Setting the stop flag here is what makes "lost
        ledger authority" mean something: the loop does not claim again.
        """
        owned = database.mesh_worker.settle(
            hub_key_id=offer.key_id,
            hub_operation_id=offer.hub_operation_id,
            first_ordinal=offer.first_ordinal,
            terminal_outcome=str(terminal_outcome),
        )
        if not owned:
            with self._election:
                self._stop = True
            log.error(
                "job %s: this worker no longer owns its reservation (%s); "
                "it stops serving rather than claiming work it cannot account for",
                offer.job_id, RESERVATION_LOST,
            )
        return bool(owned)

    def _acknowledged(self, ack: Any, offer: Any, digest: str) -> bool:
        """Is this the hub's acknowledgement of THIS report? (repair R9)

        A 2xx body ends retransmission only when it has the exact expected field
        set AND names this job, this offer, and the digest of the exact terminal
        bytes that were sent. An acknowledgement for another report, a truncated
        one, or one carrying unknown fields is not an answer to this delivery.
        """
        if not isinstance(ack, dict) or set(ack) != set(ACK_FIELDS):
            return False
        if ack["success"] is not True or not isinstance(ack["duplicate"], bool):
            return False
        return (
            str(ack["job_id"]) == str(offer.job_id)
            and str(ack["offer_id"]) == str(offer.offer_id)
            and str(ack["report_digest"]) == digest
        )

    @staticmethod
    def _refusal_code(exc: urllib.error.HTTPError) -> str:
        """The hub's own fixed refusal class, named ONCE (repair R2.8).

        The edge answers a refusal with a strict ``{"error", "code"}`` body. Only
        that exact shape yields a class; anything else is simply a refused
        delivery. The raw body never travels further than this function, so a
        hub that echoed content cannot leak it into a log line.
        """
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except Exception:
            return ""
        if not isinstance(body, dict) or set(body) != set(ERROR_BODY_FIELDS):
            return ""
        code = body.get("code")
        return code if isinstance(code, str) and OPAQUE_ID_PATTERN.fullmatch(code) else ""

    def _deliver(self, offer: Any, report: dict[str, Any], outcome: Any) -> bool:
        """Send the FIXED terminal bytes, and keep sending exactly those.

        Repair R2.3 opens with the election. If stop won before the first send
        begins, the body is discarded and NOTHING is sent. If this delivery wins,
        a later stop cannot unsend it: byte-identical retransmission continues
        inside the signed monotonic settlement window and never repeats the model.

        Repair R2.8 separates three answers a POST can bring back. A structured
        4xx is the hub's DECISION — named once, never retried. A 2xx that is not
        the acknowledgement of THESE bytes is a terminal protocol refusal. A 5xx
        means the hub did not acknowledge, so the SAME immutable report may go
        out again inside the signed count and window, and exhaustion is the fixed
        class ``mesh_hub_unavailable`` — never a hub decision misnamed as loss.
        """
        succeeded = outcome.terminal_outcome == "succeeded"
        if not self._claim_publication():
            log.warning(
                "job %s: stop won before this report was published (%s); "
                "nothing was sent", offer.job_id, PUBLICATION_STOPPED,
            )
            return False
        path = f"/api/mesh/relay/{offer.job_id}/" + ("complete" if succeeded else "fail")
        body = {
            "report": report,
            "mac": report_mac(report, self.token),
            "result": outcome.result if succeeded else "",
        }
        digest = report_digest(report)
        attempts = 0
        while True:
            remaining = offer.remaining_seconds(monotonic=self._monotonic())
            if remaining <= 0:
                break
            attempts += 1
            try:
                ack = self._post(path, body, timeout=remaining)
            except urllib.error.HTTPError as exc:
                # FIRST, because it is a `URLError` subclass: a structured status
                # is an answer that arrived, not a packet that was lost.
                status = int(exc.code)
                if 400 <= status < 500:
                    log.warning(
                        "job %s: the hub refused the terminal report (HTTP %s, %s)",
                        offer.job_id, status, self._refusal_code(exc) or "unnamed",
                    )
                    return False
                # 5xx: the hub did NOT acknowledge. The same bytes may go out
                # again — no model runs again, and the hub treats an exact
                # duplicate as read-only idempotency.
                log.warning("hub did not acknowledge %s: HTTP %s", offer.job_id, status)
            except MeshServeRefused:
                # The remainder was already exhausted before the request began.
                break
            except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError):
                # TRANSPORT only. The exception's own text is never logged: a raw
                # message is exactly where a prompt or a credential leaks out.
                log.warning("could not reach the hub for %s", offer.job_id)
            except Exception as exc:
                # A NAMED refusal is the hub's answer, not a lost packet.
                # Resending it would spin against a decision that will not change.
                log.warning(
                    "the hub refused the terminal report for %s: %s",
                    offer.job_id, getattr(exc, "code", None) or type(exc).__name__,
                )
                return False
            else:
                if self._acknowledged(ack, offer, digest):
                    return succeeded
                # A 2xx that acknowledges something else — or nothing this
                # protocol defines — is terminal, not transport loss.
                log.warning(
                    "job %s: the hub's answer does not acknowledge this report (%s)",
                    offer.job_id, ACK_INVALID,
                )
                return False
            if attempts >= REPORT_RETRY_LIMIT:
                break
            # Repair R2.4: a sleep may never overshoot the remaining window.
            pause = min(
                REPORT_RETRY_SECONDS,
                offer.remaining_seconds(monotonic=self._monotonic()),
            )
            if pause <= 0:
                break
            self._sleep(pause)
        log.warning(
            "job %s: the hub never acknowledged this report (%s)",
            offer.job_id, HUB_UNAVAILABLE,
        )
        return False

    def poll_step(self) -> bool:
        """One loop tick: claim; execute when work arrived. True = did work."""
        try:
            claimed = self.claim_once()
        except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError) as exc:
            log.warning("hub unreachable (%s); retrying in %.0fs", exc, self._backoff)
            self._sleep(self._backoff)
            self._backoff = min(BACKOFF_MAX_SECONDS, self._backoff * 2)
            return False
        self._backoff = BACKOFF_BASE_SECONDS
        if claimed is None:
            return False
        job, offer = claimed
        log.info("job %s CLAIMED for node %s", offer.job_id, self.node)
        try:
            self.execute(job, offer)
        except (MeshAuthorityRefused, MeshServeRefused) as exc:
            log.warning("job %s refused: %s", offer.job_id, exc.reason)
        return True

    # ── the modes ────────────────────────────────────────────────────

    def run_once(self) -> int:
        """Claim at most one job, run it, exit — as the ONE live owner.

        Repair R2.2: ``--once`` is an ordinary production serve mode, not a test
        seam. It reserves, executes, and settles against the same worker ledger
        ``run_forever`` does, so two ordinary CLI processes over one worker HOME
        must not be able to touch that ledger at the same time. The lock is the
        same OS lock, taken before any claim or reservation and released by the
        OS on exit of any kind.
        """
        try:
            with self._db().mesh_worker.owner_lock():
                return self._serve_once()
        except MeshAuthorityRefused as exc:
            if exc.reason != WORKER_OWNER_LOCKED:  # pragma: no cover - defensive
                raise
            log.error(
                "another live worker already owns this node's database (%s); "
                "not touching its reservations",
                exc.reason,
            )
            return 1

    def _serve_once(self) -> int:
        try:
            claimed = self.claim_once()
        except MeshAuthorityRefused as exc:
            log.error("the hub's dispatch offer was refused: %s", exc.reason)
            return 1
        except Exception as exc:
            log.error("hub unreachable: %s", exc)
            return 1
        if claimed is None:
            log.info("no relay work queued for node %s", self.node)
            return 0
        job, offer = claimed
        log.info("job %s CLAIMED for node %s", offer.job_id, self.node)
        try:
            return 0 if self.execute(job, offer) else 1
        except (MeshAuthorityRefused, MeshServeRefused) as exc:
            log.error("job %s refused: %s", offer.job_id, exc.reason)
            return 1

    def run_forever(self) -> int:
        """Serve this node, as the ONE live owner of its worker database.

        Repair R7: startup reconciliation rewrites every reservation left open,
        so it may only run when nothing else is serving from this database — a
        second `mesh serve` would otherwise declare a running worker's in-flight
        attempt indeterminate. The owner lock is taken FIRST, before startup
        reconciliation, any claim, and any reservation; it is held for the
        serving lifetime and released by the OS on exit of any kind.
        """
        try:
            with self._db().mesh_worker.owner_lock():
                return self._serve()
        except MeshAuthorityRefused as exc:
            if exc.reason != WORKER_OWNER_LOCKED:  # pragma: no cover - defensive
                raise
            log.error(
                "another live worker already owns this node's database (%s); "
                "not touching its reservations",
                exc.reason,
            )
            return 1

    def _serve(self) -> int:
        log.info(
            "serving the mesh as node %s (hub %s, poll %.1fs) — Ctrl-C to stop",
            self.node, self.hub_url, self.poll_interval,
        )
        # Reservations left open by a previous life reconcile to `indeterminate`.
        # They are never rerun: at-most-once execution and an honest hub timeout
        # beat an invisible second call to the model.
        abandoned = self._db().mesh_worker.reconcile_abandoned()
        if abandoned:
            log.warning(
                "%d mesh reservation(s) from a previous run reconciled indeterminate",
                abandoned,
            )
        while not self._stop:
            did_work = self.poll_step()
            if self._stop:
                break
            if not did_work:
                # jittered idle wait; a working loop re-polls immediately
                self._sleep(self.poll_interval * random.uniform(0.8, 1.2))
        log.info("node %s stopped serving the mesh", self.node)
        return 0


def run_mesh_serve_command(args: Any) -> int:
    """Serve the mesh with THIS node's imported pairing.

    Both halves of the credential come from the deliberate pairing transfer
    (`holdspeak node token export` on the hub, `holdspeak node pair` here): the
    pinned hub offer public key, and the node's own bearer token in owner-only
    custody. The environment variable still wins when it is set, so an operator
    can keep the token out of any file — but the shared-owner
    `HOLDSPEAK_HUB_TOKEN` posture is gone, not demoted to a fallback.
    """
    from ..delivery.node_credentials import NodeCustodyError, load_hub_pin

    hub_url = str(getattr(args, "hub", "") or "http://127.0.0.1:8765")
    token_env = str(getattr(args, "token_env", "") or DEFAULT_TOKEN_ENV)
    try:
        pin = load_hub_pin()
    except NodeCustodyError as exc:
        log.error("this node's hub pin is unusable: %s", exc.reason)
        return 1
    if pin is None:
        log.error(
            "this machine has not imported a pairing; run "
            "`holdspeak node token export --name <node>` on the hub and "
            "`holdspeak node pair --from <file>` here before serving"
        )
        return 1
    token = os.environ.get(token_env, "").strip() or pin.node_token
    if not token:
        log.error(
            "no node credential: set %s to this node's pairing token, or import "
            "a pairing that carries it (`holdspeak node pair --from <file>`)",
            token_env,
        )
        return 1

    worker = MeshServeWorker(hub_url=hub_url, pin=pin, token=token)
    if getattr(args, "once", False):
        return worker.run_once()

    signal.signal(signal.SIGINT, worker.stop)
    signal.signal(signal.SIGTERM, worker.stop)
    return worker.run_forever()
