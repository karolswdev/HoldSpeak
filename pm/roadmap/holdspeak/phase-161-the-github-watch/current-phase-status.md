# Phase 161 - Project Rooms: The GitHub Watch (P2a)

**Last updated:** 2026-09-01 — CHARTERED off main `34e330a2` (160 merged; anchors re-verified: GitHubWatchSource@43, diff_snapshots@118, test/baseline@234/296, setup suggest@237, provider_connections@3693 empty, zero P2a squatting, gh authenticated as karolswdev).

## Goal

The proving V0 slice under the owner's delivery=GitHub ruling: a
REAL provider joins the interview — authenticated connection status
reported by the server (never guessed from a binary), repository
discovery with the typed-repo fallback, precise PR Watches compiled
from the §8.1 templates, a LIVE bounded test showing current PRs,
baseline without false history, and manual evaluation feeding
normalized PR observations into the Delta the owner already reviews.
Exit is a STOPWATCH: one live tested Watch and populated Now in
under five prepared-fixture minutes, measured like 156-07. Domain
slice P2a (§14) + setup slice V0-B (§15); PROV-001..011, §8.1,
WAT-001..005, SETFLOW-001/003/004.

Constitution: Art III.2 (the egress badge at the point of decision —
GitHub reads CROSS EGRESS; the badge and the receipt arrive with
them, NFR-009/DOM-014 now bite for real), Art VI (auth honesty:
installed ≠ connected ≠ ready), Art IX (the stopwatch is a number,
not a vibe; OWNER VERDICT closes the face). No writes, no webhooks
(V0-E later).

## Scope

- **In:** the seven stories below; PR from
  `feat/project-rooms-p2a-the-github-watch`. The 160 debt S-2
  (decide→create_item split transaction) is PAID in this phase's
  close.
- **Out:** GitHub writes/webhooks (V0-E), Jira (P7), scheduling
  (P5), MCP exposure (P6), model assistance.

## Exit criteria (evidence required)

- [ ] §14 P2a exit: the owner reaches one LIVE tested Watch and populated Now in under five prepared-fixture minutes — the stopwatch MEASURED on glass (06), segments itemized.
- [ ] Connection truth (PROV-003/SETFLOW-003): auth status reported server-side; installed-but-unauthenticated → owner_action_required + Recheck, setup preserved; GitHub never appears active before a passing test.
- [ ] The live test shows repo, normalized query, entity count, ≤5 representative PRs, present conditions, observed time, typed errors (§8.1); zero matches with a successful read = PASS.
- [ ] Every GitHub read crosses egress THROUGH the kernel with a receipt and shows the badge at the point of decision (NFR-009/DOM-014/WEB-VIS-005) — the first provider egress of the arc, done lawfully.
- [ ] Manual evaluation lands watch.transition observations in the 160 Delta (the arc compounds: a real PR change appears as evidence-linked Delta).
- [ ] S-2 paid: decide→create_item joins one transaction (or the reorder), fault-proven.
- [ ] Shots 1440+393; beauty; THE OWNER'S VERDICT closes 05; sweep/web/counsel clean.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-161-01 | The provider adapter (real auth status, discovery, typed fallback, egress receipts) | done | [story-01-the-provider-adapter](./story-01-the-provider-adapter.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-161-02 | The compilation (§8.1 templates → WatchSpec@1; GitHub joins the interview's inventory) | done | [story-02-the-compilation](./story-02-the-compilation.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-161-03 | The live test + baseline + manual evaluation (into the Delta) | backlog | [story-03-the-live-test](./story-03-the-live-test.md) | - |
| HS-161-04 | The wire (provider routes, api-surface) | backlog | [story-04-the-wire](./story-04-the-wire.md) | - |
| HS-161-05 | The face (Check connection → Discover → Clarify → Test; auth honesty — shots + verdict) | backlog | [story-05-the-face](./story-05-the-face.md) | - |
| HS-161-06 | The stopwatch walk (< 5:00 measured; + one real-metal leg) | backlog | [story-06-the-stopwatch-walk](./story-06-the-stopwatch-walk.md) | - |
| HS-161-07 | The close (gates, S-2 paid, final summary) | backlog | [story-07-the-close](./story-07-the-close.md) | - |

## Where we are

2/7. 02 DONE — the compilation. The five §8.1 templates
(review_queue, ci_health, merge_flow, delivery_drift,
release_readiness) live as a closed data table + one compile() in
pure `holdspeak/github_templates.py`; EVERY output passes
watch_validation (parametrized truth table) — no validator widening
was needed, the §8.1 vocabulary mapped cleanly. GitHub joined the
interview: suggest() consults the LIVE adapter's connection_status
(INT-007) — connected ⇒ five candidates beside natives; any other
state or no adapter ⇒ ZERO (no grey theater). clarify_repo_scope:
discovered list AND typed fallback, both validated; PROV-011 proven
(candidates never name un-surfaced repos). Cadence-preset duplication
(circular-import break) is pinned by a field-parity test. Proposals
persist identically to natives. Next: 03 the live test + baseline +
manual evaluation into the Delta. Chain: 03 → 04 → 05 ∥ 06(rig after
05's functional) → 07. All standing laws carry.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Egress without admission | medium | verify the runner's existing kernel path FIRST; every new gh call rides the same chokepoint | a gh invocation with no receipt |
| The stopwatch becomes vibes | low | the rig measures wall clock per segment; the bar is an exit criterion | a close without the number |
| Discovery flakiness (network) | medium | prepared fixtures for the bar; the real-metal leg separate + marked; typed-repo fallback always works | a fixture faking readiness (the SRS forbids it twice) |
| Auth theater | medium | PROV-003: server-reported status; SETFLOW-003 legs | a "connected" badge with no authenticated probe |
