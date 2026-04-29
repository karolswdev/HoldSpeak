# Style Handoff

## Current Visual Language

The current UI uses a dark operational theme:

- Background: near-black navy.
- Panels: dark blue surfaces with subtle borders.
- Text: high-contrast off-white with muted secondary text.
- Accent: cyan/blue for primary actions and status signals.
- Warnings: amber.
- Danger: red/pink.
- Shape: compact 6-8px radii, thin borders, dense spacing.

This is functional but not yet a full design system.

## Desired Direction

The product should feel like a private local workbench:

- Calm and precise.
- Fast to scan.
- Clear about local/private behavior.
- Confident around destructive actions.
- Technical enough for power users, but not visually chaotic.

Avoid:

- Marketing-style hero layouts.
- Decorative gradients or large illustration cards.
- One-note blue/purple palette dominance.
- Nested cards inside cards.
- Overly large type inside dense tool panels.

## Component Families To Formalize

- Top navigation and route identity.
- Status pills for local state, connector state, runtime state, and job state.
- Primary/secondary/danger buttons with loading/disabled states.
- Toolbar groups for panel actions.
- Dense list rows for records, candidates, annotations, and jobs.
- Empty states with one useful next action.
- Inline panel messages for success/error.
- Forms for settings, rules, connector configuration, and block editing.
- Preview result blocks for command plans, rule matches, and dry-run traces.
- Confirmation patterns for deletion and connector output clearing.

## Accessibility And Responsiveness

- Preserve high contrast between body text and dark surfaces.
- Ensure all controls have visible focus states.
- Keep text wrapping stable on narrow screens.
- Avoid horizontal overflow in command previews and URLs.
- Make button labels short and durable under localization.
- Keep mobile layouts functional even if desktop remains the primary target.

## Open Style Questions

- Should the app keep a unified dark theme, or support light/dark tokens now?
- Should activity, history, and dictation share one global nav component?
- What is the visual grammar for "local-only" status across the whole product?
- How should connector command previews be displayed so they are inspectable but
  not intimidating?
- How should meeting candidate state be visualized across candidate, meeting,
  and history surfaces?
