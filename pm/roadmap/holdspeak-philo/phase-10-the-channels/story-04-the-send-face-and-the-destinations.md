# PHILO-10-04 - The Send face and the destinations setup (canvas first)

- **Project:** holdspeak-philo
- **Phase:** 10
- **Status:** done
- **Depends on:** the owner's ratification; the two canvases ratified by the owner; PHILO-10-01 for the build
- **Unblocks:** PHILO-10-05, PHILO-10-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks canvases and build
- **Closure finding:** the charter's state/width matrix
- **Canvas:** two, before any build (UX-CANON §A.2): the Send well under a published update; the destinations setup

## Problem

The update's only outbound verbs are Copy and Mark delivered (`web/src/features/project-room/update/UpdatePosture.tsx:52`, `:696`). There is no place to save a destination and no face for a send's outcome.

## Scope

- **In:** the Send well (in-world, no modal): the saved destinations as rows with their host chips and account states, one pick, a readable preview derived from the frozen payload (never raw XHTML or JSON; Codex Astra r2), Send (library Button), the receipt rows for every state of the matrix, PREPARED rows with Send and Discard, ACCEPTED BY SENDGRID with its message id (never "delivered"), UNKNOWN after a restart, DESTINATION CHANGED on a prepared row; the Copy and Mark delivered row kept. The destinations setup (the Connections face recommended; the canvas decides): add, check, remove (park; history kept), per-channel fields (folder, with a "synced" mark the owner sets; repository and issue or pull request number; Jira site account and one work item key; Confluence account and space; email: the provider, the verified sender (from address and name), the API key saved once into the OS keychain — never shown again — and the To and Cc lists). Words from the ratified canvases (ASD-STE100; no prose; no counter of zero).
- **Out:** a Send well on other documents (BACKLOG); Slack.

## Acceptance criteria

- [x] Both canvases ratified by the owner (verbatim word recorded) before the build commit. (2026-09-29: "Ratify as drawn (Recommended)".)
- [x] Every state of the matrix shot and fenced through the real hub at 1440 and 393; the face's outcome equals the hub's record and receipt in the same fence.
- [x] Every verb is the library Button; the host chip is on each row that leaves the machine; no modal; nothing covers the Send verb at 393.
- [x] The web baseline has zero branch-new failures.

## Effort (not a promise)

PROVISIONAL: 2–3 engineering days (canvases included).

## Test plan

- **Glass:** Playwright fences through the real hub on an isolated HOME at both widths; shots under `.tmp/evidence-shots/` unless the story ships them.
- **Web unit:** the Send well's states.

## Notes

- 2026-09-29 — round three: Codex Astra r2 on #697 DO-NOT-RATIFY (`checks/story-04-built-astra-r2.md`) paid — B11 says what was answered and when (and NOT CHECKED SINCE KEY CHANGE); a held acli lock is a 409 refusal with its receipt and the client honours any refused receipt; the lying Atlassian seed replaced by the real connection-check producer; board 05's receipt centred. Glass 24/24, red first.
- 2026-09-29 — DONE: story 03 merged in (main e22b1b95); the email boards (16–19, B7, B8, B11) fenced on story 03's canned HTTPS edge and in-memory key store; B11's Check reports the sender's verification from the provider's last answer. Every ratified board built and fenced at 1440 and 393 (glass 22/22), each through the real hub with the hub's record in the same fence; web baseline zero branch-new. Evidence: `evidence-story-04.md`; proof table: `assets/story-04-proof/captures.md`. The real-account legs are story 06's.
- 2026-09-29 — board 25 fenced: a real hub process killed mid-send, a second hub on the same HOME, the Room shows UNKNOWN · INTERRUPTED and never sends again (both widths).
- 2026-09-29 — board 14 as ratified (Muad'Dib's ruling): the Atlassian channels check sign-in before the boundary → REFUSED NOT SIGNED IN, nothing sent; a follow-up fix to story 02 carried here (noted in `assets/story-02-proof/captures.md`); red on the story 02 wire, green now.
- 2026-09-29 — story 02 merged in (main 3965c5e1): the GitHub, Jira and Confluence boards (7, 9–15, 20, B4–B6, B9, B10) and SENDING (8, 26b, 26c, 27) fenced on story 02's real channels with the process edge canned; glass 16/16 at both widths, every board measured. Board 14 reads FAILED · NOT SIGNED IN (story 02 records a signed-out switch as a known non-delivery). Owed: the email boards (16–19, B7, B8 save, B11) with story 03 (#696).
- 2026-09-29 — round two: Codex Astra r1 on #697 DO-NOT-RATIFY (`checks/story-04-built-astra-r1.md`) paid — a returned send record joins the one result source (a failed read never hides a known FAILED); a failed Remove stays open, named, with Retry; `dispatch_seq` allocated inside the boundary transaction orders "latest" (the equal-clock sequence fenced); B10's Checked time restored; the armed boards measured. Glass 10/10 at both widths; each fix red on the old face first (`assets/story-04-proof/captures.md`).
- 2026-09-29 — BUILT by the Fedaykin lane (Opus 5.5), branch `feat/philo-10-04`, on main after #694: the SEND well, the PREPARED rows and the one DELIVERY history (`web/src/features/channels/`), the Destinations group in Settings → Connections under Tools (`web/src/pages/cores/connections/Destinations.tsx`), the harness proposal ported into the real species (no shim); A2 on the list and history; the library repairs moved (`gadgets.css`: the 12 px floor and the 44 px narrow target; `provenance.css`, `surface.css`, `connections.css`: the 12 px floor); the steward policy face lists `prepare_send`; story 01's boundary time kept to the microsecond (two sends in one second still have an order for "latest by `dispatch_started_at`"). Glass on the real wire (file channel, a remote agent's prepare, fetch-seam faults) at 1440 and 393: 8/8, shots in `assets/story-04-shots/`; RED on main captured; web baseline zero branch-new. NOT MET: the GitHub, Jira, Confluence and email boards (stories 02 / 03), SENDING across Back → return (story 02's GATE 2). Proof: `assets/story-04-proof/captures.md` (the evidence file comes with the done flip).
- 2026-09-29 — both canvases RATIFIED by the owner ('Ratify as drawn', AskUserQuestion; all six recommendations A1–A3, B1–B3), after Codex Astra r1 DNR → r2 DNR → r3 DNR → r4 RATIFY (`checks/canvases-astra-r1.md` … `r4.md`); the two built face changes (story 01's RESULT UNKNOWN row, story 02's nudge card) accepted with them. The build follows `assets/story-04-send-canvas/` and `assets/story-04-destinations-canvas/`.
- 2026-09-28 — the two canvases drawn (`assets/story-04-send-canvas/`, `assets/story-04-destinations-canvas/`); unratified.
- 2026-09-28 — round four: the email fields follow the owner's Q1 ruling (a provider interface; SendGrid first).
- 2026-09-28 — round three: the readable preview (Codex Astra r2, MISSED).
- 2026-09-28 — round two: amended on Codex Astra r1 DO-NOT-RATIFY (`checks/charter-astra-r1.md`); bound by `design/send-lifecycle.md`.
- 2026-09-28 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
