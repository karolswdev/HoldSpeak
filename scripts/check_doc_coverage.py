#!/usr/bin/env python3
"""Build and check the evidence coverage report for Philo metadata.

The report deliberately separates references that exist from claims whose test
assertions were inspected or whose tests were executed. A documentation path
alone never makes a semantic claim covered.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import json
from typing import Any

try:  # Works both as ``python scripts/...`` and as an imported test module.
    from scripts.validate_architecture import ROOT, REGISTRY_TYPES, ValidationResult, validate, _test_parts, _execution_passed
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from validate_architecture import ROOT, REGISTRY_TYPES, ValidationResult, validate, _test_parts, _execution_passed


OUTPUTS = ("docs/generated/DOC_COVERAGE.md", "docs/generated/doc-coverage.json")
DOC_CLASSES = {
    "operational": {"OPERATIONS.md", "TROUBLESHOOTING.md", "MODEL_RUNTIME.md", "DESK_ARCHITECTURE.md", "MEETING_ARCHITECTURE.md", "DICTATION_ARCHITECTURE.md", "EXECUTION_DESTINATIONS.md"},
    "security": {"SECURITY_MODEL.md", "AUTHORITY_MODEL.md", "AUTHORITY.md"},
    "api": {"API_REFERENCE.md", "API_SURFACE.md", "SYSTEM_INTEGRATION_MAP.md", "api-surface.json"},
}


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _test_records(record: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in record.get("tests", []):
        path, node, assertion, execution = _test_parts(raw)
        out.append({"path": path, "node": node, "assertion": assertion, "execution": execution})
    return out


def _doc_class(path: str) -> str | None:
    return next((name for name, names in DOC_CLASSES.items() if Path(path).name in names), None)


def _record_coverage(root: Path, kind: str, record: dict[str, Any]) -> dict[str, Any]:
    sources = record.get("sources", []) if isinstance(record.get("sources", []), list) else []
    tests = _test_records(record)
    docs = record.get("docs", []) if isinstance(record.get("docs", []), list) else []
    source_present = sum(1 for ref in sources if isinstance(ref, dict) and isinstance(ref.get("path"), str) and (root / ref["path"]).is_file())
    test_present = sum(1 for ref in tests if isinstance(ref.get("path"), str) and (root / ref["path"]).is_file())
    docs_present = sum(1 for path in docs if isinstance(path, str) and (root / path).is_file())
    assertions = sum(1 for ref in tests if isinstance(ref.get("assertion"), str) and bool(ref["assertion"].strip()))
    executed = sum(1 for ref in tests if _execution_passed(ref.get("execution")))
    docs_by_class = {name: sum(1 for path in docs if isinstance(path, str) and _doc_class(path) == name and (root / path).is_file()) for name in DOC_CLASSES}
    has_executed_assertion = any(
        bool(ref.get("assertion")) and _execution_passed(ref.get("execution"))
        for ref in tests
    )
    return {
        "id": record.get("id"),
        "kind": kind,
        "path_presence": {"sources": [source_present, len(sources)], "tests": [test_present, len(tests)], "docs": [docs_present, len(docs)]},
        "assertions_inspected": assertions,
        "tests_executed": executed,
        "docs": docs_by_class,
        "semantic_status": "partially_evidenced" if has_executed_assertion else "unresolved",
        "semantic_status_reason": "A matching assertion and executed test are required; path presence alone is not sufficient." if not has_executed_assertion else "At least one same-row assertion has a recorded passing test. This does not resolve every behavior, platform or authority claim.",
    }


def build_coverage(root: Path = ROOT, result: ValidationResult | None = None) -> dict[str, Any]:
    result = result or validate(root, allow_missing_shards=True)
    rows = [_record_coverage(root, kind, record) for kind in REGISTRY_TYPES for record in result.records.get(kind, []) if isinstance(record, dict)]
    totals = {"records": len(rows), "source_paths": [0, 0], "test_paths": [0, 0], "doc_paths": [0, 0], "assertions_inspected": 0, "tests_executed": 0, "docs": {name: 0 for name in DOC_CLASSES}, "records_with_executed_assertions": 0, "semantics_unresolved": 0}
    for row in rows:
        for key, target in (("sources", "source_paths"), ("tests", "test_paths"), ("docs", "doc_paths")):
            totals[target][0] += row["path_presence"][key][0]
            totals[target][1] += row["path_presence"][key][1]
        totals["assertions_inspected"] += row["assertions_inspected"]
        totals["tests_executed"] += row["tests_executed"]
        for name in DOC_CLASSES:
            totals["docs"][name] += row["docs"][name]
        totals["records_with_executed_assertions" if row["semantic_status"] == "partially_evidenced" else "semantics_unresolved"] += 1
    return {
        "generated": True,
        "generator": "scripts/check_doc_coverage.py",
        "snapshot": next((record.get("snapshot") for record in _load_shard_headers(root)), None),
        "missing_shards": result.missing_shards,
        "validation_errors": len(result.errors),
        "totals": totals,
        "records": rows,
    }


def _load_shard_headers(root: Path) -> list[dict[str, Any]]:
    data_dir = root / "docs/internal/philo/data"
    headers = []
    for name in ("runtime", "voice", "desk", "integrations"):
        path = data_dir / f"{name}.json"
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                headers.append(data)
    return headers


def _json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _markdown(data: dict[str, Any]) -> str:
    totals = data["totals"]
    lines = [
        "# Philo documentation coverage", "", "<!-- GENERATED FILE: scripts/check_doc_coverage.py -->", "",
        f"Source snapshot: `{data.get('snapshot') or 'unknown'}`.",
        "", "The report keeps path presence, inspected assertions and executed tests separate.",
        "A record is partially evidenced when one same-row assertion has a recorded passing test; this does not certify the whole capability.",
        "Documentation paths are classified by file name; a path does not establish semantic coverage.", "",
        f"Missing shards: **{', '.join(data['missing_shards']) if data['missing_shards'] else 'none'}**.",
        f"Validation errors at generation: **{data['validation_errors']}**.", "",
        "| Measure | Present / total or count |", "| --- | ---: |",
        f"| Source paths | {totals['source_paths'][0]} / {totals['source_paths'][1]} |",
        f"| Test paths | {totals['test_paths'][0]} / {totals['test_paths'][1]} |",
        f"| Documentation paths | {totals['doc_paths'][0]} / {totals['doc_paths'][1]} |",
        f"| Assertions inspected | {totals['assertions_inspected']} |",
        f"| Tests executed | {totals['tests_executed']} |",
        f"| Records with an executed assertion | {totals['records_with_executed_assertions']} |",
        f"| Semantic records unresolved | {totals['semantics_unresolved']} |",
        "", "## Documentation classes", "", "| Class | Existing linked paths |", "| --- | ---: |",
    ]
    lines.extend(f"| {name} | {count} |" for name, count in sorted(totals["docs"].items()))
    lines.extend(["", "## Record coverage", "", "| ID | Kind | Sources | Tests | Assertions | Executed | Docs | Semantics |", "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |"])
    for row in data["records"]:
        lines.append(f"| `{row['id']}` | {row['kind']} | {row['path_presence']['sources'][0]}/{row['path_presence']['sources'][1]} | {row['path_presence']['tests'][0]}/{row['path_presence']['tests'][1]} | {row['assertions_inspected']} | {row['tests_executed']} | {sum(row['docs'].values())} | {row['semantic_status']} |")
    return "\n".join(lines) + "\n"


def generate(root: Path = ROOT, *, allow_invalid: bool = False, allow_missing_shards: bool = True) -> dict[str, str]:
    result = validate(root, allow_missing_shards=allow_missing_shards)
    if result.errors and not allow_invalid:
        raise ValueError("architecture metadata is invalid; run scripts/validate_architecture.py for diagnostics")
    data = build_coverage(root, result)
    return {"docs/generated/doc-coverage.json": _json(data), "docs/generated/DOC_COVERAGE.md": _markdown(data)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--allow-invalid", action="store_true")
    parser.add_argument("--allow-missing-shards", action="store_true", help="keep absent shards as explicit warnings in the report")
    parser.add_argument("--require-shards", action="store_true")
    args = parser.parse_args(argv)
    try:
        outputs = generate(args.root, allow_invalid=args.allow_invalid, allow_missing_shards=not args.require_shards)
    except ValueError as exc:
        print(exc)
        return 1
    drift = []
    for rel, text in outputs.items():
        path = args.root / rel
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                drift.append(rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    if drift:
        print("Documentation coverage drift: " + ", ".join(drift))
        return 1
    print("Documentation coverage " + ("checked" if args.check else "generated") + ".")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
