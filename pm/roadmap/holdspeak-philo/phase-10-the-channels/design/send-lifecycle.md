# The Send lifecycle (PHILO-10 design, round two)

**Status:** DRAFT for the Codex Astra r2 check. Written 2026-09-28 by the Fedaykin docs lane (Opus 5.5) for Muad'Dib, on Codex Astra r1 DO-NOT-RATIFY (`../checks/charter-astra-r1.md`), findings 1–5. It settles the record and the rules before any build. It adds one small table and one reused table. It adds no framework.

## 1. The records

**`channel_destinations`**: one row per saved destination. Columns: `id`, `name`, `channel` (`file`, `github`, `jira`, `confluence`, `email`), `account` (the connection id from `watch_provider_connections` for GitHub and Atlassian, or the Mail account name, or empty), `target_json` (canonical, see section 5), `target_digest` (sha256 of `channel` + `account` + `target_json`), `synced` (for a folder: the owner marks it at save), `state` (`active` or `parked`), `created_at`, `parked_at`. No secret. A row never changes its target: Edit parks the old row and makes a new one. Remove parks the row. History is kept.

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

- The **payload** is exactly what the channel reads: GitHub, the Markdown body; Jira, plain text; Confluence, storage-format XHTML; email, a JSON object with To, Subject and the plain-text body; file, the file bytes. The preview on the face shows these bytes.
- **No document text in argv, and none in script source.** At dispatch the payload is written to a private file: a directory with mode 0700 that the hub makes, a file with mode 0600 opened with exclusive create. The sha256 of the file is compared with `payload_digest` just before the command runs; a mismatch refuses `payload_changed` and nothing runs. The file is deleted after the command ends.
- What each CLI accepts (probed on an isolated HOME; `docs/internal/philo/phase-10/grounding/transport-probe.out.txt`):
  - `gh issue comment` and `gh pr comment`: `--body-file <path>`. `-` would read stdin, but a file is used for all channels.
  - `acli jira workitem comment create`: `--body-file <path>`. Given `-`, it answered "failed to read comment body from file", so stdin does not work. A 0600 file got past the file read and stopped at the missing login.
  - `acli confluence blog create`: `--from-file <path>`.
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

## 5. Destinations and targets (finding 5)

- **Frozen twice.** At prepare, the row copies the destination's `account`, `target_json` and `target_digest`. At the press, the send re-reads the destination, before the boundary: a parked row refuses `destination_parked`; a different digest refuses `destination_changed`. The row stays `prepared`; he discards it and prepares again. The receipt and the row keep the historical target.
- **One target per channel, validated at save and at dispatch:**
  - GitHub: `owner/repo` (`^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$`), kind `issue` or `pr`, number ≥ 1.
  - Jira: **one** canonical key `^[A-Z][A-Z0-9_]+-[1-9][0-9]*$`, with no comma and no space. The help says `--key` takes "a list of work item keys" (`docs/internal/philo/phase-10/grounding/cli-probe.out.txt:58`), so a second key is refused `jira_key_not_single`. The argv never has `--jql`, `--filter` or `--edit-last`.
  - Confluence: a space id (digits) and the account.
  - Email: at most 20 addresses, each parsed by `email.utils.parseaddr` and re-rendered canonically; the Mail account name.
  - File: an absolute folder, resolved with `realpath` at save. At dispatch it is resolved again, and a different resolved path refuses `destination_changed`. The file name is `<YYYY-MM-DD>-<project-slug>-r<draft_revision>-<first 8 hex of send id>.md`, created with exclusive create. If the name exists anyway, the suffix gets `-2`, `-3` and so on, and the chosen path is recorded at the boundary.
- **The badge:** GitHub, Jira, Confluence and email are `cloud`, with the host on the chip. A folder is `local` unless the owner marked it `synced` at save, then `cloud`. There is no sync detector.
- **The account:** GitHub and Atlassian destinations point to their connection. Its Phase 9 B1 state (connected, never checked, needs him) shows on the destination row. An Atlassian send runs switch → status → create under `_ACLI_LOCK` (`holdspeak/services/jira_provider.py:175`, `:570`).

## 6. Seams (finding 4)

- **CLI channels** use Phase 38's seam as it is: a `WriteConnectorManifest` with `shell:exec` and its argv prefixes, a `plan`, and an `interpret` (`holdspeak/plugins/gated_connector.py:127-288`). The change is plumbing, not framework: `build_gated_connector` → `_route` → `PermissionGate.execute_subprocess` → `run_subprocess_operation` pass on the **authenticated owner principal**, the **parent operation id** (the send) and the **broker**. Today `execute_subprocess` defaults to `local-owner` (`holdspeak/connector_runtime.py:141-146`), and causal admission compares the child's principal with the parent's (`holdspeak/kernel/causation.py:28-33`). This change also gives the nudge's `gh` op its parent (grounding F5).
- **The file channel is the one direct writer.** The write manifest supports only `shell:exec` and `network:outbound` (`holdspeak/plugins/gated_connector.py:43-47`). The file write is the `channel.send` operation's own effect, done by the channel's code inside the boundary rules above. The framework is not extended for symmetry.
- **SMTP** (only under Q1 a) is an `outbound` `GatedOperation` → an `external.egress` child whose allowed host is the frozen destination's host.

## 7. What this design does not decide

- The operation names (story 01's first commit).
- The Mail `false` case (story 03 probes it offline before it is mapped; until then `false` is UNKNOWN).
- The pinned error lists and the Atlassian JSON shapes (story 02, from real sends).
