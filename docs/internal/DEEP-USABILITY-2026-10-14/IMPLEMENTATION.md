# Settled repair — deep usability

Base eb9a3266e. One coherent PR: preserve the owner's working material and make
inner surfaces lead with useful content. Audit is BRIEF plus work/create/
operate/root records. Root read before images; each lane makes a small native
canvas in its named folder before product edits. Hold for SHIP; no staging.
No new global store, navigator, entity, backend or writer framework.

## Work lane

Own PeopleCore.tsx + local people CSS; features/project-room/ProjectRoomCore.tsx
and useProjectRoomController.ts; their focused tests. Canvas deep-work.

- Person Context leads with saved notes and linked work, fully readable at393.
  Add note opens the existing input fields in one on-request well. Calendar,
  alias and project link setup fold through existing Disclosure; preserve
  existing links, source identity and private/shared authority.
- Topic/body/visibility draft uses existing per-relationship desk draft keys.
  It survives Context→Prep/History→Context, Close/reopen and reload. Only clear
  the submitted draft after an actual successful write; refusal keeps it.
- Room Save & confirm awaits real success before closing. A refusal keeps
  editor and entered text/owner/due with visible cause and retry in that same
  context. Do not falsely label an accepted write failed if a reread fails.
- Do not add task editors or revive inert plan rows. Audit found a real Open
  path for accepted actions elsewhere in the same Room.
- Focused files: peopleCore, peopleReopenLens.philo1306, ProjectRoomCore and
  useProjectRoomController tests. No broad suites.

## Create lane

Own components/Pullout.tsx and pullouts/types.ts for a local optional close
guard; editors/{useDebouncedSave,types,NoteEditor,KbEditor,RecipeEditor,
WorkflowEditor}; editorDraft if necessary; InlineEditor.tsx/local CSS;
KbPullout/RecipePullout/WorkflowPullout and exact shared save consumers/tests.
Canvas deep-create. No People/Workbench/Grounding/Settings source edits.

- Keep autosave. One truthful Done/Back action, one pending/saved/failure
  receipt from the actual writer. Flush before Done or chrome/Escape Close.
  Failed save retains editor and durable draft with Retry. No rollback engine.
- Reuse current writer and keepDraft; expose close/status locally to existing
  hosts, not a global save store. Preserve per-field draft acknowledgement.
- Knowledge is name plus member collection. Remove unsupported body authoring
  and reuse current membership routes/row grammar. If a retained unsupported
  body actually exists, show explicit recovery through the existing Note
  producer and keep it until success. Do not claim already forgotten text
  can be recovered or add KB body persistence.
- Prompt-only Workflow edits its existing prompt. Branching graphs retain
  their stored graph and an honest existing editing limit. No graph designer.
- Changed action controls use library Button, preserving voice/editor actions.
- Focused files: InlineEditor.test, deskRemembers2.philo1307, speakableDesk,
  plus a bounded new writer/editor regression file if needed. Name exact tests
  and collect them before run. Include every actual hook consumer.

## Operate lane

Own WorkbenchWindow/localCSS, WorkbenchesHomeCore, ScheduleCreateWindow,
deliveryDossier and DeliveryDossierWindow if observed findings confirmed;
corresponding focused tests. Canvas deep-operate. No other lane sources.

- Work/items/composer lead. Existing agent configuration opens on request;
  a small true bound/unbound fact and actual Choose action stay available.
  Avoid an agent catalogue as the default work body and duplicate empty Add.
- Keep unfinished instruction/body/priority and references per Workbench in
  existing desk drafts. Reopen/reload does not submit. Clear only an accepted
  item; failure preserves all entered work and source context.
- Workbenches list rereads existing authoritative data after creation/item
  changes through existing store/event signals. No new polling framework.
- Recurring schedule mode/cron/duration are kept with title/time if confirmed
  by capture; only clear on accepted create, never arm anything in a walk.
- Dossier Retry/Reload must actually retry its same read, not close the face,
  if observed. Keep current request identity/authority; no dispatch/run action.
- Scoped checks: workbenchEditing, workbenchFrames, workbenchOperates,
  workbenchesHome, scheduledRecordingSlice; add at most targeted schedule/
  dossier files where no current component check exists. No broad suites.

## Verification and integration

After implementation, repeat the failed job transitions at1440/393 and inspect
shots, including refused write→retry→durable read, and draft return/reload.
Retain source identity/private context and current writer fences. Isolated
HOME+test_lock for every command, Node22, Vitest with --maxWorkers=2, pytest -n 8 --dist worksteal. No owner state,
model/agent/terminal/mic/schedule execution or external delivery. Two capture
setup attempts then exact gap. Root owns fresh built review, combined quick
check GREEN, status/PR/merge and normal idle local hub deployment.

Root owns the now-reproduced shared Grounding selection/keyboard seam and
its focused tests plus real Ask selection graph walk. Other tails remain explicit: Repo browsing is not a promise of a new code editor; parked
Directory is not revived. The audit matrix names unseen states instead of
inheriting approval from generic app screenshots.
