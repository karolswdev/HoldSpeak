# HS-105-05 - The menu bar — the system admits what it can do

- **Project:** holdspeak
- **Phase:** 105
- **Status:** done
- **Depends on:** HS-105-02, HS-105-03, HS-105-04
- **Unblocks:** HS-105-07
- **Owner:** unassigned

## The reference (the bar)

Workbench 2.0's menus were the browsable face of everything the
system could do — context-sensitive, keyboard-equivalent (the
Amiga-key shortcuts printed right in the menu), and COMPLETE: if
the system could do it, a menu admitted it. And beneath the menus
sat the era's most forward-thinking move: ARexx, one scripting
port per application, so every capability had a programmatic face
too. The mindset: a verb is not a button someone remembered to
draw — it is a REGISTERED capability, and every face of the system
(menu, palette, wire) renders the same registry.

## Problem

The desk's verbs live in three unreconciled places: the ⌘K
launcher, scattered right-click menus, and per-surface buttons.
Nothing guarantees a verb reachable one way is reachable the
others; discoverability is archaeology; and nothing states, in one
place, what the desk can do — which also means the future Swift
spec has no verb inventory to consume.

## Recipe

1. **One verb registry, first.** Consolidate into a single registry
   (grow what ⌘K already reads rather than minting a rival): each
   verb declares id, label, scope (global | kind | selection |
   window), availability predicate, keyboard equivalent, and
   handler. A census forbids components invoking desk verbs outside
   the registry — the registry IS the capability truth.
2. **Three faces, one truth** (the ARexx move):
   - **The menu bar:** real pull-down menus in the existing top bar
     (Desk / Object / View / Go, tuned in the sitting), rendered
     FROM the registry — context-sensitive (Object menu reflects
     the selection's kind and its contract verbs, including
     HS-105-02 drop verbs phrased as commands and HS-105-04 Info),
     disabled-with-reason rather than hidden (the Workbench
     ghosting rule: the system admits the verb exists even when it
     cannot run), keyboard equivalents printed in the row.
   - **⌘K:** re-pointed at the same registry (it largely is — the
     work is closing the gap where surfaces bypass it).
   - **The wire:** `GET /api/desk/verbs` (the inventory with
     scopes and availability) and `POST /api/desk/verbs/<id>` for
     verbs whose handlers are hub-side or store-effecting via the
     existing bus. Consent-gated verbs refuse over the wire exactly
     as they refuse on glass — the wire face never widens
     authority (Article V), and the endpoint wears the standard
     token gate.
3. **Keyboard truth.** Every registered equivalent works and is
   shown; conflicts are a build-time registry error, not a runtime
   surprise (extends the Phase-96 keyboard-truth posture).
4. **The spec dividend.** The registry export (ids, scopes,
   equivalents, per-kind verb sets) is written into the contract
   area — the verb inventory page of the future Swift spec,
   generated, never hand-maintained.

## Out of scope

- Removing existing buttons (dedup after the sitting proves the
  menus); user-defined verbs/macros (a future phase on this
  registry); tearing off menus.

## Acceptance

- The menu bar renders from the registry; selecting a note vs a
  zone vs nothing changes the Object menu correctly; a
  cannot-run verb shows ghosted with its reason.
- Ten representative verbs proven identical via all three faces
  (menu, ⌘K, wire) on a staged hub — same handler, same refusals;
  a consent-gated verb refuses over the wire by name.
- The census green (no out-of-registry verb invocations); keyboard
  equivalents all live; conflict detection proven by a failing
  fixture.
- Voice guard green; both viewports (phone: the menu bar collapses
  into the existing sheet grammar, not a hamburger novel).

## Test plan

- **Unit:** registry validation (conflicts, scopes, predicates);
  menu derivation per selection state.
- **Integration:** the three-face parity harness; wire refusals.
- **Live (evidence):** the headed walk, screenshots read.

## Chef's notes

- Build the registry consolidation as its own commit before any
  menu pixel — the menus are a projection; if the projection is
  built first it will quietly become a second truth.
- Ghosted-with-reason is quietly the most OS-feeling deliverable in
  the phase: hiding says "this might not exist"; ghosting says "I
  know exactly what I can do and why not now."
- The wire face is deliberately modest (list + invoke). Resist
  designing a grand automation API here; ARexx won by being plainly
  present everywhere, not by being clever.
