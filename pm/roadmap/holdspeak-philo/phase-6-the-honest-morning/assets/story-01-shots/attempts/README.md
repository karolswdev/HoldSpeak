# Parked attempts (not evidence)

Three rig runs of `case.philo601.import_failed.badge` that crashed before a
verdict. The first `observe_at` was a Playwright `:has-text()` selector; the
rig reads `observe_at` with `document.querySelector`, which refuses it
(`SyntaxError ... is not a valid selector`). One 1440 run also used
`--headless`, which the rig refuses for face steps. The atlas case now observes
`[data-testid=arrival-meeting-badge]` (the hub holds one meeting). Parked, not
deleted (owner ruling: never delete).
