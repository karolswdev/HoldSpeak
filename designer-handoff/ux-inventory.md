# UX Inventory

## Routes

| Route | Purpose | Main User |
|---|---|---|
| `/` | Runtime dashboard for active/idle meeting state | Meeting user |
| `/activity` | Local activity ledger, candidates, project rules, connectors | Power user / operator |
| `/history` | Saved meetings, detail review, exports | Meeting reviewer |
| `/settings` | Settings surface served by history UI today | Operator |
| `/dictation` | Dictation blocks, readiness, KB, runtime, dry-run | Power user / admin |
| `/docs/dictation-runtime` | Runtime setup guidance | Installer / troubleshooter |

## Important UI Surfaces

### Runtime Dashboard

- Meeting start/stop.
- Runtime status.
- Transcript, bookmarks, action items, intel/artifacts where available.
- WebSocket-updated live state.

### Activity Dashboard

- Ingestion status and retention.
- Browser source availability.
- Domain exclusions.
- Project mapping rules with preview/apply.
- Meeting candidates with preview/save/filter/start.
- GitHub/Jira connector APIs exist; UI controls are next.
- Recent activity records.

### History

- Meeting list.
- Meeting detail and export paths.
- Action item and artifact review surfaces.
- Speaker and project context where available.

### Dictation

- Readiness checks.
- Block list and editor.
- Project KB editor.
- Runtime model settings.
- Dry-run trace and final transcript preview.

## Current Gaps For Designer Review

- Connector controls exist at API level but need first-class `/activity` UI.
- Navigation style is inconsistent across activity, history, and dictation.
- Empty states improved on `/activity`, but other surfaces need the same pass.
- The visual hierarchy of dense panels could be tightened.
- Command previews need a standardized monospaced, copyable, inspectable style.
- Destructive deletion flows need consistent confirmation language.

## Suggested Design Deliverables

- Route-level information architecture map.
- Component inventory and token proposal.
- Desktop and narrow viewport layout proposals for `/activity`.
- Connector control pattern for `gh`, `jira`, and future connectors.
- Empty/error/loading state library.
- Visual treatment for local-only privacy status.
- Prioritized UI polish backlog.
