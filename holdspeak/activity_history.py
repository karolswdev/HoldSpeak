"""Local browser history readers for HoldSpeak activity intelligence."""

from __future__ import annotations

import hashlib
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urlsplit

from .db import MeetingDatabase, get_database
from .logging_config import get_logger

log = get_logger("activity_history")

SAFARI_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)
SQLITE_COMPANION_SUFFIXES = ("-wal", "-shm")


@dataclass(frozen=True)
class BrowserHistorySource:
    """One readable local browser history source."""

    source_browser: str
    source_profile: str
    path: Path
    enabled: bool = True

    @property
    def source_path_hash(self) -> str:
        return _hash_source_path(self.path)


@dataclass(frozen=True)
class BrowserHistoryImportResult:
    """Import result for one browser history source."""

    source_browser: str
    source_profile: str
    source_path_hash: str
    imported_count: int
    checkpoint_raw: Optional[str]
    enabled: bool
    error: Optional[str] = None


def discover_browser_history_sources(home: Optional[Path] = None) -> list[BrowserHistorySource]:
    """Discover default-enabled local Safari and Firefox history sources."""
    root = Path(home).expanduser() if home is not None else Path.home()
    sources: list[BrowserHistorySource] = []

    safari_history = root / "Library" / "Safari" / "History.db"
    if safari_history.is_file():
        sources.append(
            BrowserHistorySource(
                source_browser="safari",
                source_profile="default",
                path=safari_history,
                enabled=True,
            )
        )

    firefox_roots = [
        root / "Library" / "Application Support" / "Firefox" / "Profiles",
        root / ".mozilla" / "firefox",
    ]
    seen_firefox_paths: set[Path] = set()
    for profiles_root in firefox_roots:
        if not profiles_root.is_dir():
            continue
        for places_db in sorted(profiles_root.glob("*/places.sqlite")):
            resolved = places_db.resolve()
            if resolved in seen_firefox_paths:
                continue
            seen_firefox_paths.add(resolved)
            sources.append(
                BrowserHistorySource(
                    source_browser="firefox",
                    source_profile=places_db.parent.name,
                    path=places_db,
                    enabled=True,
                )
            )

    return sources


def import_browser_history(
    *,
    db: Optional[MeetingDatabase] = None,
    home: Optional[Path] = None,
    sources: Optional[Iterable[BrowserHistorySource]] = None,
) -> list[BrowserHistoryImportResult]:
    """Import all discovered readable browser history sources into the ledger."""
    database = db or get_database()
    active_sources = list(sources) if sources is not None else discover_browser_history_sources(home)
    results: list[BrowserHistoryImportResult] = []
    for source in active_sources:
        if not source.enabled:
            results.append(
                BrowserHistoryImportResult(
                    source_browser=source.source_browser,
                    source_profile=source.source_profile,
                    source_path_hash=source.source_path_hash,
                    imported_count=0,
                    checkpoint_raw=None,
                    enabled=False,
                )
            )
            continue
        if source.source_browser == "safari":
            results.append(import_safari_history(source, db=database))
        elif source.source_browser == "firefox":
            results.append(import_firefox_history(source, db=database))
        else:
            results.append(
                BrowserHistoryImportResult(
                    source_browser=source.source_browser,
                    source_profile=source.source_profile,
                    source_path_hash=source.source_path_hash,
                    imported_count=0,
                    checkpoint_raw=None,
                    enabled=source.enabled,
                    error=f"Unsupported browser history source: {source.source_browser}",
                )
            )
    return results


def import_safari_history(
    source: BrowserHistorySource,
    *,
    db: Optional[MeetingDatabase] = None,
) -> BrowserHistoryImportResult:
    """Import Safari History.db metadata into the activity ledger."""
    database = db or get_database()
    return _import_history_source(
        source=source,
        db=database,
        reader=_read_safari_rows,
        timestamp_converter=_safari_timestamp_to_datetime,
    )


def import_firefox_history(
    source: BrowserHistorySource,
    *,
    db: Optional[MeetingDatabase] = None,
) -> BrowserHistoryImportResult:
    """Import Firefox places.sqlite metadata into the activity ledger."""
    database = db or get_database()
    return _import_history_source(
        source=source,
        db=database,
        reader=_read_firefox_rows,
        timestamp_converter=_firefox_timestamp_to_datetime,
    )


def _import_history_source(
    *,
    source: BrowserHistorySource,
    db: MeetingDatabase,
    reader,
    timestamp_converter,
) -> BrowserHistoryImportResult:
    source_hash = source.source_path_hash
    checkpoint = db.get_activity_import_checkpoint(
        source_browser=source.source_browser,
        source_profile=source.source_profile,
        source_path_hash=source_hash,
    )
    since_raw = checkpoint.last_visit_raw if checkpoint else None
    imported = 0
    max_raw = since_raw

    try:
        with tempfile.TemporaryDirectory(prefix="holdspeak-history-") as tmp:
            snapshot_path = _copy_sqlite_snapshot(source.path, Path(tmp))
            rows = reader(snapshot_path, since_raw=since_raw)
            for row in rows:
                if not _is_importable_url(row["url"]):
                    continue
                first_seen = timestamp_converter(row["first_visit_raw"])
                last_seen = timestamp_converter(row["last_visit_raw"])
                db.upsert_activity_record(
                    source_browser=source.source_browser,
                    source_profile=source.source_profile,
                    source_path_hash=source_hash,
                    url=row["url"],
                    title=row["title"],
                    domain=_domain_from_url(row["url"]),
                    visit_count=row["visit_count"],
                    first_seen_at=first_seen,
                    last_seen_at=last_seen,
                    last_visit_raw=row["last_visit_raw"],
                )
                imported += 1
                max_raw = _max_raw_timestamp(max_raw, row["last_visit_raw"])

        db.set_activity_import_checkpoint(
            source_browser=source.source_browser,
            source_profile=source.source_profile,
            source_path_hash=source_hash,
            last_visit_raw=max_raw,
            enabled=True,
        )
        return BrowserHistoryImportResult(
            source_browser=source.source_browser,
            source_profile=source.source_profile,
            source_path_hash=source_hash,
            imported_count=imported,
            checkpoint_raw=max_raw,
            enabled=True,
        )
    except Exception as exc:
        log.warning("Failed to import %s history: %s", source.source_browser, exc)
        db.set_activity_import_checkpoint(
            source_browser=source.source_browser,
            source_profile=source.source_profile,
            source_path_hash=source_hash,
            last_visit_raw=since_raw,
            last_error=str(exc),
            enabled=True,
        )
        return BrowserHistoryImportResult(
            source_browser=source.source_browser,
            source_profile=source.source_profile,
            source_path_hash=source_hash,
            imported_count=0,
            checkpoint_raw=since_raw,
            enabled=True,
            error=str(exc),
        )


def _read_safari_rows(snapshot_path: Path, *, since_raw: Optional[str]) -> list[dict[str, object]]:
    since_value = float(since_raw) if since_raw not in (None, "") else None
    where = "WHERE hv.load_successful = 1"
    params: list[object] = []
    if since_value is not None:
        where += " AND hv.visit_time > ?"
        params.append(since_value)
    with _readonly_sqlite(snapshot_path) as conn:
        rows = conn.execute(
            f"""
            SELECT
                hi.url AS url,
                COALESCE(MAX(hv.title), '') AS title,
                MAX(hi.visit_count) AS visit_count,
                MIN(hv.visit_time) AS first_visit_raw,
                MAX(hv.visit_time) AS last_visit_raw
            FROM history_items hi
            JOIN history_visits hv ON hv.history_item = hi.id
            {where}
            GROUP BY hi.id, hi.url
            ORDER BY MAX(hv.visit_time) ASC
            """,
            params,
        ).fetchall()
    return [_row_to_history_dict(row) for row in rows]


def _read_firefox_rows(snapshot_path: Path, *, since_raw: Optional[str]) -> list[dict[str, object]]:
    since_value = int(since_raw) if since_raw not in (None, "") else None
    where = ""
    params: list[object] = []
    if since_value is not None:
        where = "WHERE hv.visit_date > ?"
        params.append(since_value)
    with _readonly_sqlite(snapshot_path) as conn:
        rows = conn.execute(
            f"""
            SELECT
                p.url AS url,
                COALESCE(p.title, '') AS title,
                MAX(COALESCE(p.visit_count, 0)) AS visit_count,
                MIN(hv.visit_date) AS first_visit_raw,
                MAX(hv.visit_date) AS last_visit_raw
            FROM moz_places p
            JOIN moz_historyvisits hv ON hv.place_id = p.id
            {where}
            GROUP BY p.id, p.url, p.title
            ORDER BY MAX(hv.visit_date) ASC
            """,
            params,
        ).fetchall()
    return [_row_to_history_dict(row) for row in rows]


def _copy_sqlite_snapshot(source_path: Path, destination_dir: Path) -> Path:
    """Copy SQLite DB plus WAL/SHM companions into a temp directory."""
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    destination_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = destination_dir / source_path.name
    shutil.copy2(source_path, snapshot_path)
    for suffix in SQLITE_COMPANION_SUFFIXES:
        companion = source_path.with_name(f"{source_path.name}{suffix}")
        if companion.is_file():
            shutil.copy2(companion, snapshot_path.with_name(f"{snapshot_path.name}{suffix}"))
    return snapshot_path


def _readonly_sqlite(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_history_dict(row: sqlite3.Row) -> dict[str, object]:
    return {
        "url": str(row["url"] or ""),
        "title": str(row["title"] or "") or None,
        "visit_count": max(0, int(row["visit_count"] or 0)),
        "first_visit_raw": str(row["first_visit_raw"]),
        "last_visit_raw": str(row["last_visit_raw"]),
    }


def _safari_timestamp_to_datetime(raw: object) -> Optional[datetime]:
    if raw in (None, ""):
        return None
    return (SAFARI_EPOCH + timedelta(seconds=float(raw))).replace(tzinfo=None)


def _firefox_timestamp_to_datetime(raw: object) -> Optional[datetime]:
    if raw in (None, ""):
        return None
    return datetime.fromtimestamp(int(raw) / 1_000_000, tz=timezone.utc).replace(tzinfo=None)


def _max_raw_timestamp(left: Optional[str], right: Optional[str]) -> Optional[str]:
    if right in (None, ""):
        return left
    if left in (None, ""):
        return str(right)
    try:
        return str(right) if float(str(right)) > float(str(left)) else str(left)
    except ValueError:
        return str(right)


def _hash_source_path(path: Path) -> str:
    return hashlib.sha256(str(path.expanduser()).encode("utf-8")).hexdigest()[:16]


def _domain_from_url(url: str) -> str:
    return (urlsplit(url).hostname or "").lower()


def _is_importable_url(url: object) -> bool:
    parsed = urlsplit(str(url or "").strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
