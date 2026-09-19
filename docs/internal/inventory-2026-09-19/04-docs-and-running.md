# HoldSpeak inventory — 04: docs and running it

Repo: `/Users/karol/dev/tools/HoldSpeak` · branch `main` · HEAD `16d78b0b` (2026-09-19)
Scope: can a person install it, run it, and understand it from the docs?
Method: read-only. Docs read directly; CLI probed with `--help` and live runs under an
isolated `$HOME`; one real hub booted in a throwaway `$HOME` on a pinned port and killed.
No pytest suite run, no write to the owner's `~/.holdspeak` / `~/.local/share/holdspeak`.

---

## 0. Headline

The documentation is *unusually good prose* sitting on top of an *unusually bad
first-run path*. The writing standard is real (ASD-STE100, a style doc, a terminology
register, a navigation linter, three drift guards, a claims-bound-to-predicates CI
fence). Generated references — `docs/API_SURFACE.md` (693 routes) and
`docs/MCP_SIDECAR.md` (225 tools) — are exact to the code.

What is not covered is everything between `git clone` and a working desk. The four
hardest facts a new operator needs (the port is random; `holdspeak doctor` is not the
doctor the docs mean; state lives in three separate home directories; the hub downloads
a Whisper model from HuggingFace before it finishes booting) appear in **no**
user-facing document.

---

## 1. Docs inventory

### 1a. Root + `docs/*.md` (user- and operator-facing)

`Updated` = `git log -1 --format=%cs <file>`.

| Path | Audience | Purpose | Updated | Freshness verdict |
|---|---|---|---|---|
| `README.md` | user | Product overview, install quickstart, capability table, platform matrix | 2026-09-06 | **STALE (1 measured defect)**. `README.md:106` says "222 tools across 40 families"; live registry is 225/41. No generator, no drift guard on this file. Everything else sampled held. |
| `CHANGELOG.md` | user | Release history | 2026-09-01 | Stale relative to HEAD: 18 days and ~12 merged phases behind; `pyproject.toml:3` still pins `version = "0.4.0"` |
| `CONTRIBUTING.md` | developer | Checkout, contracts table, doc checks, regeneration commands | 2026-09-05 | Accurate. The three named check commands and `docs/internal/architect-assistant/proof/run_tests.py` all exist |
| `docs/README.md` | user | Documentation index by task | 2026-09-18 | Accurate; 225/41 correct here (`docs/README.md:53`) |
| `docs/GETTING_STARTED.md` | user | Install → first sentence → models → Interview → hotkey → macOS permissions | 2026-09-07 | **PARTLY STALE**. `/studio` row is dead (§2); "Select **Dictate one sentence**" names a heading, not a control; extras table omits 3 user-facing extras; `holdspeak doctor` advice is wrong (§4) |
| `docs/USER_GUIDE.md` | user | 40-section daily-operation reference, 2 900 lines | 2026-09-18 | Fresh. Four labels sampled, 4/4 verified in `web/src`. Four of its sentences are under the HS-200-46 predicate fence |
| `docs/WEB_DESK.md` | user | Desk windows, objects, navigation | 2026-09-05 | Fresh; `WEB_DESK.md:13` words first capture more correctly than GETTING_STARTED does |
| `docs/GLOSSARY.md` | user | 60 product terms | 2026-09-06 | **One stale entry**: `sidecar` described as accessing services "without hosting the Web runtime", contradicting `docs/MCP_SIDECAR.md:9-18` where the sidecar is a pure hub client that refuses without a running hub |
| `docs/SECURITY.md` | operator | Data classes, at-rest posture, network boundaries, egress table | 2026-09-18 | Fresh and the best operator doc in the tree. One registered **known_false** claim at `docs/SECURITY.md:286` (tailnet-only bind is not enforced anywhere) |
| `docs/MODELS.md` | user | Concierge, engines, readiness states, assignment sets | 2026-09-06 | Accurate on states; **silent on where model files land on disk and how big they are** |
| `docs/AUTHORITY.md` | user | Secure / Normal / YOLO control modes | 2026-09-05 | Fresh; YOLO default verified at `holdspeak/config/core.py:288-289` |
| `docs/MEETING_MODE_GUIDE.md` | user | Record/import/review a meeting, system audio setup | 2026-09-05 | Fresh |
| `docs/DICTATION_PIPELINE_GUIDE.md` | user/dev | DIR-01 pipeline, blocks, project facts | 2026-09-06 | Fresh |
| `docs/DICTATION_COPILOT.md` | user | Coding-prompt dictation example | 2026-09-05 | Fresh |
| `docs/INTERVIEW.md` | user | Interview thread mode, saved context, limits | 2026-09-09 | Fresh; states its own limits honestly |
| `docs/PROJECT_ROOMS.md` | user | Project sources, Watches | 2026-09-05 | Fresh |
| `docs/CADENCE.md` | user | Open-loop review; off by default | 2026-09-05 | Fresh |
| `docs/AUTOMATION.md` | user | Triggers, execution paths, limits | 2026-09-05 | Fresh |
| `docs/ENVIRONMENTS.md` | user | Places / Settle in | 2026-09-05 | Fresh |
| `docs/DESK_MEMORY.md` | user | Attention items, Receipts | 2026-07-11 | **STALE** — 2+ months old, 41 lines, predates the Arrival rework |
| `docs/RELATIONSHIP_AWARE_MEMORY.md` | user | Cross-record memory search | 2026-09-18 | Fresh |
| `docs/ARCHITECTURE.md` | developer | Runtime + data flow | 2026-09-17 | Fresh |
| `docs/ARCHITECTURE_WORK.md` | user | Architecture-work recipes | 2026-09-05 | Fresh |
| `docs/API_SURFACE.md` + `docs/api-surface.json` | developer | Generated route reference | 2026-09-18 | **EXACT**: 693 routes, generator `scripts/gen_api_surface.py`, snapshot-tested by `tests/unit/test_api_surface.py` |
| `docs/MCP_SIDECAR.md` | developer/agent | Generated MCP tool contract | 2026-09-18 | **EXACT**: 225 tools / 41 families, roster diffed clean, guarded by `tests/unit/test_mcp_sidecar_doc_drift.py` |
| `docs/PLUGIN_AUTHORING.md` | developer | Meeting plugin authoring | 2026-08-29 | Aging but no measured defect |
| `docs/CONNECTOR_DEVELOPMENT.md` | developer | Activity connector authoring | 2026-09-02 | OK |
| `docs/AGENT_HOOK_INSTALL.md` | developer/agent | Claude/Codex hook install | 2026-07-04 | **Aging**; notable as the *only* user-visible doc that mentions `HOLDSPEAK_WEB_PORT` (`docs/AGENT_HOOK_INSTALL.md:179`) |
| `docs/PEOPLE_INTEGRATION.md`, `docs/PEOPLE_SECURITY.md` | user/operator | Confidential relationship records, keystore | 2026-08-29 | Aging |
| `docs/RELEASING.md` | operator | Backup, restore, packaging, release checks | 2026-09-17 | Fresh |
| `docs/REACH_RUNNER.md` | operator | Remote sweep runner | 2026-09-05 | Fresh |
| `docs/VOICE_COMMANDS.md` | user | Spoken keyword → action | 2026-06-08 | **STALE** — 3 months |
| `docs/ACTIVITY_PREBRIEFING.md` | user | Activity review before dictation | 2026-06-08 | **STALE** — 3 months |
| `docs/DEVICE_PROTOCOL.md`, `docs/AIPI_LITE_DEV_WORKFLOW.md` | developer | Companion device protocol | 2026-06-11 | **STALE**; companion track is dormant per project memory |
| `docs/FIREFOX_EXTENSION_GUIDE.md` | user | Browser activity connector | 2026-06-11 | **STALE** |
| `docs/INFERENCE_TARGETS.md` + `.json` | developer | Placement terminology | 2026-08-26 / 2026-07-11 | Thin (20 lines) |
| `docs/WEB_UI_UX_SYSTEM_AUDIT.md`, `docs/WEB_REACT_PARITY_LEDGER.json` | developer | Historical audit/ledger | 2026-07-10 | **STALE** — historical |
| `docs/product-language.json` | developer (runtime data) | Force-included into the wheel as `holdspeak/data/product-language.json` (`pyproject.toml`) | 2026-07-19 | **STALE — 2 months**, and it *ships in the package*. See §5 |
| `docs/trust-destinations.json` | developer (runtime data) | Also force-included into the wheel | 2026-07-11 | Stale-dated |
| `docs/workbenches.json`, `docs/inference-targets.json` | developer | Fixture/reference data | 2026-08-04 / 2026-07-11 | Aging |
| `docs/evidence/**` (~35 files) | PM | Frozen phase evidence snapshots | 2026-03 – 2026-04 | **Intentionally frozen.** `docs/README.md:88` says so explicitly; `tests/unit/test_doc_drift_guard.py:29` excludes them |

### 1b. `docs/internal/**` (agent / PM / architect)

| Path | Audience | Purpose | Updated | Verdict |
|---|---|---|---|---|
| `docs/internal/CONSTITUTION.md` | agent | Supreme canon: ratified articles | 2026-08-02 | Canon; stable by design |
| `docs/internal/UX-CANON.md` | agent | Face canon + review protocol | 2026-09-17 | Fresh; carries the A1 raw-`<button>` ratchet (175), predicate-fenced |
| `docs/internal/POSITIONING.md` | PM | Story, pillars, canonical feature names, voice rules | 2026-09-06 | Fresh |
| `docs/internal/DOCS_STYLE.md` | agent | ASD-STE100 reference, page structure | 2026-09-05 | Fresh |
| `docs/internal/DOCS_TERMINOLOGY.md` | agent | Terminology register (64 lines) | 2026-09-05 | Fresh — see §5 |
| `docs/internal/DOC_AUDIT_2026-09.md` | PM | Current doc-refresh scope + remaining language review | 2026-09-05 | Fresh; the honest record of what the refresh did *not* cover |
| `docs/internal/DOC_AUDIT_2026-06.md`, `…2026-08.md` | PM | Prior audits | 2026-08-29 | Historical |
| `docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md` | developer | Backend runtime contract | 2026-09-06 | Fresh |
| `docs/internal/ARCHITECTURE_WEB_FRONTEND.md` | developer | Frontend architecture | 2026-07-18 | **STALE — 2 months**, and it is the doc CONTRIBUTING sends web contributors to |
| `docs/internal/ARCHITECTURE_INTELLIGENCE_ROUTER.md` | developer | Router semantics + authority | 2026-08-30 | Aging |
| `docs/internal/DESK_GRAMMAR.md` | agent | Desk interaction grammar | 2026-09-17 | Fresh; one sentence predicate-fenced |
| `docs/internal/DESIGN_SYSTEM.md` | agent | Token/component system | 2026-09-04 | Fresh |
| `docs/internal/DESKOS_COMPONENT_PATTERN.md` | agent | Surface pattern canon | 2026-06-26 | **REGISTERED-FALSE.** Its own predicate says it documents the SwiftUI iPad desk while "DeskOS" now means the web desk |
| `docs/internal/OPERATIONAL-SURFACE-AUDIT.md` | PM | The two-missing-callers audit | 2026-09-14 | Fresh; partly superseded (the intel-queue caller was paid in HS-200-42) |
| `docs/internal/project-rooms/HANDOVER-MUADDIB.md` | agent | Orchestrator handover, 2 600+ lines | 2026-09 | Fresh. **Holds operational facts found nowhere in `docs/`** — e.g. `:1139` "The hub takes `HOLDSPEAK_WEB_PORT` — there is no `--port` flag" |
| `docs/internal/project-rooms/SRS_*.md` (5) | PM/dev | Project Rooms requirement specs | 2026-08/09 | Specs, not behaviour — `docs/README.md:83` warns of this |
| `docs/internal/architect-assistant/**` (12) | PM/dev | Interview spec package + proof drivers | 2026-06/07 | Spec package; includes the working `proof/run_tests.py` CONTRIBUTING cites |
| `docs/internal/CORE_MEMORY_*.md` (3) | dev | Core-memory design/council/SRS | 2026-09-01 | Aging |
| `docs/internal/PLAN_*.md` (13) | PM | Historical phase plans | 2026-06 – 2026-08 | **Historical.** Four are named in `CLAUDE.md` as source canon while dated 2026-06/07 — a live pointer at a frozen doc |
| `docs/internal/CROSS_PLATFORM_*.md`, `LINUX_PORT_*.md` | PM | Platform roadmaps/boards | 2026-06/07 | **STALE** — historical |
| `docs/internal/PRIVACY_APPROVAL_CONTROL_DESIGN_REVIEW.md` | PM | 1 291-line design review | 2026-08-17 | Historical |
| `docs/internal/SYSTEM_PRIMITIVE_COMPONENT_INVENTORY.md` | dev | 1 383-line component census | 2026-08-07 | **STALE** — a census 6 weeks old on a UI that moved every week since |
| `docs/internal/PROZILLAOS_STUDY.md`, `OPENWORKER_INTEGRATION_FEASIBILITY.md` | PM | Studies | 2026-07/08 | Historical |
| remaining ~15 internal `.md` | PM/agent | Assorted plans, briefs, checklists | 2026-06 – 2026-09 | Mixed; none load-bearing for install |

**Structural note.** `docs/README.md:83-86` states the rule that saves this tree from
being misleading: *"User guides describe implemented behavior. Internal specifications
can also describe planned behavior… Historical evidence does not establish the current
product state."* That rule is stated but not enforced — nothing marks an individual
internal doc as historical at the top of the file, so a reader arriving via grep gets no
warning.

---

## 1c. The HS-200-46 claims fence — what it covers and what it does not

Location:

| File | Role |
|---|---|
| `tests/unit/doc_claims/registry.py` (834 lines) | The registry: one row per load-bearing sentence, each with `doc`, `anchor`, `sentence`, `truth`, `state`, `story`, and an **executable `predicate()` over the real module** |
| `tests/unit/test_phase200_doc_claims.py` (119 lines) | Five fences over that registry |
| `scripts/doc_claims.py` | Renders the registry as one markdown table; `--measure` re-runs every predicate |

I ran it: `HOME=$(mktemp -d) uv run python scripts/doc_claims.py --measure` →
**16 claims, 4 known_false, 0 drifted.**

What it actually enforces (`tests/unit/test_phase200_doc_claims.py:44-119`):

| Fence | Effect |
|---|---|
| `test_registered_claim_anchor_is_still_in_its_document` | A sentence that MOVES or is DELETED fails — you cannot quietly stop being checked |
| `test_registered_claim_matches_its_state` | A `holds` claim that goes false fails **and** a `known_false` claim that becomes true fails, so a fix cannot land without correcting the prose in the same commit |
| `test_known_false_count_is_a_down_only_ratchet` | Admitted debt may shrink, never grow, without editing `KNOWN_FALSE_RATCHET_REASON` in the same commit |
| `test_ratchet_ceiling_is_not_left_slack` | A repaired claim MUST lower the ceiling, so the slack cannot absorb a new lie |
| `test_registry_rows_are_distinct_and_named` | No duplicate `(doc, anchor)` rows |

The 16 registered rows, by document:

| Document | Rows | State |
|---|---|---|
| `docs/USER_GUIDE.md` (`:983`, `:997`, `:1018`, `:1085`) | 4 | all holds |
| `holdspeak/mcp/resources.py` (`:63`, `:162`) | 2 | **both known_false** |
| `docs/SECURITY.md:286` | 1 | **known_false** (tailnet bind not enforced) |
| `docs/internal/DESKOS_COMPONENT_PATTERN.md:3` | 1 | **known_false** |
| `docs/internal/UX-CANON.md:132`, `docs/internal/DESK_GRAMMAR.md:52`, `docs/MCP_SIDECAR.md:927` | 3 | holds |
| `holdspeak/web/routes/mcp_http.py:13`, `holdspeak/db/connection.py:3`, `holdspeak/db/schema.py:1346` | 3 | holds |
| `CLAUDE.md:153`, one `pm/roadmap/…` settled-design file | 2 | holds |

**What it does NOT cover — the gap that matters here.** The fence is a *hand-curated
16-row* registry aimed at architectural and canon sentences that had previously misled
an agent. It contains **zero rows covering the install path, the run-it path, the CLI,
ports, state layout, or any prose in `README.md` or `docs/GETTING_STARTED.md`.**

Concretely, every defect in §2 and §4 of this report would pass CI today:

| Real defect | Caught by HS-200-46? |
|---|---|
| `README.md:106` says 222 tools / 40 families; live is 225/41 | No — README is not in the registry |
| `docs/GETTING_STARTED.md:126` documents `/studio` as "Studio"; the route was deleted and lands on Settings | No |
| `holdspeak doctor --help` says "Run environment checks"; it runs the hub doctor instead | No |
| `holdspeak doctor --strict` / `--connectors` are parsed and discarded | No |
| `docs/GLOSSARY.md` "sidecar" contradicts `docs/MCP_SIDECAR.md` | No |
| The hub port is random and no user doc says so | No |

The claim in `pm/roadmap/…/story-46-a-stale-doc-fails-ci.md` that "a stale doc fails CI"
is true only for the 16 sentences somebody thought to register. It is a **manual
allowlist with an excellent enforcement mechanism attached**, not coverage.

The genuinely *generated* surfaces are the ones that never rot:
`docs/API_SURFACE.md` (`scripts/gen_api_surface.py` + `tests/unit/test_api_surface.py`)
and `docs/MCP_SIDECAR.md` (`scripts/gen_mcp_sidecar_doc.py` +
`tests/unit/test_mcp_sidecar_doc_drift.py`). Both measured exact. `README.md:106`
repeats the same two numbers by hand, under no generator and no guard — which is exactly
why it is the one that rotted.

### Other doc checks in CI (`.github/workflows/test.yml:13-26`)

| Check | Covers | Does not cover |
|---|---|---|
| `scripts/check_docs.py` | Local links + GitHub heading anchors in public Markdown | External URLs, code examples, meaning, terminology |
| `tests/unit/test_docs_navigation.py` | Same, as a test | — |
| `tests/unit/test_doc_drift_guard.py` (26 tests) | Counts, product terms, generated-contract agreement over maintained docs | The install path |
| `tests/unit/test_api_surface.py` | 693-route snapshot | — |
| `tests/unit/test_mcp_sidecar_doc_drift.py` | 225-tool roster | `README.md`'s copy of the number |

---

## 2. The run-it path, from a fresh clone

### 2a. What the docs tell you to do

Reconstructed from `README.md:17-38`, `docs/GETTING_STARTED.md:8-100`,
`CONTRIBUTING.md:6-23`, `pyproject.toml:236-238` (`[project.scripts]`). **There is no
Makefile and no justfile in this repo** — `pyproject.toml` + the CLI `--help` are the
only machine-readable entry points.

```sh
# prerequisites the docs name: Python >=3.10, uv, Node.js >=22.12, npm, git,
# a microphone, portaudio, and on Debian/Ubuntu:
#   sudo apt-get install portaudio19-dev ffmpeg xclip pulseaudio-utils
git clone https://github.com/karolswdev/HoldSpeak.git
cd HoldSpeak
uv venv
source .venv/bin/activate
uv pip install -e .            # Linux: uv pip install -e '.[linux]'
holdspeak                      # -> prints a URL; opens a browser
# then, on the Desk: "Dictate one sentence" -> speak -> Copy / Keep as Note
```

`uv pip install -e .` is not a Python-only install: `hatch_build.py:20-50` runs
`npm ci && npm run build` inside `web/` and **hard-fails** if `npm` is missing and
`holdspeak/static/_built/index.html` is absent. `HOLDSPEAK_SKIP_WEB_BUILD=1` exists as
the escape hatch — documented in **no** user-facing doc.

### 2b. Where docs and code disagree

| # | Doc says | Code does | Evidence |
|---|---|---|---|
| D1 | "Open the URL printed in the terminal. The default listener uses loopback (`127.0.0.1`). Use the printed URL because the port and access parameters can differ." (`docs/GETTING_STARTED.md:81-85`) | The port is **randomly allocated on every boot** by `_find_free_port`. There is no `--port` flag (`holdspeak web --help` shows only `--no-open`, `-v`). The only pin is the env var `HOLDSPEAK_WEB_PORT`. | `holdspeak/web_server.py:48,398`; `holdspeak/web_runtime.py:67-76`; `holdspeak/main.py:84-99` |
| D2 | `holdspeak doctor` help text: "Run environment checks and show setup fixes" (`holdspeak/main.py:349-352`); GETTING_STARTED troubleshooting sends you to it for "Capture cannot start" (`docs/GETTING_STARTED.md:243`) | `holdspeak doctor` runs the **hub** doctor (`holdspeak/doctor.py`): 10 HTTP/WS probes against a *running* hub. It never checks the microphone, the hotkey, permissions, or ffmpeg. The 31-check environment doctor in `holdspeak/commands/doctor.py` is unreachable from the CLI — its only caller is `holdspeak/setup_status.py:239`, i.e. the web `/setup` surface. | `holdspeak/main.py:28,39-40,537-538`; live run below |
| D3 | `holdspeak doctor --strict` and `--connectors` are declared (`holdspeak/main.py:353-365`) | Both flags are **parsed and discarded**: `run_doctor_command(_args)` ignores its argument and calls `run_doctor()` with no parameters. Verified live: `holdspeak doctor --connectors` printed the identical 10-line hub report. | `holdspeak/main.py:39-40` |
| D4 | Nothing | The hub doctor defaults to `http://127.0.0.1:8765` unless `HOLDSPEAK_URL` is set — a port the hub **never binds by default** (D1). So on a normal install `holdspeak doctor` reports 4 FAIL on a perfectly healthy hub. `HOLDSPEAK_URL` and `HOLDSPEAK_TOKEN` are documented nowhere. | `holdspeak/doctor.py:21,301,308` |
| D5 | `/studio` → "Studio" (`docs/GETTING_STARTED.md` route table) | Studio was deleted (HS-100-10). The address resolves to surface `configure-settings` — identical to `/settings`. A user following the table lands on the row above it and cannot tell. | `web/src/routes.tsx:70-72` |
| D6 | "Select **Dictate one sentence** on the Desk" (`docs/GETTING_STARTED.md:96`) | The string is an `<h1>`/`<h2>` heading, not a control. The panel is already on screen; you press the talk button. `docs/WEB_DESK.md:13` gets this right. | `web/src/desk/components/FirstWords.tsx:355,357-360` |
| D7 | "The MCP sidecar exposes 222 tools across 40 families" (`README.md:106`) | 225 tools, 41 families. Confirmed directly: `len(TOOLS) == 225`. `docs/README.md:53` and `docs/MCP_SIDECAR.md:4` both say 225/41. | `holdspeak/mcp/tools.py`; `docs/MCP_SIDECAR.md:4` |
| D8 | Extras table lists 4 optional capabilities (`docs/GETTING_STARTED.md:225-230`) | `pyproject.toml` declares 3 more user-facing extras the table omits: `wakeword` (`:97`), `tts` (`:101`), `presence` (`:122`). | `pyproject.toml:97,101,122` |
| D9 | "Whisper transcription \| macOS on Apple Silicon: MLX Whisper" (`README.md` platform table) | Selection is `darwin` **and** `arm64` **and** mlx importable; Intel Macs silently fall through to faster-whisper, which the table does not say. | `holdspeak/transcribe.py:139-141` |
| D10 | `README.md:122` "The main configuration file is `~/.config/holdspeak/config.json`" | True, but it is one of **three** home directories the product writes (§4). Only `docs/SECURITY.md:174-196` comes close to the full picture, and it too omits `~/.local/share/holdspeak/holdspeak.log`. | `holdspeak/config/core.py:35-36`; `holdspeak/db/core.py:47`; `holdspeak/logging_config.py` |
| D11 | `docs/GLOSSARY.md` "sidecar": accesses HoldSpeak services "without hosting the Web runtime" | The sidecar opens **no** database and **requires** a running hub; with no hub, every call but `initialize`/`ping` returns an error. | `docs/MCP_SIDECAR.md:9-31` vs `docs/GLOSSARY.md` |
| D12 | `pyproject.toml:3` `version = "0.4.0"`; `CHANGELOG.md` last touched 2026-09-01 | HEAD is 18 days and ~12 merged phases past that. A user cannot tell which release contains what. `README.md:10` handles this honestly ("These documents describe the code on `main`. A published release can have fewer features.") but the changelog itself is the artefact that would answer the question. | `pyproject.toml:3`; `CHANGELOG.md` |

### 2c. Prerequisites the docs never name

| Missing prerequisite | Evidence | Why it bites |
|---|---|---|
| **The port is random.** No user doc states it; the only statements live in `docs/AGENT_HOOK_INSTALL.md:179` and `docs/internal/project-rooms/HANDOVER-MUADDIB.md:1139` ("there is no `--port` flag") | `holdspeak/web_server.py:398` | You cannot bookmark the desk, script against it, put it behind a reverse proxy, or write a systemd unit |
| **`HOLDSPEAK_WEB_PORT` / `HOLDSPEAK_WEB_HOST` / `HOLDSPEAK_URL` / `HOLDSPEAK_TOKEN`** — the four env vars that make the product operable — are absent from README, GETTING_STARTED, SECURITY and USER_GUIDE | `holdspeak/web_runtime.py:67`; `holdspeak/doctor.py:301,308` | The hub is unaddressable and the doctor unusable without them |
| **First boot downloads a Whisper model from HuggingFace, unprompted.** Live-observed: a fresh `$HOME` gained `~/.cache/huggingface/hub/models--mlx-community--whisper-base-mlx` within seconds of `holdspeak web`, before any user action | hub log: `Initializing Transcriber with model_name='base'` … `MLX model loaded from mlx-community/whisper-base-mlx` | Network egress on first launch; the model cache is a **fourth** on-disk location, named in no doc; `docs/MODELS.md` never says where models live or how large they are |
| **Node/npm is a hard install-time dependency for source installs**, not merely "recommended" — `uv pip install -e .` fails without it | `hatch_build.py:38-44` | README lists Node under prerequisites but does not say the Python install *invokes* it |
| **`HOLDSPEAK_SKIP_WEB_BUILD=1`** — the only way to install without Node | `hatch_build.py:26-35` | Undocumented outside the source file |
| **Where the log is**: `~/.local/share/holdspeak/holdspeak.log`. The CLI prints it in `--help` output; no `.md` under `docs/` names it except `docs/internal/PLAN_MEETING_MODE.md:179` | `holdspeak/logging_config.py` | The only real debugging surface is undiscoverable |
| **BlackHole** (macOS system-audio loopback) for meeting capture | `README.md` platform table mentions it in passing; `docs/MEETING_MODE_GUIDE.md` covers setup | Named, but only in the meeting guide |
| **Keychain / Secret Service** is a hard runtime dependency for People (`keyring>=25.0` is a core dep) | `pyproject.toml:52-55` | Not named in GETTING_STARTED requirements |
| **Playwright + Chromium** for the e2e suite, and `PLAYWRIGHT_BROWSERS_PATH` for isolated-HOME runs | `CLAUDE.md` test commands | Named in CLAUDE.md, absent from CONTRIBUTING |
| **The DB is 3.2 MB with ~240 tables on first boot**, reconciled to schema v79 at startup | live hub log | No doc sets the expectation |

### 2d. Steps requiring knowledge no doc gives

1. **"Open the URL printed in the terminal"** — if you piped stdout to a file (a
   systemd unit, `nohup`, a container), Python block-buffers and the URL does not
   appear until flush. There is no other way to learn the port short of reading
   `~/.local/share/holdspeak/holdspeak.db.owner.lock`, whose JSON body carries
   `{pid, process_start, port, host, label}`. **No doc mentions the owner lock as an
   operator surface** — `docs/MCP_SIDECAR.md:10-14` describes it only as the sidecar's
   discovery mechanism.
2. **Restarting the hub changes the port.** Nothing says so.
3. **`holdspeak doctor` failing is normal.** On a healthy default install it reports
   `4 FAIL` because it probes `:8765`. Nothing tells a user this is a false alarm or
   that `HOLDSPEAK_URL` is the fix.
4. **Getting the auth token.** `_check_websocket`, `_check_auth` and `_check_inference`
   all SKIP with "no token configured". The token is minted into
   `~/.config/holdspeak/config.json` under `meeting.web_auth_token`
   (`holdspeak/web_auth.py:58-70`). No doc says to read it out of there.
5. **Which of three home directories to back up.** `holdspeak backup` snapshots the
   database. Whether `~/.holdspeak/` (gate state, packs, delivery config, pricing,
   node ledger, profile custody keys) is covered is stated nowhere.

### 2e. Live verification

```
$ HOME=<tmp> HOLDSPEAK_WEB_PORT=39412 holdspeak web --no-open
# hub log, ~2s to serving:
  Schema reconciled to version 79 (changed=True)      # ~240 tables created
  Seeded 10 built-in skills
  Workbench conductor started
  Scheduled recording conductor started
  Intel queue drainer started (poll 15s)
  Meeting web server started: http://127.0.0.1:39412
  Initializing Transcriber with model_name='base'
  Found BlackHole device: BlackHole 2ch (idx=1, in=2, out=2)
  MLX model loaded from mlx-community/whisper-base-mlx   # +17s, downloaded from HF
  heartbeat sweep: watches=0 rooms=0 held=False duration=4ms

$ curl -s http://127.0.0.1:39412/health
{"status":"ok"}
```

Boot works and is fast. Everything else in this section is about *finding out that it
worked*.

---

## 3. CLI inventory

Two console entry points (`pyproject.toml:236-238`):

| Entry point | Target | Audience |
|---|---|---|
| `holdspeak` | `holdspeak.main:main` | user |
| `holdspeak-mcp` | `holdspeak.mcp.server:main` | agent / MCP client (this is what `.mcp.json` runs) |

`holdspeak` subcommands, with doc coverage measured by grepping `docs/*.md` + `README.md`
for the literal invocation:

| Subcommand | Purpose (from `--help`) | Audience | Documented in |
|---|---|---|---|
| *(none)* | Defaults to `web` | user | README, GETTING_STARTED |
| `web` | Start the web flagship runtime (`--no-open` for headless) | **user** | 7 docs |
| `meeting` | Capture mic + system audio directly (`--setup`, `--list-devices`) | **user** | MEETING_MODE_GUIDE, USER_GUIDE |
| `import` | Import an existing audio recording as a meeting | **user** | MEETING_MODE_GUIDE |
| `doctor` | *Declared* "environment checks and setup fixes"; *actually* the hub health probe | **user** | 6 docs — **and all 6 describe the wrong doctor** |
| `backup` | Back up the database to a timestamped file | **user** | README, RELEASING, SECURITY, ARCHITECTURE |
| `restore` | List backups, or restore one | **user** | README, GETTING_STARTED, RELEASING, ARCHITECTURE |
| `control-mode` | Show or set the authority policy for future operations | user/operator | AUTHORITY |
| `cadence` | Cadence Engine: `status`, `loops`, `run`, `brief`, `closeout`, `audit` | user/operator | CADENCE |
| `dictation` | Inspect / dry-run the DIR-01 dictation pipeline | developer | DICTATION_PIPELINE_GUIDE, USER_GUIDE |
| `agent-hook` | Ingest Claude/Codex hook events for project-aware dictation | developer | AGENT_HOOK_INSTALL |
| `gate` | Tool-call gate: hold a steered agent's risky calls for the desk | developer/operator | USER_GUIDE, SECURITY |
| `memory` | Long-horizon memory index maintenance (`rebuild-index` only) | operator | ARCHITECTURE, USER_GUIDE |
| `device-psk` | Show or rotate the AIPI-Lite shared PSK | operator | DEVICE_PROTOCOL, AIPI_LITE |
| `intel` | Deferred intel queue + MIR route simulation/reroute | developer/rig | MEETING_MODE_GUIDE (partial) |
| `mesh` | Mesh-edge commands (`serve`) | developer/rig | SECURITY (passing mention) |
| `history` | Browse meeting history in the terminal | user | **NOT DOCUMENTED** |
| `actions` | Manage action items across meetings | user | **NOT DOCUMENTED** |
| `node` | Delivery-node commands (`serve`, `token`) | developer/rig | **NOT DOCUMENTED** |
| `seed` | Apply the packaged architect's-desk seed (idempotent; never deletes) | user/operator | **NOT DOCUMENTED** |

`seed` is the notable omission: it is the *only* CLI path to populate a desk, it is
advertised in `holdspeak --help`, and it appears in no `.md` under `docs/` or in
`README.md`.

Developer/rig tooling outside the CLI: **~130 scripts** under `scripts/` (walks,
screenshot rigs, dogfood drivers, closeout beats, generators). Only four are referenced
from `CONTRIBUTING.md`: `check_docs.py`, `gen_api_surface.py`, `gen_mcp_sidecar_doc.py`,
`check_web_baseline.py`. The other ~126 are undocumented and mostly historical
phase-evidence rigs.

---

## 4. Ports, processes, files

### Processes

| Process | Started by | Kind | Notes |
|---|---|---|---|
| `holdspeak` (uvicorn hub) | `holdspeak` / `holdspeak web` | Main process; uvicorn runs in a daemon **thread**, not a child process | `holdspeak/web_server.py:405-418` |
| Workbench conductor | Hub startup | In-process thread | `holdspeak/web_server.py:1265-1274` |
| Scheduled-recording conductor | Hub startup | In-process thread | `holdspeak/web_server.py:1279-1301` |
| Calendar-ingest conductor | Hub startup | In-process thread; refreshes ICS sources at boot and every 15 min | `holdspeak/web_server.py:1307-1309` |
| Intel-queue drainer | Hub startup | In-process thread, 15 s poll | `holdspeak/web_server.py:1319-1321` |
| Heartbeat sweep | Hub startup | In-process; observed every ~10 s in the log | `holdspeak/runtime/heartbeat` |
| `holdspeak-mcp` sidecar | The MCP **client** (Claude Code etc.) spawns it per `.mcp.json` | Separate child process | Stateless relay: finds the hub via the owner lock, forwards to `POST /api/mcp`, opens no DB |
| Browser | `webbrowser.open(owner_url)` unless `--no-open` | External | `holdspeak/web_runtime.py:585-589` |
| Desktop presence panel | Only when `HOLDSPEAK_DESKTOP_PRESENCE=1` and the `presence` extra is installed | Optional native renderer | `pyproject.toml:120-129` |

### Ports

| Port | Who | Default |
|---|---|---|
| Hub HTTP + WS | `holdspeak web` | **Random free port on 127.0.0.1**, per boot (`holdspeak/web_server.py:48,398`) |
| Hub, pinned | `HOLDSPEAK_WEB_PORT=<n>` | The only pin. No CLI flag |
| Hub bind host | `HOLDSPEAK_WEB_HOST` | `127.0.0.1`. A non-loopback bind **without** a configured auth token is refused (`holdspeak/web_auth.py:73-89`) |
| `127.0.0.1:8765` | `holdspeak doctor`'s hardcoded `DEFAULT_URL` | **Not a port the product binds.** Override with `HOLDSPEAK_URL` |
| MCP sidecar | none — stdio only | — |

### State on disk — three home directories, not one

| Path | Contents | Named by |
|---|---|---|
| `~/.config/holdspeak/config.json` | The config, including `meeting.web_auth_token` and `device.psk` | `README.md:122`, `SECURITY.md:179` |
| `~/.config/holdspeak/blocks.yaml` | Dictation block config | `holdspeak/plugins/dictation/assembly.py` |
| `~/.config/holdspeak/agent_sessions.json` | Agent hook sessions | `docs/AGENT_HOOK_INSTALL.md:95` |
| `~/.local/share/holdspeak/holdspeak.db` (+ `-wal`, `-shm`) | The main SQLite database, ~240 tables, schema v79, WAL | `SECURITY.md:174,195` |
| `~/.local/share/holdspeak/holdspeak.db.owner.lock` | `{pid, process_start, port, host, label}` — **the only reliable way to discover the hub's port** | `MCP_SIDECAR.md:10-14` (as a sidecar mechanism, not an operator surface) |
| `~/.local/share/holdspeak/holdspeak.log` | The log | **Only `docs/internal/PLAN_MEETING_MODE.md:179`** |
| `~/.local/share/holdspeak/people.v1.sqlite3` | Encrypted People store | — |
| `~/.local/share/holdspeak/meetings/`, `meeting-captures/`, `calendar-snapshots/` | Meeting JSON, capture journal, ICS snapshots | `ARCHITECTURE.md:744`, `USER_GUIDE.md:1321` |
| `~/.holdspeak/` | `gate.json`, `pricing.json`, `delivery_workbench.json`, `delivery_sources.json`, `agent_profiles.json`, `agent_launches.json`, `node_auth_tokens.json`, `mesh_hub_pin.json`, `node_command_ledger.db`, `profile-custody/profile-keys.json`, `connector_packs/`, `plugin_packs/`, `workbenches/`, `agent_credentials/`, `gate-spawn-settings/` | Scattered across 6 docs; **no single doc lists the tree** |
| `~/.cache/huggingface/hub/` | Whisper + other downloaded model weights | **No doc at all** |
| macOS Keychain / Linux Secret Service | People encryption keys | `PEOPLE_SECURITY.md` |
| Browser `localStorage`, `hs.draft.v1.*` | Recovery drafts | `SECURITY.md:180` |

### Health and logs

| Question | Answer |
|---|---|
| Is there a doctor? | Two, and the wrong one is wired to the CLI |
| `holdspeak doctor` (what you get) | 10 checks against a running hub: `hub-health` (`GET /health`), `runtime-status`, `runtime-preflight`, `websocket`, `desk-bootstrap`, `auth`, `mcp-server`, `inference`, `database`, `observer`. Three SKIP without a token; four FAIL without `HOLDSPEAK_URL` pointing at the real port. `holdspeak/doctor.py:299-321` |
| The environment doctor (what the docs mean) | 31 checks in `holdspeak/commands/doctor.py:1276-1310`: Config, Runtime, Database, Microphone, Transcription backend, Web runtime, Web auth, Meeting intel runtime/egress, Endpoint health, Trust destinations, Runtime profiles, Inference targets, Mesh edges, Cloud preflight, Dictation project context/runtime/constraint compile/runtime counters, MIR routing, MIR telemetry, **Global hotkey, Text injection, Clipboard backend, ffmpeg, pactl, System audio capture**, Connector packs, People keystore, Agent capabilities, Tool call gate. **Reachable only through the web `/setup` surface** (`holdspeak/setup_status.py:239`) |
| Simplest liveness check | `curl http://127.0.0.1:<port>/health` → `{"status":"ok"}` |
| Logs | `tail -f ~/.local/share/holdspeak/holdspeak.log`; `holdspeak -v` also mirrors to stderr |
| In-product | `/setup` renders the 31-check environment doctor with remediation |

---

## 5. Terminology consistency

Four sources claim authority over product nouns. They do not agree with each other, and
none of them fully agrees with the UI.

| Source | Updated | Terms | Enforced by |
|---|---|---|---|
| `docs/product-language.json` | 2026-07-19 | 21 registry terms + legacy aliases + guarded terms + prohibited copy patterns | `tests/unit/test_product_language.py`, `web/src/lib/productLanguage.test.ts`, `apple/Tests/ContractsTests/ProductLanguageTests.swift`, `holdspeak/product_copy.py` |
| `docs/GLOSSARY.md` | 2026-09-06 | ~60 user-facing terms | **Nothing.** `grep -rln GLOSSARY tests/ scripts/` returns nothing |
| `docs/internal/DOCS_TERMINOLOGY.md` | 2026-09-05 | ~30 register entries | **Nothing** — referenced only from prose (`CONTRIBUTING.md:32`, `docs/internal/DOCS_STYLE.md:34`) |
| `docs/internal/POSITIONING.md` | 2026-09-06 | ~73-row canonical-name table | 4 banned strings in `tests/unit/test_doc_drift_guard.py:545-553` |

**`product-language.json` is load-bearing at runtime**, not a doc: `pyproject.toml:183`
force-includes it into the wheel as `holdspeak/data/product-language.json`, and
`holdspeak/product_language.py:279-297` loads it (source tree first, wheel copy as
fallback, raise if neither). `web/src/lib/productLanguage.ts` and
`apple/.../ProductLanguage.swift` are hand-maintained **mirrors** that never read the
JSON; equality is only asserted at test time.

### Conflicts

| # | Conflict | Side A | Side B |
|---|---|---|---|
| C1 | **POSITIONING contradicts itself about Studio in one file** | `docs/internal/POSITIONING.md:106` "there is no Studio" | `docs/internal/POSITIONING.md:152` still lists Studio as a canonical name; `web/src/routes.tsx:70-72` redirects `/studio` to Settings |
| C2 | **"the Concierge" is a doc-only word — the product says "Models."** Five user guides send the reader looking for a label that is not on screen | `docs/GLOSSARY.md:19`, `docs/internal/POSITIONING.md:187`, `docs/GETTING_STARTED.md:139`, `docs/MODELS.md`, `docs/DICTATION_COPILOT.md:187` | `web/src/desk/applications.ts:304,317` label and eyebrow are both `"Models"`; "Concierge" survives only as a code identifier |
| C3 | **`chain` carries two different labels inside `web/src`** | `web/src/desk/pullouts/editors/registry.ts:19` → `"Sequence"` (correct per `docs/product-language.json:83-88`) | `web/src/desk/tools.ts:40` → `"Workflow"`, collapsing it onto `workflow` at `tools.ts:48`. No test catches it |
| C4 | `coder_session` truncated | `docs/product-language.json:71-76`, `docs/GLOSSARY.md:18` "Coder session"; `web/src/desk/tools.ts:41` correct | `web/src/desk/pullouts/editors/registry.ts:20` → `"Coder"` |
| C5 | **"connector": canonical in one source, retired in another** | `docs/GLOSSARY.md:20` canonical noun; `docs/internal/POSITIONING.md:211` uses it | `docs/product-language.json:140-141` files it under `legacy_aliases` → `integration`; UI ships "Integration" (`web/src/desk/components/DeliveryBoard.tsx:329`) |
| C6 | "target profiles" vs "Runs on" | `docs/internal/POSITIONING.md:156` declares **target profiles** canonical | `docs/product-language.json:95-100,143` → "Runs on"; UI ships "Runs on" (`web/src/pages/cores/SettingsCore.tsx:197`) |
| C7 | "the Companion" retired and rendered | `docs/internal/POSITIONING.md:178-179` retires it | `web/src/desk/applications.ts:138` sets the Agents eyebrow to `"Companion"` |
| C8 | Thought Workbench vs Thought workspace | `docs/GLOSSARY.md:36,58`, `docs/internal/DOCS_TERMINOLOGY.md:14`, `POSITIONING.md:180` | `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:404` "Thought workspace", `:470` bare "Thought". "Workbench" is separately a *different* noun (`applications.ts:234` "Workbenches") |
| C9 | **Ten doc-canonical names with zero UI presence**: Heartbeat, Resourceful, Automations, Project Room, Everyday context, Home, arrival, Grant, "Knowledge collections", Watches | `docs/GLOSSARY.md:10,13,29,31,33,46,50,61`; `POSITIONING.md:150,184,185,186,188,192-193,202`; `docs/product-language.json:56,119-124` | Nothing rendered. Heartbeat ships only as "Rhythm"; Project Room ships as "Room"; Watches renders only from `web/src/features/project-room/_parked/` (a dead directory) |
| C10 | **Thirteen UI names no doc declares**: "Ask AI", "Intelligence", "Live meeting", "Context", "Workbenches", "Components", "Activity", "Desk memory", "Processes", "Commands", "Calendar snapshot", "Connections", "Meeting memory" | `web/src/desk/applications.ts:68,94,122,177,217,234,251,267,285,344,361,395,421` | None of the four sources. `docs/internal/POSITIONING.md:256-258` requires "one row per new user-facing surface, in the phase that ships it" — unhonoured for at least 13 surfaces |
| C11 | **Guarded terms ship through a hole in the guard** | `docs/product-language.json:275-282` guards `Profile, Action, Context, Target, Pending, Local` | `tests/unit/test_product_language.py:126-137` scans only `*.tsx` under `web/src/desk` + `web/src/pages`. So `applications.ts:217` ships `"Context"`, `web/src/lib/spriteStates.ts:31` ships `"Pending"`, `web/src/lib/primitives.ts:701` ships `"Local"`. `web/src/features/**` and `web/src/components/**` are unscanned entirely |
| C12 | "persona" banned as copy, used as canon | `tests/unit/test_web_vocabulary_guard.py:36` bans `personas?` in web copy | `docs/internal/POSITIONING.md:88,177` uses it; the registry key is still `persona` (`docs/product-language.json:65`) |
| C13 | APPLIED chip documented in the wrong place | `docs/internal/POSITIONING.md:221` defines it for the Speak/dictation loop | Rendered only in `web/src/desk/pullouts/editors/NoteEditor.tsx:101` and `KbEditor.tsx:96`, for a lens. `web/src/desk/components/MicButton.test.tsx:249` asserts outright that the Speak face has no APPLIED chip |

### Is `product-language.json` stale?

Last commit 2026-07-19; `web/src` last moved 2026-09-18. Verdict: **not rotten, thin.**
All 21 terms still resolve and all 14 paths in its `copy_contract` sections still exist.
Of 17 sampled entries: 12 still describe the product; 2 describe labels nobody renders
(`Knowledge collections` at `:56`, `Grant` at `:119-124`); 1 is contradicted by the UI
(`Sequence`, C3); 1 is defeated by its own enforcement gap (`guarded_terms`, C11); and 1
is an open-ended exception with no expiry (`apple-agent-rename-pending-v1` at `:391-399`,
parked in July "until the HSM follow-up phase", never re-checked).

The staleness is by omission: ~13 surfaces shipped since July and none were added, and
the registry has no entry for Thought, Thread, Watch, Steward, Heartbeat, Rhythm,
Concierge, People or Decision — all rendered nouns today.

### Summary of enforcement

`product-language.json`'s 21 terms are structurally enforced and mirrored into two
clients by test. `GLOSSARY.md` has **zero** automated enforcement. `DOCS_TERMINOLOGY.md`
has **zero**. `POSITIONING.md`'s 73-row table is enforced to the extent of four banned
strings. That asymmetry is exactly why C1–C10 are all live.

---

## 6. Blunt verdict — the top 10 reasons a competent engineer cannot reach daily use in one sitting

| # | Blocker | The gap behind it |
|---|---|---|
| 1 | **The hub's port is random and nothing user-facing says so.** Restart it and the address changes. No `--port` flag exists. | Code: `holdspeak/web_server.py:398`. Docs: `docs/GETTING_STARTED.md:81-85` says "the port… can differ" and leaves it there. The two places that state the truth plainly are `docs/AGENT_HOOK_INSTALL.md:179` and an internal handover. `HOLDSPEAK_WEB_PORT` appears in zero user guides. |
| 2 | **`holdspeak doctor` is the wrong doctor, and it lies twice.** Its own `--help` says "environment checks"; it runs a hub probe. Its `--strict` and `--connectors` flags are parsed and thrown away. On a healthy install it reports `4 FAIL` because it probes `:8765`, which the hub never binds. | `holdspeak/main.py:39-40` discards `args` and calls `holdspeak/doctor.py`'s `run_doctor()`. The 31-check environment doctor at `holdspeak/commands/doctor.py:1276-1310` has exactly one caller, `holdspeak/setup_status.py:239`. Six docs send users to the CLI doctor for microphone and permission problems it cannot see. |
| 3 | **The four environment variables that make the product operable are undocumented.** `HOLDSPEAK_WEB_PORT`, `HOLDSPEAK_WEB_HOST`, `HOLDSPEAK_URL`, `HOLDSPEAK_TOKEN`. | No env-var reference page exists anywhere in `docs/`. |
| 4 | **State is scattered across three home trees plus a HuggingFace cache, and no document draws the map.** Backup/restore covers the database only; whether `~/.holdspeak/` (custody keys, gate state, packs, node ledger) is included is stated nowhere. | `~/.config/holdspeak/`, `~/.local/share/holdspeak/`, `~/.holdspeak/`, `~/.cache/huggingface/`. `docs/SECURITY.md:174-196` is the closest, and it omits the log file and the model cache. |
| 5 | **The log file is effectively undiscoverable.** The only debugging surface is named in `holdspeak --help` output and one internal plan doc from 2026-07. | `holdspeak/logging_config.py`; grep of `docs/*.md` finds only `docs/internal/PLAN_MEETING_MODE.md:179`. |
| 6 | **First boot silently downloads a model over the network before you have done anything.** Observed live: whisper-base-mlx pulled into `~/.cache/huggingface` within seconds. Behind a proxy or offline, this is where you stop. | `docs/GETTING_STARTED.md:16` says only "The transcription backend can download model files on first use." No size, no destination, no offline path, no proxy note. `docs/MODELS.md` never says where model files land. |
| 7 | **The very first instruction is wrong.** "Select **Dictate one sentence** on the Desk" names an `<h1>`, not a control. | `docs/GETTING_STARTED.md:96` vs `web/src/desk/components/FirstWords.tsx:355`. `docs/WEB_DESK.md:13` words it correctly, so the repo already knows better. |
| 8 | **The docs name two surfaces that are not on screen.** (a) The route table's `/studio` → "Studio"; Studio was removed and the address now renders Settings, so the reader sees *something* and cannot tell it is the wrong thing. (b) Every model-setup instruction in the product tells you to use "the **Concierge**" — a word that appears nowhere in the UI; the window is labelled "Models". This is the second step of getting AI work running. | (a) `docs/GETTING_STARTED.md` route table vs `web/src/routes.tsx:70-72`. (b) `docs/GETTING_STARTED.md:139`, `docs/MODELS.md:4`, `docs/GLOSSARY.md:19`, `docs/internal/POSITIONING.md:187` vs `web/src/desk/applications.ts:304,317`. |
| 9 | **The CLI's only desk-population command is undocumented, and three others with it.** `holdspeak seed` exists, is idempotent, and appears in `holdspeak --help` — and in no `.md`. `history`, `actions`, `node` likewise. | `holdspeak/main.py:443-446`; grep of `docs/` + `README.md`. |
| 10 | **The doc-freshness fence does not cover the getting-started path.** HS-200-46 is a genuinely strong mechanism — 16 sentences with executable predicates, bidirectional fences, a down-only ratchet — pointed almost entirely at architectural canon. Every defect in rows 1-9 above passes CI today. Meanwhile the one number `README.md` duplicates by hand from a generated doc (`222`/`40` against a live `225`/`41`) is the one that rotted, proving the mechanism works and is simply aimed elsewhere. | `tests/unit/doc_claims/registry.py` (16 rows, 0 touching README or GETTING_STARTED); `README.md:106` vs `docs/MCP_SIDECAR.md:4`. |

**Honourable mentions** (real, not top-10): thirteen terminology conflicts across four
competing canonical-name sources, of which ten are doc-canonical names with no UI
presence at all (§5, C9); `docs/GLOSSARY.md`'s "sidecar" entry contradicts
`docs/MCP_SIDECAR.md`; the extras table omits `wakeword`/`tts`/`presence`;
`CHANGELOG.md` is 18 days and ~12 phases behind a `0.4.0` version pin; four docs named
as source canon in `CLAUDE.md` were last touched in June/July; and
`docs/internal/ARCHITECTURE_WEB_FRONTEND.md` — where `CONTRIBUTING.md` sends every web
contributor — is two months stale.

**What is genuinely good, stated plainly so the contrast is legible:** the generated
references are exact (693 routes, 225 tools, both diffed clean); `docs/USER_GUIDE.md` is
2 900 lines and four out of four sampled labels verified; `docs/SECURITY.md` is an
honest operator document that names its own unenforced claim; the seeded first-run
(six drawers, Start here note, Everyday context) matches its manifest exactly; the
macOS permissions section of `docs/GETTING_STARTED.md` is the best piece of writing in
the repo and all eight of its state strings exist verbatim in the code; and boot itself
takes about two seconds to a serving `/health`.

The problem is not that this product is undocumented. It is that the documentation was
written for someone who already has it running.
