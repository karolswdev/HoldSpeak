"""Gated write-connector framework + permission manifest (Phase 38, HS-38-01).

Phase 37 proved actuators are *safe*: an actuator proposes, a human approves, and
a guarded executor (`actuator_executor.ActuatorExecutor`) acts on the approved
proposal through an **injected** `connector(proposal) -> dict`. The executor is
deliberately connector-agnostic — it never opens a socket or shells out itself.

To do *real writes* safely we need a contract for the connectors the executor
injects. The only built-in connector pack (`github_cli`) is **read-only by
Phase-25 policy**; the Phase-37 reference connector writes a local file. This
module is the missing seam: a **write-connector permission manifest** plus a
`build_gated_connector(...)` helper that turns a side-effect *plan* into a gated
`connector(proposal) -> dict`.

The manifest declares the connector's concrete scope: argv prefixes for a CLI
connector or hosts for an outbound connector. Since HS-107-03, subprocess plans
carry that trusted scope into ``subprocess.exec`` admission; since HS-107-04,
outbound plans carry permission and host scope into ``external.egress`` too.
The kernel is the only policy decision and binds argv/cwd or destination/data
classes before approval.

`build_gated_connector` therefore runs plan → kernel → interpret for both
operation families. Either refusal occurs before the effect.

A connector with an empty allow-list admits nothing and so *does nothing* — the
manifest can only ever narrow, never widen, what reaches the wire. The concrete
GitHub (`gh issue create`) and webhook (HTTP POST) connectors are HS-38-02 /
HS-38-03; this story ships only the framework, exercised with a fake gate/runner.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional

from ..connector_runtime import PermissionGate, SubprocessRunner
from ..kernel.external_egress import EgressOperationRefused
from ..kernel.subprocess_exec import SubprocessOperationRefused
from ..connector_sdk import NETWORK_PERMISSIONS, ConnectorManifest
from .actuator_executor import Connector

# The two egress permissions a *write* connector may hold, each mapped to the
# `PermissionGate` operation it unlocks. A write connector declares exactly one.
_PERMISSION_OPERATIONS: dict[str, str] = {
    "shell:exec": "run_subprocess",
    "network:outbound": "open_outbound_socket",
}
WRITE_PERMISSIONS: frozenset[str] = frozenset(_PERMISSION_OPERATIONS)


class ConnectorOperationRefused(RuntimeError):
    """A planned operation is not on the connector's permission manifest.

    Raised by the gated connector **before** any egress when the manifest does
    not admit the planned op. The `ActuatorExecutor` catches it like any other
    connector failure: the proposal becomes `failed` (retryable) with an audit
    row, and **no** side effect occurs. The string form is operator-readable.
    """

    def __init__(self, *, connector_id: str, operation: str, reason: str) -> None:
        self.connector_id = connector_id
        self.operation = operation
        self.reason = reason
        super().__init__(
            f"connector {connector_id!r} refused operation [{operation}]: {reason}"
        )


@dataclass(frozen=True)
class GatedOperation:
    """One concrete side effect, planned from a proposal, awaiting the gate.

    A connector's `plan(proposal)` returns exactly one of these. `kind` selects
    the `PermissionGate` operation the framework dispatches to:

      - ``"subprocess"`` — `argv` is the full command line; `subprocess_kwargs`
        is forwarded to the runner (e.g. ``capture_output``/``text``/``timeout``).
      - ``"outbound"`` — `address` is the ``(host, port)`` socket to open;
        `request` carries whatever the connector's opener needs to send.
    """

    kind: str
    argv: tuple[str, ...] = ()
    address: Optional[tuple[str, int]] = None
    request: Any = None
    subprocess_kwargs: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def subprocess(cls, argv: "Any", **subprocess_kwargs: Any) -> "GatedOperation":
        return cls(
            kind="subprocess",
            argv=tuple(str(a) for a in argv),
            subprocess_kwargs=dict(subprocess_kwargs),
        )

    @classmethod
    def outbound(cls, host: str, port: int, *, request: Any = None) -> "GatedOperation":
        return cls(kind="outbound", address=(str(host), int(port)), request=request)

    @property
    def host(self) -> Optional[str]:
        return self.address[0] if self.address else None

    def summary(self) -> str:
        """A short, operator-readable description for refusals / audit detail."""
        if self.kind == "subprocess":
            return "subprocess: " + " ".join(self.argv)
        if self.kind == "outbound" and self.address is not None:
            return f"outbound: {self.address[0]}:{self.address[1]}"
        return self.kind


def _argv_has_allowed_prefix(
    argv: tuple[str, ...], prefixes: tuple[tuple[str, ...], ...]
) -> bool:
    """True iff `argv` starts with one of the declared token prefixes.

    Mirrors `connector_packs.github_cli.is_command_allowed` but generalized to
    arbitrary-length prefixes matched from the *first* token, so the connector's
    own `argv[0]` (e.g. ``"gh"``) participates in the match.
    """
    for prefix in prefixes:
        if len(prefix) <= len(argv) and argv[: len(prefix)] == tuple(prefix):
            return True
    return False


@dataclass(frozen=True)
class WriteConnectorManifest:
    """The narrow allow-list for one write connector.

    Declares the `PermissionGate` permission token the connector needs plus the
    concrete operations it may perform. Exactly one permission; the matching
    allow-list is consulted:

      - ``shell:exec``      → `allowed_argv_prefixes` (a command is admitted iff
                              its argv starts with one of these token tuples).
      - ``network:outbound`` → `allowed_hosts` (an op is admitted iff its target
                              host is a member, case-insensitive).

    An empty allow-list admits nothing — the connector then does nothing, which
    is the safe default. The manifest can only narrow what reaches the wire.
    """

    connector_id: str
    permission: str
    label: str = ""
    description: str = ""
    allowed_argv_prefixes: tuple[tuple[str, ...], ...] = ()
    allowed_hosts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.permission not in WRITE_PERMISSIONS:
            raise ValueError(
                f"write-connector permission must be one of "
                f"{sorted(WRITE_PERMISSIONS)}; got {self.permission!r}"
            )

    @property
    def operation(self) -> str:
        """The `PermissionGate` operation this permission unlocks."""
        return _PERMISSION_OPERATIONS[self.permission]

    def allows(self, op: GatedOperation) -> bool:
        """True iff this manifest admits the concrete operation `op`."""
        if self.permission == "shell:exec":
            return op.kind == "subprocess" and _argv_has_allowed_prefix(
                op.argv, self.allowed_argv_prefixes
            )
        if self.permission == "network:outbound":
            host = (op.host or "").lower()
            return (
                op.kind == "outbound"
                and bool(host)
                and host in {h.lower() for h in self.allowed_hosts}
            )
        return False  # pragma: no cover — __post_init__ rejects other permissions

    def build_gate(self) -> PermissionGate:
        """A `PermissionGate` that admits exactly this connector's permission."""
        return PermissionGate(self._synthesize_manifest())

    def _synthesize_manifest(self) -> ConnectorManifest:
        """A minimal `ConnectorManifest` carrying this connector's permission.

        The `PermissionGate` consults only `.id` + `.permissions`; the remaining
        fields are placeholders so we reuse the existing gate rather than add a
        second egress primitive.
        """
        return ConnectorManifest(
            id=self.connector_id,
            label=self.label or self.connector_id,
            version="0.0.0",
            kind="cli_enrichment",
            capabilities=("commands",),
            description=self.description,
            permissions=(self.permission,),
            requires_network=self.permission in NETWORK_PERMISSIONS,
        )


def _route(
    gate: PermissionGate,
    op: GatedOperation,
    *,
    manifest: WriteConnectorManifest,
    runner: Optional[SubprocessRunner],
    opener: Optional[Callable[[GatedOperation], Any]],
) -> Any:
    """Dispatch an op; subprocess authority is resolved only by the kernel."""
    if op.kind == "subprocess":
        return gate.execute_subprocess(
            op.argv,
            runner=runner,
            allowed_argv_prefixes=manifest.allowed_argv_prefixes,
            **dict(op.subprocess_kwargs),
        )
    if op.kind == "outbound":
        if op.address is None:
            raise ValueError("outbound GatedOperation requires an address")
        if opener is None:
            raise ConnectorOperationRefused(
                connector_id=manifest.connector_id,
                operation=op.summary(),
                reason="outbound connector has no HTTP opener",
            )
        # The kernel-bound sender receives only the address; close over the full
        # immutable plan so the connector opener can send ``op.request``.
        return gate.open_outbound_socket(
            op.address,
            opener=lambda _addr: opener(op),
            allowed_hosts=manifest.allowed_hosts,
        )
    raise ValueError(f"unknown GatedOperation.kind: {op.kind!r}")


def build_gated_connector(
    manifest: WriteConnectorManifest,
    *,
    plan: Callable[[Any], GatedOperation],
    interpret: Callable[[Any, GatedOperation], "dict[str, Any]"],
    gate: Optional[PermissionGate] = None,
    runner: Optional[SubprocessRunner] = None,
    opener: Optional[Callable[[GatedOperation], Any]] = None,
) -> Connector:
    """Wrap a side-effect plan in its typed subprocess or outbound authority path.

    Returns the `connector(proposal) -> dict` the `ActuatorExecutor` expects.
    The author supplies:

      - `plan(proposal) -> GatedOperation` — the one concrete op this proposal
        would perform, derived from its stored payload (mutation-free).
      - `interpret(raw, op) -> dict` — maps the gate's raw result into the
        executor's result dict; may raise to mark the proposal `failed`.
      - `runner` (CLI) / `opener` (outbound) — injected effect primitives so
        tests drive the full loop with **no** real subprocess or network call.
        Subprocess has a real default; outbound without its HTTP opener refuses
        by name because the removed raw-socket branch was never a connector.

    `gate` defaults to one synthesized from the manifest; it passes declared
    permission and destination scope into kernel admission. Tests may inject a
    spy with that same shape.

    Both operation families run **plan → kernel → interpret**.
    """
    the_gate = gate if gate is not None else manifest.build_gate()

    def _connector(proposal: Any) -> "dict[str, Any]":
        op = plan(proposal)
        if not isinstance(op, GatedOperation):
            raise TypeError(
                f"plan() must return a GatedOperation, got {type(op).__name__}"
            )
        # The codec receives every concrete constraint. There is no manifest
        # decision here in addition to kernel admission.
        try:
            raw = _route(
                the_gate, op, manifest=manifest, runner=runner, opener=opener
            )
        except (SubprocessOperationRefused, EgressOperationRefused) as exc:
            raise ConnectorOperationRefused(
                connector_id=manifest.connector_id,
                operation=op.summary(),
                reason=exc.reason,
            ) from exc
        return interpret(raw, op)

    return _connector


__all__ = [
    "ConnectorOperationRefused",
    "GatedOperation",
    "WRITE_PERMISSIONS",
    "WriteConnectorManifest",
    "build_gated_connector",
]
