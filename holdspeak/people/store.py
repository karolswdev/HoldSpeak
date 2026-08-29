"""Private-permission, AES-GCM encrypted SQLite sidecar for People PR1."""

from __future__ import annotations

import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from .crypto import Envelope, PeopleCryptoError, decrypt_payload, encrypt_payload
from .keys import KeyStore, PeopleKeyError, new_key, new_key_id


DEFAULT_PEOPLE_DB_PATH = Path.home() / ".local" / "share" / "holdspeak" / "people.v1.sqlite3"


class PeopleReadiness(StrEnum):
    READY = "ready"
    UNCONFIGURED = "unconfigured"
    KEY_UNAVAILABLE = "key_unavailable"
    LOCKED = "locked"
    UNAVAILABLE = "unavailable"
    CORRUPT = "corrupt"
    UNSAFE_PERMISSIONS = "unsafe_permissions"


class PeopleStoreError(RuntimeError):
    """Content-free store failure with a stable readiness state."""

    def __init__(self, readiness: PeopleReadiness) -> None:
        self.readiness = readiness
        super().__init__(f"people_store_{readiness.value}")


@dataclass(frozen=True)
class PeopleRecord:
    id: str
    kind: str
    lifecycle: str
    created_at: str
    updated_at: str
    payload: Any


class EncryptedPeopleStore:
    """The only persistence authority for People confidential payloads."""

    def __init__(self, path: Path, key_store: KeyStore) -> None:
        self.path = path
        self.key_store = key_store

    @property
    def directory(self) -> Path:
        return self.path.parent

    def initialize(self) -> PeopleReadiness:
        """Deliberately create a new store and native-held key once."""
        if self.path.exists():
            return self.readiness()
        self._ensure_private_directory()
        key_id, key = new_key_id(), new_key()
        created_here = False
        try:
            self.key_store.put(key_id, key)
            with self._connect(create=True) as conn:
                created_here = True
                self._schema(conn)
                conn.execute("INSERT INTO meta(key, value) VALUES('key_id', ?)", (key_id,))
                conn.execute("INSERT INTO meta(key, value) VALUES('format_version', '1')")
            self._ensure_private_files()
        except (OSError, sqlite3.Error, PeopleKeyError):
            # Key deletion is safe only if setup failed before a usable sidecar.
            try:
                self.key_store.delete(key_id)
            except PeopleKeyError:
                pass
            if created_here:
                for candidate in (self.path, self.path.with_name(self.path.name + "-wal"), self.path.with_name(self.path.name + "-shm")):
                    try:
                        candidate.unlink(missing_ok=True)
                    except OSError:
                        pass
            raise PeopleStoreError(PeopleReadiness.UNAVAILABLE)
        return PeopleReadiness.READY

    def readiness(self) -> PeopleReadiness:
        if not self.path.exists():
            return PeopleReadiness.UNCONFIGURED
        try:
            self._require_private_files()
            with self._connect() as conn:
                self._schema(conn)
                key_id = self._key_id(conn)
                key = self.key_store.get(key_id)
                row = conn.execute("SELECT id, kind, key_id, nonce, ciphertext, format_version FROM records LIMIT 1").fetchone()
                if row is not None:
                    decrypt_payload(key=key, record_id=row[0], kind=row[1], envelope=Envelope(row[2], row[3], row[4], row[5]))
                if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    return PeopleReadiness.CORRUPT
            return PeopleReadiness.READY
        except PeopleStoreError as exc:
            return exc.readiness
        except PeopleKeyError as exc:
            # A sidecar with no usable native key is never an empty new ledger.
            return PeopleReadiness.KEY_UNAVAILABLE if str(exc) == "people_key_missing" else PeopleReadiness.LOCKED
        except PeopleCryptoError:
            # AES-GCM cannot distinguish a substituted key from tampering.  Do
            # not report a data-integrity conclusion before key custody is fixed.
            return PeopleReadiness.KEY_UNAVAILABLE
        except (OSError, sqlite3.Error):
            return PeopleReadiness.UNAVAILABLE

    def put(self, *, record_id: str, kind: str, lifecycle: str, payload: Any, timestamp: str) -> None:
        """Encrypt before SQLite sees the caller-provided payload."""
        with self._ready_connection() as (conn, key_id, key):
            envelope = encrypt_payload(key=key, key_id=key_id, record_id=record_id, kind=kind, payload=payload)
            conn.execute(
                """INSERT INTO records(id,kind,lifecycle,created_at,updated_at,key_id,nonce,ciphertext,format_version)
                VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET lifecycle=excluded.lifecycle, updated_at=excluded.updated_at,
                key_id=excluded.key_id, nonce=excluded.nonce, ciphertext=excluded.ciphertext,
                format_version=excluded.format_version""",
                (record_id, kind, lifecycle, timestamp, timestamp, envelope.key_id, envelope.nonce, envelope.ciphertext, envelope.format_version),
            )
        self._ensure_private_files()

    def _get_record(self, record_id: str) -> PeopleRecord | None:
        with self._ready_connection() as (conn, _key_id, key):
            row = conn.execute("SELECT id,kind,lifecycle,created_at,updated_at,key_id,nonce,ciphertext,format_version FROM records WHERE id=?", (record_id,)).fetchone()
            if row is None:
                return None
            try:
                payload = decrypt_payload(key=key, record_id=row[0], kind=row[1], envelope=Envelope(row[5], row[6], row[7], row[8]))
            except PeopleCryptoError as exc:
                raise PeopleStoreError(PeopleReadiness.CORRUPT) from exc
            return PeopleRecord(row[0], row[1], row[2], row[3], row[4], payload)

    # Small domain-facing protocol used by the People service.  All filtering
    # happens after decrypting in process; no payload field becomes a SQLite index.
    def create(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        record_id = str(uuid.uuid4())
        value = dict(payload)
        # The storage authority owns its opaque ids; accepting a caller id would
        # permit an encrypted body to lie about the row returned by a read.
        value.pop("id", None)
        timestamp = str(value.get("updated_at") or value.get("created_at") or _now())
        lifecycle = str(value.get("lifecycle") or "active")
        self.put(record_id=record_id, kind=kind, lifecycle=lifecycle, payload=value, timestamp=timestamp)
        return self._record_dict(self._get_record(record_id))

    def get(self, record_id: str, kind: str | None = None) -> dict[str, Any] | None:
        record = self._get_record(record_id)
        if record is None or (kind is not None and record.kind != kind):
            return None
        return self._record_dict(record)

    def list(
        self,
        kind: str | None = None,
        relationship_id: str | None = None,
        active_only: bool = False,
    ) -> list[dict[str, Any]]:
        with self._ready_connection() as (conn, _key_id, key):
            clauses, values = [], []
            if kind is not None:
                clauses.append("kind=?")
                values.append(kind)
            query = "SELECT id,kind,lifecycle,created_at,updated_at,key_id,nonce,ciphertext,format_version FROM records"
            if clauses:
                query += " WHERE " + " AND ".join(clauses)
            rows = conn.execute(query, values).fetchall()
            results: list[dict[str, Any]] = []
            for row in rows:
                try:
                    payload = decrypt_payload(key=key, record_id=row[0], kind=row[1], envelope=Envelope(row[5], row[6], row[7], row[8]))
                except PeopleCryptoError as exc:
                    raise PeopleStoreError(PeopleReadiness.CORRUPT) from exc
                if relationship_id is not None and payload.get("relationship_id") != relationship_id:
                    continue
                if active_only and row[2] == "archived":
                    continue
                results.append(self._record_dict(PeopleRecord(row[0], row[1], row[2], row[3], row[4], payload)))
            return results

    def replace(self, record_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        existing = self._get_record(record_id)
        if existing is None:
            raise KeyError("people_record_missing")
        value = dict(payload)
        value.pop("id", None)
        lifecycle = str(value.get("lifecycle") or existing.lifecycle)
        self.put(record_id=record_id, kind=existing.kind, lifecycle=lifecycle, payload=value, timestamp=_now())
        return self._record_dict(self._get_record(record_id))

    def archive(self, record_id: str) -> dict[str, Any]:
        return self.transition(record_id, "archived")

    def transition(self, record_id: str, to_state: str) -> dict[str, Any]:
        existing = self._get_record(record_id)
        if existing is None:
            raise KeyError("people_record_missing")
        payload = dict(existing.payload)
        payload["state"] = to_state
        payload["lifecycle"] = to_state
        self.put(record_id=record_id, kind=existing.kind, lifecycle=to_state, payload=payload, timestamp=_now())
        return self._record_dict(self._get_record(record_id))

    def open_commitments(self) -> list[dict[str, Any]]:
        return [
            record for record in self.list(kind="commitment")
            if record["lifecycle"] == "open"
        ]

    def accept_request(
        self,
        request_id: str,
        commitment_payload: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Accept one request and mint exactly one encrypted commitment atomically.

        The accepted request stores the random commitment id inside its encrypted
        payload.  A retry observes that id rather than creating another promise.
        """
        with self._ready_connection() as (conn, key_id, key):
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT id,kind,lifecycle,created_at,updated_at,key_id,nonce,ciphertext,format_version FROM records WHERE id=?",
                (request_id,),
            ).fetchone()
            if row is None:
                raise KeyError("people_record_missing")
            if row[1] != "request":
                raise ValueError("people_request_kind_required")
            try:
                request_payload = decrypt_payload(key=key, record_id=row[0], kind=row[1], envelope=Envelope(row[5], row[6], row[7], row[8]))
            except PeopleCryptoError as exc:
                raise PeopleStoreError(PeopleReadiness.CORRUPT) from exc
            existing_id = request_payload.get("accepted_commitment_id") if isinstance(request_payload, dict) else None
            if row[2] == "accepted" and isinstance(existing_id, str):
                existing = self._record_from_row(conn.execute(
                    "SELECT id,kind,lifecycle,created_at,updated_at,key_id,nonce,ciphertext,format_version FROM records WHERE id=?",
                    (existing_id,),
                ).fetchone(), key)
                if existing is None or existing.kind != "commitment":
                    raise PeopleStoreError(PeopleReadiness.CORRUPT)
                return self._record_dict(self._record_from_values(row, request_payload)), self._record_dict(existing)
            if row[2] not in {"active", "open", "requested"} or not isinstance(request_payload, dict):
                raise ValueError("people_request_not_acceptable")
            relationship_id = str(request_payload.get("relationship_id") or "")
            relationship = self._record_from_row(conn.execute(
                "SELECT id,kind,lifecycle,created_at,updated_at,key_id,nonce,ciphertext,format_version FROM records WHERE id=?",
                (relationship_id,),
            ).fetchone(), key)
            if (
                relationship is None
                or relationship.kind != "relationship"
                or relationship.lifecycle != "active"
                or not isinstance(relationship.payload, dict)
                or str(relationship.payload.get("state") or "") != "active"
            ):
                raise ValueError("people_relationship_inactive")
            commitment_id, timestamp = str(uuid.uuid4()), _now()
            accepted_payload = dict(request_payload)
            accepted_payload["accepted_commitment_id"] = commitment_id
            accepted_payload["state"] = "accepted"
            accepted_payload["lifecycle"] = "accepted"
            commitment_value = dict(commitment_payload)
            commitment_value.pop("id", None)
            commitment_value["request_id"] = request_id
            commitment_value["lifecycle"] = "open"
            self._write_encrypted(conn, record_id=request_id, kind="request", lifecycle="accepted", created_at=row[3], timestamp=timestamp, key=key, key_id=key_id, payload=accepted_payload)
            self._write_encrypted(conn, record_id=commitment_id, kind="commitment", lifecycle="open", created_at=timestamp, timestamp=timestamp, key=key, key_id=key_id, payload=commitment_value)
            request = PeopleRecord(request_id, "request", "accepted", row[3], timestamp, accepted_payload)
            commitment = PeopleRecord(commitment_id, "commitment", "open", timestamp, timestamp, commitment_value)
            return self._record_dict(request), self._record_dict(commitment)

    def roll_agenda_item(
        self,
        source_id: str,
        successor_payload: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Roll one open agenda item exactly once and mint its successor.

        Both encrypted writes share one immediate transaction.  The source may
        only link to a successor in the same relationship and 1:1 session, which
        prevents an opaque id from becoming an arbitrary cross-relationship link.
        """
        with self._ready_connection() as (conn, key_id, key):
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT id,kind,lifecycle,created_at,updated_at,key_id,nonce,ciphertext,format_version FROM records WHERE id=?",
                (source_id,),
            ).fetchone()
            source = self._record_from_row(row, key)
            if source is None:
                raise KeyError("people_record_missing")
            if source.kind != "agenda_item" or source.lifecycle != "active" or not isinstance(source.payload, dict):
                raise ValueError("people_agenda_item_not_rollable")
            if str(source.payload.get("state") or "open") != "open":
                raise ValueError("people_agenda_item_not_rollable")
            value = dict(successor_payload)
            value.pop("id", None)
            if (
                value.get("relationship_id") != source.payload.get("relationship_id")
                or value.get("session_id") != source.payload.get("session_id")
            ):
                raise ValueError("people_agenda_roll_scope_invalid")
            successor_id, timestamp = str(uuid.uuid4()), _now()
            source_value = dict(source.payload)
            source_value.update({"state": "rolled", "lifecycle": "rolled", "rolled_to_id": successor_id})
            value.update({"rolled_from_id": source_id, "state": "open", "lifecycle": "active"})
            self._write_encrypted(
                conn, record_id=source.id, kind="agenda_item", lifecycle="rolled",
                created_at=source.created_at, timestamp=timestamp, key=key, key_id=key_id,
                payload=source_value,
            )
            self._write_encrypted(
                conn, record_id=successor_id, kind="agenda_item", lifecycle="active",
                created_at=timestamp, timestamp=timestamp, key=key, key_id=key_id, payload=value,
            )
            rolled = PeopleRecord(source.id, "agenda_item", "rolled", source.created_at, timestamp, source_value)
            successor = PeopleRecord(successor_id, "agenda_item", "active", timestamp, timestamp, value)
            return self._record_dict(rolled), self._record_dict(successor)

    @staticmethod
    def _record_dict(record: PeopleRecord | None) -> dict[str, Any]:
        if record is None:
            raise KeyError("people_record_missing")
        if not isinstance(record.payload, dict):
            raise PeopleStoreError(PeopleReadiness.CORRUPT)
        return {
            **record.payload,
            "id": record.id,
            "kind": record.kind,
            "lifecycle": record.lifecycle,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    @staticmethod
    def _record_from_values(row: Any, payload: Any) -> PeopleRecord:
        return PeopleRecord(row[0], row[1], row[2], row[3], row[4], payload)

    def _record_from_row(self, row: Any, key: bytes) -> PeopleRecord | None:
        if row is None:
            return None
        try:
            payload = decrypt_payload(key=key, record_id=row[0], kind=row[1], envelope=Envelope(row[5], row[6], row[7], row[8]))
        except PeopleCryptoError as exc:
            raise PeopleStoreError(PeopleReadiness.CORRUPT) from exc
        return self._record_from_values(row, payload)

    @staticmethod
    def _write_encrypted(
        conn: sqlite3.Connection,
        *,
        record_id: str,
        kind: str,
        lifecycle: str,
        created_at: str,
        timestamp: str,
        key: bytes,
        key_id: str,
        payload: Any,
    ) -> None:
        envelope = encrypt_payload(key=key, key_id=key_id, record_id=record_id, kind=kind, payload=payload)
        conn.execute(
            """INSERT INTO records(id,kind,lifecycle,created_at,updated_at,key_id,nonce,ciphertext,format_version)
            VALUES(?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET lifecycle=excluded.lifecycle, updated_at=excluded.updated_at,
            key_id=excluded.key_id, nonce=excluded.nonce, ciphertext=excluded.ciphertext,
            format_version=excluded.format_version""",
            (record_id, kind, lifecycle, created_at, timestamp, envelope.key_id, envelope.nonce, envelope.ciphertext, envelope.format_version),
        )

    @contextmanager
    def _ready_connection(self):
        readiness = self.readiness()
        if readiness is not PeopleReadiness.READY:
            raise PeopleStoreError(readiness)
        conn = self._connect()
        try:
            key_id = self._key_id(conn)
            yield conn, key_id, self.key_store.get(key_id)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _connect(self, *, create: bool = False) -> sqlite3.Connection:
        if not create and not self.path.exists():
            raise PeopleStoreError(PeopleReadiness.UNCONFIGURED)
        # SQLite creates DB/WAL/SHM files during connect and first write.  The
        # process-wide umask is serialized so they are private from birth; the
        # containing directory is private independently.
        with _UMASK_LOCK:
            prior_umask = os.umask(0o077)
            try:
                conn = sqlite3.connect(str(self.path))
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA foreign_keys=ON")
            finally:
                os.umask(prior_umask)
        return conn

    @staticmethod
    def _schema(conn: sqlite3.Connection) -> None:
        conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY, kind TEXT NOT NULL, lifecycle TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL, key_id TEXT NOT NULL,
            nonce BLOB NOT NULL, ciphertext BLOB NOT NULL, format_version INTEGER NOT NULL)"""
        )

    @staticmethod
    def _key_id(conn: sqlite3.Connection) -> str:
        row = conn.execute("SELECT value FROM meta WHERE key='key_id'").fetchone()
        if row is None or not row[0]:
            raise PeopleStoreError(PeopleReadiness.CORRUPT)
        return str(row[0])

    def _ensure_private_directory(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        os.chmod(self.directory, 0o700)
        self._require_private_path(self.directory)

    def _ensure_private_files(self) -> None:
        for candidate in (self.path, self.path.with_name(self.path.name + "-wal"), self.path.with_name(self.path.name + "-shm")):
            if candidate.exists():
                os.chmod(candidate, 0o600)
                self._require_private_path(candidate)

    def _require_private_files(self) -> None:
        self._require_private_path(self.directory)
        self._require_private_path(self.path)
        for suffix in ("-wal", "-shm"):
            candidate = self.path.with_name(self.path.name + suffix)
            if candidate.exists():
                self._require_private_path(candidate)

    @staticmethod
    def _require_private_path(path: Path) -> None:
        if path.stat().st_mode & 0o077:
            raise PeopleStoreError(PeopleReadiness.UNSAFE_PERMISSIONS)


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


_UMASK_LOCK = threading.Lock()


def _dev_sidecar_path(keyfile: Path) -> Path:
    """F4: derive the dev sidecar path from the keyfile world.

    The dev world uses ``<keyfile-stem>.sidecar.sqlite3`` adjacent to the
    key file.  This is NEVER ``DEFAULT_PEOPLE_DB_PATH`` -- the dev store
    cannot open or create the production sidecar.
    """
    return keyfile.parent / f"{keyfile.stem}.sidecar.sqlite3"


def production_people_store() -> EncryptedPeopleStore:
    """Build the sole production People authority; never substitutes a fallback.

    When ``HOLDSPEAK_PEOPLE_KEYSTORE_FILE`` is set, the store uses a
    :class:`FileKeyStore` at that path AND an ISOLATED sidecar derived from
    the key file (F4, HS-149-01).  Unset means byte-identical production
    behaviour through :class:`NativeKeyStore`.
    """
    env = os.environ.get("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", "").strip()
    if env:
        from .keys import FileKeyStore
        keyfile = Path(env)
        return EncryptedPeopleStore(_dev_sidecar_path(keyfile), FileKeyStore(keyfile))
    from .keys import NativeKeyStore
    return EncryptedPeopleStore(DEFAULT_PEOPLE_DB_PATH, NativeKeyStore())
