# The Send lifecycle (PHILO-10 design, round two)

**Status:** round three — Codex Astra r2 RATIFY-WITH-CONDITIONS (`../checks/charter-astra-r2.md`); its three corrections are recorded here (section 4a recovery across take-over and reaping; section 5 the GitHub identity; section 3 the Confluence title) and the readable preview (section 3). Earlier: DRAFT for the Codex Astra r2 check. Written 2026-09-28 by the Fedaykin docs lane (Opus 5.5) for Muad'Dib, on Codex Astra r1 DO-NOT-RATIFY (`../checks/charter-astra-r1.md`), findings 1–5. It settles the record and the rules before any build. It adds one small table and one reused table. It adds no framework.

## 1. The records

**`channel_destinations`**: one row per saved destination. Columns: `id`, `name`, `channel` (`file`, `github`, `jira`, `confluence`, `email`), `account` (the **concrete** identity, never a connection row id: GitHub `{host, login}`; Jira and Confluence `{site, email}`; Mail the account name; empty for a folder — round three: the GitHub connection row is one fixed id whose login the provider rewrites on every probe, `holdspeak/services/github_provider.py:220`, `:305-311`), `target_json` (canonical, see section 5), `target_digest` (sha256 of `channel` + `account` + `target_json`), `synced` (for a folder: the owner marks it at save), `state` (`active` or `parked`), `created_at`, `parked_at`. No secret. A row never changes its target: Edit parks the old row and makes a new one. Remove parks the row. History is kept.

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

- The **payload** is exactly what the channel reads: GitHub, the Markdown body; Jira, plain text; Confluence, a JSON object with the **title and the storage-format XHTML body together** (round three); email, a JSON object with To, Subject and the plain-text body; file, the file bytes. The digest covers every byte of it, the title included.
- **The preview is readable, and derived from the frozen payload** (round three): Markdown and plain text as rendered text; Confluence as its title and the body rendered as text; email as To, Subject and body fields. The face never shows raw XHTML or raw JSON. The preview is computed from the stored payload, so it cannot show other words than the ones sent.
- **No document text in argv, and none in script source.** At dispatch the payload is written to a private file: a directory with mode 0700 that the hub makes, a file with mode 0600 opened with exclusive create. The sha256 of the file is compared with `payload_digest` just before the command runs; a mismatch refuses `payload_changed` and nothing runs. The file is deleted after the command ends.
- What each CLI accepts (probed on an isolated HOME; `docs/internal/philo/phase-10/grounding/transport-probe.out.txt`):
  - `gh issue comment` and `gh pr comment`: `--body-file <path>`. `-` would read stdin, but a file is used for all channels.
  - `acli jira workitem comment create`: `--body-file <path>`. Given `-`, it answered "failed to read comment body from file", so stdin does not work. A 0600 file got past the file read and stopped at the missing login.
  - `acli confluence blog create`: `--from-json <path>`, with the title and body in the one 0600 JSON file, and no `--title` in argv (round three). Probed (`docs/internal/philo/phase-10/grounding/confluence-json-probe.out.txt`): with no login, `acli` answers `unauthorized` before it reads the file, even for `--generate-json`, so the JSON shape is **unknown** until the real-account leg. **Named limit:** if `--from-json` cannot carry the title, the fallback is `--from-file <body>` + `--title <title>`, with the title in argv and in the subprocess receipt. It is disclosed on the Confluence destination row and in the preview, the digest still covers it, and it is Muad'Dib's ruling before story 02 merges. Otherwise Confluence goes to the BACKLOG.
  - `osascript`: a fixed script file in the repository gets the payload file's path as an argument and reads it with `read (POSIX file p) as «class utf8»`. Probed: text with quotes, `&` and `end tell` came back as text and did not run as code.
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
| Mail (Q1 b) | the script returns `true`: **HANDED TO MAIL** (the proof is that label and the time) | the script stopped before `send` with a pinned error (the account is not in Mail; Automation not allowed, `-1743`) | `false` (until the offline case is probed, section 6); a timeout |
| SMTP (Q1 a) | `250` after DATA; proof = the Message-ID HoldSpeak wrote | any RCPT refused: `QUIT` before DATA, and the reason names each refused address; connect or auth refused | the connection dropped after DATA started |

The pinned error lists live in each channel's `interpret`. An error not on a list is UNKNOWN, never FAILED.

**HoldSpeak never submits again by itself.** An UNKNOWN row stays UNKNOWN. To send again, the owner makes a new send, with a new row and a new key, and the face asks him to check the destination first. Mail may still deliver a message it holds in its own Outbox. That is Mail finishing the first handoff, not a second submission, and the face never calls it "sent again".

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

**Invariant:** per send key, **one dispatch, one terminal receipt, one history row**, whatever the order of take-over, reaping, restart and replay.

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
  - Email: at most 20 addresses, each parsed by `email.utils.parseaddr` and re-rendered canonically; the Mail account name.
  - File: an absolute folder, resolved with `realpath` at save. At dispatch it is resolved again, and a different resolved path refuses `destination_changed`. The file name is `<YYYY-MM-DD>-<project-slug>-r<draft_revision>-<first 8 hex of send id>.md`, created with exclusive create. If the name exists anyway, the suffix gets `-2`, `-3` and so on, and the chosen path is recorded at the boundary.
- **The badge:** GitHub, Jira, Confluence and email are `cloud`, with the host on the chip. A folder is `local` unless the owner marked it `synced` at save, then `cloud`. There is no sync detector.
- **The account is concrete and verified before dispatch** (round three, Codex Astra r2 condition 2).
  - **GitHub:** the destination freezes `{host, login}`, read at save from `gh api user --hostname <host>`. Before the dispatch boundary, the send runs the same read (a classified CLI read, not an effect) and compares its login with the frozen login. A different login or no login refuses `github_identity_changed` or `github_not_logged_in` by name, before anything runs. The Phase 9 connection row (`wpc_github`, rewritten by every probe, `holdspeak/services/github_provider.py:220`, `:305-311`) is shown on the row for its state only; it is never the identity. Residual window: `gh auth switch` run by hand between that check and the command is not detected; this is named, not engineered away (Tenet 1).
  - **Jira and Confluence:** the destination freezes `{site, email}`. The send runs switch → status → create under `_ACLI_LOCK` (`holdspeak/services/jira_provider.py:175`, `:570`), and create runs only if status confirms that site and email (the existing switch-and-verify law).
  - Its Phase 9 B1 state (connected, never checked, needs him) shows on the destination row.

## 6. Seams (finding 4)

- **CLI channels** use Phase 38's seam as it is: a `WriteConnectorManifest` with `shell:exec` and its argv prefixes, a `plan`, and an `interpret` (`holdspeak/plugins/gated_connector.py:127-288`). The change is plumbing, not framework: `build_gated_connector` → `_route` → `PermissionGate.execute_subprocess` → `run_subprocess_operation` pass on the **authenticated owner principal**, the **parent operation id** (the send) and the **broker**. Today `execute_subprocess` defaults to `local-owner` (`holdspeak/connector_runtime.py:141-146`), and causal admission compares the child's principal with the parent's (`holdspeak/kernel/causation.py:28-33`). This change also gives the nudge's `gh` op its parent (grounding F5).
- **The file channel is the one direct writer.** The write manifest supports only `shell:exec` and `network:outbound` (`holdspeak/plugins/gated_connector.py:43-47`). The file write is the `channel.send` operation's own effect, done by the channel's code inside the boundary rules above. The framework is not extended for symmetry.
- **SMTP** (only under Q1 a) is an `outbound` `GatedOperation` → an `external.egress` child whose allowed host is the frozen destination's host.

## 7. What this design does not decide

- The operation names (story 01's first commit).
- Q5 is not open: the steward and connected agents prepare, by his standing ruling "You, every time" (a stated default, round three).
- The Mail `false` case (story 03 probes it offline before it is mapped; until then `false` is UNKNOWN).
- The pinned error lists, the Atlassian JSON shapes and whether `--from-json` carries the Confluence title (story 02, from the real-account leg; the fallback is the named limit in section 3).
