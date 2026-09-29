# PHILO-10-07 - Resend, the second email provider

- **Project:** holdspeak-philo
- **Phase:** 10
- **Status:** done
- **Depends on:** PHILO-10-03 (the `EmailProvider` Protocol and the `EMAIL_PROVIDERS` table); PHILO-10-04 (the Destinations group and the Send face)
- **Unblocks:** PHILO-10-06 (the real-account leg can go through Resend, the provider the owner has)
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
- **Closure finding:** the owner's closing-review ruling for Phase 10 (below)
- **Design:** `design/send-lifecycle.md` section 8 (the provider interface: one class, one table row); story 03's key custody and outcome rules, unchanged
- **Canvas:** the story 04 destinations canvas; the Provider row was drawn there as a cycle, and now it has two values

## The owner's ruling

"the changes will include also plugging in 'resend' client, okay? We can have SendGrid and Resend (I happen to actually have that.)" (2026-09-29, the Phase 10 closing review)

## Problem

Phase 10 sends email through one provider, SendGrid. The owner has a Resend account. Without a Resend provider, his email channel cannot send through it.

## Scope

- **In:**
  - **`ResendProvider`: one class and one `EMAIL_PROVIDERS` row** (`holdspeak/services/channel_email.py`). `POST https://api.resend.com/emails`, `Authorization: Bearer <key>`, `User-Agent: HoldSpeak` (Resend refuses a request with no User-Agent with a 403), JSON body `{"from", "to": [...], "cc": [...], "subject", "text"}`: text only, as SendGrid. The sender is `Name <address>`, with the name kept as typed (quoted when it must be, never RFC 2047 encoded).
  - **Its outcomes, by story 03's rules.** `200` + `{"id": ...}` is SENT; the id is the proof; the face word is **ACCEPTED BY RESEND** (accepted for processing, never "delivered"). `200` with no id is UNKNOWN `accepted_without_message_id`. A 4xx is FAILED only when Resend answered it (its `{statusCode, name, message}` body) and the (status, name) pair is on the pinned list: `resend_invalid_request` (400/422 validation), `resend_key_invalid` (401 missing key; 403 invalid, restricted or suspended key), `resend_rate_limited` (429 rate limit), `resend_quota_exceeded` (429 daily or monthly quota). Round two (Codex Astra r1 on #701): only Resend's whole, consistent envelope counts (a JSON object, an integer `statusCode` equal to the HTTP status, a string `name`, a string `message`). A pinned `403 validation_error` whose message says the domain is not verified, or that a test sender sends only to its owner, is `sender_not_verified` (the same code as SendGrid's, so the B11 Check reads it); `403 invalid_permission` and any other `403 validation_error` are `resend_forbidden`; an unknown name is UNKNOWN. A 3xx is UNKNOWN `redirect_refused` (not followed). Everything else is UNKNOWN `unpinned_<status>`. The contract was read from Resend's API reference (send-email, errors, introduction) on 2026-09-29.
  - **Key custody, one slot per provider.** The keychain item is `<provider>:<key_ref>` (`key_slot`; `:` is never in a key_ref). A SendGrid key and a Resend key never share a slot, and a destination of one provider never reads the key of another. The key save names its provider (`channel.save_email_key` `provider`). HTTP-only key save, no redirects, sanitized exceptions: story 03's code, unchanged.
  - **The B11 Check reads its own provider.** `_email_state` reads the latest answer for this sender AND this provider, and the key-saved receipt of this provider's slot.
  - **The face.** The Destination form's Provider cycle has SendGrid and Resend (the library `CycleGadget`); the key row reads "Resend key"; the key is saved under `resend-<from>` with `provider: resend`. The egress chip, the SENT word, the far side ("Check") and the open row's Provider field come from one face table (`EMAIL_PROVIDERS` in `channels.ts`). The channel option reads "Email" (the provider is its own row). Each new code has its face word; `email_key_missing` now reads NO KEY (it named SendGrid).
  - **Generated docs:** `docs/generated/operations.json` (the operation descriptions name both providers).
- **Out:** the real Resend send (the real-account leg, story 06, on his own session). Resend's `Idempotency-Key` (HoldSpeak already never sends twice; a key per send is a later hardening). HTML mail, attachments, scheduled sends. (Round two moved the Resend atlas cases IN.)

## Acceptance criteria

- [x] One class and one table row: `EMAIL_PROVIDERS` holds `sendgrid` and `resend`; the send path (the channel's dispatch, the kernel, the routes) is unchanged. The send service changed only for the per-provider key slot (the key save and the Check).
- [x] The exact request through the real producer with a recording HTTPS edge: host, URL, Bearer key, User-Agent, Content-Type, and the body bytes equal to the frozen payload and to the expected JSON; one `external.egress` child to `api.resend.com:443` with the frozen digest admitted.
- [x] `200` + id → SENT with proof `{provider: resend, message_id, word: ACCEPTED BY RESEND, scope}`; each pinned (status, name) → FAILED with its code; the two 403 sender messages → `sender_not_verified`; a 403 not from Resend, a 409, a 5xx, a timeout → UNKNOWN; a refused connection → FAILED; a 302 and a 308 → UNKNOWN `redirect_refused` with one request only.
- [x] A Resend error that echoes the key and the body leaves neither in an error, a receipt, a log or the database; a transport exception that carries them leaves neither.
- [x] Key slots: the same key name for both providers is two slots with two keys; each send carries its own provider's key; a Resend destination that names a key saved for SendGrid only is refused `email_key_missing`, and nothing leaves.
- [x] The Check (B11) of a SendGrid destination does not read a Resend answer for the same sender; a Resend key saved again after its answer reads `key_changed`.
- [x] The face: the Provider cycle, "Resend key", the key save `PUT /api/channels/email-keys/resend-<from>` with `provider: resend`, `API.RESEND.COM`, ACCEPTED BY RESEND, the Resend activity page as the far side (vitest). The SendGrid glass boards (story 04) stay green at 1440 and 393.
- [x] Every emitted code has a face word (the story 05 census fence).
- [x] Round two: an answer that is not Resend's consistent envelope (Codex's three probes and eight more) is UNKNOWN through the real save → prepare → send routes, never FAILED (red 8/11 before).
- [x] Round two: five Resend atlas cases at 1440 and 393 (setup, accepted, prepared → sent, history, unknown with its Check far side), through a recording HTTPS edge and a memory key store in the rig's hub: 10/10, every shot looked at; the whole Phase 10 file 52/52.

## Effort (not a promise)

0.5 engineering day.

## Test plan

- **Unit / integration:** `tests/unit/test_philo10_email_channel.py` (`test_c7_*` and the story 03 fences), `tests/unit/test_philo10_face_words.py`, `tests/unit/test_philo10_atlas.py`, `tests/unit/test_philo10_send_contract.py`, `tests/unit/test_philo10_cli_channels.py`, `tests/unit/test_philo5_the_loop_r2.py`, `tests/unit/test_philo5_one_decision.py`, `tests/unit/test_philo5_graph_op.py`.
- **Web:** `web/src/features/channels/__tests__/resendProvider.test.tsx`; `scripts/check_web_baseline.py --run`.
- **Glass:** `tests/e2e/test_philo10_04_send_face_glass.py::TestSendEmailGlass` and `::TestSendFaceGlass::test_the_destinations_group`.
- **Atlas:** `assets/story-07-proof/rig_story07.sh <label> [--obs-only] [--case ...]` (story 05's rig_run.py and retain.py).
- **Real send:** none in a lane (no key); story 06's real-account leg.

## Notes

- 2026-09-29 — BUILT on `feat/philo-10-07` from main `05d01ffb`. The keychain slot changed for SendGrid too (`sendgrid:<key_ref>`, was `<key_ref>`): a SendGrid key saved before this change must be saved again. Not known from this lane whether he saved one.
- 2026-09-29 — ROUND TWO on Codex Astra r1 DO-NOT-RATIFY (`checks/story-07-built-astra-r1.md`): P1 the envelope validated before FAILED (red 8/11 → green); P2 five Resend atlas cases, 10/10 with shots, Phase 10 52/52; the full suite's atlas-anchor red paid; the cardinality test and the CI arrivalAttention red classified not branch-new (evidence).
