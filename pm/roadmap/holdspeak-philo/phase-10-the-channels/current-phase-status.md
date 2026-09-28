# Phase 10 - The Channels

**Last updated:** 2026-09-28 (round two: Codex Astra r1 DO-NOT-RATIFY paid — the send lifecycle settled in `design/send-lifecycle.md` (a durable dispatch boundary; recovery never dispatches again; a small send record for prepare and press; the transport bytes in a private file, not argv; exact-target binding; the file channel the one direct writer), Mail conditional, the two absolute claims corrected, the verification split; Codex Astra r2 owed; the owner's ratification owed. Earlier: DRAFTED by the Fedaykin docs lane (Opus 5.5) for Muad'Dib, on the owner's words and picks of 2026-09-28; grounded on main `920e6189`: the census of every outbound path, each channel's mechanics probed on an isolated HOME, the email transports laid out. The Codex Astra check is owed; the owner's ratification and his answers to Q1–Q6 are owed. Nothing is built.)

**Status:** DRAFT — round two: Codex r1 DNR paid; Codex r2 owed; the owner's ratification owed.

## Goal

The owner sends a finished document to where it goes, with one press. He sets up his destinations once (a folder, a GitHub issue or pull request, a Jira work item, a Confluence space, an email address). Under a published project update he picks one destination, sees exactly what will go there, and presses Send. The Room shows what was sent, where, and the proof (the file, the link, the handed-to-Mail receipt), or the true reason it was not sent, or that the result is unknown. An agent or the steward can prepare a send; only he sends. The project update is the first document; the contract takes any rendered document, so the Monday brief, a decision or a meeting summary plug in later with no new channel work.

## Authority

The owner, 2026-09-28 (verbatim):

> "I'd love for us to explore #2 [delivery is copy+confirm only]. I feel like 'delivery' should be an abstraction that we can plug many things into. If you think about it, one implementation could be a simple file system delivery, another would be a slack message, another an e-mail, each..., with their own senses of abstraction, right? Not to mention gh work and acli work, that could also plug into that."

His picks, by AskUserQuestion, 2026-09-28:

- **Payload:** "Any document; updates first" — the contract takes a rendered document; the project update is the first consumer; the Monday brief, a decision, a meeting summary plug in later.
- **Channels for this phase:** "File system", "gh + acli", "Email". Slack was not picked: Out (BACKLOG).
- **Who sends:** "You, every time" — agents and the steward may PREPARE a send, never send, in this phase.
- **Destinations:** "Saved destinations" — named, set up once; each send is one pick.

The ledger this phase pays: Phase 9's THE LEDGER row 2, "The product does not send the update" (`../phase-9-the-room-on-the-contract/final-summary.md:123`), and the BACKLOG row "Automated send of a published project update" (`pm/roadmap/holdspeak/BACKLOG.md:1393`).

Carried, unchanged: the Seven Tenets (`docs/internal/CONSTITUTION.md:18-60`); Article III, honest egress (`:85-91`); Article XI (`:167-193`); UX-CANON §A.1 every verb the library Button, §A.2 the canvas before build, §A.3 no prose, §A.4 no modals, §A.9 egress exactly where egress happens, §A.10 honest states, §A.11 a verb that does nothing is a lie (`docs/internal/UX-CANON.md:17-58`); the laws of handovers XXVIII–XXXI; Phase 5's settled positions; Phase 7's "Settled between the brains"; Phase 9's admission by effect (its Q1) and its delivery lessons (bound to its update, one key per press, REFUSED with its reason, a lost answer is not "not sent"); the owner's ruling that MCP flows through the services (2026-09-23); the owner's Jira ruling: `acli`, many accounts on many sites, switch and verify.

## The roots

- **Tenet 7 (a Senior Architect with reports):** he tells his boss and his team where a project stands. Today the Room gives him the text and he carries it himself (grounding F1). The job is his.
- **Tenet 3 (help and accelerate):** one pick and one press, not copy, switch app, find the thread, paste, come back, confirm.
- **Tenet 1 (no over-engineering) and Tenet 3 ("never a million interfaces"):** no new plugin framework. The write seam exists: Phase 38's `WriteConnectorManifest` + `build_gated_connector` (plan → kernel → interpret), with six live users (grounding F2). A CLI channel is one manifest, one `plan`, one `interpret`; the file channel is the one direct writer, stated as an exception, not a framework extension (the write manifest has no file kind, `holdspeak/plugins/gated_connector.py:43-47`). The connector SDK stays the read side.
- **Tenet 2 (not even pre-alpha):** the channels he named, no more; each proven by one real send or a named limit.
- **Tenet 5 (component framework):** the Send well and the destinations setup compose library species, drawn on the canvas and ratified before build.
- **Tenet 4 (ASD-STE100):** the face words are verbs and states: SEND, SENT, REFUSED, FAILED, UNKNOWN, PREPARED, HANDED TO MAIL.
- **Article III:** a send is egress (except to a local folder that no cloud client syncs). The host chip is on the destination row and on the Send well, never in a header.
- **Article XI:** a send crosses egress or files; it is admitted once and ends in a terminal receipt, including the result that cannot be determined. Its CLI or network effect is a child of the send (XI.1: nesting exempts nothing; today the nudge's child has no parent, F5).

## The framing, checked (Muad'Dib's brief, grounded)

| Claim | Verdict | Evidence |
|---|---|---|
| "A `deliver` capability in the connector SDK" | **Refined.** The SDK is the read side; the write seam is `holdspeak/plugins/gated_connector.py` | grounding F2 |
| "Every send through `external.egress`" | **Refined.** A CLI send (`gh`, `acli`, `osascript`) is `subprocess.exec`; only a socket or HTTP send (SMTP) is `external.egress`; a local file write is the send's own effect | grounding F3; `holdspeak/kernel/subprocess_exec.py:227-292` |
| "Saved destinations ARE that allow-list" | **Confirmed**, with the target frozen, not only the id (design section 5). The four named direct `external.egress` callers allow exactly their own destination; the webhook actuator already has a configured host allow-list (`holdspeak/plugins/builtin/webhook_post_actuator.py:158-168`) | grounding F6 (corrected in round two) |
| "`nudge.send` is a delivery in disguise" | **Confirmed**, with two defects: an unknown result is recorded as failed and offered again (F4); its `gh` child has no parent (F5) | `holdspeak/services/project_steward_service.py:1906-2066` |
| "`project_update_deliveries` gains channel + destination + native proof, additive" | **Confirmed** (insert-only, `operation_id NOT NULL UNIQUE`) | `holdspeak/db/schema.py:4170-4186`; `holdspeak/db/updates.py:470-560` |
| "The clipboard confirm stays as the manual channel" | **Confirmed**; existing rows read `manual` | `holdspeak/services/project_update_service.py:1929-1980` |
| (new) "Delivery" is the name | **Refuted as a code word.** `holdspeak/delivery/` is the Delivery Runtime and the repo runs Delivery Workbench; the product verb is Send, the code word is channel | grounding F12 |

## Status of this charter

DRAFT, 2026-09-28, written by the Fedaykin docs lane (Opus 5.5) for Muad'Dib. Round two paid Codex Astra r1 (DO-NOT-RATIFY, `checks/charter-astra-r1.md`): findings 1–5 are settled in one short design, `design/send-lifecycle.md`, which binds stories 01–03; findings 6–8 are paid in this file, the stories, the grounding and the BACKLOG. Owed: the Codex Astra r2 check (`docs/internal/TWO-BRAINS.md`); the owner's ratification and his answers to "Decisions for the owner" (Q1–Q6); the two canvases (story 04) before any face build. Nothing is built. The stories stay `backlog` until the owner ratifies.

## The grounding (main `920e6189`)

The full record, with the probes and their output: `docs/internal/philo/phase-10/grounding/README.md`. In short:

- **The census** (C1–C8): the update's Copy + Mark delivered (the manual channel), `nudge.send` (a GitHub comment), Cadence Telegram, the Slack export of a meeting, the meeting actuators (`gh issue create`, `gh pr comment`, webhook, the outbox file), the intel failure alert, the meeting export, the voice macros. Two are deliveries of a document to other people today: the nudge and the Slack export.
- **FINDINGs:** F1 nothing sends a published project update (meeting results already go to Slack, C4); F2 the write seam exists, the SDK is the read side; F3 a CLI send is `subprocess.exec`, whose admission hashes argv but not stdin; F4 the nudge turns "unknown" into "failed" and offers Send again (a double post); F5 the nudge's `gh` child has no parent; F6 the four named direct `external.egress` callers allow only their own destination (the webhook actuator has a real host list); F7 the old file connector overwrites without a word (probed); F8 `acli` 1.3.36 has no Confluence page create or update, only `blog create` (probed); F9 an `acli` send must switch and verify the account under the existing lock; F10 Mail.app's `send` answers only true or false (probed from its dictionary); F11 `markdown-it-py` imports only by accident; F12 "delivery" is a taken word; F13 Slack already sends meeting results; F14 the actuators' "what executes is what was previewed" binding exists to copy; F15 (round two) `gh` reads a body from a file or stdin, `acli jira` from a file only (stdin refused), `acli confluence` from a file, and a fixed `osascript` script reads a 0600 file without running its text; `acli` links a macOS keychain library, so a scratch HOME does not isolate its login.
- **Per channel:** the command, the admission of the effect, the proof, the custody and the badge (grounding section 3). No account exists on an isolated HOME: `gh` "not logged into any GitHub hosts", `acli` "unauthorized". A real send needs his login (Q6).

## Scope

- **In:**
  1. **The Send contract, the saved destinations and the file channel (story 01), as `design/send-lifecycle.md` settles it.** Declared operations (names proposed; story 01 fixes them): `channel.destinations` (list), `channel.save_destination`, `channel.remove_destination` (parks), `channel.check_destination`, `channel.preview`, `channel.prepare`, `channel.discard`, `channel.send`, `channel.sends` (what was sent). CLI channels use the existing seam: one `WriteConnectorManifest` + `plan` + `interpret` over `build_gated_connector`, with the owner principal, the parent and the broker threaded through it (design section 6); the file channel is the one direct writer. A **document** is `{ref, title, body_md}` from a renderer the document kind owns (the update's first; `project_update:<id>`). **Records** (design section 1): `channel_destinations` (no secret; Edit and Remove park, history kept); `channel_sends` (one row from prepare to its end: `prepared` → `dispatching` → `sent` / `failed` / `unknown`, or `discarded`), with the frozen target and the exact transport bytes; additive columns on `project_update_deliveries` (`channel` default `manual`, `send_id`, `outcome`, `proof_json`), inserted when a send settles `sent` or `unknown`. **The durable dispatch boundary** (design section 4): `dispatching` commits before any effect; recovery of an abandoned send never dispatches again — it returns the stored proof, reads a file back, or answers UNKNOWN. **Outcomes**: SENT (proof); REFUSED (named, before the boundary, nothing ran); FAILED only on a known non-delivery; UNKNOWN when HoldSpeak cannot know; HoldSpeak never submits again by itself. **Prepare and press** (design section 2): prepare completes under the preparer's identity with the frozen preview; the owner's press makes the send; Send and Discard settle with one conditional write, one wins. **The file channel**: a saved folder resolved with `realpath`; a new file per send with a collision-proof suffix and exclusive create (Q4); proof = absolute path + sha256 read back + size; badge `local`, or `cloud` for a folder the owner marked synced (no sync detector). The manual Copy + Mark delivered stays as the `manual` channel, unchanged (`project.mark_update_delivered`).
  2. **The GitHub and Atlassian channels, and the nudge on the GitHub channel (story 02).** The body reaches every CLI through a private 0600 payload file whose digest is checked just before dispatch; argv carries only paths, keys and flags, so the subprocess receipt carries no body (design section 3). GitHub: a comment on an issue or a pull request (`gh issue comment` / `gh pr comment --body-file <path>`), proof the comment URL; a gist is parked (Q2). Jira: `acli jira workitem comment create --key <ONE canonical key> --body-file <path> --json` (`--key` accepts a list, so one key is validated; never `--jql`, `--filter` or `--edit-last`). Confluence: `acli confluence blog create --space-id <id> --title <t> --from-file <path> --json` as Q3 rules (no page create exists, F8). Size limits refuse by name before dispatch. Each Atlassian send runs switch → status → create under the existing acli lock (F9), each command a `subprocess.exec` child of the send (F5 closed for the channels). The destination names the connection (site, email) from `watch_provider_connections`; its Phase 9 B1 state shows on the destination row. **The nudge**: `nudge.send` keeps its name and contract, sends through the GitHub channel's send path, parents its `gh` child (F5), and records an unknown result as unknown, never re-offering Send on it (F4).
  3. **The email channel as Q1 rules (story 03).** Recommended (b), conditionally (Q1): Mail.app by a fixed `osascript` script that reads the message from a 0600 file (no document text in script source), from the account he picks; the outcome label HANDED TO MAIL, never "delivered" and never a promise of the Sent box; Mail's own Outbox retry is Mail finishing the first handoff, not HoldSpeak sending again; the `false` answer is probed offline before it is mapped (until then UNKNOWN); macOS only. Under (a), SMTP stops before DATA unless every recipient is accepted. The To list is the saved destination; the subject is the document's title; the body is the document as plain text (HTML only if Q1 (a) and the owner asks; then `markdown-it-py` is declared, F11).
  4. **The Send face and the destinations setup (story 04; canvas first).** Under a published update: the Send well (in-world, no modal): the saved destinations as rows with their host chips, one pick, the preview exactly as the channel will get it, Send (library Button), the receipt rows (SENT with the link or path, HANDED TO MAIL, REFUSED and why, FAILED and why, UNKNOWN with "check" and the destination's link, PREPARED by whom with Send and Discard, DESTINATION CHANGED on a prepared row). The Copy and Mark delivered row stays. The destinations setup: where it lives (the Connections face is recommended, since the accounts live there) and its fields per channel are drawn on the canvas. Both canvases ratified by the owner before build (UX-CANON §A.2).
  5. **The atlas cases and their `.op` siblings for Send (story 05)**, at 1440 and 393.
  6. **The closing use (story 06), in two separate legs:** (A) the isolated rehearsal — a cold-context Codex session prepares a send of a published update from the MCP catalogue alone; the owner's Send is pressed on the face at 1440 and 393 (the rig presses as the owner on an isolated hub; file sends are real, remote channels use a recording runner); (B) the real-account leg, explicitly authorized by the owner per target (Q6), on his own session, because a scratch HOME isolates neither Mail.app nor the keychain logins of `gh` and `acli` (F15): one real send per channel, its proof read back from the far side, or a named limit. Owner-reviewed shots, never a sitting.
- **Out (with their homes):**
  - **Slack** as a channel: not picked (BACKLOG "PHILO-10 charter follow-ups"). The meeting Slack export (C4) stays as it is.
  - **An agent that sends under a grant** ("You, every time", this phase): BACKLOG. The kernel already refuses an AGENT at `subprocess.exec` (`holdspeak/kernel/subprocess_exec.py:177-186`).
  - **Other documents** (the Monday brief, a decision, a meeting summary): the contract is ready for them; each is a renderer and a Send well on its face. BACKLOG.
  - **Confluence page create or update**: `acli` has none (F8); BACKLOG, re-probe when `acli` changes.
  - **Moving the other outbound paths onto the channels** (Telegram, the Slack export, the webhook actuator, `gh issue create`, the intel alert): BACKLOG. The nudge is the only one moved (it is a GitHub comment of a text he reviewed).
  - **Undo of a send**, scheduled sends, attachments, edit-last-comment, a gist unless Q2 picks it: BACKLOG.
  - **Replacing the self-allow lists of the existing egress callers** (F6): report only; BACKLOG.

## Admission by effect (proposed; story 01 fixes the names)

| Operation | Effect | Admission | Who |
|---|---|---|---|
| `channel.destinations`, `channel.sends` | reads | exempt (XI.5) | owner; an agent reads |
| `channel.preview` | computation (render per channel) | exempt (XI.5) | owner; an agent |
| `channel.save_destination`, `channel.remove_destination` | changes the allow-list: authority (XI.1); Remove parks | **admitted** | owner only |
| `channel.check_destination` | GitHub / Jira / Confluence: an account probe (egress); folder and Mail: a local check | **admitted** for the remote channels (as `connection.recheck`, Phase 9); exempt for folder and Mail | owner |
| `channel.prepare` | inserts a `prepared` send row with the frozen target and preview; nothing leaves | **admitted**, completes under the preparer's identity (the receipt names who prepared) | owner, the steward, an agent as Q5 rules |
| `channel.discard` | decides a prepared send (`prepared` → `discarded`; one wins against Send) | **admitted** | owner only |
| `channel.send` | crosses egress or files (XI.1) | **admitted**, one terminal receipt: `succeeded` (SENT), `refused`, `failed`, `indeterminate` (UNKNOWN) | **owner only** ("You, every time"): the owner's press creates this operation; no operation is held for an agent; an agent's call is refused `owner_principal_required` with a receipt |
| its effect: `gh`, `acli` (switch, status, create), `osascript` | CLI | `subprocess.exec`, a **child** of the send, under the authenticated owner principal threaded through the seam (F5 closed; `holdspeak/connector_runtime.py:141-146`, `holdspeak/kernel/causation.py:28-33`) | the send's owner |
| its effect: SMTP (only under Q1 (a)) | network | `external.egress`, a child; the destination on the saved list | the send's owner |
| its effect: the file write | filing | the send's own effect by the one direct writer, after the dispatch boundary commits (a file write is outside SQLite rollback; design section 4) | the send's owner |
| `project.mark_update_delivered` | the manual channel | admitted, unchanged | owner only |
| `nudge.send` | a GitHub comment | admitted, unchanged; its `gh` child parented | owner; as Phase 9 ruled |

The journal carries the destination's id (`destination:<id>`) and the payload digest, not an email address or the body (the `external.egress` precedent: destination, data classes, digest, `holdspeak/kernel/external_egress.py:1-20`).

## Exit criteria (evidence required)

"Red on main" applies where a defect exists (F4, F5, F7-shaped overwrite, and the Room's take-over that dispatches twice, `checks/charter-astra-r1.md` finding 1); everywhere else the proof is new capability, shown through the real hub on an isolated HOME, never a test double that lies about the field a check reads (a recording runner mints through the channel's real `plan`). "At both widths" means 1440x900 and 393x852.

- [ ] 1. **The Send is discoverable and executable over MCP alone.** A fence reads only the real `tools/list` answer and maps "where can I send", "send my update to <destination>", "prepare a send", "what was sent" to a tool and an argument path; no description says an agent can send. Every in-scope operation is reachable by route, by MCP and by the rig's `op` step, and reaches the same declared operation and service in one hub.
- [ ] 2. **Admission by effect, as the table says.** One kernel operation and one terminal receipt per admitted row on both transports; each refusal class leaves its receipt; reads and previews leave none; each CLI or network effect is a child of its send (red on main for the nudge, F5); a send to a destination not saved, parked or changed since prepare is refused before any effect, and the record keeps the historical target; a Jira destination with more than one key is refused; an agent's send is refused `owner_principal_required` with a receipt; an agent's prepare completes under its own identity and the row waits until the owner sends or discards it; Send and Discard at the same time: one wins, the other is refused with a receipt. Fences with an authenticated principal; a deliberate mutation of each turns its fence red.
- [ ] 3. **What is sent is what was previewed.** For each channel, the digest of the preview equals the digest of the payload file the CLI read (or the file written); a change between preview and Send is refused (`preview_changed`, `payload_changed`); no body appears in argv, in a subprocess receipt, in a log or in an error (a sentinel fence); an oversize payload is refused `payload_too_large:<channel>`.
- [ ] 4. **Honest outcomes and the crash rule** (design section 4). SENT keeps its native proof (URL, path + sha256, the Atlassian id, HANDED TO MAIL); FAILED only on a pinned known non-delivery; UNKNOWN on a timeout, a kill, an unpinned nonzero exit, a missing or malformed proof; a restart, a lost caller or a failed settle write after the effect ends UNKNOWN (or the file's read-back proof) with **exactly one dispatch** (red on main: the Room's take-over dispatches twice with one key, `checks/charter-astra-r1.md` finding 1; red on main for the nudge: `failed` and re-offered, F4); the same key twice answers the first result with one effect.
- [ ] 5. **Each channel, one real send or a named limit — the real-account leg kept apart from the rehearsals.** File: a real write on the isolated HOME. GitHub, Jira, Confluence (as Q3 rules), email (as Q1 rules): one send each to a target the owner authorized under Q6, on his own session, its proof read back from the far side (the URL answers, the Jira comment or the blog post is there, the mail reached his inbox; HANDED TO MAIL is not claimed as delivery); or the limit named with its reason. Tokens and addresses redacted at capture (handover XXX law 12).
- [ ] 6. **The face, as ratified.** The Send well and the destinations setup match the owner-ratified canvases; the state/width matrix below is shot and fenced through the real hub; every verb is the library Button; the host chip is on each row that leaves the machine; no modal; the web baseline has zero branch-new failures.
- [ ] 7. **The atlas** has a case for each Send state at both widths, with an `.op` sibling where the outcome is durable, and transitions for: a restart during `dispatching` (UNKNOWN, one dispatch), a replay of the same key, a destination changed after prepare (REFUSED, row stays prepared), and receipts that survive the face's branch change (away and back); the Phase 7, 8 and 9 atlas cases still pass.
- [ ] 8. **The closing use.** A cold Codex session (the Phase 9 R3 setup: scratch root, HOME and CODEX_HOME with the auth file only, the isolated hub the only MCP server, zero repository reads in the retained log) prepares a send of a published update to a saved destination; the owner's Send is pressed on the face; the Room shows SENT with its proof at 1440 and 393, read back from the hub. Rehearsed, owner-reviewed shots; never recorded as a sitting.

## The state/width matrix (story 04 shoots each at 1440 and 393)

| State | What the face shows |
|---|---|
| No destination saved | the Send well's one true line and the verb that opens the setup |
| Destinations listed | one row per destination: name, channel, host chip, account state (Phase 9 B1: connected, never checked, needs him) |
| Destination picked | the preview as the channel will get it, and Send |
| Sending | Send busy; nothing else moves |
| SENT | the row: destination, time, the proof (link, path, HANDED TO MAIL) |
| REFUSED | the reason in plain words (not saved, account not connected, owner only, not published) |
| FAILED | the channel's reason (for example, "GitHub: issue not found"); nothing was sent |
| UNKNOWN | "check <destination>" with its link; Send is a new send with its own key, never a retry of the old one |
| UNKNOWN after a restart | the same row, with the reason `interrupted`; no second dispatch |
| HANDED TO MAIL | the Mail outcome; no "delivered" word |
| DESTINATION CHANGED | on a prepared row: REFUSED `destination_changed` or `destination_parked`; Discard and prepare again |
| PREPARED | who prepared it, where to, the preview; Send and Discard |
| Manual | Copy, To, Mark delivered, as Phase 9 |
| Several sends | each with its own row and receipt; no counter of zero |

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| PHILO-10-01 | The Send contract, saved destinations and the file channel | backlog | [story-01-the-send-contract-and-the-file-channel](./story-01-the-send-contract-and-the-file-channel.md) | — |
| PHILO-10-02 | The GitHub and Atlassian channels (and the nudge) | backlog | [story-02-the-github-and-atlassian-channels](./story-02-the-github-and-atlassian-channels.md) | — |
| PHILO-10-03 | The email channel | backlog | [story-03-the-email-channel](./story-03-the-email-channel.md) | — |
| PHILO-10-04 | The Send face and the destinations setup (canvas first) | backlog | [story-04-the-send-face-and-the-destinations](./story-04-the-send-face-and-the-destinations.md) | — |
| PHILO-10-05 | The atlas cases for Send | backlog | [story-05-the-atlas-cases-for-send](./story-05-the-atlas-cases-for-send.md) | — |
| PHILO-10-06 | Prepare it cold, send it yourself | backlog | [story-06-prepare-it-cold-send-it-yourself](./story-06-prepare-it-cold-send-it-yourself.md) | — |

The stories stay `backlog` until the owner ratifies the charter.

## Lanes (proposed)

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| The contract | 01 | Muad'Dib's lane (Fedaykin, Opus 5.5) | Codex Astra | ../wt-philo-10-01 | feat/philo-10-01-send-contract |
| The channels | 02, 03 (parallel after 01) | Muad'Dib's lane (Fedaykin, Opus 5.5) | Codex Astra | ../wt-philo-10-02, ../wt-philo-10-03 | feat/philo-10-02-gh-atlassian, feat/philo-10-03-email |
| The face | 04 (canvases now; build after 01) | Muad'Dib's lane (Fedaykin, Opus 5.5) | Codex Astra | ../wt-philo-10-04 | feat/philo-10-04-send-face |
| The atlas and the closing use | 05 → 06 | Astra (Luna) | Muad'Dib | ../wt-philo-10-05, ../wt-philo-10-06 | feat/philo-10-05-atlas, feat/philo-10-06-prepare-cold |

01 lands first: the operation table, the record columns and the destinations table have one shipping owner. 02 and 03 each add one channel module and its manifest; they touch the send service only through the channel registry 01 defines. The story 04 canvases can be drawn while 01 is built. A lane runs its scoped fences and rig cases only. The orchestrator runs the full suite before the done call (`docs/internal/ORCHESTRATION.md:64-67`). CI does not gate a merge (the owner, 2026-09-28; `../phase-9-the-room-on-the-contract/final-summary.md:146`).

## Where we are

2026-09-28, round two: Codex Astra r1 DO-NOT-RATIFY (`checks/charter-astra-r1.md`) paid — `design/send-lifecycle.md` settles findings 1–5; Q1 qualified; F1 and F6 corrected; the verification split into isolated rehearsals and an authorized real-account leg; the full-suite duty restored; atlas transitions added; transports probed (`docs/internal/philo/phase-10/grounding/transport-probe.out.txt`). Owed: the Codex Astra r2 check; the owner's ratification and Q1–Q6.

2026-09-28: DRAFTED from the owner's words and picks of 2026-09-28, Phase 9's ledger row 2 and the grounding on main `920e6189` (`docs/internal/philo/phase-10/grounding/README.md`): the census (C1–C8), F1–F14, each channel's mechanics on an isolated HOME, the email transports. Owed: the Codex Astra check; the owner's ratification and Q1–Q6; the story 04 canvases before the face build. Nothing is built.

**Estimate (PROVISIONAL until the design is checked; not grounded per story):** effort **10.5–14.5 engineering days** — 01 3.5–4.5 (about nine declared operations, the two records and the columns, the dispatch boundary and its recovery, prepare and press, the file channel, the parity, crash and outcome fences); 02 2–3 (three channels on the existing seam, the acli lock, the nudge's two repairs); 03 1–1.5 under Q1 (b), 1.5–2 under (a); 04 2–3 (two canvases, the Send well, the setup, the matrix at two widths); 05 about 1; 06 about 1, plus the real-send legs Q6 allows. Calibration: Phase 9's 9–13 d closed in about two elapsed days of build plus check rounds; Phase 8's closed in about a day and a half. **Elapsed forecast: about 3–5 days, gated by the two canvases, the Codex check rounds, the owner's word and his accounts for the real sends.** The range is re-stated after story 01 lands.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A new plugin framework or a "channel SDK" instead of three manifests on the existing seam | medium | one `WriteConnectorManifest` + `plan` + `interpret` per channel (F2); a registry is a dict of those | a new Protocol hierarchy, a capability in `connector_sdk.py`, or a discovery of channel packs |
| A double send | medium | one key per press; UNKNOWN is never re-sent by the product; Send after UNKNOWN is a new press with its own key; the nudge fixed the same way (F4) | a fence where a timeout leads to a second effect without a second press |
| The preview and the sent bytes differ, or the body leaks through argv | medium | the payload frozen at prepare; a private 0600 payload file checked against the digest just before dispatch; argv carries no body (design section 3) | a parity fence green while a recording runner shows other bytes; a body sentinel in argv, a receipt or `ps` |
| A second dispatch after a crash or a failed settle | medium | the durable dispatch boundary; recovery never dispatches (design section 4) | a take-over fence that records two dispatches for one key |
| An `acli` send leaves his terminal on another account | medium | switch → status → create under the existing lock (F9); the story names whether it switches back | a send outside `_ACLI_LOCK` |
| Real sends touch his real accounts or leak addresses into tracked files | medium | the real-account leg only to targets he authorized (Q6), kept apart from the rehearsals; redact at capture | an address or token in a tracked file; a send to a target not in Q6 |
| Mail's Automation prompt blocks the first send, or names the wrong process under launchd | medium | story 03 proves it on his desk first and names the limit | the send hangs at the prompt with no face state |
| Scope creep into Slack, other documents, or moving every outbound path | high | Out with homes; only the nudge moves | a story edits `slack_export.py`, `cadence_telegram.py` or the actuators |

## Decisions for the owner

- **Q1 — "How should an email leave?"** **Recommended: (b), on three conditions:** your work account is already set up in Mail; your company allows that use; and Automation works when the hub runs the way it runs on your desk (story 03 checks this first, before any build). If a condition fails: (a) if your provider allows SMTP app passwords, else email waits (BACKLOG). (Grounding section 4 has the table.)
  - (a) SMTP, with an app password kept in the macOS keychain. *Server proof (the `250` answer and the Message-ID); stops before the message body unless every recipient is accepted; HoldSpeak holds a secret; many company mail systems turn off app passwords.*
  - (b) Mail.app sends it (a fixed `osascript` script). *No secret held; sends from an account in Mail; the outcome is HANDED TO MAIL — HoldSpeak does not see the server, and Mail may hold it in its Outbox and try again by itself; macOS asks once for permission; Mac only.*
  - (c) The Gmail API with OAuth. *Strong proof; a Google Cloud project, a consent flow and token refresh (fails Tenet 1); Gmail only.*
  - (d) Open a draft in Mail; he presses Send there. *Smallest; the manual channel with a head start, so not "Email" as he picked it.*
- **Q2 — "On GitHub, where does an update go?"** **Recommended: (a); the gist is parked (BACKLOG).**
  - (a) A comment on an issue or a pull request he saves as a destination (a tracking issue per project). *One command family, the nudge's precedent, proof is the comment URL.*
  - (b) As (a), and also a secret gist (a new link per send). *One more manifest; a link he pastes elsewhere.*
- **Q3 — "On Confluence, what do we make?"** `acli` cannot make or change a page today (F8). **Recommended: (a).**
  - (a) A blog post in the space he saves (one per send; the genre fits a status update).
  - (b) No Confluence in this phase; Jira only; Confluence waits for `acli` page commands (BACKLOG).
- **Q4 — "When the same update goes to the same folder again?"** **Recommended: (a).**
  - (a) A new file each time, named by date, project, revision and a short send id, created only if the name is free (exclusive create), never over an old one.
  - (b) One file per project, replaced each time (a "latest" file others read). *Loses the old file; overwriting is irreversible.*
- **Q5 — "Who may prepare a send for you?"** **Recommended: (a).**
  - (a) The steward, and any agent you connected; only you send. *The press is the gate; the receipt names who prepared. It carries out your "You, every time"; no grant screen without a need.*
  - (b) Only an agent with the project grant (Phase 9) and the steward. *One more grant row to set up before an agent helps.*
- **Q6 — "Where may the test sends go?"** A real send needs your login. **Recommended: (a).**
  - (a) Targets you name once and authorize: a private scratch repository and issue, one scratch Jira work item, your personal Confluence space, your own email address. The rehearsals stay on an isolated hub. The real sends are a separate leg on your own session, because `gh` and `acli` keep their logins in the macOS keychain and Mail uses your Mail (a scratch HOME isolates none of them; F15).
  - (b) No real sends before the close; the proof is your first real Send, recorded after the phase.

## Decisions made (this phase)

- 2026-09-28 — the owner: "explore #2"; Payload "Any document; updates first"; Channels "File system", "gh + acli", "Email" (Slack not picked); Who sends "You, every time"; Destinations "Saved destinations" (AskUserQuestion).
- 2026-09-28 — round two: Codex Astra r1 DO-NOT-RATIFY paid; `design/send-lifecycle.md` (the records, prepare and press, the transport bytes, the dispatch boundary and recovery, destinations, seams) — Fedaykin docs lane for Muad'Dib; Codex Astra r2 owed.
- 2026-09-28 — DRAFTED: six stories; the Send on the existing write seam, no new framework; the product word "Send" and the code word "channel" (F12); Slack, agent sends, other documents and Confluence pages Out — Fedaykin docs lane for Muad'Dib.

## Decisions deferred

- Q1–Q6: the owner, at ratification.
- The operation names (`channel.*` or another family): story 01's first commit, checked by Codex Astra. (The prepared-send design is settled: a `channel_sends` row, not a held kernel operation — `design/send-lifecycle.md` section 2.)
- The pinned error lists, the Atlassian JSON shapes and the size limits' exact numbers: story 02, from real sends. The Mail `false` case: story 03, probed offline.
- Whether the record stays on `project_update_deliveries` when the second document kind arrives, or moves to one table keyed by document: when that document is chartered (the owner's "updates first").
- The Send well's words and seat, and where the destinations setup lives: the two canvases, ratified by the owner before build.
- Whether an `acli` send switches his account back afterwards: story 02, from where `acli` keeps its login (unknown).
