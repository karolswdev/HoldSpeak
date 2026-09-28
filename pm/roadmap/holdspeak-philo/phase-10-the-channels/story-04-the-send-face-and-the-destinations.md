# PHILO-10-04 - The Send face and the destinations setup (canvas first)

- **Project:** holdspeak-philo
- **Phase:** 10
- **Status:** backlog
- **Depends on:** the owner's ratification; the two canvases ratified by the owner; PHILO-10-01 for the build
- **Unblocks:** PHILO-10-05, PHILO-10-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks canvases and build
- **Closure finding:** the charter's state/width matrix
- **Canvas:** two, before any build (UX-CANON §A.2): the Send well under a published update; the destinations setup

## Problem

The update's only outbound verbs are Copy and Mark delivered (`web/src/features/project-room/update/UpdatePosture.tsx:52`, `:696`). There is no place to save a destination and no face for a send's outcome.

## Scope

- **In:** the Send well (in-world, no modal): the saved destinations as rows with their host chips and account states, one pick, the preview as the channel will get it, Send (library Button), the receipt rows for every state of the matrix, PREPARED rows with Send and Discard, HANDED TO MAIL, UNKNOWN after a restart, DESTINATION CHANGED on a prepared row; the Copy and Mark delivered row kept. The destinations setup (the Connections face recommended; the canvas decides): add, check, remove (park; history kept), per-channel fields (folder, with a "synced" mark the owner sets; repository and issue or pull request number; Jira site account and one work item key; Confluence account and space; email account and To list). Words from the ratified canvases (ASD-STE100; no prose; no counter of zero).
- **Out:** a Send well on other documents (BACKLOG); Slack.

## Acceptance criteria

- [ ] Both canvases ratified by the owner (verbatim word recorded) before the build commit.
- [ ] Every state of the matrix shot and fenced through the real hub at 1440 and 393; the face's outcome equals the hub's record and receipt in the same fence.
- [ ] Every verb is the library Button; the host chip is on each row that leaves the machine; no modal; nothing covers the Send verb at 393.
- [ ] The web baseline has zero branch-new failures.

## Effort (not a promise)

PROVISIONAL: 2–3 engineering days (canvases included).

## Test plan

- **Glass:** Playwright fences through the real hub on an isolated HOME at both widths; shots under `.tmp/evidence-shots/` unless the story ships them.
- **Web unit:** the Send well's states.

## Notes

- 2026-09-28 — round two: amended on Codex Astra r1 DO-NOT-RATIFY (`checks/charter-astra-r1.md`); bound by `design/send-lifecycle.md`.
- 2026-09-28 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
