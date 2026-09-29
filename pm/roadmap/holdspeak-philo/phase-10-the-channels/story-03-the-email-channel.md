# PHILO-10-03 - The email channel — a provider interface

- **Project:** holdspeak-philo
- **Phase:** 10
- **Status:** in-progress
- **Depends on:** PHILO-10-01; the Codex Astra check of the round-four email delta; the owner's Q1 ruling (2026-09-28) and Q6 ("Scratch targets you name")
- **Unblocks:** PHILO-10-05, PHILO-10-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
- **Closure finding:** the owner's Q1 ruling; `docs/internal/philo/phase-10/grounding/keyring-probe.out.txt`
- **Design:** `design/send-lifecycle.md` sections 3, 4, 4a, 5, 6 and 8 (binding); Codex Astra r3 conditions (`checks/charter-astra-r3.md`)
- **Canvas:** the email destination's fields are on the story 04 setup canvas

## The owner's ruling

"Nah man. Not mail.app since it wouldn’t work on non-Macs. Let’s have it declare an interface that would allow us to plug it into major providers like sendgrid and so on." (2026-09-28, AskUserQuestion)

## Problem

He picked "Email". HoldSpeak has no mail path. It must work off a Mac too, and it must admit the major providers without a change to its callers.

## Scope

- **In:**
  - **The contract.** An `EmailProvider` Protocol (`name`, `host`, `limits`, `serialize(message)`, `preview(body_bytes)`, `plan(body_bytes)`, `interpret(status, headers, error_excerpt)`) and one registry table `EMAIL_PROVIDERS`. No discovery, no entry points (design section 8).
  - **One byte contract.** At prepare, the message (from, to[], cc[], subject, text — **text only** in this phase) is serialized once into SendGrid's exact JSON request body. That body is the frozen payload and its digest. The readable preview is parsed from it. Dispatch sends those bytes.
  - **The network seam (this story owns it).** `data_classes=("email_message",)`, `payload_material={"payload_digest": …}`, the parent, the authenticated owner principal and the broker are passed through `build_gated_connector` → `_route` → `PermissionGate.open_outbound_socket` → `run_external_egress`. Today it hashes the destination only and declares `connector_request` (`holdspeak/connector_runtime.py:194-233`).
  - **SendGrid, the one implementation.** `POST https://api.sendgrid.com/v3/mail/send` as an `external.egress` child of the send, allowed host `api.sendgrid.com`, data class `email_message`, badge `cloud`. The proof is `X-Message-Id` on `202`: internal `sent`, face word **ACCEPTED BY SENDGRID** (accepted for processing, not delivered). A 4xx is FAILED only when its status and discriminator are pinned: `403` + sender-identity → `sender_not_verified`; another `403` → `sendgrid_forbidden`; `400`, `401`, `413`, `429`. A timeout, a dropped connection after the request left, a 5xx, a 3xx or any unpinned answer is UNKNOWN. An UNKNOWN email is never retried by the product. A future provider's mixed acceptance would be UNKNOWN `partial_acceptance`.
  - **The key.** Held in the OS keychain through `keyring`: macOS Keychain, Linux Secret Service, Windows Credential Manager, behind a native-only allow-list copied from the People key store (`holdspeak/people/keys.py:53-71`). Any other backend is refused `email_key_store_not_native`. The key is never planning material (not in the payload, the `GatedOperation`, `payload_material`, `args` or `kwargs`), a row, a receipt, argv, a log or a file. Only the dispatch opener reads it and sets the header. **Redirects are disabled.** **Transport exceptions are sanitized before the native result is recorded**, and this story repairs the existing leak at `holdspeak/kernel/external_egress.py:290` for every caller. The webhook actuator's redirect leak (`holdspeak/plugins/builtin/webhook_post_actuator.py:125-133`) is ledgered in the BACKLOG, not touched here.
  - **The sender.** The destination's account freezes `{provider, from_email, from_name, key_ref}`. A changed sender refuses `destination_changed`.
  - **Size and recipients.** Limits refused by name before dispatch: provisional 1 MB and 20 recipients, pinned from SendGrid's published reference.
- **Out:** Postmark, Mailgun, SES and generic SMTP (BACKLOG; each is one class and one table row later). The Mail.app draft channel (parked, BACKLOG). The Gmail API. Attachments.

## Acceptance criteria

- [x] The email send is one `channel.send` with one `external.egress` child to `api.sendgrid.com:443`, parented, under the authenticated owner principal, data class `email_message`. The bytes on the wire (a recording opener) equal the frozen request body, and the egress admission's `payload_digest` equals its digest. Two different bodies produce two different digests (red on main: `connector_runtime.py:215` gives them one). A request to any other host is refused by the kernel.
- [ ] Through the real producer with a recording opener: `202` + `X-Message-Id` → `sent`, face and read-back **ACCEPTED BY SENDGRID** with the id; each pinned 4xx → FAILED with its name; the two `403` discriminators map apart; an unpinned 4xx, a 5xx, a timeout after the request left, `202` without an id → UNKNOWN; a 3xx is not followed (UNKNOWN `redirect_refused`) and no `Authorization` reaches a second host. The crash fences R1–R6 hold for email (design section 4a). **OPEN (Codex Astra r1 on #696, finding 6):** the outcomes, the read-back and the crash fences are proven; the DISPLAYED word on the Room face is story 04's build (the history still counts an email `sent` row under DELIVERED); this box flips with story 04's rendered fences.
- [x] An exception carrying a synthetic key and body leaves neither in the native result, the broker's full read, a receipt or a log (red on main at `external_egress.py:290`).
- [x] No key and no body in the kernel journal, a receipt, a log, an error or a tracked file (a sentinel fence). The journal carries `destination:<id>`, `egress:api.sendgrid.com:443`, `data-class:email_message` and the digest.
- [x] Key custody: a native backend stores and reads the key. The `fail` backend, a chainer with no native store, and a file-based backend each refuse `email_key_store_not_native`. The tests inject a memory store and never touch the real keychain.
- [x] A second provider can be added with one class and one table row: a fence registers a recording test provider and sends through it with no caller change. (Round two: the test provider is modelled on Postmark — its own auth header, its acceptance id in the JSON body — so the contract carries `auth_headers(key)` and `interpret(status, headers, body)`.)
- [ ] The real-account leg, apart from the rehearsals (Q6, "Scratch targets you name"): one real send through his SendGrid account from a verified sender to his own address, with `X-Message-Id` recorded and the mail found in his inbox; or the limit named.

## Effort (not a promise)

PROVISIONAL: 1.5–2 engineering days.

## Test plan

- **Integration:** a recording HTTPS opener minted through the real `plan` (no network in a lane); the kernel's egress admission with the real allow-list; the memory key store; the crash fences.
- **Real send:** the Q6 leg only, on his own session.

## Notes

- 2026-09-29 — ROUND THREE: merged main `3965c5e1` (#695, story 02). One seam for both families: `build_gated_connector(principal, parent_operation_id, broker)` threads a subprocess child (story 02) and an outbound child (this story) alike; the send passes story 02's `Seam` to every channel's `dispatch(row, seam)`. `channel.send` is `blocking_io` (its comment now names the email egress) and `channel.save_email_key` is `blocking_io` (the keychain), so both run off the event loop (HTTP `run_in_threadpool`; MCP `tools/call` of `channel.send` in the threadpool); fenced with a real socket hub and a 1.5 s SendGrid answer over HTTP and MCP. The one owner-press source is the descriptor flag (`kernel/channel_send.owner_press_operations()`); `channel.save_email_key` is HTTP only, so #694's MCP table has no row for it and story 02's census now says so.

- 2026-09-29 — ROUND TWO on Codex Astra r1 DO-NOT-RATIFY (`checks/story-03-built-astra-r1.md`), paid: (1) the credential-bearing edge `QuietHTTPSHandler` forces wire debug OFF for its own connections (the global `http.client` debuglevel is never read or changed), fenced with global debug ON over the real edge and an offline socket; (2) a transport failure is FAILED only when the edge proves no byte was written (`sent_any`, set before the first write to a connected socket): a TLS failure during the header or body write is UNKNOWN `tls_failed`, a handshake failure, a refused connection or DNS stays FAILED; (3) the provider contract declares its own authentication (`auth_headers(key)`, called only by the dispatch opener) and interprets bounded response material (`interpret(status, headers, body)`: every header and a 64 KiB body, the key removed), proven with a Postmark-like TEST provider. Criterion 2's displayed word (story 04) and criterion 7 (story 06's real send) stay OPEN. Owed: the #695 merge and the event-loop check for the email send.

- 2026-09-29 — BUILT (PHILO-10-03 lane, Fedaykin Opus 5.5), criteria 1–6 proven, the story stays **in-progress** for criterion 7 (the owner's real-account send, Q6), as story 02 did. `holdspeak/services/channel_email.py` (the `EmailProvider` Protocol, `EMAIL_PROVIDERS` = SendGrid only, the native-only key store, the dispatch opener `transmit`, the `EmailChannel`); the network seam: `GatedOperation.outbound(…, data_classes, payload_digest, subject_refs)` → `build_gated_connector(…, principal, parent_operation_id, broker)` → `_route` → `PermissionGate.open_outbound_socket(…)` → `run_external_egress(…, subject_refs)`; the admission binds the frozen bytes' own digest (`holdspeak/kernel/egress_material.py`); every egress caller's native result keeps the exception's type only (`sanitized_error`, was `external_egress.py:290`). `channel.save_email_key` (config, owner press, owner only, HTTP only: `PUT /api/channels/email-keys/{key_ref}`; the key is HELD by the transport, never an argument, so it never reaches the kernel request or its envelope digest); it is in no MCP palette, so #694's authority table (MCP tools only) needs no row. Sender verification through SendGrid is not built: a 403 `sender_not_verified` at send names it (BACKLOG). Proof: `assets/story-03-proof/captures.md` (the evidence file ships with the flip, after the real-account leg).

- 2026-09-28 — round four: redrawn on the owner's Q1 ruling. The Mail.app / `osascript` design of rounds one to three is parked (BACKLOG "Mail.app draft channel"; the history keeps it). Nothing was sent; no call was made to SendGrid in the grounding.
- 2026-09-28 — drafted by the Fedaykin docs lane for Muad'Dib.
