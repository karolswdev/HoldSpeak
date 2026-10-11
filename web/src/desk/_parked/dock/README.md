# Parked: the Dock's People 1:1 mark (PHILO-17 doors, 2026-10-10)

One primary door per application: People opens from its desk drawer and Go,
not the Dock. The People tile's next-1:1 mark (`desk-dock-people-state`) and
its read are parked here, unchanged. Nothing imports them; `tsconfig.json`
and vitest exclude `_parked/`.

- `peopleOneOnOne.ts`: `readPeopleProjection` (readiness first, then the
  relationships and their briefs). The four Dock vitest cases that fenced it
  were removed with the tile; they are in git history at `Dock.test.tsx`
  (origin/main 03f6f9c73).
