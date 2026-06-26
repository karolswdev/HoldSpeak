# Turning dictation into a task

Produce a precise product/eng task, not a paraphrase. For each request:

1. **Name the concrete files** it touches (use real paths from this
   repo, e.g. `src/server/streaks.ts`, `src/server/trpc/quests.ts`,
   `src/lib/flags.ts`, `prisma/schema.prisma`).
2. **Write an imperative spec** — one short paragraph of what to build,
   in the voice "Add…", "Change…", "Gate…", not "We could…".
3. **Acceptance criteria as a checklist** — observable, testable lines.
4. **Require a feature flag** — name it (e.g. `flag.guildsV1`) and place
   it in `src/lib/flags.ts`. No flag, not done.
5. **Require a tracked event** — name it and its key props (e.g.
   `guild_joined { guildId, source }`) via `src/lib/analytics.ts`.
6. **State the north-star tie** — one line on the expected effect on
   **WAQC** (or why it's neutral/instrumentation only).
7. **Link the issue/PRD** if one exists (QL-3xx, `docs/prd/...`).

If the request is a decision (build vs defer, scope cut), output options
with a recommendation and the WAQC/risk tradeoff — do not invent a
spec for a thing we haven't decided to build.

Keep it tight. No preamble, no restating the ask.
