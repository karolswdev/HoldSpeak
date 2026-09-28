# PHILO-10-03 - The email channel

- **Project:** holdspeak-philo
- **Phase:** 10
- **Status:** backlog
- **Depends on:** PHILO-10-01; the owner's answers to Q1 and Q6
- **Unblocks:** PHILO-10-05, PHILO-10-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
- **Closure finding:** `docs/internal/philo/phase-10/grounding/README.md` section 4, F10, F11
- **Canvas:** the email destination's fields are on the story 04 setup canvas

## Problem

He picked "Email". HoldSpeak has no mail path. The transports differ in custody, proof and cost (grounding section 4). Mail.app's `send` answers only true or false (F10).

## Scope

- **In:** the transport Q1 picks. Under (b), recommended: `osascript` builds one outgoing message (To from the saved destination, subject from the document's title, the body as plain text) from the account the destination names, and sends it; the script is the argv of a `subprocess.exec` child of the send, so the admission binds it; proof HANDED TO MAIL; the first-use Automation prompt proven on his desk and named. Under (a): `smtplib` over TLS as an `external.egress` child to the saved host; the password in the macOS keychain through `keyring` (the People custody precedent); proof the `250` answer and the Message-ID HoldSpeak writes.
- **Out:** HTML mail unless the owner asks (then `markdown-it-py` is declared, F11); attachments; a Gmail API (fails Tenet 1).

## Acceptance criteria

- [ ] The email send is one `channel.send` with its child; the To list and the body are what the preview showed (digest parity).
- [ ] Under (b), a `false` from Mail is FAILED; a timeout is UNKNOWN; under (a), a refused recipient is FAILED with the server's reason.
- [ ] One real send to his own address (Q6), found in his inbox (and his Sent box under (b)); or the limit named.
- [ ] No address appears in the kernel journal or in a tracked file (the journal carries `destination:<id>`).

## Effort (not a promise)

PROVISIONAL: 1–1.5 engineering days under (b); 1.5–2 under (a).

## Test plan

- **Integration:** a recording runner (b) or a local socket double that records the SMTP dialogue (a), each minted through the real `plan`.
- **Real send:** his own address, on his desk or with a Q6 scratch HOME.

## Notes

- 2026-09-28 — drafted by the Fedaykin docs lane for Muad'Dib; unratified. Mail.app was read only through its scripting dictionary (`sdef`); nothing was sent.
