#!/usr/bin/env python3
"""Reproduce the Philo research snapshot without importing the application.

Reads a Git revision, evaluates only the literal base-schema string and uses an
in-memory SQLite connection. It never opens a HoldSpeak database or user config.
The output is archaeology of the named revision, not a runtime-support claim.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import tomllib

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "docs/internal/philo/snapshot.json"


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True)


def category(path: str) -> str:
    if path.startswith("pm/"):
        return "roadmap-and-evidence"
    if path.startswith("docs/internal/"):
        return "internal-documentation"
    if path.startswith("docs/"):
        return "public-docs-and-assets"
    if path.startswith("tests/"):
        return "tests-and-fixtures"
    if path.startswith("apple/"):
        return "apple-clients-and-native-runtime"
    if path.startswith("aipi-lite/"):
        return "aipi-firmware-and-bridge"
    if path.startswith("extensions/"):
        return "browser-connectors"
    if path.startswith("web/"):
        return "web-frontend"
    if path.startswith("holdspeak/"):
        if "/db/" in path:
            return "python-storage"
        if "/kernel/" in path:
            return "python-kernel"
        if "/connectors/" in path:
            return "python-connectors"
        if "/plugins/" in path:
            return "python-plugins"
        if "/static/" in path:
            return "bundled-static-assets"
        return "python-runtime"
    if path.startswith("scripts/"):
        return "development-tools"
    if path.startswith(".github/"):
        return "ci-and-release"
    if path.startswith(("uat/", "dogfood/")):
        return "verification-harness"
    if path.startswith((".githooks/", ".claude/")):
        return "delivery-and-agent-tools"
    return "root-contract-or-other"


def source(revision: str, path: str) -> str:
    return git("show", f"{revision}:{path}")


def dumps(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def collect(revision: str) -> dict[str, str]:
    revision = git("rev-parse", revision).strip()
    paths = git("ls-tree", "-r", "--name-only", revision).splitlines()
    tree = [{"path": p, "category": category(p)} for p in paths]
    counts = Counter(row["category"] for row in tree)
    manifests = [p for p in paths if Path(p).name in {
        "pyproject.toml", "uv.lock", "package.json", "package-lock.json",
        "Package.swift", "Package.resolved", "requirements.txt", "requirements-dev.txt",
        "Cargo.toml", "Cargo.lock", "project.yml", "manifest.json",
    } or p.endswith("project.pbxproj")]
    package = tomllib.loads(source(revision, "pyproject.toml"))["project"]
    dependencies = {
        "python_required": package.get("dependencies", []),
        "python_optional": package.get("optional-dependencies", {}),
        "node_manifests": {p: json.loads(source(revision, p)) for p in manifests if p.endswith("package.json")},
        "manifest_paths": manifests,
    }
    schema_tree = ast.parse(source(revision, "holdspeak/db/schema.py"))
    schema = None
    for node in schema_tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SCHEMA_SQL" for t in node.targets):
            schema = ast.literal_eval(node.value)
    if not isinstance(schema, str):
        raise ValueError("SCHEMA_SQL is no longer a literal; inspect the new schema contract")
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(schema)
        records = []
        for name, sql in conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"):
            quoted = '"' + name.replace('"', '""') + '"'
            records.append({
                "name": name, "sql": sql,
                "columns": [dict(zip(("cid", "name", "type", "notnull", "default", "pk"), row)) for row in conn.execute(f"PRAGMA table_info({quoted})")],
                "foreign_keys": [dict(zip(("id", "seq", "table", "from", "to", "on_update", "on_delete", "match"), row)) for row in conn.execute(f"PRAGMA foreign_key_list({quoted})")],
                "indexes": [dict(zip(("seq", "name", "unique", "origin", "partial"), row)) for row in conn.execute(f"PRAGMA index_list({quoted})")],
                "is_sqlite_internal": name.startswith("sqlite_"),
                "is_fts_shadow": bool(re.search(r"_(?:data|idx|content|docsize|config)$", name)) and any(x in name for x in ("fts", "search")),
            })
    finally:
        conn.close()
    docs = []
    for path in paths:
        if not path.endswith(".md") or not (path.startswith("docs/") or path in {"README.md", "CONTRIBUTING.md"}):
            continue
        text = source(revision, path)
        declaration = next((line[:240] for line in text.splitlines()[:25] if "status" in line.lower()), "No explicit status in first 25 lines")
        if "machine-generated" in text[:3000].lower() or text.startswith("# API surface") or "Generated by `scripts/" in text[:500]:
            kind, disposition = "generated-reference", "keep-generator-owned"
        elif not path.startswith("docs/internal/"):
            kind, disposition = "public-guide", "keep-and-reconcile"
        elif Path(path).name.startswith("PLAN_"):
            kind, disposition = "plan-or-rfc", "retain-status-do-not-infer-shipped"
        else:
            kind, disposition = "internal-record", "retain-provenance-review-authority"
        docs.append({"path": path, "kind": kind, "declared_status": declaration, "disposition": disposition})
    head = f"Source snapshot: `{revision}`. Generated by `scripts/philo_repository_census.py`.\n"
    md = "# Repository map\n\n" + head + "\nThis classifies every tracked path at the snapshot. Counts include evidence and assets; they are not capability counts.\n\n| Category | Files |\n| --- | ---: |\n"
    md += "".join(f"| {name} | {n} |\n" for name, n in sorted(counts.items()))
    md += f"\nTotal tracked files: **{len(paths)}**. See [complete tree](repository-tree.json), [manifest census](dependency-manifests.json), [declared schema](schema-inventory.json), and [document dispositions](document-status.json).\n"
    md += "\n## Architectural dependencies\n\n| Dependency | Responsibility | Boundary and setup |\n| --- | --- | --- |\n"
    md += "| FastAPI and Uvicorn | HTTP and WebSocket hub | Required; listen address/auth determine network reach |\n| sounddevice, pynput, pyperclip | Capture, hotkey and text-delivery adapters | Required dependencies; device/session/permission limits remain |\n| mlx-whisper | Apple Silicon speech backend | Platform-marked core dependency; model acquisition can use network |\n| faster-whisper | Linux speech backend | Optional linux extra; inspect model cache/download setup |\n| llama-cpp-python, mlx-lm, OpenAI client | Model execution backends | Optional extras; local inference and endpoint inference are different boundaries |\n| cryptography and keyring | People encryption and native credential access | Required; native secret backend availability is platform-sensitive |\n| React, Vite, Pixi, Zustand | DOM shell, build, spatial renderer and client state | Web package; renderer state is not backend authority |\n| Playwright, Vitest, pytest, Puppeteer | Verification | Development/test scope; not runtime capability proof |\n"
    md += "\n## Manifest inventory\n\n" + "\n".join(f"- `{p}`" for p in manifests) + "\n"
    md += "\n## Limits\n\nManifest declarations show packaging requirements, not that an optional adapter is configured. The JSON preserves complete declarations for review. The schema inventory executes the base SCHEMA_SQL in memory; additional reconciliation and separate stores are documented in STORAGE_AND_MIGRATIONS. A declared foreign key is not proof that every production connection enforces it. The document disposition rules are routing defaults; normative conflicts still need source review.\n"
    return {
        "repository-tree.json": dumps({"snapshot": revision, "files": tree}),
        "dependency-manifests.json": dumps({"snapshot": revision, **dependencies}),
        "schema-inventory.json": dumps({"snapshot": revision, "scope": "base SCHEMA_SQL only, in-memory SQLite; includes engine-created FTS shadow tables", "tables": records}),
        "document-status.json": dumps({"snapshot": revision, "documents": docs}),
        "REPOSITORY_MAP.md": md,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default=json.loads(SNAPSHOT.read_text())["commit"])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = ROOT / "docs/generated"
    generated = collect(args.revision)
    failures = []
    for name, text in generated.items():
        path = output / name
        if args.check:
            if not path.exists() or path.read_text() != text:
                failures.append(str(path.relative_to(ROOT)))
        else:
            output.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    if failures:
        print("Stale census: " + ", ".join(failures))
        return 1
    print(f"Repository census: {len(generated)} outputs {'verified' if args.check else 'written'}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
