# HoldSpeak docs style guide

The 13 guides were written across many phases and drifted in tone and shape.
This is the **floor** they should all clear — a shared voice and a standard page
skeleton — so the set reads as one product, not an anthology. It is a floor, not
a cage: reference docs keep their depth; a doc may add sections, just not skip the
spine.

Companion to [`DOC_AUDIT_2026-06.md`](./DOC_AUDIT_2026-06.md) (accuracy) — this
one is **voice + structure + navigation**.

## Voice

- **Direct and second-person.** "Hold your hotkey, speak, release." Address the
  reader as *you*; HoldSpeak is *it*. Prefer the imperative for steps.
- **Confident, not breathless.** State what it does plainly. No marketing
  superlatives in the guides (the README carries the pitch; guides carry the
  truth).
- **Honest over hype.** Pre-release is pre-release; off-by-default is stated as
  such; "100% local" only where literally true (the model endpoint you point at is
  yours). If a claim isn't true today, don't write it — file it. Canon wins over a
  drifted doc; every claim is grounded in live code.
- **Active and tight.** Cut hedging and repetition. One idea per sentence; one job
  per paragraph.
- **Terms, consistently:** *dictation* (not "voice typing" mid-guide once you've
  introduced it), *meeting mode*, *the dictation pipeline*, *intel* for LLM meeting
  extraction, *actuator* for the propose→approve→execute kind, *desktop presence*
  for the ambient HUD, and *project knowledge* for the whole capability of
  teaching the copilot about a repo. Project knowledge has two parts. *Project
  facts* (UI tab **Project Facts**, formerly "Project KB") is the
  `.holdspeak/project.yaml` `kb:` map: exact values the `kb-enricher` stage stamps
  into block templates verbatim via `{project.kb.*}` placeholders, no LLM.
  *Project context* (UI tab **Project Context**) is the **separate** `.hs/`
  Markdown files: background the optional `project-rewriter` LLM stage reads. The
  two are distinct and easily confused, so gloss them on first use and never use
  one to mean the other (facts are stamped in verbatim; context guides a rewrite).
  The on-disk names (`.holdspeak/project.yaml`, `.hs/`, `kb-enricher`,
  `project-rewriter`, `{project.kb.*}`) are unchanged; "facts" and "context" are
  the user-facing names. Code identifiers in `backticks`.

## Product-tense, not roadmap vocabulary (guard-enforced)

User-facing docs describe the product as it is, not the project's build history. A
reader installing HoldSpeak has never heard of a "phase" and does not know what
`HS-17-05` means, so the guides never carry the internal roadmap or process
vocabulary.

**Banned in user-facing docs** (the root README and `docs/*.md`):

- Phase tags: `Phase 14`, `phase-37`, "the next phase".
- Story ids: `HS-17-05`, `HS-25-03`.
- Process words: `PMO`, "closeout", "the current roadmap", "evidence snapshot".
- Phase-relative tense. Rewrite "Phase 11 shipped the connector contract" as
  "HoldSpeak's connector contract is ...", and "Phase 15 will add TLS" as "TLS is
  future work".

**Kept** (these are product, not roadmap):

- Product nouns: `actuator`, `connector`, `artifact_generator`, the dictation
  pipeline.
- Named architecture specs: `MIR-01`, `DIR-01`, `WFS-01`. They are spec names, not
  phase tags.

**Exempt corpus.** This rule is for what a user reads. The internal record keeps its
phase/story vocabulary by design and is never scrubbed or scanned: `docs/internal/`
(including this guide, which is why it can list the banned tokens above),
`docs/evidence/`, `docs/assets/`, and `pm/roadmap/`.

**Enforced.** A case-insensitive guard in `tests/unit/test_doc_drift_guard.py`
(`test_no_user_facing_doc_leaks_roadmap_vocabulary`) fails the build when a
user-facing doc carries a numbered or tagged leak. It catches the high-signal tags;
bare process-speak with no number ("a separate phase") is on you and the reviewer to
keep out.

## The standard page skeleton

Every user-facing guide clears this spine, in this order:

1. **Title** (`# …`) + an optional pixellab graphic.
2. **Lede** — one or two sentences: *what this does* and *why you'd read it*. No
   throat-clearing. Link the prerequisite doc if there is one ("read [Getting
   Started] first").
3. **Quickstart / TL;DR** — the shortest path to a working result (a command
   block, a numbered list, or a "see it work" pointer).
4. **Reference** — the depth: configuration, options, the contract. Sectioned with
   `##`/`###`; a long doc may open with a table of contents.
5. **Troubleshooting** — a symptom → cause → fix table where the surface has common
   failure modes.
6. **`## The voice guard (POSITIONING.md is the canon)

User-facing prose follows the voice rules in
[`POSITIONING.md`](./POSITIONING.md), and three of them are enforced by
`tests/unit/test_doc_drift_guard.py` over the same corpus as the vocabulary
guard (root README + non-recursive `docs/*.md`, fenced code blocks exempt):

- **No em/en dashes in prose.** Use a period, comma, colon, or parentheses.
  A doc line that quotes a real UI string containing a dash must match the
  UI verbatim and be added to the guard's `_VERBATIM_UI_QUOTES` allowlist.
- **No AI-vocabulary tells** (delve, seamless, the verb leverage,
  supercharge, effortless, game-changing, cutting-edge, "is a testament",
  the "it's not just X" tic). Compounds and plain logical uses
  ("highest-leverage", "every meeting, not just the visible page") stay
  legal; the patterns are tuned for zero false positives on the corpus.
- **Canonical feature names only.** One name per surface, declared in the
  POSITIONING.md table; the guard bans the drift-prone synonyms (e.g.
  "voice macros" for voice commands). New surfaces add a canon row in the
  phase that ships them.

## See also`** — 2–4 cross-links, each with a short value prop (see below).

Reference/developer docs (Plugin Authoring, Connector Development, Device
Protocol) keep their own deep structure but still carry a one-line lede and a
`## See also` footer.

## The privacy / local-first callout

When a doc touches what's stored or what can leave the machine, state it inline
with a blockquote, in the same shape everywhere:

> **Local-first.** <what stays local>. Nothing leaves your machine except the
> model endpoint you point at (local or LAN is fine).

The authoritative version is [`SECURITY.md`](../SECURITY.md); guides summarize and
link, not re-derive.

## Cross-links & anchors (what the link-check enforces)

- **Relative links only** between docs (`./FILE.md`, `../README.md`) — never an
  absolute repo path or a bare filename. The dangling-link guard
  (`tests/unit/test_doc_drift_guard.py`) fails the build on a path that doesn't
  resolve.
- **Anchors** follow GitHub's slugger: lowercase, punctuation `().,&` stripped,
  spaces → hyphens. A heading like `## 11. Desktop Presence (ambient, on-desktop
  status)` slugs to `#11-desktop-presence-ambient-on-desktop-status` (the
  parenthetical *words* stay). Verify a deep link against the actual heading — do
  not hand-guess a shorter slug.
- **`## See also` footer** — the standard footer. Use that exact heading (not
  "Related Docs" / "Where to go next"). Each line: a link + an em-dash + a
  one-line value prop:
  ```markdown
  ## See also

  - [The doc audit](DOC_AUDIT_2026-06.md) — accuracy + the canonical facts.
  - [The plugin RFC](PLAN_ARCHITECT_PLUGIN_SYSTEM.md) — design rationale.
  ```

  Targets are relative to the *linking* doc: a sibling in the same folder is a
  bare `FILE.md` (as above — both siblings of this style guide); a guide in
  `docs/` reaches `internal/` as `internal/FILE.md`, and `internal/` reaches a
  guide as `../FILE.md`.

## The index is a map, not a list

`docs/README.md` groups guides by **journey** (Start here · Dictate · Meet ·
Extend · Operate & Trust), each entry a one-line value prop scannable in seconds.
Keep its journeys and names in lockstep with the README's "Where to go next"
table — same journeys, same names.

## See also

- [`DOC_AUDIT_2026-06.md`](./DOC_AUDIT_2026-06.md) — the accuracy audit + canonical
  facts the guides are measured against.
- [`../README.md`](../README.md) — the public entry; the index map mirrors its
  "Where to go next" table.
- [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) — dev setup, the test command,
  and the commit-contract workflow.
