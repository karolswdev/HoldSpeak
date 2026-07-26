# HS-106-03 - The effect census, pinned as a test

- **Project:** holdspeak
- **Phase:** 106
- **Status:** ready
- **Depends on:** none
- **Unblocks:** HS-106-04, HS-106-05, HS-106-06, HS-106-07

- **Owner:** unassigned

## The thesis (the bar)

A census is a photograph; a test is a fence. The
[effect census](../proposals/kernel-effect-census-2026-07-25.md)
found **40 effect-capable call sites, 4 covered, 36 not** — but a
Markdown snapshot rots the first time someone adds a `subprocess.run`
on a Tuesday. Pinning it as a test converts a one-time audit into a
standing property: *no new ambient effect site appears without a
human deciding to add it to the ledger.*

This is the cheapest story in the phase and possibly the most
durable. It is worth landing even if the kernel is never built —
which is exactly why the RFC calls it pure hardening (§8).

## Problem

Today a contributor (human or agent) can add a direct
`TextTyper.type_text`, a raw `subprocess.run`, a bare `urlopen`, or
an AppleScript keystroke and nothing notices. The census's own
finding is that this has already happened 36 times.

## Recipe

1. **The ledger becomes data.** The census's classification moves
   from prose into a checked-in ledger: every known effect site with
   its family (tmux transport / TextTyper / subprocess / egress /
   raw clipboard-AX-AppleScript), its status (covered / bypass /
   mixed / dormant), and the reason it is allowed to exist today.
2. **The test walks the source and compares.** A static pass over
   `holdspeak/` (including ignored source paths, excluding generated
   bytecode, source maps, and vendored assets — the census's own
   scoping rules) finds effect-capable statements and diffs against
   the ledger. A new site not in the ledger fails the suite by name
   and prints the file:line and the family.
3. **The count is asserted, not just the set.** The suite states the
   present numbers out loud, so a story that reduces bypass sites
   updates the ledger deliberately and the diff shows the progress.
4. **The broker density guards land here too** (RFC §12, sol's
   amendment 6b), so they are green *before* any slice merges rather
   than invented to fit one:
   - a **line-budget guard** on broker modules in the Phase-79
     style;
   - a **zero-conditional census test** asserting no broker module
     contains driver-specific branching.
   Both start as guards over an empty or near-empty broker package —
   that is fine and deliberate. A fence built before the field is
   planted is a fence nobody argues with later.
5. **Removal is as loud as addition.** A ledger entry whose site
   disappears also fails, so the ledger cannot drift into fiction.

## Out of scope

- Rerouting any site through anything. Rung 1 of the ladder is
  explicitly "no rerouting yet."
- Judging whether a site *should* exist. The test records reality;
  the slices change it.
- Dynamic or runtime effect detection. Static call sites only, as
  the census scoped it.

## Acceptance

- The ledger reproduces the census's 40 sites with the same family
  breakdown (4 tmux transport, 8 TextTyper, 5 subprocess, 13
  egress, 10 raw clipboard/AX/AppleScript) and the same
  covered-versus-not verdict (4 / 36).
- Adding a new `subprocess.run` in a scratch file fails the suite by
  name — **proven by mutation**: add it, watch the named failure,
  remove it, watch green (the HS-104-03 method).
- Deleting a ledgered site fails the suite by name, proven the same
  way.
- The line-budget guard and the zero-conditional guard are green and
  both fail correctly under mutation.
- The suite runs in the normal `uv run pytest -q` path — no separate
  opt-in command that will be forgotten.

## Test plan

- **Unit:** the source walker's classification against fixtures for
  each family.
- **Mutation (evidence):** four mutations — add a site, remove a
  site, blow the line budget, add a driver conditional — each
  producing a named failure and then green again.
- **Full suite:** `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Chef's notes

- Keep the walker boring. An AST pass with an explicit family table
  beats a clever heuristic; false negatives are silent, and a silent
  fence is worse than no fence.
- The census counted *statements*, not user actions — one logical
  action can cross several sites (`gated_connector._route` →
  `PermissionGate` → `urlopen`). Keep that counting rule, or the
  numbers stop matching the proposal and nobody will trust either.
- Everything bottoms out at `holdspeak/tmux_transport.py:20`
  (`send_text_to_pane`) for the typing families — that is the
  chokepoint the terminal slice will adapt, so make sure the ledger
  makes it obvious.
