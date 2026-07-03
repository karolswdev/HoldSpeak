# Evidence — HSM-19-03 — Meeting import on the iPad

**Status:** done (2026-07-03), on `holdspeak-mobile/hsm-19-03-meeting-import`. The
multipart client (`013c7d0`) gains its surface: a recording or transcript on the iPad
becomes a real meeting in the hub's full intel pipeline.

## 1. The import surface (`CompanionShellApp.swift`)

- **"Import file"** beside Start meeting opens `.fileImporter` scoped to audio +
  `.vtt/.srt/.txt` (the exact set the hub parses).
- **Security-scoped access done right:** the read happens inside
  `startAccessingSecurityScopedResource()`, and the REAL `lastPathComponent` rides the
  part — the hub validates by suffix and titles the meeting from the stem (the HS-57
  temp-stem lesson, honored from the client side).
- **The honest states:** Uploading… while in flight; "Importing on your desktop" on the
  202 (and the list reloads so the new row appears); a 400 maps to the format/empty
  reason; unreachable is named. A meeting row whose `intel_status` is `importing` wears a
  live spinner mark; `import_failed` stays visible in red — the failure never disappears.
- New screenshot-run affordance `HS_SHELL_IMPORT_FILE=<path>` — uploads on launch through
  the SAME `importFile` path the picker calls.

## 2. The live-hub proof (real routes, scratch DB + scratch CONFIG)

```
1. POST .vtt   -> 202; {'meeting_id': '7dc77e8b', 'status': 'importing'}
2. meeting     -> title='phase19-kickoff', intel_status={'state': 'queued', …}, segments=3, speakers=['Dana', 'Karol']
3. POST .pages -> 400; the hub's own list of supported formats
4. POST empty  -> 400; 'The uploaded file is empty.'
```

(Check 2 confirms the known gotcha stands: the detail endpoint NESTS `intel_status`; the
iPad's summary read uses the flat list shape, unaffected.)

**Then the app itself imported a file end to end** — the running simulator uploaded
`imported-from-the-ipad.vtt` through `importFile` → the real route → the parser:
[`hsm-19-03-live-hub-import.png`](./screenshots/hsm-19-03-live-hub-import.png) shows the
new `imported-from-the-ipad` row above the curl-imported `phase19-kickoff`, the
"Importing on your desktop" note, and the 19-02 facet chips already carrying the
speakers (Dana, Karol) parsed from the uploaded file — the import feeding the archive's
facets live, on one screen.

## Honest boundaries

- The Files-sheet **tap** is not simulatable headlessly; the launch-time upload exercised
  the identical code path. The on-device pick rides the 19-07 walk (W3).
- An **audio** import needs Whisper on the hub (and ffmpeg for non-WAV); the live proof
  used the pure transcript path. A real-audio import is exactly the walk's W3 with a
  recording.

## Suites

`swift test` **425 passed / 8 skipped / 0 failures** (`MeetingImportClientTests` lock the
multipart body + decode) · companion-shell simulator build (iPad Air 13-inch M4)
**BUILD SUCCEEDED** — both after the change.
