# HS-37-03 — Approval surface (preview → approve/reject, no execution)

- **Project:** holdspeak
- **Phase:** 37
- **Status:** not-started
- **Depends on:** HS-37-02
- **Unblocks:** HS-37-04
- **Owner:** unassigned

## Problem

A persisted proposal is invisible until a human can see exactly what it would do and
decide. The approval surface is where the safety invariant becomes real to the user: a
clear **preview**, the **target** + **reversibility**, and an explicit **Approve** /
**Reject** — with the guarantee that **looking at a proposal never causes a side effect**.

## Scope

- **In:**
  - An API exposing a meeting's proposals (`GET …/proposals`) and a decision endpoint
    (`POST …/proposals/{id}/decision` → `approved` | `rejected`), writing through the
    HS-37-02 repo (decision records `decided_by` + an audit entry).
  - A Signal **proposal card** in the meeting detail (`web/src/pages/history.astro` +
    `history-app.js`): the `target`/`action`, a **preview** rendered with
    `CommandPreview.astro` (the exact `payload`/preview text), a reversibility indicator,
    and **Approve** / **Reject** controls with confirmed/decided state. Approving flips DB
    state **only** — no execution in this story.
  - Pending vs decided states are visually distinct; a rejected proposal is terminal in
    the UI.
- **Out:**
  - Execution / egress (HS-37-04) — Approve here just sets `approved`; the executor is a
    later story. A clear "approved — pending execution" state is fine.
  - Editing a proposal's payload (out of scope; approve-as-is or reject).

## Acceptance criteria

- [ ] Proposals render in the meeting detail with the preview + target + reversibility;
      **nothing egresses on load or render** (assert no executor/connector call on the
      read path).
- [ ] **Approve** sets `approved` (+ `decided_by` + audit); **Reject** sets `rejected`
      (terminal); the UI reflects the decided state.
- [ ] The decision endpoint rejects illegal transitions (e.g. deciding an already-executed
      proposal) with a clean error.
- [ ] `cd web && npm run build` succeeds; the bundle is the gitignored build product (not
      committed); suite green.

## Test plan

- API: list proposals; approve → `approved`; reject → `rejected`; illegal decision → error.
- API/unit: the read + decision paths perform **no** outbound action (spy on the executor
  seam, which is still a no-op here).
- Manual: rebuild; open a meeting with a seeded proposal; confirm the preview + approve/
  reject states.
- Suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` green.

## Notes / open questions

- Reuse the `CommandPreview` clipboard/preview component for the payload preview so it
  reads as a reviewable command/trace, consistent with the dictation dry-run previews.
- Default proposal cards to **expanded** (like artifact cards) so the preview is visible
  without interaction; the approval decision is the only state the user changes.
- This story is the user-facing embodiment of the egress invariant — keep the "view ≠
  act" boundary obvious in the UI copy.
