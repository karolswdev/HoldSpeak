# HS-46-02 — The README, reimagined (the 10-second hook)

- **Project:** holdspeak
- **Phase:** 46
- **Status:** backlog
- **Depends on:** HS-46-01
- **Unblocks:** HS-46-05
- **Owner:** unassigned

## Problem
The README (205 lines) reads like a spec sheet: a competent one-liner, then a
feature list. It has no 10-second hook, buries the best stories (it *learns you*;
your **voice** gets the afterlife your **meetings** do; 14 real LLM-backed
plugins; 100% local), and repeats itself ("What it does" / "Intelligence
Pipeline" / "Meeting intelligence plugins" overlap; pre-release stated twice;
AIPI-Lite gets two long paragraphs). The user's read: *too low on cool facts,
slightly too large and repetitive.* **The graphics are loved and stay.**

## Scope
- **In:**
  - A **bold reimagining** (user-chosen direction): open with a real **hook**
    ("Hold a key. Speak. It types — anywhere. 100% local. And it learns you.") +
    a **"Why it's different" cool-facts strip** (local-first; learns you via
    journal + correct-in-the-moment + replay; meetings *and* voice both get a
    reviewable afterlife; 14 real LLM plugins; bring-your-own model; AIPI-Lite
    companion; desktop presence — each a punchy line with a link).
  - **Keep every graphic** — the logo, the workflow-map table, the operator-loop
    GIF, the AIPI device art — repositioned for impact, not removed.
  - A crisp **capability matrix** (what it does, at a glance) and a **60-second
    start** (the install + `doctor` + launch), with the optional extras trimmed.
  - **Cut the repetition + bloat:** fold "Intelligence Pipeline" into the hook;
    trim AIPI-Lite to a teaser + link; reduce the 14-plugin table to a teaser +
    link to the authoring/meeting guide; move the raw config block to a linked
    doc; state pre-release **once**.
  - Keep a tight **"Where to go next"** table (the journey map) and the
    badges/license/contributing footer.
  - **Materially shorter** — target ~130–150 lines (from 205) without losing a
    single graphic.
- **Out:** the other docs (HS-46-03/04/05); new graphics. README only.

## Acceptance criteria
- [ ] The README opens with a 10-second hook + a cool-facts highlights strip;
      the journal/replay "it learns you" story is above the fold.
- [ ] **Every** existing pixellab graphic is still present (logo, workflow map,
      operator GIF, AIPI art).
- [ ] Repetition removed (no overlapping "what it does"/"pipeline"/"plugins"
      re-description; pre-release stated once; AIPI + plugin depth linked out).
- [ ] Materially shorter (target ~130–150 lines) while keeping a quickstart, the
      capability matrix, and the "where to go next" map.
- [ ] Honest: pre-release banner kept; no claim contradicts local-first; cool
      facts are all true (cross-checked against HS-46-01).
- [ ] Doc-drift + dangling-link guards green; a **before/after** of the README is
      captured (line count + rendered snapshot or excerpt).

## Test plan
- Unit: `uv run pytest -q -k "doc_drift or link"`.
- Manual: render the README (GitHub/preview); confirm every graphic resolves,
  links work, and it reads as a hook in the first screen.

## Notes / open questions
- The "cool facts" must stay *true* (honesty invariant) — lean on HS-46-01's
  audit for the claims.
- Decide cool-facts home here (README strip vs a dedicated doc) — default to a
  README strip; only spin out a `HIGHLIGHTS` doc if it earns its place (revisit in
  HS-46-05).
