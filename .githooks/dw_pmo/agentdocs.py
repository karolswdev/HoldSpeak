"""The managed agent-docs block for CLAUDE.md / AGENTS.md.

`dw agent-docs` writes (or refreshes) a marker-delimited block so the
agent-facing contract no longer depends on a human pasting a snippet.
`install.sh` calls it on install, `update.sh` on every update, and
`dw doctor` reports when the block is missing or stale. Content outside
the markers is never touched.
"""

from __future__ import annotations

from pathlib import Path

from .paths import read_text, template_dir, write_text

BEGIN_MARKER = "<!-- BEGIN DELIVERY WORKBENCH (managed by pmo-roadmap install.sh/update.sh — edits inside are overwritten) -->"
END_MARKER = "<!-- END DELIVERY WORKBENCH -->"

CANONICAL_BLOCK = """## Delivery Workbench (PMO rails)

This repository uses Delivery Workbench: an evidence-first commit gate
over a Markdown roadmap under `pm/roadmap/<project>/` (phases, stories,
paired evidence files). Markdown is the source of truth; `.githooks/dw`
is the CLI for everything below. Run `.githooks/dw doctor` if anything
seems miswired. `.githooks/dw-workbench --root .` serves a localhost
web view of the roadmap (browse, health, trace, guarded edit).

Orient before working:

- `.githooks/dw context [project] --compact` — JSON snapshot: issues,
  warnings, next story, per-story trace paths.
- `.githooks/dw next [project]` — the next actionable story
  (exit 0 = found, 2 = nothing actionable, 1 = error; `--json` for a
  machine-readable object).
- `.githooks/dw check [project]` — structural and evidence-content
  lint; greppable `ERROR <path>: <issue>` lines, exit 1 on issues.

Work a story (statuses: backlog | ready | in-progress | blocked | done;
done-synonyms complete/closed/shipped gate identically):

1. `.githooks/dw story status <project> <phase> <story> in-progress`
2. Do the work.
3. Prove it — run the real verification through
   `.githooks/dw evidence capture <project> <phase> <story> -- <command>`
   (records command, exit code, index tree, and output into the story's
   evidence file; screenshots/binaries go under `assets/` next to it).
4. `.githooks/dw story status <project> <phase> <story> done`
   (refuses without evidence).

Commit — every commit passes the gate:

1. Stage everything (`git add …`), THEN generate the contract:
   `.githooks/dw contract new [--story ID] [--consent yes --reasons "…"]
   [--tests-capture <evidence-path>[#ts]]`
   It stamps machine-verified facts (branch, HEAD, index tree, staged
   sample, story IDs); restaging afterwards invalidates it (regenerate
   with `--force`).
2. Honestly verify each rule, then flip every `- [ ]` to `- [x]` in
   `.tmp/CONTRACT.md`. A `--tests-capture` reference pre-checks the
   "Tests ran." box and is re-verified by the gate.
3. `git commit`. Trailers (`PMO-Story`, `PMO-Contract-Digest`) and the
   contract archive under `.git/pmo-contract-archive/<sha>` are
   automatic; the contract survives an aborted commit.

Gate rules the machinery enforces: one story flips done per commit
(bundle only with `.tmp/BUNDLE-OK.md` + one-line rationale), the
flipped story's `evidence-story-NN.md` ships in the same commit, and
evidence never appears or disappears orphaned. Preflight any time with
`.githooks/dw gate [--porcelain]` — it never consumes the contract.
`.githooks/dw verify [<base>..<head> | --all]` re-derives the
structural rules from pushed history alone — audit any range,
no local contract needed.

MCP-capable agents: prefer the MCP tools over shelling out —
`.githooks/dw-mcp` (wired via `.mcp.json`) serves the same core as
structured tools with identical refusals: orientation (`dw_context`,
`dw_next`, `dw_check`, `dw_doctor`), verification (`dw_verify`,
`dw_gate`), guarded mutations (`dw_story_status`,
`dw_evidence_capture`, `dw_contract_new`). Certification is never a
tool call: flipping contract boxes stays a manual, deliberate edit
(see `docs/mcp.md` in the framework repo).

Never use `--no-verify`; when blocked, read the banner — it names the
rule and the remediation, and includes the exact contract template.

Slash commands (Claude Code, under `.claude/commands/`): `/dw-next`,
`/dw-story-done`, `/dw-contract`, `/dw-adopt`.

Canon: `pm/roadmap/PMO-CONTRACT.md` (rules),
`pm/roadmap/roadmap-builder.md` (methodology)."""


def canonical_block() -> str:
    """The block content; the source-repo template wins when present."""
    templates = template_dir()
    if templates and (templates / "CLAUDE-snippet.md").exists():
        return read_text(templates / "CLAUDE-snippet.md").strip()
    return CANONICAL_BLOCK


def managed_region(text: str) -> tuple[int, int] | None:
    """(start, end) character span of the managed block, or None."""
    start = text.find(BEGIN_MARKER)
    if start == -1:
        return None
    end = text.find(END_MARKER, start)
    if end == -1:
        return None
    return start, end + len(END_MARKER)


def render_block() -> str:
    return f"{BEGIN_MARKER}\n\n{canonical_block()}\n\n{END_MARKER}"


_CLAUDE_SLASH_PARAGRAPH_START = "Slash commands (Claude Code"
_MCP_CLAUDE_WIRING = "(wired via `.mcp.json`)"
_MCP_NEUTRAL_WIRING = (
    "(stdio JSON-RPC; wire it per your client — Claude Code reads "
    "`.mcp.json`, Codex uses `codex mcp add`)"
)
_AGENTS_CLI_NOTE = (
    "Agents without MCP support: the CLI commands above are the "
    "complete surface — nothing below requires MCP."
)


def agents_block() -> str:
    """The brief for AGENTS.md-reading harnesses (Codex, pi, others):
    the same canon minus Claude-only affordances. Transformations are
    best-effort at runtime (canon may be template-overridden); a unit
    test in the framework repo asserts they both actually fired."""
    text = canonical_block()
    start = text.find(_CLAUDE_SLASH_PARAGRAPH_START)
    if start != -1:
        end = text.find("\n\n", start)
        end = len(text) if end == -1 else end + 2
        text = text[:start] + text[end:]
    if _MCP_CLAUDE_WIRING in text:
        text = text.replace(_MCP_CLAUDE_WIRING, _MCP_NEUTRAL_WIRING, 1)
        text = text.rstrip() + "\n\n" + _AGENTS_CLI_NOTE
    return text.strip()


def render_agents_block() -> str:
    return f"{BEGIN_MARKER}\n\n{agents_block()}\n\n{END_MARKER}"


def agents_variant_for(path: Path) -> bool:
    """AGENTS.md gets the harness-neutral variant; anything else the
    Claude variant (CLAUDE.md is the historical default target)."""
    return path.name == "AGENTS.md"


def render_block_for(path: Path) -> str:
    return render_agents_block() if agents_variant_for(path) else render_block()


def agent_docs_target(root: Path) -> Path:
    """Prefer an existing CLAUDE.md, then AGENTS.md, else a new CLAUDE.md."""
    for name in ("CLAUDE.md", "AGENTS.md"):
        if (root / name).exists():
            return root / name
    return root / "CLAUDE.md"


def write_agent_docs(root: Path, target: Path | None = None) -> tuple[Path, str]:
    """Create or refresh the managed block. Returns (path, action)."""
    path = target or agent_docs_target(root)
    block = render_block_for(path)
    if not path.exists():
        write_text(path, block + "\n")
        return path, "created"
    text = read_text(path)
    region = managed_region(text)
    if region is None:
        joined = text.rstrip("\n") + "\n\n" + block + "\n" if text.strip() else block + "\n"
        write_text(path, joined)
        return path, "added"
    current = text[region[0]:region[1]]
    if current == block:
        return path, "unchanged"
    write_text(path, text[:region[0]] + block + text[region[1]:])
    return path, "refreshed"


def agent_docs_status(root: Path) -> tuple[str, Path | None]:
    """One of 'missing', 'stale', 'current' plus the file examined.
    Each file is compared against its own variant (WLA-12-04)."""
    for name in ("CLAUDE.md", "AGENTS.md"):
        path = root / name
        if not path.exists():
            continue
        text = read_text(path)
        region = managed_region(text)
        if region is None:
            continue
        if text[region[0]:region[1]] == render_block_for(path):
            return "current", path
        return "stale", path
    return "missing", None
