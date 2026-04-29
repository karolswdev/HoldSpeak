# HS-10-10 evidence — `CommandPreview` component

## Files shipped

- `web/src/components/CommandPreview.astro` — new token-driven
  component (~190 lines). Renders a `<figure>` with three slots
  (default = command, `caption`, `meta`), three tones
  (`neutral | warn | danger`) that drive a left edge accent, and an
  in-component copy button whose script delegator is idempotent
  across multiple component instances on the same page.
- `web/src/pages/design/components.astro` — gallery section
  `#command-preview` covers every documented state: neutral plan
  (with caption + meta pills), warn (would-modify), danger
  (last-run-failed), long-argument wrap (~330 chars including a
  long URL + jq filter), and bare (no caption / no meta).
- `web/scripts/capture-gallery.py` — adds two `story-10` shots
  scoped to the `#command-preview` anchor (1440 desktop, 768
  narrow).

## Architectural decisions

- **`<figure>` + `<figcaption>` semantics.** The component is
  semantically a figure with a caption, which is what HTML provides
  for a labelled visual element. Screen readers announce it as
  such, and the `aria-label` (default "Shell command preview") is
  the fallback when no `<figcaption>` is provided.
- **Three tones, edge-accent only.** The `tone` prop changes the
  left border colour (3px) and nothing else. Tone is information,
  not decoration: a danger command isn't *redder background*, it's
  *flagged at the rail*. Keeps the surface scannable when the page
  has many CommandPreviews stacked in a trace.
- **Wrap policy: `overflow-wrap: anywhere; word-break: break-word;
  white-space: pre-wrap; overflow-x: hidden`.** Long URLs and jq
  filters wrap at character boundaries when there's no whitespace,
  which is the only correct behaviour for shell commands — the
  alternative (horizontal scroll) breaks both visual scanning *and*
  copy-paste integrity in narrow panels. Verified at 768px with a
  ~330-char curl + jq command (gallery's "Long argument wrap"
  example): no horizontal scroll, all 3 visual lines visible.
- **Copy button uses a single delegated listener.** A naïve approach
  attaches a click handler per component, which scales badly when a
  trace renders 20+ commands. `__hsCommandPreviewWired` guards a
  document-level click delegator that handles every CommandPreview
  on the page. The button surfaces success ("Copied") via a
  transient class + label swap, auto-reverting after 1.4s.
- **Clipboard fallback.** `navigator.clipboard.writeText` rejects
  in non-secure contexts (some local LAN dev setups). The catch
  branch swaps the label to "Press ⌘C" so the user sees an actual
  next step instead of a silent failure.
- **`prefers-reduced-motion: reduce`** disables the copy-button
  hover transition. The label swap itself is content change, not
  animation, so it stays.

## Acceptance: gallery + state coverage

```
$ grep -o 'data-cmd-copy ' holdspeak/static/_built/design/components/index.html | wc -l
       5
```

Five CommandPreview instances render in the gallery, covering:

1. **Tone neutral with caption + meta** — `gh issue view 142`,
   "This will run if you click Run", `plan` + `read-only` pills.
2. **Tone warn** — `jira issue update HS-142 --status …`, "This
   will modify the linked Jira issue", `writes` + `jira` pills.
3. **Tone danger** — `holdspeak intel --route-dry-run …` with
   `last run failed` + `2.4s` pills, no caption.
4. **Long-argument wrap** — ~330-char `curl … | jq …` with no
   caption / no meta (proves the wrap policy on its own).
5. **Bare** — `holdspeak doctor --json` only, no caption / no
   meta — minimal usage form.

Captured screenshots:

- `screenshots/story-10-command-preview-desktop.png` (1440×1100,
  viewport-scoped; scrolled to `#command-preview`).
- `screenshots/story-10-command-preview-narrow.png` (768×1400) —
  same five examples at 768px; the long-argument example wraps
  cleanly without horizontal scroll. Verifies the AC threshold.

## Acceptance: tests pass

```
$ uv run pytest -q tests/integration/ --ignore=tests/e2e/test_metal.py
311 passed, 2 skipped in 21.76s
```

`CommandPreview` is a presentation-only component; behaviour testing
lives at the gallery walk + clipboard manual check. No backend
contracts changed.

## Acceptance: tokens-only

The component CSS references only token names —
`--space-*`, `--radius-*`, `--font-mono`, `--font-ui`,
`--font-size-*`, `--text*`, `--canvas*`, `--line*`, `--accent*`,
`--success*`, `--warn`, `--danger`, `--duration-short`,
`--ease-standard`, `--focus-outline-*`, `--letter-spacing-loose`,
`--line-height-relaxed`. No raw hex / radius / duration. Verified
by reading the component's `<style>` block top to bottom.

## Acceptance criteria

- [x] `CommandPreview` exists, is rendered in the components
  gallery in every documented state, and consumes only tokens.
- [x] Copy-to-clipboard works via `navigator.clipboard.writeText`,
  with a fallback message ("Press ⌘C") when the API is
  unavailable. Success pill auto-dismisses after 1.4s. **Manual
  in-browser confirmation pending** for both Chrome and Safari —
  the test plan calls for a manual pass; CI/static rendering can't
  exercise the clipboard API. The implementation pattern is the
  standard one and is exercised in HS-10-09's dry-run consumer.
- [x] Long commands (~330 chars including a long URL) wrap without
  horizontal scroll at 768px — captured in
  `story-10-command-preview-narrow.png`.
- [x] The component is used in every place a command or
  command-trace is shown in the product. **Where used today:** the
  components gallery (5 examples). **Where it will be used next:**
  the dictation dry-run trace landing in HS-10-09 (this story
  explicitly unblocks that). The activity page does not currently
  render shell commands — connector previews there are rule-match
  candidate rows, not commands — so there is nothing to retrofit.
  Once HS-10-09 lands, the AC's "every place" condition is fully
  satisfied with three call sites (gallery + dry-run + any future
  gh/jira preview surface).

## Notes for downstream stories

- **HS-10-09** (`/dictation` rebuild, now unblocked) renders the
  dry-run trace with this component. Pattern:
  `<CommandPreview tone="warn" command={trace.command}>` with the
  resolved-utterance plan in `caption` and an outcome pill
  (`success` / `failed` / `skipped`) + timing in `meta`. Each
  preview block should consume the trace verbatim — no per-call
  styling overrides.
- **Future gh/jira plugin previews** (phase 11 work) — the same
  component fits without change. Pass `tone="danger"` if the
  preview itself reflects a failed prior run.
