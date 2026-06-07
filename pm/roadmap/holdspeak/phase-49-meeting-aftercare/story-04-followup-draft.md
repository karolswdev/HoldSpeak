# HS-49-04 — Draft the follow-up (preview + copy)

- **Project:** holdspeak
- **Phase:** 49
- **Status:** done
- **Depends on:** HS-49-01
- **Owner:** unassigned

## Problem
After a meeting, the recurring chore is writing the follow-up: "here's what we
decided, here's who owns what, here's what's still open." The data already exists
(decisions + action items + owners), but the user retypes it by hand every time.

## Scope
- **In:**
  - A **local follow-up draft** assembled from the aftercare data (HS-49-01):
    decisions, open action items with owners, and the since-last-meeting delta,
    rendered as a clean, copyable message (markdown).
  - **Preview + copy** only: show the draft, let the user copy it. Never auto-send,
    never open a connector to deliver it. (Mirrors dictation replay's "preview +
    copy" stance.)
  - Local-first: assemble deterministically from existing artifacts/actions. An
    LLM polish pass is a candidate, not required (settle here); if added it must be
    optional and degrade to the local assembly.
- **Out:** the aggregation (HS-49-01); provenance (HS-49-02); actions-to-issues
  (HS-49-03); docs (HS-49-05). This story is the draft + copy.

## Acceptance criteria
- [x] A follow-up draft (decisions + open actions + owners) is generated locally
      from the aftercare data and is copyable from the surface.
- [x] Preview + copy only: nothing is sent and no connector is opened; behavior-
      preserving; honest when there's little to summarize (no padding).
- [x] Tests assert the draft content reflects the seeded decisions/actions;
      `npm run build` ✓; 0 `_built/` tracked.

## Test plan
- Integration: seed decisions + open actions -> the draft endpoint/assembly
  includes them with owners; an empty meeting yields a minimal honest draft, not
  filler; `uv run pytest -q -k "aftercare or followup or meeting"`.
- Manual + screenshot: open a meeting, generate the follow-up, copy it.

## Notes / open questions
- Reuse the existing copy-to-clipboard / markdown idiom already in `history.astro`
  (artifacts have copy-as-markdown).
- Keep it deterministic first; if an LLM pass is added, gate it and fall back to
  the local assembly when no runtime is configured (same fail-open posture as the
  dictation pipeline).
- Do not duplicate the digest aggregation; the draft consumes HS-49-01's data.
