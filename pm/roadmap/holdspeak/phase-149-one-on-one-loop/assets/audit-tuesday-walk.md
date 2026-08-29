# Phase 149 audit — the Tuesday walk (reduced, and why)

Orchestrator-run 2026-08-29 via
[`audit-walk-rig.py`](./audit-walk-rig.py) — **zero keychain writes
by construction**. Shots in
[`audit-walk-shots/`](./audit-walk-shots/). Companion:
[audit-census.md](./audit-census.md).

## Why reduced — the two-dialog incident (evidence, not shame)

The full walk (populated People state) is BLOCKED by Phase-138's
ledger item L3, and this arc PROVED it on the owner's screen twice:

1. A delegated walk hit the macOS **"Keychain Not Found"** GUI
   dialog storing `people-key-v1:…` — the exact dialog the 138
   record logs ("owner saw it").
2. Resumed WITH the 138 walk-scoped-keychain drill, it hit the
   dialog AGAIN (`test-user`), and its dying diagnosis explains why
   the drill cannot work headlessly anymore:
   - **macOS keychain services are UID-scoped, not $HOME-scoped** —
     an isolated HOME does not redirect default-keychain
     resolution;
   - **Python keyring #623**: `set_generic_password` accepts a
     custom-keychain target and NEVER USES IT — every write goes to
     the user's default keychain regardless.
   - The only workaround is mutating the OWNER'S real keychain
     search list — forbidden by walk law; the agent was stopped at
     the plan stage; the owner's search list verified pristine
     (login + System, default login).
   - Elevation would not help (root's keychain, worse).

The 138 walk passed 55/0 because it was ATTENDED. Headless
populated-People walking requires the **dev-only keystore seam L3
named and deferred in 138** — which therefore becomes **story 01 of
this phase**, together with L2 (silent empty People cards on a
broken sidecar).

## The facts the reduced walk established on glass

- **Readiness gate honest**: `/api/people/readiness` →
  `unconfigured / store absent / sync local_only / capture
  notes_only / reason_code people_store_unconfigured`.
- **TUESDAY PROBE (a)** — event → person: with "1:1 w/ Ewa" on the
  rail, the row's full markup contains NO person/relationship
  affordance or reference. **DOES NOT EXIST** (shot
  `tuesday-rail-1440.png`).
- **TUESDAY PROBE (b)** — armed recording → person: arming the 1:1
  via Record this (147 path, worked first tap) yields a schedule
  payload with NO person/relationship field. **DOES NOT EXIST**
  (shot `tuesday-armed-1440.png`).
- **393**: Open People is unreachable at narrow except via ⌘K
  (Desk/mark menus hidden by design) — a manager-on-phone gap to
  weigh in the charter.
- **Era mismatch, eyeballed**: the unconfigured People window
  (`people-unconfigured-1440.png`) is a vast empty panel with a
  tiny "Not set up / Set up" — honest but joyless, predating the
  144-148 empty-state pattern (compare the rail's "No calendar
  connected. → Connect calendar" lead). The joy law applies when
  149 touches this surface.

## Walk-derived charter inputs

1. Story 01 = the L3 dev keystore seam (env-gated, never default)
   + L2 sidecar-state surfacing — unblocks every later story's
   walk AND the phase's own exit walk.
2. The person link affordance must live where the probe failed:
   the relationship detail (per the census/INTEGRATION contract)
   with the rail row showing the resolved person once linked.
3. The exit walk MUST include a populated-People leg through the
   new seam — the first ever headless one.
4. The People empty state gets the joy pattern when touched.
