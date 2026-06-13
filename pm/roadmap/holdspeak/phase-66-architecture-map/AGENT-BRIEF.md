# Phase 66 — Agent Brief (read this first)

**Phase 66 — The Architecture Map** for HoldSpeak. Opened on owner
direction ("As far as pipeline architecture, architectural diagrams,
mermaid... shouldn't we have a dedicated phase where we really nail it?").

## 0. Mission

Give a developer one place to understand how HoldSpeak actually runs, with
diagrams that render. Today there is no system-overview doc, no end-to-end
pipeline picture, and three Mermaid blocks in the whole corpus. POSITIONING
says the audience is people who will read the code; this is the map they
should hit first.

## 1. The one thing you must not get wrong

**A diagram that does not render is worse than no diagram.** Every Mermaid
block must parse and render (verified, not eyeballed), and a guard must
keep it that way. And every diagram must match the SHIPPED code paths, not
an idealized design. When the diagram and the code disagree, the code
wins; trace it before you draw it.

## 2. Rules (the standing set)

PMO gate; no `Co-Authored-By`; cadence per shipping commit; one PR, branch
`phase-66-architecture-map`, merged on green; full suite via
`--ignore=tests/e2e/test_metal.py`; docs under the live voice guard
(Mermaid lives in fenced code, which the dash/vocab guard exempts, but the
prose around it is scanned). Docs-only: zero behavior change.

## 3. Ground truth (verified at scaffold)

- **No top-level architecture/system-overview doc exists.** The two
  `docs/internal/ARCHITECTURE_*` docs are module-STRUCTURE (the Phase
  54/63 decompositions), not runtime data flow. Ten `PLAN_*` RFCs are
  design-time and scattered. The docs index has no "how it works" entry.
- **Mermaid renders on GitHub natively** in fenced ```mermaid blocks. Use
  that as the canonical renderer. Whether the Astro docs site renders
  Mermaid is UNVERIFIED — check it; if it does not, either add support or
  keep these as GitHub-rendered docs and say so. Do not block the phase on
  the Astro site.
- **A validator exists**: `npx @mermaid-js/mermaid-cli` (mmdc 11.15.0)
  renders/validates a block (needs a browser; heavy, CI-skippable, run
  locally) — the Playwright/pre-flight pattern. The guard story picks the
  exact mechanism.
- **The two pipelines to diagram (trace these in code, do not guess):**
  - *Dictation:* hotkey (`hotkey.py`) OR wake word (`wake_word.py` +
    `runtime/wake_glue.py`, preview-default) → capture → `transcribe.py`
    (MLX/faster-whisper; the pinned-thread detail) → `dictation_runner.
    run_dictation_pipeline` (intent route, project context, target
    profile, LLM rewrite) → type (`typer.py`) → journal/correct/replay
    loop. Plus voice-command dispatch (`dispatch_voice_command`) and the
    device path (`device_audio_ws.py` → voice typing / agent reply).
  - *Meeting:* live capture or import (`meeting_import.py`,
    `transcript_parse.py`) → windowed transcribe → MIR routing
    (`plugins/router.py`) → `plugins/host.py` → artifacts → aftercare
    (`meeting_aftercare.py`) → the actuator propose/approve/execute flow
    (`plugins/actuator_executor.py`) → Send to Slack (`slack_export.py`).
  - *Trust/egress boundary:* what crosses the machine boundary and the
    gate on each crossing (cloud intel, the wake-model download, Slack
    webhook, connector CLIs, the web bind/auth) — align to
    `docs/SECURITY.md` §egress and the Phase-62 egress-badge posture.
- **The component pieces:** web runtime (the mixin-composed `WebRuntime`),
  the transcriber, the dictation pipeline, the meeting session, the plugin
  host + router, the actuator executor + gated connectors, the device
  bridge, desktop presence/Qlippy, the SQLite DB. The system diagram shows
  how these connect, not their internals.

## 4. Stories

- **HS-66-01 — the system map + the diagram guard.** A new
  `docs/ARCHITECTURE.md`: a short orienting overview + the top-level
  component diagram (the pieces above and how they connect). The
  Mermaid-renders guard (`tests/.../test_mermaid_renders.py` or similar):
  extract every ```mermaid block across the docs and assert each
  parses/renders; CI-skippable like the route pre-flight, green locally.
  GitHub-render verified by eye. Wire a first docs-index pointer.
- **HS-66-02 — the dictation pipeline, diagrammed.** The end-to-end flow
  (hotkey + wake entry, capture, transcribe, the pipeline stages, type),
  the journal/correction/replay loop, voice-command dispatch, and the
  device/ESP path, each as a Mermaid diagram in `docs/ARCHITECTURE.md`
  (or a linked section), with prose that names the real modules. Traced
  against the code.
- **HS-66-03 — the meeting pipeline + the trust boundary, diagrammed.**
  The capture/import → routing → plugins → artifacts → aftercare →
  actuators → Send to Slack flow, and a dedicated trust/egress boundary
  diagram aligned to SECURITY. Traced against the code.
- **HS-66-04 — closeout.** Every diagram re-verified to render (mmdc or
  GitHub preview, recorded); docs index + CONTRIBUTING + a README pointer
  to the architecture map; voice guard + full suite green; final-summary;
  README cadence; PR merged on green; memory.

## 5. Gotchas

- Trace before you draw. The decomposition phases moved a lot; method
  names and module paths changed (e.g. the runtime mixins under
  `holdspeak/runtime/`, `meeting_session/` is a package now). A diagram
  with a stale module name is a bug.
- Keep diagrams legible: a system diagram that tries to show every edge is
  unreadable. One diagram per concern, layered.
- The voice guard scans top-level `docs/*.md` prose; `docs/ARCHITECTURE.md`
  is in scope. No dashes in prose, canonical names, no banned synonyms.
  Mermaid code is exempt (fenced), but node LABELS are read by humans, so
  keep them canon-consistent too.
- Do not invent capabilities to make a diagram tidy. If a path is
  conditional/opt-in (the pipeline, actuators, the wake word), the diagram
  says so.
