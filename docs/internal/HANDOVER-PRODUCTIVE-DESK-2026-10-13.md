# Productive desk — 2026-10-13

PR: [#1197](https://github.com/karolswdev/HoldSpeak/pull/1197).
Branch: `feat/desk-productivity-overhaul`. Base: `1e3bce495` (design index,
PR #1196). One integrated PR, at the owner's request. Builders: Luna workers;
integration and verification: Sol. Merge follows `CLAUDE.md`'s October 12
fast cycle; this is not a Muad'Dib review or owner usability acceptance.

## Design and owner decision

Read all four October 13 designs under `philo/phase-17`: verbs, windows,
words, attention; also DESIGNS and RECON. Scope and seams are in
[the implementation brief](philo/phase-17/IMPLEMENTATION-PRODUCTIVITY.md).
The owner's answer was **Inside Meetings, with Back**. It supersedes the
October 10 separate meeting window interpretation.

## Jobs changed

- A meeting opens inside Meetings. Back retains the selected list row;
  reload retains the open record. Historical meeting windows migrate;
  ordinary object windows retain their identity and saved geometry.
- Meeting Outcomes has one review path. Confirmed actions enter accepted
  work; Done survives reload, leaves open People prep, and can be reopened.
  Names and aliases resolve through the existing ambiguity-aware People
  service. A locked encrypted store does not fall back to plaintext matching.
- A saved Note can create a Task, join an existing Project, or open Ask with
  its context. The task retains its note source. Save precedes each action;
  subsequent editor operations use the latest workspace cursor. Search lists
  objects first and renders human text instead of serialized note JSON.
- An effective chosen assignment governs Ask and Note before the legacy
  migration marker exists. Invocation and subject selectors reach admission.
  An incompatible choice remains visible for repair. Speech retains the
  coupled session admission gate while freezing selected capability routes.
- Engine and run lines give one route/status and plain refusal words. Ask
  freezes terminal elapsed time and prints the actual result route. Room's
  Draft press creates the draft; a failed manual model draft offers an
  explicit plain retry. Automatic callers retain their existing fallback.
- Engines and Accounts open in Settings. Closing Settings persists across
  reload. Phone Go lists the apps, Back returns through scoped views, four
  dock doors remain, and compact footers put secondary verbs under More.
  New window sizes fit the job; saved rectangles remain authoritative.
- One attention list and bell replace the duplicate shade and ambient card.
  The old faces and tests are parked. Default local egress badges are quiet;
  outgoing boundaries retain their badges. Fresh desks get Start here and
  the Weekly update prompt. Historical edited or removed seed notes stay
  under owner control. Note titles, reads, and save receipts use plain words.

## Verification

Integrated quick check: **GREEN** (`.tmp/productivity/quick-r3.log`):
106 sweep checks passed, 3 existing known reds xfailed, 15 canon guards
passed. The final related run passed
3,699 web tests and 4,709 affected Python tests (3 model-dependent skips;
1 background-thread warning). The previous run’s two Python failures and
one Brief stillness failure were retained and corrected. The Brief sweep
now waits for the actual refresh completion before measuring stillness.
API surface manifest: 6 passed (`.tmp/productivity/api-final.log`).
Type check: passed (`.tmp/productivity/typecheck-r2.log`). Architecture data
validation and capability generation: passed. Speech regression budget:
95 passed (`speech-collect.log`, `speech-run.log`). Meeting regression budget:
123 passed (`meeting-regression-collect.log`, `meeting-regression-run.log`).
All test and graph runs used the machine lock and isolated HOME.
No real model, microphone, owner DB, Keychain, or delivery was used by tests.
The full suite remains the postmerge watcher's job, per the fast cycle.

Real graph walks, each at 1440 and 393, are declared in
[atlas-productivity.json](philo/graph/atlas-productivity.json):

| Case | Observed result | Retained run directories under `.tmp/productivity/walks/` |
|---|---|---|
| `case.productivity.engines.settings` | `/models` opens Settings Engines, no Concierge host | `settings-1440-final`, `settings-393` |
| `case.productivity.settings.closed` | closed Settings remains absent after reload | `settings-closed-1440-r2`, `settings-closed-393` |
| `case.productivity.note.task` | UI Add writes the task and its note source to the real isolated hub | `note-task-1440-final`, `note-task-393-final` |
| `case.productivity.meeting.back` | actual text import → record → reload → Back to selected list; no separate meeting host | `meeting-back-1440`, `meeting-back-393` |

Each directory contains the observation, before/after shots and provenance.
Protocol readings are retained in the observation; the rig removes its
temporary DB on cleanup. These are production UI and hub observations with
synthetic input, not observations of the owner's desk. Failed intermediate
runs remain in scratch. Generated API/operation and capability docs were
refreshed; obsolete historical test citations were marked as parked or
moved to limitations, not promoted to current proof.

## Open work and unknowns

- Owner judgment on his actual desk and real LAN engine latency remain
  unobserved. A bounded read-only metadata diagnostic found no legacy
  Thoughts migration marker; it did not establish the cause of the reported
  122-second Ask delay. The assignment repair is covered by controlled tests.
- Automatic task extraction on Finish (attention S6), the remaining full
  words sweep, and retiring the legacy branch after a week of real use remain
  later work. This PR does not claim every line of all four designs is done.
- The existing three sweep known reds remain individually recorded in the
  sweep. No new baseline waivers were added. The atlas census still contains
  historical unindexed operations; this is not a whole-atlas coverage claim.
- An isolated test background thread outlived its DB and raised
  `no such table: deployment_revisions`; the quick check retained the warning.
  Owner runtime impact is unverified; follow up in the main tape.
- Postmerge Astra review and the full main tape remain due. Security or data
  loss findings follow the existing revert rule; ordinary findings fix forward.
