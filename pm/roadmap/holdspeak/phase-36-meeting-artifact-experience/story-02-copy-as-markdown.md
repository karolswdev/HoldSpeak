# HS-36-02 — Copy-as-Markdown per artifact

- **Project:** holdspeak
- **Phase:** 36
- **Status:** not-started
- **Depends on:** HS-36-01
- **Unblocks:** none
- **Owner:** unassigned

## Problem

There is no way to lift an artifact's content out of the web view. A user reviewing a
meeting wants to drop the incident timeline, the risk register, or the stakeholder
update straight into a doc / Slack / ticket as Markdown. Direct user ask: *"there isn't
a facility to quickly copy the content into a markdown clipboard."*

## Scope

- **In:**
  - A per-artifact **"Copy"** button in the card header (the slot HS-36-01 leaves)
    that serializes that artifact's `structured_json` to clean Markdown and writes it
    to the clipboard.
  - A **Markdown serializer per artifact type** (in `history-app.js` or a small helper
    module): headings + tables for tabular types (risk register), ordered lists for
    timelines, sectioned lists for stakeholder update / decisions / requirements, etc.
    Driven by the artifact data, not the DOM (so a collapsed card still copies).
  - Reuse the **`CommandPreview` clipboard pattern** (`navigator.clipboard.writeText`
    + a copied-state label/animation + graceful fallback when clipboard is blocked).
  - A **"Copy all"** affordance that concatenates every artifact's Markdown (with a
    meeting heading) for the whole meeting.
  - Rebuild the bundle (`cd web && npm run build`) for verification — it is a gitignored build product (built at install/package time from `web/src`), NOT committed.
- **Out:**
  - File download / export (`.md`/`.json`) — deferred (clipboard only).
  - Copying the transcript (already its own surface) — artifacts only.

## Acceptance criteria

- [ ] Each artifact card has a "Copy" button that writes well-formed Markdown for that
      type to the clipboard and shows a copied-state.
- [ ] The Markdown is generated from the artifact data (works even if the card body is
      collapsed).
- [ ] Tabular artifacts (risk register) copy as a Markdown table; timelines copy as an
      ordered list; sectioned artifacts (stakeholder update, decisions, requirements)
      copy with headings — spot-checked per type.
- [ ] A "Copy all" control copies every artifact for the meeting under a meeting
      heading.
- [ ] Clipboard-blocked path degrades gracefully (no crash; a fallback hint), matching
      `CommandPreview`.
- [ ] `cd web && npm run build` succeeds + committed; suite green.

## Test plan

- Unit/suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` — green.
- Manual: rebuild, open a meeting, click Copy on the risk register + the timeline +
  the stakeholder update; paste into a Markdown renderer and confirm formatting; click
  Copy-all and confirm concatenation.
- (Optional) a small JS-level unit/DOM test for the serializers if a harness exists;
  otherwise manual is the gate (documented).

## Notes / open questions

- Keep serializers pure (data → string) so they're easy to eyeball and could get a JS
  test later.
- Markdown table for the risk register should escape `|` in cell text.
