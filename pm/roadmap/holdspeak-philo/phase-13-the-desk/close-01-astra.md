# PHILO-13-01 — close preparation on main

**DRAFT — UNCHECKED — awaiting Muad'Dib. Story 01 remains in-progress.**

LANE: B0 / story 01. Astra owns; Muad'Dib checks. Worktree
`../wt-philo-13-close-astra`, branch `docs/philo-13-close-astra`.
Product baseline: main `23a6c137f896e230e44e8e4e31f1f508b60fa05f`, after
C7 #751 (`1e5f3984ee10872814539318ca597f06b95ef4e4`). The same worktree
closed B5 separately in #753; no product or atlas source changed here.

OUTCOME: partial. The requested current-main Directory/Zone and F1 reruns
are complete. #747 remains OPEN at `ad3855f0d4e984bd60c38ca26c41ecb7facf1fa3`
as checked on 2026-10-03. A merged B2 revision and its final main rerun do
not yet exist. No B0 done flip or final canonical evidence is claimed.

PROOF:

- The story's five-file selection [collects 172 tests](assets/story-01-close-prep/collection.txt)
  and passes 172 in 8.58 s through Delivery Workbench. The selection retains
  the three mandatory shared fences. The [captured commands and output](assets/story-01-close-prep/captured-runs.md)
  also record all six actual atlas invocations, one case and one isolated hub
  at a time. This incremental capture waits outside `evidence-story-01.md`
  while the story stays open, as required by the gate's pairing rule.
- Every observation names product revision `23a6c137f`, a fresh run HOME,
  a DB beneath that HOME, and the production frontend build. `dirty=true`
  reflects closure documentation/evidence only. Phone runs use native touch.
  [Run index](assets/story-01-close-prep/runs.json);
  [unaltered observation/shot hashes](assets/story-01-close-prep/manifest.json).
- The historical B2 table is present in #747's tree, despite its PR body
  referring to a comment that is absent:
  [batch](https://github.com/karolswdev/HoldSpeak/blob/ad3855f0d4e984bd60c38ca26c41ecb7facf1fa3/pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-07-shots/b0-on-head/summary-batch.txt),
  [reruns](https://github.com/karolswdev/HoldSpeak/blob/ad3855f0d4e984bd60c38ca26c41ecb7facf1fa3/pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-07-shots/b0-on-head/summary-reruns.txt).
  Astra read the four Dossier/Terminal observations: their predicates pass
  at both widths, including F2 at 393. Those candidate observations report
  revision `e9b01e227` plus a dirty working tree, not the later final B2
  merge. Info's amended reruns also record passes at both widths.
- Astra inspected every available shot and read initial/terminal results
  separately. A trigger or setup failure has no successful terminal result.
  No hidden target or missing predicate is counted as a pass.

| Path | Width | Pass | Product-red | Rig-limit / unverified path |
|---|---:|---|---|---|
| Directory → Zone | 1440 | No | F7 persists: real Directory and world-hit probes agree, but Open is disabled. C7/story 17 residual; Tenets 3 and 6. | No timeout-only inference: the disabled menu is visible in the [blocked shot](assets/story-01-close-prep/zone-1440/blocked.png). |
| Directory → Zone | 393 touch | No | The face enters hidden-menu mode after the recorded Floor tap; Search is unreachable. C7 controls/gesture investigation; Tenets 3 and 6. | Setup stops at `.desk-tools-launch`; this run does not reach the Zone Open predicate and does not re-prove phone F7. [Observation](assets/story-01-close-prep/zone-393/observation.json), [shot](assets/story-01-close-prep/zone-393/blocked.png). |
| Chain pullout | 1440 | Yes | F1 cleared: Close removes the card and Dock chip; the ordinary door reopens both after reload. | None. [Observation](assets/story-01-close-prep/chain-1440/observation.json), [after](assets/story-01-close-prep/chain-1440/after.png). |
| Chain pullout | 393 touch | No | Card and Dock chip do close. After reload and the recorded Floor tap, hidden menus prevent Search. C7 controls/gesture investigation. | The reopen portion of F1 is not observed; this is not evidence that the old ghost returned. [Observation](assets/story-01-close-prep/chain-393/observation.json), [shot](assets/story-01-close-prep/chain-393/blocked.png). |
| Coder pullout | 1440 | Yes | F1 cleared: Close removes the card and Dock chip; the ordinary door reopens both after reload. | None. [Observation](assets/story-01-close-prep/coder-1440/observation.json), [after](assets/story-01-close-prep/coder-1440/after.png). |
| Coder pullout | 393 touch | No | Card and Dock chip do close. The same post-reload hidden-menu Search failure interrupts reopening. C7 controls/gesture investigation. | Reopen not observed; original F1 ghost not reproduced. [Observation](assets/story-01-close-prep/coder-393/observation.json), [shot](assets/story-01-close-prep/coder-393/blocked.png). |

LEDGER:

- **b / observed main defect:** F7's disabled Zone Open survives #751 at
  1440. Its existing home is C7/story 17, even though that story is marked
  done. The closure must retain this residual or a named handoff.
- **Unclassified cause / observed main access failure:** three 393 runs
  record Floor as tapped but show the Chair with hidden menus and Back to
  Desk. The Floor handler only toggles Chair/Floor
  (`web/src/desk/chairState.ts:18`); Hide the menus belongs to another
  control. Thus the logs alone do not establish whether the native tap
  hit the wrong moving Dock target or whether case setup needs a new
  visible door. Home: C7 controls/gesture investigation, with B0 owning any
  proven atlas correction. No guard was weakened or case edited to pass.
  Source confirms the observed mode hides Search (`chrome-menus.css:14`)
  and offers Back to Desk (`components/window/RoomActions.tsx:30`). That
  recovery was not exercised in these six runs. A proposed optional recovery
  step is not a verified repair; first establish why Floor entered this mode,
  then change any necessary case and its fence together.
- **Inherited results, not rerun here:** repository.window F3 → C1/story 11;
  roadmap.window 1440 → C4/story 14 (also red on main in the B2 record);
  Calendar raw refusal wording → BACKLOG B0-L1. See the prior
  [findings](findings-01-astra.md). Their current outcomes need the final
  main table; this preparation does not silently promote old evidence.
- **Pending dependency:** B0-F2 must pass after B2 merges. The dispatch
  reports F2 passing at 393 on B2's head; that is branch evidence, not a
  final current-main result. `ad3855f0`'s optional Floor step for Info is
  on #747 and must ride that merge.

AMENDMENTS: none. This is a rerun and ledger update, with no product, atlas,
test or guard changes. The dispatch asks to prepare now and close after
#747; this document does not change that gate. No full-suite result is
claimed for this documentation-only preparation.

The earlier built B0 check is not missing: Muad'Dib's
[signed r3](https://github.com/karolswdev/HoldSpeak/pull/726#issuecomment-5962766839)
and Astra's [merge record](https://github.com/karolswdev/HoldSpeak/pull/726#issuecomment-5963142100)
record the conditions paid for #726. This new closing evidence stays DRAFT
for the caller's check and the B2 dependency.

UNKNOWN: #747's final merged commit; the final nine-case/two-width main
table; the cause of the 393 wrong-screen transition; the unreached phone
Zone/reopen predicates. Tuesday: desktop Chain/Coder return correctly;
the architect still cannot complete these phone paths in the recorded runs.

## Remaining close steps

1. After #747 merges, fetch its merged main revision into an isolated lane
   worktree. Preserve the merge SHA and the existing B2-head table.
2. Run all nine actual B0 atlas cases at both widths, one invocation per
   case, with the story's scoped fences. Inspect every observation and shot.
   F2 must pass; keep every outside-B2 red with its named home. Recheck the
   phone access failures above without weakening hit or lifecycle guards.
3. Capture final proof through Delivery Workbench into
   `evidence-story-01.md`; cite B0's #726 merge `44ec934a`, the B2 merge,
   the B2-head table and the new main run table. Check acceptance honestly,
   then flip only story 01 and ship its paired evidence through the gate.
