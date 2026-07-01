# HS-70-02 — Home: "what is this + your next action"

- **Status:** done
- **Priority:** HIGH (the anti-confusion centerpiece)
- **Depends on:** HS-70-01
- **Evidence:** [evidence-story-02.md](./evidence-story-02.md)

## Goal

Reframe `/` from a data dashboard into an orienting **Home** that answers two
questions in one screen: *what is this?* and *what should I do right now?* This
is the single highest-leverage cure for the owner's "I'm confused about my own
product."

## Scope

- One-breath identity line at the top: the POSITIONING one-liner, once (the
  voice rule allows the pitch line on a dedicated surface; not a privacy
  novel, not prose sprawl).
- **Two mode cards, co-equal and unmistakable:** Dictation and Meetings, each
  with a one-line "what it does" and one primary action (Dictation → start /
  open the cockpit; Meetings → capture or import). These are the front door to
  the two modes.
- **The single next-best-action** for a returning user (e.g. "3 dictations
  learned from" / "a meeting is waiting on aftercare" / "finish setup"), driven
  by the existing status + first-run signals. One nudge, not a feed.
- A condensed recent-activity strip (reusing existing data), and one quiet,
  visually-secondary **Studio** affordance ("Power tools →"). Studio is never
  louder than the two modes.
- Built on the Phase-69 `.signal-card` substrate + `hs-materialize`. Empty /
  first-run state is the HS-70-07 component (guides, doesn't blank).
- Replaces the current dashboard content; the `/` first-run guard is
  reconciled in HS-70-03 (Home is where the wizard lands).

## Proof required

Screenshots: Home for a fresh user (empty/first-run), Home for a returning
user with real seeded data (both mode cards, the one next-action, recent
strip, the quiet Studio link). A 10-second "what is this + what do I do"
read-test noted in evidence.

## Done

Shipped and screenshot-proven (empty + seeded). `/` is now an orientation Home:
identity (the positioning one-liner), a next-action band fed by
`/api/setup/status` (`primary_action`, hidden once ready), the two modes as
co-equal `.signal-card`s with guiding dynamic subtitles + action buttons, and a
quiet Studio link. The 1378-line live-meeting runtime dashboard moved off `/` to
`/live` (a `git mv`, behaviour unchanged, `current="meetings"`); `/live`
registered in pages.py + PAGE_ROUTES. Empty-state subtitles guide instead of
blanking. Route pre-flight 2 passed; full suite 3045 passed. See
[evidence-story-02.md](./evidence-story-02.md).
