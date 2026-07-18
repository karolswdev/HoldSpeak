# HS-95-08 — Studio, sessions, and the last exits

- **Project:** holdspeak
- **Phase:** 95
- **Status:** backlog
- **Depends on:** HS-95-03, HS-95-05, HS-95-06, HS-95-07
- **Unblocks:** HS-95-09, HS-95-10

## Problem

After the domain stories land, the heavy studio surfaces still live
outside: the Workbench (the node-canvas workflow editor), Studio, the
Companion page (personas and coder sessions — conceptually overlapping the
in-desk PersonaChat and SessionPullout windows), and Activity. And the
product still carries two navigation worlds: the desk shell and the flat
`AppShell` with its own `PRIMARY_NAV`. The phase's promise — no desk action
navigates away — is only real when the last exits are gone and the flat
shell is demoted to a deep-link door.

## Scope

- In:
  - Workbench hosted in-world: the canvas core in a desk window that
    supports maximize (the canvas wants the full stage); "edit-workflow"
    Pullout links open it scoped to the workflow object;
  - Studio and Activity cores in desk windows via the shelf;
  - Companion reconciled, not duplicated: the Companion core hosted
    in-world and the existing PersonaChat/SessionPullout windows become the
    single sessions surface (one list, one chat, one session detail — decide
    the merge direction in-story and record it);
  - the final sweep: zero `<Link>` out of `web/src/desk/` to any product
    route, enforced by a lint/test guard so regressions cannot land
    silently;
  - flat-route demotion: every wrapped route renders the desk with the
    matching window opened (the existing `?open=` arrival mechanism,
    generalized) instead of the flat `AppShell` page; `AppShell` and
    `PRIMARY_NAV` are deleted along with `react-app.css` page chrome that
    nothing uses anymore (pre-release product: no compatibility ceremony);
  - external links (receipt sources, PR URLs, asset downloads) stay honest
    `<a>`s — leaving the product is allowed; leaving the desk for the
    product's own surface is not.
- Out:
  - workflow/persona/session semantics or hub routes;
  - the theater/presence immersive routes (`/welcome`, `/presence`);
  - Swift parity.

## Acceptance criteria

- [ ] Workbench opens in-world, maximizes to the full stage, and edits a
      real workflow end to end; the Pullout's "edit-workflow" opens it
      scoped.
- [ ] Studio and Activity open as windows from the shelf with full
      capability.
- [ ] One sessions surface: opening personas/coder sessions from the shelf
      and opening a session from the world land in the same reconciled
      windows; no duplicated list/chat implementations remain.
- [ ] The guard is live: a `<Link>` from `web/src/desk/` to a product route
      fails the web test suite; the sweep shows zero occurrences.
- [ ] Every former flat route (`/dictation`, `/history`, `/meetings`,
      `/live`, `/settings`, `/profiles`, `/commands`, `/cadence`,
      `/activity`, `/studio`, `/workbench`, `/companion`, `/setup`,
      `/docs/dictation-runtime`, `/design/components`) resolves to the desk
      with the right window open at the right scope; `AppShell`,
      `PRIMARY_NAV`, and dead page chrome are deleted from the bundle.
- [ ] The `?room=` workroom "Back to Desk" bridge is retired (nothing
      renders outside the desk to come back from); the codec survives only
      where deep links still need scope decoding.
- [ ] Bundle check: the flat-shell chunk disappears from the build output;
      no route regression at 1440 or 393.

## Test plan

- `npm --prefix web test` — reconciliation suites, the no-exit guard, the
  route-demotion table test (each route → expected window + scope).
- Playwright: hit every demoted route cold, assert the desk arrives with
  the right window; drive one real workflow edit in-world.
- Full sweep: `uv run pytest -q` (excluding the standing metal exclusion)
  for hub-served route smoke.

## Implementation direction

- Demotion is a routing-table change: `PRODUCT_ROUTES` entries map to
  `{window, scope}` descriptors handled by the desk arrival path — one
  mechanism, sixteen table rows.
- Prefer keeping SessionPullout as the session-detail body and letting the
  Companion core provide the roster; kill whichever chat duplicate loses.
- Delete boldly and let the guard hold the line; this story is where the
  two-worlds architecture actually dies.

## Evidence required

- captured test runs including the guard failing on a planted violation
  (then removed);
- Playwright demotion walk output covering every route;
- build output showing the flat-shell chunk gone;
- screenshots: Workbench maximized in-world, the reconciled sessions
  surface.
