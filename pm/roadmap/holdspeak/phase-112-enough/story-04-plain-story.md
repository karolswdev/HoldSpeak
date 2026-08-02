# HS-112-04 - The plain story

- **Project:** holdspeak
- **Phase:** 112
- **Status:** backlog
- **Depends on:** HS-112-01, HS-112-02, HS-112-03
- **Unblocks:** HS-112-05
- **Owner:** unassigned

## The thesis (the bar)

The owner: "enough with me not really even understanding what
HoldSpeak does and what HoldSpeak is." The docs story (the standing
per-phase rule: after features, before closeout, touching the real
entry points). The bar: **the README's first screen says what
HoldSpeak IS in one paragraph a Senior Software Architect nods at,
and the getting-started path is the phase's own three moves — seed
the desk, set the dial, hold the key.** Every claim truth-audited to
the shipped tree; owner vocabulary; no feature tour.

## Method

1. The one paragraph, written last after 01-03 settle the surfaces:
   what it is, where it runs, what leaves the machine (the egress
   badge stance, one line, never a privacy novel).
2. `README.md` + `docs/GETTING_STARTED.md` restructured around the
   three moves; the config docs point at the one dial and stop
   documenting the dead fields.
3. Prune: entry-point docs that describe retired surfaces
   (the raw settings boxes, the dry-run-only deck) are corrected the
   same commit their surfaces die — this story sweeps what 01-03
   left and reconciles `docs/SECURITY.md` / architecture entry
   points if the phase moved them.

## Test plan

- Truth audit: every claim in the touched pages maps to a shipped
  file:line on the tree at HEAD.
- The three-move quickstart executes verbatim on a fresh HOME
  (doubles as HS-112-05 rehearsal).
- Grep: zero README/getting-started references to
  `intel_cloud_base_url`, `openai_compatible_base_url`, or the
  dry-run deck as the dictation entry point.
- The owner-legibility check rides to the sitting: the paragraph is
  the exhibit's first page.
