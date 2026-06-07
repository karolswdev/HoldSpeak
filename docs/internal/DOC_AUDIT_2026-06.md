# Documentation truth audit — 2026-06

**Story:** HS-46-01 (Phase 46 — Documentation Excellence & the 10-Second Hook).
**Date:** 2026-06-06. **Method:** every claim checked against live code at
`HEAD` of `phase-46-documentation-lift`. Paths below are repo-root relative.

This is the **map** the rest of Phase 46 builds on (HS-46-02 README reimagining,
HS-46-03 voice/structure, HS-46-05 coverage matrix). It is *accuracy only* — voice,
structure, and visuals are explicitly out of scope here. It is also a **template**
for the next doc pass: re-run the same canonical-facts → per-doc-verdict sweep.

## Canonical facts (verified, the yardstick)

These are the code truths the docs are measured against. Source files in parens.

| Fact | Truth | Source |
|---|---|---|
| Built-in meeting-intel plugins | **14**, all real (zero stubs) | `holdspeak/plugins/builtin/__init__.py` (`register_builtin_plugins`) |
| Actuators registered by default | **none** — opt-in via `register_{followup,github_issue,webhook_post}_actuator` | `holdspeak/plugins/builtin/` |
| Intent types | **5**: architecture, delivery, product, incident, comms | `holdspeak/plugins/signals.py`, `router.py` |
| Routing profiles | 5 base chains (balanced, architect, delivery, product, incident) | `holdspeak/plugins/router.py` |
| Dictation journal default | **on** (`dictation.pipeline.journal_enabled = True`), retention 500, local-only | `holdspeak/config.py` |
| Dictation pipeline default | **off** (`dictation.pipeline.enabled = False`) | `holdspeak/config.py` |
| Desktop presence enablement | **config-backed** (`presence.enabled = False` default; Settings / welcome-wizard UI toggle is the path). `HOLDSPEAK_DESKTOP_PRESENCE=1` is a **retained power-user / headless override**, not the primary path | `holdspeak/config.py`, `desktop_presence.py:228`, `web_runtime.py:644` |
| Actuator execution | off + default-safe: `allow_actuators=False`, `allowed_actuators=[]`, `webhook_allowed_hosts=[]` | `holdspeak/config.py` |
| Whisper model default | `model.name = "base"`, `model.backend = "auto"` (MLX on Apple Silicon else faster-whisper) | `holdspeak/config.py` |
| Cloud intel timeout | fixed `DEFAULT_INTEL_CLOUD_TIMEOUT_SECONDS = 180.0` — **not** a config key | `holdspeak/intel/models.py:23`, `engine.py:55` |
| CLI subcommands | **9**: web, meeting, history, actions, intel, dictation, agent-hook, device-psk, doctor | `holdspeak/main.py` |
| Web page routes | **10**: `/`, `/welcome`, `/setup`, `/history`, `/settings`, `/activity`, `/dictation`, `/companion`, `/docs/dictation-runtime`, `/presence` | `holdspeak/web/routes/pages.py` |
| Retired (Phase 32) | `tui` + `menubar` subcommands, `--no-tui`, `textual`/`rumps` deps — gone | `holdspeak/main.py` (absent) |
| Package version | `0.2.1`, pre-release, **not** on PyPI (install from source) | `pyproject.toml:3` |

## Per-doc verdicts

Scope = the **user-facing** set (README + `docs/*.md`) plus the root contributor
docs. `docs/internal/*` (RFCs, phase specs, port plans) and `docs/evidence/*`
(frozen run snapshots) are **provenance, not user guides** — listed at the bottom,
not drift-audited (the standing rule keeps them verbatim).

| Doc | Purpose | Verdict | Findings |
|---|---|---|---|
| `README.md` | Project entry: hook, quickstart, plugin list, nav | **Minor drift** | F1 |
| `docs/README.md` | Docs index / start-here map | **Fresh** | — (links + anchors verified, see F-anchors) |
| `docs/GETTING_STARTED.md` | Install, permissions, first dictation | **Minor drift** | F1 (presence tip) |
| `docs/USER_GUIDE.md` | Day-to-day features + web runtime | **Fresh** | — |
| `docs/MEETING_MODE_GUIDE.md` | Meeting capture, routing, config reference | **Minor drift** | F2 |
| `docs/INTELLIGENT_TYPING_GUIDE.md` | Dictation pipeline, presence §11, journal §12 | **Minor drift** | F1 (presence "Turn it on") |
| `docs/DICTATION_COPILOT.md` | End-to-end copilot walkthrough + demo | **Fresh** | — |
| `docs/MODELS.md` | Bring-your-own-model contract | **Fresh** | — (suggestions match code defaults) |
| `docs/PLUGIN_AUTHORING.md` | `HostPlugin` contract, chains, actuators | **Fresh** | N1 (examples illustrative-but-partial) |
| `docs/CONNECTOR_DEVELOPMENT.md` | Activity connector authoring | **Minor drift** | F3 |
| `docs/DEVICE_PROTOCOL.md` | AIPI-Lite remote-audio WS protocol | **Minor drift** | F4 |
| `docs/AGENT_HOOK_INSTALL.md` | Claude/Codex hook wiring | **Fresh** | — |
| `docs/AIPI_LITE_DEV_WORKFLOW.md` | Firmware + bridge dev workflow | **Fresh** | — |
| `docs/FIREFOX_EXTENSION_GUIDE.md` | Browser activity connector | **Fresh** | — |
| `docs/SECURITY.md` | Threat model, egress boundaries, at-rest | **Fresh** | — (egress invariants match code + tests) |
| `CONTRIBUTING.md` | Dev setup, test cmd, commit contract | **Fresh** | — |
| `CHANGELOG.md` | Release notes | **Fresh** | — (version + retirements accurate) |
| `CLAUDE.md` | Agent working agreement (PMO gate) | **Fresh** | — |

## Drift findings (fixed in this story)

### F1 — Desktop presence is sold as env-var-only, but it's a config toggle now
- **Where:** `README.md:26` ("Enable with `HOLDSPEAK_DESKTOP_PRESENCE=1`"),
  `docs/INTELLIGENT_TYPING_GUIDE.md:444-450` (§11 "Turn it on" → sets the env var),
  `docs/GETTING_STARTED.md:107-112` (Tip → launch with the env var).
- **Claim:** the env var is the (only) way to turn presence on.
- **Reality:** since HS-43-04 presence is **config-backed** — `presence.enabled`
  (default `False`), flipped from the **Settings page / welcome wizard** UI toggle,
  started/stopped live. `desktop_presence_enabled(config_enabled=…)` returns `True`
  on the config flag; the `HOLDSPEAK_DESKTOP_PRESENCE` env var is only a **retained
  force-on override** for headless/power-user launches. (`holdspeak/desktop_presence.py:228`,
  `web_runtime.py:644`, `config.py:380`.)
- **Fix:** lead with the UI toggle as the path; keep the env var as a labelled
  power-user/headless override. (Severity: factual / misleading — users miss the
  canonical path.)

### F2 — `intel_cloud_timeout_seconds` is documented as a config key but isn't one
- **Where:** `docs/MEETING_MODE_GUIDE.md:399` (in the MeetingConfig reference table).
- **Claim:** `meeting.intel_cloud_timeout_seconds` (float, 180.0) is user-settable.
- **Reality:** there is no such config field. The value is the fixed constant
  `DEFAULT_INTEL_CLOUD_TIMEOUT_SECONDS = 180.0` (`holdspeak/intel/models.py:23`),
  passed as a default parameter to the engine (`engine.py:55`) — never read from
  config. Setting it in `config.json` is silently dropped (unknown-key filter).
- **Fix:** remove the row from the config table (the timeout is a fixed default, not
  a knob). Not a code bug — the engine works; the doc over-claims configurability.
  *Follow-up idea (not this story):* if user-tuning is wanted, wire it as a real
  `MeetingConfig` field. (Severity: factual error.)

### F3 — KNOWN_KINDS quick-reference is missing `pipeline`
- **Where:** `docs/CONNECTOR_DEVELOPMENT.md:67`.
- **Claim:** kind is one of `cli_enrichment, candidate_inference, extension_events,
  history_import` (4).
- **Reality:** `KNOWN_KINDS` has **5** members — `pipeline` (HS-13-06, "consumes
  other packs' output") is also valid (`holdspeak/connector_sdk.py:31-39`). The doc
  describes `pipeline` later (its "Phase 13 additions" section) but omits it from the
  line-67 list, so an author checking the quick reference misses it.
- **Fix:** add `pipeline` to the line-67 list. (Severity: factual / incomplete.)

### F4 — Device-protocol example contradicts the doc's own (correct) spec
- **Where:** `docs/DEVICE_PROTOCOL.md:350` and `:358` (the worked turn example).
- **Claim (example):** after `start` the server pushes
  `{"type":"status","text":"Listening..."}` and after `stop`
  `{"type":"status","text":"Thinking..."}`.
- **Reality:** those pushbacks were **removed (AIPI-4-13)** because they clobbered
  the device's persistent bottom widget — stated correctly in the same doc's §6.1
  table (`:288-299`) and matched by the code (`holdspeak/web_runtime.py:2013,2043` —
  "no 'Listening...' / 'Thinking...' pushback"). The example was just never updated.
- **Fix:** drop the two `status` push lines from the example so it agrees with §6.1
  and the firmware-side TX-glyph behavior. (Severity: factual / internal contradiction.)

## Verified-correct (do NOT "fix" — recorded so a future pass doesn't regress them)

- **F-anchors — README + docs index deep links are correct.** `README.md:123-124`
  and `docs/README.md:23,27` link to
  `INTELLIGENT_TYPING_GUIDE.md#11-desktop-presence-ambient-on-desktop-status` and
  `#12-dictation-journal-corrections--replay`. GitHub's slugger keeps the
  parenthetical **words** (it strips only the punctuation `().,&`), so the headings
  `## 11. Desktop Presence (ambient, on-desktop status)` and
  `## 12. Dictation journal, corrections & replay` slugify **exactly** to those
  anchors (note the intentional `--` double hyphen from the removed ` & `). These
  are right; an earlier auto-audit flagged them as broken — that was wrong.
- **README "14 built-in plugins"** matches the registry exactly.
- **Pre-release / not-on-PyPI** framing in README + CHANGELOG matches `pyproject 0.2.1`.

## Noted, not fixed (illustrative, not wrong)

- **N1 — `docs/PLUGIN_AUTHORING.md:104-110`** lists *example* plugins per kind and is
  accurate but not exhaustive (e.g. `incident_timeline`/`risk_heatmap` are also
  synthesizers; `runbook_delta`/`decision_announcement_drafter` also artifact
  generators). The table reads as illustrative ("e.g."), so this is a polish item
  for HS-46-03, not a truth error.

## Provenance docs (listed, not drift-audited)

`docs/internal/*` — RFCs and phase specs kept for contributor context, not
user guides: `PLAN_ARCHITECT_PLUGIN_SYSTEM.md`, `PLAN_PHASE_DICTATION_INTENT_ROUTING.md`,
`PLAN_PHASE_MULTI_INTENT_ROUTING.md`, `PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md`,
`PLAN_MEETING_MODE.md`, `PLAN_MEETING_INTEL_PI.md`, `PLAN_INTEL_STREAMING.md`,
`PLAN_ACTIVITY_ASSISTED_ENRICHMENT.md`, `CROSS_PLATFORM_ROADMAP.md`,
`CROSS_PLATFORM_TASK_BOARD.md`, `LINUX_PORT_PLAN.md`, `LINUX_PORT_EXECUTION.md`,
`RELEASE_HARDENING_CHECKLIST.md`, plus this audit. `docs/evidence/*` — frozen
run snapshots. Both are intentionally verbatim history; the doc-drift guard
excludes `docs/evidence/`.

## Guards

- `tests/unit/test_doc_drift_guard.py` — no live doc claims a `DeterministicPlugin`
  stub; no dangling relative links. **Extended in this story** with a guard that the
  advertised built-in-plugin count (README "N built-in plugins") matches
  `register_builtin_plugins` (14), so the headline count can't silently drift.
  (HS-46-04 added an **image-ref guard** — `<img src>` + markdown images across the
  README + docs resolve.)

## Feature → doc coverage matrix (HS-46-05)

Every shipped, user-facing capability → its **guide home** → its **README/highlights
hook** → its **index journey** (`docs/README.md`). The test: no orphan feature (a
capability no doc covers) and no orphan doc (a doc nothing links to).

| Capability (phase) | Guide home | README hook | Index journey |
|---|---|---|---|
| Voice typing — hold-to-talk, punctuation, `clipboard` | Getting Started; User Guide | hook line + "What it does at a glance" | Start here / Dictate |
| Intelligent dictation pipeline — intent routing, KB enrichment, rewriting, target profiles (DIR-01/39) | Intelligent Typing; Dictation Copilot | strip 🧠 + "See it learn" | Dictate |
| Dictation **journal + correct-in-the-moment + replay** (45) | Intelligent Typing §12 | strip 🧠 + journal screenshot | Dictate (own entry) |
| **Persistent correction memory + config cockpit** (40) | Intelligent Typing §10 (cockpit + Memory tab shots) | strip 🧠 ("it learns you") | Dictate (Intelligent Typing) |
| **Desktop presence** — native HUD / tray (41/43) | Intelligent Typing §11 | strip 🪟 | Dictate (own entry) |
| **First-run welcome wizard** (42/43) | Getting Started (welcome screenshot) | quickstart → Getting Started | Start here |
| Settings — sectioned/searchable (43) | Getting Started (routes table) | Configuration section | Start here |
| Meeting mode — dual-stream capture, transcript, speakers | Meeting Mode Guide | "What it does at a glance" | Meet |
| Meeting intelligence + **14 plugins** + MIR routing | Meeting Mode; Plugin Authoring | strip 🧩 + "Meeting intelligence" + `/history` screenshot | Meet / Extend |
| **Actuators I/II** — propose→approve→execute, write connectors (37/38) | Plugin Authoring §Actuators | "Meeting intelligence" paragraph | Extend (Plugin Authoring) |
| Models — bring your own (GGUF/MLX/OpenAI-compatible) | MODELS.md | strip 🔌 | Dictate |
| Agent hooks — Claude/Codex | Agent Hook Install | (ITG "see also" + index) | Extend |
| Activity connectors / Firefox extension | Connector Development; Firefox Extension | (Extend group) | Extend |
| AIPI-Lite companion + device protocol | AIPI-Lite Workflow; Device Protocol | strip 📟 + "AIPI-Lite companion" + art | Extend |
| Security & privacy posture | SECURITY.md | strip 🔒 | Operate & Trust |
| CLI — `doctor` / `meeting` / `history` / `actions` / `intel` / `dictation` / `agent-hook` / `device-psk` | User Guide; Getting Started; Meeting Mode | quickstart | Start here / Dictate / Meet |

**Result:** no orphan features (every capability has a guide home + an index link)
and no orphan docs (every `docs/*.md` is linked from the journey-map index;
verified by sweep). The README strip carries the seven top differentiators; depth
features (cockpit/memory, wizard, settings) are covered in their guide and reached
from the index rather than padded into the strip — discoverable without
overstating. Gap closed in this story: the index's Plugin Authoring entry now names
**actuators** (previously discoverable only by opening the guide). Every hook
cross-checked true against the canonical-facts table above.

**Clarity gap found (user-reported): the "project KB" is under-explained.** The
term + `kb-enricher` appeared in the Intelligent Typing guide ~150 lines before the
`.hs/` folder that *is* the KB was shown, and the README never grounds it. Fixed
here (docs side): a plain definition on first use in the guide, a gloss on
`kb-enricher`, and a glossary entry in `DOCS_STYLE.md`. The deeper **product/UX
legibility** (naming, the `/dictation → Project Context` surface, an in-app
explainer/empty-state, a guided "create your `.hs/`" flow, a discovery nudge) is
out of scope for a docs-only phase and is **teed up as a dedicated phase (47 —
"Project KB: legible & inviting")**.
