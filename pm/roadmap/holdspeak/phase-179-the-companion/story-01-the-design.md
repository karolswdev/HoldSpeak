# HS-179-01 — The design

- **Project:** holdspeak
- **Phase:** 179
- **Status:** backlog
- **Depends on:** Phase 178 merged
- **Unblocks:** HS-179-02, HS-179-03, HS-179-04, HS-179-05, HS-179-06, HS-179-08
- **Owner:** unassigned

## Problem

Every face in 179 must be designed on the library at 1440 + 393 and
ratified by the owner before any build begins (UX-CANON.md rule A.2).
The companion's canvas is the iPad frame recreating the finished web
spec's portfolio and Room surfaces. The phone variant (if universal) is
a second artboard. Without artboards the Swift recreation has no spec
to build to.

## Scope

- In: artboards at 1440 + 393 for:
  - The companion's portfolio surface (Room rows with needs-you count,
    release-readiness indicator, urgency sort; the iPad frame).
  - The Room drill-down (needs-you rows, health tokens, the first
    WHY; the iPad frame).
  - The Monday brief portfolio section on the companion.
  - The needs-you notification (the local notification content; the
    count; the tap target).
  - The discovery/authentication state (connecting, authenticated,
    disconnected; the honest disconnect screen per Article VI).
  - The phone variant (if universal): the same surfaces adapted to
    the smaller viewport.
- Out: implementation; new library species (use existing ones); the
  web spec itself (finished through 178).

## Acceptance criteria

- [ ] Artboards on the ratified shell for every companion face
      (Article IX.2; UX-CANON.md rule E.1).
- [ ] Counsel reads the artboards before the owner (UX-CANON.md rule
      E.1).
- [ ] The owner's word on the canvas (Article IX.4).
- [ ] No prose in the artboards (Article VII.1; UX-CANON.md rule A.3).
- [ ] Every artboard uses at least three type steps (UX-CANON.md rule
      C).
- [ ] The companion artboards are recognizably the same product as the
      web desk -- same species, same tokens, same grammar
      (Article VIII.3 -- every glass is first-class).
- [ ] The disconnect screen is honest (Article VI).

## Test plan

- Unit: n/a (design-only story).
- Integration: n/a.
- Manual: counsel review of artboards; owner review on the artifact.

## Notes / open questions

- The 1440 width is the iPad landscape; 393 is the iPhone mini/SE. If
  the companion is iPad-only, the 393 artboard covers the iPad portrait
  mode instead. The design story resolves this.
- Article VIII.3: "Every glass is first-class: the workstation window,
  the phone's bottom sheet, the iPad's diorama. Craft is not a
  desktop-only property." The companion must meet this bar.
