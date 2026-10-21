# Settings and Automation builder — owner feedback, 2026-10-21

Source reports (read-only): `46bda55a89ce3feb83e0e79e77b71e9a` (Automation builder) and `b3a536d4972f39390bd9e5ce7fb88937` (Settings), under the owner feedback directory. Both include original audio, configured-engine transcripts, window PNGs and context. The owner explicitly requests a wizard for building automations, and less information, pictograms and better dropdowns in Settings.

Tuesday: the owner can complete one Automation setting at a time, or find and change one preference without scanning unrelated categories. Tenets 2, 3, 5 and 6 govern this change. This is not a claim of whole-product aesthetic acceptance.

Setup MCP context read: owner-started Codex used the installed connection.
`project.list` has no HoldSpeak project reference (`project.get` therefore has
no applicable id); `memory.search` supplied no newer matching brief. The owner
reports and repository canon settle this scope. Review helper access is checked
on built work, with any refusal recorded honestly in the PR review.

## Settled face canvas — before build

Static direction: [canvas](canvases/settings-builder-2026-10-21.html).

Material: existing Workbench paper, steel chrome, ink rules, blue selected state and existing pixel sprites. Library Button and existing gadgets; no new framework, modal, provider, or backend data model.

Automation (920×680 desktop, contained at 393): a compact pictogram step rail, a single paper editor well, and Back / Next navigation. Five steps: Do, About, With, When, Put it in. A blank, result-free scratch automation opens at Do. Existing configured automations keep their working summary and results, with a visible Edit setup verb to enter the same wizard. The current step is named in a clear heading with its sprite. No empty Results crater during setup. Keep entered drafts when going Back. Next must save the Do draft successfully before moving on; no run occurs from navigation. Other editors keep their existing immediate-save operations and errors; navigation cannot advance during a pending write or refusal. The last step finishes setup and shows the saved summary and the explicit Run now action. Persist no extra automation or fake completion data. Keep current actual egress chips in engine and destination choices, agent admission, run refusal, result history, sources and old-queue operations. Future step visits are allowed through the rail only when they cannot discard a dirty draft. Run now remains disabled while guided setup is open. Existing templates and saved automations preserve their normal editor path. Improve the summary with the same pictograms and paper grouping.

Settings (880×528 desktop, contained at 393): narrow pictogram category rail on the left; one category visible in a paper reading pane. At narrow widths the eight pictogram choices wrap as a compact grid above the pane, with 44px targets. Initial category You. Preserve all mounted category children under hidden sections so unsaved local inputs survive navigation; hidden contents leave keyboard/a11y navigation. Category selection is real view selection, not document scrolling. Keep stable section ids, scope aliases and row highlights; reset the window scroll when selecting a category. Default You shows identity only; unrelated Speak/Meetings/etc do not fill the view. Remove repeated category/group titles where they repeat the same name. Group relevant controls using existing library materials and show sprites next to category names. Shared CycleGadget remains the single dropdown implementation; improve Settings closed-face dropdown affordance and custom popup readability using existing library hooks, preserving keyboard, native form, disabled and value behavior. No horizontal scrolling inside the window.

The saved feedback receipt also gets a library Done button. Firefox glass
showed that the receipt otherwise sits over the next form controls, especially
at 393. Done dismisses only the receipt through the existing cancellation/UI
reset; the saved report files stay intact. This is a small seam repair needed
to resume editing after reporting either face.

## Lanes and verification

All work: `/Users/karol/dev/tools/wt-settings-builder-delight-20261021`, branch `feat/settings-builder-delight-20261021`, base main `83d790151`. Line anchors drift; locate symbols.

Automation worker owns `web/src/desk/components/automation/{AutomationWindow,SentenceLine}.tsx`, `automation.css`, any new colocated guided UI component, and focused `web/src/desk/__tests__/automation.app.test.tsx`. Settings worker owns `web/src/pages/cores/SettingsCore.tsx`, `settingsPrefs.tsx`, `settings.css`, `settingsSurfaceRepair.css`, focused Settings tests and, only where needed, existing CycleGadget/WorkbenchSelect styling. Neither owns the other lane. Astra owns this record, browser tests and delivery/status integration.

Workers hold for SHIP; no stage/commit, tests/build/typecheck/model probes until orchestrator freezes all tracked source. Every validation uses the machine test lock and isolated HOME, focused tests only, never metal or owner desk writes. Check 1440 and 393 real private-Hub glass, including Firefox, actual navigation, saved values and screenshot capture. Required quick green precedes PR merge; exact merged runtime is then deployed and reviewed under CLAUDE.md fast cycle. Full tape runs afterward. Report limitations honestly.

## Built checks and limits

The first focused web check passed 151 cases in nine files; a direct blank-Do
rail regression was then added. Build and typecheck passed after the final
source changes. Firefox glass completes the real wizard, saves its source,
engine and output target, checks that no run occurred, saves both window
reports, dismisses their receipts and verifies category selection and language
persistence at 1440 and 393. Existing automation result/agent flows also ran.
Evidence: `.tmp/evidence-shots/settings-builder-feedback/`, and saved window
PNGs in `.tmp/evidence-shots/ui-feedback/`.

The absolute Firefox capture timing check is now marked slow and run separately
under the machine lock, with its 3-second capture and 1-second heartbeat limits
unchanged. Eight simultaneous browser jobs produced one 3.476-second capture
and 1.186-second gap; the separate two-case run passed all six captures, at
1.102–1.541 seconds and gaps at most 368 ms. Fake Firefox microphone startup
gets 1.2 seconds to deliver frames, preserving the 100 ms WAV minimum. This
keeps host contention distinct from product capture regression. The full main
tape includes the slow cases. Required quick still runs the actual new Firefox
form, save, screenshot, receipt and persistence paths alongside the Chromium
regressions.

Setup MCP review helper returned `launch_only` (403), because this owner-started
session has no launched task item. The local Luna review under AGENTS is an
independent fallback, not Muad'Dib's check. It found a required-Do rail bypass
and mismatched category sprites; both were fixed before the required quick.
The owner judges aesthetic acceptance on the deployed desk.

The first required quick passed 4,117 web cases, 13 affected browser cases and
110 sweep cases, then caught an accent border, the fixed five-step total's
unguarded length expression, incomplete save-failure copy and the new guided
component's missing route census entry. The border now uses a complete rule,
the fixed count reads five, failure copy names retained open work, the action
kind reads Make a result, and the builder is classified as display transport
under the existing 143-13 engine authority. No guard ceiling or assertion was
relaxed. The independent local review's second verdict identified the same
border, failure copy and route classification conditions; the final quick
verifies their corrections.
