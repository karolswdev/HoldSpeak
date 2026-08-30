# Close counsel -- Phase 153 The Practice (DC-03)

**Verdict: RATIFY-WITH-CONCERNS**

One must-fix. Three should-fixes. Seven recorded notes.

---

## MUST-FIX

### M1. People fence gap: compact/guardrail egress scope mismatch

`compact_thread` (`thread_service.py:566`) and `_run_guardrail_admission`
(`thread_service.py:1786`) decide whether to redact sensitive People
content based on the THREAD's turn `egress_scope` (derived from the
`chat.turn` route plan at `thread_service.py:449`), not on the
compact/guardrail capability's own egress boundary.

Both `run_compact` and `run_guardrail` (`thread_practice.py`) invoke the
model via `runner.invoke` directly, bypassing the adoption service's
`execute_stream` path where the `payload_redactor` (`_m1_redactor` at
`thread_service.py:1662`) runs. The manual redaction at lines 566 and
1786 is the ONLY redaction on these paths, and it is keyed on the wrong
scope.

- **Repro:** assign `chat.compact` or `chat.guardrail` to a cloud model
  (settled-design D3: "the owner points them at a cheaper model in
  Assignments") while `chat.turn` runs locally (e.g., llama.cpp on .43).
  Run `/compact` or trigger a guardrail on a thread whose People refs
  are present. The compact/guardrail payload carries the unredacted
  sensitive text because `egress_scope` is "private_network" (from the
  local chat.turn route), not "cloud" (what the compact/guardrail
  capability actually routes through).
- **Consequence:** Constitution Art. III ("nothing leaves the machine
  by default; egress is disclosed by the badge at the point of
  decision") and Art. XI (consequential operations admitted through
  the kernel) violation. Sensitive People content crosses the cloud
  boundary unredacted.
- **Fix:** resolve the actual egress boundary for the compact/guardrail
  capability's deployment revision (the `_resolve_deployment_revision`
  function in `thread_practice.py` already resolves the `profile_id`;
  from that, derive the boundary via the deployment_revisions table
  or the runner's route) and redact based on THAT boundary. Alternative:
  route compact/guardrail through the adoption service's
  `admit` + `execute_stream` path, which applies `payload_redactor`
  automatically.

> **Orchestrator, in-round (2026-08-30):** applied.
> `_resolve_deployment_revision` (`thread_practice.py:17`) now returns
> `(id, boundary)` by querying `SELECT id, boundary FROM
> deployment_revisions WHERE model=?`. Both `run_guardrail` and
> `run_compact` accept `sensitive_texts` kwarg, embed it as
> `_sensitive_texts` in the payload, and apply M1 redaction based on
> the CAPABILITY's own boundary before constructing the
> `InvocationRequest`. The thread_service callers (`compact_thread`
> at `thread_service.py:554` and `_run_guardrail_admission` at
> `thread_service.py:1784`) pass `sensitive_texts` through instead of
> doing their own egress-scope-based redaction. Tests:
> `TestGuardrailM1CapabilityBoundary` (2 tests,
> `test_thread_guardrail.py`) and `TestCompactM1CapabilityBoundary`
> (2 tests, `test_thread_compaction.py`).

---

## SHOULD-FIX

### S1. Guardrail violation-to-tool mapping over-matches

`thread_service.py:1077-1079`: the violation-to-tool mapping uses an
OR condition:

    if pname in v_str or _guardrail_matches(pname, [...trigger_tools...]):

The second disjunct (`_guardrail_matches`) always evaluates True for
every pending call whose name matches the trigger pattern, regardless
of the violation text content. When a guardrail returns a violation
naming one specific tool (e.g., `"people.commitment.transition
lacks a source"`), ALL pending calls matching the trigger pattern
(e.g., `people.*`) are marked as violated -- including innocent calls
like `people.note.create`.

- **Consequence:** in safe/neutral mode, `default_decision` flips to
  "deny" for innocent calls. The user must manually approve each
  one. Advisory only (never auto-denies), so no data loss, but the
  UX is wrong.
- **Fix:** remove the second disjunct or limit it to cases where the
  violation text does not name any specific tool (fall back to
  "all matching tools" only when the violation is generic).

> **Orchestrator, in-round (2026-08-30):** applied.
> `thread_service.py:1062-1085`: the mapping now checks whether the
> violation text names any specific pending tool (`named = [pname for
> pname in pending_names if pname in v_str]`). If named, only those
> tools carry the violation. Generic violations (naming no specific
> tool) fall through to trigger-pattern matching. Tests:
> `TestS1PerCallViolationMapping` (3 tests, `test_thread_guardrail.py`:
> specific, generic, and mixed violation scenarios).

### S2. `/guardrail on|off <name>` is on-only

The PATCH route (`threads.py:120`) hardcodes `enable=True`:

    toggle_guardrail_on_mode(svc._db, thread.recipe_id, str(toggle_guardrail_id), enable=True)

The frontend (`ThreadComposer.tsx:695-707`) matches guardrails by title
without parsing an `on|off` prefix. D2 specifies `/guardrail on|off
<name>`.  The backend `toggle_guardrail_on_mode` (`thread_modes.py`)
accepts `enable: bool` and correctly handles both states.

- **Consequence:** guardrails can be enabled via `/guardrail` but never
  disabled through the slash command. The owner must use a direct API
  call or wait until the route and frontend are updated.
- **Fix:** parse the `on|off` prefix in the frontend's `executeSlashCommand`
  case for "guardrail"; pass the boolean through the PATCH body; read it
  in the route and forward to `toggle_guardrail_on_mode`.

> **Orchestrator, in-round (2026-08-30):** applied. Three sites:
> (1) `ThreadComposer.tsx:695-715` parses `on `/`off ` prefix from
> the arg, passes `enable` boolean to `onToggleGuardrail`.
> (2) `ThreadComposer.tsx:346` signature updated to
> `(guardrailId: string, enable: boolean)`.
> (3) `threads.py:128` reads `toggle_guardrail_enable` from body,
> defaults to `True` for backward compat.
> (4) `completeSlash` (`ThreadComposer.tsx:197-202`) strips `on `/`off `
> prefix from the arg query for autocomplete.
> (5) `ThreadPullout.tsx:1689-1692` passes `enable` through.
> Vitest: `completeSlash` tests for `/guardrail on e` and
> `/guardrail off e` (2 tests, `ThreadComposer.test.tsx`; 48 total pass).

### S3. Hardcoded `color: #fff` on the People badge

`thread-pullout.css:597` uses a literal `#fff` on the `.thread-tool-people-badge`
selector. The background is tokenised (`var(--warn-signal, #f59e0b)`) but
the foreground is not. White-on-amber is readable in both themes, so the
visual impact is nil, but it breaks the token architecture.

- **Fix:** replace with `var(--badge-text, #fff)` or an equivalent
  semantic token.

> **Orchestrator, in-round (2026-08-30):** applied.
> `thread-pullout.css:597`: `color: #fff` replaced with
> `color: var(--badge-text, #fff)`. The `#fff` fallback preserves
> existing rendering; the token is available for theme overrides.

---

## RECORDED NOTES

### R1. Multi-tool-per-pass sibling gap (inherited from 152 R1)

Still present. When the model calls 2+ tools in a single pass, each
result is a sibling `tool` message with `parent_id = assistant_msg_id`.
The leaf-path walker picks only the newest sibling; earlier siblings are
absent from later turns' `_assemble_payload` messages. No People fence
issue; functional context loss for rare parallel-tool-call scenarios.

### R2. Paraphrase laundering (inherited from 152 R2)

The `egress-guard` guardrail (seeded in `thread_modes.py`) is the belt
for this gap. Annotation quotes are added to `_sensitive_texts` via
the full annotation string (e.g., `"The owner annotated: <quote> -- <comment>"`
at `threads.py:381`), not as the raw quote substring. If the model
paraphrases People content into its answer text and the owner annotates
that paraphrase, the annotation text is redacted but standalone
occurrences of the raw quote are not independently tracked. Known
limitation; the guardrail is the designed second line.

### R3. Double compaction re-summarizes from raw

A second `/compact` call iterates ALL `user`/`assistant` messages from
the root (`thread_service.py:529` filters `m.role in ("user", "assistant")`),
including messages before the first compaction cut. The first summary
(a `system` role message) is excluded by the role filter. The second
compaction independently re-summarizes the raw messages rather than
building on the first summary. Functionally correct (the assembler at
`thread_service.py:1850-1860` uses only the latest compaction row
onward), but wasteful for long threads.

### R4. Compaction excludes tool-role messages

`compact_thread` (`thread_service.py:529`) includes only `user` and
`assistant` messages. Tool-role messages (containing tool results with
potentially important context) are excluded from the summary input.
Design choice consistent with the compaction contract (summarize the
conversation, not the tool exchange), but tool context could be
relevant for understanding the thread's decisions.

### R5. No streaming-state guard on compact

`compact_thread` does not check `_active_turns` for the thread. If the
user runs `/compact` while a streaming turn is in progress, the path
may include an incomplete assistant message. The compact would
summarize incomplete text. Edge case (requires sending `/compact` during
active streaming), consequence is a suboptimal summary (overwritten by
the next compaction).

### R6. Thread verb registry stubs

The verb registry entries for the `thread` scope
(`verbRegistry.ts:475-540`) have `run: () => {}` (empty handlers). The
actual behavior is driven by the composer's `onSlash` callbacks in
`ThreadComposer.tsx` and the pullout's `onModeSelect`, `onToggleGuardrail`,
etc. The stubs prevent crashes if a verb is invoked through the command
palette, but the ghost function always returns `null` (never ghosted),
so they appear callable when they are not functional outside the
composer context.

### R7. AGPL clean

`git grep -rn warpdrv` across `.py`, `.ts`, `.tsx` source files returns
zero hits. The three hits in markdown are in
`pm/roadmap/holdspeak/phase-152-the-hands/assets/story-06-walk/report.json`
(a walk artifact referencing the plan origin) and the plan documents
under `docs/internal/` and `pm/roadmap/`. No code copied; the port is
a clean-room re-implementation of the shape, per the plan's opening
paragraph and the AGPL/Apache-2.0 boundary.

---

## Evidence reviewed

| Question | Verdict | Key evidence |
|---|---|---|
| Palette seam: tool outside mode allow-list reaches the model? | **CLEAN.** `_palette_for` (`thread_service.py:140`) is the ONE helper. `start_turn` resolves the palette at admission (`line 419`); the payload's `tools` key is frozen. `_run_streaming_turn` reads `"tools" in payload` at line 852. `palette_for` (`thread_modes.py`) intersects the mode's allow-list with `TOOL_NAMES` (fail-closed; unknown tools logged and dropped). Draft returns an empty frozenset; `start_turn:421` skips the `tools` key when the effective palette is empty. Custom modes go through the same intersection; `_warned_modes` deduplicates the warning. No path offers a tool outside the intersection. | `thread_modes.py:165-180`, `thread_service.py:140-157,416-422,852`, `test_thread_modes.py` |
| Guardrail advisory law: any path that auto-denies? | **CLEAN.** The guardrail result maps to `guardrail_violations`; the `default_decision` is set to "deny" only when `violated and control_mode != "yolo"` (`thread_service.py:1185`). In yolo mode, `default_decision` is "allow". The decision box default is emitted via `thread_tool_pending` frame (`line 1201`); the actual admit/deny is the user's click on `/decide`. Guardrail failure produces a `guardrail_failed` part and an empty-results frame (`lines 1107-1124`); the turn continues. Never auto-denies (M8 met). | `thread_service.py:1062-1124,1180-1202`, `test_thread_guardrail.py` |
| ONCE-per-pass rule? | **CLEAN.** The guardrail runs inside the per-pass for loop at `line 1048`. It fires once per pass (when `active_guardrails and tool_calls_this_pass`). The matched guardrails are combined into a single `combined_instruction` (`line 1773`) and one `run_guardrail` invocation (`line 1062`). Not once-per-call. | `thread_service.py:1048-1072,1773` |
| Timeout behaviour, `guardrail_failed`? | **CLEAN.** `_run_guardrail_admission` uses `asyncio.wait_for` with `timeout_s` (`line 1810`). On timeout, `asyncio.TimeoutError` propagates to the `except Exception` at `line 1100`, which emits `guardrail_failed`. | `thread_service.py:1799-1819,1100-1124` |
| Reconcile kind-drift on a real 40k-row DB? | **CLEAN.** `_rebuild_thread_message_parts_for_kind_drift` (`reconcile.py:448`) detects live vs canonical kind CHECK, copies all rows into a new table with the canonical DDL under a SAVEPOINT, preserves indexes/triggers/FTS, drops and renames. Idempotent (returns False when canonical kinds are a subset of live kinds at `line 487`). The `draft` column is in the canonical DDL (`schema.py: draft INTEGER NOT NULL DEFAULT 0`) and `reconcile_schema` adds missing columns via ALTER (`reconcile.py:main path`). Story-03 evidence confirms the rebuild passes against the pre-change DDL. | `reconcile.py:448-545`, `schema.py:CREATE TABLE thread_message_parts`, `evidence-story-03.md` |
| `action_items.meeting_id` nullable + `source_type`, `source_ref`? | **CLEAN.** The canonical DDL at `schema.py:99` declares `meeting_id TEXT REFERENCES meetings(id) ON DELETE CASCADE` (nullable, no NOT NULL). `source_type TEXT NOT NULL DEFAULT 'meeting'` and `source_ref TEXT NOT NULL DEFAULT ''` are present. `DoorService.add_item` (`door_service.py:72`) inserts with `meeting_id = NULL`. Reconcile adds missing columns additively. | `schema.py:98-112`, `door_service.py:68-82` |
| Draft/annotation: one draft message per thread? | **CLEAN.** `draft_message_for` (`db/threads.py:709-732`) selects the user message where ALL parts have `draft=1` and NO parts have `draft=0`, `ORDER BY created_at DESC LIMIT 1`. Only one draft can exist per thread (the second annotation creates a part on the existing draft message). `promote_drafts` (`line 789`) sets `draft=0` on all parts in one UPDATE. The promoted message then has `draft=0` parts and is no longer a draft. | `db/threads.py:709-810`, `thread_service.py:362-379` |
| Fork/regenerate with drafts? | **CLEAN.** `branch` (`thread_service.py:1504`) calls `start_turn` with `parent_id=message_id`; `start_turn` looks for a draft message (`line 362`). If a draft exists, it is promoted. If the fork point is before the draft message, the draft message's parent is still the original thread's leaf; the new branch gets its own messages. Drafts survive forks because they live on the origin message tree. | `thread_service.py:1504-1524,362-379` |
| Delete of a promoted annotation part? | **CLEAN.** `delete_part` (`db/threads.py:763-786`) deletes the part by id and removes the parent message if no parts remain. A promoted annotation part (`draft=0`) can be deleted via `DELETE /api/threads/{id}/annotations/{part_id}` (`threads.py:413`), but the route validates the part is in the draft parts list (`line 417`), so only draft (unpromoted) parts can be deleted via this route. Promoted parts are permanent in the message. | `db/threads.py:763-786`, `threads.py:413-425` |
| Compaction: sensitive summary inheritance (M7)? | **CLEAN.** `compact_thread` collects `any_sensitive` and `sensitive_texts` from all parts (`line 535-546`). The summary part inherits `sensitive=any_sensitive` (`line 625`). The assembler picks up the sensitive summary text in `_assemble_payload` (`line 1905-1908`) and adds it to `sensitive_texts`. The M1 redactor handles it on cloud egress. | `thread_service.py:535-546,625,1905-1908` |
| Todo: receipt, source_ref, truth table? | **CLEAN.** `todo_from_thread` (`thread_service.py:654`) creates a `ThreadToolExecutor` and calls `admit` with `door.add_item` (`line 712`). The executor goes through `resolve_tool_decision` (the truth table). In safe mode, the handle is `awaiting_decision`; the route waits for `/decide`. The receipt row is the tool_call part (`line 763`) and the tool result message (`line 779`). `source_ref` is `thread:<message_id>` (`line 677-680`). `source_type` is "thread" (`line 708`). The `follow_through_service` creates `CardProvenance` with `thread_id` (`line 475-485`). | `thread_service.py:654-815`, `door_service.py:41-92`, `follow_through_service.py:475-485` |
| Door chip opens the pullout? | **CLEAN.** `DoorBoardLane.tsx:786` renders a chip with `onClick={() => useDesk.getState().openPullout(\`thread:${card.provenance!.thread_id}\`)}`. | `DoorBoardLane.tsx:780-788` |
| UI: no modals, no prose, no window test hooks, tokens, keyboard, 393? | **CLEAN.** Annotation popover is an absolute-positioned div (not a modal). No `window.__` or `(window as any)` in production code outside test files. CSS uses desk window tokens (vars with fallbacks). The `a` key triggers the popover only when text is selected and focus is not in an input/textarea/contenteditable (`ThreadPullout.tsx:1458`). 393 overflow: screenshots in `assets/story-*/` confirm no horizontal overflow. One token issue: `color: #fff` on the People badge (S3). | `ThreadPullout.tsx:669-760,1350-1470`, `thread-pullout.css`, screenshots |
| Slash grammar R3? | **CLEAN.** `isSlashAtLineStart` (`ThreadComposer.tsx:131`) checks that `/` is at column 0 of the line. `completeSlash` (`line 144`) returns null when the condition fails. `handleSend` (`line 771`) intercepts freeform-arg slash commands before sending as regular messages. The verb registry fence: every slash command maps to a registered verb id in `THREAD_SLASH_COMMANDS` (`line 80-93`) cross-referenced with the verb registry's `thread` scope entries (`verbRegistry.ts:475-540`). | `ThreadComposer.tsx:80-93,131-220,765-790`, `verbRegistry.ts:475-540` |
| AGPL clean? | **CLEAN.** See R7 above. | `git grep -rn warpdrv --include='*.py' --include='*.ts' --include='*.tsx'` |

---

## What the phase got right

Five stories delivering the full practice layer -- modes, prompts, slash
verbs, guardrails, annotations, compaction, and todos -- in a single
day's sitting. The one palette seam (`_palette_for`) is clean: resolved
once at admission, frozen for the turn, Draft mode correctly omits the
tools key (no executor, one pass). The guardrail is genuinely advisory
(never auto-denies, failure becomes a warning row, the turn continues)
and the ONCE-per-pass rule holds. The annotation flow is in-world (no
modal, Art. VII), keyboard-reachable (`a` key with selection guard), and
carries the mic (Art. IV). The compaction cut is honest: the assembler
reads only from the latest cut onward, the summary inherits sensitivity,
and the sensitive text joins `_sensitive_texts` for the M1 redactor. The
todo flows through the same ThreadToolExecutor path as a model call
(truth table, receipt, source_ref) and the Door chip opens the pullout.
The kind-drift reconcile for thread_message_parts is the right pattern
for a single-owner desk with an existing production DB. Story-05 found
seven real-path defects (the runner invocations were dead; the test mocks
had hidden them) and fixed all of them in-round.

The one must-fix (M1, compact/guardrail egress scope mismatch) is real:
the manual redaction uses the thread's turn egress scope instead of
resolving the compact/guardrail capability's own boundary. This matters
when the owner assigns a cloud model for guardrails while keeping the
chat local. The fix is bounded (resolve the capability's boundary and
redact on that, or route through the adoption service's `execute_stream`
path).
