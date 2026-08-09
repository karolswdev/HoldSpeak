# HS-130-02 — Collision-free secret slots: the exfiltration path closes

- **Project:** holdspeak
- **Phase:** 130
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

This is a **security fix and it ships first in the commit lane.** Sol's
escalation of issue claim 8: `profile_key_env` (`intel/providers.py:270-274`)
maps every non-alphanumeric character to `_`, so `foo-bar`, `foo_bar`,
`foo.bar` all resolve to `HOLDSPEAK_PROFILE_FOO_BAR_KEY`. Profile ids are
**client-supplied** (`profile_service.py:49` — `profile_id=str(fields.get("id")
or self._new_id())`) and `push()` merges `profiles` by whatever id arrives from
any peer, validating only `meta.id`+`meta.kind` (`sync_service.py:690-705`). So
a synced peer creates `foo_bar`, points its `base_url` at an endpoint it
controls, and `_apply_runtime_profile` / `build_meeting_intel_for_profile`
(`providers.py:347,423`) hand it the genuine key belonging to `foo-bar`. That
is exfiltration of a device-local credential through a shape-only sync channel —
the exact boundary `schema.py:1031-1034` declares inviolate.

### What changes

1. Credentials resolve through an **injective secret-slot id** — a derived,
   collision-free, non-secret identifier — not a lossy slug of the display id.
2. Slot resolution **refuses on ambiguity**; it never falls back to a shared
   env name. A profile whose slot cannot be uniquely resolved reports a
   readiness refusal with an actionable message (not the current blank
   `model file not found: ` class of empty refusal).
3. `_profile_key_present` (`inference_targets.py:45-49`, used at 229 and
   292-296) reports ready only when the destination has **its own** key under
   its own slot — never because a colliding destination's key is present.
4. The slot id is a derived non-secret identifier (safe to compute
   deterministically across devices); the **secret value stays device-local
   and never syncs** — the schema boundary is preserved, not moved onto the
   synced row. (Sol, "Keep valid layers": local secret custody vs synced
   destination definition.)

## Acceptance criteria

1. Two destinations whose display ids differ only by punctuation resolve to
   two distinct secret slots; neither can read the other's key.
2. A profile arriving via sync cannot cause an existing destination's key to
   be sent to a new endpoint; the collision test reproduces the exfiltration
   on the pre-change tree and is closed after.
3. Key-presence readiness is true only for a destination with its own key in
   its own slot.
4. The secret value does not appear in any synced bucket (assert against the
   `profiles` serializer).

## Test plan

- Backend: a regression test that constructs `foo-bar` (with key) + `foo_bar`
  (attacker `base_url`) and asserts no key crosses; slot-injectivity property
  test; readiness-presence test; sync-serializer secret-absence test.
- Full backend suite read from file before flip.

## Out of scope

- Broader sync-push authentication / principal checks on `push()` (named for
  Phase 131's sync-registry work; this story closes only the credential
  crossover).
- Renaming the `profiles` table or its client contract (issue Wave 1).
