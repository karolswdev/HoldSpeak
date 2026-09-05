# Phase 173 — The Steward's Hand and Voice: final summary (DRAFT — stacked on 172 (#555) on 171 (#554) on 170 (#553); closes on his word)

## What shipped

- **The design (01):** settled-design-stewards-hand.md + nine boards
  (HEALTH rows · all-green · the NUDGE card · the receipt · 393; the
  drafted update · deterministic · 393; the policy row). Canvas
  https://claude.ai/code/artifact/9f1558b4-0867-4152-bc7e-1314dde5e82c.
  Counsel RATIFY-W-C on the design, six conditions ruled: `REVIEW WAIT`
  in days from createdAt (never a latency the system does not have);
  the green state present with `CLEAR` / `PASSING` / `READY`; the nudge
  text names the tool and no person; the receipt names who; the model
  named beside its host; one `CHECKED N MIN AGO`; `NUDGED N D AGO`
  while cooling.
- **The wire (02 · 03 · 04 · 05):** the model drafter behind the claim
  schema (stakeholder prompt; refs verbatim; UNVERIFIED never smoothed;
  `generator_host` · `generator_model` recorded at draft time);
  `createdAt` on PR entities (the read allowlist unchanged);
  `room_health_service` (review wait · issue aging · CI tone + flaky +
  queue · readiness composite; a tone on every signal); the Room read's
  `health.signals` + `checked_at` + resolved `people` (no raw login) and
  `review_bottleneck` needs-you items; the steward's OBSERVE collects
  `gh run list --limit 10` history; the sixth effect kind
  `github_comment` proposed as steps of the real steward run (one per
  reviewer × PR; eligibility gate; 7-day cooldown; `nudge_template` on
  the policy), `GET /api/projects/{id}/nudges`, `POST /api/nudges/{id}/
  send|dismiss` (Send re-checks the gate, admits through the kernel,
  runs only `gh pr comment` through the gated connector, receipts who ·
  where · the exact text), MCP `steward.nudges` · `nudge.send` ·
  `nudge.dismiss` (211 tools / 39 families).
- **The faces (02 · 03 · 04 · 05):** the drafted update (ref chips `PR
  #612` · `KAN-7` · `MTG 09-05` per sentence under the editable body,
  `UNVERIFIED` beside its claim, the model named beside its host; the
  deterministic draft bare); the Room's HEALTH section (four rows with
  tones; `CLEAR` / `PASSING` / `READY`; `1 BLOCKER`, `1 PR WAITING`; one
  `CHECKED <age>`); bottleneck rows with `Nudge` (only when a proposal
  exists) and `Open`; the NUDGE card (who · `#612 · title` · the text in
  a StringGadget with the mic · `GITHUB.COM` · Send · Dismiss); the
  receipt `SENT · Ania Kowalska · #612 · hh:mm · GITHUB.COM` with no
  Undo; `NUDGED JUST NOW` after Send; the policy row `Reviewer nudge` +
  `GITHUB.COM` + `PER-NUDGE APPROVAL` + `Nudge text` when armed. Rigs:
  health (4 legs + nudge), update (3), policy (3); 14 green serially
  with the 172 Room rig.
- **The docs (07):** README, USER_GUIDE "The steward's hand",
  ARCHITECTURE (two sequences), SECURITY (the nudge boundary),
  MCP_SIDECAR, POSITIONING names — verified against the built faces
  (seven markers cleared; Dismiss also starts the 7-day cooldown; four
  update verbs incl. Regenerate; `CHECKED <age>` as built).
- **The walk (06):** live173_walk.py drafted with every write denied;
  the owner's-desk run PENDING.
- **The hygiene lane (08):** 158 S-1 paid (add/remove resource,
  associate/disassociate meeting each one atomic transaction);
  steward/update tsc clear; the 165 sidecar seam already fixed in the
  project family (the heartbeat family's copy is 171's tree); 158 N-1
  deferred with reason; THE-TUESDAY-ARC §4 rows updated.

## Found in review and paid

- A face lane raised the ratchet ceiling for a mic false positive; the
  scanner now knows the library StringGadget carries the mic, the
  ceiling LOWERED by 30, and the nudge text field keeps its mic (the
  owner's law: a mic on every input).
- The CI history collector assumed a `Database.automations` handle the
  steward test fakes lack; guarded (best-effort, never blocks OBSERVE).
- A nudge step must belong to a real steward run — never a dummy run,
  never foreign keys off.

## Gates

- Counsel on the design: RATIFY-W-C, ruled. Counsel on the built phase:
  PENDING.
- Suite (CI shape): PENDING.
- Web: baseline zero branch-new; ratchet at its (lowered) floor.

## The owner's questions (from counsel, in the handover)

1. The nudge's attribution: tool named, no personal name — how your
   team should read it?
2. Wait in days since the PR was created — the honest approximation —
   acceptable?
3. The 7-day cooldown shown as `NUDGED N D AGO` — keep?

## His word

Design canvas above; **PR #556** stacked on #555. Merge order stays his:
#553 → #554 → #555 → 173's.
