"""HS-200-46 — the load-bearing documentation claims, bound to the code.

Handover §7b used to be a hand-maintained table of sentences in this tree
that are false.  A hand-maintained list of lies rots exactly like the lies
it catalogues, so the list lives here instead, where every row carries an
executable predicate over the REAL module, the REAL file, or the REAL
generated surface.

Each :class:`Claim` is one sentence somebody wrote in a document:

* ``doc`` / ``anchor``  — where it lives, and a literal substring that must
  still be findable in that document.  A moved or deleted sentence fails the
  anchor test, so a row cannot quietly stop describing anything.
* ``sentence``          — the author's words, verbatim.
* ``predicate``        — a zero-arg callable.  ``True`` means the code
  satisfies the sentence.
* ``state``            — ``"holds"`` (the predicate must stay ``True``) or
  ``"known_false"`` (the predicate must stay ``False`` — and when it starts
  returning ``True``, the sentence must be corrected in the same commit and
  the row moved to ``holds``).
* ``truth``            — one sentence: what is actually true right now.  It
  is what the failure prints, so a reader can act without opening the test.
* ``story``            — the story that owns the repair, or ``""`` when no
  story does.

**A predicate never asserts against a value transcribed into this file.**
Counts are computed from the live server, pragmas are read off a real
connection, verb sets are parsed out of the real registry.  A transcribed
constant proves only that somebody can transcribe
(``reference_lying_test_doubles``).
"""
from __future__ import annotations

import importlib.util
import json
import re
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Claim:
    doc: str
    anchor: str
    sentence: str
    predicate: Callable[[], bool]
    state: str
    truth: str
    story: str = ""

    def path(self) -> Path:
        return REPO_ROOT / self.doc

    def anchor_line(self) -> int:
        """1-based line of ``anchor`` in ``doc``; 0 when it is not present."""
        try:
            text = self.path().read_text(encoding="utf-8")
        except OSError:
            return 0
        index = text.find(self.anchor)
        if index < 0:
            return 0
        return text.count("\n", 0, index) + 1

    @property
    def label(self) -> str:
        return f"{self.state}:{Path(self.doc).name}:{self.anchor_line()}"


# ---------------------------------------------------------------------------
# Real-surface readers.  Every one of these opens the tree or the runtime.
# ---------------------------------------------------------------------------

def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _strip_line_comments(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("//")
    )


def web_verb_registry_ids() -> set[str]:
    """The verb ids the face actually registers.

    ``web/src/desk/verbRegistry.ts`` is regex-parseable for its literal ids
    (``id: "desk.new-note"``), but the Go verbs are spread from
    ``DESK_TOOLS`` (``go.${tool.action}``), which is itself a filter over
    ``DESK_APPLICATIONS``.  So the derived half is parsed out of
    ``applications.ts``: one entry per top-level object, and only the
    entries whose ``group`` is ``app`` or ``tool`` reach ``DESK_TOOLS``
    (``web/src/desk/tools.ts:4-6``).  Both files are read from disk; no node
    or bundler is involved.
    """
    registry = _strip_line_comments(_read("web/src/desk/verbRegistry.ts"))
    ids = set(
        re.findall(r'^\s*id:\s*"([a-z][a-z0-9]*\.[a-z0-9-]+)"', registry, re.M)
    )
    apps = _strip_line_comments(_read("web/src/desk/applications.ts"))
    body = apps[apps.index("DESK_APPLICATIONS"):]
    for block in body.split("\n  },"):
        action = re.search(r'^\s{4}action:\s*"([a-z0-9-]+)"', block, re.M)
        group = re.search(r'^\s{4}group:\s*"(app|tool)"', block, re.M)
        if action and group:
            ids.add(f"go.{action.group(1)}")
    return ids


def mcp_verb_catalog_ids() -> set[str]:
    """The verb ids ``holdspeak://desk/verbs`` publishes, from the real module."""
    from holdspeak.mcp import resources

    return {str(row[0]) for row in resources._VERBS}


def _owner_principal():
    from holdspeak.principals import Principal, PrincipalKind

    return Principal(PrincipalKind.OWNER, "hs-200-46")


def desk_snapshot_keys() -> set[str]:
    """Keys of the real ``holdspeak://desk/snapshot`` payload."""
    from holdspeak.mcp import resources
    from holdspeak.runtime import composition

    # HS-200-45: MCP reads compose from the process's composition root. Under
    # pytest the conftest installs a bare root; `scripts/doc_claims.py` runs
    # outside pytest, so install one here for the duration of the read.
    mine = composition.installed() is None
    if mine:
        composition.install(composition.bare(label="doc-claims"))
    try:
        contents = resources.read_resource("holdspeak://desk/snapshot", _owner_principal())
    finally:
        if mine:
            composition.uninstall()
    payload = json.loads(contents["contents"][0]["text"])
    return set(payload) if isinstance(payload, dict) else set()


def mcp_resource_counts() -> dict[str, int]:
    """Static/template counts for owner and default non-owner discovery."""
    from holdspeak.mcp import resources

    owner = resources.list_resources(_owner_principal())
    other = resources.list_resources(None)
    return {
        "owner_static": len(owner["resources"]),
        "owner_templates": len(owner["resourceTemplates"]),
        "nonowner_static": len(other["resources"]),
        "nonowner_templates": len(other["resourceTemplates"]),
        "nonowner_total": len(other["resources"]) + len(other["resourceTemplates"]),
    }


def connection_pragmas() -> dict[str, Any]:
    """``PRAGMA`` values on a connection opened through the real factory."""
    from holdspeak.db.connection import connection

    db_path = Path(tempfile.mkdtemp(prefix="hs200-46-")) / "probe.db"
    with connection(db_path) as conn:
        return {
            "journal_mode": str(conn.execute("PRAGMA journal_mode").fetchone()[0]),
            "busy_timeout": int(conn.execute("PRAGMA busy_timeout").fetchone()[0]),
            "foreign_keys": int(conn.execute("PRAGMA foreign_keys").fetchone()[0]),
        }


def owner_remote_refusal_modules() -> set[str]:
    """Modules under ``holdspeak/web`` that refuse OWNER on a non-loopback request."""
    hits: set[str] = set()
    for path in sorted((REPO_ROOT / "holdspeak" / "web").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "PrincipalKind.OWNER" in line and "not is_loopback_host" in line:
                hits.add(path.relative_to(REPO_ROOT).as_posix())
    return hits


def bind_host_references() -> set[str]:
    """Python modules that mention ``bind_host`` at all."""
    hits: set[str] = set()
    for path in sorted((REPO_ROOT / "holdspeak").rglob("*.py")):
        if "bind_host" in path.read_text(encoding="utf-8"):
            hits.add(path.relative_to(REPO_ROOT).as_posix())
    return hits


def ux_canon_ceiling_a1() -> int:
    """The committed repo-wide A1 ceiling in ``tests/ux_canon_ceiling.json``."""
    data = json.loads(_read("tests/ux_canon_ceiling.json"))
    # The repo-wide ceiling is `per_rule`; `faces/<name>/A1` are per-face
    # sub-ceilings and must not be mistaken for it.
    return int(data["per_rule"]["A1"])


def raw_button_count() -> int:
    """Raw ``<button`` elements in ``web/src``, counting multi-line JSX.

    The canon scanner's A1 rule searches ``<button[\\s>/]`` on ONE line, so a
    ``<button`` that ends its line is invisible to it — the blind spot
    HS-200-44 owns.  This reader keeps the scanner's own exclusions (the
    library files ``Signal.tsx`` / ``gadgets.tsx``, and comment lines,
    ``scripts/ux_canon_scan.py:422-440``) and drops component tests, but uses
    ``<button\\b`` so an end-of-line tag counts.
    """
    root = REPO_ROOT / "web" / "src"
    total = 0
    for path in sorted(root.rglob("*.tsx")):
        rel = path.relative_to(root).as_posix()
        if "Signal.tsx" in rel or "gadgets.tsx" in rel or "__tests__" in rel:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.search(r"<button\b", line)
            if not match:
                continue
            stripped = line.strip()
            before = line[: match.start()]
            if stripped.startswith(("//", "*", "/*", "{/*")):
                continue
            if "//" in before or "{/*" in before:
                continue
            total += 1
    return total


def canon_scanner_a1_total() -> int:
    """The A1 count the real canon scanner reports over the live tree."""
    script = REPO_ROOT / "scripts" / "ux_canon_scan.py"
    spec = importlib.util.spec_from_file_location("hs200_46_ux_canon_scan", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return int(module.scan(REPO_ROOT)["totals"]["per_rule"].get("A1", 0))


def ghost_layout_keys() -> list[str]:
    """``GHOST_LAYOUT_KEYS`` as the face declares it."""
    text = _read("web/src/desk/store/types.ts")
    block = re.search(r"GHOST_LAYOUT_KEYS = \[(.*?)\]", text, re.S)
    return re.findall(r'"([^"]+)"', block.group(1)) if block else []


def live_workspace_storage_key() -> str:
    """The layout key the store actually reads and writes."""
    text = _read("web/src/desk/store/workspaceStorage.ts")
    match = re.search(r'DESK_WORKSPACE_STORAGE_KEY\s*=\s*"([^"]+)"', text)
    return match.group(1) if match else ""


def retired_layout_key_readers(key: str) -> set[str]:
    """Files under ``web/src`` that mention ``key`` outside the ghost list/tests."""
    root = REPO_ROOT / "web" / "src"
    hits: set[str] = set()
    for path in sorted(root.rglob("*.ts*")):
        rel = path.relative_to(root).as_posix()
        if "__tests__" in rel or rel == "desk/store/types.ts":
            continue
        if key in path.read_text(encoding="utf-8"):
            hits.add(rel)
    return hits


def mcp_json_servers() -> set[str]:
    """Server names declared in the repo's ``.mcp.json``."""
    payload = json.loads(_read(".mcp.json"))
    return set(payload.get("mcpServers", {}))


def deskos_component_pattern_web_references() -> set[str]:
    """``web/src`` paths the DeskOS component-pattern doc names."""
    text = _read("docs/internal/DESKOS_COMPONENT_PATTERN.md")
    return set(re.findall(r"web/src/[A-Za-z0-9_./-]+", text))


def handle_message_for_principal_parameters() -> set[str]:
    """Parameter names of the MCP entry point the HTTP route calls."""
    import inspect

    from holdspeak.mcp.server import handle_message_for_principal

    return set(inspect.signature(handle_message_for_principal).parameters)


def intel_queue_worker_production_callers() -> set[str]:
    """Non-test, non-script modules that start the intel queue worker chain."""
    hits: set[str] = set()
    for path in sorted((REPO_ROOT / "holdspeak").rglob("*.py")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel.startswith("holdspeak/intel_queue"):
            continue  # the queue modules themselves are not callers
        text = path.read_text(encoding="utf-8")
        if "start_intel_queue_conductor(" in text or "start_intel_queue_worker(" in text:
            hits.add(rel)
    return hits


def undelete_clears_unavailable() -> str:
    """Drive the REAL schema: what does an undelete leave in ``stale_reason``?"""
    from holdspeak.db.schema import SCHEMA_SQL

    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(SCHEMA_SQL)
        conn.execute("INSERT INTO notes (id, deleted) VALUES ('hs20046', 0)")
        conn.execute(
            "INSERT INTO context_dependents "
            "(canonical_ref, consumer_kind, consumer_id, bound_at) "
            "VALUES ('note:hs20046', 'thought', 't1', datetime('now'))"
        )
        conn.execute("UPDATE notes SET deleted = 1 WHERE id = 'hs20046'")
        marked = conn.execute("SELECT stale_reason FROM context_dependents").fetchone()[0]
        assert marked == "unavailable", marked
        conn.execute("UPDATE notes SET deleted = 0 WHERE id = 'hs20046'")
        return str(conn.execute("SELECT stale_reason FROM context_dependents").fetchone()[0])
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# The registry.
# ---------------------------------------------------------------------------

def reconcile_backup_follows_bookmarks_repair() -> bool:
    """Observe the real reconcile call order on a disposable missing-table DB.

    The backup spy reads the actual connection's shape at invocation. It does
    not assume a source line order or turn a backup call into pre-change proof.
    """
    from unittest.mock import patch
    from holdspeak.db.schema import SCHEMA_SQL
    from holdspeak.db.reconcile import reconcile_schema

    with tempfile.TemporaryDirectory(prefix="philo-reconcile-") as tmp:
        path = Path(tmp) / "probe.db"
        conn = sqlite3.connect(path)
        try:
            conn.executescript(SCHEMA_SQL)
            conn.execute("DROP TABLE bookmarks")
            conn.commit()
            observed = []

            def inspect_at_backup(_path):
                observed.append(conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='bookmarks'"
                ).fetchone() is not None)
                return Path(tmp) / "probe.bak"

            with patch("holdspeak.db.core.backup_database", inspect_at_backup):
                reconcile_schema(conn, db_path=path)
            return observed == [True]
        finally:
            conn.close()


def gate_preview_preserves_short_secret_marker() -> bool:
    from holdspeak.coder_gate import redact_args

    payload = {"command": "TOKEN=philo-synthetic-marker echo ok"}
    canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
    _digest, head = redact_args(payload)
    return head == canonical and "philo-synthetic-marker" in head


def kernel_parent_snapshot_retains_prompt() -> bool:
    from holdspeak.db import Database
    from holdspeak.kernel.runtime import _configure
    from holdspeak.principals import Principal, PrincipalKind

    with tempfile.TemporaryDirectory(prefix="philo-parent-") as tmp:
        database = Database(Path(tmp) / "parent.db")
        broker = _configure(database, clock=lambda: 1000.0)
        try:
            parent = broker.parent_run_controller.start(
                Principal(PrincipalKind.OWNER, "philo-probe"), kind="sequence",
                definition_ref="sequence:philo", definition_revision="1",
                input_snapshot={"prompt": "philo synthetic prompt"},
                deadline_at=2000.0, child_budget=0,
            )
            with database._connection() as conn:
                row = conn.execute("SELECT input_json FROM kernel_parent_runs WHERE operation_id=?", (parent.operation_id,)).fetchone()
            return json.loads(row["input_json"]) == {"prompt": "philo synthetic prompt"}
        finally:
            broker.parent_run_controller.shutdown()
            database.close()


CLAIMS: list[Claim] = [
    Claim(
        doc="docs/STORAGE_AND_MIGRATIONS.md",
        anchor="`kernel_parent_runs.input_json` stores caller input",
        sentence="kernel_parent_runs.input_json stores caller input snapshots.",
        predicate=kernel_parent_snapshot_retains_prompt,
        state="holds",
        truth="A real admitted Sequence parent stores a synthetic prompt in input_json in a disposable database.",
        story="PHILO-1-02",
    ),
    Claim(
        doc="docs/SECURITY_MODEL.md",
        anchor="Gate argument previews truncate canonical JSON; they do not remove secrets.",
        sentence="Gate argument previews truncate canonical JSON; they do not remove secrets.",
        predicate=gate_preview_preserves_short_secret_marker,
        state="holds",
        truth="A short synthetic tool input survives intact in the returned prefix, including its credential-like marker.",
        story="PHILO-1-04",
    ),
    Claim(
        doc="docs/STORAGE_AND_MIGRATIONS.md",
        anchor="bookmarks table, the table is recreated before the automatic backup is called.",
        sentence="For a missing bookmarks table, the table is recreated before the automatic backup is called.",
        predicate=reconcile_backup_follows_bookmarks_repair,
        state="holds",
        truth="The actual reconciliation recreates bookmarks before invoking the backup spy; automatic backup is not an original-shape guarantee.",
        story="PHILO-1-02",
    ),
    # ── paid by HS-200-45 (2026-09-17) ───────────────────────────────
    Claim(
        doc="holdspeak/web/routes/mcp_http.py",
        anchor="installs its composed services as the\nprocess's ONE composition root",
        sentence=(
            "``MeetingWebServer._create_app`` installs its composed services as the "
            "process's ONE composition root (``holdspeak/runtime/composition.py``); "
            "``tools.dispatch`` and every MCP family read that root."
        ),
        predicate=lambda: (
            "composition.install_from_web_context(" in _read("holdspeak/web_server.py")
            and "get_database()" not in _read("holdspeak/mcp/tools.py")
            and not [
                path
                for path in sorted(REPO_ROOT.glob("holdspeak/mcp/families/*.py"))
                if "get_database()" in path.read_text(encoding="utf-8")
            ]
        ),
        state="holds",
        truth=(
            "web_server.py installs the hub's services through "
            "holdspeak.runtime.composition.install_from_web_context; tools.py and "
            "every families/*.py resolve db/observer/services through that root "
            "(db_or/observer_or/runtime_service) and call get_database() nowhere"
        ),
        story="HS-200-45",
    ),
    Claim(
        doc="holdspeak/db/connection.py",
        anchor="the connection protocol lives in one place: the\nthree pragmas",
        sentence=(
            "Extracted from ``Database`` so the connection protocol lives in one "
            "place: the three pragmas, the row factory, and commit-on-clean-exit / "
            "rollback-on-raise."
        ),
        predicate=lambda: (
            connection_pragmas()["journal_mode"].lower() == "wal"
            and int(connection_pragmas()["busy_timeout"]) == 5000
            and int(connection_pragmas()["foreign_keys"]) == 1
        ),
        state="holds",
        truth=(
            "a connection opened through this factory reports journal_mode=wal, "
            "busy_timeout=5000 and foreign_keys=1, all three set by _apply_pragmas "
            "(HS-200-45 R5; before it, journal_mode was delete and only foreign_keys "
            "was set)"
        ),
        story="HS-200-45",
    ),
    # ── unowned: the remote bind is still decorative ───────────────────
    Claim(
        doc="docs/SECURITY.md",
        anchor="is stored without a listener or peer-address enforcement path.",
        sentence="The configured bind_host is stored without a listener or peer-address enforcement path.",
        predicate=lambda: bind_host_references() == {"holdspeak/web/routes/mcp_http.py"},
        state="holds",
        truth="Only the MCP settings route mentions bind_host; it stores and echoes the value without applying a network fence.",
        story="PHILO-1-06",
    ),
    # ── owned by HS-200-44 ────────────────────────────────────────────
    Claim(
        doc="docs/internal/UX-CANON.md",
        anchor="A1 (raw `<button>`) is held to a\ndated, down-only ratchet of 106, measured on 2026-09-21 by HS-202-03",
        sentence=(
            "A1 (raw `<button>`) is held to a dated, down-only ratchet of 106, "
            "measured on 2026-09-21 by HS-202-03 (175 on 2026-09-17 by HS-200-44, "
            "once the matcher could see a multi-line opening tag). That number "
            "can only shrink."
        ),
        predicate=lambda: (
            ux_canon_ceiling_a1() == 106
            and int(re.search(r"down-only ratchet of (\d+)", _read("docs/internal/UX-CANON.md")).group(1))
            == ux_canon_ceiling_a1()
            and canon_scanner_a1_total() <= ux_canon_ceiling_a1()
        ),
        state="holds",
        truth=(
            "tests/ux_canon_ceiling.json holds A1 = 106 with a dated reason, the "
            "canon scanner's A1 count over web/src is at or under it, and the "
            "document states the same number. Lowered 175 -> 106 on 2026-09-21 by "
            "HS-202-03 (the shared species on the first-use path became library "
            "Buttons); the row is re-pinned to the new number so the predicate "
            "keeps the down-only law honest. Corrected 2026-09-17 by HS-200-44"
        ),
        story="HS-202-03",
    ),
    # Philo corrects known descriptive drift without adding missing behavior.
    Claim(
        doc="holdspeak/mcp/resources.py",
        anchor="# Curated subset of web/src/desk/verbRegistry.ts; it does not promise full parity.",
        sentence="Curated subset of web/src/desk/verbRegistry.ts; it does not promise full parity.",
        predicate=lambda: bool(mcp_verb_catalog_ids()) and mcp_verb_catalog_ids() <= web_verb_registry_ids(),
        state="holds",
        truth="The published MCP IDs are a subset of the resolved Web verb IDs; completeness is not claimed.",
        story="PHILO-1-06",
    ),
    Claim(
        doc="holdspeak/mcp/resources.py",
        anchor="Saved Desk records: chains, decisions, directories, notes, profiles, workbenches and workflows.",
        sentence="Saved Desk records: chains, decisions, directories, notes, profiles, workbenches and workflows.",
        predicate=lambda: desk_snapshot_keys() == {"chains", "decisions", "directories", "notes", "profiles", "workbenches", "workflows"},
        state="holds",
        truth="The real snapshot contains those seven record lists; layout and window state are not advertised.",
        story="PHILO-1-06",
    ),
    Claim(
        doc="docs/internal/DESKOS_COMPONENT_PATTERN.md",
        anchor="Status: SwiftUI iPad-specific guidance, not the current Web Desk contract.",
        sentence="Status: SwiftUI iPad-specific guidance, not the current Web Desk contract.",
        predicate=lambda: "apple/App/MeetingCapture/DeskDioramaStage.swift" in _read("docs/internal/DESKOS_COMPONENT_PATTERN.md") and not deskos_component_pattern_web_references(),
        state="holds",
        truth="The preserved pattern describes its SwiftUI iPad reference and is explicitly scoped away from the Web Desk.",
        story="PHILO-1-06",
    ),
    Claim(
        doc="CLAUDE.md",
        anchor="The repository `.mcp.json` declares only the `holdspeak` server; Delivery",
        sentence="The repository `.mcp.json` declares only the `holdspeak` server; Delivery Workbench MCP is not enabled in that file.",
        predicate=lambda: set(mcp_json_servers()) == {"holdspeak"},
        state="holds",
        truth=(
            ".mcp.json declares exactly one server, 'holdspeak'; dw-mcp is not wired "
            "there and the omission is intentional (corrected 2026-09-17, HS-200-46)"
        ),
        story="HS-200-46",
    ),
    # ── corrected by this story ───────────────────────────────────────
    Claim(
        doc="docs/USER_GUIDE.md",
        anchor="`POST /api/mcp` the owner's web token is refused on a non-loopback request",
        sentence=(
            "On `POST /api/mcp` the owner's web token is refused on a non-loopback "
            "request; no other route applies that refusal."
        ),
        predicate=lambda: owner_remote_refusal_modules()
        == {"holdspeak/web/routes/mcp_http.py"},
        state="holds",
        truth=(
            "exactly one module under holdspeak/web refuses an OWNER principal on a "
            "non-loopback request: holdspeak/web/routes/mcp_http.py:93"
        ),
        story="",
    ),
    Claim(
        doc="docs/internal/DESK_GRAMMAR.md",
        anchor="THE WINDOW REMEMBERS — view,\n   sort, direction per zone and the open set (`hs.desk.workspace.v1`)",
        sentence=(
            "THE WINDOW REMEMBERS — view, sort, direction per zone and the open set "
            "(`hs.desk.workspace.v1`), rect via panels — and restores. The older "
            "`hs.desk.zone-views` / `hs.desk.zone-windows` keys are retired: they "
            "survive in `GHOST_LAYOUT_KEYS` so a reset still sweeps them, and nothing "
            "reads them."
        ),
        predicate=lambda: (
            live_workspace_storage_key() == "hs.desk.workspace.v1"
            and {"hs.desk.zone-views", "hs.desk.zone-windows"} <= set(ghost_layout_keys())
            and not retired_layout_key_readers("hs.desk.zone-windows")
            and not retired_layout_key_readers("hs.desk.zone-views")
        ),
        state="holds",
        truth=(
            "DESK_WORKSPACE_STORAGE_KEY in web/src/desk/store/workspaceStorage.ts is "
            "'hs.desk.workspace.v1'; both zone-* keys appear in web/src only inside "
            "GHOST_LAYOUT_KEYS (and its tests)"
        ),
        story="",
    ),
    Claim(
        doc="docs/MCP_SIDECAR.md",
        anchor="Owner discovery exposes 16 static resources and 21 resource templates.",
        sentence=(
            "Owner discovery exposes 16 static resources and 21 resource templates. "
            "The default non-owner discovery filters that to 15 static resources and "
            "19 templates, or 34 total."
        ),
        predicate=lambda: _sidecar_counts_match_doc(),
        state="holds",
        truth=(
            "the sentence's four numbers are read back out of the document and "
            "compared to holdspeak.mcp.resources.list_resources for OWNER and for the "
            "default non-owner principal, so they cannot drift again silently"
        ),
        story="",
    ),
    Claim(
        doc="holdspeak/db/schema.py",
        anchor="1. `unavailable` -> `stale` on an undelete is DELIBERATE.",
        sentence=(
            "`unavailable` -> `stale` on an undelete is DELIBERATE. The AU branch "
            "below reaches 'stale' only when NEW.deleted = 0 -- the record genuinely "
            "came back -- so the refresh a consumer would attempt CAN succeed."
        ),
        predicate=lambda: undelete_clears_unavailable() == "stale",
        state="holds",
        truth=(
            "driving the real SCHEMA_SQL: marking a note deleted sets "
            "context_dependents.stale_reason='unavailable', and undeleting it leaves "
            "'stale'"
        ),
        story="",
    ),
    Claim(
        doc="pm/roadmap/holdspeak/phase-172-the-loop-closes/assets/settled-design-loop-closes.md",
        anchor="**FALSE — corrected 2026-09-14 (HS-200-42).**",
        sentence=(
            "FALSE — corrected 2026-09-14 (HS-200-42). The paragraph above was wrong "
            "when it was written and is kept only as the record of where the defect "
            "entered. ... `IntelQueueWorker` had zero production callers until "
            "HS-200-42."
        ),
        predicate=lambda: bool(intel_queue_worker_production_callers()),
        state="holds",
        truth=(
            "HS-200-42 gave the worker a production caller: holdspeak/web_server.py "
            "calls start_intel_queue_conductor, which starts "
            "start_intel_queue_worker (holdspeak/intel_queue_conductor.py:138)"
        ),
        story="",
    ),

    # ── paid by HS-200-17 (the prepared-recipe catalog) ──────────────
    Claim(
        doc="docs/USER_GUIDE.md",
        anchor="A descriptor declares a limit only where one is real.",
        sentence=(
            "A descriptor declares a limit only where one is real. Where "
            "the executing service enforces a cap, the descriptor points at "
            "that service's own value and reads it rather than repeating "
            "the number. Where no cap exists, it declares none. The same "
            "rule covers inputs: none of the three offers a setting no step "
            "can act on."
        ),
        predicate=lambda: _prepared_recipes_declare_nothing_unreadable(),
        state="holds",
        truth=(
            "no descriptor carries a literal: limit or an input that no "
            "step binds (recipe_catalog.unreachable_declarations is empty "
            "for all three), and weekly_update declares no limits at all "
            "because ProjectUpdateService enforces no claim cap"
        ),
        story="HS-200-17",
    ),
    Claim(
        doc="docs/USER_GUIDE.md",
        anchor="Three prepared procedures ship",
        sentence=(
            "Three prepared procedures ship: meeting preparation, decision "
            "and commitment review, and the weekly project update. Each is a "
            "versioned descriptor in the product tree, bound to the service "
            "that already does the work."
        ),
        predicate=lambda: _prepared_catalog_is_the_declared_three(),
        state="holds",
        truth=(
            "holdspeak/services/recipe_catalog.py holds exactly "
            "preparation_brief, decision_review and weekly_update, and every "
            "execution step of all three imports to a real method on a "
            "service that shipped before HS-200-17"
        ),
        story="HS-200-17",
    ),
    Claim(
        doc="docs/USER_GUIDE.md",
        anchor="**None of the three fires on a schedule yet.**",
        sentence=(
            "None of the three fires on a schedule yet. All three name the "
            "same owner path, the one that really recurs in this product: "
            "a connector watch on its evaluation interval, swept by the "
            "Heartbeat, whose due evaluation mints an effect the steward "
            "drains for that project. No effect kind names one of these "
            "three yet."
        ),
        predicate=lambda: _no_prepared_recipe_has_a_wired_schedule(),
        state="holds",
        truth=(
            "every descriptor's TRIGGER_SCHEDULED binding names the "
            "connector_watches -> run_sweep -> evaluate_due -> "
            "project.steward.run_once -> run_due chain and carries "
            "available=False, so compiling under it yields a "
            "trigger_owner_not_wired gap; CadenceService still exposes no "
            "create/schedule verb and cadence_loops carries no next-fire "
            "column; and no module in that chain imports recipe_catalog. "
            "The day one of them does, this predicate goes False and the "
            "sentence must be corrected in the same commit"
        ),
        story="HS-200-17",
    ),

    # ── PHILO-2-07: the council's three doc-drift lines ──────────────
    Claim(
        doc="web/src/desk/useDeskChangedRefresh.ts",
        anchor="Meeting changes announce themselves from the import worker",
        sentence=(
            "Meeting changes announce themselves from the import worker when an "
            "import ends, success or failure (`MeetingService._run_import_job`), "
            "and from the summary queue after durable running and settled "
            "transitions (`_notify_queue_meeting_changed`). Other meeting writes, "
            "project rooms, thoughts and sync emit no frame; their surfaces "
            "carry their own signals."
        ),
        predicate=lambda: desk_changed_comment_holds(),
        state="holds",
        truth=(
            "literal-kind 'meeting' desk_changed calls under holdspeak/ are in "
            "MeetingService._run_import_job and _notify_queue_meeting_changed; "
            "real-producer queue fences verify durable running and settled "
            "publication. No literal thought/project/room/sync kind exists "
            "(PHILO-3-02, updated 2026-09-23)"
        ),
        story="PHILO-3-02",
    ),
    Claim(
        doc="docs/internal/philo/data/voice.json",
        anchor='Models window verb \\"Use this for summaries\\"',
        sentence=(
            "model.assignment: exposure user; surfaces: arrival SETUP row \"No "
            "engine for summaries\" (opens Models); Models window verb \"Use this "
            "for summaries\"."
        ),
        predicate=lambda: model_assignment_exposure_holds(),
        state="holds",
        truth=(
            "the record's exposure is 'user'; ConciergeCore.tsx:571 draws 'Use this "
            "for summaries', whose handler useNewEngineForSummaries calls "
            "conciergeSummarySelection; meetingPathBlocker.ts:95 states 'No engine "
            "for summaries' for the arrival's SETUP row (ChairHome.tsx:953). The "
            "owner has not observed it (fnd.docs.model_assignment_exposure, "
            "corrected 2026-09-22)"
        ),
        story="PHILO-2-07",
    ),
    Claim(
        doc="docs/internal/philo/briefs/live-pass-lane-brief.md",
        anchor="the SET_ENGINE chain fills the atlas address `http://192.168.1.43:8080`, unchanged",
        sentence=(
            "the SET_ENGINE chain fills the atlas address `http://192.168.1.43:8080`, "
            "unchanged (corrected by PHILO-2-07: this line named `…:8080/v1` when "
            "both live passes ran ...)"
        ),
        predicate=lambda: lane_brief_engine_address_holds(),
        state="holds",
        truth=(
            "every LAN engine address in docs/internal/philo/graph/atlas.json is "
            "http://192.168.1.43:8080, the address the brief now names "
            "(fnd.live.lane_brief_engine_address, corrected 2026-09-22)"
        ),
        story="PHILO-2-07",
    ),
]


def _prepared_recipes_declare_nothing_unreadable() -> bool:
    """No invented limit, no orphaned input (HS-200-17 ruling R17-10)."""
    from holdspeak.services import recipe_catalog as catalog

    return all(
        catalog.unreachable_declarations(descriptor) == []
        for descriptor in catalog.list_descriptors()
    )


def _prepared_catalog_is_the_declared_three() -> bool:
    """The catalog holds those three ids and every step really resolves."""
    from holdspeak.services import recipe_catalog as catalog

    if sorted(catalog.CATALOG) != sorted(
        (
            catalog.RECIPE_PREPARATION_BRIEF,
            catalog.RECIPE_DECISION_REVIEW,
            catalog.RECIPE_WEEKLY_UPDATE,
        )
    ):
        return False
    try:
        for descriptor in catalog.list_descriptors():
            for step in descriptor.steps:
                catalog.resolve_step(step)
    except catalog.CatalogError:
        return False
    return True


def _no_prepared_recipe_has_a_wired_schedule() -> bool:
    """True while no descriptor claims an unattended firing it cannot make.

    Also checks the two owners the sentence rules OUT, against the real
    class and the real schema rather than against this file's memory of
    them (HS-200-17 ruling R17-8).
    """
    from holdspeak.db import schema
    from holdspeak.services import recipe_catalog as catalog
    from holdspeak.services.cadence_service import CadenceService

    for descriptor in catalog.list_descriptors():
        binding = descriptor.trigger(catalog.TRIGGER_SCHEDULED)
        if binding is None or binding.available:
            return False
        if binding.owner != catalog.SCHEDULED_TRIGGER_OWNER:
            return False
    for link in (
        "connector_watches", "HeartbeatService.run_sweep",
        "WatchService.evaluate_due", "project.steward.run_once",
        "ProjectStewardService.run_due",
    ):
        if link not in catalog.SCHEDULED_TRIGGER_OWNER:
            return False
    verbs = {name for name in dir(CadenceService) if not name.startswith("_")}
    if verbs & {"create", "create_loop", "schedule", "set_schedule"}:
        return False
    loops = schema.SCHEMA_SQL.split(
        "CREATE TABLE IF NOT EXISTS cadence_loops"
    )[1].split(");")[0]
    if any(
        column in loops
        for column in ("next_evaluation_at", "next_fire_at", "rrule")
    ):
        return False

    # The direct check on the event the sentence actually describes: no
    # module in the recurring chain reaches the prepared-recipe catalog.
    # Without this the predicate only proved the descriptors still SAY
    # available=False, which a builder could forget to flip.
    for relative in (
        "holdspeak/runtime/heartbeat.py",
        "holdspeak/services/heartbeat_service.py",
        "holdspeak/services/watch_service.py",
        "holdspeak/services/project_steward_service.py",
    ):
        if "recipe_catalog" in _read(relative):
            return False
    return True


def _sidecar_counts_match_doc() -> bool:
    """Compare the four counts written in MCP_SIDECAR.md to the live server.

    The numbers are parsed back OUT of the document rather than typed here, so
    editing the prose without re-measuring fails, and a change in the real
    resource list fails too.
    """
    text = _read("docs/MCP_SIDECAR.md")
    match = re.search(
        r"Owner discovery exposes (\d+) static resources and (\d+) resource templates\."
        r"\s+The\s+default non-owner discovery filters that to (\d+) static resources and\s+"
        r"(\d+) templates, or (\d+) total\.",
        text,
    )
    if not match:
        return False
    written = [int(group) for group in match.groups()]
    live = mcp_resource_counts()
    return written == [
        live["owner_static"],
        live["owner_templates"],
        live["nonowner_static"],
        live["nonowner_templates"],
        live["nonowner_total"],
    ]


# ---------------------------------------------------------------------------
# PHILO-2-07 — the three doc-drift lines the PHILO-2-06 council named
# (docs/internal/philo/graph/COUNCIL.md, "Findings restored, split or
# narrowed"; council-resolutions.json res.docs_*).  Each sentence was corrected
# to the current truth in the same commit that added its row.
# ---------------------------------------------------------------------------

_DESK_CHANGED_CALLS = {"notify_desk_changed", "emit_desk_changed"}


def desk_changed_literal_kinds() -> dict[str, set[tuple[str, str]]]:
    """Every ``desk_changed`` announcement under holdspeak/ whose kind is a
    string literal: kind -> {(file, innermost enclosing function)}.

    Parsed out of the real modules with ``ast``; a variable kind (the
    composed services' own frames) is not a literal and is not collected.
    """
    import ast

    found: dict[str, set[tuple[str, str]]] = {}
    for path in sorted((REPO_ROOT / "holdspeak").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if "desk_changed" not in text:
            continue
        rel = str(path.relative_to(REPO_ROOT))

        class Visitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.stack: list[str] = []

            def _function(self, node: ast.AST) -> None:
                self.stack.append(node.name)  # type: ignore[attr-defined]
                self.generic_visit(node)
                self.stack.pop()

            visit_FunctionDef = _function
            visit_AsyncFunctionDef = _function

            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
                if (
                    name in _DESK_CHANGED_CALLS
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                ):
                    where = self.stack[-1] if self.stack else "<module>"
                    found.setdefault(node.args[0].value, set()).add((rel, where))
                self.generic_visit(node)

        Visitor().visit(ast.parse(text))
    return found


def desk_changed_comment_holds() -> bool:
    """The corrected useDeskChangedRefresh comment, against the real emitters."""
    kinds = desk_changed_literal_kinds()
    if kinds.get("meeting") != {
        ("holdspeak/services/meeting_service.py", "_run_import_job"),
        ("holdspeak/intel_queue.py", "_notify_queue_meeting_changed"),
    }:
        return False
    if set(kinds) & {"thought", "thoughts", "project", "project_room", "room", "sync"}:
        return False
    return True


def _philo_record(shard: str, record_id: str) -> dict[str, Any]:
    document = json.loads(_read(shard))
    for records in document.values():
        if isinstance(records, list):
            for record in records:
                if isinstance(record, dict) and record.get("id") == record_id:
                    return record
    raise KeyError(record_id)


def model_assignment_exposure_holds() -> bool:
    """``model.assignment`` is recorded as a user capability, and every quoted
    face word in its surfaces is really drawn by one of its cited web sources."""
    record = _philo_record("docs/internal/philo/data/voice.json", "model.assignment")
    if record.get("exposure") != "user":
        return False
    web = [s["path"] for s in record.get("sources", []) if s["path"].startswith("web/src/")]
    if not web:
        return False
    texts = [_read(path) for path in web]
    for surface in record.get("surfaces", []):
        words = re.findall(r'"([^"]+)"', surface)
        if not words:
            return False
        if not all(any(word in text for text in texts) for word in words):
            return False
    # The Models verb really writes the summary assignment.
    controller = _read("web/src/features/concierge/useConciergeController.ts")
    body = controller.split("const useNewEngineForSummaries = useCallback", 1)
    return len(body) == 2 and "conciergeSummarySelection(" in body[1].split("\n  }, [", 1)[0]


def lane_brief_engine_address_holds() -> bool:
    """The lane brief names exactly the LAN address every atlas step fills."""
    brief = _read("docs/internal/philo/briefs/live-pass-lane-brief.md")
    match = re.search(r"fills the atlas address `([^`]+)`", brief)
    if not match:
        return False

    values: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, str) and re.match(r"https?://192\.168\.1\.43[:/]", node):
            values.add(node)

    walk(json.loads(_read("docs/internal/philo/graph/atlas.json")))
    return values == {match.group(1)}


# ---------------------------------------------------------------------------
# HS-200-46, 2026-09-17 — the dated, down-only known_false ratchet.
#
# Thirteen load-bearing sentences were measured against this tree (43's tip)
# on 2026-09-17.  Eight of them are FALSE and are recorded here so the fence
# reports a NEW lie instead of failing the same way forever, exactly as
# HS-200-03 converted the product-copy, broker-density and driver-conditional
# fences.  The ratchet is down-only: the live known_false count may shrink
# (fix the code, correct the sentence, move the row to `holds`), and it may
# NOT grow past this number without a commit that changes the reason string
# below to name the new debt and why it is being admitted.
#
# Philo corrected the four remaining descriptions without claiming that the
# missing listener fence, catalogue parity or layout projection was implemented.
KNOWN_FALSE_RATCHET = 0
KNOWN_FALSE_RATCHET_DATE = "2026-09-19"
KNOWN_FALSE_RATCHET_REASON = (
    "Philo corrected the MCP listener, verb catalogue and snapshot descriptions "
    "and scoped the SwiftUI iPad pattern away from the Web Desk. No missing runtime "
    "capability was added or claimed. The known-false ceiling is now zero."
)


def known_false_claims() -> list[Claim]:
    return [claim for claim in CLAIMS if claim.state == "known_false"]


def holding_claims() -> list[Claim]:
    return [claim for claim in CLAIMS if claim.state == "holds"]


def markdown_table() -> str:
    """The registry as the markdown table handover §7b used to carry."""
    rows = [
        "| State | Where | What it claims | What is true |",
        "|---|---|---|---|",
    ]
    for claim in CLAIMS:
        line = claim.anchor_line()
        where = f"`{claim.doc}:{line}`" if line else f"`{claim.doc}` (ANCHOR MISSING)"
        state = claim.state.upper().replace("_", " ")
        if claim.story:
            state = f"{state} ({claim.story})"
        sentence = " ".join(claim.sentence.split()).replace("|", "\\|")
        truth = " ".join(claim.truth.split()).replace("|", "\\|")
        rows.append(f"| {state} | {where} | {sentence} | {truth} |")
    return "\n".join(rows)
