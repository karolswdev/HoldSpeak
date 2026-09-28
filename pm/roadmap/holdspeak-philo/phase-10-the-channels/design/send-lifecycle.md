# The Send lifecycle (PHILO-10 design, round two)

**Status:** round five — Codex Astra r3 RATIFY-WITH-CONDITIONS on the email delta (`../checks/charter-astra-r3.md`); recorded here: one byte contract for every channel (section 3), the network seam's owner (sections 6 and 8), key custody with redirects off and sanitized exceptions (section 8), ACCEPTED BY SENDGRID and the pinned failure mapping (sections 4 and 8), text-only email, the pre-boundary exception to the invariant (section 4a). Earlier: round four — the owner RATIFIED the charter ("Ratify, build it") and ruled Q1: "Not mail.app since it wouldn’t work on non-Macs. Let’s have it declare an interface that would allow us to plug it into major providers like sendgrid and so on." Section 8 is the email provider interface; the Mail.app and SMTP-password material is removed from this design and parked (BACKLOG "Mail.app draft channel"; the history keeps it). Codex Astra checks this delta. Earlier: round three — Codex Astra r2 RATIFY-WITH-CONDITIONS (`../checks/charter-astra-r2.md`); its three corrections are recorded here (section 4a recovery across take-over and reaping; section 5 the GitHub identity; section 3 the Confluence title) and the readable preview (section 3). Earlier: DRAFT for the Codex Astra r2 check. Written 2026-09-28 by the Fedaykin docs lane (Opus 5.5) for Muad'Dib, on Codex Astra r1 DO-NOT-RATIFY (`../checks/charter-astra-r1.md`), findings 1–5. It settles the record and the rules before any build. It adds one small table and one reused table. It adds no framework.

## 1. The records

**`channel_destinations`**: one row per saved destination. Columns: `id`, `name`, `channel` (`file`, `github`, `jira`, `confluence`, `email`), `account` (the **concrete** identity, never a connection row id: GitHub `{host, login}`; Jira and Confluence `{site, email}`; email `{provider, from_email, from_name, key_ref}` — the verified sender and the keychain item name, never the key (section 8); empty for a folder — round three: the GitHub connection row is one fixed id whose login the provider rewrites on every probe, `holdspeak/services/github_provider.py:220`, `:305-311`), `target_json` (canonical, see section 5), `target_digest` (sha256 of `channel` + `account` + `target_json`), `synced` (for a folder: the owner marks it at save), `state` (`active` or `parked`), `created_at`, `parked_at`. No secret. A row never changes its target: Edit parks the old row and makes a new one. Remove parks the row. History is kept.

**`channel_sends`**: one row per send, from prepare to its end. Columns: `id`, `document_ref` (for example `project_update:<id>`), `destination_id`, the frozen `account`, `target_json` and `target_digest` (copied from the destination), `payload` (the exact transport bytes, section 3), `payload_digest`, `prepared_by_kind`, `prepared_by_identity`, `prepare_operation_id`, `send_operation_id` (unique), `state`, `proof_json`, `reason`, `file_path` (file channel), `created_at`, `dispatch_started_at`, `settled_at`.

States: `prepared` → `dispatching` → `sent` | `failed` | `unknown`; `prepared` → `discarded`. No other move. No move out of `sent`, `failed`, `unknown` or `discarded`.

**`project_update_deliveries`** keeps its Phase 9 shape and law (insert-only, `operation_id NOT NULL UNIQUE`) and gets the additive columns `channel` (default `manual`), `send_id`, `outcome` (`confirmed`, `sent`, `unknown`), `proof_json`. A row is inserted when a send of an update settles `sent` or `unknown`, in the settle transaction. The Room reads the update's history from this one table, as it does today.

## 2. Prepare and press (finding 2)

- **Prepare** (`channel.prepare`) renders the document for the destination's channel and inserts one `channel_sends` row in state `prepared`, with the frozen target and the frozen payload. It completes as its own admitted operation, under the preparer's identity: the owner, the steward (as its run's child, under the owner's policy), or an agent he connected (Q5). Its receipt names who prepared. Nothing leaves the machine.
- **Send** (`channel.send`) is the **owner's** press. Only an OWNER principal is admitted; any other principal is refused `owner_principal_required` with a receipt. No kernel operation is held for an agent: an agent's `channel.send` is refused, and its `channel.prepare` completes.
- The press names either a prepared row (`send_id`) or, for the owner's own Send well, the document, the destination and the digest of the preview he saw. In the second form the send operation inserts its own row, and refuses `preview_changed` when a fresh render does not match the digest he saw.
- **Discard** (`channel.discard`) is owner only and moves `prepared` → `discarded`.
- **One wins.** Send and Discard each move the row with one conditional write (`UPDATE … WHERE id=? AND state='prepared'`). The loser changes nothing and is refused `send_already_settled` with a receipt.
- A prepared row is a database row: it survives a restart with its preview. It keeps the payload frozen at prepare, even when a newer update is published later. The face shows the revision the row came from.

## 3. The transport bytes (finding 3)

- **One byte contract for every channel** (round five, Codex Astra r3 condition 1): at prepare the channel serializes its **transport request** — the exact bytes the far side will receive — and freezes them with their sha256. The readable preview is derived from those bytes. Dispatch transmits those exact bytes and nothing re-renders them. Their digest reaches admission: for a CLI channel, through the send operation's payload hash and the payload file's digest check (section 3 below; the CLI seam, stories 01 and 02); for the email provider, as the `payload_digest` of the `external.egress` child with data class `email_message`, its parent, the authenticated principal and the broker (the network seam, story 03; section 6).
- The **payload** is exactly what the channel reads: GitHub, the Markdown body; Jira, plain text; Confluence, a JSON object with the **title and the storage-format XHTML body together** (round three); email, **the provider's serialized request body itself** (for SendGrid, the exact JSON of `POST /v3/mail/send`: `personalizations`, `from`, `subject`, `content[text/plain]`; text only in this phase; section 8); file, the file bytes. The digest covers every byte of it, the title included.
- **The preview is readable, and derived from the frozen payload** (round three): Markdown and plain text as rendered text; Confluence as its title and the body rendered as text; email as From, To, Cc, Subject and the text, parsed from the frozen request body. The face never shows raw XHTML or raw JSON. The preview is computed from the stored payload, so it cannot show other words than the ones sent.
- **No document text in argv, and none in script source.** At dispatch the payload is written to a private file: a directory with mode 0700 that the hub makes, a file with mode 0600 opened with exclusive create. The sha256 of the file is compared with `payload_digest` just before the command runs; a mismatch refuses `payload_changed` and nothing runs. The file is deleted after the command ends.
- What each CLI accepts (probed on an isolated HOME; `docs/internal/philo/phase-10/grounding/transport-probe.out.txt`):
  - `gh issue comment` and `gh pr comment`: `--body-file <path>`. `-` would read stdin, but a file is used for all channels.
  - `acli jira workitem comment create`: `--body-file <path>`. Given `-`, it answered "failed to read comment body from file", so stdin does not work. A 0600 file got past the file read and stopped at the missing login.
  - `acli confluence blog create`: `--from-json <path>`, with the title and body in the one 0600 JSON file, and no `--title` in argv (round three). Probed (`docs/internal/philo/phase-10/grounding/confluence-json-probe.out.txt`): with no login, `acli` answers `unauthorized` before it reads the file, even for `--generate-json`, so the JSON shape is **unknown** until the real-account leg. **Named limit:** if `--from-json` cannot carry the title, the fallback is `--from-file <body>` + `--title <title>`, with the title in argv and in the subprocess receipt. It is disclosed on the Confluence destination row and in the preview, the digest still covers it, and it is Muad'Dib's ruling before story 02 merges. Otherwise Confluence goes to the BACKLOG.
- argv then carries only paths, keys and flags. The subprocess receipt, which exposes argv (`holdspeak/kernel/subprocess_exec.py:199-213`), carries no body.
- Errors are cut to 240 characters, and any line that contains payload text is removed before they reach a receipt, a log or the face.
- **Size limits**, each refused before dispatch as `payload_too_large:<channel>`: GitHub 65,536 characters; Jira 32,767 characters; Confluence 1 MB; email 1 MB; file 10 MB. PROVISIONAL: the GitHub and Jira numbers are the services' published limits, not probed here, and story 02 pins them with a real send. `ARG_MAX` on this host is 1,048,576 (probed). With the body in a file, it no longer limits the body.

## 4. Dispatch, outcomes and recovery (finding 1)

**The durable dispatch boundary.** After admission and before any effect, the send commits one transaction by itself: the row moves `prepared` → `dispatching`, with `send_operation_id`, `dispatch_started_at` and, for a file, the chosen `file_path`. The effect runs only after that commit. Then one **settle** transaction moves the row to `sent`, `failed` or `unknown`, writes the proof or the reason, inserts the `project_update_deliveries` row (for `sent` and `unknown`), and writes the kernel terminal receipt.

**Recovery never dispatches again.** The Room takes over an abandoned operation and calls its service again (`holdspeak/services/project_kernel.py:398-400`, `:528-531`). The send's service call therefore reads the row first:

| Row state when the call starts | What the call does |
|---|---|
| `prepared` (the boundary did not commit) | dispatch normally: nothing has run |
| `dispatching` (the boundary committed; no settle) | **never dispatch.** File: read `file_path` back — present with the payload digest → `sent`; absent → `failed` (`not_written`); present with other bytes → `unknown`. Every other channel → `unknown` (`interrupted`) |
| `sent`, `failed`, `unknown` | return the stored result and proof; no effect |

This rule covers a crash, a restart, a lost caller and a settle transaction that fails after the effect. In each case the next call finds `dispatching`, and the result is proof (file) or UNKNOWN, never a second effect. A proof held only in memory when the settle fails is lost. The row says UNKNOWN, which is true.

**Outcomes.** SENT = proof exists. REFUSED = a named refusal before the boundary; nothing ran; the row does not move. FAILED = **known** non-delivery only. UNKNOWN = HoldSpeak cannot know. The mapping per channel:

| Channel | SENT | FAILED (a known non-delivery) | UNKNOWN |
|---|---|---|---|
| File | exclusive create, write, fsync, close; the bytes read back match the digest; proof = path + sha256 + size | create or write refused by the OS before any byte (`EACCES`, `ENOSPC` on create, `EEXIST` after the suffix, section 5) | a partial file; a crash after create |
| GitHub | exit 0 and stdout has a URL of the form `https://github.com/<owner>/<repo>/(issues\|pull)/<n>#issuecomment-<id>` for the frozen target | exit 4 (auth), or an error on a pinned list (not found, no permission to the repository), both answered before a comment exists | exit 0 without a valid URL; any other nonzero exit; a timeout; a kill |
| Jira, Confluence | exit 0 and a JSON answer with the created id (its shape is pinned by the first real send) | the switch or status step failed (create never ran); create answered an error on a pinned list (`unauthorized`, `can't be edited`, not found) | exit 0 without an id; any other nonzero exit; a timeout |
| Email (SendGrid, section 8) | `202` with an `X-Message-Id` header: internal state `sent`, face word **ACCEPTED BY SENDGRID**; proof = that id, and its scope is "SendGrid accepted the request for processing", not recipient delivery | a whole-request rejection proven by the response: before the request left (connect refused, DNS or TLS failed); after it, a 4xx on the pinned list with its discriminator (section 8) | a timeout or a dropped connection after the request left; any 5xx; `202` without `X-Message-Id`; a 3xx (redirects are not followed); a 4xx not on the list; any future provider's mixed or partial acceptance (`partial_acceptance`) |

The pinned error lists live in each channel's `interpret`. An error not on a list is UNKNOWN, never FAILED.

**HoldSpeak never submits again by itself.** An UNKNOWN row stays UNKNOWN. To send again, the owner makes a new send, with a new row and a new key, and the face asks him to check the destination first. The email provider offers no idempotency key HoldSpeak relies on, so an UNKNOWN email is never retried by the product.

## 4a. Recovery across take-over AND reaping (round three, Codex Astra r2 condition 1)

Section 4 alone does not work. Two kernel paths never reach the send service:

- **Replay after a non-`succeeded` end.** `_replayed` raises for every final state except `succeeded` (`holdspeak/services/project_kernel.py:387-390`). After a take-over settled UNKNOWN (kernel `indeterminate`), the next replay raised `interrupted` instead of answering UNKNOWN.
- **The reaper.** `reap_expired` (`holdspeak/kernel/liveness.py:10-47`) ends a claimed, silent operation `indeterminate` through `desk_broker.reap` (`holdspeak/kernel/desk_broker.py:158-172`); startup runs it through `holdspeak/kernel/projection_stager.py:343`. The send row stays `dispatching`, and no history row is written.

Codex reproduced both with the real kernel (`../checks/charter-astra-r2.md` finding 1).

**The scoped kernel change** (three small seams, each with a precedent):

1. **Reaping settles the row.** Add `channel_send_ended_effect(operation, reason)` beside `steward_run_ended_effect` (`holdspeak/kernel/project.py:402-426`). `desk_broker.reap` already passes that `effect=` into `transition_and_receipt`, so the settle runs **in the same transaction as the kernel's `indeterminate` receipt**. For a `channel.send` operation whose row is `dispatching`: the row → `unknown` (reason `reaped`), and one `project_update_deliveries` row (`outcome: unknown`). For a file send, a read-back that matches the digest is written into `proof_json` as `found_on_disk`; the outcome stays UNKNOWN, as the kernel's state is. A row still `prepared`, where the boundary never committed, is not moved: nothing ran, and its receipt names `reaped_before_dispatch`. `None` for every other operation.
2. **Take-over settles through the service.** The take-over (`holdspeak/services/project_kernel.py:398-400`, `:528-550`) calls the send service again. The service reads the row (section 4 table) and ends the operation through its handle's terminal write with an `effect=` (the `mark_update_delivered` pattern, `holdspeak/services/project_update_service.py:1929-1980`). Row settle, history row and receipt happen in one transaction. The kernel state follows the row: `sent` → `succeeded`, `failed` → `failed`, `unknown` → `indeterminate`.
3. **Replay answers the settled row.** For `channel.send` only, `_replayed` returns the settled row's answer (outcome, proof or reason, `send_id`) when the final state is `indeterminate` or `failed` and a settled row exists for the operation. Refusals (pre-boundary) still raise as today. This is one name-scoped hook, as `delivery_by_operation` answers a replayed mark (`project_update_service.py:1990-1995`).

**Both forms.** Every `channel_sends` row carries `send_operation_id` (unique), so take-over, reaping and replay all find it by the operation.

- **The `send_id` form:** the row exists from prepare; the boundary sets `send_operation_id`.
- **The owner's inline form:** the row is inserted by the boundary itself. If there is no row, nothing ran: take-over renders again, compares the digest he saw, and dispatches; reaping finds no row and writes only the kernel receipt.

**Invariant:** per send key, **one dispatch, one terminal receipt, one history row**, whatever the order of take-over, reaping, restart and replay — **except** a send that ends before the boundary (refused, or reaped while `prepared`, R6): **zero dispatches and no history row**, only its receipt.

**The fences** (story 01). Each is red on the round-two design, where only the service reads the row, and green on this one:

| Fence | Order | Red on round two | Green |
|---|---|---|---|
| R1 | dispatch, settle write fails → take-over → replay | replay raises `interrupted` | replay answers UNKNOWN; 1 dispatch, 1 receipt, 1 history row |
| R2 | dispatch, silent → the real reaper (clock past the execution deadline) → replay | row `dispatching`, no history row | row `unknown` in the receipt's transaction; replay answers it |
| R3 | dispatch → hub restart (`projection_stager.recover`) → replay | as R2 | as R2 |
| R4 | reaper and take-over race on one key | two settles possible | one wins (the strict revision), the other is a no-op |
| R5 | a file send reaped with the file present | no proof | UNKNOWN with `found_on_disk` path + sha256 |
| R6 | reaped before the boundary (`prepared`) | — | row stays `prepared`, no dispatch, receipt `reaped_before_dispatch` |

Each fence is parametrized over the `send_id` form and the inline form. The mutations: drop the reap effect (R2 and R3 turn red), drop the replay hook (R1 turns red), drop the strict revision (R4 turns red).

## 5. Destinations and targets (finding 5)

- **Frozen twice.** At prepare, the row copies the destination's `account`, `target_json` and `target_digest`. At the press, the send re-reads the destination, before the boundary: a parked row refuses `destination_parked`; a different digest refuses `destination_changed`. The row stays `prepared`; he discards it and prepares again. The receipt and the row keep the historical target.
- **One target per channel, validated at save and at dispatch:**
  - GitHub: `owner/repo` (`^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$`), kind `issue` or `pr`, number ≥ 1.
  - Jira: **one** canonical key `^[A-Z][A-Z0-9_]+-[1-9][0-9]*$`, with no comma and no space. The help says `--key` takes "a list of work item keys" (`docs/internal/philo/phase-10/grounding/cli-probe.out.txt:58`), so a second key is refused `jira_key_not_single`. The argv never has `--jql`, `--filter` or `--edit-last`.
  - Confluence: a space id (digits) and the account.
  - Email: at most 20 addresses, each parsed by `email.utils.parseaddr` and re-rendered canonically, for To and Cc together; the frozen sender and provider (section 8).
  - File: an absolute folder, resolved with `realpath` at save. At dispatch it is resolved again, and a different resolved path refuses `destination_changed`. The file name is `<YYYY-MM-DD>-<project-slug>-r<draft_revision>-<first 8 hex of send id>.md`, created with exclusive create. If the name exists anyway, the suffix gets `-2`, `-3` and so on, and the chosen path is recorded at the boundary.
- **The badge:** GitHub, Jira, Confluence and email are `cloud`, with the host on the chip. A folder is `local` unless the owner marked it `synced` at save, then `cloud`. There is no sync detector.
- **The account is concrete and verified before dispatch** (round three, Codex Astra r2 condition 2).
  - **GitHub:** the destination freezes `{host, login}`, read at save from `gh api user --hostname <host>`. Before the dispatch boundary, the send runs the same read (a classified CLI read, not an effect) and compares its login with the frozen login. A different login or no login refuses `github_identity_changed` or `github_not_logged_in` by name, before anything runs. The Phase 9 connection row (`wpc_github`, rewritten by every probe, `holdspeak/services/github_provider.py:220`, `:305-311`) is shown on the row for its state only; it is never the identity. Residual window: `gh auth switch` run by hand between that check and the command is not detected; this is named, not engineered away (Tenet 1).
  - **Jira and Confluence:** the destination freezes `{site, email}`. The send runs switch → status → create under `_ACLI_LOCK` (`holdspeak/services/jira_provider.py:175`, `:570`), and create runs only if status confirms that site and email (the existing switch-and-verify law).
  - Its Phase 9 B1 state (connected, never checked, needs him) shows on the destination row.

## 6. Seams (finding 4)

- **CLI channels** use Phase 38's seam as it is: a `WriteConnectorManifest` with `shell:exec` and its argv prefixes, a `plan`, and an `interpret` (`holdspeak/plugins/gated_connector.py:127-288`). The change is plumbing, not framework: `build_gated_connector` → `_route` → `PermissionGate.execute_subprocess` → `run_subprocess_operation` pass on the **authenticated owner principal**, the **parent operation id** (the send) and the **broker**. Today `execute_subprocess` defaults to `local-owner` (`holdspeak/connector_runtime.py:141-146`), and causal admission compares the child's principal with the parent's (`holdspeak/kernel/causation.py:28-33`). This change also gives the nudge's `gh` op its parent (grounding F5).
- **The file channel is the one direct writer.** The write manifest supports only `shell:exec` and `network:outbound` (`holdspeak/plugins/gated_connector.py:43-47`). The file write is the `channel.send` operation's own effect, done by the channel's code inside the boundary rules above. The framework is not extended for symmetry.
- **The network seam has an owner: story 03** (round five, Codex Astra r3 condition 1), as the CLI seam has stories 01 and 02. Today `PermissionGate.open_outbound_socket` hashes only the destination, declares `connector_request`, and forwards no parent, principal or broker (`holdspeak/connector_runtime.py:194-233`, `:215-223`): two different bodies get one digest (Codex probe). Story 03 passes `data_classes=("email_message",)`, `payload_material={"payload_digest": <frozen digest>}`, the parent (the send), the authenticated owner principal and the broker through `build_gated_connector` → `_route` → `open_outbound_socket` → `run_external_egress`. The email provider is an `outbound` `GatedOperation` → an `external.egress` child whose allowed host is `api.sendgrid.com`. Section 8.

## 7. What this design does not decide

- The operation names (story 01's first commit).
- Q5 is not open: the steward and connected agents prepare, by his standing ruling "You, every time" (a stated default, round three).
- SendGrid's exact size limits and the pinned 4xx list: story 03, from its published reference and the real-account send (section 8).
- The pinned error lists, the Atlassian JSON shapes and whether `--from-json` carries the Confluence title (story 02, from the real-account leg; the fallback is the named limit in section 3).

## 8. Email: a provider interface (round four, the owner's Q1 ruling)

**The contract** (Tenet 1: one Protocol and one table, no discovery, no entry points; round five: one byte contract):

```text
EmailProvider (Protocol)
  name            "sendgrid"
  host            "api.sendgrid.com"            the only allowed egress host
  limits          max_bytes, max_recipients     refused by name before dispatch
  serialize(message) -> bytes                   at PREPARE: the exact request body; frozen with its digest
  preview(body_bytes) -> From/To/Cc/Subject/text   derived from the frozen bytes
  plan(body_bytes) -> GatedOperation.outbound   no key in it; the frozen bytes unchanged
  interpret(status, headers, error_excerpt) -> Sent(message_id) | Failed(code) | Unknown(reason)

EMAIL_PROVIDERS = {"sendgrid": SendGridProvider()}   the registry TABLE
```

- **The message** he composes (from, to[], cc[], subject, text) is serialized once, at prepare, into the provider's request body. **That body is the frozen payload**, and its digest is the digest the egress admission binds. The preview parses it back into From, To, Cc, Subject and the text, never showing JSON. Dispatch sends those bytes. A fence asserts that the bytes on the wire (a recording opener) equal the frozen bytes.
- **Text only in this phase** (round five, Codex Astra r3). The body carries one `text/plain` content. HTML waits until one source can produce both text and HTML (BACKLOG).
- **Refusals before dispatch** (REFUSED, nothing leaves) are named: `email_provider_unknown`, `email_key_missing`, `email_key_store_not_native`, `payload_too_large:email`, `email_recipients_too_many`, `destination_changed`.
- **Adding a provider** means one class and one table row. Postmark, Mailgun, SES and generic SMTP are named for later in the BACKLOG. Callers do not change. A future provider that can accept some recipients and reject others maps that answer to UNKNOWN `partial_acceptance`. It is never "nothing sent", and it builds no second lifecycle now.

**SendGrid, the one implementation in this phase.**

- `POST https://api.sendgrid.com/v3/mail/send` with the frozen JSON body. It runs as an `external.egress` child of the send: destination `api.sendgrid.com:443`, data class `email_message`, `payload_digest` the frozen digest, and the parent, principal and broker threaded (section 6).
- **The key is never planning material** (round five, Codex Astra r3 condition 2). It is not in the payload, the `GatedOperation`, `payload_material`, `args` or `kwargs`. Only the dispatch opener reads it from the key store and sets `Authorization: Bearer …` on the request it opens.
- **Redirects are disabled.** The opener uses a `urllib` opener whose redirect handler refuses. A 3xx is UNKNOWN (`redirect_refused`), and `Authorization` is never sent to another host.
- **Transport exceptions are sanitized before the native result is recorded.** The opener catches every exception and re-raises a sanitized one: its type and a fixed code, never `str(exc)`, a header, the key or the body. Only that reaches `EGRESS_EXECUTIONS.record(… error=…)`.
- **Two existing defects are named.** `external_egress.py:290` records `f"{type(exc).__name__}: {exc}"` today; Codex reproduced a synthetic key and body in the native result and the broker's full read. Story 03 makes that record sanitized for every caller. `webhook_post_actuator.py:125-133` follows redirects with its headers; Codex's offline probe forwarded a synthetic `Authorization` to another host. That defect is ledgered in the BACKLOG, because story 03 does not touch the webhook actuator.
- **The response contract** kept for interpretation: the status, the `X-Message-Id` header, and a bounded, sanitized excerpt of the error JSON (`errors[].message`, `errors[].field`). This is enough to classify, and it never holds the key or the body.
- **Outcomes** (section 4 table):
  - `202` + `X-Message-Id` → internal `sent`. The **face word is ACCEPTED BY SENDGRID**, and the proof's scope is "accepted for processing", not delivered to the recipient. SendGrid documents that it accepts the request first and delivers later.
  - A 4xx is FAILED only where SendGrid's contract makes it a whole-request rejection (the request is validated before any send) **and** the status plus its discriminator are on the pinned list:
    - `400` → `invalid_request`
    - `401` → `api_key_invalid`
    - `403` with the sender-identity discriminator (the error names the from address not matching a verified Sender Identity) → `sender_not_verified`
    - `403` with any other discriminator (for example a temporary sending block) → `sendgrid_forbidden`, with the provider's sanitized reason and no remediation claimed
    - `413` → `payload_too_large`
    - `429` → `rate_limited`
  - Every other answer is UNKNOWN with a named reason.
- The exact limits and discriminator strings are pinned by story 03 from SendGrid's published reference and the real-account send (Q6). Until then `max_bytes` is 1 MB and `max_recipients` is 20 (provisional).
- **Fences through the real producer** (story 03), each with a recording opener, no network: success; an HTTP error (each pinned 4xx, an unpinned 4xx, a 5xx); an exception whose text carries a synthetic key and body, where neither may appear in the native result, the broker's read, a receipt or a log; and a redirect, which is not followed and sends no `Authorization` to the second host.

**The key: custody on every platform.**

- `keyring` is already a core dependency (`pyproject.toml:60`, `keyring>=25.0`; 25.7.0 installed). Its native backends are macOS Keychain, Linux Secret Service and Windows Credential Manager (`keyring.backends.macOS`, `.SecretService`, `.Windows` all import here; `docs/internal/philo/phase-10/grounding/keyring-probe.out.txt`).
- The custody boundary copies the People key store (`holdspeak/people/keys.py:53-71`): one allow-list of native backends. The email store admits `keyring.backends.Windows.WinVaultKeyring` as well, which the People list does not name (HoldSpeak targets macOS and Linux today; the entry costs one line).
- Any other backend is refused `email_key_store_not_native`: the `fail` backend on a headless Linux without Secret Service, the chainer when it resolves to no native store, and any file-based `keyrings.alt` store. **Never a plaintext file, never an environment variable.**
- The destination holds only `key_ref` (the keychain item name). The key is saved once through the setup face and read at dispatch.
- A test uses the injected memory store only: the People `MemoryKeyStore` precedent. On this machine an isolated HOME still resolves to the macOS Keychain (the probe), so a lane must never touch the real keychain.

**The sender is part of the account freeze.** The destination's `account` is `{provider, from_email, from_name, key_ref}`, and its digest covers them (section 5). A changed sender refuses `destination_changed` before dispatch. SendGrid answers `403` for a sender it has not verified (FAILED, `sender_not_verified`, pinned). `channel.check_destination` may ask SendGrid for its verified senders; that is admitted as egress, like `connection.recheck`. Rotating the key under the same `key_ref` does not change the sender or the recipients, so it is not a destination change.
