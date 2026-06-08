# HS-52-06 — Docs: the Voice Commands guide

- **Project:** holdspeak
- **Phase:** 52
- **Status:** done
- **Depends on:** HS-52-04, HS-52-05
- **Owner:** unassigned

## Problem
Voice commands run real system actions, including shell commands, off a voice keyword.
That power and its safety model have to be documented clearly and honestly, in
product-tense, and the doc must obey the Phase-51 roadmap-vocabulary guard.

## Scope
- **In:**
  - A "Voice commands" user guide (e.g. `docs/VOICE_COMMANDS.md`): what they are, the
    action kinds (open a URL, launch an app, run a shell command, type a snippet), how to
    add one in the settings cockpit, and the safety model stated plainly: off by default,
    you own the risk because you configure the mapping, the match is a deterministic
    whole-utterance keyword (it selects which macro fires, it never composes a command),
    each macro is bounded to its configured action, and every fire is audited.
  - Link it into the docs index (`docs/README.md`) under the right journey; add to the
    README "Where to go next" table if appropriate. Keep the index a map (`DOCS_STYLE.md`).
  - Product-tense, no roadmap vocabulary (the Phase-51 guard will fail otherwise). Run the
    `humanizer` skill over the new doc.
- **Out:** new feature work; internal design docs.

## Acceptance criteria
- [x] `docs/VOICE_COMMANDS.md` exists: the action kinds, the add/test/save walkthrough,
      and the off-by-default + you-own-the-risk + deterministic-match model stated
      honestly (including that shell runs real code); every claim grounded in the shipped
      board + dispatch.
- [x] Linked in `docs/README.md` under "Dictate"; the index stays a map.
- [x] Passes the Phase-51 roadmap-vocabulary guard and the link/image guards
      (`uv run pytest -q -k "doc_drift or doc_guard or doc"` -> 75 passed); `humanizer`
      run (one tailing-negation fixed), no em/en dashes, no roadmap vocabulary.
- [x] `npm run build` n/a; 0 `_built/` tracked.

## Test plan
- `uv run pytest -q -k "doc_drift or doc_guard or doc"`; manual read as a new user
  deciding whether to enable this.

## Notes / open questions
- This is the dedicated docs story (standing rule). Be honest about the risk; do not
  undersell that this runs local code. The Phase-51 guard now protects this doc; keep
  `Phase 52` / `HS-52-xx` out of it.
