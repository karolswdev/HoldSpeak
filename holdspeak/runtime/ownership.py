"""HS-200-02: DatabaseOwnershipMixin -- who owns this database, and the sweeps.

One process owns the database for the life of its run (C1, C10): it holds a
flock beside the file, records the port it serves on so a refused sibling can
name it, and is the only process that starts the scheduled sweeps. A second
hub on the same database refuses to start, or -- with the escape hatch --
starts with the sweeps off and a TWO RUNTIMES repair state on the Desk.

Carved out of ``web_runtime.py`` by HS-200 (the backend density guard: the
runtime core is boot/run/config only). Bodies are verbatim moves; ``self`` is
the runtime.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

from ..logging_config import get_logger

log = get_logger("runtime.ownership")


class DatabaseOwnershipMixin:
    """The database owner claim, the port note, and the ownership-gated sweeps."""

    def _capture_identity_and_claim(self) -> None:
        """Freeze this process's identity, then take the database (HS-200-02).

        Identity is captured BEFORE anything serves it, so a later checkout
        cannot change what an already running hub reports.
        """
        from ..runtime_identity import capture_runtime_identity

        capture_runtime_identity(started_at=self.runtime_started_at)
        self._claim_database()

    def _claim_database(self) -> None:
        """Take the database owner lock, or refuse to be a second hub (HS-200-02).

        C1 forbids two processes silently owning the same scheduled work; C10
        forbids introducing a multi-writer SQLite arrangement at all. So the
        second hub refuses to start. ``HOLDSPEAK_ALLOW_UNOWNED_DB=1`` starts
        anyway with the sweeps OFF and a TWO RUNTIMES repair state on the Desk.
        """
        from ..db import core as db_core
        from ..runtime_lock import allow_unowned, claim_database, refusal_message

        db_path = Path(db_core.DEFAULT_DB_PATH).expanduser()
        started = self.runtime_started_at.isoformat()
        lock = claim_database(db_path, process_start=started)
        self.owns_database = lock.held
        if lock.held:
            return
        message = refusal_message(db_path, lock.owner())
        if allow_unowned():
            log.warning(f"Starting without database ownership.\n{message}")
            print(message, file=sys.stderr)
            print("HOLDSPEAK_ALLOW_UNOWNED_DB is set: starting with scheduled work OFF.", file=sys.stderr)
            return
        print(message, file=sys.stderr)
        log.error("Refusing to start: another hub owns this database.")
        raise SystemExit(1)

    def _note_serving_port(self) -> None:
        """Record the served port on the owner claim (HS-200-02).

        The port only exists after ``server.start()``. A refused sibling reads
        this to name the hub already serving. It is a note, never a gate: a
        failure here must not touch the boot.
        """
        if not self.owns_database:
            return
        try:
            from ..runtime_lock import current_lock

            lock = current_lock()
            if lock is None:
                return
            lock.acquire(
                port=getattr(self.server, "port", None),
                host=getattr(self.server, "host", None),
                process_start=self.runtime_started_at.isoformat(),
            )
        except Exception as exc:  # pragma: no cover - the claim already stands
            log.debug(f"Could not record the serving port on the owner claim: {exc}")

    def _release_database(self) -> None:
        """Hand the database back on an ordinary stop (HS-200-02).

        flock releases on exit anyway; this makes the ordinary stop leave no
        claim behind at all. Shutdown is best effort: never raise from here.
        """
        try:
            from ..runtime_lock import release_database

            release_database()
        except Exception as exc:  # pragma: no cover - shutdown is best effort
            log.debug(f"Database owner lock release failed: {exc}")

    def _start_scheduled_work(self) -> None:
        """Start the sweeps -- in the database's owner process only (HS-200-02).

        The Cadence Engine tick is OFF BY DEFAULT (CAD-1-04) and starts only
        when the user has opted in; the heartbeat is always-on (HS-171-02).
        Both are now gated on ownership: C1 forbids two processes silently
        owning the same scheduled work, so a hub that lost the claim runs
        neither, and says so.
        """
        if not self.owns_database:
            log.warning("Scheduled work is OFF: this hub does not own the database.")
            return
        if self._cadence_enabled():
            self.cadence_thread = threading.Thread(
                target=self._cadence_loop,
                name="HoldSpeakCadenceEngine",
                daemon=True,
            )
            self.cadence_thread.start()
        self._start_heartbeat_thread()  # HS-171-02
