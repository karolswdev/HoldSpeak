"""Private custody for node pairing material (HS-131-16, design §1).

Three things must never become repository, database, argv, log, or kernel-row
content: the per-node bearer token, the hub's per-node Ed25519 offer PRIVATE key,
and the worker's pinned copy of the matching public key. This module owns how all
three are written and read.

Two rules from Sol's round-four rulings shape the I/O here:

* **Ruling 2 (custody).** A private document is refused BEFORE use unless one
  no-follow, metadata-checked read proves a regular, owner-held, securely
  permissioned file — and the inode actually opened matches the path inspected.
  A symlink swapped in between the check and the open therefore cannot be read.
* **Ruling 3 / Amendment 3 (coherence).** Writers take an exclusive cross-process
  lock and replace atomically, so a rotate or revoke on one process is visible to
  every other without a hub restart, and a torn document is never observable.
"""

from __future__ import annotations

import json
import os
import secrets
import stat
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

from ..mesh_authority import ed25519

#: Owner-only. Anything looser is refused rather than repaired.
PRIVATE_FILE_MODE = 0o600

#: Where a worker keeps what it pinned about its hub at pairing.
DEFAULT_HUB_PIN_PATH = Path.home() / ".holdspeak" / "mesh_hub_pin.json"

#: Schema of that pin document. v2 carries the node's own bearer token beside the
#: pinned public material, because the deliberate pairing transfer moves both.
HUB_PIN_SCHEMA = 2

#: Schema of the one document `node token export` writes and `node pair` reads.
PAIRING_TRANSFER_SCHEMA = 1

#: Exactly what a pairing transfer may contain. The hub's Ed25519 offer PRIVATE
#: key is not in this tuple and never will be: the whole asymmetry of the
#: protocol is that only the hub can sign an offer.
PAIRING_TRANSFER_FIELDS = (
    "mesh_pairing_transfer_schema",
    "node_name",
    "node_id",
    "generation",
    "key_id",
    "offer_public_key",
    "node_token",
)


class NodeCustodyError(ValueError):
    """Private custody refused. The message names no path and no secret."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class NodeCredentialSnapshot:
    """One authenticated pairing, read fresh under the store's lock.

    ``offer_private_key`` is present only on the HUB side and only for the
    transaction that is about to sign; it is never returned to a caller that is
    merely authenticating a request, and it never crosses a process boundary.
    """

    name: str
    node_id: str
    generation: int
    key_id: str
    offer_public_key: str
    token: str = ""
    offer_private_key: str = ""

    def public_view(self) -> "NodeCredentialSnapshot":
        """The same identity with every secret dropped."""
        return NodeCredentialSnapshot(
            name=self.name,
            node_id=self.node_id,
            generation=self.generation,
            key_id=self.key_id,
            offer_public_key=self.offer_public_key,
        )

    def __repr__(self) -> str:
        """The redacted rendering, and the ONLY one (repair R1).

        A snapshot travels as an ordinary argument into observed service methods,
        and generic observation serializes whatever it is handed. A dataclass's
        default ``repr`` would put the bearer token and the offer private key into
        an observer row, a log line, and a traceback. This one is the redaction
        seam: the identity stays legible, the secrets never render.
        """
        token = "<redacted>" if self.token else ""
        private = "<redacted>" if self.offer_private_key else ""
        return (
            "NodeCredentialSnapshot("
            f"name={self.name!r}, node_id={self.node_id!r}, "
            f"generation={self.generation!r}, key_id={self.key_id!r}, "
            f"token={token!r}, offer_private_key={private!r})"
        )


def mint_offer_keypair() -> tuple[str, str, str]:
    """A fresh per-node offer keypair: ``(key_id, private_hex, public_hex)``."""
    private = secrets.token_bytes(ed25519.PRIVATE_KEY_BYTES)
    return (
        "meshkey_" + uuid.uuid4().hex[:16],
        private.hex(),
        ed25519.public_key(private).hex(),
    )


# ── guarded private I/O ──────────────────────────────────────────────


def read_private_document(path: Path) -> Optional[dict[str, Any]]:
    """One metadata-checked, no-follow read, or a named refusal.

    Returns ``None`` when the document simply does not exist yet (an unpaired
    machine is not a custody failure). Every other disagreement — a symlink, a
    directory, a foreign owner, group/world permissions, or an inode that changed
    under us — refuses rather than reads.
    """
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        inspected = os.lstat(path)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise NodeCustodyError("node_custody_unreadable") from exc
    if not stat.S_ISREG(inspected.st_mode):
        raise NodeCustodyError("node_custody_not_regular_file")
    try:
        handle = os.open(path, flags)
    except OSError as exc:
        raise NodeCustodyError("node_custody_unreadable") from exc
    try:
        opened = os.fstat(handle)
        if (opened.st_ino, opened.st_dev) != (inspected.st_ino, inspected.st_dev):
            raise NodeCustodyError("node_custody_inode_changed")
        if not stat.S_ISREG(opened.st_mode):
            raise NodeCustodyError("node_custody_not_regular_file")
        if opened.st_uid != os.geteuid():
            raise NodeCustodyError("node_custody_foreign_owner")
        if opened.st_mode & 0o077:
            raise NodeCustodyError("node_custody_permissive_mode")
        raw = os.read(handle, 4 * 1024 * 1024).decode("utf-8")
    finally:
        os.close(handle)
    try:
        document = json.loads(raw) if raw.strip() else None
    except ValueError as exc:
        raise NodeCustodyError("node_custody_malformed") from exc
    if document is None:
        return None
    if not isinstance(document, dict):
        # Repair R2.6: a document that parsed but is not an object is MALFORMED,
        # not absent. Returning `None` here made a custody file that is a list
        # (or a bare string) indistinguishable from a machine that never paired,
        # and the next write then replaced it.
        raise NodeCustodyError("node_custody_malformed")
    return document


@contextmanager
def exclusive_custody_lock(path: Path) -> Iterator[None]:
    """An exclusive cross-process lock around one custody document.

    The lock is a sibling file, so taking it never truncates or races the document
    being replaced. On a platform without ``fcntl`` the write still happens; the
    atomic replace below keeps readers whole either way.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + ".lock")
    handle = os.open(lock_path, os.O_RDWR | os.O_CREAT, PRIVATE_FILE_MODE)
    try:
        try:
            import fcntl

            fcntl.flock(handle, fcntl.LOCK_EX)
        except (ImportError, OSError):  # pragma: no cover - platform fallback
            pass
        yield
    finally:
        os.close(handle)


def write_private_document(path: Path, document: dict[str, Any]) -> None:
    """Replace a custody document atomically, owner-only, never in place."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex[:8]}")
    handle = os.open(
        temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, PRIVATE_FILE_MODE
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(document, indent=2, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, PRIVATE_FILE_MODE)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:  # pragma: no cover - best effort cleanup
            pass
        raise


# ── the worker's pin ─────────────────────────────────────────────────


@dataclass(frozen=True)
class MeshHubPin:
    """What a worker pinned about its hub, and the credential it answers with.

    Public key material plus this node's OWN bearer token. The hub's offer
    private key is not here and cannot be: a worker verifies signatures, it never
    makes them.
    """

    node_name: str
    node_id: str
    generation: int
    key_id: str
    offer_public_key: str
    node_token: str = ""

    @property
    def public_key_bytes(self) -> bytes:
        try:
            return bytes.fromhex(self.offer_public_key)
        except ValueError as exc:
            raise NodeCustodyError("node_custody_malformed") from exc

    def __repr__(self) -> str:
        """Redacted, for the same reason a credential snapshot is (repair R1)."""
        token = "<redacted>" if self.node_token else ""
        return (
            "MeshHubPin("
            f"node_name={self.node_name!r}, node_id={self.node_id!r}, "
            f"generation={self.generation!r}, key_id={self.key_id!r}, "
            f"node_token={token!r})"
        )


def save_hub_pin(pin: MeshHubPin, *, path: Optional[Path] = None) -> None:
    """Persist one pairing's pin under private custody."""
    target = Path(path) if path else DEFAULT_HUB_PIN_PATH
    with exclusive_custody_lock(target):
        write_private_document(
            target,
            {
                "mesh_hub_pin_schema": HUB_PIN_SCHEMA,
                "node_name": pin.node_name,
                "node_id": pin.node_id,
                "generation": int(pin.generation),
                "key_id": pin.key_id,
                "offer_public_key": pin.offer_public_key,
                "node_token": pin.node_token,
            },
        )


def load_hub_pin(*, path: Optional[Path] = None) -> Optional[MeshHubPin]:
    """Read the pin, or ``None`` when this machine was never paired."""
    target = Path(path) if path else DEFAULT_HUB_PIN_PATH
    document = read_private_document(target)
    if document is None:
        return None
    if document.get("mesh_hub_pin_schema") != HUB_PIN_SCHEMA:
        raise NodeCustodyError("node_custody_malformed")
    generation = document.get("generation")
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
        raise NodeCustodyError("node_custody_malformed")
    for field in ("node_name", "node_id", "key_id", "offer_public_key"):
        if not isinstance(document.get(field), str) or not document[field].strip():
            raise NodeCustodyError("node_custody_malformed")
    token = document.get("node_token", "")
    if not isinstance(token, str):
        raise NodeCustodyError("node_custody_malformed")
    return MeshHubPin(
        node_name=str(document["node_name"]),
        node_id=str(document["node_id"]),
        generation=generation,
        key_id=str(document["key_id"]),
        offer_public_key=str(document["offer_public_key"]),
        node_token=token,
    )


# ── the deliberate pairing transfer (design §1.1, repair R2) ─────────


def build_pairing_transfer(
    snapshot: NodeCredentialSnapshot, token: str
) -> dict[str, Any]:
    """The ONE document that moves a pairing from the hub to its worker.

    It carries the bearer token, the stable node id, the credential generation,
    the key id, and the offer PUBLIC key — everything a worker needs to
    authenticate itself and to verify a hub signature, and nothing that would let
    it produce one. The private half is refused structurally below rather than
    merely omitted here.
    """
    document = {
        "mesh_pairing_transfer_schema": PAIRING_TRANSFER_SCHEMA,
        "node_name": snapshot.name,
        "node_id": snapshot.node_id,
        "generation": int(snapshot.generation),
        "key_id": snapshot.key_id,
        "offer_public_key": snapshot.offer_public_key,
        "node_token": str(token),
    }
    if set(document) != set(PAIRING_TRANSFER_FIELDS):  # pragma: no cover - guard
        raise NodeCustodyError("node_custody_malformed")
    return document


def write_pairing_transfer(
    path: Path, snapshot: NodeCredentialSnapshot, token: str
) -> None:
    """Export one pairing to owner-only custody on the hub machine."""
    write_private_document(Path(path), build_pairing_transfer(snapshot, token))


def read_pairing_transfer(path: Path) -> MeshHubPin:
    """Import one exported pairing into this worker's own custody.

    The document is read through the same no-follow, owner-only, permission- and
    inode-checked path every private custody read uses, and its field set is
    exact: an extra field — most of all a private key someone tried to smuggle
    in — refuses instead of being ignored.
    """
    document = read_private_document(Path(path))
    if document is None:
        raise NodeCustodyError("node_custody_absent")
    if set(document) != set(PAIRING_TRANSFER_FIELDS):
        raise NodeCustodyError("node_custody_malformed")
    if document.get("mesh_pairing_transfer_schema") != PAIRING_TRANSFER_SCHEMA:
        raise NodeCustodyError("node_custody_malformed")
    generation = document.get("generation")
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
        raise NodeCustodyError("node_custody_malformed")
    for field in ("node_name", "node_id", "key_id", "offer_public_key", "node_token"):
        if not isinstance(document.get(field), str) or not document[field].strip():
            raise NodeCustodyError("node_custody_malformed")
    pin = MeshHubPin(
        node_name=str(document["node_name"]),
        node_id=str(document["node_id"]),
        generation=generation,
        key_id=str(document["key_id"]),
        offer_public_key=str(document["offer_public_key"]),
        node_token=str(document["node_token"]),
    )
    pin.public_key_bytes  # a pin whose key is unreadable is refused at import
    return pin


__all__ = [
    "DEFAULT_HUB_PIN_PATH",
    "HUB_PIN_SCHEMA",
    "MeshHubPin",
    "NodeCredentialSnapshot",
    "NodeCustodyError",
    "PAIRING_TRANSFER_FIELDS",
    "PAIRING_TRANSFER_SCHEMA",
    "PRIVATE_FILE_MODE",
    "build_pairing_transfer",
    "exclusive_custody_lock",
    "load_hub_pin",
    "mint_offer_keypair",
    "read_pairing_transfer",
    "read_private_document",
    "save_hub_pin",
    "write_pairing_transfer",
    "write_private_document",
]
