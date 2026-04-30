# HS-10-11 evidence — Destructive-action confirmation pattern

## Files shipped

- `web/src/components/ConfirmDialog.astro` — new component (~290
  lines). Renders a single `<dialog id="holdspeak-confirm-dialog">`
  plus an inline dispatcher script that registers
  `window.holdspeakConfirm({ title, body, scopeNote, confirmLabel,
  cancelLabel, danger }) → Promise<boolean>`. Token-driven styles
  duplicate the relevant `Button.astro` rules (`btn--secondary`,
  `btn--danger`, `btn--primary`) so the dialog buttons match the
  rest of the system without going through Astro components (the
  buttons need to be wired by the inline script that toggles
  variants per call).
- `web/src/layouts/AppLayout.astro` — imports and mounts
  `<ConfirmDialog />` once at the end of `<body>`. Every page that
  composes `AppLayout` now has the dialog available; verified by
  `grep -c holdspeak-confirm-dialog` on the built HTML which
  returns 2 hits per page (the `<dialog>` element and the closing
  tag) for `index`, `activity`, `history`, `dictation`,
  `docs/dictation-runtime`, `design/components`, `design/check`.
- `web/src/pages/design/components.astro` — new gallery section
  `#confirm-dialog` with three trigger buttons (delete records,
  clear dismissed candidates, stop meeting) so reviewers can walk
  the keyboard pattern in isolation.

## Adoption — every destructive site is on the new dialog

| Surface | File:line | Wording highlight |
|---|---|---|
| `/activity` clear imported records | `web/src/scripts/activity-app.js:295` | "Delete imported activity records?" + scope: only the local ledger; the browser's own history is untouched. |
| `/activity` un-exclude domain | `web/src/scripts/activity-app.js:356` | "Remove `<domain>` from the exclude list?" — non-danger styling (re-imports on next refresh, not destructive). |
| `/activity` delete project rule | `web/src/scripts/activity-app.js:445` | "Delete project rule "`<id>`?" + scope note. |
| `/activity` clear dismissed candidates | `web/src/scripts/activity-app.js:566` | Connector-output scope language: "underlying connector data and any source systems (GitHub, Jira, etc.) are not touched". |
| `/dictation` delete block | `web/src/scripts/dictation-app.js:332` | "Delete block …?" + scope note. |
| `/dictation` delete project KB file | `web/src/scripts/dictation-app.js:651` | Calls out that `.holdspeak/` is preserved and source files referenced from inside the KB are untouched. |
| `/history` archive project | `web/src/scripts/history-app.js:771` | "Archive project …?" + scope note. Previously had no confirmation at all. |
| `/` dashboard stop meeting | `web/src/scripts/dashboard-app.js:1078` | "Stop the meeting session?" — non-danger styling. Previously a `window.confirm`. |

```
$ grep -rn 'confirm(' web/src/
(no output)
```

`window.confirm(` → 0 matches. All destructive paths route through
`window.holdspeakConfirm`.

## Architectural decisions

- **Native `<dialog>` element + `showModal()`.** Free focus trap,
  free `cancel` event for Esc, free backdrop. We do not ship a
  hand-rolled modal: the platform behaviour is the right behaviour.
- **Promise-returning dispatcher.** Each call site is a one-line
  `await`. Reads the same as the `confirm()` it replaces, no event-
  driven state machines per page. Prior calls are forcibly settled
  to `false` if a second prompt is requested before the first
  resolves, so two awaiters can never race against the same dialog.
- **Cancel is default-focus *and* default-Enter.** Native `<dialog>`
  treats Enter as "activate the focused button". By focusing
  `[data-confirm-cancel]` on every open (after a `requestAnimationFrame`
  so the showModal frame has committed), Enter resolves `false`.
  Destructive actions never auto-confirm on a stray Enter.
- **`returnFocusTo` captured before `showModal()`.** `document.activeElement`
  at the moment of the prompt is recorded and re-focused on every
  resolution path (button click, Esc, backdrop), so keyboard users
  land back on the trigger.
- **`danger` prop toggles the primary button between `btn--danger`
  (red) and `btn--primary` (accent).** "Stop meeting?" and
  "Remove `<domain>` from the exclude list?" are reversible-ish
  actions; making them red would wash out the visual signal on
  truly destructive sites.
- **Scope note is a separate, hideable block** with a `local-only`
  pill and the explicit "source data on X is untouched" wording.
  `[data-empty="true"]` collapses it when the call site does not
  pass `scopeNote`. The pattern enforces the acceptance criterion
  that connector-output deletions name what is *not* affected.

## Manual verification

Walked each surface in Chromium against the local dev build:

- **Keyboard-only**: Tab from the trigger → opens dialog →
  focus lands on Cancel → Tab cycles Cancel ↔ Confirm only (focus
  stays inside the dialog) → Esc closes, focus returns to trigger.
- **Enter behaviour**: Open the dialog and press Enter immediately
  → resolves `false`, no destructive call happens.
- **Backdrop click**: clicking the dimmed area outside the form
  resolves `false`.
- **Visual**: the `btn--danger` red treatment (canvas tokens) only
  shows on actually-destructive prompts; the meeting-stop and
  domain-unexclude prompts use the accent primary instead.

## Build

```
$ npm run build
…
[build] 7 page(s) built in 854ms
[build] Complete!
```

## Tests

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
…
1184 passed, 13 skipped in 30.38s
```

This is a presentation-layer change with no Python surface — the
suite is included as a regression check, not a feature gate.
