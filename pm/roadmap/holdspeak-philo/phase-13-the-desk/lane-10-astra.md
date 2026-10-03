# PHILO-13-10 — Astra lane report

**Closed on main — [current proof and ledger](close-10-astra.md).** Muad'Dib's
[PASS on #739](checks/story-10-muaddib-record.md) is recorded. The report below
is the historical candidate record; its pending-check and clipping statements
are superseded by the closure record.

LANE: B5, The update writes the week. Worktree `../wt-philo-13-10-astra`; branch `feat/philo-13-10-astra`; base `5912fcb9474cae7b058838f120a2c216189be89a`.

OUTCOME: the deterministic composer now reads active linked meetings, their stored summaries, Room decisions and open actions with owners. Each added line has its source claim. Failed source reads produce named coverage caveats. Action-kind proposals do not become duplicate decisions. No story flips done before counsel.

PROOF:

- [235 collected](assets/story-10-week/collection.txt), [235 passed through Delivery Workbench](assets/story-10-week/captured-runs.md), including the three mandatory shared files. [Missing-week red](assets/story-10-week/red-before.txt) and [action-as-decision red](assets/story-10-week/red-decision-kind.txt) preceded their fixes. Tests mint meetings, actions, decision artifacts and confirmations through real producers; a forbidden broker fences the deterministic path.
- Actual Room → Updates → Draft cases pass at 1440 and 393 native touch; the operation sibling reads the stored draft and claims. [Run index](assets/story-10-week/runs.json), [manifest](assets/story-10-week/manifest.json). The summary and decision producer use a labelled loopback provider reply; drafting itself is deterministic. The inspected rows carry the summary, one decision, Avery's migration-window action and Morgan's rollback-checklist action, with meeting/decision/action refs.
- [All 12 Documentation Navigation commands](assets/story-10-week/navigation.txt) and [web build](assets/story-10-week/build.txt) pass. No full suite ran.

LEDGER: (b, inherited editor behavior, exposed by populated draft) long CodeMirror lines do not wrap. At 393 the summary and owners extend past the visible right edge; at 1440 the long summary also extends past the editor edge. [Phone shot](assets/story-10-week/week-393/after.png), [desktop shot](assets/story-10-week/week-1440/after.png). Tenets 3 and 7: the report owner must scroll to read the full line. Home: Room/editor faces lane. The atlas text predicate proves draft content and stored data, not complete on-screen readability. No Room/CSS file changed here.

AMENDMENTS: the shared canonical-producer allowlist now includes the existing `project.draft_update`; the old read/write guard still rejects a mutating observation. The first operation walk requested an `operation_id` absent from this operation's response and failed; the unused capture was removed, then the actual case passed. Both observations are retained. Capability metadata and generated references are refreshed. Tests and walks ran on the named base plus this candidate diff; the run HOME and hub DB were isolated and cleaned. Node 22.21.0 was used because the installed Node 25 cannot load llhttp.

UNKNOWN: Muad'Dib's check, merge and the owner's sitting. Tuesday: the week is written without typing its source facts; full phone readability still needs the editor face fix above.
