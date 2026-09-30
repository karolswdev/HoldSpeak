# PHILO Phase 11 grounding — backend half

**Status: DRAFT — UNCHECKED — awaiting Muad'Dib.** This is grounding, not a ratified design or permission to build.

**Date:** 2026-09-29 (America/Denver; probe timestamps can be 2026-09-30 UTC). **Base:** `7e09c8b40`. **Owner:** Astra. **Checker:** Muad'Dib, pending. **Worktree:** `/Users/karol/dev/tools/wt-philo-11-ground-astra`. **Branch:** `docs/philo-11-ground-astra`.

The owner's pick: **“More documents on the channels”** — “Phase 10 sends project updates only. Next: briefs, decisions and meeting summaries through the same channels, plus Slack (it was left out of Phase 10).” The standing rules are **“Payload: Any document; updates first,” “Who sends: You, every time,”** saved destinations, and declared interfaces with pluggable providers on each platform.

**Tuesday:** the owner should open an existing brief, decision or meeting summary, see the exact document and saved destination, and press Send once. Today only a published project update can enter that flow. Three new publish workflows or a second Slack send system would add cost before his first use (Tenets 1, 2, 3 and 7).

Scope: backend code, local producer probes, and public Slack documentation. All probes use an isolated HOME. No account was created, no credential was read, and no live external send was made. The companion faces grounding belongs to Muad'Dib; this document does not claim a glass walk or settle his UI design.

## 1. The Send contract as built

**Prepare is local, but it is not source-agnostic.** There are two different boundaries:

| Boundary | Evidence at the base | Consequence for Phase 11 |
|---|---|---|
| The rendered value is almost generic | `holdspeak/services/channel_contract.py:65`: `Document(ref, title, body_md, slug, revision)`; `:361`: `serialize_for(destination, document)` | Keep this separation: a source produces a document; a channel serializes it. `revision` currently serves file naming, not persisted source provenance. |
| Preview and prepare require an update | `holdspeak/services/channel_service.py:153`, `:349` call `render_update`; `holdspeak/channel_operations.py:174`, `:198` require `update_id`, reject additional properties | Change the service and its single descriptor schema together. A generic Python dataclass alone does not give HTTP/MCP generic preparation. |
| Only published updates render | `holdspeak/services/channel_contract.py:195` reads `project_updates`, rejects non-published rows, derives title from the current project name | Add explicit source resolvers for the three ruled kinds. Resolve a specific stored source, never an agent-supplied body that merely claims another record's identity. |
| Inline Send renders again | `holdspeak/services/channel_service.py:449` renders and compares `preview_digest` before dispatch | Preserve the comparison; extend the reference and source-version inputs. A changed preview must require another owner press. |
| Prepared Send uses frozen transport bytes | `holdspeak/services/channel_service.py:439`, `:466` reads the stored payload and verifies its hash | Preserve this. Do not regenerate a prepared brief or summary at Send time. |
| File naming still reads an update | `holdspeak/services/channel_contract.py:213` rejects any other kind; `holdspeak/services/channel_service.py:473` calls it even for a prepared Send | Freeze title/slug/version with preparation. A prepared send must not need a live source lookup to name its file. |
| Public history is update-shaped | `holdspeak/services/channel_service.py:141`; `holdspeak/channel_operations.py:294` expose an `update_id` filter, although `holdspeak/db/channels.py:142` already lists any `document_ref` | Offer a generic document filter. Reuse the send rows for new document history. |
| The send row is generic but lacks a source version | `holdspeak/db/schema.py:4221`: a free `document_ref`, target/account, payload and its digest, preparer, operation IDs, state/proof/time/dispatch order | Persist explicit source provenance beside the frozen transport payload. The schema has no source snapshot digest or frozen title/version today. |
| Delivery projection is deliberately update-only | `holdspeak/db/schema.py:4177`: `update_id` FK; `holdspeak/db/channels.py:75` inserts only for `project_update:` and `sent`/`unknown` | Keep this as the Room's update/manual-delivery projection. New kinds can read `channel_sends`; they do not need fake project updates or three delivery tables. |

The minimum proposed provenance is `kind`, `source_id`, the source's real revision identifier when it has one, a digest of the canonical source snapshot consumed by the renderer, and a renderer version. Retain `document_ref` as the lookup key and retain the separate **transport** `payload_digest`. Freeze title/slug and a displayable version label too. A source timestamp alone is not a version: linked data can change without updating that timestamp. Do not invent revision `1` as proof of an immutable source.

For the existing update, keep both `project_revision` / `source_manifest_json` (the source envelope) and `draft_revision` (the authored update revision); they describe different things (`holdspeak/db/schema.py:4148`; `holdspeak/services/project_update_service.py:1542`). Neither should silently replace the other. The snapshot digest must cover the fields the document actually renders, including its title.

Preview must return this provenance and the transport digest; prepare must persist it in the same terminal transaction as the frozen bytes. Inline Send must bind and recheck the source snapshot as well as the bytes the owner saw. This matters when two sources or revisions render identical text. Reading the source and the data it includes must produce one consistent snapshot. These are proposed changes, not properties of the current code.

The proposed extension point is a declared document-source interface: resolve a kind/ID/version into a rendered document with provenance. Register the update and these three sources explicitly. A future source can implement that same interface without changing each channel. Unsupported kinds refuse by name. This needs neither plugin discovery nor a new document publishing framework.

Also extend the kernel target mapping: `holdspeak/services/project_kernel.py:184` chooses `channel_send`, `project_update`, or other fixed ID fields. New inline/preparation references must name their real source in the receipt and admission payload. The destination fields are separate from the document reference; in particular, the existing destination `kind` means GitHub issue/PR (`holdspeak/channel_operations.py:76`).

**Keep the lifecycle.** The durable boundary, one conditional winner against Discard, frozen destination/account digest, unique operation IDs, and `sent` / known `failed` / `unknown` outcomes already exist (`holdspeak/services/channel_service.py:380`, `:400`, `:483`; `holdspeak/db/channels.py:50`). Recovery never dispatches again. Both kernel reaping and startup recovery use the same settle function (`holdspeak/kernel/channel_send.py:50`, `:77`); the settled-row replay hook is already named for `channel.send` (`holdspeak/services/project_kernel.py:382`). Generalizing the source must retain those paths and their tests.

**Manual delivery is a separate seam.** Copy plus `project.mark_update_delivered` still validates a published update and writes only `project_update_deliveries` (`holdspeak/services/project_update_service.py:1958`, `:1969`). It is not a `CHANNELS` implementation. The proposal above generalizes transport sends; it does not silently claim that manual confirmation now works for every kind. Q7 settles whether to extend that ledger too.

## 2. The three sources

### Brief: the persisted chief-of-staff / next-day brief

The relevant producer is `MondayBriefService.generate` (`holdspeak/services/monday_brief_service.py:389`), despite its historical name. It returns the existing brief for the same local date (`:402`) and inserts a new header and its items for a new date (`:492`, `:506`). Storage is `monday_briefs` and `monday_brief_items` (`holdspeak/db/schema.py:2466`, `:2476`); item acknowledgement/defer state lives separately (`:2491`).

This is a stable daily identity and persisted content, **not a published document version**. The loader joins the current shelf state (`holdspeak/services/monday_brief_service.py:1492`, `:1523`), and `get_latest` chooses the newest brief (`:1428`). A send reference must select the actual brief ID, not “latest.” A text/Markdown document renderer and a source-by-ID read are needed. Render saved headline/sections/items with date and provenance; decide explicitly whether shelf state is part of the shared document. Recommended: omit personal triage state, preserve the saved substantive sections, and freeze the result when prepared.

The daily brief is already a useful persisted generation. Its missing send renderer/version metadata is not a reason to add a new publication workflow. The probe confirms same-day reuse and a different ID on the next producer day; “next-day brief” describes that later generation, not an additional source type.

Do not conflate this source with `project_briefs` or the Cadence brief. The project preparation producer stores `body_md` and a frozen source manifest (`holdspeak/services/preparation_brief_service.py:889`, `:952`; `holdspeak/db/schema.py:4505`). Cadence's Morning Push is computed on read (`holdspeak/services/cadence_service.py:60`) and has text/Markdown renderers (`holdspeak/cadence/brief.py:76`, `:88`), but no durable brief document ID. Those are different sources, not missing aliases for the daily brief; including them is an additional scope choice.

### Decision: resolve what “decision receipt” names

There are distinct records here. A decision lifecycle action operates on `decisions` (`holdspeak/db/schema.py:387`); its service returns a `DecisionLifecycleReceipt` with subject, action, actor, old/new lifecycle and time (`holdspeak/services/decision_lifecycle_service.py:36`; `holdspeak/db/decisions.py:617`, `:662`). That result has no rendered body or document version. The probe's direct service call is not evidence about kernel receipts on a routed operation.

A reusable stored document candidate is `DecisionRecordService`: create from a meeting decision or an authored desk decision (`holdspeak/services/decision_record_service.py:91`, `:123`), or its canonical `create` (`:45`). Storage is `decision_records`, related sources/work, and field-level revisions (`holdspeak/db/schema.py:1129`, `:1144`, `:1154`, `:1164`). The schema explicitly distinguishes the mutable governing **Decision Record** from immutable kernel evidence called a receipt (`:1124`). Q1 recommends this governing record as the shared decision document; it does not assume that the owner's phrase already settled the backend identity.

An active record can change; each changed field adds a revision (`holdspeak/services/decision_record_service.py:150`). `get` returns the present record plus sources, work and revisions (`:428`). This is useful audit history, but no published full-document revision or text/Markdown channel renderer. A revision row is one field change, not a complete sendable version. Render a specific record snapshot with the decision, rationale, owner/review date and source information; include its lifecycle/successor when applicable. Freeze that snapshot and digest at preparation. The owner then sends the words in the preview even if the active record changes later.

The separate decision lifecycle/promotion code (`holdspeak/services/decision_lifecycle_service.py:36`, `:55`) is not a send renderer. Do not send raw kernel receipts or assume a promoted artifact is the canonical governing record.

### Meeting summary: saved intelligence, not the transcript export

The owner gesture queues intelligence at `holdspeak/services/meeting_intel_service.py:199`. The bound worker produces summary/topics/actions (`holdspeak/intel_queue.py:460`); publication inserts a summary into `intel_snapshots` only after its transcript fence (`holdspeak/kernel/meeting_plugin_projection.py:262`). Meeting-save also has a snapshot writer (`holdspeak/db/meetings.py:347`). The stored header/segments belong to the meeting; summary history is `intel_snapshots(id, meeting_id, timestamp, summary, raw_response, created_at)` (`holdspeak/db/schema.py:125`).

Historical summary rows therefore **do exist**. They are not a frozen full export. `_load_latest_intel` chooses by `timestamp DESC`, joins the current topics/actions, and drops the snapshot ID from the returned `IntelSnapshot` (`holdspeak/db/meetings.py:558`). The bound writer uses meeting duration as that timestamp (`holdspeak/kernel/meeting_plugin_projection.py:273`), so it is not a unique run/version key. Preserve a selected snapshot/job identity and freeze any included related rows; do not use the current “latest” composite as historical proof.

`MeetingService.export_meeting` reads the stored meeting plus up to 200 plugin artifacts (`holdspeak/services/meeting_service.py:501`). Its HTTP/MCP service accepts Markdown or JSON (`:507`); the lower-level renderer also supports text and SRT (`holdspeak/meeting_exports.py:224`).

**The current Markdown and text exports include the transcript.** Markdown includes summary, topics, actions, optional artifacts, tags/bookmarks and the transcript (`holdspeak/meeting_exports.py:118`, `:159`); text includes summary and transcript (`:170`, `:183`). Passing these exports unchanged to “Send summary” would send more than that action names.

Phase 11 needs a summary-specific renderer and a selected stored intelligence revision/snapshot. Recommended default: title/date, summary, and explicitly included decisions/actions; no transcript. Read the stored result instead of invoking a model during preview or Send. A re-run of intelligence or a rename must not change an already prepared payload. Summary absence is a named refusal, not a transcript fallback.

History's CLI export calls the same writer (`holdspeak/commands/history.py:139`; `holdspeak/meeting_exports.py:261`); it writes a file, but creates no channel preparation or send provenance row. The local probe saved real meeting records and two summary snapshots, then showed that the same meeting ID exported different bytes after a source change. It did not invoke a model or claim to test the production analysis route.

## 3. Slack: one more channel, with an explicit provider contract

### Existing C4 is a different send path

`slack_message_for` formats the aftercare digest/follow-up (`holdspeak/slack_export.py:150`) and applies a 3,800-character cap with a visible truncation note (`:36`, `:73`). `build_slack_connector` injects the configured webhook URL at execution and delegates to the webhook actuator (`:166`). The URL validator accepts any HTTPS host, plus HTTP loopback (`:49`); the comment at `:204` about a removed Slack-host check is not the actual validator's rule.

Execution reads the then-current Settings webhook (`holdspeak/web/routes/actuator_shared.py:241`, `:265`; `holdspeak/services/meeting_aftercare_service.py:103`). That is neither a frozen saved destination nor the channel send lifecycle. Settings carries the URL into configuration (`holdspeak/services/settings_service.py:604`, `:621`, `:1020`); `Config.save` writes the dataclass as JSON (`holdspeak/config/core.py:387`). Redacting the value from Settings reads (`holdspeak/services/settings_service.py:173`) does not give native key custody. The URL itself is a credential.

The real aftercare producer records a text/body proposal (`holdspeak/services/meeting_aftercare_service.py:157`, `:166`). When its captured policy allows `control_posture`, it approves and executes in the same call (`:170`). That is an existing route which Phase 11 must not inherit as “agent prepares”: channel preparation must stop before owner Send. The legacy webhook opener also follows urllib redirects (`holdspeak/plugins/builtin/webhook_post_actuator.py:125`) and treats any 2xx as success while raising for every other status (`:147`). Those semantics do not meet the Phase 10 proof/UNKNOWN contract.

### Public contract, read 2026-09-29; no account or send

| Choice | Target and authority | Native proof | Cost |
|---|---|---|---|
| Incoming webhook | Secret URL bound to its installed channel; `incoming-webhook` installation permission | Successful response is `200` / `ok`, with no message `ts`. It cannot itself supply a message permalink. | Easier per-channel setup; a receipt must state the narrower acknowledgement scope. |
| Bot token + `chat.postMessage` | Saved workspace/account and channel ID; bot has `chat:write` and access to that channel | Success returns `ok`, `channel`, `ts`. Validate those against the frozen target. | Stronger native proof and a discoverable message; requires an installed app/token. |

Sources: [incoming webhooks](https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/), [chat.postMessage](https://docs.slack.dev/reference/methods/chat.postMessage/). Recommendation: a small declared Slack provider interface, **bot token first**. Incoming webhook is an alternative implementation, not a special UI escape from Send. This is an open owner fork (Q3).

`chat.getPermalink` takes the channel and timestamp and returns a URL; it still needs a token although it requires no additional scope. Proposed behavior: preserve successful post proof if this separate lookup fails; failure to get a link must never trigger a second post. [Slack permalink contract](https://docs.slack.dev/reference/methods/chat.getPermalink/)

### What the channel must add

Follow the email seam: its provider interface separates serialization, preview, plan, auth and outcome interpretation (`holdspeak/services/channel_email.py:110`); its `addressed` channel freezes destination-dependent bytes (`:653`, `:698`). Slack's proposed equivalent serializes the **entire request body** once, including channel ID/text and any formatting/unfurl settings. Derive the preview from those bytes. Do not reuse C4's cap after the owner has previewed a document.

The native keyring pattern is already present for macOS Keychain, Linux Secret Service and Windows Credential Manager (`holdspeak/services/channel_email.py:396`). Store a bot token or the entire webhook URL there, with a nonsecret provider/key reference in the destination. Resolve secrets at dispatch; never place them in `payload`, operation arguments, receipts or a public target URL. A webhook key reference must not be retargetable to a different channel while an old prepared send remains valid: bind a credential version/fingerprint to the destination, or park/recreate the destination when replacing it. An isolated HOME does not isolate the OS keychain; probes use no live keyring.

For a bot destination, freeze the verified workspace and bot identity as well as the channel ID. Slack's `auth.test` returns `team_id`, `user_id` and, for a bot, `bot_id`; a changed token must not silently change the sending account. Proposed setup/dispatch identity checks are admitted egress to `slack.com`, not a secret-bearing local “read.” The owner presses Send; Slack posts as the installed app's bot. No impersonation scope is needed. [Slack identity check](https://docs.slack.dev/reference/methods/auth.test/), [chat:write scope](https://docs.slack.dev/reference/scopes/chat.write/)

The egress child must carry the send's authenticated principal, parent, broker and payload digest, as email does (`holdspeak/services/channel_email.py:636`, `:641`). Allow **`slack.com:443`** for Web API calls or **`hooks.slack.com:443`** for commercial Slack webhooks. Use exact hosts, no wildcard; refuse redirects; sanitize transport failures before any native record. GovSlack requires a distinct, explicit future host/provider choice. A link's workspace host is receipt data, not blanket permission to send to that host.

### Proposed outcome pins and limits

Pin a small, reviewed response table; do not treat every HTTP 2xx as success or every error as non-delivery. Bot success needs `ok: true` plus valid `channel` and `ts`; webhook acknowledgement needs its documented status/body. Treat timeouts after a possible write, 5xx, redirects, malformed answers, success without required proof, and unlisted errors as **UNKNOWN**. Slack explicitly says `internal_error` and `fatal_error` can occur after partial success. [chat.postMessage errors](https://docs.slack.dev/reference/methods/chat.postMessage/)

The following is a proposed **small pinned list**, to become executable provider tests before build closure. An unlisted response remains UNKNOWN even when Slack documents other error names.

| Provider | FAILED candidate pins: certain non-delivery | Not FAILED |
|---|---|---|
| Webhook | `400 + invalid_payload`; `403 + action_prohibited`; `404 + channel_not_found`; `410 + channel_is_archived` | `500 + rollup_error`, unlisted status/body pairs, or `200` without exact `ok` acknowledgement |
| Bot Web API | `ok:false` with `not_authed`, `invalid_auth`, `token_revoked`, `missing_scope`, `channel_not_found`, `not_in_channel`, `is_archived`, or `no_text`, in the expected Slack JSON envelope | Bare status codes, `internal_error`, `fatal_error`, missing/mismatched proof, unlisted codes |
| Either | Documented `429` rate refusal, retaining bounded `Retry-After`; or transport proof that no request byte could leave | A timeout/drop after possible transmission, generic 5xx, redirect, or an error whose delivery semantics are unknown |

These are documentation-grounded candidates, not live-account pins. Sources: [webhook status/error pairs](https://docs.slack.dev/changelog/2016-05-17-changes-to-errors-for-incoming-webhooks/), [Web API native errors](https://docs.slack.dev/reference/methods/chat.postMessage/), [rate limits](https://docs.slack.dev/apis/web-api/rate-limits/). Local validation is REFUSED before the boundary. No automatic repost, including after `Retry-After`; the owner makes a new send. Slack generally allows one message per second per channel; this does not call for a new unattended retry queue.

Slack recommends short text (4,000 characters) and truncates over 40,000; block limits differ. These are not C4's 3,800-character product cap. Proposed first implementation: one text message, a conservative declared cap before preparation/dispatch, and a named too-large refusal. Do not silently truncate, split into multiple posts, or add file-upload machinery in this phase. The cap is Q4. [Slack message limits](https://docs.slack.dev/reference/methods/chat.postMessage/)

**C4 recommendation:** move its owner-facing send onto the same channel contract; retain its digest/follow-up renderers and historical proposal evidence. Park the old executor/setup path when the replacement is usable. Do not silently convert an arbitrary HTTPS webhook into Slack, copy its secret to a DB row, or run old and new sends for one press. No compatibility framework or destructive migration is needed in this pre-alpha phase (Tenets 1–3).

## 4. MCP and thread authority

| Job | Tools today | Authority and gap |
|---|---|---|
| Produce/read a daily brief | `monday_brief.generate`, `monday_brief.get`, shelf tools (`holdspeak/mcp/tools.py:495`, `:1248`) | WORK (`holdspeak/mcp/tool_authority.py:95`); no sendable document renderer/source-by-ID API. |
| Produce/read a decision record | `decision_record.create_from_meeting`, `create_from_desk`, `get`, `list`, `search` (`holdspeak/mcp/tools.py:418`, `:1199`) | WORK (`holdspeak/mcp/tool_authority.py:84`); no document export or kind-specific channel preparation. |
| Read/export a meeting; run its intelligence | `meeting.get`, `meeting.export`, `meeting.run_intelligence` (`holdspeak/mcp/tools.py:318`, `:1085`) | WORK (`holdspeak/mcp/tool_authority.py:47`, `:70`); existing export is full meeting Markdown/JSON, not a summary Send. |
| Preview/prepare/read channel sends | `channel.preview`, `channel.prepare`, `channel.sends` | WORK (`holdspeak/mcp/tool_authority.py:265`); currently update-only. Generalize these tools rather than add three parallel send APIs. |
| Send/discard | `channel.send`, `channel.discard` | EGRESS (`holdspeak/mcp/tool_authority.py:271`); `owner_press=True` (`holdspeak/channel_operations.py:241`, `:288`). Applies to file sends too. |
| Save/park a destination | `channel.save_destination`, `channel.remove_destination` | AUTHORITY (`holdspeak/mcp/tool_authority.py:266`); owner press stays required. |
| Save a secret | Email precedent `channel.save_email_key` | HTTP only, `held=(api_key,)`, owner-only and owner-press (`holdspeak/channel_operations.py:319`). No MCP key tool today. Use the same held-secret boundary for Slack; any future exposed configuration tool is CONFIG. |

The thread gate removes non-WORK tools from all modes and refuses a forged call (`holdspeak/services/thread_tools.py:325`, `:365`, `:592`). **WORK is not the same as offered in every palette:** the default chat palette (`:344`) contains brief/decision reads but no `channel.prepare`. If Phase 11 promises “ask a thread to prepare this,” add only the needed WORK tools to the intended palette/mode and test that path; an MCP-only probe cannot prove chat discoverability.

The external-agent check is separate: `holdspeak/kernel/channel_send.py:19` admits prepare under the agent identity; `holdspeak/kernel/project_codec.py:62` derives rights and refuses other owner operations. Probe evidence shows a real agent can prepare and receives `owner_principal_required` for Send. WORK classification also does not grant an external agent project publication rights: the same probe received `project_delegation_required` for publishing an update. Do not expand authority as a side effect of adding source kinds.

## 5. Findings and the owner forks

Ranked by cost to the owner; all are grounded gaps/recommendations, not defects introduced by this docs lane.

| Rank / home | Finding | Tenets |
|---|---|---|
| F1 — §3, Q5 | C4 has mutable Settings custody/target, posture-triggered execution, redirect following and different outcome semantics. Route preparation and owner Send through one lifecycle; do not carry these behaviors into it. | 2, 3, 5; Articles V, VI |
| F2 — §2, Q2 | “Send summary” cannot reuse the full meeting export: it includes the transcript. The source selection and rendered content must match the action. | 3, 7 |
| F3 — §1, Q7 | Generic serialization exists, but update-bound descriptors, rendering, file naming and history prevent the promised three new sources. Manual confirmation is separately update-only. Change the chosen seams together. | 3, 5, 7 |
| F4 — §§1–2, Q1 | None of the three sources supplies the required complete published document version today. Freeze source provenance and bytes at preparation; avoid three new publishing systems. | 1, 2, 3 |
| F5 — §3, Q3 | Webhook acknowledgement cannot prove a native message ID/link. Choosing it silently would weaken the Send receipt. | 3, 7; Article VI |
| F6 — §4, Q6 | A WORK tool can be callable through MCP yet absent from the default chat palette. “Agents can prepare” must name which route was verified. | 3, 7 |
| F7 — §3, Q4 | Long documents exceed a practical single Slack message. The old cap truncates; an exact-document Send needs a pre-send refusal or an explicitly ruled alternate payload. | 1, 3, 7 |

These questions are for the owner to rule at charter; this draft does not wait for answers to complete grounding:

1. **What counts as the brief and decision?** Recommended: the persisted daily chief-of-staff/next-day brief and the governing Decision Record, frozen when prepared. Exclude project preparation briefs, generated announcements and raw kernel receipts from this first scope. No extra Publish step.
2. **What is in a meeting summary?** Recommended: title/date, saved summary and selected decisions/actions, with provenance; omit transcript and unrelated plugin artifacts. An explicit full meeting export remains a different document choice.
3. **Which Slack transport first?** Recommended: bot token with `chat.postMessage`, native channel/timestamp proof, optional permalink lookup. If the owner prefers webhook setup, accept its narrower `200/ok` acknowledgement explicitly and label it without a fabricated link or ID.
4. **What should happen to a long Slack document?** Recommended: one message, refuse above 4,000 rendered text characters before dispatch. This is a product default, not Slack's hard limit. Offer another saved channel; no truncation, multi-post split, upload or automatic summary. The owner can choose a higher explicit cap below the documented truncation threshold.
5. **Should the old C4 sender remain active?** Recommended: route the supported content through Channel Send and park C4's separate send/setup once that works. Keep its renderers and history. Owner re-saves the destination through native credential custody; no silent credential migration.
6. **Should the ordinary thread prepare these sends?** Recommended: yes, in the existing work-capable modes, with the minimal read/preview/prepare tools. Keep Send, Discard, destination changes and secrets behind the owner's press.
7. **Does “same channels” include a manual-delivery confirmation for the new kinds?** Recommended: transport sends first; keep the current update confirmation intact and park generalized manual confirmation. If included now, give it generic source provenance and an owner-only EGRESS ledger operation; do not insert non-updates into `project_update_deliveries` or call a human confirmation native transport proof.

## 6. Verification, ledger and limits

The Send, source and Slack workers ran as Luna at xhigh. Astra read the important source anchors and probe output before incorporating them. Worker findings are evidence, not Muad'Dib's check.

Test setup used `uv sync --extra test`. The full runner installs the locked web dependencies with `npm ci`, uses a fresh HOME with the existing browser/npm caches, and excludes `tests/e2e/test_metal.py` as required by `CLAUDE.md`.

Stored pytest failure output has trailing whitespace removed for the commit; all content, line order and result counts are retained.

| Evidence | What it proves |
|---|---|
| [Send probe](probes/send_contract.py.txt), [output](probes/send_contract.out.txt) | Real hub/MCP producer, frozen prepared row, schema columns, preparer identity, owner-only Send refusal. No successful dispatch. |
| [Source probe](probes/document_sources.py.txt), [output](probes/document_sources.out.txt) | Real stored meeting and exports change bytes under one meeting ID; same-day brief deduplication and next-day distinct ID; decision record/receipt distinction; alternate brief types. No model execution. |
| [Slack docs probe](probes/slack_public_docs.py.txt), [output](probes/slack_public_docs.out.txt) | GET-only official documentation checks, all PASS. Astra reran it after aligning the cap recommendation with Q4. Public contract evidence only; no account, token or message. Printed recommendations are not rulings. |
| [Backend fences](probes/verify_backend.py.txt), [collection](probes/verify_backend.collect.out.txt), [run](probes/verify_backend.out.txt) | **182 collected; 182 passed.** Existing send/recovery/restart, meeting export, decision record, daily brief, Slack actuator and thread gate tests. Local file effects or injected transport seams only. |
| [Full-suite runner](probes/verify_full.sh.txt), [output](probes/verify_full.out.txt) | **3 failed, 13,440 passed, 117 skipped, 4 xfailed, 36 warnings; exit 1.** `pytest -q -n auto --ignore=tests/e2e/test_metal.py`, isolated HOME, 3,384.10 seconds. The full suite is not green; see the ledger below. |
| [Failure recheck](probes/verify_failures.py.txt), [collection](probes/verify_failures.collect.out.txt), [run](probes/verify_failures.out.txt) | **3 collected; 1 failed, 2 passed** serially in another isolated HOME. Records an empty product/test diff against HEAD and the heartbeat's actual timing instructions. Both Speak loop cases pass; the wall-clock assertion still fails. |

**Baseline glass inspected:** the full suite produced the current Phase 10 prepared-file Send shots below. At both widths, Astra observed the `SAVED` receipt, file path, preparer identity and revision, with another prepared send still listed. These are isolated test fixtures, not an owner-desk observation or a Phase 11 face. The scratch PNGs are not part of this docs-only commit:

- `.tmp/evidence-shots/pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-shots/29-prepared-file-sent-1440.png`
- `.tmp/evidence-shots/pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-shots/29-prepared-file-sent-393.png`

**Verification ledger:** no product or test files differ from HEAD, and no test was changed to obtain these results.

| Class / home | Evidence and disposition |
|---|---|
| (a) Inherited test assumption — `tests/integration/test_phase200_recipe_catalog.py:648` | The test demands timing integers in `co_consts`. On Python 3.14.2 this run has no integer constants there, but disassembly records `LOAD_SMALL_INT 60`, `10`, `60`; the actual loop still declares its tick and waits (`holdspeak/runtime/heartbeat.py:86`, `:89`). The same assertion fails in the full and serial runs. This is a test compatibility gap, not proof that the wall-clock loop disappeared. No repair in this docs lane. |
| (b) New regression | None identified; product/test diff is empty. The lane adds only this report and probe sources/output. |
| (c) Unrelated suite-dependent failures — `tests/e2e/test_hs176_loop_glass.py:276` | Both widths saw the first utterance's text instead of the second corrected utterance in the full run. Both pass in the serial recheck. A timing/order interaction is a hypothesis, not a diagnosed cause or a reason to call the full run green. The test's landing helper waits for a visible result (`:161`); no runtime or test fix is claimed. |

F1–F7 are separate existing capability/design gaps, with homes in this document and the listed owner forks; they are not relabelled as flakes. The table above is the home for the verification debt in this bounded lane. This lane does not edit the phase roadmap or BACKLOG because its write scope is this grounding only.

Unknown: the full-run Speak failure cause is unresolved. No Slack workspace/token/real webhook, live Slack proof, actual rate/size boundary, native keyring round trip on macOS/Linux/Windows, or Phase 11 face was tested. No new atlas cases or Phase 11 shots are claimed by this backend grounding; the Phase 10 fixture shots above do not close an atlas walk. There is no product change/story flip or merge verdict. The future implementation must run actual atlas cases through `scripts/graph_walk.py`, one case per invocation, and the faces lane must supply its own glass evidence. Phase 10's existing tests do not establish that Phase 11 already works.

**Amendments:** none. These recommendations do not amend the Phase 10 lifecycle, the owner's egress authority, or the Seven Tenets. **Check:** not requested by Astra; Muad'Dib checks this draft in his own session.
