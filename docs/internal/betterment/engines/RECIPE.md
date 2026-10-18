# Engines: recipe

Build order for `DESIGN.md`. One slice = one PR in the fast cycle
(`CLAUDE.md`). File and line references are from `MODEL.md` (2026-10-17);
check them against main before you start.

Rules for every slice: tests never run the owner's real `claude`, `codex`,
`pi` or `gemini`. They put a fake script on PATH inside the scratch HOME.
Every rig hub sets `HOLDSPEAK_CLI_ENGINES=off` unless the test turns it on.
Faces obey `docs/internal/UX-CANON.md`: the library Button, no modals, no
counters of zero.

The security fix for `/api/setup/discover-models` (the env `OPENAI_API_KEY`
sent to any typed address) is a separate PR, already in flight. It is not
a slice here.

---

## E0. Shots of today

- **Goal:** we have the honest "before" picture.
- **Files:** `docs/internal/betterment/engines/shots/`, `RECON.md`.
- **Changes:** on an isolated hub, walk Settings → Engines at 1440 and 393:
  empty, Add an engine, Check against a stub server, the switchboard, a
  drag. Log presses and confusion the way `../workbench/RECON.md` does.
- **Done when:** the shots and the log exist, and DESIGN §2 cites them.
- **Tests:** none.
- **Not in this slice:** any code change.

## E1. The agent CLI engine (backend)

- **Goal:** an agent (or MCP) can add Claude Code or Codex as an engine and
  assign it to a job, and the job runs on it.
- **Files:** new `holdspeak/intel/cli_engine.py`; `inference_targets.py`;
  `intel/providers.py`; `services/inference_route_plan_service.py`;
  `services/model_profile_service.py`; `inference_locality.py`;
  `services/profile_service.py`; `services/model_library_service.py`;
  `mcp/families/model_library.py`; `web/routes/model_library.py`. (The
  kind map is copied in five of them; see MODEL §3.)
- **Changes:**
  - Add kind `cli_engine`, profile kind `cliCommand`, transport
    `subprocess`, runtime family `cli_v1`, provider family `cli_agent`.
    Store the preset as `base_url = "cli:<preset>"` and the model in
    `model`. No schema change.
  - Add `CliEngine(MeetingIntel)`. It overrides `_ensure_model_loaded`
    (the executable is on PATH), `_chat_completion_text` (runs the process)
    and `run_prompt_stream` (yields the whole answer as one delta).
  - Write the prompt as one text on stdin. Close stdin after it. Run in an
    empty temp folder. Use a timeout for each preset, inside the runner
    deadline, and kill the process on timeout or cancel.
  - Use a closed preset table: `claude` and `codex`, with the argv from
    `agent_summarizer.py` (`build_summarizer_command`). Reuse
    `validate_summarizer_command` and `_extract_summary_text`; do not write
    them a second time. Claude gets `--max-budget-usd 0.10`.
  - For typed jobs, add the JSON schema to the prompt. A bad answer is
    `invalid_typed_output`, and the chain goes to its fallback.
  - Set the egress boundary to `cloud`, with the preset's vendor host.
  - The compatibility check refuses `speech.*` for `cli_v1`.
  - Add the verb `connect_cli_engine(principal, draft)`, plus an MCP tool and
    a route next to `connect_hosted_model`.
  - Add the rig switch `HOLDSPEAK_CLI_ENGINES` (default on; rigs set it to
    off).
- **Done when:** with a fake `claude` on PATH, `connect_cli_engine` plus an
  assignment of `ask.answer` makes an Ask return the fake CLI's text, with
  egress `cloud` / `API.ANTHROPIC.COM`. A fake that sleeps past the timeout
  is killed and the chain falls back.
- **Tests:** T1 hub tests, `tests/integration/test_desk_engines.py` (new),
  plus a unit file for `cli_engine.py`.
- **Not in this slice:** any face change; pi and Gemini presets; streaming.

## E2. Found on this Mac, and one-press Add

- **Goal:** his installed, signed-in CLIs appear under Found, and one press
  adds one.
- **Files:** `services/concierge_service.py` (`detect`);
  `web/src/features/runson/model.ts`, `useRunsOn.ts`, `RunsOnCore.tsx`;
  `web/src/features/runson/__tests__/` (or the runs-on app test).
- **Changes:** `detect` lists each CLI preset whose executable is on PATH,
  with the sign-in reads from `onboarding_service.py:696-773` (UNKNOWN means
  "try once"). The face shows them under **Found on this Mac**, with an
  agent emblem and the vendor egress chip, and **Add** calls
  `connect_cli_engine`. The engine row shows NOT SIGNED IN in words when
  that applies.
- **Done when:** on a hub with a fake signed-in `claude`, the Engines window
  shows "Claude Code · signed in" under Found. Add moves it into Your
  engines as READY with the ANTHROPIC chip, at 1440 and 393. With nothing
  found, the section is absent.
- **Tests:** T2 vitest on recorded hub answers
  (`scripts/record_needs_you_fixture.py` pattern); the T3 sweep stays green.
- **Not in this slice:** What runs where; services.

## E3. The model picker, and one engine for each model

- **Goal:** he chooses the model; two models on one host are two engines.
- **Files:** `web/src/features/runson/useRunsOn.ts` (`:778-812`),
  `RunsOnCore.tsx`; `web/src/features/concierge/endpointDraft.ts`
  (`:56-83`); the matching vitest.
- **Changes:** Check fills a searchable picker; nothing is picked for him.
  The profile id comes from host + model, not host only. **Use** saves the
  model that he picked.
- **Done when:** against a stub server with three models, Check lists all
  three and he can add two of them, which become two engines. An old
  host-only engine still loads (no data loss).
- **Tests:** T2 vitest; T1 for the profile id.
- **Not in this slice:** named service tiles.

## E4. Add an engine, by kind

- **Goal:** Add an engine asks *what kind*, and a service needs no URL.
- **Files:** `RunsOnCore.tsx` (the add row `:78-160`),
  `services/concierge_service.py` (unskip the hosted presets, `:724`),
  `services/model_library_service.py` (Anthropic: try the OpenAI-compatible
  endpoint; unblock the name only if `/models` passes), the vitest.
- **Changes:** Add an engine unfolds in place into five tiles (agent on this
  Mac, service, server on my network, model on this Mac, another
  HoldSpeak). Services are named tiles (OpenRouter, OpenAI, Anthropic,
  Gemini) that carry their base URL. The key field leads to the E3 picker,
  with catalog presets on top. Remove NOT SUPPORTED YET dead ends.
- **Done when:** OpenRouter with a chosen model takes at most 5 presses and
  one paste, with no URL typed (stub OpenRouter in the rig). Anthropic is
  either a working tile or absent.
- **Tests:** T2 vitest; T1 for the presets in `detect`.
- **Not in this slice:** the assignment list.

## E5. What runs where

- **Goal:** each job is a row with a picker, and single jobs can be set.
- **Files:** a new `web/src/features/runson/WhatRunsWhere.tsx`;
  `useRunsOn.ts` (`scopeFor`, `:152-154`, writes `capability:<cap>` as
  well as `group:` and `global`); `RunsOnCore.tsx`; the vitest. Park the
  switchboard component behind RAW (move it; do not delete it).
- **Changes:** the rows and words from DESIGN §4. The picker lists only
  engines that can serve the job (compatibility from the hub). The change
  is applied at once, with Undo in the foot. Try it shows the answer or the
  error in words under the row.
- **Done when:** "Meeting summaries → OpenRouter" and "Answers → Claude
  Code" take 2 presses each. An inheriting row reads "Everything else".
  Speech to text lists no agent or service. 1440 and 393.
- **Tests:** T2 vitest; T1 for capability-scope writes; the T3 sweep.
- **Not in this slice:** per-automation engines (that is the Automations
  recipe).

## E6. One name

- **Goal:** the user sees "Engines" everywhere.
- **Files:** `web/src/desk/applications.ts` (`:189-191`, `:356-368`),
  `RunsOnCore.tsx` (`:170`), `SettingsCore.tsx`, the palette entries, the
  user docs that say "Runs on".
- **Changes:** retitle only. Routes and code names stay.
- **Done when:** no visible "Runs on" or "Concierge" text remains (a canon
  guard greps the built UI strings).
- **Tests:** T3 sweep; the doc guards.
- **Not in this slice:** route renames.

## E7. pi and Gemini CLI presets

- **Goal:** the other agents he named.
- **Files:** `intel/cli_engine.py` (the preset table); `concierge_service.py`.
- **Changes:** first confirm each CLI's one-shot flags and the tools-off
  mode on this Mac (record them in this file). For pi, the egress chip
  comes from the owner ("MY SERVER" means private network).
- **Done when:** both appear under Found when installed and answer Try it
  through a fake script in tests.
- **Tests:** T1.
- **Not in this slice:** streaming output (a later slice, Claude
  `stream-json` first).
