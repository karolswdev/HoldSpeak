#!/usr/bin/env python3
"""Copy the Tenvil core out of HoldSpeak by manifest (handover section 4).

Kept in HoldSpeak, not in Tenvil. Reads the tree of one commit (default: the
tag tenvil-extraction-base), never the working tree, and writes plain files
into the destination. It copies; it does not cut, rename or edit.

    python3 scripts/tenvil_extract.py ../tenvil            # copy
    python3 scripts/tenvil_extract.py ../tenvil --list     # print the verdicts only
"""
from __future__ import annotations

import argparse
import collections
import os
import pathlib
import re
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[1]

ROOT_FILES = {"pyproject.toml", "uv.lock", "hatch_build.py", ".gitignore", "LICENSE", "NOTICE"}

WEB_ROOT_FILES = {
    "package.json", "package-lock.json", "vite.config.ts", "tsconfig.json", "index.html",
    "briefing.html", "atmospheres.html", "design-tokens.json", "token-allowlist.json",
    "fence-baseline.json",
}
WEB_SCRIPTS = {
    "check-bundle.mjs", "guard-architecture.mjs", "generate-tokens.cjs", "validate-tokens.cjs",
    "prune-builds.mjs", "prune-builds.d.mts", "__tests__/prune-builds.test.mjs",
}

SCRIPTS_KEEP = {
    # the checks
    "quick_check.sh", "quick_check_affected.py", "quick_check_memo.py", "main_check.sh",
    "test_lock.py", "vitest_related.py", "glass_for.py", "check_web_baseline.py",
    "ux_canon_scan.py", "lane.sh", "linux_smoke.sh", "measure.py", "measure_seams.json",
    # used by the product
    "line/build-baresip-linux.sh", "line/record_baresip_events.py",
    # loaded by kept tests (static search; the test run corrects it)
    "walk.py", "reach_runner.py", "operation_parity.py", "gen_operations_json.py",
    "residual_census.py", "prune_empty_polls.py", "program_import_history.py",
    "wire_metal_intel.py", "philo5_pairs.py", "philo13_needs_you_fixture.py",
    "needs_you_faces_fixture.py", "philo13_meetings_headline_fixture.py",
    "philo13_b4_fixture.py", "philo11_send_job.py", "philo9_room_job.py",
    "philo7_file_and_find.py", "philo5_his_words.py", "phase200_eval.py",
    # the end-user installer
    "install.sh",
}

# Whole test files that guard documents, the canon, the atlas or PM files (section 6.2).
# test_product_language.py is NOT here: its data-file checks are kept, the lead trims it.
TESTS_DROP = {
    "tests/unit/test_doc_drift_guard.py", "tests/unit/test_docs_navigation.py",
    "tests/unit/test_doc_generator_checkout.py", "tests/unit/test_mcp_sidecar_doc_drift.py",
    "tests/unit/test_engines_name_guard.py", "tests/unit/test_primitive_contract.py",
    "tests/unit/test_blueprint_graph_conformance.py", "tests/unit/test_evidence_archive.py",
    "tests/unit/test_evidence_scratch_guard.py", "tests/unit/test_architecture_tools.py",
    "tests/e2e/test_mermaid_renders.py", "tests/e2e/test_roadmap_glass.py",
    "tests/unit/test_graph_atlas.py", "tests/e2e/test_walk_rig.py",
    "tests/e2e/test_walk_rig_clearance.py", "tests/e2e/test_graph_walk_smoke.py",
    "tests/e2e/test_decisions_readable_rows.py",
}

# uat/ (decision D3): the framework and its data go; the guided site, decks,
# campaign documents and every Markdown file stay.
UAT_STAY_DIRS = {"web", "decks", "campaigns", "closeouts"}

PARKED = re.compile(r"(^|/)_parked(-[^/]*)?(/|$)")


def verdict(path: str) -> str | None:
    """Return the destination path, or None when the file stays in HoldSpeak."""
    if PARKED.search(path):
        return None
    parts = path.split("/")
    top = parts[0]
    if len(parts) == 1:
        return path if path in ROOT_FILES else None
    rest = "/".join(parts[1:])
    if top == "holdspeak":
        return None if rest == "AGENTS.md" else path
    if top == "web":
        if len(parts) == 2:
            return path if parts[1] in WEB_ROOT_FILES else None
        sub, tail = parts[1], "/".join(parts[2:])
        if sub == "src":
            return None if path.endswith(".txt") else path
        if sub == "public":
            return path
        if sub == "scripts":
            return path if tail in WEB_SCRIPTS else None
        if sub == "design":
            return path if parts[2] == "icons" else None
        return None
    if top == "tests":
        if path in TESTS_DROP or path.endswith(".md"):
            return None
        return path
    if top == "uat":
        if path.endswith(".md") or parts[1] in UAT_STAY_DIRS:
            return None
        return path
    if top == "scripts":
        if rest in SCRIPTS_KEEP or re.fullmatch(r"record_[a-z0-9_]+\.py", rest):
            return path
        return None
    if top == ".githooks":
        # Decision D2: the vendored Delivery Workbench goes only as test support.
        return "tests/support/dw/" + rest
    if top == ".holdspeak" and rest == "program.json":
        return "tests/fixtures/program.json"
    if path in ("docs/product-language.json", "docs/trust-destinations.json"):
        return "holdspeak/data/" + parts[-1]
    if path.startswith("apple/Tests/ContractsTests/Fixtures/"):
        return None  # the two files delivery06.test.tsx reads are copied by the web lead
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dest")
    ap.add_argument("--rev", default="tenvil-extraction-base")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    files = subprocess.run(
        ["git", "-C", str(REPO), "ls-tree", "-r", "-z", "--name-only", args.rev],
        check=True, capture_output=True,
    ).stdout.decode().split("\0")
    files = [f for f in files if f]
    plan = [(f, verdict(f)) for f in files]
    goes = [(s, d) for s, d in plan if d]

    counts = collections.Counter(d.split("/")[0] if "/" in d else "(root)" for _, d in goes)
    print(f"{args.rev}: {len(files)} tracked, {len(goes)} go, {len(files) - len(goes)} stay")
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {v:6d}  {k}")
    bad = [d for _, d in goes if PARKED.search(d)]
    if bad:
        print(f"REFUSED: {len(bad)} destination paths are in a _parked directory", file=sys.stderr)
        return 1
    if args.list:
        return 0

    dest = pathlib.Path(args.dest).resolve()
    if dest.exists() and any(p.name != ".git" for p in dest.iterdir()):
        print(f"REFUSED: {dest} is not empty", file=sys.stderr)
        return 1
    dest.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=os.path.join(tmp, "index"))
        subprocess.run(["git", "-C", str(REPO), "read-tree", args.rev], check=True, env=env)
        stage = pathlib.Path(tmp) / "tree"
        stage.mkdir()
        subprocess.run(
            ["git", "-C", str(REPO), "checkout-index", "-z", "--stdin", f"--prefix={stage}/"],
            input="\0".join(s for s, _ in goes).encode(), check=True, env=env,
        )
        for src, dst in goes:
            target = dest / dst
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(stage / src, target)
    print(f"copied {len(goes)} files to {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
