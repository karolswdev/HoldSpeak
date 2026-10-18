# Send: the code map (2026-10-17)

Read from the desk head `217001b2e` (`wt-daily-delight-delivery-20261017`).
Paths are from the repository root. This is the input for `DESIGN.md`
sections 3 and 4.

## 1. What a send is, in data

One table, `channel_sends`, one row per send. A row is born in one of two
ways and ends in one of four states:

```
prepare (anyone)          inline (his press, from the well)
     │                          │
  prepared ──Send (owner)──► dispatching ──► sent | failed | unknown
     │                                         (proof)  (reason) (reason)
  Discard (owner) ──► discarded
```

- **Prepared** is the only waiting state. It holds the frozen bytes, their
  digest, the destination and `prepared_by {kind, identity}`
  (`web/src/features/channels/channels.ts:57-86`).
- **Dispatching** is set inside the kernel boundary. A taken-over or lost
  caller resolves through the channel's `recover`
  (`holdspeak/services/channel_service.py:494`, `:511-515`).
- **Sent** carries proof: a folder's path, sha256 and size read back; a
  GitHub comment URL; a Jira or Confluence id; an email provider's message
  id ("accepted", never "delivered"); Slack "ok"
  (`holdspeak/channel_operations.py:251-297`).
- The answer to "did it arrive" is this proof. There is no read-back from
  GitHub, Jira, Slack or the mailbox after the send.

A **destination** is a saved place (`channel_destinations`): name, channel,
account identity (never a key), target, synced flag. The built-in
"HoldSpeak folder" (`~/Documents/HoldSpeak/Sent`) is always there. Editing
parks the old row and makes a new one.

A **document** is what a send carries, named `<kind>:<id>`. Ten kinds are
registered (`holdspeak/services/document_sources.py:600-611`):
`project_update`, `monday_brief`, `desk_decision`, `meeting_decision`,
`decision_record`, `meeting_summary`, `meeting_digest`, `meeting_followup`,
`artifact`, `note`. Each renders Markdown; each channel turns that Markdown
into its own bytes (`holdspeak/services/channel_contract.py`).

## 2. The operations (one source for HTTP, MCP and the rig)

`holdspeak/channel_operations.py` declares 11 operations; 9 are MCP tools
(`holdspeak/mcp/families/channel.py`). The two key savers are HTTP only, so a
secret is never a tool argument.

| Operation | Who | Note |
|---|---|---|
| `channel.destinations`, `.preview`, `.sends`, `.check_destination` | anyone with WORK | reads |
| `channel.prepare` | anyone with WORK (agents, threads, steward) | makes a `prepared` row |
| `channel.save_destination`, `.remove_destination` | owner (AUTHORITY) | the egress allow-list |
| `channel.send`, `.discard` | owner only (`owner_press=True`, `:291`) | an agent is refused `owner_principal_required` (observed) |
| `channel.save_email_key`, `.save_slack_webhook` | owner, HTTP only | key store; `channel_key_file.py` in the rig |

Authority classes: `holdspeak/mcp/tool_authority.py:269-277`. The Conductor
launch counts `channel.prepare` as a create of a `send`
(`holdspeak/services/conductor_launch.py:270`). The Thread palette carries
`channel.destinations` and `channel.prepare` (`holdspeak/services/thread_tools.py:370-375`).

## 3. Who prepares today

| Producer | Prepares? | Where |
|---|---|---|
| An agent over MCP (Claude Code, Codex, pi) | yes | the channel family |
| A Thread's tool calls | yes | `thread_tools.py:281`, `:375` |
| The project steward | yes: the latest published update to the destinations its policy names | `holdspeak/services/project_steward_service.py:1870-1908` |
| The steward's reviewer nudge | sends on the GitHub channel's path, with the Send's outcome rules | `project_steward_service.py:2054-2060` |
| Automations (Workbench runs) | **no**: the runner never calls the channel | `holdspeak/services/workbench_runner.py` (no `channel` reference) |
| Needs you, Today, the Brief | no | – |

## 4. Where a prepared send or a receipt is shown

| Face | Shows prepared? | Shows proof? |
|---|---|---|
| The document's own Send well | yes, `◆ PREPARED · BY <WHO>` rows first (`SendWell.tsx:732-820`) | yes, per destination row and in `SENDS N` |
| The update list in the Room | `PREPARED ×K`, `RESULT UNKNOWN ×M`, `DELIVERY ×N` chips (`features/channels/SendWell.tsx:108-125`) | count only |
| The Brief head | `PREPARED` chip (`desk/documentSends.tsx:69-75`) | no |
| A Room decision row | `PREPARED` chip (`documentSends.tsx:100-102`) | no |
| Needs you, Today, the bell, the desk | **no** (Needs you's sources are project, watch, meeting, commitment, coder: `holdspeak/services/needs_you_aggregate.py:75`) | no |
| The Dock | reads every send on each refresh (`desk/components/window/Dock.tsx:157-172`), but its SENT badge was cut; nothing renders it | no |

## 5. The face: one species, many hosts

The species is sound and shared. The hosts around it differ.

| File | Lines | What it is |
|---|---|---|
| `web/src/desk/surface/send/SendWell.tsx` | 944 | **The species**: destination rows, frozen preview, Send / Send again / Retry, receipts, prepared rows, `SENDS` history, read store, held-command replay |
| `web/src/desk/surface/send/pendingCommand.ts` | ~40 | A held command in `localStorage` (`hs.send.pending.v1`), so a lost answer replays the same bytes after reload |
| `web/src/desk/surface/send/send-well.css` | 174 | its material |
| `web/src/meetings/MeetingSendWell.tsx` | 101 | Host: a meeting, with the `Summary · Digest · Follow-up` gadget; three reads held at once |
| `web/src/desk/documentSends.tsx` | 102 | Hosts: brief, desk decision, decision record (folded), artifact, note |
| `web/src/features/channels/SendWell.tsx` | 135 | Host: the project update, **plus a second history**, `DELIVERY`, with a manual `To` field and `Mark delivered` |
| `web/src/desk/windowSend.tsx` | 409 | `Send to ▸` in the Object menu and the window's context menu; picks a destination through `pickDestination` and opens the well |
| `web/src/desk/floorSendBinding.ts` | 139 | The pure binding from a desk object to its document (used by `windowSend`) |
| `web/src/pages/cores/connections/Destinations.tsx` | 627 | Settings ▸ Accounts ▸ Destinations: list, details, the add/edit form |
| `web/src/features/channels/channels.ts` | ~400 | The words, the wire client, refusal and reason words |

So there is **one Send well in code**, composed by six hosts. What looks
duplicated to him is:

1. **Two "Send" buttons.** Each host's footer "Send" only unfolds the well;
   the well's own "Send" is the egress press.
2. **Two histories on an update**: the species' `SENDS` and the update's
   `DELIVERY` with a manual "Mark delivered".
3. **Two account checks**: Accounts (`gh auth status`,
   `connections_service.py:302`) versus the send path (`gh api user`,
   `channel_cli.py:260-262`); the form gates on the first
   (`Destinations.tsx:270-276`).
4. **Two homes for "add a destination"**: the well's `Add destination`
   opens the Settings window (`SendWell.tsx:604-606`).
5. **Older outbound paths** beside the channel: the legacy actuator
   proposals (`holdspeak/services/actuator_service.py:105-108`, Settings ▸
   Meetings ▸ RAW ▸ `Allow actuators`, `SettingsCore.tsx:2386-2388`), the
   aftercare `file-issue` route (`holdspeak/web/routes/meetings/aftercare.py:56`)
   and the parked Slack export, which answers `slack_moved_to_channel`
   (`aftercare.py:47-54`).

## 6. Dead, wrong or missing (with the shot that shows it)

| # | What | Evidence | Shot |
|---|---|---|---|
| 1 | Prepared sends reach no list he reads | §4 | `09-needs-you-no-prepared-*.png` |
| 2 | Automations cannot prepare a send | §3 | – |
| 3 | The account chip ignores a later successful send | `SendWell.tsx:209-221` | `08-github-sent-1440.png` |
| 4 | GitHub destination cannot be saved from the face when Accounts says Unreachable | `Destinations.tsx:270-276` | `05-new-dest-github-1440.png` |
| 5 | A published update with no accepted claim cannot be sent, and the refusal has no verb | `channel_contract.py:411-470` | `15-update-email-refused-1440.png` |
| 6 | The meeting Summary form omits decisions and owners | `document_sources.py:466-497` | `07-folder-preview-1440.png` |
| 7 | The Digest and Follow-up forms list unconfirmed action items as "Still open" | `holdspeak/meeting_aftercare.py:141`, `:222` (pending items, any review state) | `08-github-preview-1440.png` |
| 8 | An artifact's email subject is its title, which for an Automation result is the item's instruction | `document_sources.py:526-571` | `17-artifact-email-preview-*.png` |
| 9 | Email and Jira previews show raw Markdown; whether the receiver sees it raw is unknown | the preview shows `body_md` | `08-jira-preview-1440.png`, `08-email-preview-1440.png` |
| 10 | Jira proof parse is "PROVISIONAL until a real send" | `channel_cli.py:107-108` | – |
| 11 | File names take the UTC date | the saved name `2026-10-18-…` at 20:29 local on 17 Oct | `07-folder-sent-1440.png` |
| 12 | `Send to ▸ <destination>` opened the last-used destination | not traced | `18-send-to-picked-1440.png` |
| 13 | A note has no Send; only the Thought window has one | `documentSends.tsx:89-97` (the only note seat is the Thought window) | `10-note-open-1440.png` |
| 14 | The Dock reads all sends and renders nothing | `Dock.tsx:157-172`, `dockState.ts:122` | – |
| 15 | A send with no answer stays `SENDING`; nothing tells him what to do | – | `20-after-reload-jira-sending-*.png` |

## 7. Constraints a design must keep

- **Egress is his press** (UX-CANON A.9; owner rulings on egress, authority
  and config). `channel.send` stays owner-only. Every face that sends shows
  the host chip on the row that leaves the machine.
- **Frozen preview**: what he saw is what goes. The digest check
  (`preview_changed`, `payload_changed`) stays.
- **Honest unknown**: a send with no clear answer is `unknown`, never
  retried by the machine. Retry replays the same command id.
- **No key on the wire**: keys go through the two HTTP-only savers.
- **Never delete**: parked destinations stay; `channel_sends` keeps every
  row.
- **One well, many hosts**: the species is the place to change behavior;
  hosts only seat it.
