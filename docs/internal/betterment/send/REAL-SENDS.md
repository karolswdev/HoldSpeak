# First real Sends

Observed 2026-10-20. S2 remains open: no far-side arrival is recorded yet.
The owner chose defaults. Preparation is complete for the two available
destinations below. The owner makes each Send press; a prepared row is
not proof of delivery.

| Channel | Default target | Prepared send | State |
|---|---|---|---|
| Folder | `~/Documents/HoldSpeak/Sent` (iCloud; cloud egress) | `chs_ce55ec632cd3aabde9e48cbb` | Prepared; owner press and arrival pending |
| GitHub | [HoldSpeak Send test issue #699](https://github.com/karolswdev/HoldSpeak/issues/699) | `chs_7a3505d0b051bb36782c2fe0` | Prepared; owner press and comment URL pending |
| Jira | No saved target; the read-only HoldSpeak Send/scratch lookup returned no item | — | Test item needed |
| Email | No saved email-provider destination | — | Verified sender, saved provider key and owner's recipient needed |
| Slack | No saved private-channel webhook destination | — | Private destination needed |

Both prepared rows use `meeting_summary:c745e8b9`, 287 bytes, with digest
`dff002eabaf687c9da39636b5d14da5b4bd02f9ca08d9145695306b13802282b`.
Their durable prepare operations are
`op_36ca2f27822a43e4ae09a650b7557235` (folder) and
`op_9d092d27eda44fe0ac83f9b5bb935c3a` (GitHub). GET readback retained
`prepared` and the exact digest. No Send or Discard was invoked.

For each actual Send, record the returned operation and receipt, the
far-side text and link or path, and one observed far-side screenshot.
Only those real, redacted provider answers become the S2 replay fixtures.
The private-Hub rehearsal receipts and files used for S3–S7 do not close S2.
