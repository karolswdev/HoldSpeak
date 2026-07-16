"""HS-94-10 — the security / privacy audit census.

PLATFORM-CONTRACT §12 / §13 made checkable: every consequential command
the Delivery Runtime processed during a campaign run must be *accounted*
(delivered / refused / unknown — never a silent limbo), and NO secret,
node token, browser token, or absolute filesystem path may cross a client
wire, a receipt, an event, or a hub database row.

This module is both a library (the campaign imports :func:`run_census`)
and a standalone tool: ``uv run python scripts/phase94_audit_census.py``
loads the newest campaign report under the phase-94 evidence directory,
walks it recursively, dumps the hub SQLite database and the node
deduplication ledger, and prints an accounted/leaks verdict.

The census never edits product code and never touches the wire itself —
it reads what the campaign already recorded plus the durable stores.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = (
    REPO_ROOT
    / "pm"
    / "roadmap"
    / "holdspeak"
    / "phase-94-delivery-runtime"
    / "evidence"
    / "hs-94-10"
)

# A command is "accounted" when its final hub/node state is one of these —
# every consequential request has a complete or explicitly-unknown Receipt
# (acceptance: no silent limbo).
ACCOUNTED_STATES = frozenset(
    {
        # delivered / applied
        "delivered",
        "succeeded",
        "spawned",
        "renamed",
        "killed",
        "worktree_created",
        "disarmed",
        "complete",
        # refused pre-execution (safe to edit/reissue)
        "refused",
        "generation_mismatch",
        "target_gone",
        "sequence_conflict",
        "command_expired",
        "policy_version_mismatch",
        "session_key_required",
        "grant_required",
        # explicitly unknown / reconciled absence
        "unknown",
        "not_executed",
        "indeterminate_after_node_reset",
    }
)


def _iter_strings(obj: Any) -> Iterable[str]:
    """Every string leaf in an arbitrarily nested JSON-ish structure."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(key, str):
                yield key
            yield from _iter_strings(value)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            yield from _iter_strings(item)


def scan_for_leaks(
    obj: Any,
    *,
    secrets: dict[str, str],
    path_roots: Iterable[str],
    context: str,
) -> list[dict[str, Any]]:
    """Recursively scan ``obj`` for any secret value or absolute path root.

    Returns a list of typed leak records; an empty list is a clean scan.
    Only *absolute* roots and known secret material are hunted — repo-
    relative paths inside evidence markdown are legitimate content and are
    deliberately not flagged (§13 is about client-crossing raw paths and
    secrets, not roadmap prose).
    """
    roots = [str(r) for r in path_roots if str(r or "").strip()]
    leaks: list[dict[str, Any]] = []
    for text in _iter_strings(obj):
        for label, value in secrets.items():
            if value and value in text:
                leaks.append(
                    {
                        "context": context,
                        "kind": "secret",
                        "label": label,
                        "sample": _redact(text, value),
                    }
                )
        for root in roots:
            if root and root in text:
                leaks.append(
                    {
                        "context": context,
                        "kind": "abs_path",
                        "label": root,
                        "sample": _redact(text, root),
                    }
                )
    return leaks


def _redact(text: str, needle: str) -> str:
    """A bounded, safe echo of a leak site — the offending token itself is
    masked so the census output never becomes a new leak."""
    idx = text.find(needle)
    start = max(0, idx - 24)
    end = min(len(text), idx + len(needle) + 24)
    window = text[start:end].replace(needle, f"<{'*' * 8}>")
    return window[:120]


def dump_hub_db(db_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Every row of the delivery hub tables as plain dicts, for scanning
    and for command accounting. Missing tables yield empty lists."""
    tables = (
        "delivery_command_receipts",
        "work_attempts",
        "work_attempt_events",
    )
    out: dict[str, list[dict[str, Any]]] = {t: [] for t in tables}
    if not Path(db_path).exists():
        return out
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        for table in tables:
            try:
                rows = conn.execute(f"SELECT * FROM {table}").fetchall()  # noqa: S608 — fixed names
            except sqlite3.OperationalError:
                continue
            out[table] = [dict(row) for row in rows]
    finally:
        conn.close()
    return out


def dump_node_ledger(ledger_path: Path) -> list[dict[str, Any]]:
    """Every stored node receipt (the deduplication ledger)."""
    if not Path(ledger_path).exists():
        return []
    conn = sqlite3.connect(str(ledger_path))
    conn.row_factory = sqlite3.Row
    try:
        try:
            rows = conn.execute(
                "SELECT command_id, target_id, receipt_json FROM command_receipts"
            ).fetchall()
        except sqlite3.OperationalError:
            return []
        out: list[dict[str, Any]] = []
        for row in rows:
            try:
                receipt = json.loads(row["receipt_json"])
            except ValueError:
                receipt = {"_unparseable": row["receipt_json"]}
            out.append(
                {
                    "command_id": row["command_id"],
                    "target_id": row["target_id"],
                    "receipt": receipt,
                }
            )
        return out
    finally:
        conn.close()


def account_commands(
    commands: list[dict[str, Any]],
    hub_rows: list[dict[str, Any]],
    node_receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Every command the campaign issued must reach an accounted terminal
    state, and every hub row must carry a resolved ``hub_state``."""
    hub_by_id = {str(r.get("command_id")): r for r in hub_rows}
    node_by_id = {str(r.get("command_id")): r for r in node_receipts}
    unaccounted: list[dict[str, Any]] = []
    accounted = 0
    for cmd in commands:
        cid = str(cmd.get("command_id") or "")
        states: set[str] = set()
        for key in ("final_state", "outcome", "state"):
            val = str(cmd.get(key) or "").strip()
            if val:
                states.add(val)
        hub_row = hub_by_id.get(cid)
        if hub_row is not None:
            states.add(str(hub_row.get("hub_state") or ""))
            receipt = hub_row.get("receipt_json")
            if isinstance(receipt, str) and receipt not in ("", "{}"):
                try:
                    states.add(str(json.loads(receipt).get("outcome") or ""))
                except ValueError:
                    pass
        node_row = node_by_id.get(cid)
        if node_row is not None:
            states.add(str(node_row.get("receipt", {}).get("outcome") or ""))
        if states & ACCOUNTED_STATES:
            accounted += 1
        else:
            unaccounted.append({"command_id": cid, "observed_states": sorted(states)})
    # Any hub row whose state never left "sent"/"claimed" is a limbo Receipt.
    for row in hub_rows:
        state = str(row.get("hub_state") or "")
        if state in ("sent", "claimed"):
            unaccounted.append(
                {
                    "command_id": str(row.get("command_id")),
                    "observed_states": [state],
                    "note": "hub row never resolved past dispatch",
                }
            )
    return {
        "issued": len(commands),
        "accounted": accounted,
        "unaccounted": unaccounted,
        "all_accounted": not unaccounted,
    }


def run_census(
    *,
    workspace: Path,
    report: dict[str, Any],
    hub_db_path: Optional[Path] = None,
    node_ledger_path: Optional[Path] = None,
) -> dict[str, Any]:
    """The whole census over one campaign run. Returns a verdict dict:
    command accounting + a recursive leak scan across every client wire
    body the campaign captured, every hub DB row, and every node receipt.
    """
    workspace = Path(workspace)
    secrets = {k: str(v) for k, v in (report.get("secrets") or {}).items() if v}
    path_roots = list(report.get("path_roots") or [])
    hub_db_path = Path(hub_db_path or (workspace / "hub.db"))
    node_ledger_path = Path(node_ledger_path or (workspace / "node_ledger.db"))

    hub = dump_hub_db(hub_db_path)
    node_receipts = dump_node_ledger(node_ledger_path)

    leaks: list[dict[str, Any]] = []
    # 1. every client wire body the campaign recorded.
    for entry in report.get("wire_capture") or []:
        leaks += scan_for_leaks(
            entry.get("body"),
            secrets=secrets,
            path_roots=path_roots,
            context=f"wire:{entry.get('method')} {entry.get('path')}",
        )
    # 2. node link metadata events (the §6.4 allow-list).
    leaks += scan_for_leaks(
        (report.get("node_link") or {}).get("events"),
        secrets=secrets,
        path_roots=path_roots,
        context="node_events",
    )
    # 3. hub database rows (receipts + attempts + attempt history).
    for table, rows in hub.items():
        leaks += scan_for_leaks(
            rows, secrets=secrets, path_roots=path_roots, context=f"hub_db:{table}"
        )
    # 4. node deduplication ledger receipts.
    leaks += scan_for_leaks(
        node_receipts,
        secrets=secrets,
        path_roots=path_roots,
        context="node_ledger",
    )

    accounting = account_commands(
        report.get("commands") or [],
        hub.get("delivery_command_receipts") or [],
        node_receipts,
    )

    return {
        "accounted": accounting,
        "leaks": leaks,
        "clean": not leaks,
        "scanned": {
            "wire_bodies": len(report.get("wire_capture") or []),
            "hub_rows": sum(len(v) for v in hub.values()),
            "node_receipts": len(node_receipts),
            "secrets_hunted": sorted(secrets),
            "path_roots_hunted": path_roots,
        },
        "hub_db_path": str(hub_db_path),
        "node_ledger_path": str(node_ledger_path),
    }


def _latest_report(evidence_dir: Path) -> Optional[Path]:
    candidates = sorted(evidence_dir.glob("campaign-report*.json"))
    return candidates[-1] if candidates else None


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="HS-94-10 audit / privacy census")
    parser.add_argument(
        "--report",
        default=None,
        help="campaign report JSON (default: newest under the evidence dir)",
    )
    parser.add_argument("--workspace", default=None, help="campaign workspace root")
    args = parser.parse_args(argv)

    report_path = Path(args.report) if args.report else _latest_report(EVIDENCE_DIR)
    if report_path is None or not report_path.exists():
        print("no campaign report found — run scripts/phase94_delivery_campaign.py first")
        return 2
    report = json.loads(report_path.read_text(encoding="utf-8"))
    workspace = Path(
        args.workspace or report.get("meta", {}).get("workspace") or report_path.parent
    )
    verdict = run_census(workspace=workspace, report=report)

    acc = verdict["accounted"]
    print(f"census over {report_path.name}")
    print(
        f"  commands: {acc['accounted']}/{acc['issued']} accounted, "
        f"{len(acc['unaccounted'])} unaccounted"
    )
    print(
        f"  leak scan: {len(verdict['leaks'])} leaks across "
        f"{verdict['scanned']['wire_bodies']} wire bodies, "
        f"{verdict['scanned']['hub_rows']} hub rows, "
        f"{verdict['scanned']['node_receipts']} node receipts"
    )
    for leak in verdict["leaks"][:10]:
        print(f"    LEAK {leak['kind']} [{leak['label']}] in {leak['context']}: {leak['sample']}")
    for miss in acc["unaccounted"][:10]:
        print(f"    UNACCOUNTED {miss}")
    ok = acc["all_accounted"] and verdict["clean"]
    print("  verdict:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
