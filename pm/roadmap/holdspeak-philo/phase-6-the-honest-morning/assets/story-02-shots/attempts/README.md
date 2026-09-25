# Parked attempts (not evidence)

Runs of `case.philo602.brief_more.destination` on the `origin/main` build that
BLOCKED before the trigger: the first case versions seeded too few human rows,
and on `origin/main` the raw `Service.method` rows are hidden from the Arrival,
so the fold `N more` was never drawn (`wait_for [data-testid=arrival-brief-more]`
timed out). The blocked 1440 shot still shows the defect: `BRIEF · 3 THINGS
WAITING` over `Brief ready · 6 items · 8:54 PM` and `GENERATED SEP 24 20:54`.
The case now seeds four proposed decisions. Parked, not deleted.
