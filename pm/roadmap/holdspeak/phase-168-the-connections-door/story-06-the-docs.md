# HS-168-06 - The docs: "Connect your tools"

- **Project:** holdspeak
- **Phase:** 168
- **Status:** done
- **Depends on:** HS-168-03, HS-168-04
- **Unblocks:** HS-168-07
- **Owner:** unassigned

## Problem

The guide describes connecting GitHub and Jira as a step inside the
Project Rooms interview; the README's prerequisites name gh and acli
with no face to point at. The dedicated docs story (the standing
law) records the new front door.

## Scope

- **In:** docs/USER_GUIDE.md gains "Connect your tools" (Settings →
  Connections; the states; the one command per tool; labels
  verbatim from the face); the Project Rooms guide's setup section
  re-shot on the recomposed Sources step; README prerequisites point
  at the face; docs/MCP_SIDECAR.md REGENERATED (the generator, never
  hand-edited counts) with the two new tools; the doc drift guard,
  the product-copy guard and the roadmap-vocabulary guard green;
  ARCHITECTURE's provider section names the connections service with
  verified anchors.
- **Out:** positioning changes.

## Acceptance criteria

- [x] Every label in the guide matches the built face verbatim; shots current.
- [x] MCP_SIDECAR regenerated with the drift guard green; README prerequisites updated.
- [x] All doc guards green with the stash-compare law (zero branch-new violations).

## Delivered (2026-09-04)

docs/USER_GUIDE.md "Connect your tools" (Settings → Connections: the
four tool cards, every state chip and verb verbatim from
ConnectionsPane.tsx, the one command per tool, the receipt, the
no-hosted-relay line once, the wire and the MCP twins) + a
Connections row in the product map; docs/PROJECT_ROOMS.md's walk
rewritten to connect-once (1. Connect your tools · 3. Sources with
the TOOLS row, the cold desk, the answered row · 4. Scope and test
with the known-scope card, the population facts, the MATCHES ledger,
`Back · Test this Watch · Use this Watch`) with nine shots from the
03/04 rigs under docs/assets/connections/; docs/ARCHITECTURE.md's
connections readiness projection with verified anchors; README
prerequisites pointing at Settings → Connections; the stale tool
count fixed in docs/README.md and the MCP_SIDECAR narrative (187 →
189 / 33 → 34). Orchestrator catches paid: three sentences that
described what the face does not do (an "answered suggestion card"
that is the interview's answered row; BASE as "the repository's
default branch" — it is the template's base filter; "the condition
that fired" — the MATCHES ledger lists number · title · state).
Evidence: the doc drift, sidecar drift, vocabulary and api-surface
guards 42 passed; the generators current (the only sidecar diff is
the narrative count fix); test_product_copy's one failure is the
pre-existing set on main (the 167 close ledgered it), zero
branch-new.

## Test plan

- **Guards:** `uv run pytest -q tests/ -k "doc or guard or drift"`; the MCP_SIDECAR generator's check mode.
