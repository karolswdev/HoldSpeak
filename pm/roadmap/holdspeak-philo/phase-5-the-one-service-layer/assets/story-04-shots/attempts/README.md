# Stopped rehearsal attempts

These real-engine attempts are retained as failures of the closing rig, not as completed rehearsals. Their original client events, full server MCP transcripts, effective configuration, DB/lock proof, hub logs, and available shots are unchanged.

| Attempt | Result | Exact stop |
| --- | --- | --- |
| `20260924T234600Z-his-words-real` | Codex imported and read the real recording. The driver stopped before opening the Desk. | `RuntimeError: MCP exchange reconciliation for 'meeting.import' found no unused matching /api/mcp row` |
| `20260924T235148Z-his-words-real` | Codex imported, requested a real summary, and read the ready summary. Two before shots were taken. The driver stopped before its after shots. | `Locator.inner_text: Error: strict mode violation: locator("[data-testid=summary-record-attempts]") resolved to 2 elements` |

The first stop exposed a representation mismatch: Codex emits `structured_content: null` and omits `isError: false`; the server does the inverse. The explicit result projection now pairs all three original calls while retaining content and error differences. This is a recorder comparison correction, not a product change.

The second stop exposed a browser recipe error. Clicking the Arrival row at 1440 opened a Meetings window over the Arrival and duplicated the receipt selector. The next recipe leaves Arrival open and scopes its observations to that face. The 393 before shot was already on Arrival. No completed delivery claim rests on this stopped attempt.

`run-2-output.txt` retains the second command output. The first failure above was returned by the live command; the initial driver did not yet persist a failure-status file. It is recorded here by Astra, not presented as a machine capture.

| Later attempt | Result | Exact stop |
| --- | --- | --- |
| `20260925T000121Z-his-words-real` | Summary delivered without refresh at both widths; decision and edited Thought saved and read back. Thought screenshot at 1440 retained. | `Locator.inner_text: Timeout 10ms exceeded` at the 393 fresh read. Five browser text-read timeouts used milliseconds where ten seconds was intended; corrected to 10000. |
| `20260925T000518Z-his-words-real` | Full Codex sequence completed. It chose an accepted decision and also created a durable decision record. The brief was saved and read back. | The strict decision-source fence failed: an accepted desk decision is excluded from the collector's proposed-decision review queue. Its extra record also lies outside the pilot registry. This run is not a successful pilot verdict. |

The final ordinary-language request explicitly puts the decision on the owner's list to review tomorrow. This preserves the requested job of a decision visible in tomorrow's brief without spelling a status field or operation name. The collector is unchanged. The previous prompts and their outcomes remain retained.

The supplemental `receipt-red/` read restarted run 4's same isolated hub and read its existing Codex-produced brief; it did not generate another brief. Both widths showed the saved rows and no `Brief ready` receipt. The real receipt defect was verified before the product edit.

The initial `db-proof.sqlite` files were plain copies of a live WAL database and can omit committed WAL rows. They are retained as incomplete snapshots, not used as domain proof. `db-complete.sqlite` was made later from each original isolated HOME with SQLite's read-only backup API; run 4's copy follows the supplemental receipt read. The final driver uses that API directly. The original registry readbacks and complete MCP transcripts remain the evidence of each original turn.
