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

    contents = resources.read_resource("holdspeak://desk/snapshot", _owner_principal())
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

CLAIMS: list[Claim] = [
    # ── owned by HS-200-45 ────────────────────────────────────────────
    Claim(
        doc="holdspeak/web/routes/mcp_http.py",
        anchor="composing on\nthe web runtime's LIVE services (never the sidecar's bare serve() instances)",
        sentence=(
            "JSON-RPC in -> handle_message_for_principal -> JSON-RPC out, composing "
            "on the web runtime's LIVE services (never the sidecar's bare serve() "
            "instances)."
        ),
        predicate=lambda: bool(
            handle_message_for_principal_parameters()
            & {"services", "runtime", "container", "composition", "context"}
        ),
        state="known_false",
        truth=(
            "the route calls holdspeak.mcp.server.handle_message_for_principal, whose "
            "only parameters are "
            "{request, principal, palette} — no live-services handle is threaded in, "
            "so it composes exactly as the sidecar's serve() does"
        ),
        story="HS-200-45",
    ),
    Claim(
        doc="holdspeak/db/connection.py",
        anchor="the connection protocol (WAL pragmas, row factory,",
        sentence=(
            "Extracted from ``Database`` so the connection protocol (WAL pragmas, "
            "row factory, commit/rollback) lives in one place."
        ),
        predicate=lambda: connection_pragmas()["journal_mode"].lower() == "wal",
        state="known_false",
        truth=(
            "a connection opened through this factory reports journal_mode=delete; the "
            "module sets only PRAGMA foreign_keys=ON, and the 5000ms busy_timeout it "
            "reports is sqlite3.connect's own timeout=5.0 default, not a pragma this "
            "module applies"
        ),
        story="HS-200-45",
    ),
    Claim(
        doc="docs/SECURITY.md",
        anchor="it accepts\nconnections on the tailnet address only",
        sentence=(
            "The Streamable HTTP listener (`POST /api/mcp`) is opt-in and off by "
            "default. When enabled, it accepts connections on the tailnet address only."
        ),
        predicate=lambda: bool(
            bind_host_references() - {"holdspeak/web/routes/mcp_http.py"}
        ),
        state="known_false",
        truth=(
            "bind_host is stored and echoed by the settings route in "
            "holdspeak/web/routes/mcp_http.py and mentioned by no other module, so "
            "nothing applies it to a bind or a peer check; the package's only "
            "tailnet CIDR (100.64.0.0/10, concierge_service.py:297) is an "
            "egress-advice helper, not a listener fence"
        ),
        story="HS-200-45",
    ),
    # ── owned by HS-200-44 ────────────────────────────────────────────
    Claim(
        doc="docs/internal/UX-CANON.md",
        anchor="A1 (raw `<button>`) must stay within\na named allowlist (4 residues with reasons)",
        sentence=(
            "(ii) *Hard zeros*: DS6 (accent rail) and A9 (missing egress) must stay "
            "at 0; A1 (raw `<button>`) must stay within a named allowlist (4 residues "
            "with reasons)."
        ),
        predicate=lambda: raw_button_count() <= 4,
        state="known_false",
        truth=(
            "the live web/src tree holds 203 raw <button> elements outside the Signal/"
            "gadgets library files; the canon scanner sees 4 of them because its A1 "
            "regex requires a character after `<button` on the same line, so every "
            "multi-line JSX tag is invisible to it"
        ),
        story="HS-200-44",
    ),
    # ── no story owns these ───────────────────────────────────────────
    Claim(
        doc="holdspeak/mcp/resources.py",
        anchor="# Mirrors web/src/desk/verbRegistry.ts, including verbs derived from DESK_TOOLS.",
        sentence=(
            "Mirrors web/src/desk/verbRegistry.ts, including verbs derived from "
            "DESK_TOOLS."
        ),
        predicate=lambda: mcp_verb_catalog_ids() == web_verb_registry_ids(),
        state="known_false",
        truth=(
            "the face registers 67 verbs and the catalog publishes 45: 22 registry "
            "verbs are missing from the catalog (the nine desk.* intelligence/thread/"
            "project verbs, go.change-places, go.open-project-memory, "
            "object.continue-in-thread and the ten thread.* verbs) and the catalog "
            "holds no phantoms — the audit's '13 phantoms' were the DESK_TOOLS-derived "
            "go.* verbs it did not resolve"
        ),
        story="",
    ),
    Claim(
        doc="holdspeak/mcp/resources.py",
        anchor='"description": "Canonical current Desk state, including its stored objects and layout."',
        sentence=(
            "Canonical current Desk state, including its stored objects and layout."
        ),
        predicate=lambda: bool(
            {
                key
                for key in desk_snapshot_keys()
                if any(
                    word in key.lower()
                    for word in ("layout", "window", "focus", "panel", "geometry", "position", "stack")
                )
            }
        ),
        state="known_false",
        truth=(
            "the real resource returns seven lists of DB rows — chains, decisions, "
            "directories, notes, profiles, workbenches, workflows — and no key "
            "describing layout, windows, focus, panels, geometry or stacking"
        ),
        story="",
    ),
    Claim(
        doc="docs/internal/DESKOS_COMPONENT_PATTERN.md",
        anchor="The canon for how a surface on the iPad desk (DeskOS) should look and behave",
        sentence=(
            "The canon for how a surface on the iPad desk (DeskOS) should look and "
            "behave, distilled from the one we got right: **the ambient recorder**."
        ),
        predicate=lambda: bool(deskos_component_pattern_web_references()),
        state="known_false",
        truth=(
            "the doc names zero web/src faces; its reference implementation is "
            "apple/App/MeetingCapture/DeskDioramaStage.swift, so it documents the "
            "SwiftUI iPad desk while 'DeskOS' now means the web desk that is the spec"
        ),
        story="",
    ),
    Claim(
        doc="CLAUDE.md",
        anchor="`.githooks/dw-mcp` (NOT wired in `.mcp.json`, which declares only the",
        sentence=(
            "MCP-capable agents: prefer the MCP tools over shelling out — "
            "`.githooks/dw-mcp` (NOT wired in `.mcp.json`, which declares only the "
            "`holdspeak` server by intent; add it to your own client config) serves "
            "the same core as structured tools with identical refusals"
        ),
        predicate=lambda: not {
            name for name in mcp_json_servers() if "dw" in name.lower()
        },
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
]


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
# Reason for the current ceiling:
#   four are owned (HS-200-45: the MCP composition root, the WAL pragma
#   sentence, the SECURITY.md tailnet bind; HS-200-44: the UX-CANON A1
#   residue count), and three are unowned and need a code change rather than
#   a prose correction — the verb-catalog mirror and desk_snapshot's
#   advertised shape, and DESKOS_COMPONENT_PATTERN (a whole doc describing
#   the wrong desk).
KNOWN_FALSE_RATCHET = 7
KNOWN_FALSE_RATCHET_DATE = "2026-09-17"
KNOWN_FALSE_RATCHET_REASON = (
    "HS-200-45 owns three (mcp_http composition, connection WAL pragmas, "
    "SECURITY tailnet bind); HS-200-44 owns the UX-CANON A1 residue count; three "
    "are unowned and need a code change rather than a one-line doc correction "
    "(the verb-catalog mirror, desk_snapshot's layout, DESKOS_COMPONENT_PATTERN)"
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
