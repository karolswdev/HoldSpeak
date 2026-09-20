#!/usr/bin/env python3
"""Generate the Philo architecture views and capability documentation."""
from __future__ import annotations

import argparse
from pathlib import Path
import json
from typing import Any

try:  # Works both as ``python scripts/...`` and as an imported test module.
    from scripts.validate_architecture import ROOT, REGISTRY_TYPES, ValidationResult, validate
    from scripts.check_doc_coverage import generate as generate_coverage
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from validate_architecture import ROOT, REGISTRY_TYPES, ValidationResult, validate
    from check_doc_coverage import generate as generate_coverage


OUTPUTS = (
    "docs/generated/capabilities.yaml",
    "docs/generated/components.yaml",
    "docs/generated/integrations.yaml",
    "docs/generated/trust-boundaries.yaml",
    "docs/generated/domain-model.yaml",
    "docs/generated/platform-matrix.yaml",
    "docs/CAPABILITIES.md",
    "docs/PLATFORMS.md",
    "docs/generated/DOC_COVERAGE.md",
    "docs/generated/doc-coverage.json",
)


def _json(value: Any) -> str:
    # JSON is a strict YAML subset and makes generated output deterministic
    # without adding a YAML runtime dependency to the documentation tool.
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _snapshot(root: Path, records: dict[str, list[dict[str, Any]]]) -> str | None:
    snapshot = root / "docs/internal/philo/snapshot.json"
    if snapshot.is_file():
        try:
            value = json.loads(snapshot.read_text(encoding="utf-8"))
            if isinstance(value, dict) and isinstance(value.get("commit"), str):
                return value["commit"]
        except json.JSONDecodeError:
            pass
    for values in records.values():
        if values and isinstance(values[0], dict) and isinstance(values[0].get("snapshot"), str):
            return values[0]["snapshot"]
    return None


def _view(name: str, records: list[dict[str, Any]], snapshot: str | None, missing: list[str], errors: int) -> dict[str, Any]:
    return {"generated": True, "generator": "scripts/generate_capability_docs.py", "view": name, "snapshot": snapshot, "missing_shards": missing, "validation_errors_at_generation": errors, "records": records}


def _platform_rows(capabilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for capability in capabilities:
        for platform, availability in sorted((capability.get("platforms") or {}).items()):
            rows.append({"id": f"{capability.get('id')}@{platform}", "capability_id": capability.get("id"), "platform": platform, "availability": availability, "status": capability.get("status"), "source_ids": [source.get("path") for source in capability.get("sources", []) if isinstance(source, dict) and isinstance(source.get("path"), str)]})
    return rows


def _capability_markdown(records: list[dict[str, Any]], snapshot: str | None, missing: list[str]) -> str:
    lines = ["# Capabilities", "", "<!-- GENERATED FILE: scripts/generate_capability_docs.py -->", "", f"Source snapshot: `{snapshot or 'unknown'}`.", "", "This catalogue is generated from the Philo metadata shards. Status, evidence and release availability are separate fields.", f"Missing shards: **{', '.join(missing) if missing else 'none'}**.", "", "| Capability | Name | Purpose | Status | Exposure | Evidence | Owner observed | Egress |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in records:
        lines.append(f"| `{row.get('id')}` | {row.get('name')} | {row.get('purpose')} | {row.get('status')} | {row.get('exposure')} | {row.get('evidence_level')} | {'yes' if row.get('owner_observed') else 'no'} | {'possible' if row.get('egress_possible') else 'local'} |")
    lines.extend(["", "## Reading the catalogue", "", "A source path proves that a file was inspected. A test assertion proves what was inspected. A passing execution and owner observation are separate evidence. An unverified or missing shard stays visible in the generated metadata.", ""])
    return "\n".join(lines)


def _platform_markdown(rows: list[dict[str, Any]], snapshot: str | None, missing: list[str]) -> str:
    lines = ["# Platform matrix", "", "<!-- GENERATED FILE: scripts/generate_capability_docs.py -->", "", f"Source snapshot: `{snapshot or 'unknown'}`.", "", f"Missing shards: **{', '.join(missing) if missing else 'none'}**.", "", "| Capability | Platform | Availability | Status |", "| --- | --- | --- | --- |"]
    for row in rows:
        lines.append(f"| `{row['capability_id']}` | `{row['platform']}` | {row['availability']} | {row['status']} |")
    lines.extend(["", "Availability is a source-backed classification. It does not establish a release or owner observation.", ""])
    return "\n".join(lines)


def generate(root: Path = ROOT, *, allow_invalid: bool = False, allow_missing_shards: bool = True) -> dict[str, str]:
    result = validate(root, allow_missing_shards=allow_missing_shards)
    if result.errors and not allow_invalid:
        raise ValueError("architecture metadata is invalid; run scripts/validate_architecture.py for diagnostics")
    records = result.records
    snapshot = _snapshot(root, records)
    outputs: dict[str, str] = {}
    for kind in REGISTRY_TYPES:
        filename = {"capabilities": "capabilities.yaml", "components": "components.yaml", "integrations": "integrations.yaml", "trust_boundaries": "trust-boundaries.yaml", "domain_model": "domain-model.yaml"}[kind]
        outputs[f"docs/generated/{filename}"] = _json(_view(kind, records[kind], snapshot, result.missing_shards, len(result.errors)))
    platform_rows = _platform_rows(records["capabilities"])
    outputs["docs/generated/platform-matrix.yaml"] = _json(_view("platform_matrix", platform_rows, snapshot, result.missing_shards, len(result.errors)))
    outputs["docs/CAPABILITIES.md"] = _capability_markdown(records["capabilities"], snapshot, result.missing_shards)
    outputs["docs/PLATFORMS.md"] = _platform_markdown(platform_rows, snapshot, result.missing_shards)
    outputs.update(generate_coverage(root, allow_invalid=True, allow_missing_shards=allow_missing_shards))
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--allow-invalid", action="store_true", help="generate with explicit validation_errors_at_generation metadata")
    parser.add_argument("--allow-missing-shards", action="store_true", help="keep absent shards as explicit metadata diagnostics")
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
        print("Generated architecture drift: " + ", ".join(drift))
        return 1
    print("Architecture documentation " + ("checked" if args.check else "generated") + f" ({len(outputs)} outputs).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
