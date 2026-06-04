# Evidence — HS-37-03: Approval surface (preview → approve/reject, no execution)

**Date:** 2026-06-04. **Branch:** `phase-37/hs-37-01-actuator-contract`.

## What shipped

The user-facing embodiment of the safety invariant: a human sees exactly what a proposal
would do and decides — and **looking never acts**.

### API (`holdspeak/web/routes/meetings.py` + `holdspeak/web_requests.py`)

- `GET /api/meetings/{id}/proposals[?status=]` — lists a meeting's proposals (a pure
  `db.actuators.list_proposals` read; 404 for an unknown meeting). No side effect.
- `POST /api/meetings/{id}/proposals/{pid}/decision` — body
  `{decision: "approved"|"rejected", decided_by?}`. Validates the decision value (400
  otherwise), confirms the proposal belongs to the meeting (404 otherwise), and calls
  `db.actuators.transition_proposal` — which records `decided_by` + an audit entry and
  enforces the lifecycle (an illegal transition, e.g. on an already-decided proposal,
  surfaces as 400). **It never executes** — approving only flips state; execution is
  HS-37-04. `_ProposalDecisionRequest` is the new request DTO.

### UI (`web/src/pages/history.astro` + `web/src/scripts/history-app.js`)

- A **"Proposed actions"** detail-card in the meeting modal, loaded alongside artifacts
  in `openMeeting` (`selectedMeetingProposals`). Each proposal is a Signal card (reusing
  the `.artifact-card` shell + accent) with:
  - a target glyph + `action → target` title, a typed **status pill** (Awaiting approval
    / Approved — pending execution / Executed / Rejected / Failed), and a
    reversible/irreversible indicator;
  - a **preview** block (`.proposal-preview`, the `CommandPreview` monospace pattern):
    `action → target`, the human preview, and the **exact machine payload** — the thing
    being approved — plus a Copy button (reusing the HS-36-02 clipboard helper);
  - **Approve** / **Reject** controls (only while `proposed`) with the guard line
    "Nothing runs without your approval — this only records your decision"; a decided
    proposal shows its terminal state instead and a rejected one is visually quieted.

## Verification

### API — list, decide, illegal, no-execution

```
$ uv run pytest -q tests/integration/test_web_meeting_proposals_api.py
7 passed
```

Covers: list returns the persisted proposal (incl. the exact payload); 404 for an
unknown meeting; **approve** flips to `approved` with `decided_by` + the audit chain
`[(None,proposed),(proposed,approved)]` and `executed_at is None` (**approval ≠
execution**); **reject** is terminal and a second decision → 400 (`illegal`); an invalid
decision value (`executed` via this path) → 400; unknown proposal → 404; a proposal from
another meeting → 404 and the original stays `proposed`. The "no egress" property holds
by construction — the read path is a DB query and the decision path only transitions
state; no executor/connector is reachable until HS-37-04.

### Visual

`evidence/approval_surface.png` — the three lifecycle states rendered over the real
tokens + page CSS (Playwright): **pending** (warn accent, preview + payload, Approve/
Reject + guard), **approved** (info accent, "pending execution", `by karol`), **rejected**
(quieted, terminal).

### Bundle + suite

```
$ cd web && npm run build          # ✓ 8 pages built; _built carries decideProposal/proposalPreviewText
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2059 passed, 15 skipped            # +7 (the proposals API test)
$ uv run ruff check holdspeak/web/routes/meetings.py holdspeak/web_requests.py
All checks passed!
```

The bundle (`holdspeak/static/_built/`) is the gitignored build product — rebuilt to
verify (`decideProposal` present), **not committed**. (The integration test file carries
the same `importorskip`-then-import `E402` as the sibling web API tests — the repo's
committed convention for meeting-gated tests.)

## Notes

- "View ≠ act" is enforced structurally, not just by copy: the only state a user changes
  is the decision, and the decision endpoint cannot execute (no executor exists yet).
- Cards default to **expanded** so the preview is visible without interaction (matching
  the artifact cards) — the reviewer reads the payload, then decides.
