# HS-92-10 — The owner walk and evidence close

- **Project:** holdspeak
- **Phase:** 92
- **Status:** in-progress
- **Depends on:** HS-92-01, HS-92-02, HS-92-03, HS-92-04, HS-92-05, HS-92-06, HS-92-07, HS-92-08, HS-92-09
- **Unblocks:** none
- **Owner:** unassigned

## Problem

This phase can look coherent in fixtures while still requiring the author's
mental model on real devices. Closure requires one continuous Desk-centered
owner walk, real microphones/models/endpoints/failures, actual Swift evidence,
terminology and trust censuses, and measurable comparison to the research
baseline. Responsive Web screenshots cannot waive native acceptance.

## Scope

- **In:** Full automated suites and architecture/term/secret guards; ten-journey
  owner campaign; actual Web desktop/compact and physical iPhone/iPad captures;
  accessibility and fault campaigns; performance/memory/first-value measures;
  docs/canon/UAT reconciliation; defect sweep; phase close artifacts only after
  every gate is satisfied.
- **Out:** Waiving a failed journey; crediting companion/classic/simulator or
  responsive Web evidence to the flagship; unrelated feature work; creating
  evidence/final-summary before real execution.
- **Paths:** `scripts/web_ui_audit.py`, `scripts/uat_site_walk.py`, `uat/`,
  `tests/`, `apple/Tests/`, `web/src/test/`, `docs/`,
  `pm/roadmap/holdspeak/README.md`, every Phase-92 story/evidence asset, and the
  Delivery Workbench commands named below.

## Acceptance criteria

- [ ] All ten primary journeys run from the production Web and canonical Swift
      roots with Desk entry/return, focused-room context, durable result or
      receipt, and deliberate platform differences recorded.
- [ ] The owner walk includes first-run/basic dictation, live meeting/recovery/
      aftercare/sync, organize/ground, Persona and Workflow runs, five placement
      classes, pairing, one Integration, review/approval/grant, waiting Coder,
      forced failures, and next-day return.
- [ ] Real first-value steps/decisions/time, capture memory/recovery bounds,
      ambiguous-verb count, canonical-term parity, silent-failure count,
      detached-surface count, and Desk-return percentage meet the phase exit
      thresholds with raw measurements attached.
- [ ] Web audit passes desktop and compact; physical iPhone/iPad evidence covers
      orientation, permissions, lock/route change, offline, pairing, capture,
      sync, model run, approval, steering, VoiceOver, Reduce Motion, and
      accessibility text.
- [ ] Python, Web, Swift, contract fixtures, UAT, secret scans, auth/policy
      invariants, generated API surface, docs drift, and packaging/build checks
      are green with captured command output.
- [ ] `README.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `docs/MODELS.md`,
      `docs/WEB_DESK.md`, meeting/dictation/integration guides, product language,
      UAT feature ownership, and scenarios state the shipped terms and limits.
- [ ] No existing phase/story is changed to done by this work; HS-92-10 and
      Phase 92 close only with paired evidence files and a genuine
      `final-summary.md` under Delivery Workbench rules.
- [ ] `.githooks/dw check holdspeak`, `.githooks/dw gate`, and repository status
      show a structurally clean, intentionally scoped close.

## Test plan

- **Unit:** `uv run pytest -q tests/unit`; `cd web && npm test -- --run && npm run typecheck && npm run build`; `cd apple && swift test` (or repository-canonical equivalents captured at execution time).
- **Integration:** `uv run pytest -q tests/integration tests/e2e --ignore=tests/e2e/test_metal.py`; targeted real-metal tests separately; full UAT conductor campaign for Phase 92 features; `scripts/web_ui_audit.py`; generated API/product-language drift checks.
- **Manual / device:** Signed owner verdict on the exact production Web build and
  exact flagship iPhone/iPad artifacts, with build/commit/device/OS/model/audio
  route provenance and all captures stored under story evidence assets.

## Notes / open questions

If any primary journey fails, keep the story and phase open. Defects discovered
here belong in this story only when they are necessary to meet an existing
acceptance criterion; unrelated discoveries become later candidates.
