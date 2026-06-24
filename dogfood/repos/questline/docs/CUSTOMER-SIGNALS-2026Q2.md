# Customer signals — 2026 Q2

A digest of qualitative and quantitative signal feeding the Stage 5 and
Q3 decisions. Sources: support tickets, churn survey, app-store reviews,
and the funnel dashboard. Owner: Dana.

## Headline: the onboarding step-3 leak (QL-301)

D7 activation dropped **41% → 33%** after the March onboarding redesign.
The funnel pinpoints **step 3 (first quest setup)** — specifically the
cadence picker. Users reach it and abandon.

> "I just wanted to track 'go for a run' and it asked me daily vs weekly
> vs how many times a week and I closed the app." — churn survey, free user

> "There were no examples. I didn't know what a good quest looked like."
> — app-store review, 2★

**Read:** the cadence picker is a cliff. A template/example quest at
step 3 is the leading hypothesis (see `onboardingTemplatesV2` flag,
currently at 10%).

## Demand for social accountability (feeds QL-310 / Guilds)

Recurring, unprompted ask. Strongest *retention* signal we have.

> "If my friends could see my streak I'd never miss." — NPS comment, Pro user

> "I do these challenges with my sister in a group chat already. I wish
> it was just in the app." — support ticket

> "Make it social. Solo gets boring after week 2." — app-store review, 4★

**Caveat:** wanting social ≠ social moving WAQC. The week-2 boredom
quote may equally be an activation/habit-depth problem, not a loneliness
problem. No experiment has separated these.

## Streak fairness complaints (feeds QL-322)

> "My streak reset overnight and I DID do it. I'm in Seattle." — ticket

> "Lost a 40-day streak to the daylight savings change. Furious." — 1★

**Read:** non-UTC and DST streak loss is actively churning our most
engaged users — the worst possible cohort to lose. Sev-2.

## Pricing / freemium

Light but present friction at the 3-quest cap; conversion is steady, not
a fire. The 1-guild cap is unexercised because guilds don't exist yet.
