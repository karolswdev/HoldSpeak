# Shared system and flagship workflows — bounded planning audit

DRAFT — UNCHECKED, awaiting Muad'Dib. 2026-10-16.

Read-only planning audit of the current worktree. No tests, browser, build,
owner-state read, or implementation in this task. Existing unmerged Brief
candidate edits were preserved and are not treated as verified behavior.
Source anchors can drift. All remaining candidates below are source-inferred;
none was newly observed on the owner's desk.

Tuesday: an architect can ask about work, open the cited source, keep an output,
give an agent a decision, and change a setting without losing words or guessing
whether the action happened. Tenets 3/4/5/7 and Constitution VI apply.

## Preserve the work already delivered

The release records report actual isolated observations, not observations made
by this audit. Do not reissue those repaired defects as current findings:

- #1214–1215: journal popup exclusion, exact-row dismissal, bounded notice
  stacks, full payload wells, reachable phone actions, conversation paper,
  exact Ask transmission/Keep lineage, Thread reply/load recovery. See
  `THREAD-ASK-REFINEMENT-2026-10-15/README.md:15`, `:77`, `:91`, `:118`, `:122`.
- #1216: Workbench Close/refusal/reopen and ordered drafts, exact Add/Coder
  Retry, honest Conductor/Lane decisions and accepted-read recovery. The
  current status records these outcomes at `pm/STATUS.md:67`.
- #1217–1218: Search Close/focus and meeting identity, empty Context, Calendar
  draft/Retry ownership, Thread replay/Rails native controls, Ask zero-grounding
  and named citations, current-value Pad speech, readable PR draft outcomes,
  and desktop footer action ownership. See `pm/STATUS.md:30` and `:48`.
- #1219: grouped native phone launchers, wrapped names, precise destinations,
  Presence material and query-preserving Desk return. The final record says
  no further concrete entry blocker was established in that finite pass:
  `COHESIVE-DESK-ENTRY-2026-10-16/README.md:165`, `:184`. Its inherited retained
  Presence activity label on disconnect remains an explicit limit (`:79`).

These records do not establish every provider/hardware state or owner aesthetic
acceptance. They are a reason to build on the current system, not restart it.

## The existing kit is sufficient

| Need | Existing primitive and source | Planning rule |
| --- | --- | --- |
| App hierarchy and readable groups | `surface/Surface.tsx:109` Section, `:388` Facts, `:440` Well, `:780` Ledger; `surface/contract.md` interior kit | One leading fact, named groups, quiet facts and local verbs. Preserve each application's useful composition. |
| User-authored and generated material | `surface/Material.tsx:110`; Ask uses it at `components/AskPanel.tsx:57`; Thread uses the common traffic grammar at `pullouts/ThreadPullout.tsx:1633` | Preserve paragraphs/lists. Use the existing material reader; no parallel Markdown skin. |
| Control sheets and editors | `surface/gadgets.tsx:27` Group/inset/actions, `:59` Row/controlWidth, `:260` String, `:363` Pad | Group related settings; full-width Pad for multiline work. Preserve current-value late speech and existing draft ownership. |
| Native actions and closed choices | library Button; `surface/gadgets.tsx:160` CycleGadget | Preserve native Enter/Space, checked choice, disabled reason and exact writer. No per-app dropdown or raw-button purge. |
| Loading, empty and unavailable | `surface/Surface.tsx:214` State with loading/error/empty and real Retry/action | Empty means a successful empty read. Failed reads keep known content and expose a local recovery action. |
| Outcomes and pending/refused actions | `surface/patterns/ActionNotice.tsx:8`, `surface/SurfaceFooter.tsx`; `hooks/useWriteReceipt.ts:224`; EngineLine/RunLine already composed by Ask (`AskPanel.tsx:75`) | One outcome beside its action. Pending belongs to the actual request; Retry retains its subject. Prefer existing face state/hooks over a new controller. |
| Citations and source opening | `surface/citations.tsx:84`; `openObject` and `shell`; applications manifest at `applications.ts:7` | Preserve qualified identity and fragment. Named cached citations and truthful plain non-window refs already exist. Source inspection must not change lifecycle. |

Paths in the table are relative to `web/src/desk/` unless named otherwise.
`DESKOS_COMPONENT_PATTERN.md` describes the SwiftUI iPad reference; it is not a
replacement web-component framework.

## Remaining source candidates, ranked by cost to the owner

1. **Thread command failure can discard the unaccepted input.**
   `ThreadComposer.tsx:652` clears the draft before `/todo` submits; `:666` and
   `:669` append a failure string with no retained exact Retry. `/compact` has
   the same separate status-string path at `:674`. Normal Send already preserves
   words until acceptance (`:792`). This is a concrete source inconsistency in
   the same conversation, not a claim that reply recovery is still broken.
   Tenet 3 and Article VI.

2. **Context choices conflate read failure with no choices.**
   `AskPanel.tsx:187` parses a raw `apiRequest` response without checking HTTP
   success; `:194` substitutes an empty Projects list on failure. Thread's
   `/mode` read swallows failure (`ThreadComposer.tsx:448`, `:472`), and prompt,
   guardrail and People helpers return empty on failed reads (`:252`, `:282`,
   `:317`). Ordinary empty caches can therefore look like unavailable services.
   This does not invalidate the repaired Ask grounding receipt/citations.
   Tenet 3 and Article VI.

3. **Actionable notifications have unequal recovery.**
   Qlippy's projection Dismiss stores the exact row and failed/pending state
   (`components/AmbientLayer.tsx:390`, `:441`). Proposal Approve/Decline instead
   awaits its writer with only `finally` cleanup (`:408`), and its buttons at
   `:467` have no decision-specific failure/Retry rendering. A rejected HTTP
   promise has no named outcome in that path. This is outside the already
   repaired journal interruption and Dismiss behavior. Tenet 3 and Article VI.

4. **Remote access uses a read retry for some failed writes.**
   Toggle writes put errors into `SettingsCore.tsx:778`; revoke does the same
   at `:910`. The shared error's Retry at `:1228` only calls `fetchRemote`,
   which clears the error after a successful read (`:753`). Reading current
   state can be appropriate, but its label must say Reload if it does not
   repeat the failed action. Do not make another grant framework; preserve
   existing row-specific refusal and grant receipts (`:822`). Tenets 3/4.

5. **Outcome presentation still has small local differences.**
   Conductor's stale-member pill uses `plainReceipt` (`ConductorWindow.tsx:271`),
   while its footer can print `member.receipt` directly (`:81`). Settings uses
   custom failure wrappers (`SettingsCore.tsx:924`, `:1228`, `:2505`) beside its
   existing SurfaceState. These are composition candidates, not established
   clipping or wrong-outcome defects. Observe populated states before deciding
   whether any change earns its cost. Tenets 1/4/5.

No additional Workbench or Desk entry defect was established in this bounded
source pass. Current Workbench Runs already distinguishes failed/loading/empty
and offers the correct agent/engine/run door
(`workbench/WorkbenchRunsWing.tsx:40`); Memory retains read recovery
(`components/WorkbenchWindow.tsx:1983`); footer write failure outranks quiet
receipts (`:2065`). Preserve these patterns.

## Coherent delivery batches and acceptance

**A — Conversation continuity.** Finish the bounded cited-source repairs after
the plan settles; add honest source-choice read states and repair command
submission ownership. Keep the existing Ask/Thread material, composer and
citation species. Acceptance: an old/pending cited source opens by exact ref;
404 produces visible recovery; a failed Projects/mode/prompt read differs from
no matches; Retry does its exact read; refused `/todo` retains its words and
subject, successful submission clears only its submitted draft; newer typing
and late speech survive. Keep/Retry preserves the original prompt/sources.

**B — One actionable notice outcome.** Extend the existing Qlippy decision path
to retain the exact proposal and decision while pending/refused, as Dismiss
already does. Acceptance: failed Approve/Decline stays on that proposal with a
named outcome; Retry repeats that proposal/decision once; a newer card never
becomes the failed action's target; the stack stays above the Dock at 393;
successful dismissal still affects only presentation and newer eligible
attention still arrives. Preserve producer payload and journal exclusion.

**C — Settings action ownership.** Correct Remote access's read-versus-write
action labels and recovery in its existing inset sheet. Adopt existing
SurfaceState/receipt material only where it improves the actual face.
Acceptance: Reload means a read; any Retry names and repeats its actual failed
operation; no success is implied by an unrelated read; selected credential/
grant identity and draft remain; one-time token and existing grant receipts
retain their current lifecycle. Other settings' exact failed-change Retry,
Calendar editing and Advanced folds remain covered.

**D — Flagship continuity and final composition.** Observe a finite connected
job on the current kit: Desk/Search → source → Ask/Thread → kept output →
Workbench → Conductor decision → relevant Settings repair → return to work.
Use long real titles, populated material and one unavailable/refused branch.
Only newly observed inconsistencies produce product changes. Conductor outcome
wording is an explicit specimen to judge; Workbench's truthful empty/failed
states and the manifest-derived phone doors are reference implementations.
Acceptance at 1440/393: exact object/scope, visible outcome and next action,
preserved draft/focus, complete readable material, no duplicate completion
receipt, no zero counters, no obscured action, working native activation and
reduced-motion stillness. Source opens and return preserve the current context.

Each batch should remain a small app/concern change with focused checks and the
normal quick cycle. Shared material specimens use actual existing components;
no new navigation framework, token clone, scanner purge, or giant abstraction.
No UI work is authorized merely by this DRAFT planning record.

## Unknown

The new candidates have not been exercised. No actual visual comparison,
provider/native outcome, physical input behavior, owner aesthetic verdict,
formal postmerge review or complete source census is claimed. This audit did
not inspect every conditional Settings/Thread tool renderer. The parent plan
must integrate other app audits and choose the accepted direction before any
candidate implementation resumes.
