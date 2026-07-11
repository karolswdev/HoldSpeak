"""Propose `uat/features.yaml` from the record — the ledger's derivation.

The owner's standing point: *we have git; coverage is derived from the record,
not remembered.* This script walks two sources already in the repo —

- the Phase-2 inventory sweep (`_raw-inventory-rows.json`, 255 capabilities
  with per-surface applicability, phases, needed recipes, priority), and
- the holdspeak phase index (`pm/roadmap/holdspeak/README.md`, phases 0–N) —

and emits a proposed `uat/features.yaml`: every capability as a stable ledger
key with its per-surface applicability columns, plus a `phase_map` that pins
**every** holdspeak phase to the keys that cover it (or an explicit
`internal/no-uat-surface` marker — no phase silently absent).

The script *proposes*; the committed YAML is canon (Phase 2 makes it
exhaustive and resolves the `unknown`s). Run:

    uv run python -m uat.tools.build_ledger            # writes uat/features.yaml
    uv run python -m uat.tools.build_ledger --check    # fail if out of date
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INVENTORY = (
    REPO
    / "pm/roadmap/holdspeak-uat/phase-2-the-inventory/directory/_raw-inventory-rows.json"
)
PHASE_INDEX = REPO / "pm/roadmap/holdspeak/README.md"
LEDGER = REPO / "uat/features.yaml"
ADDITIONS = REPO / "uat/feature-additions.yaml"

NO_UAT_MARKER = "internal/no-uat-surface"

_SURFACE = {"Y": "yes", "y": "yes", "n": "no", "N": "no", "?": "unknown"}
_PRIORITY = {
    "must-test": "must",
    "should-test": "should",
    "spot-check": "spot",
    "skip": "skip",
}


def _surface(value: str | None) -> str:
    return _SURFACE.get(str(value or "").strip(), "unknown")


def _parse_phases(raw: str | None) -> list[int]:
    """Pull the HS-<n> desktop phase numbers from a row's phases field."""
    if not raw:
        return []
    nums = {int(m) for m in re.findall(r"HS-(\d+)", str(raw))}
    return sorted(nums)


def load_phase_index() -> dict[int, str]:
    """Every holdspeak phase number → its one-line title (the authoritative set)."""
    phases: dict[int, str] = {}
    # | <n> | <title> | <status> | <folder> | — a lenient status column so
    # hyphenated states (in-progress) and decorated ones still match.
    row = re.compile(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*[^|]+\|")
    for line in PHASE_INDEX.read_text().splitlines():
        m = row.match(line)
        if m:
            phases[int(m.group(1))] = m.group(2).strip()
    return phases


def build_entries(rows: list[dict]) -> list[dict]:
    by_key: dict[str, dict] = {}
    for r in rows:
        key = r["key"]
        entry = {
            "key": key,
            "title": r.get("title", ""),
            "domain": _domain_slug(r.get("domain", "")),
            "phases": _parse_phases(r.get("phases")),
            "surfaces": {
                "web": _surface(r.get("w")),
                "ipad": _surface(r.get("ip")),
                "iphone": _surface(r.get("ph")),
            },
            "recipes": list(r.get("recipes") or []),
            "priority": _PRIORITY.get(str(r.get("prio") or "").strip(), "unknown"),
            "status": "live",
        }
        if key in by_key:
            # The inventory can list a capability twice (two domains touch it);
            # merge phases + recipes so the ledger key stays unique.
            prev = by_key[key]
            prev["phases"] = sorted(set(prev["phases"]) | set(entry["phases"]))
            prev["recipes"] = sorted(set(prev["recipes"]) | set(entry["recipes"]))
        else:
            by_key[key] = entry
    return sorted(by_key.values(), key=lambda e: e["key"])


def load_additions() -> list[dict]:
    """Reviewed post-inventory feature keys, in the emitted ledger shape."""
    import yaml

    doc = yaml.safe_load(ADDITIONS.read_text()) or {}
    entries = doc.get("features") or []
    if not isinstance(entries, list) or any(not isinstance(item, dict) for item in entries):
        raise ValueError(f"{ADDITIONS} must contain a features list of mappings")
    return entries


def merge_entries(derived: list[dict], additions: list[dict]) -> list[dict]:
    merged = {entry["key"]: entry for entry in derived}
    for entry in additions:
        key = str(entry.get("key") or "").strip()
        if not key:
            raise ValueError(f"{ADDITIONS} contains an entry without a key")
        if key in merged:
            raise ValueError(f"{ADDITIONS} duplicates inventory feature {key!r}")
        merged[key] = entry
    return [merged[key] for key in sorted(merged)]


def _domain_slug(domain: str) -> str:
    # The inventory's domain is a long prose string; keep a short leading token.
    head = domain.split("(")[0].strip()
    return head[:60]


def build_phase_map(entries: list[dict], phase_index: dict[int, str]) -> dict[str, list[str]]:
    by_phase: dict[int, list[str]] = {p: [] for p in phase_index}
    for e in entries:
        for p in e["phases"]:
            by_phase.setdefault(p, []).append(e["key"])
    out: dict[str, list[str]] = {}
    for p in sorted(phase_index):
        keys = sorted(set(by_phase.get(p, [])))
        out[str(p)] = keys or [NO_UAT_MARKER]
    return out


def render_yaml(entries: list[dict], phase_map: dict[str, list[str]], phase_index: dict[int, str]) -> str:
    import yaml

    doc = {
        "version": 1,
        "generated_by": "uat/tools/build_ledger.py (proposes; committed YAML is canon)",
        "source": {
            "inventory": str(INVENTORY.relative_to(REPO)),
            "additions": str(ADDITIONS.relative_to(REPO)),
            "phase_index": str(PHASE_INDEX.relative_to(REPO)),
            "phases_total": len(phase_index),
        },
        "features": entries,
        "phase_map": phase_map,
    }
    header = (
        "# The feature ledger — the enumerated shipped surface of HoldSpeak.\n"
        "#\n"
        "# Derived from the record (Phase-2 inventory + reviewed additions + the phase index) by\n"
        "# uat/tools/build_ledger.py, then reviewed by hand. Scenarios cite these keys;\n"
        "# debriefs compute coverage against them. `unknown` surface cells are honest at\n"
        "# v1 — Phase 2 (The Inventory) owns making this exhaustive and resolving them.\n"
        "#\n"
        "# phase_map pins every holdspeak phase to the keys covering it, or the\n"
        f"# {NO_UAT_MARKER} marker — no phase silently absent.\n"
        "#\n"
        "# Regenerate: uv run python -m uat.tools.build_ledger\n"
    )
    return header + yaml.safe_dump(doc, sort_keys=False, width=100, allow_unicode=True)


def generate() -> str:
    rows = json.loads(INVENTORY.read_text())
    phase_index = load_phase_index()
    entries = merge_entries(build_entries(rows), load_additions())
    phase_map = build_phase_map(entries, phase_index)
    return render_yaml(entries, phase_map, phase_index)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="fail if features.yaml is stale")
    ap.add_argument("--out", default=str(LEDGER))
    args = ap.parse_args(argv)

    content = generate()
    out = Path(args.out)
    if args.check:
        current = out.read_text() if out.exists() else ""
        if current != content:
            print(f"features.yaml is stale — re-run: uv run python -m uat.tools.build_ledger", file=sys.stderr)
            return 1
        print("features.yaml is up to date.")
        return 0
    out.write_text(content)
    print(f"wrote {out} ({content.count(chr(10))} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
