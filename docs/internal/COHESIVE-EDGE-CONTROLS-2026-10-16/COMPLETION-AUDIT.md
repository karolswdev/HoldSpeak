# Completion coverage — cohesive HoldSpeak

DRAFT — UNCHECKED, awaiting Muad'Dib. Bounded source/evidence audit,
2026-10-16; no release verdict. This audit read the completed records and
observations named below, current sweep/test source, and one actual phone
home screenshot. No tests, browser, scanner, provider or owner-state action
was run. Only this document was written. The unfinished caption amendments
are excluded from implementation review. Root owns final freeze, shots,
merge, deployment and the goal status.

The major Desk application families have broad visual coverage and existing
functional tests. The repaired jobs also have selected actual task evidence.
The evidence does **not** yet support “every interface is finished, delivered
and accepted.” The clearest remaining product scope is the entry experience:
phone Desk home, Get ready through `/welcome`, and `/presence`. The final
release and the owner's judgment have separate proof requirements below.

## What the goal requires

The owner's goal is “all interfaces cohesive, pleasant and functionally
tested” (`../COHESIVE-WORKFLOWS-2026-10-15/README.md:3`). The earlier complaint
was a real popup that appeared not to dismiss, followed by a challenge to
its usefulness (`../ATTENTION-DISMISS-2026-10-15/README.md:3`). Subsequent
requests addressed Thread/Ask composition, notifications, lost drafts,
honest failure/recovery, navigation and conditional controls. These imply
the following concrete completion requirements, measured against Tenets
2–7 and UX-CANON A.1, A.5, A.10–13:

| Requirement | Existing evidence and its limit |
| --- | --- |
| Find and open the intended place with clear names and a consistent kit | Manifest window/wing sweep; Search Close/exact meeting identity task walks; phone home remains a visual follow-up below. |
| Read and operate the main app families at 1440 and 393 | Sweep reads the actual application manifest, aliases/scopes, seeded Room/meeting/note/person, Chair windows and palette (`tests/e2e/test_desk_sweep.py:189`). It opens visible wings through their own controls (`:938`). It checks fit, text, targets, material, motion and errors (`:878`). |
| Complete actions, keep newer work, and recover from refusal | Focused component/hub tests and selected actual tasks prove the repaired seams. An open-window screenshot alone establishes none of these outcomes. |
| Use one modular material and plain, honest states | The previous visual census, source counsel and current conditional-state observations cover the refined faces. Scanner hit counts alone are not a defect list or proof of complete compliance. |
| Receive the work on the owner's running desk | Current main must serve the released source/build (`CLAUDE.md:23`); a worktree's green quick check proves neither deployment nor owner acceptance. |
| Find the result cohesive and pleasant in normal use | The owner judges the face live (`CLAUDE.md:33`). Isolated observations and source counsel support that judgment; they do not supply it. |

This scope does not require every possible provider, device or input
combination. Natural inference, physical audio and external account execution
are explicitly outside the recorded composition checks. No new integration
campaign follows from the interface goal alone.

## Coverage actually available

The manifest includes Speak, Meetings, Conductor, Agents, Settings, Live,
Rhythm, Setup, Context, Workbenches, Components, Activity, Memory, New Project,
Processes, Commands, People and Calendar snapshot, plus Places and their
aliases (`web/src/desk/applications.ts:59`). Parked entries are treated as
retired/refused rather than silently claimed as live (`test_desk_sweep.py:204`).
Thread, owned Thought, Workbench, Rails/dossiers, Review and PR-result states
also have focused evidence outside the base app sweep.

The merged workflow census inspected main app pairs and populated objects
(`../COHESIVE-WORKFLOWS-2026-10-15/README.md:105`). The later twenty-shot census
covered the remaining meeting/record, dictation wings, activity rules,
history, People and project/setup entry views
(`../DESK-NAVIGATION-DELIGHT-2026-10-16/VISUAL-CENSUS.md:22`), with an explicit
limit: those static shots do not prove the jobs complete (`:45`).

Functional coverage is broader than the task tours. Existing app tests
exercise, for example, Speak's teach/forget loop
(`web/src/desk/__tests__/speak.app.test.tsx:344`), meeting summary/transcript
actions (`meetings.app.test.tsx:329`, `:408`), New Project creation/opened Room
(`web/src/features/project-room/door/__tests__/newProject.app.test.tsx:89`),
Room confirmation/reread (`web/src/features/project-room/__tests__/room.app.test.tsx:223`),
People's added item/reread (`people.app.test.tsx:140`), memory recall
(`memory.app.test.tsx:196`), and destination-specific send receipts
(`send.app.test.tsx:165`). These are component/boundary tests, not natural
provider executions. This audit read representative test definitions; it did
not independently re-run or exhaustively inspect the whole suite.

The inspected quick log records build plus 3945 web tests / 409 files, 651
affected Python tests, 109 sweep tests and 17 canon guards, GREEN
(`.tmp/edges/quick-release.log:11`). **109 is a test total, not 109 completed
business jobs.** Route checks and harness checks contribute to it; wing
captures may add shots inside one case. There are no strict xfails in this
result, but optional named exceptions still exist for desktop icon overlap,
late Engines movement and Room observations (`test_desk_sweep.py:295`);
`_judge` can accept matching observations (`:1019`). This audit did not
reproduce those conditions and does not promote them to new failures.

Selected actual tasks add stronger proof:

- Attention: persisted journal warnings do not interrupt; exact dismissal
  quiets the backlog and newer eligible attention can appear, both widths
  (`../ATTENTION-DISMISS-2026-10-15/README.md:36`). The four-row ambient sampler
  limitation is already explicit (`:31`).
- Thread/Ask/notices: real Edit/Send branch dispatch, exact Ask retry,
  actual Keep artifact, durable newer draft, late-update rejection and
  bounded stack controls (`../THREAD-ASK-REFINEMENT-2026-10-15/README.md:100`).
  Inference/runtime frames were declared replays; queue Open landing was not
  claimed (`:83`). Existing notification-source delivery is not a new UI
  completion requirement established here.
- Work/preferences/objects: immediate Workbench Close/reopen, canonical
  lineage opening, persisted context attach/detach, People read retry and
  calendar A/B draft retention
  (`../COHESIVE-WORKFLOWS-2026-10-15/README.md:141`).
- Navigation/calendar: Search Close/focus and exact meeting scopes, real
  Context save, readable/preserved calendar editing and exact retry producing
  isolated ICS/config output
  (`../DESK-NAVIGATION-DELIGHT-2026-10-16/README.md:98`).
- Current Edge controls: `controls-corner-{1440,393}/observation.json` records
  exactly-once replay activation, Rails above Dock, duplicate Story identity,
  exact evidence/session/dossier targets and no page errors; served build
  `f78d7f42e72d077c`. Transport/audio substitutions are named in each record.
- Current conditional faces: `review-fit-final-393/observation.json` records
  fitted Edit/Defer controls, autofocus and Escape retaining Edit;
  `material-pr-responsive-{1440,393}/observation.json` records durable
  paragraphs and readable PR outcome/output; build `83e97b8c05b13ff5`.
  `receipt-after-{1440,393}/observation.json` records real policy
  Enable/Retry/Pause writes, duplicate suppression and untouched pending work,
  alongside replayed Ask grounding; build `11dccb95ec0cd276`. These are earlier
  observations, not proof of the unfinished caption amendments.

## Remaining gaps, ranked by cost to the owner

1. **Complete the entry experience cohesion pass.** This is the concrete
   product follow-up after the present conditional-controls release. Root
   identified and this audit read the actual
   `.tmp/edges/controls-corner-393/rails-above-dock.png`: the home launchers and
   drawers appear as flat grey rows with rounded corners, visually apart from
   the refined steel/paper faces. This is a cohesion finding under Tenets
   5–6, not evidence that the rows fail to operate. Source: compact Screen
   mounts GoHome (`web/src/desk/screen/Screen.tsx:154`); GoRow uses library
   `Button variant="chrome"` (`GoHome.tsx:74`), whose plate classes are
   intentionally withheld (`web/src/components/signal/Button.tsx:9`).
   `screen.css:77` supplies row geometry but no corresponding kit material.

   The screenshot also has two Meetings labels with different destinations.
   The application verb (`DeskMenuBar.tsx:67`, `verbRegistry.ts:675`) opens
   `surface-meetings`/HistoryCore (`applications.ts:116`). The drawer row
   carries a qualified directory ref (`GoHome.tsx:41`) and opens its Contents
   (`screen/open.ts:54`, `pullouts/registry.ts:36`, `DirectoryPullout.tsx:42`).
   Source assigns different square glyphs, `▣` for the app and `◰` for a
   drawer (`applications.ts:120`, `tools.ts:33`); they are not literally
   identical. Their small rendered distinction and repeated label leave a
   clarity question for the next direction, under Tenets 3 and 7.

   `/welcome` hands off to the existing Get ready cards
   (`web/src/pages/WelcomePage.tsx:8`); `/presence` is a distinct status face
   (`PresencePage.tsx:18`, `web/src/styles/react-app.css:226`). The sweep lists
   both as standalone routes (`test_desk_sweep.py:247`) but opens every route
   at **1440 only** (`:1301`) and checks visible text/errors rather than the
   full window fences (`:1305`). The sampled Setup screenshot is not proof of
   Get ready or Presence at 393. This is a coverage gap, not a discovered
   rendering defect in those two faces.

   **Proof to close:** existing-library direction and actual entry-state
   captures at both widths; phone pointer/scroll reach; separate activation
   of Meetings app and same-name drawer with exact destinations. Read the
   Get ready and Presence states with the same visual criteria as the apps,
   including an appropriate reachable return/next action. Existing named
   tests already cover root drawer identity/open
   (`screen/__tests__/chairScreen.test.tsx:28`), phone Go mounting
   (`Screen.test.tsx:258`), Meetings launch
   (`components/DeskMenuBar.test.tsx:38`), and recorded first-run server/default
   and calendar-denied recovery (`firstrun/__tests__/firstrun.app.test.tsx:98`,
   `:135`; hub counterparts in `tests/integration/test_desk_firstrun.py:119`,
   `:189`). Preserve those jobs; extend only the changed behavior. Their
   presence does not establish material quality or paired visual proof.

2. **Finish release proof and delivery on one named frozen result.** This is
   already root-owned work for the present release, not a new product batch.
   The inspected evidence spans three build IDs, the latest action tour is
   newer than the recorded quick, and README still marks final checks and
   deployment pending (`README.md:61`). Caption amendments remain outside
   this audit. Consequently this snapshot cannot certify the final bundle
   or the running owner's desk. **Proof to close:** final quick/type check
   outcome, affected actual states on the frozen build, explicit carry-forward
   of unchanged earlier task evidence, merge identity and serving HTTP/build
   agreement with normal warm runtime. No blanket repeat of unchanged tasks
   is implied. After those steps the delivery gap is closed; it should not be
   carried as an indefinite “whole app unverified” task.

3. **Obtain the owner's live judgment of the delivered cohesive result.**
   None of the inspected records claims owner acceptance; they explicitly
   separate it from isolated software proof (`README.md:68`,
   `../THREAD-ASK-REFINEMENT-2026-10-15/README.md:88`). This is distinct from
   technical completion. Tenets 2, 3 and 7 and `CLAUDE.md:33` put the owner's
   normal use first. **Proof to close:** the delivered desk available live,
   the owner's observations recorded beside the work, and any concrete
   resulting defects fixed or explicitly left open. A concise sitting can
   cover entry, find/open, edit/keep/reopen, and a relevant work decision;
   this does not require every provider or hardware integration to pass.

4. **Record the formal postmerge review separately from source counsel.**
   Current `REVIEW-ACTIONS-RECEIPTS.md:3` and `REVIEW-MATERIAL-FRAME.md:3`, and
   the preceding release records, expressly describe bounded source counsel
   rather than formal Muad'Dib review. No formal postmerge outcome is
   evidenced by the artifacts inspected here. **Proof to close:** formal
   review of the merged result and disposition of findings, with the main
   watcher's actual outcome attributed to its head. This is fast-cycle
   follow-through (`CLAUDE.md:26`), not a premerge gate and not owner
   acceptance. This audit does not assert that an uninspected review or tape
   run never occurred.

After the current release's checks/deployment are completed, this audit
establishes one bounded interface follow-up: the entry experience above.
It establishes no additional major app family that requires a wholesale
redesign or a new browser journey merely because its base sweep is visual.
It also cannot certify every conditional state or all residual canon debt;
the earlier bounded scanner classification explicitly retained that limit
(`../DESK-NAVIGATION-DELIGHT-2026-10-16/CANON-FOLLOWUP.md:71`).

TUESDAY: The repaired jobs now have useful proof. Finish the entry surfaces,
serve the frozen result, and let the owner do his normal work before claiming
the whole experience is complete and accepted.
