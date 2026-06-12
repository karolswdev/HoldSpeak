# Phase 62 — Quiet Trust

**Status:** CLOSED (4/4). Opened 2026-06-12 on direct owner feedback:
the privacy-reassurance prose across the UI is "really cringey" — replace
the novels on cards and notifications with a compact **egress badge**
(local · local+cloud · cloud) and redo the affected screenshots. This
reverses the locked Phase-56 "three privacy answers verbatim on every
actionable card" decision.

**Last updated:** 2026-06-12 (**HS-62-04 done — phase CLOSED 4/4:** the
badge proven on REAL broadcast-driven cards: the real file-issue route's
`actuator_proposed` slid in a card carrying exactly '☁ github'; a real
taught correction's `learning_event` (reach 2) carried exactly '⌂ Local';
zero retired phrases on either card, zero page errors (17/17). Final suite
**2768 passed, 17 skipped**; see [final-summary.md](./final-summary.md);
PR merged on green. Prior: **HS-62-03 done:** docs + the re-shot
screenshots. POSITIONING gains the voice rule (egress is a badge, not
prose); README/docs alts stopped quoting retired paragraphs; all seven
user-facing screenshots re-shot from live runs, content-asserted before
capture — including the native overlay on **real .43 metal** (the rsynced
tree, the real GTK overlay, a real filed proposal, `import` off the real
root window). The zero-page-error gate also caught and fixed a
**pre-existing Phase-43 bug** (verified pre-existing on main): the welcome
wizard's `@click="copy(\"…\")"` HTML-truncated into a SyntaxError on every
/welcome load and that copy button never worked. Suite **2768 passed, 17
skipped**. Prior: **HS-62-02 done:** the sweep. Nine files, every
operational reassurance tail cut to its functional core (notes, flashes,
guards, the wizard rail, the settings lead, the LocalPill tooltip); the
dashboard guard's per-target fix also closed a real lie ('only records your
decision' was untrue for slack since Phase 61). What remains, deliberately:
the TrustChip surfaces (one short line each), the single welcome pitch
sentence, and the behavioral warnings — the residue grep ships in evidence.
Locks updated in place; build clean; suite **2768 passed, 17 skipped**.
Prior: **HS-62-01 done:** the egress badge. The card
shell renders `egress: {scope, label?}` as one pill (⌂ Local green / ⌂+☁ /
☁ + target orange); every card swapped its privacy paragraph for the badge
(`privacyLine()` deleted; the wake card's not-typed state is now three
words); the Phase-56 verbatim locks REWRITTEN to pin the badge and to refuse
the retired prose forever; the typing guide's Qlippy section truth-updated
with them. Live dogfood 11/11, zero page errors: '☁ slack' and '⌂ Local'
render styled (computed-style probed), and the rendered card DOM contains
none of the retired phrases. Suite **2768 passed, 17 skipped**. Earlier:
scaffolded — the full prose inventory and
every lock pinning the old copy are recorded in the brief §3.)

## The thesis — why this phase

Trust should be ambient, not narrated. The header LocalPill already proves
the pattern: one glyph carries the posture. Reading a privacy paragraph on
every Qlippy card and notification is noise that makes the product feel
insecure about itself. One badge, three states, and the prose goes quiet.

## Goal

No UI card or notification narrates privacy. The Qlippy card shell renders
a three-state egress badge from structured data; every reassurance tail in
the web UI is cut or shortened to its functional core; behavioral warnings
stay; docs describe the badge; every user-facing screenshot showing the
old copy is re-shot live.

## Scope

- **In:** the badge component + card shell (HS-62-01); the prose sweep
  across history/welcome/settings/components + flashes (HS-62-02); docs +
  the voice rule + re-shot doc screenshots (HS-62-03); closeout
  (HS-62-04).
- **Out:** the SECURITY/README documentation posture (docs explain once —
  that is allowed); behavioral warnings (wake type-action, shell macros);
  the journal's "Preview only" state string; any backend change.

## Exit criteria (evidence required)

- The Qlippy cards render the badge, never a privacy paragraph; the
  cloud state keeps the target label; locks pin the new pattern.
  (HS-62-01)
- Zero "nothing leaves / stored locally / never sent" reassurance tails
  in web/src outside the allowed explain-once surfaces; build clean.
  (HS-62-02)
- Docs aligned + POSITIONING voice rule + every user-facing-doc
  screenshot showing old copy re-shot from a live run. (HS-62-03)
- Live dogfood proves the badge on real cards with zero page errors;
  full suite green; final-summary; PR merged on green. (HS-62-04)

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-62-01 | The egress badge on Qlippy cards | done | none |
| HS-62-02 | The sweep | done | HS-62-01 |
| HS-62-03 | Docs + re-shot screenshots | done | HS-62-02 |
| HS-62-04 | Closeout | done | HS-62-01..03 |

## Where we are

CLOSED 4/4. Trust is ambient: one badge, three states, no novels. See
[final-summary.md](./final-summary.md).
