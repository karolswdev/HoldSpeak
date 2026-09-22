#!/usr/bin/env python3
"""Validate a Philo graph join against its schema and its own references.

Usage:

    uv run python scripts/philo_graph_validate.py docs/generated/graph.json

Two gates, in order.  First the JSON Schema of brief section 8
(``docs/internal/philo/graph/graph.schema.json``).  Then referential
integrity, which a JSON Schema cannot state: link endpoints, case edge and
state ids, observation case ids, finding case and claim ids, resolution
finding ids, id uniqueness across every collection, and — against the tree
itself — Phase 1 record ids, API method/path pairs and source paths.  The
graph does not own Phase 1 semantics (brief section 8), so a reference into
an inventory must land on a record that is really there.

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


def _load_inventory(root: Path, inventory_path: str) -> tuple[Any, str | None]:
    """Read an inventory file.  Generated views are a strict YAML subset, so
    JSON is tried first and YAML only as a fallback."""
    target = root / inventory_path
    if not target.is_file():
        return None, "does not exist in the tree"
    text = target.read_text(encoding="utf-8")
    try:
        return json.loads(text), None
    except ValueError:
        pass
    try:
        import yaml
    except ImportError:  # pragma: no cover - pyyaml ships with the project
        return None, "is not JSON and PyYAML is not installed"
    try:
        return yaml.safe_load(text), None
    except Exception as exc:  # noqa: BLE001 - any parse failure is one violation
        return None, f"could not be parsed ({exc.__class__.__name__})"


def _record_ids(document: Any) -> set[str]:
    """Every record id in an inventory: the ids of dict members of every
    top-level list.  This covers the curated shards (capabilities,
    components, integrations, domain_model, trust_boundaries) and the
    generated views (records) without naming either."""
    ids: set[str] = set()
    if not isinstance(document, dict):
        return ids
    for value in document.values():
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                ids.add(item["id"])
    return ids


def _api_pairs(document: Any) -> set[tuple[str, str]]:
    """Every (METHOD, path) pair an OpenAPI document declares."""
    pairs: set[tuple[str, str]] = set()
    if not isinstance(document, dict):
        return pairs
    paths = document.get("paths")
    if not isinstance(paths, dict):
        return pairs
    for path, operations in paths.items():
        if isinstance(operations, dict):
            for method in operations:
                pairs.add((str(method).upper(), str(path)))
    return pairs


class _Inventories:
    """One read per inventory file, so the output stays deterministic and the
    tree is not walked once per reference."""

    def __init__(self, root: Path) -> None:
        self._root = root
        self._cache: dict[str, tuple[Any, str | None]] = {}

    def get(self, inventory_path: str) -> tuple[Any, str | None]:
        if inventory_path not in self._cache:
            self._cache[inventory_path] = _load_inventory(self._root, inventory_path)
        return self._cache[inventory_path]


def _phase1_violations(graph: dict, root: Path) -> list[str]:
    """Phase 1 references must land on a record that exists."""
    lines: list[str] = []
    inventories = _Inventories(root)

    targets: list[tuple[str, dict]] = []
    for index, node in enumerate(graph.get("nodes", [])):
        refs = node.get("phase1_refs")
        if isinstance(refs, list):
            for position, ref in enumerate(refs):
                if isinstance(ref, dict):
                    targets.append((f"nodes[{index}].phase1_refs[{position}]", ref))
    # A claim review's claim_ref carries the same Phase 1 shape when it names
    # a record and field, and owes the same proof that the record exists.
    for index, review in enumerate(graph.get("claim_reviews", [])):
        claim_ref = review.get("claim_ref")
        if isinstance(claim_ref, dict) and "record_id" in claim_ref:
            targets.append((f"claim_reviews[{index}].claim_ref", claim_ref))

    for where, ref in targets:
        inventory_path = ref.get("inventory_path")
        if not isinstance(inventory_path, str):
            continue
        document, problem = inventories.get(inventory_path)
        if problem is not None:
            lines.append(
                f"phase1-inventory-unreadable: {where}: inventory "
                f"{inventory_path!r} {problem}"
            )
            continue
        record_id = ref.get("record_id")
        if isinstance(record_id, str):
            if record_id not in _record_ids(document):
                lines.append(
                    f"phase1-record-unresolved: {where}: record_id "
                    f"{record_id!r} is not a record in {inventory_path!r}"
                )
            continue
        method = ref.get("method")
        api_path = ref.get("path")
        if isinstance(method, str) and isinstance(api_path, str):
            if (method.upper(), api_path) not in _api_pairs(document):
                lines.append(
                    f"phase1-api-unresolved: {where}: {method.upper()} "
                    f"{api_path} is not declared in {inventory_path!r}"
                )
    return lines


def _source_path_violations(graph: dict, root: Path) -> list[str]:
    """Every source reference must name a file that is really in the tree.

    A source line number is evidence, not identity (brief section 1); a path
    that does not exist is neither.
    """
    lines: list[str] = []

    def check(where: str, refs: Any) -> None:
        if not isinstance(refs, list):
            return
        for position, ref in enumerate(refs):
            if not isinstance(ref, dict):
                continue
            source_path = ref.get("path")
            if isinstance(source_path, str) and not (root / source_path).is_file():
                lines.append(
                    f"source-path-missing: {where}[{position}].path: "
                    f"{source_path!r} does not exist in the tree"
                )

    for index, node in enumerate(graph.get("nodes", [])):
        check(f"nodes[{index}].sources", node.get("sources"))
    for index, link in enumerate(graph.get("links", [])):
        check(f"links[{index}].evidence", link.get("evidence"))
    for collection in ("claim_reviews", "findings", "resolutions"):
        for index, item in enumerate(graph.get(collection, [])):
            check(f"{collection}[{index}].evidence", item.get("evidence"))
    for index, review in enumerate(graph.get("claim_reviews", [])):
        claim_ref = review.get("claim_ref")
        if isinstance(claim_ref, dict) and "path" in claim_ref:
            check(f"claim_reviews[{index}].claim_ref", [claim_ref])
    return lines


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


def validate(graph: Any, schema: dict, root: Path = REPO_ROOT) -> list[str]:
    """Schema first; integrity only on a schema-clean document.

    ``root`` is the tree the Phase 1 inventories and source paths are read
    from.
    """
    violations = schema_violations(graph, schema)
    if violations:
        return violations
    violations = integrity_violations(graph)
    violations.extend(_phase1_violations(graph, root))
    violations.extend(_source_path_violations(graph, root))
    return sorted(violations)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("graph", type=Path, help="the graph.json to validate")
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA,
        help="the JSON Schema to validate against",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="the tree the Phase 1 inventories and source paths are read from",
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

    violations = validate(graph, schema, args.root)
    for line in violations:
        print(line)
    if violations:
        print(f"FAIL {len(violations)} violation(s) in {args.graph}")
        return 1
    print(f"OK {args.graph}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
