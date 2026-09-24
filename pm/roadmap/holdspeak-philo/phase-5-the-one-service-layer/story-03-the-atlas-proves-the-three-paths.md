# PHILO-5-03 - The atlas proves the three paths

- **Project:** holdspeak-philo
- **Phase:** 5
- **Status:** done
- **Depends on:** PHILO-5-02
- **Unblocks:** PHILO-5-04
- **Owner:** Astra (Luna); Muad'Dib checks on built
- **Council tag:** Astra r2 findings 3, 7 and the Proof position

## Problem

The rig has no `op` step kind (`scripts/graph_walk.py:2288`); `run_case()` always starts Playwright (`:3603,:3675`); protocol snapshots evaluate the page (`:523`, `page.evaluate`); restart retention is skipped without a page (`:2715`). So the rig cannot prove the contract without a browser, and op-tier proof cannot yet be trusted.

## Scope

- **In:** headless `op` execution in `graph_walk.py` against the owning isolated hub (never a second writer): setup, waiting, observation and restart without a page, charted before any `op` verdict is trusted; the `.op` siblings of the named atlas pairs (phase status, "Named atlas pairs") minted and run; equivalence between the `api`/`op` path and the browser path; real-engine and replayed runs retained separately; browser face walks at 1440/393 retained independently.
- **Out:** everything the phase status lists as out; replacing any face case; `api` steps (they stay for HTTP contracts).

## Acceptance criteria

- [x] The headless path is charted and proved: an `op` case runs setup, waiting, observation and restart with no page opened; the `op` step reaches the registry inside the owning isolated hub.
- [x] Every named pair has its `.op` sibling, minted and run: the closure chain s1–s4; `case.a1.decision_face_create.opens_and_reopens` and its invalid-status refusal; `case.a3.brief_next_day.decision_on_the_face` with `case.a3.brief_next_day.new_id_with_the_decision`; `case.closure.chain.s5_next_day_brief_has_it` and `s5_next_day_brief_with_breakage`; `case.philo404.arrival_triaged_headline.all_handled` with the shelf operations; `case.j11.thought_keep.receipt_time` with saved-body/revision/time; from `atlas.json` the summary no-transcript/no-assignment refusals, same-day brief identity, shelf acknowledged/deferred/refused.
- [x] Equivalence = durable outcome + identity relationships + refusals; never identical envelopes or independently generated model text.
- [x] Real-engine and replayed-provider runs are retained and labelled separately; a replay is never reported as real-engine.
- [x] The browser face walks at 1440 and 393 are retained independently; no face case loses its selector or is "proved" by `op`.
- [x] Atlas counts reported over both named files (`atlas.json`, `atlas-phase3.json`), excluding archived variants; duration measured and recorded, not promised.
- [x] Fence law: every behavioural fence is red pre-fix through the real producers (real services, the real hub, the real lock and config paths — no test double that lies about the field the check reads); new structural invariants are proved by deliberate mutations that turn the fence red. An import failure or an unavailable symbol is not the required red.

Proof for each box: [lane report, per-box table](story-03-lane-report.md#proof), [paired runs](assets/story-03-shots/pairs.json), [browser observations](assets/story-03-shots/faces.json), and [captured evidence](evidence-story-03.md). Muad'Dib's [precommit check](checks/story-03-precommit-muaddib.md) ratified with record conditions, paid as recorded.

## Effort (council-style estimate, not a promise)

3–4 days (Astra r2)

## Test plan

- **Unit:** the rig's `op` step, headless snapshot and headless restart retention, each red pre-fix (today they require a page).
- **Registry reach:** the unit wrapper composes the real application root in-process. Reach through a spawned owning hub is proved separately by actual `/api/mcp` operation runs and the proxy restart test.
- **Integration:** the named pairs through `scripts/graph_walk.py` (`op`, `api` and browser), observations retained under this phase's assets; real and replayed runs in separate folders.
- **Manual / device:** none (proof mode: rehearsed; story 04).

## Notes

- 2026-09-24 — chartered from draft r3 + Astra r2 (`checks/charter-astra-r2.md`, the named atlas coverage and the Proof position; Muad'Dib's acceptance: the headless path is charted here before any `op` verdict is trusted).
