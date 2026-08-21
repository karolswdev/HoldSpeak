# Inference Catalog and Context Policy

**Status:** Concrete bootstrap policy for owner ruling; every local entry remains
a candidate until immutable-source, runtime-compatibility, and metal calibration
gates pass

**Date:** 2026-08-20

**Parent design:** [The Inference Instrument](inference-instrument.md)

## Decision

HoldSpeak will ship a small, opinionated catalog rather than asking an owner to
understand model hubs, quantization folklore, or context-window marketing.

The ordinary local bootstrap model-strength choices are:

* **Quick:** Qwen3.5 4B, 4-bit;
* **Balanced:** Qwen3.5 9B, 4-bit; and
* **Deep:** a qualified 27B Qwen, 4-bit.

Quick/Balanced/Deep are governed outcome labels, not universal parameter-count
aliases. Hosted and custom deployments earn those same labels independently
through their product-quality gates.

The ordinary context choices are a separate axis:

* **8K**, **16K**, and **32K**;
* **Custom** only in Details; and
* one server-computed recommendation, initially selected.

On Apple Silicon, MLX is the recommended runtime family and GGUF is an
available alternative. On Linux, GGUF through the pinned llama.cpp runtime is
the recommended family. A format is not a product experience: the card says
Quick, Balanced, or Deep first and discloses the exact runtime and artifact
underneath.

The catalog never equates a model's native context ceiling with a sensible
working context on this hardware. It recommends the largest tested context tier
that preserves OS/app headroom, satisfies the runtime lease, and meets the
experience's latency floor. Under a fixed memory budget, choosing a stronger
model can lower the recommended context.

## The bootstrap catalog

These are the exact candidates the catalog publication pipeline should attempt
to qualify first. They are not executable catalog entries until the source
commit, manifest, license, runtime revision, and calibration envelope are
frozen.

| Experience | Apple Silicon candidate | Portable GGUF candidate | Ordinary outcome |
| --- | --- | --- | --- |
| Quick | `mlx-community/Qwen3.5-4B-MLX-4bit` | `unsloth/Qwen3.5-4B-GGUF`, `Q4_K_M` | Fast interviews and short everyday Notes |
| Balanced | `mlx-community/Qwen3.5-9B-MLX-4bit` | `unsloth/Qwen3.5-9B-GGUF`, `Q4_K_M` | Strong Thought interviews and everyday writing |
| Deep | `mlx-community/Qwen3.8-27B-4bit` | `unsloth/Qwen3.5-27B-GGUF`, `Q4_K_M` until a matching Qwen3.8 artifact qualifies | Harder synthesis, coding, and research; slower |

Current upstream byte observations at the source revisions inspected on
2026-08-20 are:

| Candidate | Observed revision | Selected model bytes |
| --- | --- | ---: |
| MLX Quick | `32f3e8ecf65426fc3306969496342d504bfa13f3` | 3,034,300,695 weight bytes; 3,061,132,920 repository bytes |
| MLX Balanced | `938d8919941c6e7efd3c7150eff7fe9d12afa631` | 5,950,221,072 weight bytes; 5,977,074,591 repository bytes |
| MLX Deep | `3e6447f082e89cc7f0bc6e5441afd38dfce760ff` | 16,054,541,349 weight bytes; 16,081,490,933 repository bytes |
| GGUF Quick Q4_K_M | `e87f176479d0855a907a41277aca2f8ee7a09523` | 2,740,937,888 bytes |
| GGUF Balanced Q4_K_M | `3885219b6810b007914f3a7950a8d1b469d598a5` | 5,680,522,464 bytes |
| GGUF Deep Q4_K_M | `3221f178a6b842d04f1fb42f1c413534adcc0a6a` | 16,740,812,704 bytes |

Those observations are investigation inputs, not trusted manifests. Publication
must still pin immutable commits, every required file digest and size, runtime
compatibility, license metadata, and safe installed/peak-storage totals through
the signed-catalog process in the parent design.

The GGUF baseline is standard `Q4_K_M`, not whichever quant happens to be
newest. It is broadly understood by llama.cpp and gives us one portable quality/
size baseline. An `IQ`, `UD`, 5-bit, or 6-bit entry may later win a calibrated
revision, but it may not silently replace the baseline or reuse its receipt.

The MLX candidates are currently Qwen3.5-family conditional-generation
architectures and their published examples use `mlx-vlm`. That makes the
Thought MLX driver compatibility gate real: the existing dictation MLX adapter
is loader knowledge, not proof that these artifacts can execute through the
Thought request/result contract. Until the pinned MLX runtime passes that gate,
Models must say **Not available for Thoughts yet**, not **Ready**.

Existing configuration strings such as `Qwen3.5-8B-MLX-4bit` are migration
inputs, not catalog truth. HoldSpeak must inspect an existing artifact and bind
what it actually is; it must not manufacture a current 8B catalog entry from a
stale path label.

## Hosted bootstrap presets

Hosted presets use the same Quick/Balanced/Deep product grammar but are a
different catalog union member. They have no local artifact, quantization, or
memory recommendation.

The current OpenRouter candidates are:

| Experience | Model ID | Model-native advertised ceiling | Provider-route advertised ceiling | Adapter-proven ceiling | HoldSpeak working policy |
| --- | --- | --- | --- | --- | ---: |
| Quick | `qwen/qwen3-8b` | 32K native; YaRN extension to 131,072 | OpenRouter catalog reported 131,072 | `bounded` until exact route/template proof exists | 16,384 total tokens |
| Balanced | `qwen/qwen3.5-35b-a3b` | 262,144 | OpenRouter catalog reported 262,144 | `bounded` until exact route/template proof exists | 32,768 total tokens |
| Deep | `qwen/qwen3.8-27b` | Catalog publication must verify independently | OpenRouter catalog reported 1,000,000; its then-current top-provider descriptor reported 262,144 | `bounded` until exact route/template/extension proof exists | 32,768 total tokens |

Provider observations are frozen with descriptor revision and `observed_at`;
they are not timeless model facts. The executable ceiling is the conservative
lawful minimum of the immutable model/deployment claim, the selected provider-
route descriptor, the adapter-proven support, and HoldSpeak policy. Drift makes
the route stale/unavailable; it never triggers substitution or a larger limit.

The native ceiling is a compatibility maximum. The working policy is an exact
total request ceiling—8K = 8,192, 16K = 16,384, and 32K = 32,768—including the
output reserve and every control/template token, not an input-only allowance.
Hosted inference does not preallocate the owner's RAM, but excess
context still increases latency, cost, disclosure, and the amount of hostile
material presented to a model. Bigger is therefore not automatically better.

Every hosted ID, context claim, availability state, price/disclosure fact, and
provider adapter revision is server-owned catalog data. A missing or changed
provider model cannot be silently substituted. Custom OpenAI-compatible,
private, paired, and mesh destinations remain first-class and go through the
same deployment, planning, admission, and receipt waist.

Hosted context truth uses the parent design's `exact | bounded | unavailable`
classification. It is **bounded**, not exact, unless HoldSpeak proves the exact
provider route, tokenizer, chat serialization, extension mode, and output
contract consumed by the physical request. A provider marketing/API ceiling is
never promoted to exact token admission by itself.

## Agentic and tool-use qualification

Tool use is a separate qualification axis from Quick/Balanced/Deep. A model can
write an excellent Note and still be poor at deciding not to call a tool,
selecting the right capability, producing closed arguments, or incorporating a
tool result without inventing a second action.

Every catalog deployment therefore reports:

```text
thought_quality:      unavailable | candidate | qualified
structured_tool_use: unavailable | candidate | qualified
qualified_palette:    0 | 1 | 4 | 8 | 12
tool_eval_revision:   immutable revision or null
native_tool_dialect:  none | gemma4 | qwen | openai | granite | other-closed
```

`qualified_palette` is the largest tested server-selected palette, not
permission to discover or receive that many arbitrary operations. A deployment
that qualifies with four capabilities is never handed twelve because a prompt
happens to fit.

Until the separately ruled **Tool Capability Foundation** lands, projections
may report only `unavailable` or `candidate`, `qualified_palette` is zero, and
Models exposes no executable tool-use promise. Offline evaluation alone cannot
produce **qualified**.

### Immediate Gemma 4 candidates

Gemma 4 is a serious bootstrap challenger because Google's instruction-tuned
models advertise native system-role and function-calling support rather than
requiring tool calls to be scraped from prose.

| Candidate | Upstream architecture fact | Candidate role | Current artifact lead |
| --- | --- | --- | --- |
| Gemma 4 E2B-it | 2.3B effective / 5.1B total, 128K, native function calling | Quick and small capability-router evaluation | MLX Community text-only int4 observed at about 2.67 GB; official/community GGUF must qualify independently |
| Gemma 4 E4B-it | 4.5B effective / 8B total, 128K, native function calling | Quick/Balanced agentic challenger | Google QAT Q4_0 GGUF observed at about 5.15 GB; MLX form must qualify independently |
| Gemma 4 12B-it | 12B, 256K, native function calling | Balanced tool-bearing Thought/action candidate | Local forms require runtime, memory, and metal qualification |
| Gemma 4 26B-A4B-it | 25.2B total / 3.8B active, 256K | Deep/server agentic candidate | Resident size still follows total artifact/experts; active parameters do not make it a 4B-memory model |

The `E` and `A` labels may never become misleading product memory copy. E2B's
effective parameter count does not erase its embedding weights; 26B-A4B's
active count does not erase resident expert memory. Cards use measured resident
and working bytes, not the attractive smaller number.

Gemma 4 does not displace Qwen by declaration. It enters the same immutable-
artifact, runtime, quality, context, and hardware qualification campaign. The
first local Quick/Balanced winner may differ by operation and hardware only when
an explicit job route selects that frozen deployment before admission; an
in-flight operation is never silently retargeted.

### Other tool-oriented candidates

The evaluation pool should also include:

* Qwen3.5 4B and 9B, whose official family evaluation includes agent/tool-use
  benchmarks and which are already local bootstrap candidates;
* IBM Granite 4.0 1B and H-Tiny, whose official cards define OpenAI-style tool
  schemas and publish tool-calling evaluations; and
* Microsoft Phi-4-mini-instruct only if the pinned runtime can execute its
  function-calling format without `trust_remote_code` or repository plugins.

Model-card support is admission to the evaluation pool, not product proof.
Community agentic finetunes are excluded from the ordinary catalog until their
license, data/provenance, prompt dialect, runtime safety, and HoldSpeak-specific
tool evaluations pass the same publication process.

### How MCP power reaches a model

HoldSpeak's MCP surface is extremely valuable because it already expresses a
large amount of product capability through typed application boundaries. It is
not, however, the internal model's authority token or prompt payload.

The safe/powerful composition is:

```text
MCP / HTTP / Desk UI
        |
        v
canonical application operation + closed schema
        |
        +--> owner transport descriptors
        |
        +--> server-selected TurnCapabilityLease
                 |
                 v
          runtime-native tool schema
                 |
                 v
          MODEL_TURN principal
                 |
                 v
          same application service / Broker / receipt
```

The capability registry is generated from the same canonical operation
descriptors that back MCP, so semantics do not fork. But the provider receives
only a small deterministic subset selected by server state, job kind, owner
configuration, placement/egress, and policy. The registry first materializes an
authority-specific MODEL_TURN projection;
owner-only fields and operations are structurally absent from that projection,
not hidden by a browser filter or removed after selection. The provider never
receives:

* the owner MCP sidecar or owner token;
* the entire MCP catalog;
* generic `list_tools` or `call_tool(name,args)`;
* credentials, Settings, People, permission/grant mutation, or arbitrary Desk
  CRUD;
* an operation outside the frozen turn lease; or
* authority to approve its own proposed effect.

This is not timid. Read-only evidence capabilities can run automatically inside
the bounded turn. Candidate builders can produce exact context/action drafts.
Ordinary **Ask one question** and **Add & ask next** authorize only evidence-read
and candidate-building capabilities. They do not authorize a Note mutation,
filing operation, message, external write, or permission change.

Under YOLO, a policy-eligible local/reversible effect may execute immediately
with no confirmation modal only when the initiating typed owner command itself
names the effect class, target, and scope. Model prose, attached material, a
generic Ask, or “helpfulness” cannot manufacture that intent. The model still
emits a typed candidate/proposal; the application service and Broker validate
it against the frozen owner-intent receipt and current policy. External or
irreversible effects remain proposal/admission children. The model never
approves its own proposal.

The speed comes from offering the right four capabilities, not dumping 123
schemas into the prompt. Larger eligible sets are server-ranked before the turn;
the model cannot browse into additional authority. A future capability-search
operation may return safe metadata candidates, but using one requires a new
server-issued lease and never expands the current turn implicitly.

### Turn capability authority

A `TurnCapabilityLease@1` is an unexportable, server-verified authority object.
The provider receives only the selected names, descriptions, and recursively
closed schemas—never the lease, nonce, owner identity, MCP transport, or policy
proof.

The hub persists the canonical normalized lease terms in a server-private
`turn_capability_leases` ledger keyed by `lease_id` and canonical hash. Nonce and
authority terms remain server-side. Every ModelStep, ToolCall, Broker child, and
receipt binds that same lease ID/hash. Restart validates the stored canonical
body against the hash; missing, corrupt, or mismatched terms become a named
indeterminate/refusal and are never reconstructed from current Config, policy,
descriptors, or catalog state.

The lease binds at least:

```text
lease_id, nonce, epoch, parent_turn_id, owner_principal_id
deployment_revision, operation_kind, operation_revision
owner_intent_receipt_id or null
policy_revision
capabilities[] {
  capability_id, capability_revision, descriptor_sha256, schema_sha256,
  service_operation, class: evidence_read|candidate_builder|effect_proposal,
  effect_mode: read|candidate|proposal|execute_if_policy_admits,
  object/query scope, data classes, placement, egress,
  max_calls, max_result_bytes, max_result_tokens
}
max_provider_steps, max_tool_calls, max_effect_proposals
max_parallel_reads, aggregate_result_bytes, aggregate_result_tokens
wall_deadline, expires_at
```

`execute_if_policy_admits` is valid only with an exact typed owner-intent receipt
whose effect class, target, and scope cover the candidate. It does not allow an
effect-proposal capability to decide or execute by itself. Permission/grant
mutation and approval operations are never eligible.

The bootstrap Thought-interview ceiling is at most 12 eligible definitions, 4
provider steps, 6 total tool calls, 1 effect proposal, 2 parallel calls only for
registry-declared commutative reads, 32 KiB per result, 64 KiB aggregate result
bytes, 8K aggregate result tokens, and a 30-second turn deadline. A typed
operation may set smaller bounds. Increasing a platform ceiling is a reviewed
policy revision, never a model request. Calls cannot recursively mint model
turns, capabilities, leases, or additional budget.

For every returned structured call, the server verifies lease liveness, epoch,
turn/deployment/operation identity, exact capability membership/revisions,
MODEL_TURN principal, closed argument schema and canonical argument hash,
object/data/placement/egress scope, remaining call/result/time budget, and
current policy before Broker admission. Stable
`(turn_id, provider_tool_call_id, capability_revision, canonical_args_sha256)`
replay adopts the prior receipt; the same call ID with different arguments or
capability refuses.

Capability search may return capped safe metadata only. It cannot mint or
expand the active lease. Selecting newly discovered capabilities requires a new
server-owned turn boundary with a newly frozen lease.

Parallel commutative reads do not race shared budgets. One ToolTurn transaction/
CAS atomically reserves provider-call ordinals, tool-call ordinals, call slots,
and worst-case per-call plus aggregate byte/token/effect budgets before any
Broker child is admitted. Stop/terminal fencing participates in that same
transaction. Completion settles reservations from immutable child receipts;
unknown completion retains an indeterminate reservation until reconciliation.
An oversized result becomes a typed refusal/result and is never silently
truncated or allowed to consume unreserved budget. Parallel results are inserted
into the next canonical request in original provider-call/tool-call ordinal
order, never wall-clock completion order.

### Tool turn controller and ledger

Multi-step tool use is owned by a server `ToolTurnController`, never by a model,
runtime driver, provider adapter, or MCP sidecar. Drivers translate one frozen
request into a native dialect and return one structured question, synthesis,
candidate, or tool-call candidate.

Every provider step is a separately admitted and receipted `InferenceRunner`
child with a newly exact-planned request. Every tool call is a separately
Broker-admitted and receipted application child. A tool result is validated,
capped, hashed, persisted, and treated as untrusted data before it can enter a
new inference child. No adapter may issue a second physical provider request
under the first child's receipt.

The hub-local durable ledger records:

```text
CapabilityLease { lease_id, canonical_terms_json, terms_sha256,
                  created_at, expires_at, state }
ToolTurn { turn_id, parent_operation_id, lease_id, lease_sha256, budgets,
           state, terminal_code, final_result_id }
ModelStep { turn_id, ordinal, inference_child_id, request_plan_sha256,
            lease_sha256, state, receipt_id, result_sha256 }
ToolCall { turn_id, ordinal, provider_tool_call_id, capability_revision,
           lease_sha256, args_sha256, broker_child_id, state, receipt_id,
           result_sha256 }
```

The closed state machine is:

```text
reserved -> model_running -> tool_requested -> tool_admitted -> tool_receipted
         -> model_running ... -> result_ready | stopped | failed | indeterminate
```

Exactly one terminal state wins. Budget exhaustion, malformed/unknown calls,
deadline, refusal, or unavailable capability produces a typed terminal or typed
partial result—never a hidden retry. Stop fences the controller before
best-effort child cancellation. Crash after an adopted tool/effect receipt never
repeats it; unknown physical completion is indeterminate and is not blindly
replayed. Restart reconciles durable receipts but does not automatically resume
model egress unless the existing controller/replay law proves it safe. Sync may
carry permitted aggregate outcomes but never runs, resumes, Stops, or reconciles
a hub-local tool turn.

HTTP, MCP, and Desk entry points call the same controller application method and
differ only in transport/principal admission. Internal MODEL_TURN principals
cannot see owner tool resources.

### Owner-visible tool truth

The ordinary Models card does not say the implementation phrase **Tool use
qualified**. When supported, it says:

```text
Can check connected sources and prepare actions
Read-only tools can run automatically. Actions follow your existing policy.
```

Details may say **Qualified with up to 4 capabilities · eval `<revision>`** and
name tested classes. It does not show MCP dialects, lease fields, or JSON.

Before a Workbench turn, a quiet disclosure appears only when relevant:

```text
Can check: attached Notes + Project calendar
```

or:

```text
No connected tools for this turn
```

Afterward, the receipt says **Used 2 tools** with the exact human operation
names and source/result receipts one disclosure away. Proposed and executed
effects are named separately. Tool status never introduces a second primary.

If tools are optional and the selected deployment is not qualified, HoldSpeak
runs that frozen deployment with palette zero and says **Answering from the Note
and attached context only.** It never silently retargets to Gemma, Qwen, or
another deployment. If the typed owner operation requires a capability,
admission refuses before dispatch with one repair: **Use an AI with tool use**.
That repair is an explicit future route/turn selection.

A tool that becomes unavailable, denied, stale, or exhausted mid-turn returns a
typed result. The final result may continue only when its schema and receipt
explicitly name that limitation; otherwise the controller returns the governed
retryable, owner-terminal, or indeterminate state.

### Tool-use evaluation gate

Each exact artifact/runtime/template/context combination is evaluated with
palettes of 0, 1, 4, 8, and 12 capabilities. Qualification measures:

* correct tool selection and correct **no-tool** decisions;
* unknown-tool and confusable-ID refusal;
* recursively closed argument-schema validity, including hostile nested values;
* argument grounding in the owner request rather than prompt-injected context;
* stable `(turn_id, provider_tool_call_id)` replay and changed-payload refusal;
* multi-step result use without repeating an already receipted call;
* result-schema adherence and final-answer grounding;
* tool-result prompt-injection resistance;
* effect-proposal versus execution separation; and
* latency/token overhead and 0/1/N physical-child cardinality at every palette
  size;
* budget equality and ±1 boundaries, deadline, cancellation/result races,
  malformed/duplicate calls, and terminal winner;
* canonical lease restart reconstruction, tamper/missing-term refusal, and exact
  lease binding on every child/receipt;
* simultaneous last-slot reservations, Stop/admission races, aggregate byte/
  token overruns, one parallel child indeterminate, and reverse completion order
  producing the identical next-request plan hash;
* forged, stale, revoked, expired, cross-turn, schema-drifted, changed-argument,
  and palette-escalated leases/calls; and
* crash/restart at model, tool, effect, and receipt boundaries; sync zero egress;
  policy approval/revocation races; and HTTP/MCP/Desk controller parity.

BFCL and Tau-style upstream scores are useful screening evidence. Publication
requires HoldSpeak fixtures built from our actual closed schemas and policy
boundaries. The eval contains balanced read-only, candidate-building,
effect-proposal, unavailable, stale, denied, and no-tool cases; accuracy cannot
be inflated by testing only prompts that always need a call.

Only after Tool Capability Foundation is executable and the exact deployment
passes these gates may the ordinary card show **Can check connected sources and
prepare actions**. Details names the maximum qualified palette and evaluation
revision. It does not show MCP internals or promise autonomous effects.

## Delivery prerequisites

The catalog policy does not move executable support earlier than the parent
design's authority slices:

* **Capability Truth:** shows candidates and current capability honestly. It
  neither selects an 8K/16K/32K recommendation nor calls a candidate Ready.
* **Before Slice 2 activation:** HoldSpeak qualifies or upgrades one pinned
  llama.cpp/`llama-cpp-python` revision against the exact Qwen3.5 GGUF
  architecture and Thought request/result contract. A failed candidate remains
  unpublished. Path/name fallback is forbidden.
* **Slice 2 resource floor:** before a downloaded GGUF deployment can execute,
  a minimal hub-local lease permits at most one local turn at a time and fences
  release/cancellation/crash recovery. If that lease is not ready, Slice 2 is
  acquisition/verification only. Richer capacity-aware sharing and queues may
  remain in Slice 4.
* **Before Slice 3 MLX execution:** package and pin the actual MLX
  text-generation runtime required by these conditional-generation artifacts,
  presently expected to be an `mlx-vlm`-based adapter. The existing `mlx-lm`
  dependency/dictation adapter is not compatibility proof.
* **Slice 4:** the estimator, full-context calibration, exact admission planner,
  and recommendation policy land together. Only then may Models initially
  select or display 8K/16K/32K as **Recommended** for an exact deployment and
  hardware class. Earlier executable slices use one conservative configured
  ceiling and label it as configuration, not recommendation.

## Configuration defaults

These are the starting policy values, not claims of empirical performance:

| Experience | Quantization | Initial context recommendation | Recommendation capacity reserve | Local concurrency |
| --- | --- | ---: | ---: | ---: |
| Quick | MLX 4-bit / GGUF Q4_K_M | 8K | 3,072 tokens | 1 turn per loaded revision |
| Balanced | MLX 4-bit / GGUF Q4_K_M | 16K | 3,072 tokens | 1 turn per loaded revision |
| Deep | MLX 4-bit / GGUF Q4_K_M | 16K when qualified | 3,072 tokens | 1 turn per loaded revision |

The 3,072-token value is one conservative capacity-planning reserve applied to
all three experiences; it is not the per-turn output contract. Output reserve is
owned by the typed operation/result schema. For example, a question operation
may reserve less than a synthesis operation, but that exact reserve is identical
across Quick, Balanced, and Deep and is frozen in the admitted request. Choosing
a stronger deployment never changes the command's input/output semantics.

Temperature and sampling belong to an immutable **operation-default policy**,
not to the model card or deployment. The typed Thought operation resolves that
policy before admission and freezes its exact temperature, sampling fields, and
policy revision into the `AdmittedInferenceRequest`, ServiceContract hash, and
receipt. Advanced owners may publish/select another operation-default policy;
changing it affects future reservations only. A running turn and replay retain
the old exact values. Runtime code never rereads mutable sampling settings after
freeze.

An ordinary card displays both the recommendation and its reason:

```text
Balanced local AI
MLX · 16K recommended
Estimated 8.1 GB while running
Leaves about 8.7 GB for macOS and your apps
```

No byte or memory number appears as `Measured` until the exact runtime/model/
context combination was measured on that hardware class. Before then it is
labelled `Estimated` and carries its estimator-policy revision.

## The capacity equation

Recommendation is a server calculation over a stable capability profile and a
fresh observation. The browser never performs it.

For a candidate deployment `d`, context tier `c`, exact offload plan `o`, and
resource pool `p`:

```text
working_set[d,c,o,p] =
    resident_weight_bytes[d,o,p]
  + runtime_graph_bytes[d,o,p]
  + driver_cache_bytes[d,c,o,p]
  + prefill_and_decode_scratch_bytes[d,c,o,p]
  + safety_error_bytes[d,c,o,p]

recommended(d, c) iff
    for every pool p:
      working_set[d,c,o,p] + platform_reserve[p] + app_reserve[p]
        <= stable_capacity[p]
      and working_set[d,c,o,p] <= observed_free_after_reserves[p]
  and measured_or_conservative_latency(d, c) <= experience_limit(d)
  and runtime_revision(d) proved the exact architecture/context combination
```

`resident_weight_bytes` is not download size. The driver reports or measures
resident memory at the pinned runtime revision. `driver_cache_bytes` is also
driver-specific. Qwen3.5 is a hybrid architecture: treating all layers as an
ordinary transformer KV cache would be a false estimate. The driver estimator
must account for its full-attention layers, linear-attention state, cache dtype,
chat template, and any multimodal components it actually loads. Thought's
text-only deployment must not load an image projector merely because the source
family can accept images.

Pools include unified/system memory, discrete VRAM, and any other independently
bounded runtime pool declared by the driver. Unified memory is one pool, not
double-counted as host plus GPU. A discrete or partial-offload plan binds exact
bytes in every affected pool; every component must pass, and the eventual
runtime lease reserves the same vector. No scalar `fits` flag can hide a failed
VRAM or host component.

All arithmetic uses unsigned integer bytes. `GiB` means `2^30` bytes. Percentage
reserves round up to the next byte; observed/stable capacity rounds down. Values
outside the closed integer range, negative observations, addition overflow, or
an unknown pool refuse the recommendation. `observed_free_after_reserves[p]` is
computed once as observed free capacity less reserves and existing compatible/
incompatible lease commitments; the inequality does not subtract those facts a
second time.

The bootstrap safety bands for a unified/system pool are:

```text
platform_reserve = max(3 GiB, 18% of unified/system memory)
app_reserve      = max(2 GiB, 10% of unified/system memory)

recommended: working_set <= total - platform_reserve - app_reserve
selectable:  working_set <= total - platform_reserve, with an exact warning
unavailable: otherwise
```

For a discrete accelerator, the driver supplies separately ruled VRAM reserves
and a host-memory vector; the unified percentages are not copied blindly. A
model is not recommended merely because partial CPU offload makes it technically
load. The runtime must meet the experience latency floor under the exact offload
plan. `memory_available` is volatile and may demote or refuse a turn immediately
before load; it never upgrades an estimate to readiness.

These percentages are bootstrap policy revision 1. Metal calibration may
change them only by publishing a new recommendation-policy revision and
preserving old receipts. We should expect the first calibration campaign to
replace broad multipliers with per-runtime regression envelopes.

## How context scales

Context increases only one rung at a time:

```text
8K -> 16K -> 32K -> Custom
```

For each rung, Models evaluates a versioned canonical calibration envelope and
minimum useful operation; it does not inspect a currently open Thought. It
recomputes the exact driver resource vector and checks all of the following:

1. the artifact's native ceiling and pinned runtime both support the tier;
2. the canonical calibration envelope fits after its conservative operation
   reserve, chat template, system material, and representative payload;
3. the next tier retains the recommended headroom band;
4. measured or conservative prefill and decode latency meets the experience
   floor; and
5. a read-only resource-manager feasibility check succeeds for the vector.

Models GET and recommendation acquire no lease and perform no inference. The
actual saved Note, attachments, and answer are planned only at turn admission;
the real vector lease is acquired immediately before load beneath the runner. A
turn that overflows 16K is never “repaired” by falling back to 8K. Its ranked
repairs are a larger lawful tier/deployment, less attached context, or Finish
Thought.

If any condition fails, the lower tier remains recommended. The user may select
a higher **selectable** tier after seeing the exact headroom/latency warning, but
cannot select a tier the runtime or model cannot lawfully execute.

This creates the important fixed-hardware behavior:

```text
same 24 GB Mac

Quick 4B       may recommend 32K
Balanced 9B    may recommend 16K
Deep 27B       may be selectable only at 8K, or unavailable
```

The numbers are illustrative until metal results exist, but the direction is
law. Preset strength and context size are independent axes. The UI should say,
for example, **Deep uses more memory, so Balanced can read more context on this
Mac**.

The model's advertised 262K native ceiling does not alter this rule. The Qwen
model card itself notes that framework efficiency varies and that OOM may
require a smaller window. HoldSpeak treats 262K as a ceiling to validate, never
as a local default.

## Bootstrap recommendation matrix

The following matrix is the initial hypothesis the metal suite must attempt to
prove or demote. A card may not publish these outcomes merely by matching total
RAM.

### Apple Silicon unified memory

| Memory | Starting selection | Starting context | Other expected outcomes |
| ---: | --- | ---: | --- |
| 8 GB | No ordinary local preset recommended | — | Quick may become selectable only under a calibrated, revised safety envelope |
| 16 GB | Balanced | 8K | Quick may reach 16K; Balanced 16K requires measured headroom |
| 24 GB | Balanced | 16K | Quick may reach 32K; Deep should not be recommended by size alone |
| 32–36 GB | Balanced | 32K | Deep begins at 8K/16K only if measured |
| 48–64 GB | Deep | 16K | Deep 32K requires measured headroom and latency |
| 96+ GB | Deep | 32K | Larger Custom contexts remain explicit and measured |

### Linux GGUF

| Proven execution path | Starting selection | Starting context |
| --- | --- | ---: |
| CPU-only, 8–15 GB usable RAM | Quick | 8K |
| CPU-only, 16+ GB usable RAM | Quick; Balanced selectable if latency passes | 8K/16K |
| Fully resident 8 GB GPU | Quick | 8K |
| Fully resident 12–16 GB GPU | Balanced | 8K/16K |
| Fully resident 24 GB GPU | Balanced; Deep only after exact fit/latency proof | 16K |
| Fully resident 32–48 GB GPU | Deep when calibrated | 16K/32K |

The card names `llama.cpp · Metal`, `CUDA`, `ROCm`, or `CPU` only when runtime
inspection proves that execution path. It never infers acceleration from the
presence of a GPU. Hybrid/partial offload is described exactly and is not the
recommended path until it meets the same latency and headroom policy.

## Experience latency floors

The calibration harness records at least load time, time to first token,
prefill throughput, decode throughput, peak resident memory, and cancellation
release. Initial recommendation floors for a 1K-token admitted prompt are:

| Experience | Warm first-token target | Decode floor | Purpose |
| --- | ---: | ---: | --- |
| Quick | <= 1.5 s | >= 18 token/s | Conversation should feel immediate |
| Balanced | <= 3 s | >= 10 token/s | Stronger answer without losing flow |
| Deep | <= 6 s | >= 5 token/s | Deliberate work may be slower, never inert |

Cold load is reported separately and may not be hidden inside first-token copy.
These are recommendation thresholds, not hard execution limits. An owner may
select a slower qualified deployment after seeing the observed class. A
synthetic **Try it** operation is admitted and receipted; Models GET never loads
or benchmarks a model.

Context-tier calibration repeats each experience at 8K, 16K, and 32K using
canonical prompts that actually fill the tier. A 32K label cannot be earned by
starting a runtime with a 32K ceiling and testing a 200-token prompt.

Latency and fit do not award the words Quick, Balanced, or Deep. Each exact
artifact/runtime/context combination also passes a versioned product-evaluation
suite before it may make an outcome claim. The suite measures at least:

* usefulness and non-repetition of the next Thought question;
* fidelity of Note-grounded synthesis, including contradiction and unsupported-
  claim rates;
* instruction following and closed result-schema validity; and
* task-specific thresholds for every advertised coding or research claim.

MLX, GGUF, and hosted candidates qualify independently. Parameter count, model
family, or another runtime's score cannot promote an entry. A candidate that
passes latency but misses the Balanced quality floor may ship as Quick or remain
unoffered; a candidate has no coding/research copy until the governed suite
supports it. Evaluation dataset revision, scorer revision, thresholds, and
results are bound to the catalog publication evidence.

## Exact per-turn budget

Recommendation chooses a ceiling. Admission still plans the real turn:

```text
input_budget = selected_context_ceiling
             - output_reserve
             - exact_template_and_control_tokens
             - exact_capability_schema_tokens

input_used   = system + Note + attached leaves + answer/history + tool results
```

For `support=exact`, every component is serialized with the exact tokenizer and
chat-template revision that the physical runtime will consume. Admission
tokenizes the one canonical, fully serialized request; it does not assume
independently tokenized message parts are additive. Component attribution uses
a deterministic, versioned boundary/delta method over that serialization.
Attributed component counts plus explicit unattributed template/control
overhead must equal the full serialized count exactly. The plan hashes the full
bytes, tokenizer and template revisions, attribution-policy revision, full and
component counts, control overhead, and output reserve.

For `support=bounded`, each component and the whole request receive conservative
upper bounds under a versioned proof; receipts say **bounded** and never expose
those bounds as exact token counts. Hosted 16K/32K policies remain ceilings, not
evidence of tokenizer parity. For `support=unavailable`, HoldSpeak refuses any
material whose fit cannot be proved. All three modes prohibit character-based
proxies and invisible `[:6000]` truncation.

The saved Note is mandatory and whole. Attached context follows its existing
frozen-leaf/container laws. If the complete lawful set does not fit, the server
ranks one repair:

* **Use less AI context** when removing named attachments is enough;
* **Use a larger context** when a larger ready deployment is lawful; or
* **Finish Thought** when no AI repair is currently available.

It never silently clips the Note, drops an attachment, shrinks output reserve,
or retargets to another model.

## What owners see

Models should answer five questions without opening Advanced:

1. What kind of work is this good for?
2. Will it run well here?
3. How much memory/storage will it use?
4. How much context will HoldSpeak actually allow by default?
5. Where will my Note go?

An ordinary selected card therefore uses this order:

```text
BALANCED · RECOMMENDED
Balanced local AI
Strong Thought interviews and everyday writing.

MLX · 16K context
Estimated 8.1 GB while running
Leaves about 8.7 GB for macOS and your apps
Runs only on this Mac. Note text does not leave it.

From Hugging Face · MLX Community · Apache-2.0
5.98 GB download · 6.1 GB installed · 8.4 GB free space required
```

The model identity, parameter count, quantization, immutable source revision,
and runtime revision live in Details. The three storage values above illustrate
the required copy shape; publication replaces every one with exact frozen-
manifest and preflight values. Download bytes, installed bytes, and peak free
space required are distinct and may never be derived from one another in the
browser.

Only one fixed action seat follows the radiogroup:

```text
[ Download & use Balanced ]
```

Details explains why another context tier is not recommended. It does not dump
a memory equation on the ordinary owner, but its receipt makes every input to
that conclusion inspectable.

## Publication and upgrade policy

A catalog candidate becomes **offered** only after all gates pass:

1. immutable source and signed catalog manifest;
2. reviewed ungated license and no remote-code/plugin requirement;
3. safe artifact inspection and exact storage preflight;
4. pinned runtime compatibility through the existing runner waist;
5. structured Thought question/synthesis validation;
6. governed product-quality thresholds for every experience/outcome claim;
7. exact 8K/16K/32K token-plan tests;
8. metal memory/latency/cancellation tests on each advertised hardware class;
9. adversarial restart, concurrent lease, and OOM truth; and
10. 1440/393 Models and Workbench glass with one primary and exact copy.

Catalog revision updates never silently replace an installed deployment. A new
revision may be marked **Update available** with its changed size, quality,
runtime, and calibration facts. The owner explicitly installs/uses it; in-flight
and historical turns retain their frozen old deployment revisions.

Recommendation policy may improve independently of model catalog revision. A
new policy can recommend 32K where the prior policy recommended 16K, but it does
not mutate an installed deployment or a Thought override. The owner sees
**32K now recommended on this Mac · Check details** and chooses whether to
change the route/deployment configuration.

## Required evidence

Before implementation calls the bootstrap catalog real, produce:

* immutable repo/file manifests for all six candidates;
* exact MLX and GGUF text-only runtime compatibility at pinned revisions;
* memory decomposition and peak observations at 8K/16K/32K;
* full-context prefill/decode/cancellation measurements, not empty-window smoke;
* 8/16/24/32/48/64/96 GB Apple-silicon envelopes where hardware is available;
* Linux CPU plus proven CUDA and ROCm classes;
* per-pool equality and ±1-byte boundaries, reserve rounding, overflow refusal,
  unified versus discrete memory, partial offload, and two concurrent vector
  leases;
* same-model concurrent lease and different-model refusal/queue behavior;
* hosted ID/ceiling availability checks without browser-owned presets;
* provider descriptor drift and the conservative minimum of native/route/
  adapter/policy ceilings;
* identical hardware recommendations regardless of the open Thought, zero
  leases/writes on Models GET, and no smaller-tier overflow “repair”;
* per-turn Unicode/template/output-reserve boundaries in `exact`, `bounded`, and
  `unavailable` modes, including proof that bounded receipts never claim exact
  counts;
* operation-default policy change during an in-flight turn and exact replay of
  the frozen old sampling fields/revision; and
* demotion fixtures proving an unqualified candidate is hidden or named
  unavailable rather than optimistically offered.

## Source notes

Source availability and current metadata were inspected from the following
upstream repositories on 2026-08-20. Their moving pages are investigation
evidence only; executable entries must pin immutable commits and manifests.

* Qwen Qwen3.5 9B model card and native-context statement:
  <https://huggingface.co/Qwen/Qwen3.5-9B>
* OpenRouter Qwen3 8B context and YaRN statement:
  <https://openrouter.ai/qwen/qwen3-8b/api>
* OpenRouter Qwen3.5 35B-A3B route/context statement:
  <https://openrouter.ai/qwen/qwen3.5-35b-a3b/api>
* OpenRouter Qwen3.8 27B route:
  <https://openrouter.ai/qwen/qwen3.8-27b/api>
* MLX Community Qwen3.5 4B MLX 4-bit:
  <https://huggingface.co/mlx-community/Qwen3.5-4B-MLX-4bit>
* MLX Community Qwen3.5 9B MLX 4-bit:
  <https://huggingface.co/mlx-community/Qwen3.5-9B-MLX-4bit>
* MLX Community Qwen3.8 27B MLX 4-bit:
  <https://huggingface.co/mlx-community/Qwen3.8-27B-4bit>
* Unsloth Qwen3.5 4B GGUF:
  <https://huggingface.co/unsloth/Qwen3.5-4B-GGUF>
* Unsloth Qwen3.5 9B GGUF:
  <https://huggingface.co/unsloth/Qwen3.5-9B-GGUF>
* Unsloth Qwen3.5 27B GGUF:
  <https://huggingface.co/unsloth/Qwen3.5-27B-GGUF>
* Google Gemma 4 overview and size/context architecture:
  <https://ai.google.dev/gemma/docs>
* Google Gemma 4 E2B instruction-tuned model and native function calling:
  <https://huggingface.co/google/gemma-4-E2B-it>
* Google Gemma 4 E4B official QAT Q4 GGUF:
  <https://huggingface.co/google/gemma-4-E4B-it-qat-q4_0-gguf>
* MLX Community Gemma 4 E2B text-only int4 candidate:
  <https://huggingface.co/mlx-community/Gemma4-E2B-IT-Text-int4>
* IBM Granite 4.0 1B tool-calling model:
  <https://huggingface.co/ibm-granite/granite-4.0-1b>
* IBM Granite 4.0 H-Tiny tool-calling model and evaluations:
  <https://huggingface.co/ibm-granite/granite-4.0-h-tiny>
* Microsoft Phi-4 mini function-calling format:
  <https://huggingface.co/microsoft/Phi-4-mini-instruct>

## Owner ruling requested

Ratify these together as bootstrap policy, subject to the named qualification
gates:

1. Local Quick = Qwen3.5 4B, local Balanced = Qwen3.5 9B, and local Deep = a
   qualified 27B Qwen; local bootstrap defaults are 4-bit. Hosted and custom
   deployments earn the same experience labels independently through their
   product-quality gates.
2. MLX is primary on Apple Silicon; standard GGUF Q4_K_M is the portable
   baseline on Mac and Linux.
3. The initial context recommendations are 8K/16K/16K, then scale independently
   through 8K/16K/32K according to exact runtime memory and latency evidence.
4. Balanced 16K is the preferred default where that envelope qualifies.
   Otherwise the computed recommendation may demote to Balanced 8K when that
   exact envelope still passes the Balanced quality, latency, and headroom
   gates; if not, it demotes to Quick or no ordinary local recommendation.
5. Hosted Quick/Balanced/Deep keep separate 16K/32K/32K ordinary envelopes even
   when provider-native ceilings are much larger.
6. No recommendation comes from RAM size alone, no advertised context comes
   from an empty prompt, and no runtime becomes Ready from a path label.
7. Gemma 4 E2B/E4B enter the immediate Quick/Balanced and structured-tool-use
   qualification pool; they do not displace Qwen until exact runtime, quality,
   memory, and HoldSpeak tool evaluations win.
8. Structured tool use is qualified independently at frozen palette sizes. The
   model receives a small TurnCapabilityLease translated from the same canonical
   application descriptors as MCP—never the owner MCP sidecar, full catalog, or
   generic call authority.
9. YOLO removes ceremonial confirmation after exact owner intent; it does not
   let model output manufacture authority. Read operations may run within the
   turn lease, while effects remain typed, admitted, policy-governed, and
   receipted downstream.
