"""Connector runtime gates — in-process permission enforcement.

HS-13-02. Phase 11 manifests declare what a connector pack is
*allowed* to do (`shell:exec`, `network:outbound`,
`loopback:http`, `fs:read`). Until this story those declarations
were documentation; this module turns them into runtime checks.

`PermissionGate` wraps the privileged operations a pack might
invoke. Each operation consults the gate's underlying manifest
before delegating to the real implementation; a missing
permission raises `PermissionDenied` with the connector id, the
operation, the missing permission, and the manifest's declared
permission set so the operator can see exactly what the pack
asked for and what the gate refused.

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

    def run_subprocess(
        self,
        command: Iterable[str],
        *,
        runner: Optional[SubprocessRunner] = None,
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        """Invoke a local subprocess on behalf of the pack.

        Requires `shell:exec`. Tests pass `runner=fake` to inject a
        fake; production calls fall through to `subprocess.run`.
        Both run only if the gate admits the operation.
        """
        self._require("run_subprocess")
        actual = runner or subprocess.run
        return actual(list(command), **kwargs)

    def open_outbound_socket(
        self,
        address: tuple[str, int],
        *,
        opener: Optional[Callable[[tuple[str, int]], Any]] = None,
    ) -> Any:
        """Open a non-loopback socket on behalf of the pack.

        Requires `network:outbound`. The default opener is
        `socket.create_connection`, which is the lowest-level
        call we care to gate; HTTP libraries that ultimately
        bottom out on this socket are covered by the same gate
        when packs route through it. Tests inject `opener` to
        avoid real network use.
        """
        self._require("open_outbound_socket")
        actual = opener or socket.create_connection
        return actual(address)

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
    "SubprocessRunner",
]
