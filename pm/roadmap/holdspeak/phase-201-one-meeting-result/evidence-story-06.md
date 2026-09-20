# Evidence - HS-201-06

- **Story:** HS-201-06 - Plain words on the path
- **Status:** done
- **Date:** 2026-09-19

## Proof

### Captured run — 2026-09-19T22:48:28Z

- **Command:** `sh -c cd web && npx vitest run src/desk/surface/__tests__/count.test.ts src/meetings/MeetingIntelRecovery.test.tsx src/pages/cores/__tests__/ChangePlacesCore.test.tsx 2>&1 | tail -5`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f68e722fbc45e4f4afd68c51c0ca514762508b57

```text
 Test Files  3 passed (3)
      Tests  18 passed (18)
   Start at  16:48:29
   Duration  1.31s (transform 522ms, setup 258ms, import 746ms, tests 554ms, environment 899ms)
```

### Captured run — 2026-09-19T22:48:30Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.zI1mhVmRqW uv run pytest -q tests/unit/test_product_copy.py tests/unit/test_product_language.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_ux_canon_scan.py tests/unit/test_phase200_canon_guard.py tests/unit/test_phase200_doc_claims.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_doc_drift_guard.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** f68e722fbc45e4f4afd68c51c0ca514762508b57

```text
........................................................................ [ 41%]
........................................................................ [ 83%]
....F.....F.................                                             [100%]
=================================== FAILURES ===================================
_________ test_docs_do_not_restore_retired_inference_setup_vocabulary __________

    def test_docs_do_not_restore_retired_inference_setup_vocabulary() -> None:
        offenders: list[str] = []
        for path in _all_docs_and_readme():
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                match = _RETIRED_INFERENCE_VOCAB.search(line)
                if match:
                    offenders.append(f"{path.relative_to(_REPO)}:{lineno}: {match.group(0)!r}")
    
>       assert not offenders, (
            "Retired inference setup vocabulary returned to docs/ or README. Use "
            "Models for availability and Assignments for job selection instead:\n  "
            + "\n  ".join(offenders)
        )
E       AssertionError: Retired inference setup vocabulary returned to docs/ or README. Use Models for availability and Assignments for job selection instead:
E           docs/internal/inventory-2026-09-19/02-capabilities.md:500: 'inference_target_id'
E           docs/internal/inventory-2026-09-19/02-capabilities.md:531: 'inference_target_id'
E           docs/internal/inventory-2026-09-19/03-roadmap.md:75: 'Download & use'
E       assert not ["docs/internal/inventory-2026-09-19/02-capabilities.md:500: 'inference_target_id'", "docs/internal/inventory-2026-09-...2-capabilities.md:531: 'inference_target_id'", "docs/internal/inventory-2026-09-19/03-roadmap.md:75: 'Download & use'"]

tests/unit/test_doc_drift_guard.py:121: AssertionError
________________ test_no_live_doc_has_a_dangling_relative_link _________________

    def test_no_live_doc_has_a_dangling_relative_link() -> None:
        offenders: list[str] = []
        for path in _maintained_docs():
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for target in _MD_LINK.findall(line):
                    target = target.strip()
                    # Skip external, anchor-only, and non-doc targets.
                    if target.startswith(("http://", "https://", "mailto:", "#", "<")):
                        continue
                    # Drop any #fragment / ?query suffix.
                    rel = target.split("#", 1)[0].split("?", 1)[0]
                    if not rel:
                        continue
                    resolved = (path.parent / rel).resolve()
                    if not resolved.exists():
                        offenders.append(
                            f"{path.relative_to(_REPO)}:{lineno}: -> {target}"
                        )
    
>       assert not offenders, (
            "A maintained doc links a path that does not exist (dangling relative link). "
            "Fix the path or the move:\n  " + "\n  ".join(offenders)
        )
E       AssertionError: A maintained doc links a path that does not exist (dangling relative link). Fix the path or the move:
E           docs/internal/checks/constitution-seven-tenets-astra.md:14: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:25
E           docs/internal/checks/constitution-seven-tenets-astra.md:16: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/DOCS_STYLE.md:10
E           docs/internal/checks/constitution-seven-tenets-astra.md:16: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:35
E           docs/internal/checks/constitution-seven-tenets-astra.md:18: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:39
E           docs/internal/checks/constitution-seven-tenets-astra.md:20: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:102
E           docs/internal/checks/constitution-seven-tenets-astra.md:20: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:163
E           docs/internal/checks/constitution-seven-tenets-astra.md:22: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:125
E           docs/internal/checks/constitution-seven-tenets-astra.md:22: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/UX-CANON.md:27
E           docs/internal/checks/constitution-seven-tenets-astra.md:24: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:134
E           docs/internal/checks/constitution-seven-tenets-astra.md:24: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/UX-CANON.md:115
E           docs/internal/checks/constitution-seven-tenets-astra.md:24: -> /Users/karol/dev/tools/HoldSpeak/AGENTS.md:33
E           docs/internal/checks/constitution-seven-tenets-astra.md:26: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:89
E           docs/internal/checks/constitution-seven-tenets-astra.md:26: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:109
E           docs/internal/checks/constitution-seven-tenets-astra.md:26: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/INVENTORY-2026-09-19.md:13
E           docs/internal/checks/constitution-seven-tenets-astra.md:28: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/ORCHESTRATION.md:51
E           docs/internal/checks/constitution-seven-tenets-astra.md:28: -> /Users/karol/dev/tools/HoldSpeak/CLAUDE.md:33
E           docs/internal/checks/constitution-seven-tenets-astra.md:28: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:194
E           docs/internal/checks/constitution-seven-tenets-astra.md:88: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:24
E           docs/internal/checks/constitution-seven-tenets-astra.md:88: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:39
E           docs/internal/checks/constitution-seven-tenets-astra.md:90: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/checks/constitution-seven-tenets-astra.md:51
E           docs/internal/checks/constitution-seven-tenets-astra.md:90: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/UX-CANON.md:23
E           docs/internal/checks/constitution-seven-tenets-astra.md:90: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/ORCHESTRATION.md:234
E           docs/internal/checks/constitution-seven-tenets-astra.md:92: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/checks/constitution-seven-tenets-astra.md:43
E           docs/internal/checks/constitution-seven-tenets-astra.md:92: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/ORCHESTRATION.md:52
E           docs/internal/checks/constitution-seven-tenets-astra.md:92: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:206
E           docs/internal/checks/constitution-seven-tenets-astra.md:94: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/checks/constitution-seven-tenets-astra.md:66
E           docs/internal/inventory-2026-09-19/06-check-astra.md:15: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/05-desk-census.md:220
E           docs/internal/inventory-2026-09-19/06-check-astra.md:17: -> /Users/karol/dev/tools/HoldSpeak/holdspeak/services/meeting_deferred_queue_binding.py:126
E           docs/internal/inventory-2026-09-19/06-check-astra.md:17: -> /Users/karol/dev/tools/HoldSpeak/holdspeak/services/inference_service_route_policy.py:93
E           docs/internal/inventory-2026-09-19/06-check-astra.md:17: -> /Users/karol/dev/tools/HoldSpeak/holdspeak/db/intel.py:361
E           docs/internal/inventory-2026-09-19/06-check-astra.md:17: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:140
E           docs/internal/inventory-2026-09-19/06-check-astra.md:19: -> /Users/karol/dev/tools/HoldSpeak/holdspeak/services/meeting_intel_service.py:81
E           docs/internal/inventory-2026-09-19/06-check-astra.md:19: -> /Users/karol/dev/tools/HoldSpeak/web/src/desk/chair/ChairHome.tsx:614
E           docs/internal/inventory-2026-09-19/06-check-astra.md:19: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:45
E           docs/internal/inventory-2026-09-19/06-check-astra.md:21: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/05-desk-census.md:39
E           docs/internal/inventory-2026-09-19/06-check-astra.md:21: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/05-desk-census.md:67
E           docs/internal/inventory-2026-09-19/06-check-astra.md:21: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/05-desk-census.md:157
E           docs/internal/inventory-2026-09-19/06-check-astra.md:23: -> /Users/karol/dev/tools/HoldSpeak/web/src/features/project-room/recall/RecallFace.tsx:84
E           docs/internal/inventory-2026-09-19/06-check-astra.md:23: -> /Users/karol/dev/tools/HoldSpeak/web/src/desk/chair/ChairHome.tsx:1296
E           docs/internal/inventory-2026-09-19/06-check-astra.md:23: -> /Users/karol/dev/tools/HoldSpeak/web/src/features/project-room/useProjectRoomController.ts:33
E           docs/internal/inventory-2026-09-19/06-check-astra.md:23: -> /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/PeopleCore.tsx:456
E           docs/internal/inventory-2026-09-19/06-check-astra.md:25: -> /Users/karol/dev/tools/HoldSpeak/holdspeak/services/watch_service.py:102
E           docs/internal/inventory-2026-09-19/06-check-astra.md:25: -> /Users/karol/dev/tools/HoldSpeak/holdspeak/services/project_door_service.py:308
E           docs/internal/inventory-2026-09-19/06-check-astra.md:25: -> /Users/karol/dev/tools/HoldSpeak/holdspeak/services/reaction_service.py:219
E           docs/internal/inventory-2026-09-19/06-check-astra.md:27: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/05-desk-census.md:311
E           docs/internal/inventory-2026-09-19/06-check-astra.md:27: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/01-faces.md:410
E           docs/internal/inventory-2026-09-19/06-check-astra.md:29: -> /Users/karol/dev/tools/HoldSpeak/web/src/desk/verbRegistry.ts:581
E           docs/internal/inventory-2026-09-19/06-check-astra.md:29: -> /Users/karol/dev/tools/HoldSpeak/web/src/desk/verbRegistry.ts:232
E           docs/internal/inventory-2026-09-19/06-check-astra.md:29: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/05-desk-census.md:176
E           docs/internal/inventory-2026-09-19/06-check-astra.md:31: -> /Users/karol/dev/tools/HoldSpeak/web/src/desk/threads.ts:1083
E           docs/internal/inventory-2026-09-19/06-check-astra.md:31: -> /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/ThreadPullout.tsx:640
E           docs/internal/inventory-2026-09-19/06-check-astra.md:33: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/03-roadmap.md:140
E           docs/internal/inventory-2026-09-19/06-check-astra.md:33: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:106
E           docs/internal/inventory-2026-09-19/06-check-astra.md:33: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/INVENTORY-2026-09-19.md:361
E           docs/internal/inventory-2026-09-19/06-check-astra.md:89: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:70
E           docs/internal/inventory-2026-09-19/06-check-astra.md:91: -> /Users/karol/dev/tools/HoldSpeak/pm/roadmap/holdspeak/THE-TUESDAY-ARC.md:54
E           docs/internal/inventory-2026-09-19/06-check-astra.md:91: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/UX-CANON.md:30
E           docs/internal/inventory-2026-09-19/06-check-astra.md:91: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:29
E           docs/internal/inventory-2026-09-19/06-check-astra.md:93: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:54
E           docs/internal/inventory-2026-09-19/06-check-astra.md:93: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:66
E           docs/internal/inventory-2026-09-19/06-check-astra.md:93: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:75
E           docs/internal/inventory-2026-09-19/06-check-astra.md:95: -> /Users/karol/dev/tools/HoldSpeak/holdspeak/db/intel.py:361
E           docs/internal/inventory-2026-09-19/06-check-astra.md:97: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:56
E       assert not ['docs/internal/checks/constitution-seven-tenets-astra.md:14: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTI...cks/constitution-seven-tenets-astra.md:20: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:163', ...]

tests/unit/test_doc_drift_guard.py:269: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_doc_drift_guard.py::test_docs_do_not_restore_retired_inference_setup_vocabulary
FAILED tests/unit/test_doc_drift_guard.py::test_no_live_doc_has_a_dangling_relative_link
2 failed, 170 passed in 23.36s
```

### Captured run — 2026-09-19T22:49:25Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.eaNJRa6vBp uv run pytest -q tests/unit/test_product_copy.py tests/unit/test_product_language.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_ux_canon_scan.py tests/unit/test_phase200_canon_guard.py tests/unit/test_phase200_doc_claims.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_doc_drift_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 88e26388e8d14d6b566323e06061215c035832b5

```text
........................................................................ [ 41%]
........................................................................ [ 83%]
............................                                             [100%]
172 passed in 23.24s
```

## The ten rows

Acceptance criterion 1: *each of the ten rows is fixed (file:line) or
justified; the evidence table says which.* The ten are the rows of
`audits/face-walk-opus.md:45-54` ("Labels not in ASD-STE100"), in that
order. Row 7 carries four labels, so it is split into 7a/7b/7c. Every
"file:line now" is this branch (`feat/hs-201-b`) after the counsel fix
round of 2026-09-19. Shot names are in
`assets/story-06-shots/`, each captured at **both** 1440 and 393.

| # | Audit row (label · where the audit found it) | Disposition | file:line now | Shot |
|---|---|---|---|---|
| 1 | "Tap to speak, edit here, then use" · `FirstWords.tsx:356` | **Fixed** → "Speak. Then edit and keep your text." Two short sentences, each an instruction. | `web/src/desk/components/FirstWords.tsx:359` | `arrival-first-words-1440.png`, `arrival-first-words-393.png` |
| 2 | `RETAINED 0 SEG` · `MeetingIntelRecovery.tsx:135` | **Fixed** → whole words through `countToken`: `KEPT 3 SEGMENTS`. A zero prints nothing at all (UX-CANON A8: no counters of zero); the empty record says "No transcript" on its own line instead. | `web/src/meetings/MeetingIntelRecovery.tsx:49` (`keptToken`), `:177` | `record-kept-segments-1440.png`, `record-kept-segments-393.png`, `record-empty-no-zero-counter-1440.png`, `record-empty-no-zero-counter-393.png` |
| 3 | `REMAINING: … ROUTED ARTIFACTS` · `MeetingIntelRecovery.tsx:138` | **Fixed** → `NOT DONE: SUMMARY, TOPICS, ACTION ITEMS`. "Routed" is dropped: the user never asked for a route. | `web/src/meetings/MeetingIntelRecovery.tsx:65` (`remainingWords`), `:180` | `record-empty-no-zero-counter-1440.png`, `record-empty-no-zero-counter-393.png` |
| 4 | `INTELLIGENCE FAILED` / `INTELLIGENCE` for "summary" · `MeetingHeader.tsx`, `MeetingIntelRecovery.tsx:125` | **Fixed** → the axis is `SUMMARY` on the ledger row (`SUMMARY FAILED`) and the record's group is "Summary". The wire keeps the word "meeting intelligence"; no face says it. Registered: `terms.summary` in `docs/product-language.json`. | `web/src/pages/cores/history/helpers.ts:89`; `web/src/meetings/MeetingIntelRecovery.tsx:164`; `docs/product-language.json` | `meetings-ledger-1440.png`, `meetings-ledger-393.png`, `record-kept-segments-1440.png`, `record-kept-segments-393.png` |
| 5 | "no intelligence can run" · `meeting_intel_service.py:41` | **Fixed** → "This meeting has no transcript. No summary can run." The face closes the first sentence before adding its own ("The Meeting and completed work remain saved."), so the two no longer read as one run-on line. | `holdspeak/services/meeting_intel_service.py:41`; `web/src/meetings/MeetingIntelRecovery.tsx:96-102` (`twoSentences`) | `record-retry-refusal-1440.png`, `record-retry-refusal-393.png` |
| 6 | `7 WAITINGS` · `ConciergeCore.tsx:388` | **Fixed at the source** → `countToken` cannot pluralise a state word, so the token reads `7 WAITING` wherever it is used (AC2's fence; proven red before the fix, see "Captured run" below). | `web/src/desk/surface/count.ts:18-39`; caller `web/src/features/concierge/ConciergeCore.tsx:388` | `models-waiting-1440.png`, `models-waiting-393.png` |
| 7a | "Develop a thought" · `ChairHome.tsx:2078` | **Fixed by the story 01 worker this round** → "Write a thought". `ChairHome.tsx` is that worker's file for this round (Muad'Dib's response 5, `checks/laneb-built-astra.md:40`); this lane shot the result on the path instead of editing the file. | `web/src/desk/chair/ChairHome.tsx:2176` | `chair-meeting-row-1440.png`, `chair-meeting-row-393.png` (the dock) |
| 7b | "Settle in" · `verbRegistry.ts:245` | **Fixed** → "Hide the menus" (and "Back to Desk" when they are already hidden). | `web/src/desk/verbRegistry.ts:247`; `web/src/pages/cores/ChangePlacesCore.tsx:57` | `desk-menu-hide-the-menus-1440.png`, `change-places-hide-the-menus-1440.png`, `change-places-hide-the-menus-393.png` |
| 7c | "Places", "Panes" · `verbRegistry.ts` | **Justified, not changed.** Both are the owner's own words for his Desk furniture (Workbench 2.0 vocabulary), they name one thing each, and neither is on the meeting path this story scopes. Renaming his nouns is his call, not a worker's. | `web/src/desk/verbRegistry.ts` (dock) | `trust-window-heads-1440.png` (the dock carries both) |
| 8 | "Boundary / Authority / Background / Revoke / Last receipt" · `TrustWindow.tsx` | **Fixed** → "Where it goes / Data / Allowed by / Runs without you / **How to stop sending**". The fix round renamed the last head from "How to stop it": the row stops the transfer off this device, not the work itself (Astra finding 5), and the text under it was reworded to say so in plain words for the two runtime destinations. "Last receipt" is **justified, not changed**: Receipt is a registered product term (`docs/product-language.json`, `terms.receipt`). | `web/src/desk/components/TrustWindow.tsx:136-143`; `docs/trust-destinations.json:4-5` | `trust-window-heads-1440.png`, `trust-window-heads-393.png` |
| 9 | "Untitled meeting" · `api.ts:436` | **Fixed** → "Meeting with no title" (no `un-` prefix). The Chair's own copy of the fallback was fixed in the same round by the story 01 worker, who owns `ChairHome.tsx`. | `web/src/desk/api.ts:437`; `web/src/desk/intelligenceAttention.ts:94`; `web/src/desk/chair/ChairHome.tsx:1795` (the 01 worker's edit) | `chair-meeting-row-1440.png`, `chair-meeting-row-393.png` |
| 10 | "Meeting intelligence is awaiting Stop settlement" · `meeting_intel_service.py:41` | **Ledgered to lane A, not fixed here.** `holdspeak/**` is lane A's this round (Muad'Dib's response 5). The literal sits at three sites — `holdspeak/services/meeting_intel_service.py:41`, `:67`, `:131` — and a fence matches the phrase at `tests/unit/test_meeting_deferred_admission.py:727` and `:729`, so all five move together. Unchanged on this branch. | `holdspeak/services/meeting_intel_service.py:41,67,131` | none (the state needs a live Stop race; never observed in this walk) |

Two disclosures that are not one of the ten:

- The Trust window still titles the first destination section **MEETING
  INTELLIGENCE** — that string is the destination *name* in
  `docs/trust-destinations.json:4`, not a column head, and it was not in
  the audit's ten. It is visible in `trust-window-heads-1440.png`.
  Ledgered, not changed: renaming a registry destination reaches the
  doctor and `docs/SECURITY.md`, which is wider than this story.
- The `SUMMARY` column break on the empty record
  (`record-empty-no-zero-counter-*.png`) is inherited layout and belongs
  to HS-201-04 (Astra finding 6; Muad'Dib's response 6).

## Counsel fix round

2026-09-19, after `checks/laneb-built-astra.md` (Astra findings 5, 6, 7
and Muad'Dib's response). Three things changed in this lane:

1. **The ten-row table above** now lives in this evidence file, which is
   what acceptance criterion 1 asks for. The rows handed to others are
   named as handed (7a and 9 to the story 01 worker, who owns
   `ChairHome.tsx` this round; 10 ledgered to lane A, which owns
   `holdspeak/**`), with their file:line.
2. **"How to stop it" → "How to stop sending"**
   (`web/src/desk/components/TrustWindow.tsx:142`). The column advises
   moving the work onto this device, which does not stop the work — it
   stops the sending. The two runtime rows under it were reworded to say
   that in plain words (`docs/trust-destinations.json:4-5`):
   "Use a model on this device for summaries, or stop summaries. Then no
   transcript goes out." and the same shape for dictation. The other
   five destinations already named a deletion that ends the sending
   ("Delete the Slack secret in Settings"), and read correctly under the
   new head; they were left alone. A vitest holds the head set and the
   text under it:
   `web/src/desk/components/__tests__/trustWindowHeads.test.tsx`. It was
   proven red first — with the head put back to "How to stop it" both
   its tests fail (`Test Files 1 failed (1) · Tests 2 failed (2)`), and
   the file was restored before the green run below.
3. **393 shots for every station.** `assets/story-06-shots/story06_walk.py`
   now runs its seven stations once per viewport (1440x900, then
   393x852) and names each file `<station>-<width>.png`. Two things the
   second width forced into the runner, both honest rather than
   papered over:
   - The first-run arrival is `first_run AND no onboarding disposition`
     (`holdspeak/setup_status.py:291`), and crossing the gate writes a
     disposition — so the second pass would never see the arrival card.
     `reset_arrival()` clears that row in the **scratch** DB between
     passes.
   - At phone width every verbbar item but Go is `display:none`
     (`web/src/desk/components/chrome-menus.css:888`), so there is no
     Desk menu to open at 393. That station shoots the bar that does
     exist (`desk-menubar-go-393.png`) and says why; "Hide the menus"
     itself is shot at 393 in Change places.
   - A phone-width record fills the surface, so the runner returns to
     the ledger before opening each record instead of assuming the
     desktop's two columns.

Result: **20 shots, 0 FAILS, exit 0** (ten shots at each width; station
2 carries a different file name at 393 for the reason above).

```text
============================================================
SHOTS: 20  FAILS: 0
  arrival-first-words-1440.png  (Speak. Then edit and keep your text.)
  desk-menu-hide-the-menus-1440.png  (Hide the menus (was: Settle in))
  chair-meeting-row-1440.png  (the Chair's no-title fallback, in plain words)
  change-places-hide-the-menus-1440.png  (Hide the menus (was: Settle in))
  meetings-ledger-1440.png  (the ledger after the words changed)
  record-kept-segments-1440.png  (KEPT 3 SEGMENTS (was: RETAINED 3 SEG))
  record-empty-no-zero-counter-1440.png  (NOT DONE (no routed artifacts); no RETAINED 0 SEG)
  record-retry-refusal-1440.png  (two sentences, each closed (was one run-on))
  trust-window-heads-1440.png  (Where it goes / Allowed by / Runs without you / How to stop sending)
  models-waiting-1440.png  (N WAITING (was: 7 WAITINGS))
  arrival-first-words-393.png  (Speak. Then edit and keep your text.)
  desk-menubar-go-393.png  (the phone menu bar: Go only, no Desk menu at this width)
  chair-meeting-row-393.png  (the Chair's no-title fallback, in plain words)
  change-places-hide-the-menus-393.png  (Hide the menus (was: Settle in))
  meetings-ledger-393.png  (the ledger after the words changed)
  record-kept-segments-393.png  (KEPT 3 SEGMENTS (was: RETAINED 3 SEG))
  record-empty-no-zero-counter-393.png  (NOT DONE (no routed artifacts); no RETAINED 0 SEG)
  record-retry-refusal-393.png  (two sentences, each closed (was one run-on))
  trust-window-heads-393.png  (Where it goes / Allowed by / Runs without you / How to stop sending)
  models-waiting-393.png  (N WAITING (was: 7 WAITINGS))

NOTES:
  - [1440] the Chair's fallback reads 'Meeting with no title' (ChairHome.tsx, the story 01 worker's edit this round)
  - [393] no Desk menu on the phone menu bar (chrome-menus.css:888 hides every verbbar item but Go); 'Hide the menus' is shot at this width in Change places
  - [393] the Chair's fallback reads 'Meeting with no title' (ChairHome.tsx, the story 01 worker's edit this round)
```

The walk ran against a bundle built from the shared tree, so the Chair
shots also carry the story 01 worker's in-flight edits to
`ChairHome.tsx` (that is what rows 7a and 9 show). Nothing outside the
scratch HOME was written; no microphone was opened.

Not verified in this round: the full suite (the orchestrator's, in the
quiet tree — Muad'Dib's response 7); a successful summary on a real
model; row 10's "awaiting Stop settlement" state, which needs a live
Stop race.

The re-run of the same checks follows.

### Captured run — 2026-09-19T23:10:43Z

- **Command:** `sh -c cd web && npx vitest run src/desk/surface/__tests__/count.test.ts src/meetings/MeetingIntelRecovery.test.tsx src/pages/cores/__tests__/ChangePlacesCore.test.tsx src/desk/components/__tests__/trustWindowHeads.test.tsx 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f541048b1df5ba8187af7ba0694220c6623e53c2

```text

 Test Files  4 passed (4)
      Tests  20 passed (20)
   Start at  17:10:44
   Duration  2.45s (transform 1.00s, setup 1.03s, import 1.87s, tests 753ms, environment 4.09s)
```

### Captured run — 2026-09-19T23:10:50Z

- **Command:** `sh -c cd web && npx tsc --noEmit && echo "tsc: no errors"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f541048b1df5ba8187af7ba0694220c6623e53c2

```text
tsc: no errors
```

### Captured run — 2026-09-19T23:11:05Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.vWFaBTloMn uv run pytest -q tests/unit/test_product_copy.py tests/unit/test_product_language.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_ux_canon_scan.py tests/unit/test_phase200_canon_guard.py tests/unit/test_phase200_doc_claims.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_doc_drift_guard.py tests/unit/test_trust_destinations.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f541048b1df5ba8187af7ba0694220c6623e53c2

```text
........................................................................ [ 41%]
........................................................................ [ 82%]
...............................                                          [100%]
175 passed in 23.26s
```

### Captured run — 2026-09-19T23:11:35Z

- **Command:** `sh -c tail -32 /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/a656696c-d9eb-491f-8d02-7b5a6518db89/scratchpad/walk3.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f541048b1df5ba8187af7ba0694220c6623e53c2

```text
  PASS  [393] concierge surface opened
  PASS  [393] no invented plural  Models · No engine yet · THIS MAC · M‑SERIES · CHECKED 5:07 PM · FOUND · Add an engine... · THE SET · Adjust · • · Thoughts & notes · — · ○ · WAITING · ■ · Chat · — · ○ · WAITING · – · Writing & dictation · — · ○ · WAITING · ∕ · Speech recognition · — · ○ · WAITING · ■ · Meetings · — · ○ · WAITING · ◦ · Age
  PASS  [393] waiting token present  Models · No engine yet · THIS MAC · M‑SERIES · CHECKED 5:07 PM · FOUND · Add an engine... · THE SET · Adjust · • · Thoughts & notes · — · ○ · WAITING · ■ · Chat · — · ○ · WAITING · – · Writing & dictation · — · ○ · WAITING · ∕ · Speech recognition · — · ○ · WAITING · ■ · Meetings · — · ○ · WAITING · ◦ · Age
  SHOT  models-waiting-393.png  (N WAITING (was: 7 WAITINGS))

============================================================
SHOTS: 20  FAILS: 0
  arrival-first-words-1440.png  (Speak. Then edit and keep your text.)
  desk-menu-hide-the-menus-1440.png  (Hide the menus (was: Settle in))
  chair-meeting-row-1440.png  (the Chair's no-title fallback, in plain words)
  change-places-hide-the-menus-1440.png  (Hide the menus (was: Settle in))
  meetings-ledger-1440.png  (the ledger after the words changed)
  record-kept-segments-1440.png  (KEPT 3 SEGMENTS (was: RETAINED 3 SEG))
  record-empty-no-zero-counter-1440.png  (NOT DONE (no routed artifacts); no RETAINED 0 SEG)
  record-retry-refusal-1440.png  (two sentences, each closed (was one run-on))
  trust-window-heads-1440.png  (Where it goes / Allowed by / Runs without you / How to stop sending)
  models-waiting-1440.png  (N WAITING (was: 7 WAITINGS))
  arrival-first-words-393.png  (Speak. Then edit and keep your text.)
  desk-menubar-go-393.png  (the phone menu bar: Go only, no Desk menu at this width)
  chair-meeting-row-393.png  (the Chair's no-title fallback, in plain words)
  change-places-hide-the-menus-393.png  (Hide the menus (was: Settle in))
  meetings-ledger-393.png  (the ledger after the words changed)
  record-kept-segments-393.png  (KEPT 3 SEGMENTS (was: RETAINED 3 SEG))
  record-empty-no-zero-counter-393.png  (NOT DONE (no routed artifacts); no RETAINED 0 SEG)
  record-retry-refusal-393.png  (two sentences, each closed (was one run-on))
  trust-window-heads-393.png  (Where it goes / Allowed by / Runs without you / How to stop sending)
  models-waiting-393.png  (N WAITING (was: 7 WAITINGS))

NOTES:
  - [1440] the Chair's fallback reads 'Meeting with no title' (ChairHome.tsx, the story 01 worker's edit this round)
  - [393] no Desk menu on the phone menu bar (chrome-menus.css:888 hides every verbbar item but Go); 'Hide the menus' is shot at this width in Change places
  - [393] the Chair's fallback reads 'Meeting with no title' (ChairHome.tsx, the story 01 worker's edit this round)
```
