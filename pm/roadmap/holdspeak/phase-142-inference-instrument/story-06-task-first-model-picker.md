# HSEGHS001HS104-142-06 - Task-First Model Picker

- **Project:** holdspeak
- **Phase:** 142
- **Status:** done
- **Depends on:** HSEGHS001HS104-142-05
- **Unblocks:** a direct, comprehensible model setup path
- **Owner:** Codex

## Problem

The three-step Models wizard spent most of its viewport explaining setup instead
of letting an owner choose a model. It duplicated headings, hid useful choices
below introductory prose, truncated model names, and separated selection from
the action with an unnecessary review step.

## Scope

- **In:** Replace the wizard with one task-first master/detail picker; keep
  source filters, all server-projected choices, full wrapping names, one stable
  action seat, compact status truth, collapsed setup issues and job routing,
  and exact 1440/393 behavior.
- **Out:** New models, recommendation policy, download authority, MLX execution,
  or any browser-authored capability/readiness fact.

## Acceptance criteria

- [x] The first useful viewport begins with `Choose a model` and the model list,
  not a hero, progress rail, location step, or review screen.
- [x] `This device`, `OpenRouter`, and `Experimental` filter one persistent list;
  selecting a row is inert until the owner invokes the sole action.
- [x] Full model names wrap and never ellipsize; detected models use compact rows.
- [x] Desktop shows list, selected detail, and action together; mobile shows at
  least three rows and an in-surface action panel without horizontal overflow.
- [x] Visible copy is limited to decision facts, current truth, and direct verbs;
  setup issues and per-job administration remain disclosed.
- [x] Focused component tests, production build, and isolated-HOME 1440/393
  browser glass pass.

## Test plan

- **Unit:** focused `InferenceCapabilityPanel` and Models settings suites.
- **Integration:** production Vite build.
- **Manual / device:** isolated-HOME Playwright glass at 1440×900 and 393×900,
  including source switching, full-name wrapping, one action seat, 44px mobile
  targets, secret non-leak, and no horizontal overflow.

## Notes / open questions

The server remains the sole source of catalog, hardware, detection, readiness,
and activation truth. This story changes presentation and copy, not authority.
