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
- **PR 2 — meeting drawer grouping (DONE).** `derivativesOf(m)` matches outputs by
  `provenance.sourceCardId == "m:<id>"` or `source == meeting.title`; `meetingDerivedOutputIds` excludes
  them from the loose `contentMembers()` list. `MeetingPrimitive` gained `derivatives: [OutputRecord]`
  and a lead "DERIVATIVES · N" section (`SectionBody.derivatives`), rendered by `DioPullout` as tappable
  cards (`onOpenDerivative` → `select("out:<id>")`); `selectedPrim()` falls back to resolving a hidden
  derivative by id. The meeting subtitle shows "N artifacts". The generic "Route this to AI" button is
  suppressed for the derivatives section. Sim-verified: tap a meeting → its derivatives sit inside;
  they're gone from the loose desk.
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

## Follow-on — desk density (owner: "why even have the tool shelves" + "shrink when crowded")

Both shipped together (one instinct: only content + things you invoke earn a permanent desk spot).
- **#1 declutter:** the lane "All" filter now excludes the "tools" bucket (models / connectors /
  workflows) — they live behind the existing "Tools" chip, surfaced at point-of-use, not as permanent
  rows you can't even drop onto (no drag on the lane). Also makes a dived empty zone genuinely calm.
  The iPad already separated content (canvas) / capabilities (rail) / tools (dock).
- **#2 auto-fit:** `DioHero` gains `densityScale`; `level()` computes `densityScale(ms.count)` (1.0 →
  floor 0.62) and `looseHome` widens (more columns as count grows: 2→3→4→5, y-band 0.30–0.80). A full
  desk spreads + shrinks to a legible floor instead of piling into a cramped middle strip. Past the
  floor, columns keep spreading (no illegible confetti); hierarchy (drawers/zones) is the real scale.
  Sim-verified: lane "All" without tools; 12 notes on iPad → clean 4×3 grid at ~0.70 scale.

## PR 3 — the full editor redesign (DONE)

`MeetingDetailView` (MeetingCaptureApp.swift) was one endless scroll (title → marked moments →
intelligence → transcript → notes) with verbose prose and a back button that overlapped the title.
Redesigned into a **premium segmented editor**:
- A header with its own row for "‹ Desk" + the egress badge (so nothing overlaps the back control),
  then a glyph + title + meta row (date · duration · N speakers).
- A segment bar — **Intelligence / Transcript / Notes** — each a focused pane (no more endless scroll).
  Intelligence = lens picker + type chips + generate + artifact cards; Transcript = marked moments +
  the speaker-coloured `TranscriptView`; Notes = the PencilKit `NotebookView`.
- Prose trimmed: dropped the redundant inner "INTELLIGENCE"+egress header, the lens paragraph blurb,
  and softened the empty hint to "Nothing generated yet."
`ArtifactDetailView` was already clean (styled markdown + "Fix it by voice" + copy/share) — left as is.
Sim-verified all three tabs on the real app (no overlap, focused panes).
