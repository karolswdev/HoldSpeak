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
  for the ambient HUD, and *project KB* for the repo's `.hs/` Markdown files (gloss
  it on first use — it's jargon; the `kb-enricher` stage reads it). Code
  identifiers in `backticks`.

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
6. **`## See also`** — 2–4 cross-links, each with a short value prop (see below).

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
