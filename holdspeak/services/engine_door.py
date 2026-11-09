"""The engine door: one way to run one AI job on the engine its assignment names.

A caller names the job (a capability id such as ``chat.compact``) and gives the
payload. The door finds the engine the owner assigned to that job, runs the job
on it through the kernel runner (which writes the one receipt, a kernel
operation), and gives back the answer. A job that does not complete raises one
typed error, :class:`EngineDoorError`.

Before the door, each caller built its own ``InvocationRequest``, its own
publish capture and its own outcome check (eight copies).
"""
from __future__ import annotations

import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from typing import Any, Optional

DEFAULT_DEADLINE_SECONDS = 120.0


class EngineDoorError(RuntimeError):
    """A job did not complete. ``code`` is ``no_engine`` (no engine is
    assigned to the job) or ``failed`` (the engine ran and gave no answer).
    ``operation_id`` names the runner's receipt when the job reached it;
    ``error`` is the engine's own words."""

    def __init__(
        self, code: str, detail: str, *, operation_id: str = "", outcome: str = "",
        send_phase: str = "", error: str = "",
    ) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.operation_id = operation_id
        self.outcome = outcome
        self.send_phase = send_phase
        self.error = error
        #: ``(revision, send_phase, operation_id, outcome)`` of each attempt (``route``).
        self.sent: tuple[tuple[str, str, str, str], ...] = ()


@dataclass(frozen=True)
class Engine:
    """The engine a job runs on: the deployment revision, the assignment that
    named it and the profile it resolved through."""

    revision: str
    assignment: str = ""
    profile: str = ""
    #: The next engine in the assignment's chain: one retry when this one fails.
    fallback: Optional["Engine"] = field(default=None, compare=False)


@dataclass(frozen=True)
class Answer:
    """The engine's answer. ``result`` is what the adapter gave (a dict with
    ``output`` and ``model`` for a prompt); ``output`` and ``model`` are read
    from it."""

    result: Any
    operation_id: str
    engine: Engine
    outcome: str = "succeeded"
    send_phase: str = ""
    published: Any = None
    invocation_id: str = ""
    #: ``(revision, send_phase, operation_id, outcome)`` of each attempt (``route``).
    sent: tuple[tuple[str, str, str, str], ...] = ()

    @property
    def output(self) -> str:
        if isinstance(self.result, dict):
            return str(self.result.get("output") or "")
        return str(self.result or "")

    @property
    def model(self) -> str:
        return str(self.result.get("model") or "") if isinstance(self.result, dict) else ""


def engine_for(broker: Any, job: str, *, subject: Optional[tuple[str, str]] = None) -> Engine:
    """The engine assigned to ``job``. Raises ``EngineDoorError('no_engine')``.

    ``subject`` (``(kind, id)``, for one ``("workbench", <id>)``): the
    assignment made for that subject (an automation's With line), resolved
    by the same route planner; with none of its own, the job's. The kind
    ``invocation`` names a one-run assignment ("Use X for this one")."""
    from .project_update_service import _resolve_for_capability, _route_plan_deployment

    if subject is not None:
        one_run = subject[0] == "invocation"
        revision, assignment, profile = _route_plan_deployment(
            broker, job, subject_kind=None if one_run else subject[0],
            subject_id=None if one_run else subject[1], invocation_id=subject[1] if one_run else None)
        if revision:
            engine = Engine(str(revision), str(assignment or ""), str(profile or ""))
            return replace(engine, fallback=_next_in_chain(broker, job, engine))

    try:
        revision, assignment, profile = _resolve_for_capability(broker, job)
    except RuntimeError as exc:
        raise EngineDoorError("no_engine", str(exc)) from exc
    if not revision:
        raise EngineDoorError("no_engine", f"No engine is assigned to {job}")
    engine = Engine(str(revision), str(assignment or ""), str(profile or ""))
    return replace(engine, fallback=_next_in_chain(broker, job, engine))


def engine_of_profile(broker: Any, profile_id: str) -> Optional[Engine]:
    """The engine one model profile names: the owner's pick for one run
    ("Use X for this one"), with no next engine. ``None`` when the profile
    names no deployment."""
    from .project_update_service import _bound_deployment_revision, _captured_deployment_revision

    db = broker.database
    revision = _bound_deployment_revision(db, profile_id) or _captured_deployment_revision(db, profile_id)
    return Engine(str(revision), "", profile_id) if revision else None


def _next_in_chain(broker: Any, job: str, first: Engine) -> Optional[Engine]:
    """The second engine of the job's assignment chain, or ``None``."""
    try:
        from .inference_route_plan_service import ROUTE_PLANNING_AUTHORITY
        from .project_update_service import _captured_deployment_revision

        plan = broker.inference_adoption_service.plans.resolve_route_plan(
            ROUTE_PLANNING_AUTHORITY, capability_id=job,
        )
        entries = sorted((e for e in (plan.get("entries") or ()) if e), key=lambda e: int(e.get("ordinal") or 0))
        for entry in entries:
            revision = str(entry.get("deployment_revision_id") or "")
            profile = str(entry.get("profile_id") or "")
            if not revision or revision == first.revision or (profile and profile == first.profile):
                continue
            if broker.database.deployment_revisions.get(revision) is None:
                revision = _captured_deployment_revision(broker.database, profile)
            if revision:
                return Engine(revision, first.assignment, profile)
    except Exception:
        return None
    return None


def egress_of(broker: Any, engine: Engine) -> str:
    """Where the engine's bytes go, as a lamp word: local, mesh,
    private_network or cloud (``unknown`` when the revision is not read)."""
    from ..inference_locality import deployment_lamp

    try:
        revision = broker.database.deployment_revisions.get(engine.revision)
    except Exception:
        revision = None
    if revision is None:
        return "unknown"
    return deployment_lamp(getattr(revision, "boundary", ""), getattr(revision, "endpoint", ""))


DEFAULT_CONTEXT_TOKENS = 16384


def room(broker: Any, engine: Engine, payload: Any, *, reserved_output_tokens: int, whole: bool = False) -> int:
    """Tokens left on the engine after ``payload`` and the reserved answer
    (one token for each 3.5 characters of the JSON payload, rounded up, plus
    16). A job's budget is the revision's ceiling, at most 16384; ``whole``
    (the chat turn) reads the whole ceiling, as its admission did. Negative
    means the payload does not fit."""
    import json

    try:
        revision = broker.database.deployment_revisions.get(engine.revision)
        ceiling = int(getattr(revision, "context_ceiling", 0) or 0)
    except Exception:
        ceiling = 0
    ceiling = (ceiling if whole else min(ceiling, DEFAULT_CONTEXT_TOKENS)) if ceiling else DEFAULT_CONTEXT_TOKENS
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    return ceiling - (-(-len(text) * 2 // 7) + 16 + int(reserved_output_tokens))


def with_memory(
    broker: Any, engine: Engine, payload: dict[str, Any], memory: Any, *,
    reserved_output_tokens: int, field: str = "user_prompt",
) -> dict[str, Any]:
    """``payload`` with the MEMORY block put before ``field``, cut to what the
    engine has room for. Memory never turns a job that fits into one that
    does not; any memory error leaves the payload as it is."""
    from .memory_grounding import fit_memory
    from .memory_grounding import with_memory as prefixed

    prompt = str(payload.get(field) or "")

    def build(candidate: Any) -> dict[str, Any]:
        return {**payload, field: prefixed(prompt, candidate)}

    try:
        fitted = fit_memory(memory(), lambda candidate: room(
            broker, engine, build(candidate), reserved_output_tokens=reserved_output_tokens) >= 0)
        return build(fitted)
    except Exception:
        return dict(payload)


def run(
    broker: Any,
    principal: Any,
    job: str,
    payload: Any,
    *,
    engine: Optional[Engine] = None,
    contract: str = "",
    contract_revision: str = "1",
    deadline: float = DEFAULT_DEADLINE_SECONDS,
    adapter: Any = None,
    result_ref: Optional[str] = None,
    invocation_id: str = "",
    stage: Optional[tuple[str, Callable[[Any], Mapping[str, Any]]]] = None,
    retry: Optional[tuple[str, str]] = None,
    on_delta: Optional[Callable[[Any], None]] = None,
    prepare: Optional[Callable[[Any, Engine], Any]] = None,
    subject: Optional[tuple[str, str]] = None,
    parent_context: Any = None,
    planned_node: str = "",
    before_physical_dispatch: Any = None,
    before_compatibility_retry: Any = None,
) -> Answer:
    """Run ``job`` once on its assigned engine (or on ``engine`` when the
    caller already holds one) and return the answer.

    ``contract`` names the payload shape in the receipt (default: the job).
    ``adapter`` turns the payload into the provider call (default: a
    system/user prompt). ``stage`` is ``(kind, encoder)``: the answer is
    staged as that projection kind and published (``Answer.published``) only
    once the runner's receipt says the job succeeded. When the engine fails
    plainly (``failed`` or ``refused``) and the assignment names a next engine,
    the job runs once more on it; ``Answer.engine`` is the one that answered.
    ``retry`` is ``(kind, key)``: the caller's own name for this job. A job
    that fails waits on the owner in Needs you (``failure_items``); when
    ``kind`` is registered (``on_retry``) its row has Retry. A caller that
    names its own ``invocation_id`` (a Stop handle) is not tracked.
    ``on_delta``: the job streams (``run_stream``). ``prepare(payload,
    engine)`` gives the bytes that go to that engine. ``subject`` is as in
    ``engine_for``. ``parent_context`` runs the job as a child of a live
    parent run (a dictation or meeting session). ``before_physical_dispatch``
    and ``before_compatibility_retry`` are the runner's hooks (a Thought binds
    each attempt with them); the retry on the next engine is attempt 2.
    Raises ``EngineDoorError``.
    """
    if engine is None:
        engine = engine_for(broker, job, subject=subject)
    if not invocation_id:
        invocation_id = door_id(job, retry)
    started: list[bool] = []

    def forward(delta: Any) -> None:
        started.append(getattr(delta, "kind", "") in _STARTED)
        on_delta(delta)  # type: ignore[misc]

    def once(on: Engine, run_id: str, attempt: int) -> Answer:
        return _run_once(
            broker, principal, job, prepare(payload, on) if prepare else payload, engine=on,
            contract=contract, contract_revision=contract_revision, deadline=deadline, adapter=adapter,
            result_ref=result_ref, invocation_id=run_id, stage=stage,
            on_delta=forward if on_delta else None, parent_context=parent_context, planned_node=planned_node,
            attempt=attempt, before_physical_dispatch=before_physical_dispatch,
            before_compatibility_retry=before_compatibility_retry,
        )

    try:
        return once(engine, invocation_id, 1)
    except EngineDoorError as exc:
        # One retry on the next engine of the chain, only when the first one
        # said plainly that it did not answer, and (streamed) before its
        # first token: after it, the failure is the job's.
        if engine.fallback is None or any(started) or exc.outcome not in {"failed", "refused"}:
            raise
        first = exc.sent
    try:
        # ``_n2``, never ``_r2``: the runner names its own dialect retry ``_r2``.
        answer = once(engine.fallback, (invocation_id + "_n2") if invocation_id else "", 2)
    except EngineDoorError as again:
        again.sent = first + again.sent
        raise
    return replace(answer, sent=first + answer.sent)


#: Delta kinds that mean a streamed answer has started.
_STARTED = frozenset({"text", "reasoning", "tool_calls"})


def run_stream(broker: Any, principal: Any, job: str, payload: Any, *, on_delta: Callable[[Any], None],
               adapter: Any, **kwargs: Any) -> Answer:
    """``run`` for a streamed job: the runner gives each ``Delta`` to
    ``on_delta``; the one retry on the next engine happens only before the
    first token."""
    return run(broker, principal, job, payload, on_delta=on_delta, adapter=adapter, **kwargs)


def route(broker: Any, sent: Any) -> Optional[dict[str, Any]]:
    """Where a job's bytes went (Article III): of its attempts that were sent,
    the least private (on a tie, the later). ``{lamp, host, model, receipt,
    fallback}``: ``receipt`` is that attempt's kernel operation, ``fallback``
    is True when that attempt did not answer and another one did. ``None``
    when no attempt was sent or its engine is not read."""
    from ..inference_locality import _SENT_PHASES, LAMP_RANK, _attempt_route

    db = getattr(broker, "database", None)
    sent = tuple(sent or ())
    answered = any(attempt[3] == "succeeded" for attempt in sent)
    best: Optional[tuple[tuple[int, int], dict[str, Any]]] = None
    for index, (revision, send_phase, operation_id, outcome) in enumerate(sent):
        if db is None or send_phase not in _SENT_PHASES:
            continue
        try:
            row = db.deployment_revisions.get(revision)
            if row is None:
                continue
            with db._connection() as conn:
                where = _attempt_route(conn, {"deployment_revision_id": revision,
                                              "boundary": getattr(row, "boundary", "")})
        except Exception:
            continue
        key = (LAMP_RANK[where["lamp"]], index)
        if best is None or key > best[0]:
            best = (key, {**where, "receipt": operation_id, "fallback": answered and outcome != "succeeded"})
    return best[1] if best else None


def stop(broker: Any, run_id: str) -> str:
    """The owner's Stop on a running job: the runner's cancel signal. A
    stopped job is his decision: it never waits in Needs you (``_stopped``)."""
    return broker.inference_runner.cancel(run_id)


def reason(exc: EngineDoorError) -> str:
    """The face reason token for a job that did not complete."""
    if exc.code == "no_engine":
        return "no_engine"
    if exc.send_phase == "pre_send":
        return "not_reachable"
    if exc.error == "inference_local_runtime_busy":
        return "engine_busy"
    return {"refused": "refused", "cancelled": "stopped"}.get(exc.outcome, "did_not_answer")


def _run_once(
    broker: Any, principal: Any, job: str, payload: Any, *, engine: Engine, contract: str,
    contract_revision: str, deadline: float, adapter: Any, result_ref: Optional[str],
    invocation_id: str, stage: Any, on_delta: Any, parent_context: Any, planned_node: str,
    attempt: int = 1, before_physical_dispatch: Any = None, before_compatibility_retry: Any = None,
) -> Answer:
    from ..kernel.inference_runner import InvocationRequest, ServiceContract
    from ..kernel.runtime import _as_principal

    if adapter is None:
        from ..kernel.prompt_adapter import CanonicalPromptAdapter

        adapter = CanonicalPromptAdapter()
    contract = contract or job
    if stage is not None and not invocation_id:
        invocation_id = "door_" + uuid.uuid4().hex
    request = InvocationRequest(
        deployment_revision=engine.revision,
        definition_origin=ServiceContract.for_payload(contract, contract_revision, payload),
        deadline_at=time.time() + deadline,
        payload=payload,
        invocation_id=invocation_id,
        parent_operation_id=str(getattr(parent_context, "operation_id", "") or ""),
        attempt_ordinal=attempt,
        before_physical_dispatch=before_physical_dispatch,
        before_compatibility_retry=before_compatibility_retry,
    )
    captured: list[Any] = []
    ref = result_ref or f"{contract.replace('.', '-')}:{engine.assignment or engine.revision}"

    def _capture(value: Any) -> str:
        captured.append(value)
        return ref

    publish: Any = _capture
    if stage is not None:
        kind, encode = stage

        def _encode(value: Any) -> Mapping[str, Any]:
            captured.append(value)
            return encode(value)

        # The stager's publisher follows a dialect retry onto the attempt that ran.
        publish = broker.projection_stager.publisher(invocation_id, kind, _encode)
    with _as_principal(principal):
        if on_delta is None:
            outcome = broker.inference_runner.invoke(
                request, adapter, publish=publish, parent_context=parent_context, planned_node=planned_node,
            )
        else:
            outcome = broker.inference_runner.invoke_stream(
                request, adapter, on_delta=on_delta, publish=publish,
                parent_context=parent_context, planned_node=planned_node,
            )
    sent = ((engine.revision, str(getattr(outcome, "send_phase", "") or ""),
             str(getattr(outcome, "operation_id", "") or ""), str(getattr(outcome, "outcome", "") or "")),)
    try:
        answer = _answer(outcome, captured, engine, job)
    except EngineDoorError as exc:
        exc.sent = sent
        raise
    if stage is not None:
        answer = replace(
            answer, published=broker.projection_stager.finalize(invocation_id), invocation_id=invocation_id,
        )
    return replace(answer, sent=sent)


def _answer(outcome: Any, captured: list[Any], engine: Engine, job: str) -> Answer:
    operation_id = str(getattr(outcome, "operation_id", "") or "")
    status = getattr(outcome, "outcome", None)
    state = str(status or "")
    send_phase = str(getattr(outcome, "send_phase", "") or "")
    failed = isinstance(status, str) and status != "succeeded"
    result = captured[0] if captured else getattr(outcome, "result", None)
    if failed or result is None:
        error = str(getattr(outcome, "error", "") or "")
        raise EngineDoorError(
            "failed", f"{job} did not complete: {error or state or 'no answer'}",
            operation_id=operation_id, outcome=state, send_phase=send_phase, error=error,
        )
    return Answer(result=result, operation_id=operation_id, engine=engine, outcome=state, send_phase=send_phase)


# ── A failed job waits on the owner (Needs you), and Retry ───────────────
#
# The record is the runner's receipt: every door job without a caller-made
# id runs under ``door_<job>_<kind>_<key>_<nonce>`` (each part hex, so the
# kernel's alphanumeric rule holds and the parts split back). A job whose
# LATEST receipt for its (job, kind, key) is not a success waits on him.
# Nothing else is written.

_DOOR_PREFIX = "door_"


def _hex(text: str) -> str:
    return text.encode("utf-8").hex()


def door_id(job: str, retry: Optional[tuple[str, str]], nonce: str = "") -> str:
    """The tracked runner id of one job. A caller that needs its own handle
    (a Stop) passes it as ``nonce`` and passes the result as ``invocation_id``."""
    kind, key = retry if retry else ("", "")
    return f"{_DOOR_PREFIX}{_hex(job)}_{_hex(kind)}_{_hex(key)}_{nonce or uuid.uuid4().hex[:12]}"


def _parse_door_id(native_id: str) -> Optional[tuple[str, str, str]]:
    parts = native_id.split("_")
    if len(parts) < 5 or parts[0] != "door":
        return None
    try:
        return tuple(bytes.fromhex(part).decode("utf-8") for part in parts[1:4])  # type: ignore[return-value]
    except ValueError:
        return None


@dataclass(frozen=True)
class RetryKind:
    """What a caller registers for its jobs: the words of the job ("the
    journal summary"), the kind of object the row shows (its sprite), the
    ref the row opens, and the callable that runs the same job again."""

    words: str
    object_kind: str
    open_ref: Callable[[str], str]
    run: Optional[Callable[[Any, str], Any]] = None


#: The one registry: retry kind -> RetryKind. Callers register at import.
RETRY: dict[str, RetryKind] = {}

#: Words for a job that names no retry kind (its capability id).
JOB_WORDS = {
    "background.rails_summary": "the journal summary",
    "decision.promotion_draft": "the decision draft",
    "delivery.pr_review_draft": "the review draft",
    "calendar.snapshot_extract": "the calendar picture",
    "background.cadence_draft": "the next action",
    "chat.guardrail": "the thread check",
    "chat.compact": "the thread summary",
    "memory.embed": "memory search",
    "memory.extract": "memory notes",
    "memory.consolidate": "memory",
    "memory.page": "a memory page",
    "agent.plan": "the program plan",
    "ask.answer": "an answer",
    "chat.turn": "the reply",
    "meeting.deferred_analysis": "the note's tasks",
    "project.brief.prepare": "the brief",
    "speech.rewrite": "the dictation rewrite",
    "speech.intent_classify": "the dictation intent",
    "speech.punctuate": "the dictation punctuation",
    "meeting.live_analysis": "the live meeting notes",
    "meeting.bookmark_label": "a bookmark label",
    "meeting.auto_title": "the meeting title",
    "project.update_draft": "the update draft",
    "recipe.run": "the agent's answer",
}

ENGINES_REF = "window:surface-engines"


def on_retry(kind: str, entry: RetryKind) -> None:
    RETRY[kind] = entry


#: The callers that register a Retry at import; read before the registry is.
_RETRY_CALLERS = (
    "holdspeak.rails_observer",
    "holdspeak.services.decision_lifecycle_service",
    "holdspeak.web.routes.delivery_prs",
    "holdspeak.services.ask_service",
    "holdspeak.services.thread_service",
)


def _load_retry_callers() -> None:
    import importlib

    for name in _RETRY_CALLERS:
        try:
            importlib.import_module(name)
        except Exception:  # a caller that cannot load has no Retry
            continue


def _stopped(row: Any) -> bool:
    """The owner's Stop (``stop``): a cancel signal on the job before its
    deadline. His decision, never a failure. A cancel at the deadline is the
    runner's watchdog: the job ran out of time, and that is a failure."""
    cancelled_at = row["cancelled_at"]
    return cancelled_at is not None and float(cancelled_at) - float(row["created_at"]) < DEFAULT_DEADLINE_SECONDS - 1


def _reason(state: str, send_phase: str) -> str:
    """One line in the owner's words; never a path, a host or a trace."""
    if state == "refused":
        return "it was not ready"
    if state == "cancelled":
        return "it ran out of time"
    if state == "indeterminate":
        return "no answer came back"
    if send_phase == "pre_send":
        return "it could not be reached"
    return "it gave no answer"


def _engine_name(conn: Any, target_ref: str) -> str:
    revision_id = target_ref.removeprefix("deployment-revision:")
    row = conn.execute(
        "SELECT destination_id, model FROM deployment_revisions WHERE id=?", (revision_id,),
    ).fetchone()
    if row is None:
        return "Your engine"
    label = conn.execute(
        "SELECT label FROM model_profile_revisions WHERE profile_id=? ORDER BY revision DESC LIMIT 1",
        (row["destination_id"],),
    ).fetchone()
    return str((label["label"] if label else "") or row["model"] or "Your engine").strip()


def failure_items(db: Any) -> list[dict[str, Any]]:
    """Every door job whose latest receipt for its (job, kind, key) failed
    on its own (a Stop is not a failure: ``_stopped``).

    ``{key, job, kind, retry_key, engine, words, reason, since, object_kind,
    open_ref, can_retry}``, newest first. A read of the kernel's receipts.
    """
    if db is None:
        return []
    import json
    from datetime import datetime, timezone

    _load_retry_callers()
    latest: dict[tuple[str, str, str], dict[str, Any]] = {}
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT o.native_id, o.target_ref, o.created_at, r.state, a.material_json,
                      (SELECT MIN(c.created_at) FROM kernel_operations c
                        WHERE c.name = 'inference.cancel' AND c.parent_operation_id = o.operation_id) AS cancelled_at
                 FROM kernel_operations o
                 JOIN kernel_receipts r ON r.operation_id = o.operation_id
                 LEFT JOIN kernel_inference_receipt_attestations a ON a.operation_id = o.operation_id
                WHERE o.name = 'inference.invoke' AND o.native_id LIKE 'door\\_%' ESCAPE '\\'
                ORDER BY o.created_at""",
        ).fetchall()
        for row in rows:
            parsed = _parse_door_id(str(row["native_id"]))
            if parsed is None:
                continue
            latest[parsed] = {**dict(row), "engine": ""}
        failed = {k: v for k, v in latest.items() if str(v["state"]) != "succeeded" and not _stopped(v)}
        for value in failed.values():
            value["engine"] = _engine_name(conn, str(value["target_ref"] or ""))
    out: list[dict[str, Any]] = []
    for (job, kind, key), row in failed.items():
        try:
            evidence = json.loads(row["material_json"] or "{}")
        except ValueError:
            evidence = {}
        entry = RETRY.get(kind)
        since = datetime.fromtimestamp(float(row["created_at"]), tz=timezone.utc).isoformat(timespec="seconds")
        out.append({
            "key": f"{job}:{kind}:{key}" if kind else job,
            "job": job, "kind": kind, "retry_key": key,
            "engine": row["engine"],
            "words": entry.words if entry else JOB_WORDS.get(job, "an AI job"),
            "reason": _reason(str(row["state"]), str(evidence.get("send_phase") or "")),
            "since": since,
            "object_kind": entry.object_kind if entry else "engine",
            "open_ref": entry.open_ref(key) if entry else ENGINES_REF,
            "can_retry": bool(entry and entry.run and key),
        })
    out.sort(key=lambda item: item["since"], reverse=True)
    return out


def retry(principal: Any, kind: str, key: str) -> Any:
    """Run the same job again through its caller's registered callable.
    Raises ``EngineDoorError('no_retry')`` for a kind with no Retry."""
    _load_retry_callers()
    entry = RETRY.get(kind)
    if entry is None or entry.run is None or not key:
        raise EngineDoorError("no_retry", f"{kind or 'This job'} has no Retry")
    return entry.run(principal, key)

