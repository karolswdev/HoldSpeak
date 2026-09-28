# PHILO-10-03 - The email channel

- **Project:** holdspeak-philo
- **Phase:** 10
- **Status:** backlog
- **Depends on:** PHILO-10-01; the owner's answers to Q1 and Q6
- **Unblocks:** PHILO-10-05, PHILO-10-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
- **Closure finding:** `docs/internal/philo/phase-10/grounding/README.md` section 4, F10, F11, F15; Codex Astra r1 finding 6
- **Design:** `design/send-lifecycle.md` sections 3–4 (binding)
- **Canvas:** the email destination's fields are on the story 04 setup canvas

## Problem

He picked "Email". HoldSpeak has no mail path. The transports differ in custody, proof and cost (grounding section 4). Mail.app's `send` answers only true or false (F10).

## Scope

- **In:** first, **the Mail preflight** on his desk (before any build under (b)): his work account is in Mail; its use is allowed; Automation works from the hub's real launch context; the `false` answer is probed with Mail offline (what stays in the Outbox). If a condition fails, Q1 falls back as the charter says. Under (b): a fixed `osascript` script file in the repository reads To, subject and body from a 0600 payload file (no document text in script source; probed) and sends from the account the destination names; a `subprocess.exec` child of the send; the outcome label HANDED TO MAIL (never "delivered", never a promise of the Sent box); Mail's own Outbox retry is not HoldSpeak sending again. Under (a): `smtplib` over TLS as an `external.egress` child to the saved host; every RCPT must be accepted before DATA, else `QUIT` and FAILED naming each refused address; the password in the macOS keychain through `keyring` (the People custody precedent); proof the `250` answer and the Message-ID HoldSpeak writes.
- **Out:** HTML mail unless the owner asks (then `markdown-it-py` is declared, F11); attachments; a Gmail API (fails Tenet 1).

## Acceptance criteria

- [ ] The email send is one `channel.send` with its child; the To list and the body are what the preview showed (digest parity).
- [ ] Under (b), `true` is HANDED TO MAIL; a pinned pre-send error (account not in Mail, Automation `-1743`) is FAILED; `false` and a timeout are UNKNOWN until the offline probe says what `false` leaves behind; under (a), a refused recipient stops the send before DATA (FAILED, named); a drop after DATA is UNKNOWN.
- [ ] The real-account leg, apart from the rehearsals (a scratch HOME does not isolate Mail): one real send to his own address, authorized under Q6, found in his inbox; or the limit named.
- [ ] No address appears in the kernel journal or in a tracked file (the journal carries `destination:<id>`).

## Effort (not a promise)

PROVISIONAL: 1–1.5 engineering days under (b); 1.5–2 under (a).

## Test plan

- **Integration:** a recording runner (b) or a local socket double that records the SMTP dialogue (a), each minted through the real `plan`.
- **Real send:** his own address, on his desk or with a Q6 scratch HOME.

## Notes

- 2026-09-28 — round two: amended on Codex Astra r1 DO-NOT-RATIFY (`checks/charter-astra-r1.md`); bound by `design/send-lifecycle.md`.
- 2026-09-28 — drafted by the Fedaykin docs lane for Muad'Dib; unratified. Mail.app was read only through its scripting dictionary (`sdef`); nothing was sent.
