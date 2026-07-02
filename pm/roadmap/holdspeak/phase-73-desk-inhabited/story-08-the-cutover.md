# HS-73-08 — The cutover: the Alpine desk dies

- **Status:** done
- **Priority:** HIGH (one paradigm, one implementation; the deletion is trivial, the inventory is the story)
- **Depends on:** HS-73-02 … HS-73-07
- **Evidence:** [evidence-story-08.md](./evidence-story-08.md)

## Goal

Delete the legacy Alpine desk — `/desk-legacy` (the old `desk.astro`,
1,732 lines) and `desk-app.js` (1,472 lines) — behind a **zero-loss verb
inventory**. Every control the legacy surface offered either has a proven
React home from stories 02–07, gets a small one here, or is relocated to a
`/studio` surface with a decision note. Nothing is silently dropped.

## Scope

- **In:** the inventory; the deletion; small in-world additions the
  inventory demands; route cleanup; guard caps.
- **Out:** migrating any other Alpine page (`/history`, `/live`,
  `/companion` etc. — a later phase per the standing rule); building new
  major surfaces for relocated verbs (a relocation is a link/placement on
  an existing page, or a deferral recorded in the status doc with the
  owner flagged).

## Tasks

- [ ] **Inventory first, in the evidence file:** walk the ENTIRE legacy
      page — not just the appendix — and table every interactive control
      with its disposition. Known population (verified at scaffold):
      per-kind `openCreate(kind)`; the create/run/file drawers; per-card
      "Move to…" `openFile(kind, item)`; `openRun(item, 'agent'|'chain'|
      'workflow')`; the empty-state "Create the first …" links; Tidy;
      Refresh; the hub/sync labels; plus any field-level edit affordances
      on the cards. The inventory must be exhaustive from the source.
- [ ] Expected mappings (validate each): create → HS-73-03 chips; open /
      inspect → HS-73-04 pull-outs; run → pull-out + rail (HS-73-07);
      "Move to…" → the pull-out's Move-to (HS-73-04); Tidy/Refresh/hub
      dot → the HS-73-02 chrome. A delete affordance, if the inventory
      finds one, goes through the shell `ConfirmDialog` — never
      `window.confirm`.
- [ ] Delete: `web/src/pages/desk-legacy.astro` (the old `desk.astro`),
      `web/src/scripts/desk-app.js`, `web/src/scripts/sprites.js` (the TS
      port is canonical now), and every orphaned style/import. Decide the
      `/desk` redirect's fate (keep the one-liner or drop the route) and
      update the pre-flight accordingly.
- [ ] Confirm zero `?raw` + `new Function` loading remains anywhere on the
      desk path; the standing rule (no new Alpine) is enforceable by grep.
- [ ] Extend the density guard to cap `web/src/desk/**` (no file over
      ~400 lines is a reasonable React-component ceiling — set the number
      from the actual post-07 tree, then lock it).

## Proof required

The disposition table with EVERY legacy control accounted for. Greps in
evidence: zero `desk-app.js` references, zero `new Function` on the desk
path, zero `role="dialog"`/`aria-modal` under `web/src/desk/`. Route
pre-flight green with the final route set; density guard green with the
new caps; full suite + `npm run build` green; a screenshot confirming the
world is byte-identical in behavior after the deletion (the walk's steps
still pass).

## Done

Shipped. The zero-loss verb inventory gated the deletion and EARNED ITS
KEEP: it caught two real gaps — the legacy toggleFile's toggle-OFF half
(Move-to now marks the containing zone and clicking it removes via the
real membership DELETE, DB tombstone asserted) and answerCoder (the coder
pull-out gains "Answer with voice" firing the same POST
/api/coders/select, honest Retry on failure) — both closed BEFORE the
deletion landed. One conscious drop recorded: the drawer's chain/workflow
authoring form (capability-graph authoring belongs to Workbench per the
owner's Blueprints direction; the workflow pull-out gains Open full →
/workbench). Then the Alpine desk died: desk-legacy.astro, desk-app.js,
the /desk-legacy route + pre-flight entry — while /desk keeps landing on /
and the shared sprite picker survives. Proofs: 404 asserted, the
toggle-off DB assertion, scoped stop-signal greps clean on web/src/desk,
17 pages, vitest 9/9; full suite 3066 passed, 37 skipped. See
[evidence-story-08.md](./evidence-story-08.md).
