# PHILO-11-07 - The closing use

- **Project:** holdspeak-philo
- **Phase:** 11
- **Status:** done
- **Depends on:** PHILO-11-01 through PHILO-11-06; the targets he names (stated default D3); a Slack webhook from him for the Slack leg
- **Unblocks:** the phase close
- **Owner:** Muad'Dib's lane; Astra checks
- **Closure finding:** the charter's exit 8
- **Design:** `design/document-sources.md`
- **Canvas:** none

## Problem

The new kinds and Slack are proven only on isolated hubs and recording edges until a real send reaches the far side.

## Scope

- **In:** two legs, kept apart. (A) The rehearsal: a cold Codex session (the Phase 9 R3 setup: scratch root, HOME and CODEX_HOME with the auth file only, the isolated hub the only MCP server, zero repository reads in the retained log) prepares a send of a new kind from the MCP catalogue alone; the owner's Send is pressed on the face at 1440 and 393. (B) The real sends, on his own session, to the targets he names: each family (brief, decision, meeting summary) on each channel he has — file, GitHub (scratch issue #699), email through Resend, Slack if he gives a webhook, Jira and Confluence if his accounts are set; each of the eight kinds at least once on the file channel; each proof read back from the far side, or a named limit with its reason.
- **Out:** a sitting (owner-reviewed shots only).

## Acceptance criteria

- [x] The cold session prepares; the face shows PREPARED by that agent; his Send ends SENT (or POSTED) with its proof at both widths, read back from the hub.
- [x] The Slack text length of each real brief sent is recorded against the Q1 limit (the Tuesday claim is conditional on it; Astra r1 finding 9).
- [x] Each real send's proof read back from the far side, or its limit named. Secrets, addresses and the webhook URL redacted at capture.

## Effort (not a promise)

PROVISIONAL: about 1 engineering day, plus the real-send legs.

## Test plan

- **Rehearsal:** the cold session on an isolated hub; glass at both widths.
- **Real sends:** his session; the far side read back.

## Notes

- 2026-10-01 — DONE (evidence `evidence-story-07.md`). Leg A: a cold Codex session (DESK credential) prepared the brief and a decision record from the MCP catalogue alone; its Send was refused `owner_principal_required`; the owner's Send on the face (Chair, Intelligence → DECISIONS) ended SAVED at 1440 and 393, read back from the hub. Leg B: 11 real sends, exactly once each: the eight kinds to `~/Documents/HoldSpeak`, the brief, the decision record and the meeting summary to issue #699; every far side read back byte for byte, no transcript and no internal id. The brief's Slack text: 566 / 39,000. Named limits: email (no Resend details), Slack (no webhook), Jira and Confluence (no accounts). Owner review of the shots is pending; never a sitting.
- 2026-09-29 — round two: amended on Astra r1 RATIFY-WITH-CONDITIONS (`checks/charter-astra-r1.md`).
- 2026-09-29 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
