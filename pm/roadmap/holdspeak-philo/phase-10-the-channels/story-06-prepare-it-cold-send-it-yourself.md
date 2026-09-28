# PHILO-10-06 - Prepare it cold, send it yourself

- **Project:** holdspeak-philo
- **Phase:** 10
- **Status:** backlog
- **Depends on:** PHILO-10-01 through PHILO-10-05; the owner's answer to Q6
- **Unblocks:** the phase close
- **Owner:** Astra (Luna) drives the cold session; Muad'Dib checks
- **Closure finding:** the charter's exits 5 and 8
- **Canvas:** none

## Problem

The owner's job: an agent gets the update ready to go; he looks once and presses Send; it is where it should be, with proof.

## Scope

- **In, leg A (isolated rehearsal):** a cold-context Codex session (the Phase 9 R3 setup; zero repository reads in the retained log) finds a published update and a saved destination from the catalogue alone and prepares a send; the owner's Send is pressed on the face (rehearsed: the rig presses as the owner on an isolated hub); the Room shows SENT with its proof at 1440 and 393, read back from the hub; the same session's attempt to send is refused `owner_principal_required` with a receipt. 
- **In, leg B (the real-account leg, kept apart):** only to targets the owner authorized under Q6, on his own session (a scratch HOME does not isolate the keychain logins of `gh` and `acli`, and the email leg needs his SendGrid key and verified sender): one send per channel, each proof read back from the far side, redacted at capture; the email proof is SendGrid's `X-Message-Id`, and the mail is found in his inbox.
- **Out:** a sitting (never recorded as one).

## Acceptance criteria

- [ ] The prepared send, the owner's press, the record and the receipt read back from the hub; the agent's own send refused with its receipt.
- [ ] The face at both widths shows PREPARED, then SENT with the proof.
- [ ] Leg B as Q6 rules, recorded apart from leg A, or each limit named.
- [ ] Rehearsed, owner-reviewed shots.

## Effort (not a promise)

PROVISIONAL: about 1 engineering day, plus the real-send legs.

## Test plan

- **Closing use:** the Phase 9 story 06 driver pattern, retained sessions, the zero-read fence.

## Notes

- 2026-09-28 — round two: amended on Codex Astra r1 DO-NOT-RATIFY (`checks/charter-astra-r1.md`); bound by `design/send-lifecycle.md`.
- 2026-09-28 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
