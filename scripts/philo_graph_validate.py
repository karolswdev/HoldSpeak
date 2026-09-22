#!/usr/bin/env python3
"""Validate a Philo graph join against its schema and its own references.

Usage:

    uv run python scripts/philo_graph_validate.py docs/generated/graph.json

Two gates, in order.  First the JSON Schema of brief section 8
(``docs/internal/philo/graph/graph.schema.json``).  Then referential
integrity, which a JSON Schema cannot state: link endpoints, case edge and
state ids, observation case ids, finding case and claim ids, resolution
finding ids, and id uniqueness across every collection.

Output is one violation per line, sorted, on stdout.  Exit 0 when clean,
exit 1 with the list otherwise.  The same input always gives the same
bytes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = REPO_ROOT / "docs" / "internal" / "philo" / "graph" / "graph.schema.json"

# Collections whose members carry an ``id`` that must be unique everywhere.
ID_COLLECTIONS = (
    "nodes",
    "cases",
    "observations",
    "claim_reviews",
    "findings",
    "resolutions",
)


def _path_of(error: Any) -> str:
    """Render a jsonschema error path as ``a.0.b``, or ``<root>``."""
    parts = [str(part) for part in error.absolute_path]
    return ".".join(parts) if parts else "<root>"


def schema_violations(graph: Any, schema: dict) -> list[str]:
    """Every schema violation, deepest-first, as sorted lines."""
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema)
    lines = []
    for error in validator.iter_errors(graph):
        lines.append(f"schema: {_path_of(error)}: {error.message}")
    return sorted(lines)


def integrity_violations(graph: dict) -> list[str]:
    """Every reference that does not resolve, and every duplicated id."""
    lines: list[str] = []

    seen: dict[str, str] = {}
    for collection in ID_COLLECTIONS:
        for index, item in enumerate(graph.get(collection, [])):
            item_id = item.get("id")
            if not isinstance(item_id, str):
                continue
            where = f"{collection}[{index}]"
            if item_id in seen:
                lines.append(
                    f"duplicate-id: {where}: id {item_id!r} is already used by {seen[item_id]}"
                )
            else:
                seen[item_id] = where

    node_ids = {
        node["id"]
        for node in graph.get("nodes", [])
        if isinstance(node.get("id"), str)
    }
    case_ids = {
        case["id"]
        for case in graph.get("cases", [])
        if isinstance(case.get("id"), str)
    }
    claim_ids = {
        review["id"]
        for review in graph.get("claim_reviews", [])
        if isinstance(review.get("id"), str)
    }
    finding_ids = {
        finding["id"]
        for finding in graph.get("findings", [])
        if isinstance(finding.get("id"), str)
    }

    def check(code: str, where: str, field: str, value: Any, known: set[str], kind: str) -> None:
        if isinstance(value, str) and value not in known:
            lines.append(
                f"{code}: {where}.{field}: {value!r} does not resolve to a {kind}"
            )

    for index, link in enumerate(graph.get("links", [])):
        where = f"links[{index}]"
        check("link-endpoint-unresolved", where, "from", link.get("from"), node_ids, "node")
        check("link-endpoint-unresolved", where, "to", link.get("to"), node_ids, "node")

    for index, case in enumerate(graph.get("cases", [])):
        where = f"cases[{index}]"
        edge_ids = case.get("edge_ids")
        if isinstance(edge_ids, list):
            for position, edge_id in enumerate(edge_ids):
                check(
                    "case-edge-unresolved",
                    where,
                    f"edge_ids[{position}]",
                    edge_id,
                    node_ids,
                    "node",
                )
        check("case-state-unresolved", where, "state_id", case.get("state_id"), node_ids, "node")

    for index, observation in enumerate(graph.get("observations", [])):
        check(
            "observation-case-unresolved",
            f"observations[{index}]",
            "case_id",
            observation.get("case_id"),
            case_ids,
            "case",
        )

    for index, finding in enumerate(graph.get("findings", [])):
        where = f"findings[{index}]"
        for field, known, kind, code in (
            ("case_ids", case_ids, "case", "finding-case-unresolved"),
            ("claim_ids", claim_ids, "claim review", "finding-claim-unresolved"),
        ):
            values = finding.get(field)
            if isinstance(values, list):
                for position, value in enumerate(values):
                    check(code, where, f"{field}[{position}]", value, known, kind)

    for index, resolution in enumerate(graph.get("resolutions", [])):
        check(
            "resolution-finding-unresolved",
            f"resolutions[{index}]",
            "finding_id",
            resolution.get("finding_id"),
            finding_ids,
            "finding",
        )

    return sorted(lines)


def validate(graph: Any, schema: dict) -> list[str]:
    """Schema first; integrity only on a schema-clean document."""
    violations = schema_violations(graph, schema)
    if violations:
        return violations
    return integrity_violations(graph)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("graph", type=Path, help="the graph.json to validate")
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA,
        help="the JSON Schema to validate against",
    )
    args = parser.parse_args(argv)

    try:
        graph = json.loads(args.graph.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"unreadable-graph: {args.graph}: {exc}")
        return 1
    try:
        schema = json.loads(args.schema.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"unreadable-schema: {args.schema}: {exc}")
        return 1

    violations = validate(graph, schema)
    for line in violations:
        print(line)
    if violations:
        print(f"FAIL {len(violations)} violation(s) in {args.graph}")
        return 1
    print(f"OK {args.graph}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
