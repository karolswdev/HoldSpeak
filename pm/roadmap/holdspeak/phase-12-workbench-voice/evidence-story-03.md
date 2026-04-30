# HS-12-03 evidence — Per-route audit + dashboard fixes

This story bundled four phase-10 polish items that surfaced
during the HS-10-13 review. Each landed inside a slice of the
voice pass (HS-12-02) since they only made sense once the new
voice was in place.

## How acceptance criteria are met

### Hero wordmark right-sized; brand never appears twice on the same screen above the fold

The dashboard `<h1 x-text="meetingTitle || 'HoldSpeak'">` was
displaying the literal "HoldSpeak" fallback at idle, which
duplicated the TopNav brand.

Fix (slice 7, this commit): the hero `.hero-title` container
now has `x-show="meetingTitle"` so the h1 renders only when a
real meeting title exists. At idle, the hero shows the
local-only pill + workspace summary + (if any) tags + the
right-rail action stage. The TopNav's brand is the only
"HoldSpeak" wordmark above the fold.

### Toast layer dedupes consecutive identical messages

Fix (slice 2, commit `01180a2`): `dashboard-app.js:toast()` now
checks `this.notifications.some(note => note.message === message)`
and short-circuits when the message is already on screen. The
double "Failed to load deferred plugin jobs" pollution that
appeared in earlier review screenshots is gone.

### Idle state on `/` shows exactly one "you can start a meeting" affordance

Phase-10 idle stacked three signals: hero `<h1>HoldSpeak</h1>`
fallback, hero copy "...run locally on this machine", "No tags
yet" placeholder, and side-rail "Press start, then hold to
talk".

Fix (slice 7, this commit):
- Hero copy trimmed to the workspace summary; the "...run
  locally on this machine" sentence removed (TopNav's
  `local-only` pill plus the side-rail message already convey
  it).
- "No tags yet" placeholder removed; tags container only
  renders when there's at least one tag.
- Hero h1 stops fallback-rendering "HoldSpeak" at idle (above).

What's left at idle: the local-only pill (where it belongs),
the workspace-summary lead, and the right-rail action stage
with the single canonical "Press start, then hold to talk"
caption. One affordance.

### Each route's screenshot in `designer-handoff/screenshots/` is current

```
$ uv run python designer-handoff/capture-screenshots.py \
    --base-url http://127.0.0.1:4321/_built \
    --out designer-handoff/screenshots
wrote …/dashboard-desktop.png 1440x1000 /
wrote …/activity-desktop.png 1440x1100 /activity
wrote …/activity-mobile.png 390x1200 /activity
wrote …/history-desktop.png 1440x1100 /history
wrote …/dictation-desktop.png 1440x1100 /dictation
```

All five shots are recaptured against the running app with the
final HS-12-02 voice in place.

### No regressions in dense list legibility on `/activity` records, `/history` meetings, `/dictation` blocks

Reviewed in the recaptured screenshots:

- `/activity` records list: dense panel-body rows, hard borders,
  legible at every state.
- `/history` meeting cards: white-on-black-border tiles with
  hover-tint + inverse-bar selected state, no regression.
- `/dictation` block list: square cards with hover-light +
  selected-inversion treatment.

## Tests

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
…
1269 passed, 13 skipped in 30.23s
```

Presentation-only changes; the suite is included as a
regression check, not a feature gate.
