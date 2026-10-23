# native_presence

Job: Show bounded native presence without stealing focus. Baseline: `main555728021` (PR1430; anchors may drift). Reviewer task: `review_native_presence`. Evidence class: source, inventory, assertions, and desk-sweep inventory; no tests/builds, live calls, provider/native actions, owner-state writes, or owner acceptance.

VERDICT: DO-NOT-RATIFY

## Totality

The real job is a transient local status signal while the owner dictates or records in another foreground app: activity starts it, a native boundary shows a truthful state, terminal work lingers or hides, and the owner keeps typing. Recovery must cover a blank WebView, unavailable renderer, disconnect, close, stale activity, and turning it off. Return means no stale panel or meeting state. A `/presence` React card is fallback/inspection, not proof of a native host (`web/src/pages/PresencePage.tsx:14-35`; `holdspeak/runtime/activity.py:35-73`).

FINDINGS:

1. **P0 — A public job is mapped to the wrong workflow.** The inventory assigns “Use a portable client” to `native_presence` (`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:716-719`), but that job starts from a paired device and is hub-backed (`docs/USE_CASES.md:18-20`). The companion boundary separates iPad/AIPI clients from Qlippy, optional Web Desk presence (`docs/COMPANIONS_ARCHITECTURE.md:31-40`); the catalogue separates `companion.ipad_client`, `companion.aipi_audio_control`, and `companion.qlippy_presence` (`docs/CAPABILITIES.md:94-96`). Cost: a worker could implement remote authority/egress as an overlay. This fails Tenets 3, 5, and 7. Correction: map the portable job to an explicit external-client audit bucket tied to catalogue capabilities `companion.ipad_client`/`companion.aipi_audio_control`; those capability IDs are not additional workflow families; keep `native_presence` local and bounded to Qlippy plus runtime activity.

2. **P1 — operationally disabled is not the same as retired code.** Research records the owner’s instruction to keep Presence off after the broken renderer (`docs/internal/betterment/native-experience/CURRENT-STATE.md:102-118`). The source still supports explicit config or legacy force-on environment override (`holdspeak/desktop_presence.py:316-330`) and live config application (`holdspeak/web_runtime.py:385-415`). Configurability is not itself a defect or a reason to add a hard lock. Owner cost: deployment that blindly carries an old force-on override could contradict the saved off preference. This fails Tenets 3 and 7 if the audit conflates source capability with current operation. Correction: preserve the owner’s false setting and avoid force-on deployment overrides. Any future repair uses isolated evidence first; re-enabling the owner’s host still requires his explicit instruction. No new approval framework, retired-adapter migration, or stack experiment is required.

3. **P1 — Seam assertions do not cover the owner’s return.** Fake-renderer tests prove show/update/linger/hide (`tests/unit/test_desktop_presence.py:55-147`), and Cocoa tests prove Stop (`tests/unit/test_desktop_presence_cocoa.py:140-155`), but no assertion establishes foreground focus, blank-panel close, or stale-state clearing. Non-activation is source-only (`holdspeak/desktop_presence_cocoa.py:124-160`), and root cause/close/focus proof remain unknown (`docs/internal/betterment/native-experience/CURRENT-STATE.md:110-116`). This fails Tenets 3, 6, and 7. Correction: preserve seam tests but add falsifiable recovery/return criteria, without launching the disabled host.

## Convergence

Share the `runtime_activity` snapshot and state policy with `speech_dictation` and `meeting_record` (`holdspeak/runtime/activity.py:35-73`; `holdspeak/activity_tracker.py:60-80`), and truthful outcomes with `feedback`. `windows` and `desktop_workspace` own Desk focus/lifecycle; they are related, not a native-overlay merge. Keep `companion.ipad_client` and `companion.aipi_audio_control` separate: their actors, transport, authentication, and egress differ. One activity projection can feed consumers, but merging these IDs makes a local glance surface pretend to be a remote client.

## User experience

Source inference suggests a good fast path: short labels, a status glyph, a passive 408×132 frame, and a non-activating panel (`holdspeak/desktop_presence.py:104-131`; `holdspeak/desktop_presence_cocoa.py:124-160`). The card can become interactive and 460px high, so an implementation must prove it does not cover the owner’s target or steal intent. No native capture was inspected in this review; listed sweeps show Desk surfaces only. Craft, accessibility, timing, and delight remain unknown.

CONDITIONS: Correct the portable-client mapping; document and preserve the disabled operational state; specify activity, renderer failure, close, stale-state, focus, and return contracts. Do not re-enable this host.

MISSED:

1. A deployment override can contradict the owner’s saved off state (highest cost).
2. Portable-client authority and egress are not native-presence behavior.
3. Blank/timeout/close and foreground-focus return are not covered by assertions.
4. A stale meeting or dictation state can survive linger unless the return contract is explicit.

TUESDAY: No—the intended glance is quick, but this audit could send the architect to a broken overlay or the wrong portable-client workflow.

## Acceptance challenges

1. With Presence disabled, start dictation in a foreground editor. No native host launches; the existing runtime activity and delivery path remain usable, and focus stays in the editor.
2. In an isolated future repair harness, inject recording → transcribing → complete → idle. The activity snapshot is ordered once, terminal state lingers once, then clears; the next run has no stale label.
3. Make the renderer unavailable or its WebView blank. Runtime remains alive, the fallback state is named, the panel closes, and the owner can continue typing; no silent green claim appears.
4. Stop a live meeting from its supported native action, then return to the Desk. The same meeting outcome is shown once, no second recording starts, and focus/selection in the foreground app is unchanged.

UNKNOWN: No tests were executed. No live native/portable client, foreground focus, WebKit rendering, close shot, performance trace, accessibility walk, provider action, or owner acceptance was observed; captures are unrelated Desk sweeps. Anchors are baseline-specific.
