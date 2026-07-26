# HS-104-06 - Docs — the gate and the watch at the entry points

- **Project:** holdspeak
- **Phase:** 104
- **Status:** done
- **Depends on:** HS-104-02, HS-104-04, HS-104-05
- **Unblocks:** HS-104-07
- **Owner:** unassigned

## The bar

The standing rule from Phase 64: docs stories touch ENTRY points —
the places a reader actually arrives — not orphan pages. And the
Phase-76 rule rides along: every claim written must be true on the
tree that ships it (truth audit, not aspiration).

## Problem

After HS-104-02/04/05 the product holds agent tool calls, renders PR
receipts, and prints session receipts — none of it discoverable or
correctly bounded in the written surface. The gate in particular
carries a consent model that MUST be documented before an owner arms
it (fail-closed means a hub outage stops an armed agent's matched
tools; that trade is the user's to make knowingly).

## Recipe

1. **USER_GUIDE:** a "The Gate" section beside the existing "Take
   Over A Session" material — arming (both opt-ins), what holds,
   deciding from the shade, what deny-with-reason looks like to the
   agent, what expiry does, and the one-paragraph honest trade of
   fail-closed. A "PR receipts" subsection in the delivery material:
   registering a source, refresh semantics, what the attribution
   labels mean (exact vs heuristic vs unattributed — quote the
   council's caution in plain words). A "Session receipts" note: the
   three tiers and why a missing cost line is a feature.
2. **SECURITY.md:** the gate's consent boundary in the Phase-87
   pattern — chokepoint, audit, redaction, fail-closed, the
   restart-invalidation rule, and the explicit statement that the
   hook install never edits another app's config. The PR watch's
   egress row (what leaves, to where, when, under which badge).
3. **ARCHITECTURE.md:** one paragraph + diagram touch for the gate
   (hook → hub → shade → decision → hook) and the PR pass in the
   delivery collector; regenerate the render guard per Phase 66.
4. **README (public surface):** one line each in the feature list,
   POSITIONING-voiced, only if the features are on by default in
   discoverability terms — the gate is off by default, so its README
   line says so in the same breath.
5. **Voice guard everything.** All new prose through the vocabulary
   and positioning guards; the dash-in-glass rule does not apply to
   docs, but the AI-vocabulary and em-dash doc rules do.

## Out of scope

- Marketing/positioning rewrites; MODELS.md (no model behavior
  changed).

## Acceptance

- Every claim in the new sections verified against the shipped
  behavior on a staged hub (spot-walk, not faith).
- Guards green; ARCHITECTURE render guard green.

## Test plan

- The doc-drift and vocabulary guards; the ARCHITECTURE mermaid
  render check; a manual read-through recorded in evidence.

## Chef's notes

- Write the fail-closed paragraph first and let it set the tone: if
  the docs can't sell the honest trade in three sentences, the
  feature design has a problem worth hearing about before closeout.
