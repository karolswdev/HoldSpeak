# Phase 58 — Agent Brief (read this first)

You are picking up **Phase 58 — The Front Door (positioning + the user-facing
docs, revised)** for HoldSpeak. Self-contained: mission, the user's explicit
positioning decisions, verified ground truth, rules, per-story success. If
this brief disagrees with the live docs or codebase, the **codebase wins**.

---

## 0. Mission

The docs grew feature by feature, phase by phase. Each new section is honest
and well-written, but nobody has ever decided **what HoldSpeak's story IS**
and revised the whole user-facing corpus to tell it. The user asked for
exactly that: *"a proper phase. Where we also revise WHAT we are saying, so
that we can be explicit around how to 'sell' this product to our community."*

Two deliverables under one thesis ("the repo can pitch itself"):

1. **A positioning canon** — one internal doc that fixes the story: the
   one-liner, the audience, the pillars, the proof points, the named
   competitive frame, the voice. It becomes project canon; every
   user-facing doc aligns to it, now and in future phases.
2. **The corpus, revised against it** — README.md rewritten as the front
   door (the pitch, the tour, honest comparisons), every top-level guide
   re-framed (ledes that say why the feature matters, consistent feature
   names), with the full humanizer voice pass and the em-dash cleanup
   riding along — and a guard so none of it regresses.

## 0.1 The user's positioning decisions (fixed; do not relitigate)

Asked directly, 2026-06-11:

- **Lead angle: "One copilot, two modes."** The pitch leads with breadth —
  dictate anywhere + meetings that close their own loops, one local
  copilot. Privacy and the learning loop are pillars one rung below the
  lead, not the headline.
- **Audience: developers.** GitHub-native, terminal-comfortable,
  self-hosting, privacy-aware. Docs may assume a shell and a config file.
- **Comparisons: name names, honestly.** An explicit comparison section
  with named tools and trade-offs stated both ways.

---

## 1. The one thing you must not get wrong

**The pitch must stay as honest as the product.** This codebase's entire
documentation culture is honest-by-construction (the learning digest is
"honest at N=0", the import notes state what is approximate, the actuator
card names what egresses). A marketing pass that overclaims would betray
that. Every claim in the new README and ledes must be one the test suite or
a guide can back; comparisons state what the OTHER tool does better too;
superlatives without proof points do not ship.

---

## 2. Rules of the road (non-negotiable)

- **PMO commit gate**: fresh `.tmp/CONTRACT.md` (7 boxes) per commit; one
  done-flip per commit with its `evidence-story-{n}.md`; phase exit ships
  `final-summary.md` in-commit. No `Co-Authored-By`; no `--no-verify`.
- **Operating cadence**: story header + phase status + project README per
  shipping commit.
- **One PR per phase**, branch `phase-58-front-door`, merged on green.
- **Tests**: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- **The Phase-51 vocab guard** stays green over every touched doc
  (product-tense, no roadmap vocabulary).
- **The humanizer skill governs the voice**: no em/en dashes in REVISED
  text (this phase removes the old ones), no AI-vocab, no rule-of-three
  padding, no negative-parallelism tics, plain copulas. Apply it as the
  editing standard for every file touched.
- **Existing doc locks are contracts**: `test_doc_drift_guard.py` pins the
  README plugin-count claim, the Qlippy guarantees, link/image integrity;
  other tests pin exact phrases in guides (grep before changing any pinned
  sentence; update locks deliberately and say so in evidence).
- **Meaning is preserved**: this phase reframes and rewrites; it must not
  drop documented facts, commands, or honest limits. Where content is
  outdated, fixing it is in scope; where it is missing (features shipped
  since the doc was written), adding a concise mention is in scope.

---

## 3. Ground truth (verified at scaffold, 2026-06-11)

**The corpus** (user-facing = root `README.md` + non-recursive `docs/*.md`,
the same scope as the vocab guard): 17 docs + README, ~25k words.

**Current state, measured:**
- Vocabulary is already clean (one "elevate", two "not just" in the whole
  corpus — Phase 51 + per-phase humanizer passes worked).
- Em-dashes are pervasive in pre-Phase-55 text: PLUGIN_AUTHORING 82,
  INTELLIGENT_TYPING_GUIDE 28, DEVICE_PROTOCOL/CONNECTOR_DEVELOPMENT/
  SECURITY 16 each, DICTATION_COPILOT 14, MEETING_MODE_GUIDE 11, README 0.
- README.md (217 lines) has good bones (honest status banner, "Why it's
  different", quickstart, platform table, where-next table) but: the hero
  doesn't lead with "one copilot, two modes"; there is **no comparison
  section**; the feature story under-represents everything since ~Phase 48
  (voice command macros, activity pre-briefing, meeting aftercare, faceted
  search, recording AND transcript import, the config cockpit, Qlippy,
  release-safety/backups as a trust point).
- `docs/README.md` is the second front door (the index with per-doc hooks).

**Locks that pin doc content** (`tests/unit/test_doc_drift_guard.py`):
`_PLUGIN_COUNT_CLAIM` (README must state the real built-in plugin count),
`test_qlippy_doc_states_the_guarantees_verbatim` (the typing guide must
keep "never acts on his own" + the three privacy markers),
`test_no_live_doc_has_a_dangling_relative_link`,
`test_all_embedded_image_refs_resolve`, the vocab guard. Run the doc slice
(`uv run pytest -q tests/ -k doc`) after every file you touch.

**Competitive landscape for the comparison section** (verify claims are
architecture-level and durable; avoid fast-moving feature claims):
cloud dictation (Apple/Google built-ins, Dragon), local Whisper menu-bar
apps (superwhisper, MacWhisper, VoiceInk), AI dictation services
(Wispr Flow, Aqua Voice — cloud), command-and-control (Talon — the
accessibility/coding-by-voice king), and raw Whisper CLIs. HoldSpeak's
durable differentiators: fully local INCLUDING the LLM, the visible
learning loop, one tool spanning dictation AND meeting intelligence with
approval-gated actions, Linux as a first-class platform, open source.
Durable trade-offs to state honestly: Talon is far deeper for hands-free
coding/grammar control; menu-bar apps are simpler to set up; cloud tools
need no local model and can be more accurate out of the box; HoldSpeak is
0.x and Python.

**The assets**: `docs/assets/pixellab/` (brand art), `docs/assets/
screenshots/` (journal, learning digest…), `docs/assets/presence/`
(HUD + Qlippy). Reuse; new screenshots only where a feature has none.

---

## 4. Per-story definition of success

- **HS-58-01 — The positioning canon.** `docs/internal/POSITIONING.md`:
  the one-liner ("one copilot, two modes" angle), the audience statement,
  3-4 pillars each with PROOF POINTS that name the shipped capability
  backing them, the named competitive frame (per-tool: what they do
  better / what we do better / who should pick which), the voice rules
  (the humanizer standard, the no-dash rule, the honesty bar), and the
  canonical feature-name table (one name per feature, e.g. "the dictation
  journal", "meeting aftercare", "Qlippy"). Added to CLAUDE.md's source
  canon and the internal docs. This is the phase's keystone — get it
  reviewed against the user's three decisions before building on it.
- **HS-58-02 — README.md, the front door.** Rewritten against the canon:
  hero + one-liner leading with both modes; a "two modes" tour that gives
  dictation and meetings equal billing and works in the post-48 features
  where they earn it; the honest comparison section (named tools, both
  directions); quickstart/platform/upgrade-trust kept (improved, not
  discarded); the where-next table aligned to the canonical names.
  `docs/README.md` index aligned to the same story. All locks green.
- **HS-58-03 — The core guides.** GETTING_STARTED, USER_GUIDE,
  INTELLIGENT_TYPING_GUIDE, MEETING_MODE_GUIDE, DICTATION_COPILOT,
  VOICE_COMMANDS, ACTIVITY_PREBRIEFING, FIREFOX_EXTENSION_GUIDE: a lede
  per doc that sells the why in two sentences, canonical names throughout,
  the humanizer pass, zero em/en dashes remaining in each finished file.
- **HS-58-04 — The developer + ops docs.** PLUGIN_AUTHORING (the 82-dash
  monster), CONNECTOR_DEVELOPMENT, DEVICE_PROTOCOL, MODELS, SECURITY,
  RELEASING, AGENT_HOOK_INSTALL, AIPI_LITE_DEV_WORKFLOW: same treatment,
  plus these double as the "extend it" pitch to contributing developers —
  the ledes should make building on HoldSpeak sound as deliberate as
  using it.
- **HS-58-05 — The guard.** Extend the doc-drift guard: zero em/en dashes
  in the user-facing corpus (now true, so lockable), an AI-vocab
  blocklist (the humanizer's high-frequency tells), and canonical-name
  consistency for the names the canon declares (catch "the memory tab" vs
  "correction memory" style drift where the canon picked one). Proven
  both ways (a seeded violation fails).
- **HS-58-06 — Closeout.** A fresh-eyes pass: render README on GitHub
  (push preview), click every link (the lock covers relative ones; spot
  the absolute ones), before/after metrics (dash counts, corpus words),
  the full suite, `final-summary.md`, BACKLOG/README flips, PR merged on
  green.

---

## 5. Gotchas

- **The plugin-count lock**: the README rewrite must keep a literal
  "N built-in plugins" claim matching the registry count.
- **Absolute GitHub URLs** in README (raw.githubusercontent links for
  images) are the pattern for PyPI rendering — keep absolute URLs there;
  the link lock only checks relative ones.
- **Pinned phrases**: grep `tests/` for any sentence you are about to
  reword (`grep -rn "exact words" tests/`); the Qlippy markers and the
  import-panel truths are asserted.
- **The em-dash rule is for prose**, not for code blocks, tables of
  shell output, or quoted UI strings that genuinely contain dashes —
  check what the guard should exempt (fenced code blocks at minimum).
- **Comparisons age**: keep them architecture-level (local vs cloud,
  static vs learning, dictation-only vs meetings) and date-stamp the
  section ("as of mid-2026") so staleness is visible, not misleading.
- **Don't bloat the README**: the pitch gets stronger by being tighter.
  Target similar length to today's 217 lines, not double.

---

## 6. Where to start

`HS-58-01`. The canon is the keystone — every later story is "align X to
the canon", so the canon must be right first. Build it strictly on the
user's three decisions, present it in the story evidence, then rewrite
outward: README (02), the guides (03, 04), the guard (05), closeout (06).
