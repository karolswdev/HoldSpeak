"""Connector runtime gates — in-process permission enforcement.

HS-13-02. Phase 11 manifests declare what a connector pack is
*allowed* to do (`shell:exec`, `network:outbound`,
`loopback:http`, `fs:read`). Until this story those declarations
were documentation; this module turns them into runtime checks.

`PermissionGate` wraps the privileged operations a pack might
invoke. Subprocess execution and outbound egress now carry manifest
permissions and concrete constraints into kernel admission, while CLI
reads check principal plus named read authority here. The file branch
retains the legacy manifest check. A missing permission raises
`PermissionDenied` with the connector and operation named.

This is *honest enforcement*, not a security boundary. A
malicious pack can still call `subprocess.run` directly. The
point is that an *honest* pack which over-declares its capability
or under-declares its permissions fails loud, every time, in
tests. Combined with the manifest validator (which already
rejects unknown permissions) this gives the runtime a single
"what does this pack actually need" surface that survives
phase 13's later stories (settings, run history, pipelines).
"""

from __future__ import annotations

import socket
import subprocess
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from .connector_sdk import ConnectorManifest
from .kernel.external_egress import EgressOperationRefused, run_external_egress
from .kernel.subprocess_exec import (
    LOCAL_OWNER,
    SubprocessOperationRefused,
    run_subprocess_operation,
)
from .principals import Principal, PrincipalKind, PrincipalRight

# Operation → permission mapping. A pack must declare the listed
# permission to invoke the gate's matching method. The mapping
# is intentionally one-to-one; pipelines that need multiple
# operations declare each permission they need.
_OPERATION_PERMISSIONS: dict[str, str] = {
    "run_subprocess": "shell:exec",
    "open_outbound_socket": "network:outbound",
    "accept_loopback_event": "loopback:http",
    "read_file": "fs:read",
}


class ReadSubprocessDenied(PermissionError):
    """A named CLI read lacks an authenticated owner read authority."""

    def __init__(self, *, command_name: str, principal: Principal) -> None:
        self.command_name = command_name
        self.principal = principal
        super().__init__(
            f"subprocess read {command_name!r} refused: principal "
            f"{principal.identity!r} lacks read authority for {command_name!r}"
        )


def require_subprocess_read_authority(
    principal: Principal, command_name: str
) -> None:
    """Require authenticated owner read authority for one named ambient CLI."""
    if (
        principal.kind is not PrincipalKind.OWNER
        or not principal.permits(PrincipalRight.READ)
    ):
        raise ReadSubprocessDenied(
            command_name=command_name, principal=principal
        )


class PermissionDenied(Exception):
    """Raised when a pack invokes a gated operation without permission.

    Carries the connector id, the operation name, the permission
    that would have allowed it, and the full declared permission
    set on the pack's manifest. The string form is operator-
    readable so it can be persisted directly as
    `connector.last_error`.
    """

    def __init__(
        self,
        *,
        connector_id: str,
        operation: str,
        required_permission: str,
        declared_permissions: tuple[str, ...],
    ) -> None:
        self.connector_id = connector_id
        self.operation = operation
        self.required_permission = required_permission
        self.declared_permissions = tuple(declared_permissions)
        declared = ", ".join(self.declared_permissions) or "(none)"
        message = (
            f"connector {self.connector_id!r} attempted "
            f"{self.operation!r} which requires permission "
            f"{self.required_permission!r}; manifest declares: {declared}"
        )
        super().__init__(message)


# Subprocess runner shape — `subprocess.run` by default, but
# tests inject fakes through the same parameter name the
# pre-phase-13 runners already used.
SubprocessRunner = Callable[..., subprocess.CompletedProcess[str]]


class PermissionGate:
    """Per-pack runtime gate.

    Constructed once per pack invocation; methods consult the
    underlying manifest before performing the gated operation.
    """

    def __init__(self, manifest: ConnectorManifest) -> None:
        self.manifest = manifest

    # ───────────────────── core check ─────────────────────

    def _require(self, operation: str) -> None:
        permission = _OPERATION_PERMISSIONS.get(operation)
        if permission is None:  # programming error — unknown operation
            raise ValueError(f"PermissionGate has no operation {operation!r}")
        if permission not in self.manifest.permissions:
            raise PermissionDenied(
                connector_id=self.manifest.id,
                operation=operation,
                required_permission=permission,
                declared_permissions=tuple(self.manifest.permissions),
            )

    # ─────────────────── gated operations ─────────────────

    def execute_subprocess(
        self,
        command: Iterable[str],
        *,
        runner: Optional[SubprocessRunner] = None,
        principal: Principal = LOCAL_OWNER,
        allowed_argv_prefixes: Iterable[Iterable[str]] = (),
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        """Execute a consequential connector command through the kernel.

        The manifest permission and any argv prefixes are hard prerequisites of
        the typed admission, not a second decision in this legacy gate.
        """
        try:
            return run_subprocess_operation(
                tuple(command),
                connector_id=self.manifest.id,
                declared_permissions=self.manifest.permissions,
                allowed_argv_prefixes=tuple(tuple(prefix) for prefix in allowed_argv_prefixes),
                principal=principal,
                runner=runner or subprocess.run,
                **kwargs,
            )
        except SubprocessOperationRefused as exc:
            if exc.reason.startswith("subprocess_permission_required:"):
                raise PermissionDenied(
                    connector_id=self.manifest.id,
                    operation="run_subprocess",
                    required_permission="shell:exec",
                    declared_permissions=tuple(self.manifest.permissions),
                ) from exc
            raise

    def run_read_subprocess(
        self,
        command: Iterable[str],
        *,
        principal: Principal = LOCAL_OWNER,
        runner: Optional[SubprocessRunner] = None,
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        """Run a classified CLI read after principal and named read authority."""
        argv = tuple(str(part) for part in command)
        command_name = Path(argv[0]).name if argv else "<empty>"
        require_subprocess_read_authority(principal, command_name)
        self._require("run_subprocess")
        actual = runner or subprocess.run
        return actual(list(argv), **kwargs)

    # Compatibility name; consequential dispatch itself is ``execute_subprocess``.
    run_subprocess = execute_subprocess

    def open_outbound_socket(
        self,
        address: tuple[str, int],
        *,
        opener: Optional[Callable[[tuple[str, int]], Any]] = None,
        allowed_hosts: Optional[Iterable[str]] = None,
    ) -> Any:
        """Open one manifest-bound destination through kernel admission.

        The permission and optional host allow-list are codec prerequisites, not
        decisions made by this compatibility surface. Tests inject ``opener``;
        the real default socket callable executes only after a warrant is claimed.
        """
        host, port = str(address[0]).strip().lower(), int(address[1])
        destination = f"{host}:{port}"
        allowed = (
            tuple(f"{str(item).strip().lower()}:{port}" for item in allowed_hosts)
            if allowed_hosts is not None else None
        )
        actual = opener or socket.create_connection
        try:
            return run_external_egress(
                connector_id=self.manifest.id,
                destination=destination,
                data_classes=("connector_request",),
                payload_material={"destination": destination},
                declared_permissions=self.manifest.permissions,
                allowed_destinations=allowed,
                sender=actual,
                args=(address,),
            )
        except EgressOperationRefused as exc:
            if exc.reason.startswith("external_egress_permission_required:"):
                raise PermissionDenied(
                    connector_id=self.manifest.id,
                    operation="open_outbound_socket",
                    required_permission="network:outbound",
                    declared_permissions=tuple(self.manifest.permissions),
                ) from exc
            raise

    def accept_loopback_event(self) -> None:
        """Defense-in-depth check for extension-events ingestion.

        Requires `loopback:http`. The runtime binds 127.0.0.1 by
        default; this gate adds a second check that the pack
        which produced the event is allowed to feed loopback
        traffic into the ledger at all.
        """
        self._require("accept_loopback_event")

    def read_file(
        self,
        path: Path,
        *,
        opener: Optional[Callable[[Path], Any]] = None,
    ) -> Any:
        """Read a file outside HoldSpeak's data dir on behalf of the pack.

        Requires `fs:read`. Phase 13's existing first-party packs
        do not exercise this path, but the gate is in place so
        future packs (e.g. browser-history readers under
        HS-13-04+) route through a uniform surface. Tests inject
        `opener` to avoid touching the real filesystem.
        """
        self._require("read_file")
        actual = opener or (lambda p: Path(p).read_text())
        return actual(path)


__all__ = [
    "PermissionDenied",
    "PermissionGate",
    "ReadSubprocessDenied",
    "require_subprocess_read_authority",
    "PipelineRunner",
    "PipelineRunResult",
    "PipelineStepResult",
    "SubprocessRunner",
]


# ─────────────────────── Pipeline runner ────────────────────────
#
# HS-13-06. A pipeline pack (`kind: pipeline`) declares the
# upstream packs it consumes via `manifest.consumes`. The
# runner walks that declaration into a topological order and
# executes each step sequentially.
#
# Each upstream pack is either:
#   - skipped because its most recent run is "fresh" (a
#     successful `connector_runs` row within
#     `pipeline_freshness_seconds`),
#   - re-run by calling its module's `run(db, **kwargs)`
#     callable if one exists,
#   - reported as a step error if neither path is available.
#
# Failure of any step aborts the pipeline. The runner is
# deliberately simple: no retries, no parallelism, no
# back-pressure. Phase 14+ may complicate this if real
# workflows demand it.

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .connector_pack_loader import RegisteredPack
    from .db import Database

_runner_log = logging.getLogger(__name__)


class UnknownPipelineError(ValueError):
    """Raised when `PipelineRunner` is asked to run an unknown id."""


class NotAPipelineError(ValueError):
    """Raised when `PipelineRunner` is asked to run a non-pipeline pack."""


@dataclass(frozen=True)
class PipelineStepResult:
    """One step in a pipeline's execution.

    `status` is one of:
      - `"skipped_fresh"` — upstream had a recent successful run.
      - `"ran"` — runner invoked `pack.run(db)` and it succeeded.
      - `"failed"` — `pack.run(db)` raised or returned an error;
        `error` carries the message.
      - `"missing_runner"` — the pack does not expose a `run`
        callable AND has no fresh successful run; the pipeline
        cannot proceed past it.
    """

    pack_id: str
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass(frozen=True)
class PipelineRunResult:
    """Outcome of one `PipelineRunner.run(target)` invocation.

    `target` is the pipeline id; `steps` lists every step in
    execution order, ending with the target itself.
    `succeeded` is true iff every step ran or was skipped clean.
    """

    target: str
    steps: tuple[PipelineStepResult, ...]
    succeeded: bool

    def to_payload(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "succeeded": self.succeeded,
            "steps": [
                {
                    "pack_id": s.pack_id,
                    "status": s.status,
                    "started_at": s.started_at.isoformat() if s.started_at else None,
                    "finished_at": s.finished_at.isoformat() if s.finished_at else None,
                    "error": s.error,
                }
                for s in self.steps
            ],
        }


class PipelineRunner:
    """Topological runner over a tuple of `RegisteredPack`s.

    `now()` is injectable so the freshness-skip behaviour can be
    tested without time travel.
    """

    def __init__(
        self,
        db: "Database",
        *,
        registry: Optional[Iterable["RegisteredPack"]] = None,
        now: Optional[Callable[[], datetime]] = None,
    ) -> None:
        from .activity_connectors import _DISCOVERY  # local import to avoid cycle

        packs = tuple(registry) if registry is not None else _DISCOVERY.packs
        self._registry = packs
        self._by_id = {p.manifest.id: p for p in packs}
        self._db = db
        self._now = now or datetime.now

    # ────────────────────────── Plan ────────────────────────────

    def plan(self, target_id: str) -> list[str]:
        """Return the topological order of `target_id`'s
        dependency graph; the target appears last."""
        if target_id not in self._by_id:
            raise UnknownPipelineError(target_id)
        target = self._by_id[target_id]
        if target.manifest.kind != "pipeline":
            raise NotAPipelineError(target_id)

        order: list[str] = []
        visited: set[str] = set()

        def visit(node_id: str, stack: tuple[str, ...]) -> None:
            if node_id in visited:
                return
            if node_id in stack:
                # Should not be reachable: pipeline graph cycles
                # are rejected at registry build time. Defensive.
                raise NotAPipelineError(
                    f"pipeline cycle through {node_id!r}: "
                    f"{' → '.join(stack + (node_id,))}"
                )
            pack = self._by_id.get(node_id)
            if pack is None:
                # Unknown upstreams are also rejected at registry
                # build; defensive.
                visited.add(node_id)
                order.append(node_id)
                return
            for entry in pack.manifest.consumes:
                visit(entry.pack_id, stack + (node_id,))
            visited.add(node_id)
            order.append(node_id)

        visit(target_id, ())
        return order

    # ───────────────────────── Run ──────────────────────────────

    def run(self, target_id: str) -> PipelineRunResult:
        order = self.plan(target_id)
        steps: list[PipelineStepResult] = []
        succeeded = True
        for node_id in order:
            step = self._execute_step(node_id, target_id)
            steps.append(step)
            if step.status in {"failed", "missing_runner"}:
                succeeded = False
                break
        return PipelineRunResult(
            target=target_id, steps=tuple(steps), succeeded=succeeded
        )

    # ───────────────────── Step dispatch ────────────────────────

    def _execute_step(self, pack_id: str, target_id: str) -> PipelineStepResult:
        pack = self._by_id.get(pack_id)
        if pack is None:
            return PipelineStepResult(
                pack_id=pack_id,
                status="missing_runner",
                error=f"pack {pack_id!r} is not registered",
            )

        # The pipeline target itself never short-circuits on
        # freshness — invoking the pipeline is the whole point of
        # the call.
        if pack_id != target_id and self._is_fresh(pack):
            return PipelineStepResult(pack_id=pack_id, status="skipped_fresh")

        run_callable = getattr(pack.module, "run", None)
        if run_callable is None:
            return PipelineStepResult(
                pack_id=pack_id,
                status="missing_runner",
                error=(
                    f"pack {pack_id!r} has no recent successful run "
                    "and exposes no `run(db)` callable"
                ),
            )

        started = self._now()
        try:
            run_callable(self._db)
        except Exception as exc:  # noqa: BLE001 — surface to caller
            finished = self._now()
            self._db.activity.record_connector_run(
                connector_id=pack_id,
                started_at=started,
                finished_at=finished,
                succeeded=False,
                error=f"pipeline {target_id!r} step failed: {exc}",
            )
            return PipelineStepResult(
                pack_id=pack_id,
                status="failed",
                started_at=started,
                finished_at=finished,
                error=str(exc),
            )
        finished = self._now()
        return PipelineStepResult(
            pack_id=pack_id,
            status="ran",
            started_at=started,
            finished_at=finished,
        )

    # ─────────────────────── Freshness ──────────────────────────

    def _is_fresh(self, pack: "RegisteredPack") -> bool:
        """A pack is fresh if its most recent run succeeded
        within the freshness window. The window is read from the
        *target* pipeline's manifest in `run()`; here we reach
        for the pack's own freshness if it's a pipeline (so a
        pipeline upstream of another pipeline carries its own
        cadence) or fall back to 300s."""
        window_seconds = (
            pack.manifest.pipeline_freshness_seconds
            if pack.manifest.kind == "pipeline"
            else 300
        )
        runs = self._db.activity.list_connector_runs(connector_id=pack.manifest.id, limit=1)
        if not runs:
            return False
        latest = runs[0]
        if not latest.succeeded:
            return False
        cutoff = self._now() - timedelta(seconds=window_seconds)
        return latest.finished_at >= cutoff
