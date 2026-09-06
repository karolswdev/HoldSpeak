# Phase 168 — The Connections Door: final summary

Written 2026-09-04 at the close. Chartered the same day off main
`ce629cc2` on the owner's word ("charter it") after his bounce on his
own walk of the Room, verbatim: "I still..., get pretty upset around
how unintuitive it is to configure the connectors, I feel like that
itself deserves its own sort of... UX wizard IMO ... Even myself - I
got confused. Not good, not good."

## The exit, and whether it was met

The exit, verbatim from the charter: a cold desk with nothing
connected reaches its first GitHub Watch on a real repo and its first
Jira Watch on a real site through the FACE alone — every step shot at
both widths — with one terminal visit per tool at most, under the
stopwatch, and the owner's word that configuring connectors no longer
confuses him.

- The face-driven walk (tests/e2e/live168_walk.py) drove the whole
  path on the owner's REAL desk at 1440 and 393 (2 passed, 89 s):
  Settings → Connections both `Connected` → New Project → the TOOLS
  row → the GitHub wizard scope-only → Test → Use this Watch → the
  second GitHub Watch via the known-scope card → the Jira wizard on
  KAN with the account step skipped → Review with both baselines
  established → Activate → the Room. Both projects archived in the
  finally with every watch paused; the DB backed up first.
- The stopwatch against the 01 audit (assets/stopwatch.md): 9 → 7
  clicks to a tested GitHub Watch; two sentences → zero; the terminal
  command gone from the interview (it lives in Settings →
  Connections, one per tool, with COPY); the second GitHub Watch four
  clicks from the first; cold: from a SILENT dead end (no provider
  card, no hint) to `Connect GitHub` on the face at four clicks.
- **The owner's attended walk and verdict: pending at the time of
  writing** (story 05 flips on his word).

## What shipped (seven stories)

1. **The audit + the settled design** — the stopwatch audit THROUGH
   THE FACE (52 window shots; the cold desk a silent dead end; the
   eight-proposal cap found starving Jira); the design on the library
   (D1 Settings → Connections; D2 the Sources step; D3 the GitHub
   wizard settled to the wire — the 167 ITEMS/LABELS sheet retired
   because the wire does not carry it); counsel RATIFY-W-C 3 M · 4 S ·
   8 N all paid; twelve artboards on the canvas; the owner's word
   "Okay." read as PASS.
2. **The connections service** — `GET /api/connections` as ONE
   readiness shape over the existing adapters (the five wire states
   mapped; one recovery_hint); suggest annotated with each proposal's
   connection; known scopes computed, never applied; MCP twins
   (189 tools / 34 families); the cap PER PROVIDER; a sidecar parity
   scar paid (no GitHub adapter in the MCP setup service).
3. **The Connections face** — one row per tool, one state, one verb;
   the sign-in fold with COPY + Recheck; the Jira rows in the 166
   grammar; Calendar and Models as link cards; Credentials + Mesh
   kept; the tile id kept, the label changed in both places; seven
   bounces over two rounds; shot cold and on the owner's real gh +
   acli.
4. **The Sources step connect-once** — the TOOLS row from the wire;
   the connect card opening Connections in place with the
   windowsById re-read and re-suggest; wizards asking scope only; the
   known-scope offer; `Back · Test this Watch · Use this Watch`;
   re-suggest made idempotent at the seam (random ids per call had
   orphaned every selection); four orchestrator rounds; the owner's
   live bounce paid — every verb the library Button, the ledger-row
   wrap fixed at the species.
5. **The walk, face-driven** — built, isolated leg green, the real
   leg on the owner's desk; two footer species bugs paid (hosts
   clipped at 156px; the receipt shifted into the egress column).
6. **The docs** — "Connect your tools", the Rooms walk rewritten to
   connect-once with nine shots, the architecture anchors, README
   prerequisites, the stale tool counts.
7. **The close** — counsel RATIFY-W-C 0 M · 4 S · 1 N (all S paid);
   the full suite and the sweep below.

## The gates at the close

- Full suite in two halves (`-n auto`, isolated HOME, metal
  excluded): unit 7946 passed · 14 failed · 6 skipped; the rest 1350
  passed · 4 failed · 59 skipped. Of the 18 failures, 9 are in the
  branch BASE's CI failure set (26 names at ce629cc2; 17 of those now
  PASS on the branch). The 9 branch-new candidates re-run serially on
  the settled tree: 4 passed (xdist flakes — three glass rigs and the
  scheduled-recording conductor), 5 deterministic and mine — all paid
  in the close: the GitHub candidates pin (5 → the per-provider cap
  4), the project family count (45 → 47), the two allow-list sizes
  (+2 connection tools), and a global DOM query in SetupRoot's
  scroll-to-tools (now a ref). Sweep: zero unexplained.
- Web: vitest setup + surface 486/486; the inherited baseline zero
  branch-new (2360 passed); api-surface, vocabulary, doc-drift and
  sidecar-drift guards green; test_product_copy's failure set is
  main's (ledgered at the 167 close), zero branch-new.
- Glass: the 159/161/166/168 rigs 19 passed + 1 honest skip; the
  connections rig 4 cold + 2 real.

## Laws this phase added (to memory)

- A setup walk drives the FACE and shoots the WINDOW; a shot of the
  desk is theater; two identical consecutive step shots fail the walk.
- A chip the wire lacks is retired from the design, not built.
- Every verb on every face is the library Button; a raw `<button>` is
  a bounce (the owner's ruling, verbatim in memory).
- A ledger row that stacks its lead above its primary is a species bug.
- Rigs settle `document.getAnimations()` before every shot; a
  "washed-out" column in a shot is a rig artifact until a probe of
  computed opacity says otherwise; a worker that explains a dim pixel
  as "quiet tone" is rationalizing.
- The footer never truncates a host; an empty footer slot never moves
  the receipt.
- Re-suggest on a session returns existing rows and adds only new
  candidates (dedup by provider + template, native by kind + name).

## Debts (carried to the ledger)

- The owner's attended walk (pending his word).
- Counsel N-1: the Jira accounts step still reads the 166
  per-connection route (`GET /api/providers/jira/connections`) with
  its older state vocabulary (`capability_missing`), not the
  connections wire's `tool.connections[]`.
- The emojiGuard sweeps only desk/ — pages/cores/ and features/ are
  unswept (an emoji emblem got through 03's first round).
- StringGadget's `label` is aria-only; a visible label needs a wrapper.
- The Connections tile's glyph stays `secret` until the icon palette
  gains a plug.
- `web/src/features/project-room/setup/__tests__/model.test.ts`
  imports `cadenceLabel` twice (a tsc duplicate-identifier error on
  main; vitest unaffected).
- The GitHub wire watches pull requests with a base-branch filter
  only; issues / releases / labels (the 167 ITEMS/LABELS sheet) are a
  V1 rider on the wire; `clarify_proposal` cannot patch `query.base`.
- `_MAX_PROPOSALS_PER_PROVIDER = 4` with five templates per provider:
  one template per provider never surfaces (the fifth); a ranking or
  a "more" affordance is a V1 call.
- The connections service is composed three times (web context, the
  web setup service, the MCP family); one composer would be honest.
- The walk runner's real leg archives but the 167 project and the two
  168 walk projects stay on the owner's desk archived (never deleted).
- test_product_copy's pre-existing violations on main (28 sites).
