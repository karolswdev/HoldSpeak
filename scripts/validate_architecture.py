#!/usr/bin/env python3
"""Validate the bounded Philo architecture registry.

This checker reads JSON and source text only. It never imports HoldSpeak. The
shards remain the authored record; the checker verifies paths, symbols,
test-node references, enums and cross-record references. Assertion text still
requires human/source review; the checker does not prove its meaning.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "docs/internal/philo/data"
SCHEMA_DIR = ROOT / "architecture"
EXPECTED_SHARDS = ("runtime", "voice", "desk", "integrations")
REGISTRY_TYPES = ("capabilities", "components", "integrations", "domain_model", "trust_boundaries")
SCHEMA_NAMES = {
    "capabilities": "capability.schema.json",
    "components": "component.schema.json",
    "integrations": "integration.schema.json",
    "domain_model": "domain_model.schema.json",
    "trust_boundaries": "trust_boundary.schema.json",
}
PLATFORMS = ("macos", "linux_x11", "linux_wayland", "ipad", "aipi")
PY_SUFFIXES = {".py", ".pyi"}
TS_SUFFIXES = {".ts", ".tsx", ".js", ".jsx"}
REFERENCE_FIELDS = {"replacement", "references", "related_ids", "replaces", "replaced_by"}


@dataclass(frozen=True)
class Diagnostic:
    level: str
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.level.upper()} {self.path}: {self.message}"


@dataclass
class ValidationResult:
    errors: list[Diagnostic] = field(default_factory=list)
    warnings: list[Diagnostic] = field(default_factory=list)
    records: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    shards: list[str] = field(default_factory=list)
    missing_shards: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(self, level: str, path: str, message: str) -> None:
        item = Diagnostic(level, path, message)
        (self.errors if level == "error" else self.warnings).append(item)


def _type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, True)


def _schema_errors(value: Any, schema: dict[str, Any], path: str, root_schema: dict[str, Any]) -> list[str]:
    """Small JSON-Schema subset, kept dependency-free for repository tooling."""
    if "$ref" in schema:
        ref = schema["$ref"]
        if ref.startswith("#/$defs/"):
            name = ref.rsplit("/", 1)[1]
            target = root_schema.get("$defs", {}).get(name)
            if target is None:
                return [f"{path}: unresolved schema reference {ref}"]
            return _schema_errors(value, target, path, root_schema)
    if "oneOf" in schema:
        branches = [_schema_errors(value, b, path, root_schema) for b in schema["oneOf"]]
        if any(not b for b in branches):
            return []
        return [f"{path}: does not match any allowed shape"]
    errors: list[str] = []
    expected = schema.get("type")
    if expected is not None:
        expected_types = expected if isinstance(expected, list) else [expected]
        if not any(_type_matches(value, t) for t in expected_types):
            return [f"{path}: expected {' or '.join(expected_types)}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} is not one of {schema['enum']!r}")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: must not be empty")
        pattern = schema.get("pattern")
        if pattern and not re.search(pattern, value):
            errors.append(f"{path}: does not match {pattern!r}")
    if isinstance(value, (list, dict)) and len(value) < schema.get("minItems", 0):
        errors.append(f"{path}: must contain at least {schema['minItems']} items")
    if isinstance(value, int) and not isinstance(value, bool) and value < schema.get("minimum", value):
        errors.append(f"{path}: must be >= {schema['minimum']}")
    if isinstance(value, dict):
        for required in schema.get("required", []):
            if required not in value:
                errors.append(f"{path}: missing required field {required!r}")
        props = schema.get("properties", {})
        for key, child in value.items():
            if key in props:
                errors.extend(_schema_errors(child, props[key], f"{path}.{key}", root_schema))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unknown field {key!r}")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            errors.extend(_schema_errors(item, schema["items"], f"{path}[{i}]", root_schema))
    return errors


def _safe_path(root: Path, raw: Any) -> Path | None:
    if not isinstance(raw, str) or not raw or Path(raw).is_absolute():
        return None
    candidate = Path(raw)
    if ".." in candidate.parts:
        return None
    return root / candidate


def _python_symbols(text: str) -> set[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    names: set[str] = set()

    def assignment_names(node: ast.AST) -> Iterable[str]:
        targets: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)):
            targets = [node.target]
        for target in targets:
            if isinstance(target, ast.Name):
                yield target.id
            elif isinstance(target, (ast.Tuple, ast.List)):
                for item in target.elts:
                    if isinstance(item, ast.Name):
                        yield item.id

    def visit(nodes: Iterable[ast.AST], prefix: str = "") -> None:
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qualified = f"{prefix}.{node.name}" if prefix else node.name
                names.add(node.name)
                names.add(qualified)
                visit(node.body, qualified)
            elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
                names.update(assignment_names(node))
            elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
                names.add(node.target.id)

    visit(tree.body)
    return names


def _symbol_exists(root: Path, rel: str, symbol: str) -> tuple[bool, str]:
    path = _safe_path(root, rel)
    if path is None or not path.is_file():
        return False, "source path does not exist"
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix in PY_SUFFIXES:
        if symbol == "module":
            return True, "module sentinel"
        if not _python_symbols(text):
            return False, "Python source cannot be parsed"
        return symbol in _python_symbols(text), "Python AST symbol"
    if path.suffix in TS_SUFFIXES:
        # TypeScript is intentionally token based: the checker must not import
        # or execute the browser bundle. Quoted prose is accepted for source
        # references only when it occurs verbatim (for a named contract).
        if re.fullmatch(r"[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*", symbol):
            return bool(re.search(rf"(?<![\w$]){re.escape(symbol)}(?![\w$])", text)), "TypeScript token"
        return symbol in text, "TypeScript source text"
    return True, "documentation/source path"


def _test_parts(value: Any) -> tuple[str | None, str | None, str | None, Any]:
    if isinstance(value, str):
        if "::" not in value:
            return value, None, None, None
        path, node = value.split("::", 1)
        return path, node, "", None
    if isinstance(value, dict):
        return value.get("path"), value.get("node"), value.get("assertion"), value.get("execution")
    return None, None, None, None


def _test_node_exists(root: Path, rel: str, node: str) -> tuple[bool, str]:
    path = _safe_path(root, rel)
    if path is None or not path.is_file():
        return False, "test path does not exist"
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix in PY_SUFFIXES:
        return node in _python_symbols(text), "Python AST test symbol"
    if path.suffix in TS_SUFFIXES:
        # Vitest titles are the stable test node in this repository. Exact
        # matching prevents a path-only or invented title from becoming proof.
        return node in text, "TypeScript test title/token"
    if path.suffix == ".swift":
        return bool(re.search(r"\bfunc\s+" + re.escape(node) + r"\s*\(", text)), "Swift test function declaration"
    return False, "unsupported test source language"


def _execution_passed(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower() in {"passed", "pass", "green", "executed", "observed"}
    if isinstance(value, dict):
        return str(value.get("status", "")).lower() in {"passed", "pass", "green", "executed", "observed"}
    return False


def _check_path(root: Path, raw: Any, label: str, location: str, result: ValidationResult) -> Path | None:
    path = _safe_path(root, raw)
    if path is None:
        result.add("error", location, f"{label} path must be a safe repository-relative path")
        return None
    if any(part in {"_built", "node_modules", ".venv", ".tmp"} for part in Path(raw).parts):
        result.add("error", location, f"{label} reference points to a build or environment artifact: {raw}")
        return None
    if not path.is_file():
        result.add("error", location, f"{label} path does not exist: {raw}")
        return None
    return path


def _check_source(root: Path, source: Any, location: str, result: ValidationResult) -> None:
    if not isinstance(source, dict):
        result.add("error", location, "source reference must be an object")
        return
    path = _check_path(root, source.get("path"), "source", f"{location}.path", result)
    line = source.get("line")
    if not isinstance(line, int) or isinstance(line, bool) or line < 1:
        result.add("error", f"{location}.line", "source line must be a positive integer")
    elif path is not None and line > len(path.read_text(encoding="utf-8", errors="replace").splitlines()):
        result.add("error", f"{location}.line", f"source line {line} is outside {source['path']}")
    if path is not None and isinstance(source.get("symbol"), str):
        ok, kind = _symbol_exists(root, source["path"], source["symbol"])
        if not ok:
            result.add("error", f"{location}.symbol", f"symbol {source['symbol']!r} not found ({kind})")


def _check_entry_point(root: Path, value: Any, location: str, result: ValidationResult) -> None:
    if not isinstance(value, str) or "::" not in value:
        result.add("error", location, "entry point must be path::symbol")
        return
    path, symbol = value.split("::", 1)
    _check_path(root, path, "entry point", f"{location}.path", result)
    ok, kind = _symbol_exists(root, path, symbol)
    if not ok:
        result.add("error", f"{location}.symbol", f"symbol {symbol!r} not found ({kind})")


def _check_test(root: Path, value: Any, location: str, result: ValidationResult) -> None:
    path, node, assertion, _execution = _test_parts(value)
    if path is None:
        result.add("error", location, "test reference must be an object or path::node")
        return
    _check_path(root, path, "test", f"{location}.path", result)
    if not node:
        result.add("error", f"{location}.node", "test node is required")
        return
    if not assertion:
        if isinstance(value, str):
            # Legacy integration ledgers used path::title before assertion
            # capture was added. Keep the reference inspectable, but leave it
            # unresolved for coverage until an assertion is recorded.
            result.add("warning", f"{location}.assertion", "test assertion was not recorded; semantic coverage remains unresolved")
        else:
            result.add("error", f"{location}.assertion", "test assertion text is required")
    ok, kind = _test_node_exists(root, path, node)
    if not ok:
        result.add("error", f"{location}.node", f"test node {node!r} not found ({kind})")


def _check_docs(root: Path, values: Any, location: str, result: ValidationResult) -> None:
    if not isinstance(values, list):
        return
    for i, raw in enumerate(values):
        _check_path(root, raw, "documentation", f"{location}[{i}]", result)


def _check_api(root: Path, value: Any, location: str, result: ValidationResult) -> None:
    """Check explicit routes; prose names of CLI/internal APIs are not routes."""
    if not isinstance(value, str):
        return
    match = re.fullmatch(r"(?:(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|WS)(/[A-Z]+)* )?(/[^ ]+)", value)
    if not match:
        return
    inventory = root / "docs/api-surface.json"
    if not inventory.is_file():
        result.add("error", location, "explicit API reference requires docs/api-surface.json")
        return
    normalize = lambda path: re.sub(r"\{[^}]+\}", "{}", path)
    routes = json.loads(inventory.read_text())["routes"]
    path = value.split(" ")[-1]
    candidates = [route for route in routes if normalize(route["path"]) == normalize(path)]
    methods = value.split(" ")[0].split("/") if " " in value else []
    if not candidates or any(not any(method in route["methods"] for route in candidates) for method in methods):
        result.add("error", location, f"API reference absent from route inventory: {value}")


def _check_references(value: Any, known_ids: set[str], location: str, result: ValidationResult) -> None:
    """Validate only declared ID fields; dependency prose remains free text."""
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}"
            if key in REFERENCE_FIELDS:
                values = child if isinstance(child, list) else [child]
                for i, ref in enumerate(values):
                    if ref is None:
                        continue
                    if not isinstance(ref, str) or ref not in known_ids:
                        result.add("error", f"{child_location}[{i}]", f"undeclared ID reference {ref!r}")
            else:
                _check_references(child, known_ids, child_location, result)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            _check_references(child, known_ids, f"{location}[{i}]", result)


def _validate_record(root: Path, record: Any, kind: str, location: str, schema: dict[str, Any], known_ids: set[str], result: ValidationResult) -> None:
    for message in _schema_errors(record, schema, location, schema):
        result.add("error", location, message)
    if not isinstance(record, dict):
        return
    for i, source in enumerate(record.get("sources", [])):
        _check_source(root, source, f"{location}.sources[{i}]", result)
    for i, doc in enumerate(record.get("docs", [])):
        _check_docs(root, [doc], f"{location}.docs[{i}]", result)
    if kind == "capabilities":
        for i, api in enumerate(record.get("apis", [])):
            _check_api(root, api, f"{location}.apis[{i}]", result)
        for i, entry in enumerate(record.get("entry_points", [])):
            _check_entry_point(root, entry, f"{location}.entry_points[{i}]", result)
        platforms = record.get("platforms", {})
        if isinstance(platforms, dict) and set(platforms) != set(PLATFORMS):
            result.add("error", f"{location}.platforms", f"platform keys must be {list(PLATFORMS)!r}")
        if record.get("egress_possible") and not str(record.get("egress", "")).strip():
            result.add("error", f"{location}.egress", "egress_possible requires an explicit egress statement")
        side_effect = record.get("side_effect", "")
        if isinstance(side_effect, str) and side_effect.startswith("external"):
            if record.get("egress_possible") is not True:
                result.add("error", f"{location}.egress_possible", "external side effect must declare egress_possible=true")
            if not str(record.get("authority", "")).strip():
                result.add("error", f"{location}.authority", "external effect requires explicit authority")
        if record.get("status") == "stable":
            if record.get("owner_observed") is not True:
                result.add("error", f"{location}.owner_observed", "stable capability requires owner_observed=true")
            if not any(_execution_passed(_test_parts(t)[3]) for t in record.get("tests", [])):
                result.add("error", f"{location}.tests", "stable capability requires an executed passing test")
            if record.get("evidence_level") not in {"tests_executed", "owner_observed"}:
                result.add("error", f"{location}.evidence_level", "stable capability requires test or owner evidence")
        for i, test in enumerate(record.get("tests", [])):
            _check_test(root, test, f"{location}.tests[{i}]", result)
    elif kind == "integrations":
        for i, test in enumerate(record.get("tests", [])):
            _check_test(root, test, f"{location}.tests[{i}]", result)
    _check_references(record, known_ids, location, result)


def validate(
    root: Path = ROOT,
    *,
    data_dir: Path | None = None,
    expected_shards: Iterable[str] = EXPECTED_SHARDS,
    allow_missing_shards: bool = False,
) -> ValidationResult:
    root = Path(root)
    data_dir = data_dir or root / "docs/internal/philo/data"
    result = ValidationResult(records={kind: [] for kind in REGISTRY_TYPES})
    expected = tuple(expected_shards)
    shard_paths: dict[str, Path] = {}
    for shard in expected:
        path = data_dir / f"{shard}.json"
        if not path.is_file():
            result.missing_shards.append(shard)
            result.add("warning" if allow_missing_shards else "error", str(path.relative_to(root) if path.is_relative_to(root) else path), "expected metadata shard is missing; ask the lane owner before treating the aggregate as complete")
            continue
        shard_paths[shard] = path
        result.shards.append(shard)
    for path in sorted(data_dir.glob("*.json")) if data_dir.is_dir() else []:
        if path.stem not in expected and path.stem not in {"requirements", "components-catalogue"}:
            result.add("warning", str(path.relative_to(root) if path.is_relative_to(root) else path), "JSON file is not an architecture shard and was ignored")
    snapshot_file = root / "docs/internal/philo/snapshot.json"
    expected_snapshot = None
    if snapshot_file.is_file():
        try:
            expected_snapshot = json.loads(snapshot_file.read_text()).get("commit")
        except json.JSONDecodeError as exc:
            result.add("error", str(snapshot_file.relative_to(root)), f"invalid snapshot JSON: {exc}")
    all_ids: dict[str, str] = {}
    ids_by_type: dict[str, dict[str, str]] = {kind: {} for kind in REGISTRY_TYPES}
    for shard, path in shard_paths.items():
        location = str(path.relative_to(root) if path.is_relative_to(root) else path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            result.add("error", location, f"cannot read JSON: {exc}")
            continue
        if not isinstance(data, dict):
            result.add("error", location, "shard must be an object")
            continue
        if data.get("schema_version") != 1:
            result.add("error", f"{location}.schema_version", "shard schema_version must be 1")
        if not isinstance(data.get("snapshot"), str) or not data.get("snapshot"):
            result.add("error", f"{location}.snapshot", "shard snapshot is required")
        elif expected_snapshot and data["snapshot"] != expected_snapshot:
            result.add("error", f"{location}.snapshot", f"snapshot drift: {data['snapshot']} != {expected_snapshot}")
        for kind in REGISTRY_TYPES:
            values = data.get(kind, [])
            if not isinstance(values, list):
                result.add("error", f"{location}.{kind}", "registry must be an array")
                continue
            result.records[kind].extend(values)
            for i, record in enumerate(values):
                if isinstance(record, dict) and isinstance(record.get("id"), str):
                    owner = f"{location}.{kind}[{i}]"
                    if record["id"] in ids_by_type[kind]:
                        result.add("error", f"{owner}.id", f"duplicate {kind} ID {record['id']!r}; first declared at {ids_by_type[kind][record['id']]}")
                    else:
                        ids_by_type[kind][record["id"]] = owner
                    # Keep a representative owner for diagnostics and record
                    # addressing; IDs are namespaced by registry type.
                    all_ids.setdefault(record["id"], owner)
    known_ids = set(all_ids)
    schema_dir = root / "architecture" if (root / "architecture").is_dir() else SCHEMA_DIR
    for kind, records in result.records.items():
        schema_path = schema_dir / SCHEMA_NAMES[kind]
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            result.add("error", str(schema_path), f"cannot read schema: {exc}")
            continue
        for i, record in enumerate(records):
            owner = all_ids.get(record.get("id"), f"{kind}[{i}]") if isinstance(record, dict) else f"{kind}[{i}]"
            _validate_record(root, record, kind, owner, schema, known_ids, result)
    for filename, collection, identity in (("requirements", "requirements", "id"), ("components-catalogue", "components", "name")):
        path = data_dir / f"{filename}.json"
        if not path.is_file():
            continue
        try:
            auxiliary = json.loads(path.read_text())
            rows = auxiliary[collection]
            if not isinstance(rows, list):
                raise ValueError("collection must be an array")
        except (ValueError, KeyError, TypeError) as exc:
            result.add("error", str(path), f"invalid auxiliary catalogue: {exc}")
            continue
        seen = set()
        for i, row in enumerate(rows):
            location = f"{filename}.{collection}[{i}]"
            if not isinstance(row, dict) or not row.get(identity) or row.get(identity) in seen:
                result.add("error", location, "missing or duplicate identity")
                continue
            seen.add(row[identity])
            for j, source in enumerate(row.get("sources", [row["source"]] if "source" in row else [])):
                _check_source(root, source, f"{location}.sources[{j}]", result)
            if filename == "requirements":
                if row.get("status") not in {"IMPLEMENTED", "PARTIAL", "SPEC-DEBT", "UNIMPLEMENTED", "CONFLICT", "DEPRECATED"}:
                    result.add("error", location, "invalid requirement status")
                for field in ("statement", "rationale", "owner", "acceptance", "test", "gap"):
                    if not isinstance(row.get(field), str):
                        result.add("error", location, f"requirement needs text field {field}")
    return result


def _print_result(result: ValidationResult, *, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps({"ok": result.ok, "shards": result.shards, "missing_shards": result.missing_shards, "errors": [d.__dict__ for d in result.errors], "warnings": [d.__dict__ for d in result.warnings]}, indent=2, sort_keys=True))
        return
    print(f"Architecture metadata: {len(result.shards)} shard(s), {sum(len(v) for v in result.records.values())} record(s)")
    for diagnostic in [*result.errors, *result.warnings]:
        print(diagnostic)
    if result.ok:
        print("Architecture metadata validation passed.")
    else:
        print(f"Architecture metadata validation failed: {len(result.errors)} error(s), {len(result.warnings)} warning(s).")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--allow-missing-shards", action="store_true", help="report absent shards as warnings while validating available shards")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    result = validate(args.root, allow_missing_shards=args.allow_missing_shards)
    _print_result(result, as_json=args.as_json)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
