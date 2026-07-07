# HS-84-05 — Docs + the live walk

- **Project:** holdspeak
- **Phase:** 84
- **Status:** backlog
- **Depends on:** HS-84-01, HS-84-02, HS-84-03, HS-84-04
- **Unblocks:** none (closes the phase)
- **Owner:** unassigned

## Problem

The phase's claim — a raw endpoint URL is typed in exactly one place — has
to be proven on real metal and taught at the entry points, or it's a code
change wearing a thesis. Also: the BACKLOG's candidate-S section still
advertises work that shipped months-to-weeks ago under other flags; the
reconciliation rides the scaffold commit, but the row's final "shipped"
flip belongs here.

## Scope

- In: entry-point docs — the settings/dictation/meeting guides that today
  teach typing a base URL now teach "author a profile once, pick it
  everywhere"; `docs/` guides touched get the voice/drift guards run
  (product-tense, no roadmap vocabulary, badge-not-prose).
- In: the live walk (`scripts/walk_hs84_live.py`, staying in `scripts/` as
  the regression rig): on the REAL hub → the `.43` llama.cpp — author ONE
  profile in `/profiles`; assign it to an agent, to meeting intel, and to
  dictation in the settings pickers; then (1) a persona thread answers on
  it, (2) an imported meeting re-processes to artifacts on it, (3) a
  dictation rewrite runs on it — every beat asserted, badges wearing
  `☁ … · 192.168.1.43`, doctor naming the profile for both pipelines.
  Screenshots committed.
- In: BACKLOG.md row S flipped to shipped-across-phases with the map
  (HSM Phase 24 / mesh / Phase 83 / this phase); roadmap README + phase
  status per the operating cadence; `final-summary.md` on close.
- In: the deferred decision on deleting the legacy config fields gets
  resolved here (delete as a rider if the walk proves the picker path and
  the owner agrees; otherwise file the follow-up and record it).
- Out: new features; Apple-surface docs (HSM track owns them).

## Acceptance criteria

- [ ] The walk passes end to end on the real hub → `.43`, all three beats
  asserted in one run, no endpoint URL entered outside `/profiles`.
- [ ] Doctor output captured in evidence naming the profile per pipeline.
- [ ] Docs guards green (`uv run pytest -q tests/unit -k "doc or voice"`);
  touched guides read product-tense.
- [ ] BACKLOG row S, roadmap README pointer/index, phase status, and
  final-summary all updated in the closing commit(s).
- [ ] Full suite green: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Test plan

- Unit: the docs guards above.
- Integration: the full suite command above.
- Manual / device: the live walk IS the manual proof (sandboxed Bash can't
  reach the LAN — run the walk outside the sandbox, per the standing
  gotcha).

## Notes / open questions

- Keep the walk script self-cleaning like `walk_hs83_live.py`; reuse its
  token-wrapper arrival beat so the auth fix stays regression-covered.
