# HS-118-05 — Voice drawer resolution

- **Project:** holdspeak
- **Phase:** 118
- **Status:** done
- **Depends on:** HS-118-01, HS-118-03, HS-118-04
- **Unblocks:** --
- **Owner:** unassigned

## The thesis (the bar)

The typed `@`-reference path (HS-118-04) gives the user inline
autocomplete. But voice is a system primitive — every input gets a
mic (Article IV), and the user should be able to speak naturally:
"summarize the Monday standup and compare with what we discussed in
research." The system must understand that "the Monday standup" and
"research" map to zones named "Monday Standup" and "Research Notes"
— even though the user didn't say the exact zone name.

Substring matching (HS-118-04's `resolveDrawerNames`) handles the
trivial cases: exact zone names appearing verbatim in speech. But
natural speech paraphrases, abbreviates, and contextualizes.
"The standup" is not "Monday Standup." "That research stuff" is not
"Research Notes." A dumb scanner can't bridge this gap.

The resolver is an LLM call. A small local model (e.g. a 4B
parameter model running on the user's machine) receives the zone
catalog and the user's utterance, and returns a structured JSON
object identifying which zone IDs the user referenced. The model is
configured via a **resolver profile** — a workbench-level setting
that points to an inference target. This is the same profile/target
system workbenches already use for their agent, as a separate
pointer — the resolver profile can (and typically should) be a
small, fast, local model, independent of the agent's model.

The user sees the resolved zone names as grounding chips in the
inlet tray before submitting. They can remove wrong resolutions.
This is honest: the system proposes, the user confirms by
submitting. Article V — consent is the spine.

**Articles served:** II (DeskPrimitive contract — the shared
`ResolvedRef` and zone-qualified refs are the primitive address
contract), IV (voice as input — every text input can be spoken
into), V (consent — resolved refs are proposals; the user confirms
by submitting or removes wrong ones), VI (honest by construction —
resolution is visible and removable; operational failures are
reported, never silent), XI (kernel admission — the resolver model
call is a consequential inference operation with a terminal
receipt), III (honest egress — the resolver profile's egress
boundary is disclosed before and after the call).

## The two-tier resolution model

Voice resolution has two tiers:

1. **Fast path (client-side, instant).** The existing
   `resolveDrawerNames()` substring scanner from HS-118-04. Runs
   in the browser, zero latency, zero cost. Handles exact zone
   names appearing verbatim in the transcript.

2. **Smart path (server-side, LLM).** An inference call to the
   configured resolver profile. Handles paraphrasing, abbreviation,
   contextual references. Returns structured JSON with zone IDs.

**Both tiers run concurrently when a resolver profile is
configured.** The fast path adds chips immediately for
responsiveness. The smart path fires in parallel and merges
additional (non-duplicate) refs when it returns. This avoids the
failure mode where an exact match for one zone causes the system to
skip the model and miss a paraphrased reference to another zone.

If no resolver profile is configured, only the fast path runs
(pure substring matching, no LLM).

## The resolver profile

A new field on the workbench (not per-item, not per-run):

```
Workbench.resolver_profile_id: Optional[str]
```

Points to an inference target profile (the same `profile` objects
that workbenches already use for their agent runs). The profile
determines which model handles resolution — typically a small,
fast, local model (4B parameter, same-device boundary). Separate
from `profile_id` (the agent's model) because the resolver needs
low latency and same-device egress, while the agent may use a
larger or remote model.

If null, only the fast path runs (pure substring matching).

The setting appears in the workbench config panel alongside the
existing AGENT and RUNS ON pickers:

```
RESOLVES WITH    [Local 4B ▾]    ● LOCAL
```

Shows the profile name, an egress lamp (same `LampGadget` pattern),
and a dropdown to select from available profiles. "None" disables
the smart path.

**Pre-call egress disclosure.** When a resolver profile is
configured, the inlet shows the profile's egress boundary
persistently — a small `EgressChip` near the mic or in the tray
area. This tells the user "your voice will be processed by [LOCAL /
LAN / CLOUD]" BEFORE they speak, not only after the call returns.
Article III requires disclosure at the decision boundary, not
retroactively.

## The resolver protocol

The model receives the zone catalog as structured data with stable
IDs, and returns zone IDs — not display names.

### Prompt

```python
RESOLVER_PROMPT = """You are a reference resolver. The user has
zones (directories) on their desk. Given the user's spoken
instruction, identify which zones they are referring to.

ZONES (JSON):
{zone_catalog_json}

USER SAID (verbatim transcript):
{transcript_json}

Return ONLY a JSON object with this exact shape:
{{"zone_ids": ["dir_abc", "dir_def"]}}

Rules:
- Return only zone IDs from the ZONES list above.
- If no zones were referenced, return {{"zone_ids": []}}.
- Do not explain. Do not add commentary.
- Do not invent zone IDs not present in the ZONES list.
- Maximum {max_refs} zone IDs.

Examples:
ZONES: [{{"id":"dir_1","name":"Monday Standup","items":3}},
        {{"id":"dir_2","name":"Research Notes","items":5}}]
USER: "summarize the standup and compare with research"
Output: {{"zone_ids":["dir_1","dir_2"]}}

ZONES: [{{"id":"dir_3","name":"Inbox","items":2}},
        {{"id":"dir_4","name":"Archive","items":10}}]
USER: "what did I do today"
Output: {{"zone_ids":[]}}
"""
```

Key design decisions:
- **Zone catalog is JSON data, not interpolated prose.** Prevents
  prompt injection from zone names containing instructions.
- **Transcript is JSON-quoted.** Same reason.
- **Model returns IDs, not names.** IDs are stable, unambiguous,
  and trivially validated by set membership. No casing, Unicode, or
  whitespace issues.
- **Max refs matches `GROUNDING_MAX_REFS = 16`.**
- **Small output-token budget** (e.g. 128 tokens) — the response
  is a small JSON object, not prose.

### Response parsing

The server parses the model response:
1. Extract JSON from the response (tolerate markdown fences and
   leading/trailing whitespace).
2. Validate shape: must have a `zone_ids` array of strings.
3. Validate each ID: must be present in the catalog snapshot used
   for this request. Drop unknown IDs silently (hallucinations).
4. Deduplicate.
5. Mint `ResolvedRef` objects from validated IDs.

If the response is not parseable JSON or has the wrong shape,
the **retry chain** fires (see below). Only after all retries are
exhausted is the failure surfaced to the user.

### Retry chain with escalating prompts

Small local models are unreliable. A 4B model may emit markdown
fences, commentary, malformed JSON, or ignore instructions on the
first attempt. The resolver retries with progressively stricter
prompts before giving up.

The retry chain is a list of prompt templates stored in
`holdspeak/voice_resolver.py` as a module-level constant. Each
entry is a prompt that receives the original zone catalog, the
transcript, AND the previous failed response. The chain is easily
editable — adding, removing, or reordering entries is a one-line
change.

```python
RESOLVER_RETRY_CHAIN = [
    # Attempt 1: standard prompt (already defined above)
    # No previous_response context.

    # Attempt 2: correction prompt
    """Your previous response was invalid:
>>> {previous_response} <<<

I need ONLY a JSON object with this exact shape:
{{"zone_ids": ["dir_xxx", "dir_yyy"]}}

No explanation. No markdown. No commentary. Just the JSON object.
Here are the valid zone IDs: {valid_ids_json}
The user said: {transcript_json}
Which zones did they reference?""",

    # Attempt 3: minimal forced-choice prompt
    """Respond with EXACTLY one line of JSON. No other text.
Valid IDs: {valid_ids_csv}
User: {transcript_json}
Output: """,
]
```

**Behavior:**

| Attempt | Prompt | Input |
|---------|--------|-------|
| 1 | Standard resolver prompt | catalog + transcript |
| 2 | Correction prompt | catalog + transcript + attempt 1's raw response |
| 3 | Minimal forced-choice | valid IDs as CSV + transcript |

Each attempt:
- Uses the same model call parameters (same profile, same token
  budget).
- Has its own timeout (5s per attempt, not cumulative).
- Parses the response with the same validation pipeline.
- If valid: stop, return refs. Success.
- If invalid: feed the raw response to the next prompt as
  `{previous_response}`.

After all attempts are exhausted:
- **This is an operational failure.** Surface it to the user (see
  error handling table: `RESOLVER ERROR` chip).
- Log the full retry chain (all prompts and responses) for
  debugging.
- The retry count and responses are included in the kernel
  terminal receipt.

**Invalid zone IDs are NOT a retry trigger.** If the model returns
valid JSON with the right shape but contains unknown IDs, those IDs
are dropped silently and the valid ones are returned. Only
structural failures (not-JSON, wrong shape) trigger retries.

**Editability.** The retry chain is a plain Python list of format
strings. Operators or developers can tune the prompts, add more
aggressive attempts, or reduce the chain to a single attempt. No
configuration UI — this is infrastructure, not user-facing.

## The resolver API

Workbench-scoped endpoint — the client does not supply a profile
ID:

```
POST /api/workbenches/{workbench_id}/voice/resolve
Body: {
  "transcript": "summarize the Monday standup...",
  "request_id": "req_abc123"
}
Response: {
  "refs": [
    {"name": "Monday Standup", "id": "dir_abc",
     "ref": "zone:dir_abc", "kind": "zone"}
  ],
  "egress": {"boundary": "same_device", "model": "..."},
  "request_id": "req_abc123"
}
```

The endpoint:
1. Authenticates the caller. Loads the workbench record.
2. Reads `resolver_profile_id` from the workbench. If null,
   returns 409 `resolver_not_configured`.
3. Checks target readiness. If unavailable, returns 503
   `resolver_unavailable`.
4. Loads the zone catalog from the DB (names, IDs, member counts).
5. Builds the resolver prompt.
6. Admits the inference operation through the kernel. The kernel
   authenticates the owner and derives authority (Article XI.3 —
   the client supplies neither profile_id nor authority).
7. Calls the model via the resolver profile. Timeout: 5 seconds
   (configurable). Output token budget: 128.
8. Parses and validates the response.
9. Returns resolved refs + egress boundary + request_id echo.
10. Terminal receipt on the kernel operation (success, refusal,
    timeout, parse failure — each is a named terminal state).

## The canonical data model

The user's spoken words are the instruction. They are never mutated,
rewritten, or partially deleted. The flow:

1. User speaks into the inlet mic.
2. Whisper returns the raw transcript.
3. **Fast path (immediate):** `resolveDrawerNames(transcript, zones)`
   runs client-side. Matching refs are added to the tray instantly.
4. **Smart path (concurrent, if resolver profile is set):** call
   `POST /api/workbenches/{id}/voice/resolve`. Assign a generation
   ID matching the current inlet draft. Show resolving indicator.
5. When the smart path responds: validate the generation ID matches
   the current draft. If it does, merge non-duplicate refs into the
   tray. If the draft has been submitted, cleared, or reset since
   the request was made, discard the response.
6. The **full original transcript** is inserted into the inlet text
   field in both cases. The user's words are preserved exactly as
   spoken.
7. On submit, the item body contains the full transcript. The
   grounding contains all resolved refs (fast + smart). The agent
   receives both.

## Error handling (Article VI)

Operational failures are NEVER silent. They are visually distinct
from a legitimate "no zones referenced" result:

| Condition | Tray behavior |
|-----------|---------------|
| No resolver profile configured | No indicator. Fast path only. |
| Resolver target unavailable | Tray shows `RESOLVER UNAVAILABLE` chip (muted, non-blocking). Retry affordance. |
| Model timeout (>5s) | Tray shows `RESOLVER TIMEOUT` chip. Retry affordance. |
| Malformed model response | Tray shows `RESOLVER ERROR` chip. No retry (model can't handle this catalog). |
| Kernel refusal | Tray shows `RESOLVER REFUSED` chip. |
| Successful response, no refs | No indicator. Silence is correct — the model found nothing. |
| Successful response, refs found | Chips animate in. |

Error chips are compact, non-modal, use `--text-faint` color, and
disappear when the inlet is cleared or a new dictation starts. They
do not block submit — the user can proceed with fast-path-only
grounding or no grounding.

## Async race and cancellation semantics

Each dictation-to-resolution cycle is tagged with a **generation
ID** (a monotonically increasing counter on the inlet component).

- **Submit before response:** submitting the inlet increments the
  generation ID and cancels/discards any pending resolution. The
  item is created with whatever grounding was in the tray at submit
  time (fast-path refs only if the smart path hadn't returned yet).
  No late mutation of submitted items.
- **Second dictation:** a new dictation increments the generation
  ID. The first smart-path response (if still pending) is discarded
  when it arrives with a stale generation. The second dictation's
  fast + smart paths run fresh.
- **Chip removal during pending:** removing a chip from the tray
  does not cancel the pending request, but the deduplication rule
  prevents the smart path from re-adding a removed ref (the
  generation matches, but the ref is checked against current tray
  state).
- **Workbench close / profile change:** closing the window or
  changing the resolver profile cancels pending requests
  (generation ID becomes stale).
- **Out-of-order responses:** generation ID comparison ensures only
  the current draft's responses are applied.

## Operational bounds

| Bound | Limit | Behavior when exceeded |
|-------|-------|------------------------|
| Empty zone catalog | -- | Skip model call, return no refs |
| Transcript length | 2048 chars | Truncate at word boundary before sending |
| Zone catalog size | 256 zones | Send first 256 by recency; log warning |
| Model timeout | 5 seconds per attempt | Cancel attempt, try next in chain |
| Retry attempts | 3 (1 standard + 2 escalating) | After all exhausted: `RESOLVER ERROR` |
| Total wall-clock budget | 15 seconds (3 × 5s) | Worst case; early success short-circuits |
| Output tokens | 128 per attempt | Model generation budget |
| Concurrent requests per inlet | 1 | New request cancels prior pending |
| Rate limit | 1 request per 2 seconds per workbench | Debounce rapid speech chunks |

No persistent caching. A short-lived in-memory cache (keyed by
profile ID + catalog revision + transcript hash, TTL 60s) is
optional and safe. No cross-workbench or post-rename reuse.

## Deliverables

1. **Resolver profile field.** Add `resolver_profile_id TEXT` to
   the `workbenches` table (nullable, default NULL). Add to
   `WorkbenchRecord`, `WorkbenchDetail`, and the update API. Add a
   RESOLVES WITH picker to the workbench config panel (same pattern
   as the existing RUNS ON picker, with egress lamp).

2. **Pre-call egress disclosure.** When resolver profile is set,
   show a persistent `EgressChip` in the inlet area indicating the
   resolver's egress boundary. Visible before any speech occurs.

3. **Resolver module.** `holdspeak/voice_resolver.py` — prompt
   template, catalog formatting (JSON with IDs), response parsing
   (JSON extraction, shape validation, ID membership check),
   operational bounds enforcement.

4. **Resolver endpoint.** `POST /api/workbenches/{id}/voice/resolve`
   as specified. Workbench-scoped. Kernel-admitted (caller supplies
   neither profile nor authority). Named terminal receipts for all
   outcomes.

5. **Wire into the inlet's `onText` callback.**

   ```typescript
   onText={async (transcript) => {
     const zones = useDesk.getState().items.directory;
     const gen = ++generationRef.current;

     // Fast path: immediate
     const { refs: fastRefs } = resolveDrawerNames(transcript, zones);
     fastRefs.forEach(r => addGroundingRef(r));

     // Smart path: concurrent (if configured)
     if (resolverProfileId) {
       setResolving(true);
       try {
         const result = await resolveVoice(workbenchId, transcript, gen);
         if (generationRef.current === gen) {
           result.refs.forEach(r => addGroundingRef(r));
         }
       } catch (err) {
         if (generationRef.current === gen) {
           setResolverError(classifyError(err));
         }
       } finally {
         if (generationRef.current === gen) setResolving(false);
       }
     }

     setInletText(v => v ? v + " " + transcript : transcript);
   }}
   ```

6. **Resolving indicator.** While the smart path is in flight, the
   inlet shows a subtle LedMeter scanning animation on the
   grounding tray. Non-blocking — the user can type, speak more,
   or submit while resolution is pending.

7. **Visual confirmation.** When resolution (fast or smart) adds
   grounding chips, the newly added chips animate in with a brief
   `var(--accent-tint)` background flash (300ms). Under
   `prefers-reduced-motion: reduce`, the flash is suppressed.

8. **Error indicators.** Operational failures show compact,
   non-modal chips in the tray as specified in the error handling
   table. Retry affordance on timeout and unavailable states.

9. **Deduplication.** Refs already in the tray (from drops,
   @-references, fast path, or prior smart-path results) are not
   added again. Dedup by qualified ref string.

10. **Grammar intent priority.** Workbench voice grammar intents
    (run, clear done, set schedule) fire BEFORE resolution.
    Resolution only runs on dictation-fallback text.

## What NOT to do

- Do NOT strip matched zone names from the transcript. The user's
  words stay intact in the input field.
- Do NOT auto-submit after resolution. The user reviews chips and
  submits explicitly.
- Do NOT call the smart path if no resolver profile is configured.
- Do NOT feed full zone contents to the resolver. IDs, names, and
  member counts only.
- Do NOT trust the model's output blindly. Every returned zone ID
  is validated against the catalog snapshot. Unknown IDs are
  dropped.
- Do NOT let a late smart-path response modify a submitted or
  cleared draft. Generation ID gating is mandatory.
- Do NOT silently swallow operational failures. A broken resolver
  must be visually distinct from "no zones referenced."
- Do NOT let the client supply the profile ID in the API request.
  The server reads it from the workbench record.

## Test plan

- `uv run pytest -q tests/ -k voice_resolve` — new backend tests:
  - Resolver prompt includes zone catalog as JSON with IDs.
  - Model returns valid zone IDs → refs resolved.
  - Model returns unknown zone ID → dropped silently.
  - Model returns empty `zone_ids` → no refs, no error.
  - Model returns malformed JSON on attempt 1 → retry with
    correction prompt including the failed response.
  - Model returns malformed JSON on all 3 attempts → named
    `RESOLVER ERROR`, full chain logged.
  - Model returns valid JSON on attempt 2 (after attempt 1 failed)
    → refs resolved, retry count in receipt.
  - Model returns valid shape but unknown IDs → IDs dropped, valid
    ones returned, no retry triggered.
  - Model timeout on attempt 1 → retry with next prompt.
  - Model timeout on all 3 attempts → `RESOLVER TIMEOUT`.
  - Resolver target unavailable → 503.
  - No resolver profile on workbench → 409.
  - Kernel admission recorded with correct kind/target.
  - Terminal receipts for success, timeout, parse failure, refusal.
  - Transcript > 2048 chars → truncated.
  - Empty zone catalog → no model call, empty refs.
  - 300 zones → first 256 sent, warning logged.
  - Rate limit: two calls within 2s → second debounced.
- `npx vitest run` — new frontend tests:
  - Fast path: exact zone name → chip added instantly, no server
    call (when no resolver profile).
  - Fast path + smart path concurrent: exact match chips appear
    immediately, smart-path chips merge after response.
  - Smart path finds refs that fast path missed → both in tray.
  - Smart path returns duplicate of fast-path ref → no second chip.
  - Submit before smart-path response → item created with
    fast-path refs only, smart-path response discarded.
  - Second dictation → first smart-path response discarded
    (generation ID mismatch).
  - Resolver error → error chip shown, not silent.
  - Resolver timeout → timeout chip shown with retry.
  - No resolver profile → no server call, no error.
  - Resolving indicator shown during smart-path flight.
  - Pre-call egress chip visible when resolver profile is set.
  - Grammar intent "run" → handled by grammar, not by resolution.
- Visual at 1440: speak natural reference ("the research stuff"),
  LedMeter scans briefly, zone chip appears, egress badge visible
  before and after call, full transcript in input.
- Visual at 393: same behavior, chips and egress badge visible.
