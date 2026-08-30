# Phase DC-01: The Desk Chat — porting the warpdrv chat experience into HoldSpeak

> **Status:** DC-01 shipped as Phase 151; DC-02 shipped as Phase 152
> The Hands; DC-03 shipped as Phase 153 The Practice; DC-04+
> unchartered. Backlog candidate **AF** in
> `pm/roadmap/holdspeak/BACKLOG.md` is the handoff row.
>
> **Reference:** [mikjee/warpdrv](https://github.com/mikjee/warpdrv) —
> "LLAMA.cpp Server Manager + Chat + Tools", ~83k LOC, **AGPL-3.0**.
> Studied from a shallow clone at commit of 2026-08-29 (the `packages/bridge`
> chat engine, `packages/server/src/routes/chat.ts`, the `FEApplet` applet
> system, the `warpmcp` tool server, the landing-site guides).
>
> **Owner ask (verbatim):** "how could we, realistically, port the chat
> feature that warpdrv is based on into HoldSpeak? Basically, augment
> HoldSpeak with the abilities this chat interface and features really
> present themselves."

## 0. The answer in one paragraph

We do not port warpdrv's code; we port its **capabilities** onto machinery
HoldSpeak already owns. warpdrv is AGPL-3.0 and HoldSpeak is Apache-2.0
(`LICENSE`, `pyproject.toml`), so a single copied function would relicense
the product — the port is a clean-room re-implementation of the *shape*
(thread tree, streamed message parts, tool loop with approval, modes,
guardrails, annotations, compaction, subthreads, voice call). The good news
is that roughly two-thirds of warpdrv's chat stack maps onto things HoldSpeak
already has and warpdrv had to build from nothing: the kernel's tool-turn
lifecycle (`tool_turns` + `tool_turn_tool_calls`, `holdspeak/kernel/tool_call.py`)
is warpdrv's approval loop with receipts; the Intelligence Router
(Phase 143) is its server/preset picker; the 82-tool MCP server
(`holdspeak/mcp/families/`) is its `warpmcp` — except ours already knows
meetings, people, decisions, commitments, the Door and the calendar; the
WebSocket bus (`web/src/runtime/RuntimeBus.tsx`, `holdspeak/realtime_frames.py`)
is its SSE fan-out; the FTS memory corpora (`holdspeak/db/memory.py`) are its
workspace RAG; the click-to-toggle mic (`MicButton.tsx`) is its dictation.
What HoldSpeak genuinely lacks — and the port must build — is small and
specific: **a persisted thread/message model, token streaming end to end, a
Thread primitive on the Desk, the chat-side tool loop wired to the kernel,
and TTS.** Everything else is a projection over existing tables. Realistic
size: five phases, the first of which (The Thread) is one open-throttle
arc in this era's rhythm and already replaces today's localStorage-only
`web/src/desk/chat.ts`.

## 1. Why this phase exists (the value-era frame)

The value era's charter question (`pm/roadmap/holdspeak/HANDOVER.md` §0):
*does this make the architect-who-manages-three measurably better at their
actual week?* A chat is only worth building if it is a chat **over the desk**:

- "What did I promise Ania last 1:1, and is it done?" → `people.*` +
  `decision_commitments` tools, answered in one thread, receipted.
- "Draft the Monday note from this week's three meetings" → grounding
  refs (`web/src/desk/grounding.ts`) + `meeting.get` + `ask.keep` minting an
  artifact — exactly today's Ask/Keep verb, but multi-turn and streamed.
- "Move the two open items from Tuesday's sync onto Marek's ledger" → the
  chat *proposes* a tool effect; the kernel admits it; the Door updates; the
  receipt sits in the thread.
- Talk it through on a walk (voice call mode: STT → thread → TTS).

warpdrv proves the *interface grammar* for this (threads, approval boxes,
status line, annotations, modes) but its tools are a coder's (`shell_exec`,
`file_patch`, `rg`, code graph). HoldSpeak's tools are a manager's. The port
keeps warpdrv's grammar and swaps the hands.

Today's gap is concrete (audited 2026-08-29, worktree of main `c9b0cd25`):

| Capability | HoldSpeak today | Path |
|---|---|---|
| Persisted threads/messages | **none** — `web/src/desk/chat.ts` keeps threads in `localStorage['hs.desk.chats']`, hub stores only `recipe_chat_results` / `ask_results` projections | build (§6.2) |
| Token streaming | **none** — `holdspeak/intel/providers.py` has zero `stream` handling; every LLM call returns one JSON blob | build (§6.3) |
| Model choice, fallback, egress | Router: profiles → assignments → frozen route plan → `InferenceRunner` → receipt | reuse |
| Tool calls with approval | Kernel tool-turn lifecycle (reserved → model_running → tool_requested → tool_admitted → tool_receipted → result_ready), dialects `gemma4/qwen/openai/granite` | reuse + wire (§6.4) |
| Tool surface | MCP server, ~82 tools across 15 families (`desk.*`, `meeting.*`, `people.*`, `ask.*`, `thought.*`, `door.*`, `cadence.*`, `memory.search`, …) | reuse as the in-process tool registry (§6.4) |
| External MCP servers (`mcp.json`) | **none** — HoldSpeak is an MCP *server*, never a client | build later (DC-02, optional) |
| Live UI fan-out | One WebSocket bus, 35 frame types, mirrored to `web/src/runtime/frames.ts` | reuse, add frames |
| STT | Whisper, click-to-toggle mic on every input, DIR-01 intent routing | reuse |
| TTS / VAD | **none** in production (`say` referenced in templates only) | build (§6.8) |
| Search over chats | FTS5 pattern exists (`segments_fts`, three memory corpora) | extend |
| Vector RAG | **none** (only speaker-voice embeddings) | defer; FTS first |
| Markdown / code / mermaid | rendered in Note/Artifact/Decision pullouts; mermaid present for docs | reuse; add streaming-safe renderer |

## 2. Normative language

MUST / MUST NOT / SHOULD / MAY per RFC 2119. "The kernel" = Article XI
machinery under `holdspeak/kernel/`. "The router" = Phase 143's Intelligence
Router. "The bus" = the runtime WebSocket. "Thread" = the new primitive
defined in §6.1.

## 3. Constitutional grounding (cite or die)

- **Art. I — the Desk is the operating surface.** Chat is not a screen; a
  Thread is a desk object that opens in a pullout/window like a Note.
  No `/chat` route with its own sidebar-world. The thread *list* is the
  Desk's own list view filtered to kind `thread` (folders = the Desk's
  existing directories; warpdrv's folder tree is not ported — the Desk
  already has one).
- **Art. II — everything is a primitive.** `thread` joins
  `web/src/lib/primitives.ts`; UI derives from it (`project_desk_primitive_contract`).
- **Art. III — local first, honest egress.** Every assistant turn carries
  the router's egress badge (`chat.ts` already types
  `egress: {scope, host}`); one badge per turn, no prose.
- **Art. IV — voice is first-class.** The composer has the mic; voice
  *arms*, never fires (the VAD-chat auto-send in §6.8 is an explicit per-
  thread toggle with a visible state, never a default).
- **Art. V / XI — consent is the spine; the kernel is the ledger.** Every
  tool call the model requests is a kernel operation, child of the thread
  turn. warpdrv's ALLOWED/ASK/DENIED tiers collapse onto the existing
  `control_mode ∈ {safe, neutral, yolo}` policy
  (`holdspeak/operation_policy.py`); under the default YOLO posture the
  approval box is a *receipt* box (ledger, not gate — owner ruling). Safe
  mode renders warpdrv's Allow-once / Allow-always / Deny.
- **Art. VII — the interface serves.** No modals: the pending-tool box,
  elicitation form and annotation popover are in-flow rows of the thread
  surface. Errors land as turn rows (error surfaces never overlap).
- **Art. IX — proof over claim.** DoD (§13) requires a real-metal walk on
  `.43` streaming from llama.cpp, and shots at 1440 + 393 before any
  story flips.

## 4. Scope and non-scope

### 4.1 In scope (the port, five phases)

| Phase | Name | What lands | warpdrv source of the idea |
|---|---|---|---|
| DC-01 | **The Thread** | thread/message/part tables; streamed turns over the router; Thread primitive + ThreadPullout; composer w/ mic, `@`-refs, attachments; markdown/code/mermaid; Keep→artifact; chat FTS; branch on edit/regenerate | `bridge/persistence`, `orchestrator` streaming, `thread.tsx`, `thread-list.tsx` |
| DC-02 | **The Hands** | model tool calls → kernel tool turns; the MCP families as the in-process tool registry; pending-tool box (receipt in yolo, decision in safe); per-thread tool set; status line; elicitation as a kernel decision; tool result renderers for desk kinds | `orchestrator.executePass`, `PendingToolCallsBox`, `Elicitation.tsx`, `set_current_status` |
| DC-03 | **The Practice** | slash commands on the verb registry; **modes** (tool allow-list + prompt + guardrails) as a Recipe extension; **guardrails** as a second router assignment reviewing tool calls; **annotations** (select → comment/dictate → queued into next turn); `/compact`; thread todo = action items | `FEApplet` slash commands, `mode-types.ts`, `guardrail-types.ts`, `SelectionPopover.tsx` |
| DC-04 | **The Call** | TTS (Kokoro, Apache-2.0) per assistant turn; VAD; voice-call mode (listen → send → speak, visible state, click to stop) | `KokoroTTS.tsx`, `VoiceInput.tsx`, `DictationContext.tsx` |
| DC-05 | **The Crew** | subthreads: a thread spawns child threads running under a Recipe/mode with auto-approved tools, parent↔child messages as bus notifications, block-then-background | `subthreadService.ts`, `create_subthread`/`*_send_message` tools |

### 4.2 Out of scope (deliberately not ported)

- **llama-server lifecycle** (backends, recipes, hub downloads, launch
  dialogs, KV-cache checkpoints, the OpenAI proxy/aliases, slot pills).
  HoldSpeak's profiles table and the router are that dial ("one dial law");
  `.43` runs llama.cpp on its own. Checkpoints are a llama.cpp-operator
  feature with no manager-of-three value.
- **Code graph** (tree-sitter callers/callees) and `shell_exec`/`file_*`/`rg`
  tools. Coder work rides the existing coder sessions
  (`holdspeak/coder_steering.py`, `SessionPullout` + xterm); the chat may
  *open* a coder session via `coder.*` tools, it does not become one.
- **Nested folder tree for threads** — the Desk's directories/list view are
  the container (Art. I).
- **Vector embeddings** — FTS5 over the memory corpora + transcripts first;
  `sqlite-vec` is a ledgered follow-on if FTS recall proves insufficient on
  the owner's real data.
- **Sampler-preset editor** (mirostat/DRY/XTC/dynatemp/grammar) — the
  router's profile is the knob; a per-thread `temperature` override is the
  only sampler field surfaced.
- **External `mcp.json` client** — optional DC-02 rider, only if the owner
  names a server they want in the thread (Jira via candidate W is more
  likely to arrive as a `desk_sync` connector than an MCP client).
- **Tauri shell, Chakra, assistant-ui.** The web Desk is the spec; the
  Signal Workbench material model is the only kit. assistant-ui (MIT) is
  *allowed* but not *needed* — its value is headless streaming primitives,
  and our bus already delivers ordered frames; adopting it would put a
  second state model beside zustand. Decision: build on the existing
  pullout/surface kit.

## 5. Relationship to existing plans and code

- **Supersedes** the device-local chat in `web/src/desk/chat.ts` and the
  `modelchat:hub:` pseudo-recipe hack; `/api/recipes/{id}/chat`
  (`holdspeak/web/routes/primitives/recipes.py:111`) becomes a thin alias
  that opens a Thread bound to that recipe.
- **Absorbs** Phase 118 The Hopper's unbuilt inlet (`InletAutocomplete.tsx`
  is reused as the composer's `@`-ref popover; the inlet endpoint never
  shipped and is not needed separately).
- **Extends** Phase 141's refinement loop philosophy (explicit context,
  frozen refs, receipts) to open-ended conversation; it does not replace
  the Thought interview, which stays the one-question-at-a-time surface.
- **Rides** Phase 143's route plans: a thread turn is one more capability
  (`chat.turn`, `chat.guardrail`, `chat.compact`, `chat.subthread`) in the
  sealed registry with its own assignment row, so the owner picks the
  chat model in Models → Assignments like every other job.
- **Rides** Article XI's tool-turn cluster verbatim; DC-02 adds no new
  admission path (Phase 131's fence stays at one path).
- **Feeds** candidates A (delegation lane — the chat is the fastest way to
  ask "what am I waiting on from X") and W (Jira desk sync — synced notes
  become groundable refs).

## 6. Architecture delta

### 6.1 The Thread primitive

`thread` = DeskPrimitive `{ id, title, recipe_id?, mode_id?, profile_override?,
directory_id?, parent_thread_id?, status_line, token_in, token_out,
created_at, updated_at, last_turn_at }`. Opens in `ThreadPullout` (desktop
window / phone sheet per the pullout protocol). Verbs on the registry:
`New thread`, `Continue in thread` (from any Note/Meeting/Decision/Person
— the object becomes the first grounding ref), `Keep as note`, `Keep as
artifact`, `Fork here`, `Search threads`, `Call` (DC-04).

### 6.2 Schema delta (additive, one declarative block in `holdspeak/db/schema.py`)

```
threads(id, title, recipe_id, mode_id, profile_override, directory_id,
        parent_thread_id, status_line, token_in, token_out,
        created_at, updated_at, last_turn_at, deleted_at)
thread_messages(id, thread_id, parent_id,          -- tree; branch = sibling
        role  CHECK IN ('user','assistant','system','tool'),
        turn_id,                                   -- FK tool_turns when a tool pass ran
        operation_id, receipt_id,                  -- kernel provenance for assistant turns
        egress_scope, egress_host, model_id, route_plan_id,
        stats_json, created_at, completed_at, aborted_at)
thread_message_parts(id, message_id, ordinal,
        kind CHECK IN ('text','reasoning','tool_call','attachment','annotation'),
        text, tool_call_id, attachment_ref, meta_json)
thread_refs(thread_id, message_id, ref_kind, ref_id, version)   -- frozen grounding leaves (141's law)
thread_tool_policy(thread_id, tool_name, decision CHECK IN ('allow','ask','deny'), set_at)
thread_messages_fts (FTS5 over parts.text, content=thread_message_parts)
```

Notes: `parent_id` gives warpdrv's branch-on-edit for free; message parts
are the discriminated union warpdrv uses (`TEXT | REASONING | TOOL_CALL |
ATTACHMENT`) plus `annotation` (DC-03). Tool calls themselves are NOT a new
table — they are `tool_turn_tool_calls` rows; the part holds the id.
Attachments are stored as artifacts (existing table), never inline base64
in the row. Migration: none needed for existing chats — localStorage
threads are imported once by the web client through `POST /api/threads/import`
on first open (cheap, honest, deletable).

### 6.3 Streaming — the one new seam in the router

`InferenceRunner` gains a streaming variant: `run_stream(request) ->
Iterator[Delta]` where `Delta ∈ {text, reasoning, tool_call_delta, usage,
done, error}`. `holdspeak/intel/providers.py` gets an SSE reader for
`/v1/chat/completions` with `stream: true` (llama.cpp, OpenRouter, OpenAI —
all emit the same `delta.content` / `delta.reasoning_content` /
`delta.tool_calls[]` shape). Non-streaming callers are untouched; the
frozen route plan, fallback disposition and receipt attestation wrap the
stream exactly as they wrap a blob today (the receipt is written at `done`,
or `indeterminate` on abort — the kernel already has that state).

Fan-out: three new frame types in `holdspeak/realtime_frames.py`
(mirrored to `web/src/runtime/frames.ts` by the existing generator):
`thread.turn_started`, `thread.delta` `{thread_id, message_id, part_ordinal,
kind, text}`, `thread.turn_done` `{…, receipt_id, egress, stats}`. Deltas
are ALSO persisted (append to the part's text every N ms / at done) so a
reload mid-turn shows the partial and the bus resumes it — warpdrv's
"chunks persisted as parts and broadcast immediately" rule. Abort =
`POST /api/threads/{id}/abort` → the runner's cancellation token; the
turn's `aborted_at` and an `indeterminate` receipt.

### 6.4 The tool loop on the kernel (DC-02)

> **Status:** SHIPPED as Phase 152 The Hands.

warpdrv: `executePass()` streams → finalize tool calls → resolve permission
→ execute → recurse (≤10 passes) or halt `PENDING_APPROVAL`; resume after
the user's decision.

HoldSpeak mapping (all existing states, `holdspeak/kernel/tool_call.py`):

```
assistant turn = tool_turn (reserved → model_running)
  model emits tool_calls            → tool_requested (one child op per call, Art. XI 6)
  policy(control_mode, thread_tool_policy)
      yolo / allow  → tool_admitted → execute → tool_receipted
      safe  / ask   → awaiting_decision  ⇒ bus frame thread.tool_pending
                       user: Allow once | Allow always (writes thread_tool_policy) | Deny
      deny          → refused receipt, model told "denied"
  all calls resolved → result_ready → next model pass (MAX_PASSES = 10, same cap as warpdrv)
```

Tool registry = the MCP families, called **in-process** (no stdio
round-trip): `holdspeak/mcp/tools.py` already exposes name/schema/handler
per tool, so the chat's tool list is `families.tools()` filtered by the
thread's mode and `thread_tool_policy`. Tool classes map straight onto the
kernel's `evidence_read` (reads: `meeting.get`, `people.brief`,
`memory.search`, `door.board`…), `candidate_builder` (drafts), and
`effect_proposal` (writes: `desk.update`, `people.commitment_transition`,
`cadence.*`). Default mode allow-list = every `evidence_read` tool + the
`candidate_builder`s; `effect_proposal`s are on in yolo, ask in safe.
Elicitation (an MCP tool asking the user a question mid-call) = a kernel
`awaiting_decision` with a JSON-Schema payload; the thread renders a form
row; Submit/Decline resolve the operation. No new admission path.

### 6.5 Modes, prompts, guardrails (DC-03)

> **Status:** SHIPPED as Phase 153 The Practice.

- **Mode** = `{name, colour, prompt_ref, allowed_tools[], allowed_recipes[],
  guardrail_ids[]}` stored as a Recipe of kind `mode` (recipes already hold
  `system_prompt`, `tools_json`, `profile_id`). Built-ins seeded (the
  seed-is-meaningful-presets rule): **Desk** (reads + drafts), **Chase**
  (people/commitment effects on), **Draft** (no tools, writing model),
  **Plan** (thought.* + door.* reads). Mode tabs sit in the composer head;
  switching re-renders the system prompt for the *next* turn only.
- **Prompt** = a Note tagged `prompt` (no new table); `/prompt <name>`
  inserts it.
- **Guardrail** = a second, cheaper router assignment (`chat.guardrail`)
  run once per tool-requesting pass with the guardrail's instruction, the
  last N messages and the pending calls; it returns `{violations[],
  warnings[]}` rendered as a row **before** the pending-tool box. It never
  auto-denies (warpdrv's rule, and ours: ledger not gate) — but in safe
  mode a violation flips the box's default to Deny. Seeds: `effect-guard`
  (flags any `effect_proposal` touching a person's ledger without a
  named source) and `egress-guard` (flags cloud egress of a `people.*`
  read result — the People refusals are a HARD boundary, the guardrail is
  belt over braces).

### 6.6 Slash commands, annotations, compaction, todo (DC-03)

> **Status:** SHIPPED as Phase 153 The Practice.

- `/` in the composer opens the verb registry filtered to thread verbs:
  `/compact`, `/mode <m>`, `/prompt <p>`, `/keep`, `/fork`, `/todo`,
  `/call`, `/guardrail on|off <g>`, `/tools`. Registry, not a second
  command system.
- **Annotations:** select text in any assistant part → in-flow popover
  (comment field WITH mic, per Art. IV) → queued `annotation` parts on a
  pending user message, shown as chips above the composer, sent with the
  next turn as a `preCompletion` prefix ("The user annotated: …"). This is
  the single most manager-shaped feature in warpdrv (mark up a draft by
  voice) and costs ~300 LOC.
- **Compaction:** `/compact` runs `chat.compact` (summarise thread, keep
  refs) and writes a `system` message with `parts.kind='text'` marking the
  cut; later turns send messages after the cut plus the summary. Token
  counts on the thread head make the need visible.
- **Todo:** warpdrv's thread-scoped todo list becomes **action items**
  (`action_items` already exist and land on the Door). `todo_write` from
  the model = `door.add_item` effect with `source=thread:<id>`. No parallel
  list.

### 6.7 Status line, search, attachments

> `set_current_status` SHIPPED as Phase 152 The Hands (the `thread` MCP family, 142 tools / 31 families).

- `set_current_status` → `threads.status_line`, shown under the window
  title (one line, no prose).
- Search: `thread_messages_fts` joins the memory corpora; `memory.search`
  gains corpus `threads`; the Desk's search box already federates.
- Attachments: drop/`+` on the composer → artifact (existing upload path,
  existing 10 MB-class limits) → `attachment` part with the artifact ref;
  PDF/text extraction reuses the artifact text pipeline; images ride the
  vision-capable assignment (146's `vision=True` refusal law applies).

### 6.8 The Call (DC-04)

- **TTS:** Kokoro (Apache-2.0). Two options; recommend **B**:
  A) `kokoro-js` in the browser (ONNX, ~300 MB first load, no server work);
  B) `kokoro` Python package server-side behind `POST /api/tts` streaming
  WAV chunks — keeps the model on the hub (Art. III, one place), works for
  iPad later, and the hub already streams audio the other direction.
  Per assistant turn: a speaker glyph; in call mode, auto-speak on
  `turn_done` (sentence-chunked so speech starts before the turn ends).
- **VAD:** `@ricky0123/vad-web` (MIT, Silero ONNX) client-side; endpoint
  detection sends the utterance through the existing Whisper WS path.
- **Call mode:** one visible state on the thread head (LISTENING /
  THINKING / SPEAKING / OFF), click to stop, never a default; barge-in
  stops TTS. Egress badge stays per turn.

### 6.9 The Crew (DC-05)

`chat.subthread` tool: creates a child `threads` row
(`parent_thread_id`), bound to a Recipe/mode with `thread_tool_policy` =
allow for its list (warpdrv: subthread tools are auto-approved; ours:
still receipted, admitted as children of the parent turn's operation).
Runs on the workbench conductor's run-loop (`holdspeak/workbench_conductor.py`
already owns fresh-session agent runs + bus frames) — the parent blocks 30 s
then backgrounds; child → parent messages are `thread.notification` frames
that the parent's next pass consumes as a `tool` role message. The child
thread is a real desk object the owner can open and steer.

## 7. Surfaces (shots law: 1440 + 393, before any flip)

- **ThreadPullout**: head (title · mode tab strip · model/egress badge ·
  status line · token meter) / turns (user rows, assistant rows with parts;
  reasoning folded behind RAW; tool rows with a per-kind renderer — a
  meeting result renders as the meeting chip, a person as the person card,
  a board as lanes — and the receipt id; pending-tool box; guardrail row;
  elicitation form row; error row) / foot (annotation chips · composer
  with mic + `@`-refs + `/`-verbs + `+` attach · Send/Stop).
- **Desk list view** for kind `thread` (title, last turn, mode colour
  swatch, token meter); "Continue in thread" on every object's context
  menu (the 148 menu grammar).
- **People / Meeting pullouts** gain a "Threads" row listing threads that
  reference them (via `thread_refs`).
- **Settings → Assignments** shows the four new capabilities.
- Beauty pass after each functional pass; owner sees shots before merge
  (standing law).

## 8. Data flow of one turn (DC-01 + DC-02)

```
composer Send
 └─ POST /api/threads/{id}/turns {text, refs[], attachments[], mode_id}
     ├─ persist user message + parts; freeze refs (thread_refs, versioned)
     ├─ kernel: admit chat.turn (principal = owner, target = thread)
     ├─ router: route plan for capability chat.turn (+ thread.profile_override)
     ├─ assemble: mode prompt + compaction summary + messages after cut
     │            + ref leaves + tool schemas (mode ∩ policy)
     ├─ InferenceRunner.run_stream → deltas → bus thread.delta (+ persist)
     ├─ tool_calls? → §6.4 loop (child ops, receipts, maybe awaiting_decision)
     └─ done → receipt attestation; bus thread.turn_done {receipt, egress, stats}
```

## 9. Detailed requirements (DC-01 unless tagged)

**Functional**
- F1 A Thread is a DeskPrimitive; creating one from any object seeds refs.
- F2 Turns stream token-by-token to every connected client; reload mid-turn
  resumes from persisted partial.
- F3 Edit-and-resend or Regenerate creates a sibling branch; the UI shows
  `‹ n/m ›` on branched rows.
- F4 Stop aborts the turn within 250 ms and leaves an `indeterminate` receipt.
- F5 Every assistant turn shows model + egress badge (Art. III) and a
  receipt id.
- F6 Keep → artifact or note, with the thread as provenance.
- F7 Threads are searchable from the Desk search and `memory.search`.
- F8 (DC-02) Model tool calls execute only through the kernel; yolo shows
  receipts, safe shows Allow-once/always/Deny; MAX 10 passes.
- F9 (DC-02) Tool results render by kind (meeting, person, board, note,
  decision); RAW folds the JSON.
- F10 (DC-03) Modes, prompts, guardrails, annotations, `/compact` as §6.5–6.6.
- F11 (DC-04) Call mode as §6.8 with visible state and barge-in.
- F12 (DC-05) Subthreads as §6.9.

**Non-functional**
- N1 First delta ≤ 1.5 s on `.43` (llama.cpp Q6) for a 2k-token context.
- N2 A thread of 500 messages opens ≤ 300 ms (parts loaded per page).
- N3 No new admission path; `.githooks/dw check` and the Phase 131 fence
  stay green.
- N4 People data never crosses to a cloud profile in a `people.*` tool
  result without the existing refusal firing (hard boundary).
- N5 Zero AGPL-derived source. Reviewer checklist item; the warpdrv clone
  never enters the repo, and no file may cite a warpdrv path as its source.

## 10. Verification strategy

- Unit: schema reconcile (additive, idempotent, on a COPY of the owner's
  real DB — the 137 law); SSE reader against recorded llama.cpp/OpenRouter
  streams; tool-loop state machine with a fake runner (all 6 states, the
  10-pass cap, deny path, abort mid-pass).
- Web (vitest + real-Chromium probes — jsdom lies about focus): composer
  keys, branch picker, pending box, annotation popover, call-state glyph.
- Glass (Playwright, 1440 + 393): the 7 rows of §7 populated AND empty AND
  error; cross-read shots.
- Real metal (`.43`): one streamed thread with two tool calls
  (`people.brief` read, `door.add_item` effect) end-to-end, receipts read
  back; control-vs-treatment per the real-metal law.
- Cold walk: a new leg appended to `scripts/door_walk_hs144.py` ("Continue
  in thread" from a Door item → tool call → receipt).

## 11. Implementation recipe (DC-01, one arc; ~8 stories)

1. **Schema + repo** — the §6.2 block, `ThreadRepository`, import endpoint.
2. **Streaming runner** — `run_stream`, provider SSE reader, receipt at
   done/abort, three bus frames.
3. **Capability + assignment** — `chat.turn` in the sealed registry, seed
   assignment = the Ask assignment's chain.
4. **Turn route** — `POST /api/threads`, `/turns`, `/abort`, `/branch`,
   `/keep`; refs frozen via 141's hydration.
5. **Thread primitive + pullout** — kind, verbs, ThreadPullout rows,
   streaming text renderer (append-safe markdown; mermaid/code after
   `turn_done`).
6. **Composer** — mic, `@`-refs (InletAutocomplete), `+` attach, Send/Stop,
   `/` verb filter.
7. **Search + list** — FTS, memory corpus, Desk list view, "Threads" rows
   on People/Meeting pullouts; localStorage import + `chat.ts` retirement.
8. **Walk + docs + close** — real-metal walk, glass exhibit, README/entry
   docs (the dedicated docs story law), counsel close.

DC-02 (~6 stories): tool registry adapter · turn↔tool_turn wiring · pending
box + policy · elicitation row · kind renderers · status line + walk leg.
DC-03 (~6): modes as recipes · prompts · guardrail capability + row ·
annotations · compact · action-item todo. DC-04 (~4): TTS route · VAD ·
call mode · walk. DC-05 (~4): subthread tool · conductor run-loop ·
notifications · walk.

## 12. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Streaming inside frozen route plans complicates fallback (which model's stream do we show if the first dies mid-turn?) | Fallback only *before* first delta; after first delta a failure is an `indeterminate` turn with a Retry verb. Same as warpdrv's behaviour, honest to the receipt. |
| Tool-call dialects: llama.cpp + small local models emit malformed JSON | The kernel already carries dialect material (`gemma4/qwen/…`) and the `llm-json` repair pattern; reuse; malformed = a `tool_requested` refusal row, not a crash. |
| Scope creep toward "warpdrv in HoldSpeak" | §4.2 is the fence; each phase is its own arc with its own charter question. |
| AGPL taint by an over-helpful worker | N5 + the clone lives only in the session scratchpad; workers get this plan, not the clone. |
| TTS weight on the hub (Kokoro ~330 MB) | Lazy download on first `/call`, egress-badged as a model fetch; never on install. |
| People hard boundary vs. a chatty model | `people.*` results marked `sensitive`; the assembler refuses to put them into a cloud-scoped route (existing refusal), the guardrail seed flags it, the badge shows it. |
| The web-unit baseline blind spot (six inherited vitest names) | The DC-01 close story ships `web-inherited-baseline.txt` (handover §3.D). |

## 13. Definition of done (DC-01)

- All §9 F1–F7, N1–N5 proven with evidence files; real-metal walk on `.43`
  recorded; shots at both widths cross-read; counsel design-beat before
  build and close counsel with zero must-fix; `chat.ts` localStorage
  threads imported and the old module deleted; README/entry docs touched;
  no file in the diff derives from the warpdrv clone.

## 14. Open questions for the owner (resolve at charter)

1. **Where does the chat live on Tuesday?** A thread window on the Desk
   (this plan) vs. a persistent right-hand "wing" (POSITIONING's "agent
   chat as wings"). Recommendation: window first; a pinned wing is a
   layout verb later.
2. **Yolo default for `effect_proposal` tools in chat?** The open-throttle
   ruling says yes; the People boundary says the ledger-touching effects
   still get the receipt row *before* the model continues. Confirm.
3. **DC order.** 01 → 02 is fixed. Then 03 (practice) or 04 (call)? For a
   manager on the move the Call may outrank modes/guardrails.
4. **Kokoro server-side (B) or in-browser (A)?** Plan recommends B.
5. **Do you want any external MCP server in the thread on day one?** If
   no, the MCP client stays parked and DC-02 stays small.

## 15. Appendix A — what warpdrv does that we are *not* copying, and why it's fine

warpdrv is a superb llama.cpp workbench with a chat on top. Its
irreducible chat core is ~7.3k LOC (`packages/bridge`) plus ~15k of React
thread/composer/tool-renderer code, backed by 27 SQLite tables. Of that
core, the parts with no HoldSpeak equivalent are the thread/message
persistence (≈2.5k LOC there; ≈600 here because the kernel owns tool
calls and receipts), the stream reader (≈300), and the recursive pass loop
(≈1.7k there; ≈400 here because policy, admission, and receipts are the
kernel's). The 17 tool renderers are coder-tool renderers; ours are desk-
kind renderers we already draw. The applet/event-bus plugin system
(`realmcore`, ≈1.4k) is warpdrv's extension seam; ours is the verb
registry + the pullout protocol. Nothing in this plan requires reading
warpdrv's source again.

## 16. Appendix B — honest credit

The *shape* — message-part union, branch-by-parent, three-tier approval
resolved per thread, guardrail-as-a-second-model, annotations queued into
the next turn, block-then-background subthreads, a status line the model
can set — is warpdrv's (mikjee, AGPL-3.0). This plan re-implements those
ideas against HoldSpeak's own Apache-2.0 machinery and records the
influence here so the credit is not lost when the code never resembles
theirs.

## 17. What DC-01 actually shipped vs the plan

Phase 151 (8 stories) implemented the DC-01 slice. Deltas from this plan:

- **No file attachments.** The composer accepts `@`-references to desk
  objects; file upload is deferred to DC-02.
- **No SSE endpoint.** Streaming uses the existing WebSocket bus
  (`thread_turn_started`, `thread_delta`, `thread_turn_done` frames),
  not the Server-Sent Events fan-out the plan's `§6.3` sketched.
- **`recipe.chat` retired, not removed.** The MCP tool still exists but
  returns a structured retirement error directing callers to `chat.turn`.
  The HTTP route redirects to the Thread surface.
- **`execute_stream` lives on the coordinator.** The streaming loop is
  a method on `ThreadService`, not a standalone executor, because the
  coordinator already owns admission and the bus broadcast.
- **Four glass-found defects fixed in-round.** CRASHED detection
  threshold (10 s), branch sibling ordering (newest-first), reconnect
  reconciliation (refetch on bus reconnect), and FTS trigger exclusion
  of deleted messages.
