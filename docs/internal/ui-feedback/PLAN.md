# Local audio feedback on the Desk

Owner request, 2026-10-20: an environment flag enables spoken feedback about a selected interface element, with the window state and a screenshot attached to every report. This is a new owner development tool, not another betterment recipe slice.

## Settled experience

`HOLDSPEAK_UI_FEEDBACK=1` enables **Desk > Give feedback** and its shared command-deck verb. It is absent by default. Choose the verb, then select an element. The selection consumes the press: it must not activate the element, submit a form, or move a window. Escape cancels. The selected element identifies its existing Desk window; Desk chrome can use the Desk root as a fallback.

Freeze the selected element, owning window, current rendered text and form values (including unsaved drafts), selected tabs, scroll positions, viewport and canonical window row at selection. Capture a PNG of that window before feedback controls appear. Keep field geometry and a selected-element rectangle so the developer can locate the target in the image. Passwords, credential fields and authentication URL parameters are excluded. Do not serialize the entire app store, Config, credentials, or unrelated database rows.

A small existing-material feedback strip then names the window, shows LOCAL and the capture state, and offers **Stop and save** and **Cancel**. There are no modals. Recording uses the existing single microphone session, its token-owned hold, WAV encoder and leased audio floor. It must not steal an active same-tab capture or a meeting microphone. Late permission, cancellation, unmount and floor loss release only this capture. Save failures retain the same audio, context and screenshot for Retry; retry must not take a newer screenshot. Saving succeeds without an engine or transcription provider. A report contains the original WAV, PNG and JSON; no automatic model calls or external delivery.

## Storage and wire

GET `/api/ui-feedback/status` -> `{enabled: boolean}`. Read the runtime flag, not a build-time Vite flag, so the normal checked bundle serves both states.

POST `/api/ui-feedback` -> body `{id, captured_at, context, audio_base64, screenshot_base64}`; id is a client-generated 32-character lowercase hexadecimal UUID retained for Retry. `context` is a JSON object. The image is required and is PNG; audio is a readable 16 kHz mono PCM WAV. Existing owner edge authentication applies. A disabled write returns 404. A successful write returns `{success: true, id, directory, files}`. A repeated identical request returns that same report; an identifier with different content returns 409.

Reports live in `~/.local/share/holdspeak/feedback/<id>/`: `report.json`, `audio.wav`, `window.png`, and a concise `README.md` for a developer. The server supplies its runtime/build identity and save time. No new database or queue. A saved receipt names the report and Copy path; it never says Saved until all attachments are durable. Files are private to the owner. Failed writes must not publish a complete report.

## Tuesday and the Seven Tenets

The owner can point at a broken control, explain it once and carry on. One opt-in verb, one local bundle and reuse of the Desk and mic serve tenets 1–3 and 5–7. Interface words use simple English (tenet 4). The owner judges the built face live under CLAUDE.md fast cycle; canvas.html settles the compact strip before implementation.

## Validation budget

Backend: `tests/integration/test_desk_ui_feedback.py`, actual authenticated routes and isolated HOME, flag off/on, durable attachments, exact retry, differing retry, invalid attachments and failed write. Frontend: `web/src/desk/feedback/feedback.app.test.tsx`, selection without activation, frozen draft values and secret exclusions, same capture retry, microphone ownership/cancel. The actual producer supplies recorded status/save replies used by any transport doubles. One scoped browser file is justified for element picking, a real PNG and 1440/393 hit ownership; use fake audio hardware only in an isolated hub. Root runs the required quick check against the fixed main base; all validation uses scripts/test_lock.py and isolated HOME. Workers hold for SHIP and never stage or commit.
