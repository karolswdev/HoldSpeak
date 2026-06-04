# Evidence — HS-36-02: Copy-as-Markdown per artifact

**Date:** 2026-06-04. **Branch:** `phase-36/hs-36-01-artifact-card-shell`.

## What shipped

A per-artifact **"Copy"** button in each elevated card header (the slot HS-36-01
left) and a **"Copy all"** control in the Artifacts section header. Both serialize
the artifact `structured_json` to clean Markdown — driven by the artifact *data*
(via the same `*For(artifact)` accessors the card renders from), so a collapsed card
still copies — and write it to the clipboard reusing the `CommandPreview` pattern
(async `navigator.clipboard.writeText`, copied-state label, graceful `Press ⌘C`
fallback when the clipboard is blocked).

### Files

- `web/src/scripts/history-app.js` — `artifactMarkdown(artifact)` (per-type
  serializer), `allArtifactsMarkdown()` (meeting-wide concat under a `# … — Artifacts`
  heading), `copyMarkdown(text)` (clipboard write, returns success bool).
- `web/src/pages/history.astro` — per-card `.artifact-card__copy` button (local
  `copyState` x-data: `idle`/`done`/`fail`), `.artifact-section-head` +
  `.artifact-copy-all` button (`copyAllState`), and the Signal CSS for both
  (hover → accent, copied → success, focus ring), mirroring `CommandPreview`.

Serializers are pure (`artifact → string`): tabular types → a Markdown table with
`|` escaped and empty cells → `—`; timelines → an ordered list; sectioned types
(stakeholder update / decisions / requirements / ADR / milestones / announcements)
→ `###` headings; the diagram type → a ```` ```mermaid ```` fence; unknown/no-render
types fall back to `body_markdown`.

## Verification

### 1. Serializer spot-check (Node harness over the real module)

Loaded `web/src/scripts/history-app.js`, instantiated `historyApp()`, and ran the
serializers over sample artifacts. Output (verbatim):

```
===RISK===
## Risks

**Type:** risk register

| Risk | Impact | Likelihood | Mitigation | Owner |
| --- | --- | --- | --- | --- |
| DB migration \| rollback hard | high | medium | stage it with a flag | Ana |
| vendor SLA | low | — | — | — |

===INCIDENT===
## Outage

**Type:** incident timeline

1. **14:02** — pool exhausted
2. rolled back

===STAKEHOLDER===
## Weekly

**Type:** stakeholder update

**On track**

### Highlights
- shipped X

### Next steps
- ship Y

===ALL (head)===
# Q3 Planning — Artifacts

## Risks
```

Confirms the acceptance criteria: tabular → Markdown table (with the `|` in
"DB migration | rollback hard" escaped to `\|`, the embedded newline in the
mitigation collapsed to a space, missing cells → `—`); timeline → ordered list;
sectioned type → headings; "Copy all" → meeting heading + concatenation.

### 2. Bundle rebuilt + helper present

```
$ cd web && npm run build      # ✓ built in 3.19s, 8 page(s)
$ grep -rl "artifactMarkdown" holdspeak/static/_built/   # holdspeak/static/_built/history/index.html
```

The bundle (`holdspeak/static/_built/`) is a **gitignored** build product — rebuilt
here to verify the source reaches it; **not committed** (built at install from
`web/src`). The referenced Signal tokens (`--accent-on`, `--success`, `--success-soft`)
all exist in `web/src/styles/tokens.css`.

### 3. Full suite green

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2020 passed, 15 skipped in 54.19s
```

Unchanged count vs HS-36-01 (2020/15) — additive UI change; the spoken-e2e artifact
selectors (`.risk-table tbody tr`, `.incident-timeline li`, …) are untouched (the
copy buttons are *added* to the card header, no existing class renamed).

## Notes

- Visual confirmation of the buttons in-card is folded into the HS-36-06 closeout,
  which re-captures the before/after meeting in the new cards (the copy gadgets are
  visible there); the per-type Markdown correctness is gated here by the serializer
  harness above (the story's documented gate).
- Clipboard-blocked path: `copyMarkdown` returns `false` on a `writeText` reject; the
  button then shows `Press ⌘C` for 1.4s and never throws — matching `CommandPreview`.
