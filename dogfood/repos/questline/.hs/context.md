# questline — product context

questline is a consumer SaaS habit and quest tracker. Users create
**quests** (real-life goals broken into repeatable actions), build
**streaks**, earn **XP**, and join **guilds** for social accountability.
The business runs on a freemium model and is measured by one north-star
metric: **WAQC** (Weekly Active Quests Completed per user).

We are a mature product: auth, onboarding, quest CRUD, streaks/XP, and
the analytics/event pipeline are all shipped (see `STAGES.md`). The two
live decisions are **Guilds (social)**, currently in discovery, and the
**Q3 delivery milestone**, currently in planning.

## Stack

TypeScript · Next.js 14 (App Router) · Postgres · Prisma · tRPC.

## Primary entry points

- Data model: `prisma/schema.prisma`
- Quest API (create/complete): `src/server/trpc/quests.ts`
- Streak computation (timezone-aware): `src/server/streaks.ts`
- Analytics / event tracking: `src/lib/analytics.ts`
- Feature flags: `src/lib/flags.ts`
- Quests list page (server component): `src/app/quests/page.tsx`
- Streak tests: `tests/streaks.test.ts`

## Product docs

- Guilds PRD (draft): `docs/prd/guilds.md`
- Customer signals digest: `docs/CUSTOMER-SIGNALS-2026Q2.md`
- Q3 roadmap (draft): `docs/roadmap-Q3.md`
- Completed stages: `STAGES.md`
- Release history: `CHANGELOG.md`

## How to read this repo

Start with `STAGES.md` for what's done and what's open, then the doc
that matches the conversation: PRD for product decisions, customer
signals for churn, the Q3 roadmap for delivery scope.
