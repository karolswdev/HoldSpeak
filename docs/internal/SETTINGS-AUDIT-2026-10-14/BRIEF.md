# Settings audit and repair — settled brief

Base eef72f987 (#1203). Owner rejects populated Meetings preferences and
requests ALL Settings surfaces audited and improved. One coherent release.
Tuesday: owner can find/change an ordinary preference, keep names and drafts,
understand the chosen behavior, and recover from failure without internal lore.
Tenets 1–7: existing component framework, simple words, actual owner jobs,
no invented settings system, no defensive framework or capability expansion.

## Evidence and scope

Source audit found a full-document write round trip choosing the legacy
calendar.subscription alias over calendar.sources: names/enabled/multiple
sources are lost. PUT responses reintroduce retired inference selectors; GET
and PUT use different authority gates. Rhythm/Telegram/mesh edits are ignored.
Main face has duplicate summary headings, technical hardware fields as first
paint, guessed calendar type/raw URL identity, stale auto-record, hidden save
receipt under Accounts and unbounded errors in the footer verbs slot.
Satellite audit found swallowed Accounts reads/checks/add refusal and lost Add
drafts; unread owner identity can overwrite aliases; TTS/Guide false readiness;
unsupported live Wallpaper switches; destination missing-account dead ends.
Source findings are not a claim of owner-state reproduction.

## Settled design

Keep native Settings window, wings and module registry. Every visible action
is the library Button. One module title, human labels, compact existing
GadgetGroups/rows; cap the preference form's reading width within a zoomed
window, container-query stack at 393. No modal, custom widget framework, extra
navigation system, decorative cards or explanatory paragraphs. Use existing
SurfaceState, FoldGadget, SurfaceWell, Receipt and SurfaceFooter slots.

Meetings: one Summary timing control (Manual / After room meetings / After
every meeting), current engine fact with an existing Engines destination.
No duplicate display banner. Separate Recording, Calendar, Export groups;
auto-record reads the edited authoritative setting immediately. Hardware default
facts stay clear; custom device-name overrides live in Audio devices details
(no fake device picker or new audio API). Export format appears when relevant.
Calendar rows lead with real label and canonical Mac calendar / Calendar feed /
Snapshot type. Never expose eventkit UUID as name. Missing native label says
Mac calendar and can be renamed; no invented original name. Edit exposes Name;
feed-only URL editing, native URL immutable. Add calendar leads to the existing
Accounts connection flow; retain Add feed and Import screenshot as secondary
existing methods. Keep vision destination badge adjacent to import action.
Park Remove behind explicit existing confirmation; preserve source identity,
all sources and disabled state. Technical knobs under Advanced, not RAW.

Writes carry only actual changed paths plus revision. Arrays remain atomic;
retain existing queue, conflict/refetch, pending overlay, leave flush and retry
semantics. All successful responses use the same migrated projection as GET.
Explicit retired selector mutations still refuse. Canonical calendar.sources
wins when an old alias is echoed; genuine subscription-only callers remain
supported. Persist existing cadence/cadence_telegram/mesh dataclasses honestly.

Save progress/result uses SurfaceFooter.receipt, Back uses verbs. A failed save
has readable in-body error and Retry with preserved edited values; footer only
a short named outcome. Accounts secret saves must remain observable. Refresh
hub/calendar facts only after accepted writes, no guessed delay timer.

Accounts retain Site/Email/destination drafts until confirmed success. Failed
read/check is a failed read/check, not empty setup. Recheck has visible busy and
named outcome. Populated accounts still offer Add. Long names/actions wrap at
393. Missing destination account offers a real existing Accounts action while
keeping draft. Owner identity cannot edit/write unread aliases; read failure
gets Retry. Agent access names Read/Read and write plainly with one receipt.
Guide readiness requires successful known checks; unknown/error stays unknown.
TTS read failure gets Retry; browser voice support is observed, not asserted.
Wallpaper applies already settled DESIGN-words direction: no live no-op
animation/sound controls or descriptions. Retain current picker/preview.
Engines #1203 behavior stays; audit regression/hosting rather than new board.

## Disjoint lanes

- backend: holdspeak/services/settings_service.py; onboarding_service.py only
  for explicit native-calendar reselection repairing blank label; tests in
  integration/test_calendar_settings.py, integration/test_desk_settings.py;
  unit/test_onboarding_backends.py only calendar cases if needed.
- main face: SettingsCore.tsx, settingsPrefs.tsx, settings.css,
  settingsSurfaceRepair.css, core-types.ts if needed, desk settings.app.test.tsx;
  main face/native direction canvas and audit-main.md. No satellite edits.
- satellites: connections/ConnectionsPane.tsx, connections/api.ts,
  connections/connections.css, connections/Destinations.tsx;
  settingsPeople.tsx, settingsTts.tsx, settingsWallpaper.tsx,
  RuntimeDocsCore.tsx; desk/firstrun/ownerName.ts; their existing focused tests
  except desk/settings.app.test.tsx (main lane). Satellite canvas and audit.
- root: brief, coverage/records/metadata, scratch rigs, production capture,
  combined quick check, commit/PR/merge/deploy. Root alone stages/commits.

Anchors in audit messages describe base eef72f987; verify before edits. Shared
worktree /Users/karol/dev/tools/wt-settings-audit-20261014. Never edit owner main
checkout; no git stash/reset/restore/clean/switch/checkout-- or add-A. Warm
web/node_modules symlink is read-only; never install or stage it. Each face gets
native direction canvas before product edits; root settles direction.

Focused tests only named above, through .tmp/settings-audit/locked.py with
isolated HOME and shared test lock; pytest -n8 --dist worksteal, Vitest4
--maxWorkers=2. No broad/full/metal/owner-state/network/mic/keychain runs.
Collect tests first; capture red regressions, then run focused green once and
one corrective rerun maximum before report. Root owns quick_check.sh at final
freeze. Report exact tails and shot paths, no unrun claims. Hold for SHIP;
workers never stage/commit. No implementation edits across lane boundaries.
