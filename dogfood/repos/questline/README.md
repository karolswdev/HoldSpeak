# questline

Turn real-life goals into quests. Build streaks. Earn XP. questline is a
gamified habit tracker for people who bounced off plain to-do apps and
want games-style motivation for the things that actually matter.

## What it does

- **Quests** — recurring goals with a daily / weekly / N-per-week cadence.
- **Streaks** — consecutive completions, counted in *your* timezone.
- **XP** — earned per completion, multiplied by your streak.
- **Guilds** — opt-in groups for social accountability (in discovery).

Free plan: up to 3 active quests and 1 guild. questline Pro lifts the
caps and unlocks XP boosts.

## Stack

TypeScript · Next.js 14 (App Router) · Postgres · Prisma · tRPC.

## Develop

```bash
npm install
npm run db:migrate
npm run dev      # http://localhost:3000
npm test         # vitest (streak logic etc.)
```

## How we ship

Everything rides a feature flag (`src/lib/flags.ts`) up the ladder
off → dogfood → 10% → GA, and emits a tracked event
(`src/lib/analytics.ts`). The number we move is **WAQC** — weekly active
quests completed per user. See `STAGES.md` and `docs/roadmap-Q3.md`.
