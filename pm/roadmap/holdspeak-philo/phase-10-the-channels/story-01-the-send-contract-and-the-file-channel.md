# PHILO-10-01 - The Send contract, saved destinations and the file channel

- **Project:** holdspeak-philo
- **Phase:** 10
- **Status:** backlog
- **Depends on:** the owner's ratification; his answers to Q4 and Q5
- **Unblocks:** PHILO-10-02, PHILO-10-03, PHILO-10-04 (build), PHILO-10-05, PHILO-10-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
- **Closure finding:** `docs/internal/philo/phase-10/grounding/README.md` F1, F2, F3, F6, F7, F12, F14
- **Canvas:** none (story 04 owns the face)

## Problem

Nothing sends a document for him: the update is copy and confirm (`holdspeak/db/schema.py:4170-4186`, F1). The write seam exists (`holdspeak/plugins/gated_connector.py:127-288`, F2) but no channel, no saved destination and no send record exist. The one file-write connector overwrites without a word (`holdspeak/plugins/builtin/followup_ticket_actuator.py:112-146`; probed, F7).

## Scope

- **In:** the declared operations of the charter's admission table (names fixed in the first commit, checked by Codex Astra); a channel registry that is a dict of `WriteConnectorManifest` + `plan` + `interpret` (no new framework); the document shape `{ref, title, body_md}` and the update's renderer; additive columns on `project_update_deliveries` (`channel` default `manual`, `destination_id`, `outcome`, `proof_json`) written in the send's terminal transaction; the destinations table (no secret); the preview digest frozen at admission and checked before the effect (F14's law); the outcome model (SENT, REFUSED, FAILED, UNKNOWN; one key per press; no automatic re-send); the prepared send (the kernel's hold awaiting the owner's decision, or a small table if the hold's expiry does not fit — decided in the first commit); the file channel (a new file per send as Q4 rules, path + sha256 read back + size, the `local`/`cloud` badge rule); the manual channel unchanged.
- **Out:** the other channels (02, 03); the face (04); other documents (BACKLOG).

## Acceptance criteria

- [ ] The operations are declared once and reachable by HTTP, MCP and the rig's `op` step, over one service.
- [ ] Each admitted row is one kernel operation with one terminal receipt; each refusal class (destination not saved, owner only, not published, preview changed) leaves its receipt; reads and previews leave none. Fences with an authenticated principal; a mutation of each turns it red.
- [ ] The file channel: two sends of one update to one folder make two files; the record holds path, sha256 and size, and the sha256 equals the bytes on disk; a name that tries to leave the folder is refused.
- [ ] A timeout after dispatch (a recording runner that raises after the effect) is UNKNOWN in the record, the receipt and the answer; the same key again makes no second effect.
- [ ] An agent's send is refused `owner_principal_required` with a receipt; an agent's prepare waits for the owner (as Q5 rules).
- [ ] Existing manual rows read `channel: manual`; `project.mark_update_delivered` is unchanged (its Phase 9 fences stay green).

## Effort (not a promise)

PROVISIONAL: 2.5–3.5 engineering days.

## Test plan

- **Integration:** fences through the real hub on an isolated HOME (the Phase 9 story 02 pattern); a recording runner minted through each channel's real `plan`.
- **Rig:** `op` steps that read the send's receipt and the record row.

## Notes

- 2026-09-28 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
