# HANDOVER — 2026-06-29 — The meeting drawer (detail redesign + derivatives + iPhone filing)

Owner asks (device walk): the meeting **detail** and the **"full editor"** are "pretty terrible"; a
recorded meeting should become a **drawer** holding all its derivatives; and on **iPhone there's no way
to drag a meeting to a zone**.

## Decisions (owner, 2026-06-29)

1. **Drawer model = group by lineage.** Derivatives (outputs) stay normal primitives but DISPLAY inside
   their meeting's drawer, matched by the back-link they already store (`OutputRecord.provenance.sourceCardId`
   == `"m:<meetingId>"`, or `OutputRecord.source` == the meeting title). No data migration; filing the
   meeting carries them. Reversible.
2. **Detail shape = in-world pull-out.** The meeting opens on the desk like every other primitive (the
   `DioPullout`), NOT a jarring full-screen `.sheet` (today it's `MeetingDetailView` via `openMeeting`).
   Derivatives as cards inside; transcript + notes one tap deeper.
3. **iPhone filing = long-press → File into…** Reuses the existing `file()`/membership path.

## Plan (sequenced)

- **PR 1 — iPhone filing (DONE).** A `.contextMenu` on `DioLaneRow`: Open + "File into…" listing every
  zone (+ Desk root, + "New zone…" which files into the freshly created zone via `pendingFileId`).
  Extracted `fileAny(_ id:into:)` (shared by drag-drop + the menu), `currentPath(of:)`,
  `allZonePaths()`. Lane empty-hint copy fixed ("Long-press any item to file it" — the old "Drag a
  meeting here" was a lie on the phone). Builds; the menu is a device walk (simctl can't long-press).
- **PR 2 — meeting drawer grouping.** Filter a meeting's derivatives OUT of the loose desk/lane lists
  (`contentMembers()`/`members()`) and surface them as the meeting's children: the meeting row/card
  shows a derivative count; `membersOfMeeting(m)` returns the matched outputs. Match by
  `provenance.sourceCardId == "m:\(m.id)"` first, then `source == m.title`.
- **PR 3 — the in-world drawer UI + detail/editor redesign.** Route a meeting tap to an in-world
  pull-out (reuse/extend `DioPullout`) showing: header (title/when/who/duration) → derivative cards
  (open/keep/dismiss/correct) → Transcript › → Notes ›. Replace the long-scroll `MeetingDetailView`
  sheet. Redesign the artifact "full editor" (`ArtifactDetailView`) too.

## Pointers

- Meeting detail today: `MeetingCaptureApp.swift` `MeetingDetailView` (~1578–1865), shown via a
  `.sheet` bound to `openMeeting` (`DeskDioramaStage.swift` ~3873).
- Artifact "full editor": `ArtifactDetailView` (sheet from `MeetingDetailView`).
- Derivative model: `OutputRecord` (`DeskPrimitive.swift` ~250) — `source` (meeting TITLE),
  `provenance.sourceCardId` (the `"m:<id>"` primitive id when routed).
- Loose-derivative rendering: `contentMembers()` (`DeskDioramaStage.swift` ~2983).
- In-world pull-out: `DioPullout` (used for `selectedPrim()`).
- Filing: `fileAny`/`file`/`drop`/`trayHit` in `DeskDioramaStage.swift`.
