# Story 06 — genuine bare-HOME glass walk

Captured 2026-08-18 against the locally built production bundle (`npm run build`)
served by `holdspeak web --no-open` through its normal loopback
`MeetingWebServer` path. Each run used a new `mktemp` HOME and therefore a new
empty HoldSpeak database/configuration. The only browser arrival credential was
the runtime's newly generated local token; no owner profile, database, fixture,
`_populate()` helper, or `holdspeak seed` command was used.

The normal-state images were reached by pressing the visible **Continue later**
control in the first-value screen, then using the visible Chair/Floor controls.
The current 393px Floor image was recaptured after the compact-list fix on a
third new HOME. It contains exactly six zones, the six furnished notes, and the
single Everyday context knowledge object; it contains no Roadmap rows.

At each captured viewport, `document.documentElement.scrollWidth` and
`document.body.scrollWidth` equalled the viewport width (1440 or 393), and the
browser recorded no console or page errors. Physical microphone capture is not
represented here: the host/browser had no physical microphone to verify.

`everyday-context-1440x900.png` records the ordinary editor surface reached by
opening Everyday context from a separate fresh bare-HOME run. Its edit/save path
was exercised with a temporary test sentence in that isolated database only.

Two further new-HOME traces exercised typed fallback without claiming a
microphone result. Copy rendered `Copied to your clipboard`. Keep created one
stable `First dictation` note (`201`); Continue then seeded (`200`), persisted
the onboarding disposition (`200`), revealed the Chair, and opened the note.
The note retained the exact text and `dictation` tag and remained findable on
the Floor. No console or page errors occurred.

Local verification read by the orchestrator:

```text
focused Python setup/seed/grounding/copy/doc suite: 71 passed in 6.60s
focused Desk Vitest suite: 7 files passed; 97 tests passed
production build: 1479 modules transformed; passed with existing warnings
doc/build-ledger follow-up: 31 passed in 1.88s
git diff --check: passed
```

Fresh Terra counsel returned RATIFY for the first door, furnished defaults,
responsive glass, capability-preserving roadmap suppression, explicit-only
Everyday context, and public wording. The owner called the result “a step in
the right direction.” The story remains active because no physical microphone
was available for the real-mic and physical permission/no-speech legs.

Files:

- `first-arrival-1440x900.png`, `first-arrival-393x900.png` — quiet first-value arrival.
- `continue-chair-1440x900.png`, `reload-chair-1440x900.png`,
  `reload-chair-393x900.png` — ordinary Chair after Continue and reload.
- `furnished-floor-1440x900.png`, `furnished-floor-393x900.png` — furnished Floor.
- `everyday-context-1440x900.png` — reachable, editable Everyday context.
