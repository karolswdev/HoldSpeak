# PHILO-10-03 - The email channel — a provider interface

- **Project:** holdspeak-philo
- **Phase:** 10
- **Status:** backlog
- **Depends on:** PHILO-10-01; the Codex Astra check of the round-four email delta; the owner's Q1 ruling (2026-09-28) and Q6 ("Scratch targets you name")
- **Unblocks:** PHILO-10-05, PHILO-10-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
- **Closure finding:** the owner's Q1 ruling; `docs/internal/philo/phase-10/grounding/keyring-probe.out.txt`
- **Design:** `design/send-lifecycle.md` sections 3, 4, 4a, 5 and 8 (binding)
- **Canvas:** the email destination's fields are on the story 04 setup canvas

## The owner's ruling

"Nah man. Not mail.app since it wouldn’t work on non-Macs. Let’s have it declare an interface that would allow us to plug it into major providers like sendgrid and so on." (2026-09-28, AskUserQuestion)

## Problem

He picked "Email". HoldSpeak has no mail path. It must work off a Mac too, and it must admit the major providers without a change to its callers.

## Scope

- **In:**
  - **The contract.** An `EmailProvider` Protocol (`name`, `host`, `limits`, `plan(message, key)`, `interpret(response)`; the write seam's own shape) and one registry table `EMAIL_PROVIDERS`. No discovery, no entry points (design section 8).
  - **The frozen message.** From, to[], cc[], subject, text and optional html, frozen at prepare with its digest. The readable preview shows From, To, Cc, Subject and the text. The provider's request body is built from those bytes.
  - **SendGrid, the one implementation.** `POST https://api.sendgrid.com/v3/mail/send` as an `external.egress` child of the send, allowed host `api.sendgrid.com`, data class `email_message`, badge `cloud`. The proof is `X-Message-Id` on `202`. A 4xx on the pinned list is FAILED by name (`sender_not_verified` for `403`). A timeout, a dropped connection after the request left, or a 5xx is UNKNOWN. An UNKNOWN email is never retried by the product.
  - **The key.** Held in the OS keychain through `keyring`: macOS Keychain, Linux Secret Service, Windows Credential Manager, behind a native-only allow-list copied from the People key store (`holdspeak/people/keys.py:53-71`). Any other backend is refused `email_key_store_not_native`. The key is never in a row, a payload, a receipt, argv, a log or a file, and it is joined into the header at call time.
  - **The sender.** The destination's account freezes `{provider, from_email, from_name, key_ref}`. A changed sender refuses `destination_changed`.
  - **Size and recipients.** Limits refused by name before dispatch: provisional 1 MB and 20 recipients, pinned from SendGrid's published reference.
- **Out:** Postmark, Mailgun, SES and generic SMTP (BACKLOG; each is one class and one table row later). The Mail.app draft channel (parked, BACKLOG). The Gmail API. Attachments.

## Acceptance criteria

- [ ] The email send is one `channel.send` with one `external.egress` child to `api.sendgrid.com:443`. The request body's digest equals the frozen payload's digest. A request to any other host is refused by the kernel (the allow-list).
- [ ] `202` + `X-Message-Id` is SENT with the id in the record. Each pinned 4xx is FAILED with its name. A timeout after the request left, a 5xx, `202` without an id, and an unlisted 4xx are UNKNOWN. The crash fences R1–R6 hold for email (design section 4a).
- [ ] No key and no body in the kernel journal, a receipt, a log, an error or a tracked file (a sentinel fence). The journal carries `destination:<id>`, `egress:api.sendgrid.com:443`, `data-class:email_message` and the digest.
- [ ] Key custody: a native backend stores and reads the key. The `fail` backend, a chainer with no native store, and a file-based backend each refuse `email_key_store_not_native`. The tests inject a memory store and never touch the real keychain.
- [ ] A second provider can be added with one class and one table row: a fence registers a recording test provider and sends through it with no caller change.
- [ ] The real-account leg, apart from the rehearsals (Q6, "Scratch targets you name"): one real send through his SendGrid account from a verified sender to his own address, with `X-Message-Id` recorded and the mail found in his inbox; or the limit named.

## Effort (not a promise)

PROVISIONAL: 1.5–2 engineering days.

## Test plan

- **Integration:** a recording HTTPS opener minted through the real `plan` (no network in a lane); the kernel's egress admission with the real allow-list; the memory key store; the crash fences.
- **Real send:** the Q6 leg only, on his own session.

## Notes

- 2026-09-28 — round four: redrawn on the owner's Q1 ruling. The Mail.app / `osascript` design of rounds one to three is parked (BACKLOG "Mail.app draft channel"; the history keeps it). Nothing was sent; no call was made to SendGrid in the grounding.
- 2026-09-28 — drafted by the Fedaykin docs lane for Muad'Dib.
