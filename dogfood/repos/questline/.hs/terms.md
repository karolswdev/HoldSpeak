# Domain glossary

- **Quest** — a user-defined recurring goal (e.g. "run 3x/week"). The
  core object. Quests have a cadence, a streak, and accumulate XP on
  completion. Modeled as `Quest` in `prisma/schema.prisma`.

- **Quest completion** — a single logged instance of doing a quest's
  action. Drives streaks, XP, and the WAQC metric. Emitted as a
  `quest_completed` event.

- **Streak** — the count of consecutive cadence windows in which a quest
  was completed, evaluated in the user's local timezone. Owned by
  `src/server/streaks.ts`. Breaking a streak is high-stakes UX.

- **XP** — experience points earned on quest completion; higher streaks
  grant multipliers. Cosmetic/motivational, not monetary.

- **Guild** — an opt-in group of users who share progress and encourage
  each other. The Stage 5 social bet, currently in discovery.

- **WAQC** — Weekly Active Quests Completed per user. The north-star
  metric. A "WAQC-positive" change is the bar for shipping.

- **Activation** — a new user reaching their **first completed quest**
  within 7 days of signup (D7 activation). The make-or-break onboarding
  outcome; onboarding step 3 is where we currently lose people (QL-301).

- **Freemium gate** — the paywall boundary: free users are capped at 3
  active quests and 1 guild. Crossing it triggers an upgrade prompt and
  a `freemium_gate_hit` event.

- **Cadence** — a quest's required rhythm (daily / weekly / N-times-per-
  week). Defines the window streaks are evaluated against.

- **Rollout ladder** — off → dogfood → 10% → GA, the path every flagged
  feature follows.
