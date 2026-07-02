# Evidence — HS-76-01 — The truth audit (the drift ledger)

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-76-documentation-sweep`)
- **Method:** three parallel read-and-verify passes over 22 user-facing
  docs, every claim checked against shipped code with file:line evidence;
  compiled here. A fresh screenshot pass fed the fix stories and caught a
  shipped bug on its own (below).

## The ledger

### HIGH — the fix targets

| Doc | The drift |
|---|---|
| `README.md` | Never presents the Desk (the owner-declared main surface is invisible on the public front door); preview described as wake-word-only (the shipped `preview_before_type` is a general opt-in); run-born artifacts absent; the room structure (`/`, `/dictation`, `/history`, `/studio`) never named. → **HS-76-02** |
| `docs/ARCHITECTURE.md` | The component map collapses the whole frontend into one box — no desk island, no runtime bus (the one `/ws` owner is invisible), no `primitives.py` run subsystem; the pipeline diagram ties preview to the wake fork only; run-born artifacts absent from the meeting-pipeline diagram. → **HS-76-03** |
| `docs/README.md` (index) | "The web app opens on **Home**" (retired in 73); the Desk filed under "Extend" instead of "Start here"; the four-destinations nav model is the pre-Desk IA. → **HS-76-05** |
| `docs/WEB_DESK.md` | The framing is inverted: "the Desk (`/desk`) lives in the Studio tier; the two modes stay the front door; Home carries an Enter-the-Desk entry" — all retired; "Tidy in the header" (there is no header); the Record orb, the agent rail, and the create chips are absent entirely. → **HS-76-04** (rewrite) |
| `docs/SECURITY.md` | Module refs to files that no longer exist (`holdspeak/db.py` → `db/core.py`; `intel.py` → `intel/providers.py`); **the §4 egress table omits three shipped egress doors**: the desk webhook connector (`desk_actuators.py:135`, arbitrary approved text to any configured endpoint), the desk GitHub issue write (`gh issue create`, distinct from the read-only enrichment row), and the desk Slack relay (non-meeting sends on the same webhook URL); one stale line anchor. → **HS-76-05** (first in line — a security doc's egress table must be complete) |

### MED

| Doc | The drift |
|---|---|
| `docs/MEETING_MODE_GUIDE.md` | "Live Dashboard (`/`)" twice — the dashboard lives at `/live`; "the web server launches when a meeting starts" (it is always-on). → **HS-76-05** |
| `CHANGELOG.md` | Trails HEAD by three shipped features (the Desk front door, run-born artifacts/schema v6, the preview gate); no populated `[Unreleased]`. → **HS-76-05** |

### LOW

- `docs/DICTATION_PIPELINE_GUIDE.md`: complete except `preview_before_type`
  (one knob missing from "every config knob"). → HS-76-05
- `docs/USER_GUIDE.md`: accurate; could disambiguate the two preview
  mechanisms (wake default vs the opt-in dictation gate). → HS-76-05
- `docs/GETTING_STARTED.md`, `MODELS.md`, `DICTATION_COPILOT.md`,
  `VOICE_COMMANDS.md`, `ACTIVITY_PREBRIEFING.md`, `CADENCE.md`,
  `RELEASING.md`: **verified current** (the per-phase docs stories did
  their job). The six subsystem docs (plugin/connector/device/hooks/
  aipi/firefox): skimmed, no rot.

### The strays (an owner decision, surfaced not taken)

Six root-level files are dead scratch from March–May 2026 (`CODEX_IDEAS.md`,
`IDEAS.md`, `TODO.md`, `INTEGRATION_NOTES.md`, `HOLDSPEAK_REFACTORING.md`,
`PLAN_TEST_FRAMEWORK.md`) — e.g. `TODO.md` self-titles "current working
roadmap" but predates the last 40 phases, and `PLAN_TEST_FRAMEWORK.md`
describes an app a fraction of today's size. They read as live docs to a
visitor. **Recommend deleting or moving to an archive/ dir; not done
unilaterally.**

## The bug the audit's screenshot pass caught (fixed in 349646d)

The Phase-75 PreviewCard's `display: flex` overrode the `hidden`
attribute's UA style — **an empty card was visibly parked on every route**
with no armed preview. The P75 proofs had asserted the attribute, not
computed visibility. Fixed (one CSS line); the reshoot harness now asserts
`is_visible()` false.

## Acceptance criteria — re-checked

- [x] Every user-facing doc read against shipped reality with file:line
      evidence; fix-here / verified-true / owner-decision buckets.
- [x] The ledger routes each drift to a fix story.
