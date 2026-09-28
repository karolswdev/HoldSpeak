# PHILO-10-01 - The Send contract, saved destinations and the file channel

- **Project:** holdspeak-philo
- **Phase:** 10
- **Status:** done
- **Depends on:** the owner's ratification; his answers to Q4 and Q5
- **Unblocks:** PHILO-10-02, PHILO-10-03, PHILO-10-04 (build), PHILO-10-05, PHILO-10-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
- **Closure finding:** `docs/internal/philo/phase-10/grounding/README.md` F1, F2, F3, F6, F7, F12, F14, F15; Codex Astra r1 findings 1–5 (`checks/charter-astra-r1.md`)
- **Design:** `design/send-lifecycle.md` (binding)
- **Canvas:** none (story 04 owns the face)

## Problem

Nothing sends a published project update: it is copy and confirm (`holdspeak/db/schema.py:4170-4186`, F1). The write seam exists (`holdspeak/plugins/gated_connector.py:127-288`, F2) but no channel, no saved destination and no send record exist. The one file-write connector overwrites without a word (`holdspeak/plugins/builtin/followup_ticket_actuator.py:112-146`; probed, F7).

## Scope

- **In:** the declared operations of the charter's admission table (names fixed in the first commit, checked by Codex Astra); a channel registry that is a dict (no new framework); the document shape `{ref, title, body_md}` and the update's renderer; the two records and the additive `project_update_deliveries` columns (design section 1); prepare and press, one wins (section 2); the payload file and the digest check before dispatch, the size limits, redacted errors — an excerpt of the payload and a secret are redacted, not only a whole line (section 3); the durable dispatch boundary, the recovery that never dispatches again, the outcome mapping (section 4); the scoped kernel change for recovery across take-over AND reaping — the reaper's settle effect, the take-over's terminal effect, the replay hook — and fences R1–R6 over both forms (section 4a); the frozen target, park-not-delete, `destination_changed` / `destination_parked` (section 5); the file channel as the one direct writer (a new file per send with a collision-proof suffix and exclusive create as Q4 rules, path + sha256 read back + size, `realpath`, the owner's synced mark); the manual channel unchanged.
- **Out:** the other channels (02, 03); the CLI seam — the `WriteConnectorManifest` + `plan` + `interpret` entries and the owner principal, the parent and the broker threaded through `build_gated_connector` → `run_subprocess_operation` (design section 6) — and the CLI outcome clauses, both moved to story 02 with their first user (round two, Codex Astra r1 finding 5); the steward preparing a send (story 02); the face (04), except the one correction below; other documents (BACKLOG).

## Acceptance criteria

- [x] The operations are declared once and reachable by HTTP, MCP and the rig's `op` step, over one service.
- [x] Each admitted row is one kernel operation with one terminal receipt; each refusal class (destination not saved, owner only, not published, preview changed) leaves its receipt; reads and previews leave none. Fences with an authenticated principal; a mutation of each turns it red.
- [x] The file channel: two sends of one update to one folder make two files; the record holds path, sha256 and size, and the sha256 equals the bytes on disk; a name that tries to leave the folder is refused.
- [x] The crash rule: through the Room's real take-over (`holdspeak/services/project_kernel.py:398-400`, `:528-531`), a settle write that fails after the effect, a restart during `dispatching`, a kill and a timeout each end with **one** dispatch and UNKNOWN (or the file's read-back proof) — red on main (Codex reproduced two dispatches for one key); for the file channel, an OS error off the pinned list and bytes that do not read back are UNKNOWN, never FAILED (the CLI forms — a nonzero exit off the pinned list, a missing or malformed proof — are story 02's); the same key again makes no second effect.
- [x] Fences R1–R6 (design section 4a), parametrized over the `send_id` form and the inline form, each red on the round-two design and green here: one dispatch, one terminal receipt, one history row per key across take-over, the real reaper, a restart and replay; the three mutations turn them red.
- [x] No body in a kernel row, a receipt, the journal, a log or an error (a sentinel fence); the redactor removes an excerpt of the payload and a secret; the payload file is 0600 in a 0700 directory and its digest is checked before dispatch; an oversize payload is refused by name. (No body in argv or a subprocess receipt: story 02, with the first CLI channel.)
- [x] A destination changed or parked after prepare is refused before dispatch, checked inside the boundary transaction (a Remove that commits first wins: nothing dispatched; one after the boundary parks and the send stands); the row keeps the historical target; Remove parks.
- [x] (Round two, Codex Astra r1 finding 1.) A send whose result is UNKNOWN is never shown as a delivery on the Room's existing face: `DELIVERED ×N` and the history head count only delivered rows; the UNKNOWN row reads `⚠ RESULT UNKNOWN · CHECK <destination>`; fenced as rendered at 1440 and 393 through the real producer. (A face change on an already-ratified species, forced by a correctness regression: for the owner's canvas review in story 04.)
- [x] An agent's send is refused `owner_principal_required` with a receipt; an agent's prepare completes under its own identity (as Q5 rules), survives a restart with its preview, and Send and Discard pressed together settle once (one wins, the other refused with a receipt).
- [x] Existing manual rows read `channel: manual`; `project.mark_update_delivered` is unchanged (its Phase 9 fences stay green).

## Effort (not a promise)

PROVISIONAL: 3.5–4.5 engineering days (until the design is checked).

## Test plan

- **Integration:** fences through the real hub on an isolated HOME (the Phase 9 story 02 pattern); a recording runner minted through each channel's real `plan`.
- **Rig:** `op` steps that read the send's receipt and the record row.

## Notes

- 2026-09-28 — ROUND TWO on Codex Astra r1 DO-NOT-RATIFY (`checks/story-01-built-astra-r1.md`): the UNKNOWN row on the Room's face, the destination re-checked inside the boundary transaction, the redactor on excerpts and secrets; the CLI seam and its clauses moved to story 02 (Scope and criteria amended); the steward's prepare given to story 02; the kernel line budget (426 → 432, this story's six lines) kept explicit.
- 2026-09-28 — BUILT by the Fedaykin lane (Opus 5.5): the nine `channel.*` operations, the two records and the four additive columns, the dispatch boundary and its recovery (seams 1–3; R1–R6 over both forms, R3 through a real SIGKILL), the file channel; 16/16 mutations caught. Unpaid and deviations: `evidence-story-01.md` (the CLI seam's plumbing moves to story 02 with its first user; the steward's prepare is not built).
- 2026-09-28 — round three: Codex Astra r2 condition 1 (section 4a) added.
- 2026-09-28 — round two: amended on Codex Astra r1 DO-NOT-RATIFY (`checks/charter-astra-r1.md`); bound by `design/send-lifecycle.md`.
- 2026-09-28 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
