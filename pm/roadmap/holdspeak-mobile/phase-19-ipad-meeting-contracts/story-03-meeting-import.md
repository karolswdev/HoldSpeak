# HSM-19-03 — Meeting import on the iPad: the picker over the multipart client

- **Project:** holdspeak-mobile
- **Phase:** 19
- **Status:** todo (the client half is merged — commit `013c7d0`)
- **Depends on:** `HTTPDesktopClient+MeetingImport.swift` (`importMeeting(fileURL:filename:mimeType:)`);
  hub route `POST /api/meetings/import` (`holdspeak/web/routes/meeting_import.py:146` —
  one multipart field `file`, suffix-validated, returns `202 {meeting_id, status:"importing"}`).
- **Unblocks:** recordings and transcripts that live on the iPad (Files, AirDrop, the
  on-device recorder's exports) reaching the hub's full intel pipeline.
- **Owner:** unassigned

## Problem

The hub imports audio (HS-55) and transcripts (HS-57) into real meetings; the iPad — the
device most likely to be holding a stray recording — has no way to hand one over. The
multipart client shipped and has **zero callers**; the only `.fileImporter` in the codebase
is GGUF-gated (`ModelManager.swift`).

## The design

1. **An "Import a recording or transcript" action on the DESKTOP card** opening
   `.fileImporter` scoped to audio + `.vtt/.srt/.txt` content types.
2. **Security-scoped access done right:** the picked URL is read inside
   `startAccessingSecurityScopedResource()`; the REAL filename rides the multipart part
   (the hub validates by suffix and titles the meeting from the stem — never send the
   temp path's name).
3. **The visible importing state:** on `202`, the meeting appears in the list with an
   `importing` mark; refresh shows it move to done or `import_failed` (the failure stays,
   honestly labeled — the hub's own error body is surfaced on a non-2xx).
4. **Egress-honest:** the file goes to the paired desktop, nothing else — the existing
   card-level egress language covers it (no privacy prose).

## Scope

- **In:** the picker, the upload, the importing/failed states in the list, hub-error
  surfacing, sim proof.
- **Out:** hub-side changes (routes shipped); polling infrastructure beyond the existing
  list refresh; on-device transcription of the file (that is the desk app's domain).

## Test plan

- `swift test` green (multipart body building is already covered by `*ClientTests`).
- Sim proof: pick a fixture `.vtt` from Files in the simulator → screenshot of the
  importing state; a rejected `.pages` showing the hub's own error message.
