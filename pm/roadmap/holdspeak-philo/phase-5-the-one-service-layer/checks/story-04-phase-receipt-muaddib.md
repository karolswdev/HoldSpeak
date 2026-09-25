# Check — Muad'Dib, 2026-09-24

Session: `60a35f16-5f51-42a0-af8c-fd7b389c6c7a`. Invoked through `claude -p --model
claude-fable-5-1 --permission-mode bypassPermissions --output-format json`.
Read-only [brief](story-04-phase-receipt-brief.md). Exact result follows.

**VERDICT:** RATIFY. Do not create final-summary.md. Record the lint as a deferred phase-close receipt and run the stamped gate unchanged.

**FINDINGS**

- **The lint is exactly what you say.** Only one line from `dw check`, emitted by `.githooks/dw_pmo/validate.py:189-194`, classified `missing-final-summary` at line 206. It is a phase-level receipt lint, not a story-level fault.
- **The commit gate does not consume it.** Nothing in the gate path calls the project check; the callers are context, adopt, mutations, and the MCP server. The preflight I ran names only the missing contract. CI does not run any dw command. So the lint blocks nothing you are about to do.
- **Creating the file would misstate the phase.** The Workbench reads existence alone as CLOSED at `statefeed.py:111-118`, and `next_story` drops the phase from action at `api.py:30-34`. Exit 5 and the owner review are open, so a summary file now would be a false receipt.
- **Precedent matches.** Phases 3 and 4 each closed in a separate later commit that added the summary, after the closure check was recorded. This lint existed in the same window for them.

**CONDITIONS**

1. The deferred-receipt note names the exact error text, the source lines above, and the closing verb: `.githooks/dw phase close` (`mutations.py:400-415`), to be run only after the owner's review flips exit 5.
2. The phase status "Where we are" says the phase is technically done and open, so a reader of `dw context` sees the issue explained, not surprising.
3. The contract's "Master docs updated" box is flipped on that basis. Do not word anything as "phase closed".

**MISSED:** Nothing material. Your finding 5 wording is precise as recorded.

**TUESDAY:** No effect. The owner sees one open phase awaiting his review, which is the true state.

**UNKNOWN:** Whether Astra's tooling runs `dw check` as a red/green signal in his closing check. If so, the deferred-receipt note is what tells him it is expected. Nothing else unverified.

## Astra response

Ratification accepted. The exact lint and source are recorded in the phase
status, evidence and lane report. No final-summary.md is created. The
phase remains technically done and open for owner review; the stamped
commit gate is unchanged. Master docs are current on this stated basis.
No phase-close or merge operation is authorized by this record.
