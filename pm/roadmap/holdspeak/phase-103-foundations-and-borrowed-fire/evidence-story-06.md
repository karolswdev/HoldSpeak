# Evidence - HS-103-06

- **Story:** HS-103-06 - Closeout
- **Status:** done (machine proof + drift-check + retrospective +
  the owner's second-sitting acceptance, 2026-07-25 — see the final
  section)
- **Date:** 2026-07-22

## Machine proof (the assembled chain)

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — 4143 passed, 37
  skipped, 7 failed on this run. 6 of the 7 are the SAME pre-existing,
  unrelated failures documented in every one of this phase's evidence
  files since HS-103-02 (a stale generated API-surface manifest/ledger,
  reproduced identically against a `git stash` of every phase-103
  change). The 7th, `test_live_bus.py::test_a_real_broadcast_reaches_the_presence_card_via_the_bus`,
  is new to THIS run — investigated and confirmed order-dependent
  flakiness, not a regression: it passes cleanly in isolation
  (`uv run pytest -q tests/e2e/test_live_bus.py` → 3 passed), fails
  only inside the full-suite run with a background-thread
  `sqlite3.OperationalError: no such table: meetings` (a torn-down-db
  race from an unrelated prior test's teardown timing, in
  `holdspeak/web/routes/meeting_import.py` / `holdspeak/db/meetings.py`
  — neither file touched by any HS-103 story). Not counted as a new
  failure attributable to this phase.
- `cd web && npx tsc --noEmit -p .` — clean.
- `npx vitest run` — 318 passed, 50 files.
- `npm run build` — clean (chunk-size warning only, pre-existing).
- `npm run tokens:gate` — clean (61 allow-listed exceptions, all in use).
- `uv run pytest -q tests/unit/test_web_vocabulary_guard.py
  tests/unit/test_interior_canon_guard.py
  tests/unit/test_doc_drift_guard.py` — 33 passed (includes HS-103-02's
  new dash-in-glass rule).

## Per-story drift-check (research finding vs. what shipped)

**HS-103-01 (session restoration).** The audit named TWO defects:
(a) no persistence for the open-window set (`SurfaceWindows.tsx:199`),
(b) a `resetLayout()` leak leaving stale geometry on an open window
(`store.ts:871`). Shipped: (a) fixed and proven live — reload now
restores the same windows at the same rects, both viewports. (b) was
investigated with a targeted regression test BEFORE any fix and found
NOT to reproduce on the current codebase — confirmed a second time
live, headed, on a staged hub. **No drift**: (a) is closed exactly as
named; (b) is an honest "this finding didn't hold" report, which the
story's own acceptance criteria explicitly anticipated ("report what's
actually found rather than forcing a clean story"). The regression
test now pins the correct behavior against future regression either way.

**HS-103-02 (voice guard on glass).** The audit named exactly 3 dash
instances. Shipped: extended the guard, ran it once before any content
fix, and it surfaced 33 offending lines, not 3 — all fixed. **No
drift**: the gap named (dash-in-prose has no glass-level guard) is
closed; the story's own scope explicitly required sweeping beyond the
3 named lines ("fix what's found, don't just satisfy the three named
ones"). A pre-existing false-positive bug in the SHARED scan helper
(comments misread as strings) was also fixed as a direct consequence
of extending the same machinery — in scope, not adjacent.

**HS-103-03 (grounding verification).** The research finding named
researchmind's claim-decomposition + citation-entailment pattern as
the carry-over. Shipped: `entailment_score`/`classify_support`
(entailed/partial/unsupported)/`decompose_claims`/`score_claims`, wired
into Ask-AI (the story's own "pick the cheaper integration" choice,
not meeting artifacts). **No drift**: the mechanism, its three-band
classification, and the "soft signal, never a hard verdict" framing
all match the named finding precisely.

**HS-103-04 (endpoint health).** The research finding named
`provider_resilience.py`'s FULL shape: a circuit breaker AND a
`score()`/`rank()` that reorders a provider list. Shipped: the circuit
breaker half only (`check`/`record_success`/`record_failure`/
`snapshot`) — no ranking/reordering. **This is a deliberate, named
scope narrowing, not undisclosed drift**: the story's own Scope section
explicitly puts "provider RANKING/reordering when only one endpoint is
configured" OUT, reasoning that HoldSpeak has one live provider on the
common path today so reordering a list of one has no value. Flagging
it here anyway, plainly, since the closeout's job is to check against
the RESEARCH finding, not just the story's own acceptance criteria —
and by that stricter bar, half of what researchmind offered was
deliberately left on the table. Correct call, worth recording as a
conscious choice rather than letting it pass silently.

**HS-103-05 (steering demo recipe).** The finding: no recipe combines
a populated desk with a live armed steering pane, so the flagship
feature is unverifiable by an outside auditor. Shipped: exactly that
composed recipe, plus a correction the investigation surfaced —
the story's OWN acceptance criteria said "the Agents surface" but the
real UI path is the search-shelf's "Panes" drawer, not `CompanionCore`'s
Agents tab (a different, unrelated registry). **No drift**: the gap is
closed; the correction is a precision fix to the story's own wording,
not a scope change.

## Retrospective: was the four-agent research method worth it?

Yes, with one important caveat surfaced by this same phase. The
external three converged rather than fragmented: two independently
(no shared context) named the same ~50-line file as the one portable
idea, which is a stronger signal than any single agent's opinion, and
the synthesis correctly used that convergence to REJECT the third
external agent's own favorite pick (governance-as-data) as solving a
problem HoldSpeak doesn't have — a single-agent pass has no such
cross-check available. The internal audit's hands-on, live-driven
scrutiny found two real, cheap-to-fix gaps (HS-103-01's durability
bug, HS-103-02's guard hole) that plausibly a code-only review would
have missed, since both required actually exercising the running
product to notice. The caveat: that SAME internal audit's second named
defect (`resetLayout()`) did not reproduce under investigation — a
live, hands-on agent's diagnosis still needs independent verification
before committing engineering time to "fix" it, exactly as this phase
did. Net: worth repeating for "what should we build next, and what's
actually broken" questions — but every finding, from any agent,
external or internal, earns a verify pass before it's trusted as
ground truth, not just the ones that sound uncertain.

## The owner's sitting (Article IX.4) — recorded

**2026-07-22.** The owner sat with the assembled Phase 103 chain.
Verdict, verbatim: "the parts of talking with the AI, the chat
interface, and so on - still need a bettered quality pass and a much
more streamlined and 'oh, I'm talking to a real cool part of the
system' kind of vibe... so all the AI Chat interfaces, bud. They need
2 notches better." Asked directly whether this closes Phase 103 with
the AI-chat quality work spun into a new, later phase, or whether it
holds Phase 103 open until the chat surfaces improve, the owner chose
explicitly: **hold Phase 103 open.**

No drift was found in HS-103-01 through HS-103-05 (see above) — the
five build stories themselves stand. The verdict names a real gap the
research-derived charter never asked any of the five stories to touch
(none of the four research findings were about chat-interface visual
craft), so this isn't a story failing its own bar — it's the owner's
felt judgment surfacing a dimension the machine-checkable acceptance
criteria structurally couldn't see. **HS-103-06 (this story) now also
depends on HS-103-07** ("The AI chat surfaces feel like a cool part of
the system," scaffolded the same sitting, scope grounded in a live
screenshot survey of `AskPanel.tsx`, `PersonaChat.tsx`, and
`SessionPullout.tsx`'s steer composer) — closeout stays `in-progress`
until HS-103-07 ships and a second, shorter sitting confirms the "2
notches better" bar is met.

## Post-repair machine proof refresh (2026-07-25, on merged main)

Context: PR #367 (the Phase 104/105 scaffolds + kernel RFC) carried a
CI-debt repair commit (`8fbfb380`) that paid exactly the failure
family this evidence documented as pre-existing since HS-103-02: the
stale generated API-surface manifest (regenerated via
`scripts/gen_api_surface.py`, 333 routes) and four integration tests
asserting pre-refit copy (assertions updated to the shipped
HS-100-07/102-04/102-06 compositions, non-vacuously). All five were
first reproduced on unmodified main at `024635b3` (targeted run:
5 failed) proving them inherited, then fixed, then CI ran fully
green on `ecc83080` (all six checks SUCCESS; merged as `e67b868c`).

Re-run of the assembled chain on merged main, outputs written to
files and read (never chained):

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — **4148
  passed, 37 skipped, 2 failed** in 14:25 (was 4143/37/7 on
  2026-07-22). Of the 2: `test_live_bus.py::
  test_every_live_page_opens_exactly_one_runtime_socket` is the SAME
  order-dependent torn-down-db flake family this file already
  dissected on 07-22 (isolation re-run: `tests/e2e/test_live_bus.py`
  → 3 passed); `test_build_ledger.py::test_committed_ledger_is_up_to_date`
  was real drift CAUSED by the scaffold merge (new roadmap files) —
  remedied exactly as the test names (`uv run python -m
  uat.tools.build_ledger`, features.yaml 4293 lines), re-run read:
  2 passed, shipped direct-to-main as `8952ffee`. Zero unrelated
  pre-existing failures remain.
- `cd web && npx tsc --noEmit -p .` — clean. `npx vitest run` — 318
  passed, 50 files. `npm run build` — clean. `npm run tokens:gate` —
  clean (61 allow-listed exceptions, all in use). Identical to the
  07-22 numbers.

The one remaining input for this story is unchanged: the owner's
second sitting confirming HS-103-07 meets the "2 notches better"
bar. Sitting staged on a live seeded hub (`seeded-desk-43`,
`http://localhost:8788/`, intelligence on the LAN llama.cpp at
192.168.1.43:8080, both health-checked).

## The owner's second sitting verdict (2026-07-25)

The owner sat the staged desk (`seeded-desk-43` on
`http://localhost:8788/`, real intelligence on the LAN llama.cpp)
against the three chat surfaces HS-103-07 re-crafted. Verdict,
verbatim: **"I accept."**

Per the 07-22 record above, this second sitting was the one
remaining dependency: HS-103-07 shipped (the egress/receipt clutter
fix, turn-entrance motion, the warmer empty state, shared
send-press feedback), the machine chain was refreshed post-repair
(zero unrelated failures), and the owner's acceptance confirms the
"2 notches better" bar is met. HS-103-06 flips done; Phase 103
closes 7/7.
