# Phase 167 drift audit — every Rooms face against the surface library

Read-only recon 2026-09-03 (anchors re-verified by the orchestrator).
The Jira wizard (166) is the reference: 17 species, near-zero
hand-rolled markup, the owner's "HECK YES". Every other face carries
hand-rolled blocks. Severity = how far the face is from the reference.

| Face | File (lines) | Phase | Species composed | Hand-rolled blocks (file:line) | Severity |
| --- | --- | --- | --- | --- | --- |
| The Room | ProjectRoomCore.tsx (963) | 158 | 12 — but via six private sub-paths, not the barrel | :191 `egress-badge` string (EgressChip unused); :197/:757 `desk-chat-well`/`-composer`; :341-376 orientation band (`project-room-orientation/-name/-purpose/-outcome/-eyebrow/-facts`); :431-477 focus block (`-focus-group/-focus-label/-count-chip`); :489-551 right rail (`-rail-section/-rail-label/-rail-value/-rail-absent/-change-row`) | HIGH |
| The interview | SetupRoot (331) SetupInterview (311) SetupBrief (158) ClarifyStep (140) SuggestionCards (211) TestResult (83) | 159 | 6 | SetupInterview.tsx:167-206 question form (`setup-question/-label/-textarea`); :261-309 answer rows (`setup-answer-row/-question/-text`); SetupBrief.tsx:27-35 brief panel | HIGH |
| The activation review | ActivationReview.tsx (327) | 159 | (shares the 6) | :185-219 raw `<dl><dt><dd>` ledger (`setup-review-ledger`); :152-170 raw `<button>` elements | HIGH |
| The GitHub wizard | ProviderWizardStep.tsx (648) | 161 | 4 | :46-114 status card (`provider-status-card/-headline/-recovery-command`); :147-202 discovery list; :349-440 test display as label:value fields (`provider-test-field/-label/-value`) | MEDIUM |
| The Jira wizard | JiraWizard.tsx (733) | 166 | 17 | :74-77 four `React.CSSProperties` with raw px (`fontSize: "10px"`, `gap: "6px"`) — a token-fence hole | LOW (reference) |
| Review posture | review/ReviewPosture.tsx (765) | 160 | 12 | :47-55 kind group + count chip; :61-91 comparison fields (`review-field-row/-key/-value`); :110-138 comparison layout (`review-comparison/-side/-label`); :147-150 `review-source-chip` | MEDIUM |
| Update posture | update/UpdatePosture.tsx (497) | 162 | 11 | :70-99 source rows (mixed); :129-158 document view (`update-document/-body/-unverified-banner/-sources`); :187-210 list-row internals inside SurfaceLedgerRow (`update-list-row/-primary/-rev/-time/-chevron`) | MEDIUM |
| Steward posture | steward/StewardPosture.tsx (618) | 163/164 | 9 | :62-100 step rows (`steward-step-row/-primary/-receipt-refs`); :230-265 run list rows; :293-331 circuit rows; :335-461 the whole policy form (`steward-policy-toggle-row/-label`, `-unattended-section`, `-policy-effects/-effect-row/-field`) | MEDIUM |

## Species that exist outside the barrel (copies to promote)

- `computeVerticalScrollHint` — web/src/features/project-room/steward/model.ts:253-267, a Y-axis copy of DoorBoardLane.tsx:255-268 (HS-145-01). One implementation with an axis prop belongs in the barrel; Review, Setup, Update and the Room have NO scroll affordance today.
- `EgressBadge` — web/src/desk/setup.ts:48-54, outside the barrel; the library's EgressChip (gadgets.tsx:716) is the one egress species.
- The glass rigs: eight copies of `_boot`, eight of `_api`, seven of `_assert_clean` across tests/e2e/test_hs158..166_*; rigs 158-163 never build first.

## What the shots show (the orchestrator's read, 1440)

- 158 room-populated: purpose and outcome as two paragraphs; FOCUS as three text lists; the rail as three label:value stacks; the CHANGES list is eight identical "Item created · kind · just now" lines.
- 159 face-questions: a two-line question sentence, a bare textarea, "STEP 2 OF 4" as text; the brief column mostly empty.
- 160 review-queue: queue labels truncated to "Schedu…"/"Update…" at 640; the detail is a label:value card (CURRENT / PROPOSED / Text / Owner / Due / Lane); the id `ai-delta-002` raw.
- 161 evaluation: a "Conflicting sources detected" proposal renders the raw hash list as the PROPOSED value — a wall of hashes.
- 162 editor-claims: a markdown editor with a B/I/U toolbar; the claims and sources have no chips in the document.
- 163/164 dogfood-completed / gate-a-detail: eleven rows of the same green COMPLETED word; no counts, no durations, no receipts in sight.
- 166 jira-scope: project ChoiceCards with TYPE/STYLE chips and the ACLI · site ProvenanceChip — the grammar the rest must speak.
