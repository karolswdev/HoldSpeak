# HS-167-04 - The faces recomposed I: the Room, the interview, the activation review, the GitHub wizard

- **Project:** holdspeak
- **Phase:** 167
- **Status:** done
- **Depends on:** HS-167-01, HS-167-03
- **Unblocks:** HS-167-05, HS-167-06
- **Owner:** unassigned

## Problem

The front half of the journey — the Room a user lands in and the
setup that creates it — is the oldest and most hand-rolled: 963 +
1,561 + 648 lines with five hand-rolled blocks in the Room, a raw
`<dl>` in the activation review, label:value test fields in the
GitHub wizard. The Jira wizard next to them is the reference.

## Scope

- **In:** ProjectRoomCore.tsx, SetupRoot/SetupInterview/SetupBrief/
  ClarifyStep/ActivationReview/SuggestionCards/TestResult,
  ProviderWizardStep.tsx recomposed to the ratified mockups from
  the barrel only (imports via `desk/surface`, the six private
  sub-paths gone); controllers, models and decoders untouched
  except the 02 wire; the GitHub wizard reaches Jira-wizard parity
  (status as a StateChip card, discovery on ChoiceCards, the test as
  a ProgressPlan + Receipt, EgressChip naming github.com); the
  interview's questions and answers as ledger rows with the mic on
  every input; the activation review as a SurfaceLedger with real
  Buttons; the Room's orientation band, focus block and rail on the
  new species with the scroll-hint on every scrolling well. Shots
  at 1440 + 393 through the rebuilt rigs (158, 159, 161) — before/
  after pairs — read by the orchestrator against the mockups before
  the gallery.
- **Out:** the postures (05); the walk (06).

## Acceptance criteria

- [x] Every hand-rolled block the 01 audit named in these files is gone; the CSS classes it owned are deleted (no dead style).
- [x] The 158/159/161 glass rigs and their vitest pass unchanged in assertion (behavior identical); web baseline zero branch-new.
- [x] Shots match the mockups at both widths; the gallery carries before/after; the orchestrator read every PNG.

## Landed (2026-09-03)

Three orchestrator rounds. Round 1 (the worker's first build) was
BOUNCED on pixels: rows overprinting, section labels twice, the
purpose hidden behind a closed fold, the posture strip missing, the
setup faces untouched "for test compat" — the law restated: a test
that pins dead DOM shape gets a selector edit, never a reason to keep
the shape. Round 2 found the ROOT CAUSE in the species: the default
ledger grid's fixed `6ch` column overprinted any date token in the
cells — paid in the barrel as the `data-cols="room"` template (a flex
row: time · lead · primary · gapped cells · trailing; the primary
wraps and cells fall under at the narrow container). Round 2 also
restored a behavior the redesign dropped (the Review verb hides when
nothing is pending — WEB-NOW-002, two unit tests + a glass assertion).
Landed: the Room on SurfaceIdentity (wire-only chips), the posture
strip (SurfaceVerbs active + count), FOCUS as room ledgers, THE WEEK
as MetricStrip + SurfaceStream with the identical-entry collapse,
EgressChip, ScrollHint, the barrel import, 18 dead classes deleted;
the interview on ProgressPlan + the placeholder well with the mic
inside + answered rows + THE BRIEF facts + the footer; the activation
review on the WHAT WILL RUN ledger + facts + the baseline plan +
full-host EgressChips (the `<dl>`, the raw buttons and the prose
gone); the GitHub wizard on StateChip/ProvenanceChip/ProgressPlan/
Receipt/EgressChip (42 dead setup classes deleted). Beauty-pass
ledger (05): MetricStrip wraps its fourth metric at 640; stream
entries keep the species' 15px sans (a dense variant); the interview's
Next verb absent while the answer is empty (render disabled). Gates
read by the orchestrator: vitest 789/789 (project-room + surface);
baseline zero branch-new; token gate clean; glass 158/159/161 18
passed + 1 honest skip. Shots: 16 before/after pairs.

## Test plan

- **Web:** web/src/features/project-room/**/__tests__; `scripts/check_web_baseline.py --run`.
- **Glass:** test_hs158_room_glass, test_hs159_interview_glass, test_hs161_github_glass on the shared conftest.
