# Parked attempts (not evidence)

Three rig runs of `case.philo601.import_failed.badge` that crashed before a
verdict. The first `observe_at` was a Playwright `:has-text()` selector; the
rig reads `observe_at` with `document.querySelector`, which refuses it
(`SyntaxError ... is not a valid selector`). One 1440 run also used
`--headless`, which the rig refuses for face steps. The atlas case now observes
`[data-testid=arrival-meeting-badge]` (the hub holds one meeting). Parked, not
deleted (owner ruling: never delete).

Round 2 (2026-09-24 night, Astra's check on built, finding 2): two runs of the
extended case (well head `IMPORT`) with the trigger `goto /`, parked:
`20260925T034810Z-…-1440` (pass) and `20260925T034826Z-…-393` (fail: the open
well sits below the sticky capture bar at 393, `a covering element owns hit
points … footer.arrival-capture-bar`). One more 393 try with `press End` failed
the same way (scratch, not retained: the Arrival's scroller does not take End).
The case's trigger is now the pointer on the well head, which scrolls it into
view; the evidence runs are `20260925T035149Z-…-1440` and `20260925T035156Z-…-393`.
