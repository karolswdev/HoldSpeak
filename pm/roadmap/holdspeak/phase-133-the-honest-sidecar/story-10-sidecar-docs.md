# HS-133-10 — The sidecar has a manual

- **Project:** holdspeak
- **Phase:** 133
- **Status:** backlog
- **Depends on:** HS-133-02..09
- **Unblocks:** HS-133-11
- **Owner:** unassigned

## Problem

After this phase the sidecar is an 82-tool surface with honest
boundaries — and no entry point teaches it. A user (or agent) who has
never seen it cannot discover `holdspeak-mcp`, `.mcp.json`, the tool
families, or what the sidecar deliberately cannot do.

## Scope

### In

- The real entry points (standing rule: docs stories touch ENTRY
  points): the README's install/usage surface gains the MCP sidecar
  section (what it is, `.mcp.json` auto-discovery in Claude Code, the
  one-line manual wiring); the sidecar's own docs page (create
  `docs/mcp-sidecar.md` or extend the existing docs home the repo uses —
  survey `docs/` first and put it where a reader would look) documents
  the eight families, the four model-invoking tools and their receipts,
  the egress note on `settings.update`, and the honest absences
  (coder/cadence reply verbs, plugin processing).
- Cross-check: tool descriptions are the first documentation surface —
  the page cites them rather than duplicating all 82.

### Out

- Web UI documentation. Plugin SDK docs. Marketing copy (POSITIONING
  voice rules apply to any user-facing phrasing).

## Acceptance criteria

- [ ] A fresh reader can wire the sidecar into Claude Code from the
  README alone.
- [ ] The docs page names every family, every model-invoking tool, and
  every deliberate absence with its reason.
- [ ] Docs build/lint (if any) green; no dead links.

## Test plan

- `uv run pytest -q tests/ -k docs --tb=short` if a docs suite exists;
  otherwise link-check the touched pages and paste the check into
  evidence.
