# Functional Handoff

## Global Navigation Model

HoldSpeak currently exposes several local web routes:

- `/` - live runtime dashboard for meeting recording and meeting-state review.
- `/activity` - local activity ledger, enrichment connectors, project rules,
  and meeting candidates.
- `/history` - meeting history, saved meeting detail, exports, and review data.
  The Settings tab is served as a tab inside `/history` (no separate route).
- `/dictation` - dictation blocks, runtime readiness, project KB, runtime
  settings, and dry-run preview.
- `/docs/dictation-runtime` - local setup guidance for dictation runtime.

Phase 10 unified the navigation: every route renders inside a single
`AppLayout` shell with one `TopNav`, so layout, density, and identity
read identically across surfaces. The app is a tool, so the first
screen should remain functional. Avoid turning these pages into
landing pages.

## Primary Workflows

### Start And Review Meeting Work

Users can start a meeting from the runtime dashboard or from a saved meeting
candidate on `/activity`. When started from a candidate, the candidate changes
to `started`, the meeting title is applied where supported, and the candidate
stores the started meeting ID.

Design needs:

- Clear distinction between idle, active, stopping, and stopped states.
- Primary start/stop actions should be prominent and not compete with secondary
  review/export actions.
- Meeting context such as title, tags, candidate source, and local status should
  be legible at a glance.

### Mine Local Activity Into Work Context

`/activity` imports local browser-history metadata and maps records to work
entities such as GitHub PRs/issues, Jira tickets, docs, domains, and calendar
meeting candidates.

Design needs:

- Keep local-only/privacy copy close to import, connector, and deletion
  controls.
- Activity records are scan-heavy; dense lists are appropriate.
- Project rules need clear preview-before-apply affordances.
- Meeting candidates need a clear preview vs saved distinction.

### Enrich Visited Work Items

GitHub and Jira CLI enrichment are optional. They are disabled by default.
Preview shows exact read-only commands before any output is written. Run actions
require explicit enablement and write local annotations only.

Design needs:

- Connector status should show enabled/disabled, CLI availability, last run, and
  last error.
- Preview and run should be visually separate.
- Deletion controls should target connector output without implying source data
  deletion.

### Configure Dictation Pipeline

`/dictation` lets users configure blocks, project KB, runtime model settings,
readiness checks, and dry-run behavior.

Design needs:

- This is a technical configuration surface; density is acceptable.
- Readiness and dry-run should reduce ambiguity about whether live dictation
  will work.
- Errors should be attached to the field or panel that generated them.

## Critical States

- Empty: no records, no candidates, no rules, no connectors enabled.
- Previewed: command/candidate/rule preview exists but has not written data.
- Enabled: connector is allowed to run when user clicks run.
- Running: buttons should be disabled and status should remain visible.
- Failed: error should preserve the command/context that failed.
- Deleted: output deletion should clearly say what was removed.

## Non-Goals For Design

- No cloud account onboarding.
- No automatic recording or automatic meeting join.
- No hidden connector execution.
- No decorative brand/marketing hero page.
- No visual treatment that implies remote sync by default.
