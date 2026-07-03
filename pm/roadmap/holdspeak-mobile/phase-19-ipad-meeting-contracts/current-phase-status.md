# Phase 19 — The iPad joins the meeting contracts

**Status:** in-progress (opened 2026-07-03) — the Equilibrium program's designed pair to
Phase 18 ([`EQUILIBRIUM.md`](../EQUILIBRIUM.md)), the meetings half of audit theme 2.

**Last updated:** 2026-07-03 (**OPENED, survey-corrected.** The 2026-06-27 draft described a
pre-work state; in reality the **entire client layer already landed and merged** via
Equilibrium Waves 3–6 + two follow-ups (PRs #151, #155, #156, #159; commits `013c7d0`
import, `8f65657` learning). Every story's `HTTPDesktopClient` extension + Contracts type
exists; 19-04 is fully wired and sim-proven; 19-01's read card is live. What remains is
**UI wiring in `CompanionShellApp.swift`** plus the write/action flows and the staged metal
walk. Stories re-grounded below against the shipped code.)

## Why this phase exists

The same imbalance as Phase 18, on the meetings side: the hub serves the full meeting
contract; the iPad reads almost none of it *on screen*. Post-survey, the verified holes are
all presentation-layer:

- **Aftercare file-issue** is a client method with no button
  (`fileAftercareIssue` in `HTTPDesktopClient+Aftercare.swift:37` has zero callers); the
  card renders the digest but cannot close the loop.
- **The faceted archive** has clients (`listFacets()` / `searchMeetings(query:speaker:type:)`)
  and no UI — the live list path is still `listMeetings()` with zero query params.
- **Meeting import** has a multipart client (`importMeeting(fileURL:filename:mimeType:)`)
  and no picker; the only `.fileImporter` in the codebase is GGUF-gated.
- **Proposals review** has clients (`meetingProposals` / `decideProposal`) and no queue
  surface; proposals created anywhere but the desk's own send card are invisible from the
  iPad.
- **The learning loop** has read clients (`journalEntries` / `learningDigest`) and no reader.
- **Artifact provenance (19-04)** is the one green story: `ConfidenceRing` + sources render
  in `CompanionShellApp.swift`, sim-proven — it needs its evidence trail and story flip.

## The load-bearing design call

**Screens over shipped clients, in the Companion shell.** The client layer is done and
metal-readiness-audited (EQ-W6: timestamps stay raw ISO strings). New surfaces land as card
funcs / tabs in `CompanionShellApp.swift` (the 19-01/19-04 precedent) — the shell stages
Contracts+Providers+RuntimeCore only, so screens are pure SwiftUI over the client seam.
The desk app's `DioSendCard` already gates its own sends with a visible receipt; 19-05's
review queue makes *everyone else's* proposals (web, aftercare file-issue, live meeting)
reviewable from the iPad — that is the real split the audit demanded. Aftercare file-issue
(19-01) feeds the 19-05 queue: file → proposal → review → approve, all honest, never
autonomous.

## Stories

| ID | Title | Status |
|----|-------|--------|
| HSM-19-01 | Meeting aftercare — the file-issue action closes the loop — **leads** | done — [`evidence-story-01.md`](./evidence-story-01.md) (live-hub proven; the tap rides the walk W1) |
| HSM-19-02 | The faceted archive — search + facet chips over the shipped clients | todo (client merged, EQ-W3) |
| HSM-19-03 | Meeting import on the iPad — the picker over the multipart client | todo (client merged, `013c7d0`) |
| HSM-19-04 | Artifact provenance — confidence ring + sources | done — [`evidence-story-04.md`](./evidence-story-04.md) (shipped #151/#159; verified today, metal joins the 19-07 walk) |
| HSM-19-05 | The proposals review queue (the split, made visible) | todo (clients merged, EQ-W3) |
| HSM-19-06 | The learning-loop reader (read-first) | todo (clients merged, `8f65657`) |
| HSM-19-07 | Docs + the staged metal walk | todo |

## Where we are

Opened 2026-07-03; **2/7** — 19-04 flipped on verified evidence the same hour (`swift test`
425 green + the shell simulator build; the code shipped pre-open via #151/#159), then
**19-01 closed the loop**: the accepted-only File issue action + inline repo row + honest
proposed pill, live-hub proven (proposed / idempotent / 400 / the filed proposal visible in
the 19-05 queue — the handshake the next story renders). Next: **19-05** (the review queue,
while the filed proposal is fresh), then 19-02 / 19-03 / 19-06. The metal gate (19-07's
walk) is staged press-play so it can join the owner's 18-06 couch session. The
`SpokenSymbols` port (18-04) is reused for any meeting-side symbol application — do not
re-implement it.
