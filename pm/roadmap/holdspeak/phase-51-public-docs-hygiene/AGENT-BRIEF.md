# Phase 51 — Agent Brief (read this first)

You are picking up **Phase 51 — Public-Docs Hygiene** for HoldSpeak. This brief is
self-contained: the mission, the exact doc + test seams (mapped against the live
tree at scaffold time), the rules of the road, and a per-story definition of
success. Read it, then read [`current-phase-status.md`](./current-phase-status.md)
and the story you're working. If this brief disagrees with the live status docs or
the codebase, the **codebase wins** — re-verify before trusting any line or number
below.

---

## 0. Mission

Phase 50 cut the release gate; HoldSpeak is now meant to be installed by strangers
from the public repo (and soon PyPI). But the public-facing documentation still
reads partly like an internal artifact. User and operator guides leak the
project's own roadmap vocabulary — phase numbers (`Phase 13 additions`), story IDs
(`HS-17-05`), PMO process words (`closeout`, `the current roadmap`) — which mean
nothing to a new user and signal "half-finished internal tool".

Make the public surface read like a product, not a roadmap:

- **Strip internal roadmap/process vocabulary** from user/operator-facing docs.
- **Rewrite phase-relative claims into product-tense.** "Phase 11 shipped the
  contract" becomes "HoldSpeak's connector contract is ...". The reader never needs
  to know what a phase is.
- **Lock the clean state with a guard** so the next phase that writes a doc cannot
  silently reintroduce the leak.
- **Codify the rule** in the doc voice authority so authors know it up front.

This phase is **release polish + docs hygiene**. It is docs-and-test only. It does
**not** change any product behavior, code path, capture, dictation, plugins,
synthesis, or routing.

---

## 1. The one thing you must not get wrong

**Do not over-scrub.** The goal is to remove *roadmap/process* vocabulary, not
every token that looks internal. Keep:

- **Legitimate product nouns.** `actuator` is a real shipped feature, not roadmap
  vocab. So are `connector`, `artifact_generator`, `plugin kind`, etc. Leave them.
- **Named architecture specs that the docs intentionally reference.** `MIR-01` and
  `DIR-01` are the meeting-side and dictation-side routing specs; `docs/README.md`
  points at them on purpose. They are product/architecture names, not phase tags,
  and they do not match the banned patterns anyway. Leave them.
- **The PMO roadmap corpus itself** (`pm/roadmap/**`) and **`docs/internal/**`** and
  **`docs/evidence/**`**. Those are the historical/internal record and are kept
  verbatim by design. They are explicitly **out of scope** — never scrub them, and
  the guard must **not** scan them.

What you *are* removing, in user/operator-facing docs only: `Phase <N>`,
`HS-<NN>-<NN>`, `PMO`, "closeout", "story", "the current roadmap", "evidence
snapshot" and similar process words, plus phase-relative tense ("Phase 9 shipped
X", "the next phase will ...").

If a sentence's *meaning* depends on the phase reference, rewrite the sentence so a
new user understands the feature, do not just delete the tag and leave a dangling
clause.

---

## 2. Rules of the road (non-negotiable)

- **PMO commit gate.** Every commit needs a fresh `.tmp/CONTRACT.md` (template in
  `pm/roadmap/PMO-CONTRACT.md` §"Contract template", **7** checkboxes; `mkdir -p
  .tmp` first; the hook validates and deletes it). A story flipping to `done` ships
  its `evidence-story-{n}.md` in the same commit; **one** done-flip per commit. The
  phase-exit story needs `evidence-story-{last}.md` **and** `final-summary.md` in
  the same commit. Status line is the list-item form `- **Status:** done`.
- **No `Co-Authored-By` trailer. No `--no-verify`.**
- **Operating cadence.** Every shipping commit updates: the story header status,
  this phase `current-phase-status.md` (row + Last-updated + "Where we are"), the
  project `README.md` (phase row + Current-phase + Last-updated), and any canon doc
  the story touched.
- **One PR per phase, merged when CI green** (Unit · Integration macOS · E2E macOS ·
  Linux Smoke · Route screenshots). Work on a phase branch; at close, push + open a
  PR to `main` + merge with a merge commit on green. Memory
  `feedback_merge_phases_via_pr`.
- **Tests actually run.** Flip a story to `done` only after running the relevant
  tests and reading the output. Full suite:
  `uv run pytest -q --ignore=tests/e2e/test_metal.py`. Type-check is not validation.
- **Run the `humanizer` skill over every doc you edit.** This phase is nothing but
  doc-prose rewriting, so this is not optional polish, it is the work. Invoke the
  `humanizer` skill on each touched file (not just an eyeball pass) and apply its
  fixes before flipping a story to done. No em or en dashes, no emoji-decorated
  bullets, no rule-of-three padding, no "not X but Y". Plain and direct.
  (`docs/internal/DOCS_STYLE.md` is the voice authority, and this phase *adds a rule
  to it* — see HS-51-04.)

---

## 3. The ground truth (doc + test seams, mapped + verified at scaffold)

Re-verify before trusting; line numbers drift. The leak inventory below was found
with:

```
grep -rInE 'HS-[0-9]{2}|Phase[ -][0-9]+|PMO|closeout|the current roadmap' \
  README.md docs/ --include='*.md' | grep -v 'docs/internal' | grep -v 'docs/evidence'
```

**Confirmed leaks at scaffold time (user/operator-facing docs):**
- `docs/CONNECTOR_DEVELOPMENT.md:5,316,318,452,454` — "Phase 9 shipped the first
  three connectors; phase 11 ...", "Phase 13 additions", "Phase 11 shipped the
  contract; phase 13 turns it on", "the current roadmap".
- `docs/DEVICE_PROTOCOL.md:310,311,315,389-390,400-401` — "Periodic tick during
  meeting (HS-17-05 ...)", "HS-17-08 / HS-17-13", "Phase 14 is plain ws://",
  "Phase 15's tunnel layer", "Phase 14 uses a single shared secret", "Phase 15+
  should issue per-device PSKs".
- `docs/INTELLIGENT_TYPING_GUIDE.md:135` — "Known-good local dogfood profile from
  HS-19 closeout".
- `docs/RELEASING.md:102` — "See the captured example in the Phase 50 evidence"
  (maintainer-facing, but still a phase tag; rewrite to "the captured release
  evidence").
- `docs/README.md:78-79,84-85` — points at `internal/PLAN_PHASE_*` specs by
  `DIR-01`/`MIR-01` name (KEEP these names) and at `pm/roadmap/holdspeak/` as "the
  project's planning of record" (a deliberate pointer for contributors; keep, but
  confirm the wording reads as "internal planning lives there", not as user
  instruction).

**The root `README.md` is already clean** of phase/story leakage (only legitimate
`actuator` product nouns appear). Confirm, do not churn it.

**The guard seam:**
- `tests/unit/test_doc_drift_guard.py` — the existing live-docs guard (stub-claim
  guard + dangling-link guard + image-ref guard + README plugin-count guard). Extend
  *this* file with the roadmap-vocabulary guard.
- **Critical scope gotcha:** the existing `_live_docs()` helper (l.23-29) returns
  `docs/**/*.md` excluding only `docs/evidence/`, so it **includes `docs/internal/`**
  (its own sanity test asserts `PLAN_ARCHITECT_PLUGIN_SYSTEM.md` is in the set). The
  internal corpus is *allowed* to say "Phase 50". Your new guard must scan a
  **narrower** set: user/operator-facing docs only = the root `README.md` plus
  `docs/*.md` at the top level (or an explicit curated list), **excluding
  `docs/internal/**` and `docs/evidence/**`**. Do not reuse `_live_docs()` as-is for
  the vocabulary guard.

**Voice authority:**
- `docs/internal/DOCS_STYLE.md` — the doc voice rules. HS-51-04 adds the
  "no roadmap vocabulary in user-facing docs" rule here.

---

## 4. Per-story definition of success

- **HS-51-01 — Leak inventory + vocabulary policy.** A short written policy (a
  section in this phase's status doc or a scratch inventory file) that lists every
  offending line in user/operator-facing docs, classifies each as *banned* (phase
  tag / story id / process word) or *keep* (product noun / named spec), and fixes
  the exact scope: which docs are user-facing, which are internal/evidence (out).
  This is the map the scrub and the guard both follow. No code changes.
- **HS-51-02 — Scrub the user-facing docs.** Every banned reference from HS-51-01 is
  gone from the user/operator-facing docs, rewritten into product-tense so the
  meaning survives for a reader who has never heard of a "phase". Legitimate product
  nouns and the `MIR-01`/`DIR-01` spec names are untouched. Doc guards (drift, link,
  image) stay green; humanizer voice (no em/en dashes).
- **HS-51-03 — Lock it: the roadmap-vocabulary guard.** A new test in
  `test_doc_drift_guard.py` that fails when a user/operator-facing doc contains
  `Phase <N>`, `HS-<NN>-<NN>`, `PMO`, or the chosen process words. Scoped to
  user-facing docs only (NOT `docs/internal/`, NOT `docs/evidence/`, NOT the PMO
  corpus). Includes a positive sanity test (the guard actually scans real files) so
  a green result is not vacuous. Green on the post-scrub tree.
- **HS-51-04 — Docs (dedicated docs story).** A rule added to
  `docs/internal/DOCS_STYLE.md`: user-facing docs speak in product-tense and carry
  no roadmap/process vocabulary; what is banned, what is kept (product nouns, named
  specs), and a pointer to the guard that enforces it. Doc guards green; every claim
  grounded in the guard that exists.
- **HS-51-05 — Closeout.** A dogfood proving the guard works both ways: it **catches**
  a planted `Phase 99` / `HS-99-01` line in a user-facing doc, and **passes** on the
  clean tree. Full suite green, `final-summary.md`, phase CLOSED, project README +
  phase status updated per the operating cadence, BACKLOG candidate H flipped to
  shipped, PR to `main` opened and merged on green CI.

---

## 5. Gotchas that will bite you

- **Scope, scope, scope.** The single most likely mistake is scrubbing or guarding
  the internal corpus. `pm/roadmap/**`, `docs/internal/**`, and `docs/evidence/**`
  are frozen history and MUST keep their phase/story vocabulary. The guard scanning
  them would be a permanent red.
- **`MIR-01` / `DIR-01` are not phase tags.** They are architecture spec names. The
  banned patterns (`HS-\d{2}`, `Phase \d+`) do not match them — keep it that way; do
  not write a pattern so greedy it catches them.
- **Don't churn the root README.** It is already clean. Confirm with the grep, leave
  it alone except whatever the guard/policy genuinely requires.
- **Rewrite, don't amputate.** "Phase 14 is plain `ws://` on loopback" carries real
  information (the TLS posture). The fix is "HoldSpeak's device link is plain `ws://`
  on loopback today; ...", not deleting the sentence.
- **The doc you touch is user-facing copy.** Apply the humanizer voice; no em/en
  dashes in the scrubbed lines.

---

## 6. Where to start

`HS-51-01` (the inventory + policy) is the cheapest first win and is the map for
everything after. Suggested sequence: 01 -> 02 -> 03 -> 04 -> 05. The scrub
(HS-51-02) must land before the guard (HS-51-03) can go green; the guard then keeps
the scrub from rotting. Keep it docs-and-test only, change no behavior, and make the
public surface read like a product someone just discovered, not a 51-phase internal
build log.
