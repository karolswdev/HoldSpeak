# The Inference Instrument

**Status:** Guru Meditation review ratified (architecture, implementation/scope,
and cold-owner craft); awaiting owner sitting

**Date:** 2026-08-20

**Grounded in:** Phase 131 one-admission-path, Phase 135 Workbench 2.0+ laws,
Phase 139 Settings Reckoning, and the implemented Phase 141 Thought Workbench.

**Bootstrap catalog/context companion:**
[Inference Catalog and Context Policy](inference-catalog-and-context-policy.md)

## Decision

HoldSpeak will present AI as one coherent **Inference Instrument**.

The Desk and every product workspace issue typed application commands. They do
not know whether a turn runs through MLX, llama.cpp/GGUF, an OpenAI-compatible
endpoint, a paired device, or a mesh worker. The application path resolves a
destination, freezes deployment and exact material, builds the canonical
request/context plan, hashes the ServiceContract, and then asks the inference
kernel to admit and dispatch that frozen request. The kernel publishes one typed
result with receipts.

Models is the instrument rack: it detects the host, recommends useful choices,
acquires and verifies model artifacts, activates deployments, and routes jobs.
Thought Workbench is the performance surface: it shows the intended destination
for the next turn and the actual destination after the turn. Runtime machinery
never leaks into the document or interview contract.

This design turns the current local setup from a path picker into the same
first-class experience already begun for hosted presets:

```text
Mac, Apple Silicon                 Linux
-------------------------------   -------------------------------
MLX · recommended                 GGUF / llama.cpp · recommended
GGUF / llama.cpp · available      CUDA/ROCm acceleration when real
Existing model · available        Existing model · available
Local/LAN endpoint · available    Local/LAN endpoint · available
Hosted/paired/mesh · available    Hosted/paired/mesh · available
```

Nothing downloads silently. One explicit **Download & use** gesture is enough;
there is no second confirmation. Policy, permissions, admission, placement,
egress, and receipts remain downstream hard boundaries.

## Scope and sequencing ruling

This document contains two different kinds of law and names them explicitly:

1. **North-star platform law** defines the final authority model. It is binding
   on later slices so a quick implementation cannot create a second waist,
   deployment ledger, routing authority, or unsafe downloader.
2. **Inference Instrument I — Capability Truth** is the only first-delivery
   commitment. It is read-only. It preserves current Config routing, current
   v1 deployment hashes, current GGUF Thought execution, and every existing Ask
   path. It adds one coherent server-owned projection and the honest Models
   composition. It does not download, activate, calibrate, migrate routes,
   execute MLX for Thoughts, or claim exact token planning.

Durable acquisition, v2 execution revisions, MLX Thought execution, exact token
admission, and Workbench destination overrides land only in their named later
slices after their authority prerequisites are implemented and tested. Slice 2
adds the minimal serialized local-execution lease required before any newly
activated artifact may execute; Slice 4 upgrades it to capacity-vector-aware
sharing and queues. Phase 141 remains 6/9 and is not expanded by this work.

## North-star owner walk

1. Open **Models**. HoldSpeak says **Apple Silicon · 24 GB unified memory** or
   **Linux · 32 GB RAM · NVIDIA 12 GB**, without benchmarking or loading a model.
2. The first row offers three useful local experiences, not file formats:
   **Quick**, **Balanced · Recommended**, and **Deep**. Each names runtime,
   artifact, download size, expected working memory, recommended context, and
   privacy boundary.
3. Select **Balanced**, then press the one fixed **Download & use Balanced**
   action. The action seat becomes a truthful byte-progress instrument with a
   quiet Cancel action. The app downloads only the named immutable
   revision into a staging directory, verifies every file, atomically installs
   it, adopts the artifact, then separately creates one deployment and CASes the
   Thoughts route. A stale route never reports **In use**. Readiness inspection
   runs no prompt.
4. The selected choice becomes **Ready · This Mac · 16K recommended**. A quiet
   **Try it** action may run a real admitted sample turn; readiness itself never
   invokes a model.
5. Open a Thought. A persistent row above the fixed command seat shows
   **Next question · This Mac · Balanced · 16K** at both widths. Changing it
   persists a per-Thought override for future turns; **Use default** clears the
   override. The in-flight turn is immutable. The Note, context, action
   hierarchy, and typed result are unchanged.
6. The returned question says **Ran on this Mac · MLX · Qwen…** and exposes its
   exact context and placement receipt. A hosted result names the provider and
   egress instead.
7. If the machine cannot run a preset comfortably, the card explains why and
   offers a smaller local choice or an already-configured endpoint. It never
   produces a mysterious failed check for a format the selected runtime cannot
   load.

## Product laws

### L1 — One typed invocation waist

No Desk component, workspace, domain service, or browser client branches on
`mlx`, `gguf`, `llama_cpp`, `openrouter`, provider SDK, model repository, or
model filename. Those facts exist only below deployment resolution.

```text
Desk surface
    -> application service
        -> inference kernel
            -> frozen deployment revision
                -> runtime driver
```

If a runtime-specific condition appears above the frozen-deployment boundary,
the design has failed.

### L2 — Destination is the owner choice; runtime is implementation

An owner selects a **destination**: this device, a named private endpoint, a
hosted provider, a paired device, or a mesh node. A destination advertises one
or more executable deployments. A deployment binds a model artifact or remote
model identity to a runtime and capability manifest.

The owner may inspect `MLX` or `GGUF`, but product commands never accept a
runtime name as authority.

### L3 — Same command and result everywhere

One Thought refinement request has the same closed schema, context law,
cancellation behavior, tool-capability lease, and typed output union on every
destination. Runtime drivers may translate the frozen prompt and schema into a
provider dialect. They may not reinterpret product intent, grant authority,
choose tools, silently retry physical calls, or mutate Desk state.

### L4 — Presets are recommendations, not hidden authority

A preset is a signed/revisioned catalog entry containing safe metadata and a
source recipe. It may recommend a model and context tier for observed hardware.
It cannot start a download, change job routing, invoke a model, accept a
license, or create provider credentials without the owner's explicit action.

**Quick**, **Balanced**, and **Deep** name model experiences only. Context is a
separate exact number—**8K**, **16K**, **32K**, or **Custom**—shown as a fact on
the selected experience. No context tier reuses the experience names.

### L5 — One gesture after informed choice

The card shows source, license, download bytes, expected installed bytes,
estimated working memory, runtime, context recommendation, and placement before
the action. **Download & use** is then direct and confirmation-free. This is
YOLO-first: rich defaults and immediate execution, with hard authority and
integrity checks downstream rather than ceremonial modal friction upstream.

### L6 — Automatic means explainable

Every automatic recommendation carries its inputs and result:

```text
Recommended because: Apple Silicon · 24 GB unified memory
Estimated: 7.8 GB model + cache · 16K context · leaves ~9 GB headroom
```

No recommendation is based only on a filename or marketing parameter count.

### L7 — Context is admitted per turn

The configured context window is a runtime ceiling, not permission to fill it.
Before every physical turn, HoldSpeak tokenizes the exact system contract,
working Note, frozen attachments, prior answer material, tool evidence, and
reserved output. The turn is admitted only if that exact plan fits.

Important material is never silently truncated. The refusal names the limiting
material and offers a lawful repair.

### L8 — Local is a first-class destination

On Apple Silicon, MLX is ordinarily recommended and GGUF remains fully
supported. On Linux, GGUF/llama.cpp is the portable default; CUDA, ROCm, or CPU
acceleration is reported only when the installed runtime proves it. Existing
files/folders remain an expert escape hatch on both platforms.

Local readiness is format-aware. An MLX directory can never be tested by a
GGUF-only driver, and a `.gguf` file can never be advertised as an MLX
deployment.

### L9 — Downloads are durable operations, not fetch callbacks

Model acquisition has a durable job, immutable source snapshot, byte counters,
bounded retries for known-safe reads, cancellation, restart reconciliation,
verification, atomic install, and a receipt. Unknown completion is never
reported as installed and an unverified artifact is never executable.

Filesystem installation and SQLite activation are an ordered, restart-safe
saga, never one falsely atomic transaction. Verified installation may succeed
while route activation conflicts; that state retains a reusable artifact and
offers **Use for Thoughts** without claiming **In use**.

### L10 — Workbench remains an instrument, not Settings

Thought Workbench exposes a compact next-turn destination control, intended
placement, actual placement, context truth, and its one state primary. It never
shows download managers, API keys, model paths, quantization controls, or a
provider matrix. **Set up AI** opens Models at the exact relevant section and
returns focus to the Workbench when setup succeeds.

### L11 — Model capability does not create tool authority

Runtime selection and tool selection are orthogonal. The inference kernel may
later translate a small server-selected capability lease into each runtime's
native structured-tool dialect. No runtime receives the owner MCP sidecar, the
global tool catalog, a generic `call_tool`, credentials, or approval authority.

### L12 — Receipts report actuality

The pre-turn UI shows advisory intended placement. The post-turn receipt names
the deployment revision, runtime, actual model identity, actual boundary,
egress classes, admitted context plan, and physical operation lineage. A label
derived from Settings is never substituted for execution evidence.

### L13 — One selected choice, one action seat

Models presents local experiences as one labelled radiogroup. Selection is
inert. Exactly one fixed action seat below the group performs the selected
state's command: **Download & use Balanced**, **Try again**, **Use Balanced for
Thoughts**, or **Return to Thought**. Cards do not each contain a primary.

### L14 — Stable capability, volatile observation

Hardware capability (platform, architecture, total memory, accelerator/runtime
support) has a stable profile hash. Available memory, free disk, and runtime
pressure are timestamped observations. Recommendations and receipts freeze both
plus the recommendation-policy revision. Volatile facts may trigger **Check
again** or an immediate capacity refusal; they do not silently change a route,
context tier, or readiness claim.

## Canonical concepts

### Destination

A routable place where inference may execute:

```json
{
  "id": "this_device",
  "kind": "this_device",
  "name": "This Mac",
  "boundary": "this_device",
  "readiness": "ready",
  "active_deployment_id": "local_balanced_mlx"
}
```

Kinds remain the existing closed destination vocabulary. Arbitrary URLs are not
destinations until a configured adapter validates their scheme, boundary,
credentials posture, and executable model identity.

Today `InferenceTarget` resolves to exactly one adjacent deployment identity.
Capability Truth preserves that contract. Later setup projections may list
other compatible deployment definitions as choices, but they do not turn one
target into an implicit multi-model executor. Activating a choice changes the
destination's mutable deployment head; a turn still resolves one immutable
execution revision.

### Runtime capability

A runtime driver reports what it can actually execute without loading a model:

```json
{
  "runtime_id": "mlx_text_v1",
  "format": "mlx_safetensors",
  "platforms": ["darwin_arm64"],
  "structured_output": true,
  "structured_tools": false,
  "cancellation": "cooperative",
  "tokenizer": "artifact",
  "kv_cache_modes": ["default"],
  "available": true,
  "reason": null,
  "runtime_revision": "sha256:..."
}
```

The initial MLX runtime implements the same canonical prompt engine used by
Ask. It is an inference engine beneath the existing adapter, never a Thought
adapter. The current
dictation MLX runtime may share low-level loading utilities, but neither
dictation nor Thought owns the driver.

### Model artifact

An immutable installed set of local bytes:

```json
{
  "artifact_id": "artifact_...",
  "format": "mlx_safetensors",
  "source": {
    "kind": "huggingface_snapshot",
    "repository": "mlx-community/...",
    "revision": "<immutable commit>"
  },
  "manifest_sha256": "sha256:...",
  "installed_bytes": 3060000000,
  "license": "Apache-2.0",
  "local_path": "<owner-private resolved path>",
  "state": "verified"
}
```

Public projections omit the resolved path unless the owner opens technical
details. Sync never copies artifact bytes or local paths.

### Deployment

A mutable **deployment definition** is setup authority: the owner's selected
runtime, artifact/model identity, context configuration, and destination. Its
configuration revision is not executable proof. Every execution captures one
canonical immutable **deployment execution revision** consumed by the existing
`InferenceRunner`.

North-star mutable definition:

```json
{
  "deployment_id": "local_balanced_mlx",
  "destination_id": "this_device",
  "runtime_id": "mlx_text_v1",
  "artifact_id": "artifact_...",
  "model_identity": "...",
  "context_ceiling_tokens": 32768,
  "recommended_context_tokens": 16384,
  "capability_manifest_sha256": "sha256:...",
  "revision": 3
}
```

Every invocation freezes the complete execution revision before kernel
admission. Editing or replacing a definition affects future turns only.

#### Deployment revision compatibility law

The existing Phase 131 `DeploymentRevision` v1 content hash and serialized
fields remain byte-for-byte stable. Historical rows are never rewritten,
backfilled into a new hash, or made dependent on new setup tables. Existing v1
revisions remain executable through the current engine factory.

When a new runtime/artifact path actually executes, it creates a versioned v2
revision in the same canonical revision registry—not a parallel ledger. V2
content identity binds:

* destination, kind, boundary, endpoint/node and nonsecret secret-slot identity;
* runtime capability ID and immutable runtime revision;
* artifact ID, canonical manifest hash, format, architecture, and model identity;
* capability-manifest hash and context ceiling; and
* schema version.

V2 excludes absolute local locators. Execution resolves `artifact_id` through
the hub-local verified artifact ledger after claim. A peer may sync immutable
nonsecret v2 metadata to resolve a historical receipt, but without the artifact
it reports unavailable and never downloads, retargets, or falls back. V1's
historical `model_path` limitation is preserved as legacy evidence; public
projections and new v2 sync never add another locator exposure.

Current v1 sync is the explicit legacy exception: `DeploymentRevision.to_dict()`
already carries `model_path`, and preserving its byte-identical hash means it
cannot be redacted in place. Capability Truth does not broaden or rewrite that
behavior. V2 ends the exposure prospectively; historical v1 metadata retains
its existing sync semantics until a separately versioned sync retirement can
state the receipt-resolution tradeoff.

### Hardware profile

Hardware detection is read-only and bounded:

```json
{
  "platform": "darwin",
  "architecture": "arm64",
  "memory_total_bytes": 25769803776,
  "memory_available_bytes": 17179869184,
  "storage_available_bytes": 128849018880,
  "unified_memory": true,
  "accelerators": [{"kind": "metal", "memory_bytes": null}],
  "cpu_logical_cores": 10,
  "observed_at": "...",
  "profile_sha256": "sha256:..."
}
```

Detection never sends hardware facts off the hub. Values used in a recommendation
are frozen into the recommendation receipt so the UI can explain later why it
made that choice.

`profile_sha256` covers stable capability only. A separate
`observation_sha256` covers timestamped available memory/storage and pressure.
Capability Truth may report nullable stable facts and an unavailable reason;
it does not recommend fit from volatile facts alone.

### Preset

A preset describes an owner outcome and a source recipe:

```json
{
  "preset_id": "local_mlx_balanced_v1",
  "experience": "balanced",
  "label": "Balanced local AI",
  "description": "Fast interviews and substantial Note development.",
  "platform": "darwin_arm64",
  "runtime_id": "mlx_text_v1",
  "source_repository": "...",
  "source_revision_policy": "resolve_then_freeze",
  "download_bytes": 0,
  "minimum_memory_bytes": 0,
  "recommended_memory_bytes": 0,
  "native_context_tokens": 0,
  "license": "...",
  "catalog_revision": 1
}
```

Zero placeholders are forbidden in a published card. Catalog generation must
resolve exact values and source revisions before a preset becomes selectable.

## One system architecture

```text
Models room                         Thought Workbench / other workspace
    |                                             |
    | setup/download/activate/route               | typed domain command
    v                                             v
InferenceSetupApplicationService       RefinementApplicationService / AskService
    |                                             |
    +---------------------+-----------------------+
                          v
                 Inference destination resolver
                          |
                 frozen deployment revision
                          |
              frozen material + canonical request
                          |
           tokenizer/template context plan + hashes
                          |
                ServiceContract payload hash
                          |
                  kernel admission + journal
                          |
          +---------------+------------------+
          |               |                  |
       MLX driver     llama.cpp driver   OpenAI-compatible driver ...
          |               |                  |
          +---------------+------------------+
                          |
                 typed result + receipts
```

The setup service can create and activate deployments. It cannot construct an
engine or dispatch. Explicit **Measure** and **Try it** commands delegate to a
separate `InferenceApplicationService`, which creates an ordinary typed admitted
operation through the existing `InferenceRunner`. The inference service can
execute a frozen deployment. It cannot download or
silently replace its artifact. This separation prevents “helpful” runtime code
from mutating setup while a turn is being admitted.

## Runtime-driver contract

The existing `InferenceRunner` and `CanonicalPromptAdapter` remain the only
dispatch waist. Runtime work extends the admitted engine factory beneath
`build_intel_for_revision`; it does not add a second provider adapter or setup
dispatch path.

Each runtime family implements the smallest internal construction/inspection
contract:

```python
class RuntimeDescriptor(Protocol):
    def describe(self) -> RuntimeCapability: ...
    def inspect_artifact(self, artifact) -> ArtifactInspection: ...

class RuntimeEstimator(Protocol):  # optional later-slice capability
    def estimate(self, execution_revision, context_tokens) -> MemoryEstimate: ...

class RuntimeTokenizer(Protocol):  # optional later-slice capability
    def tokenize(self, execution_revision, canonical_request) -> TokenPlan: ...

class InferenceRuntimeEngineFactory(Protocol):
    def build_engine(self, execution_revision, *, warrant, context) -> PromptEngine: ...

class PromptEngine(Protocol):
    active_provider: str
    active_model: str
    def run_prompt(self, *, system_prompt, user_prompt, temperature,
                   max_tokens) -> str: ...

class PlannedPromptEngine(PromptEngine):  # v2 exact-context execution
    def run_admitted_prompt(self, admitted_request) -> str: ...
```

Rules:

* `describe`, `inspect_artifact`, and `estimate` do not load weights, contact a
  provider, or run inference;
* `tokenize` uses the deployment's exact tokenizer revision;
* `build_intel_for_revision(revision, *, warrant, context)` remains the single
  engine-registry entry point and selects a runtime engine factory only from the
  frozen revision;
* `build_engine` accepts the runner-issued exact `warrant` and `context` keyword
  arguments plus frozen execution revision; direct or setup-service construction
  refuses;
* `CanonicalPromptAdapter` remains the caller from `InferenceRunner._dispatch`.
  Existing v1 payloads call byte-compatible `run_prompt`; v2 exact-context
  payloads pass the entire immutable `AdmittedInferenceRequest` to
  `run_admitted_prompt` after validating its canonical request and plan hashes;
* a v2 engine validates tokenizer/template/runtime/execution revision and
  serializes the exact admitted request. It cannot receive only two strings,
  drop plan fields, or count one representation and send another;
* one physical provider call belongs to one admitted child operation;
* compatibility fallback is a new admitted child, never hidden in an engine;
* provider-native output is untrusted until canonical schema validation;
* cancellation and terminal receipts remain runner authority;
* the engine reports actual runtime/model facts and cannot read mutable Settings;
* no factory/engine may call Desk repositories, MCP, policy mutation, or setup
  services; and
* one-path census mechanically allow-lists and spies on every runtime factory and
  physical leaf.

`Probe` means bounded metadata/dependency/artifact inspection only. It performs
zero model load, network call, or inference. **Measure this AI** and **Try it**
are real typed model operations through ordinary kernel admission, cancellation,
and receipts; the setup service has no private dispatch function.

### MLX

MLX support is selected by artifact capability, not directory shape alone.
Text-only `mlx-lm` artifacts and multimodal `mlx-vlm` artifacts are distinct
runtime capability IDs even when the owner sees one **MLX** family. A preset
may be published only when its runtime supports that exact model architecture
and chat template. The initial Thought path needs text generation only; image
inputs remain absent unless separately designed and admitted.

### GGUF / llama.cpp

GGUF inspection reads canonical metadata before load: architecture, quantization,
tokenizer/chat template, declared context, and tensor bytes. A preset binds an
exact repository revision and filename. `Q4_K_M` or another quantization label
is never treated as a complete performance estimate without architecture and
hardware facts.

### OpenAI-compatible and other endpoints

Configured endpoints continue through the same destination/deployment path.
`/models` discovery is advisory because many compatible endpoints omit context
and capability metadata. A deployment therefore carries an owner-visible
capability manifest from a known preset, a verified provider descriptor, or an
explicit expert override. Runtime failure cannot silently retarget elsewhere.

Paired and mesh execution use the same frozen deployment identity and receipts.
Live process continuity may remain hub-local; sync does not start or resume a
turn.

## Hardware-aware recommendation

### Inputs

Recommendation uses:

* platform and architecture;
* total and currently available system memory;
* unified versus discrete memory;
* proven accelerator/runtime availability;
* model tensor bytes and quantization;
* architecture-derived KV-cache cost;
* runtime workspace overhead;
* configured context tier;
* output-token reserve; and
* a conservative OS/Desk safety reserve.

It does not use:

* model filename alone;
* parameter count alone;
* an unverified GPU marketing label;
* current free memory without total memory;
* a benchmark copied from another runtime; or
* a remote leaderboard as a local readiness claim.

### Memory estimate

For each candidate context tier:

```text
steady working set
  = verified model tensor bytes
  + runtime fixed overhead
  + architecture-specific KV cache bytes(context tier, cache format)
  + tokenizer / graph / scratch estimate
  + output and tool-result reserve

required host capacity
  = steady working set
  + safety reserve
```

The architecture-specific calculation is supplied by the driver and stamped
with its runtime revision. Generic code must not guess KV geometry.

Default safety reserve is the greater of a platform floor and a fraction of
total memory. The actual constants must be established by hardware calibration
and committed as versioned policy, not chosen in CSS or the browser.

### Context choices

The setup UI offers computed experiences:

| Choice | Goal | Admission posture |
|---|---|---|
| 8K | lowest latency, ordinary short Notes | available only when canonical prompt and useful attachments fit |
| 16K | ordinary Thought development | common computed recommendation on modest local hardware |
| 32K | larger source sets and long Notes | offered when memory and prefill latency remain acceptable |
| Custom | expert override | bounded by verified model/runtime maximum with explicit risk and estimate |

The visible number is always exact: **8K**, **16K**, **32K**, not “large.”
Changing a tier produces a new deployment revision and affects future turns.

### Calibration

After installation, an optional **Measure this AI** operation may run a small,
admitted, local-only calibration suite against synthetic non-owner text. It
records load time, prompt tokens/second, generation tokens/second, peak working
set when observable, runtime revision, thermal/power caveats when available,
and timestamp. It does not read Notes and it cannot silently change routing.

The recommendation engine may propose a new tier based on measurements. Only
the owner action changes the deployment.

### Runtime resource manager

Memory fit is not authority to load concurrently. Before local engine
construction, a hub-local resource manager leases capacity for the exact
execution/runtime revision. Each lease binds declared resident bytes, working
set, context/cache reservation, operation ID, runtime revision, and expiry.

Policy is bounded and explicit: compatible calls may share one resident model
cache only when the runtime proves safe shared ownership; otherwise a caller is
queued within a short bound or refused `local_capacity_unavailable`. It is never
silently retargeted. Cancellation releases the operation lease. Process restart
reconciles stale leases against live kernel operations before a new load. An
in-flight revision cannot be silently unloaded or replaced.

The immediate pre-load observation may still refuse when real capacity has
fallen below the reserved estimate. `memory_available` remains advisory and
never makes a deployment ready by itself. Cached engines carry no child's
`DispatchContext`; the runner binds and releases the exact child context for
each attempt as it does today.

## Per-turn context admission

Exact token admission is not claimed until Slice 4. The present Ask path's
ordinary 6,000-character material cap is named debt: Slice 4 replaces silent
cutting with explicit bounded planning/refusal before any new surface can claim
exact context use.

The context planner produces one immutable `AdmittedInferenceRequest` from exact
server-owned inputs. It binds the bytes the runtime tokenizes to the bytes the
provider receives:

```json
{
  "deployment_revision": "...",
  "runtime_revision": "...",
  "tokenizer_revision": "...",
  "chat_template_revision": "...",
  "canonical_request_sha256": "sha256:...",
  "system_tokens": 0,
  "system_sha256": "sha256:...",
  "working_note_tokens": 0,
  "working_note_sha256": "sha256:...",
  "attachment_tokens": 0,
  "attachment_manifest_sha256": "sha256:...",
  "answer_tokens": 0,
  "tool_result_tokens": 0,
  "tool_schema_tokens": 0,
  "reserved_output_tokens": 0,
  "total_tokens": 0,
  "ceiling_tokens": 16384,
  "plan_sha256": "sha256:..."
}
```

Admission order is deterministic. System contract and output reserve are
mandatory. The current working Note is never silently cut. Frozen attachment
membership is preserved; a container cannot be partially presented as if the
whole attachment was used. Tool results are individually typed and capped.

The canonical request includes the exact serialized system/user/history
messages, frozen attachment envelopes, typed tool definitions/results when
lawful, response schema, chat template controls, and BOS/EOS behavior. Resolution,
material snapshot, execution revision, and plan are frozen before the existing
`ServiceContract` payload hash is computed. After kernel claim, the runtime
validates tokenizer, template, runtime, execution revision, canonical request
hash, and plan hash before physical dispatch. Serialization drift refuses; a
driver cannot count one representation and send another.

The v2 `CanonicalPromptAdapter` is upgraded additively to carry that whole
object through the existing runner waist. Dropping, changing, or reordering any
bound field between adapter and planned engine refuses before the provider/local
generation leaf. V1 callers and historical execution keep today's `run_prompt`
shape.

Token support is reported per deployment as `exact`, `bounded`, or
`unavailable`. Remote provider limits or tokenizers that cannot be proven do not
receive an `exact` label. Bounded mode admits only under a conservative
versioned rule and says so; unavailable mode requires a configured safe ceiling
or refuses material it cannot prove.

When the plan does not fit, the server nominates one named primary repair:

* **Use less AI context** when removing attachments is sufficient;
* **Use a larger context** when a ready deployment can admit the complete plan;
* **Make a compact context copy** as a future explicit typed operation, never an
  invisible summarization side effect; or
* **Finish Thought** when no AI repair is currently available.

Other lawful choices sit under **Other options**. They never compete as equal
primaries.

The provider never receives bytes omitted from the receipt's admitted plan.

## Local model catalog

The bundled inference catalog is a closed discriminated union:

* `local_artifact_preset` binds immutable source recipe/manifest, bytes,
  format/runtime/architecture compatibility, license, and later acquisition;
* `hosted_profile_preset` binds provider adapter, remote model identity,
  boundary/egress, required secret-slot identity, and configured context claim
  with provenance. It has no artifact, manifest, download, or local-memory
  fields.

Capability Truth moves today's hosted JSX preset definitions into the
server-owned hosted branch without changing their existing profile-creation and
Config route behavior. A hosted model ID is never reinterpreted as a downloadable
artifact.

The local branch is small and curated. It is not a mirror of a model hub.
For each supported platform/runtime family it may publish at most three ordinary
presets plus the existing-artifact escape hatch. Catalog updates are code/data
changes with review, source verification, license review, and hardware glass.

The first catalog should include:

* Apple Silicon MLX: Quick, Balanced, Deep where hardware qualifies;
* Apple Silicon GGUF: Quick and Balanced, with Deep only where calibrated;
* Linux GGUF: CPU-portable choices plus accelerator-aware recommendations when
  the installed llama.cpp runtime proves acceleration;
* no preset whose current runtime cannot execute its architecture;
* no unpinned mutable download URL; and
* no model-size claim copied from a hosted provider card.

Candidate source families must be verified at catalog-build time. Current
examples for investigation—not yet approved catalog entries—include:

* `mlx-community/Qwen3.5-4B-MLX-4bit`;
* `mlx-community/Qwen3.8-27B-4bit`; and
* `unsloth/Qwen3.5-4B-GGUF` with one exact quantized file.

The published catalog freezes repository commits and file manifests. A moving
`main` branch is never the executable receipt.

### Catalog trust and publication

Capability Truth ships a packaged immutable catalog; setup GET performs zero
catalog network access. A later catalog refresh is a distinct owner-triggered
or explicitly background-authorized egress operation with its own receipt.

Canonical catalog bytes bind schema version, monotonically accepted catalog
revision, generated/expiry bounds, entries, source recipes, and signing key ID.
HoldSpeak verifies them against packaged trust roots before projection. Unknown
keys, invalid signatures, rollback below the locally accepted minimum, expired
catalogs, duplicate/confusable IDs, and revoked entries refuse publication.
Trust-root rotation requires an application update or a cross-signed key policy;
catalog data cannot mint its own trust root.

Ordinary one-gesture presets must be public and ungated under a reviewed license.
A catalog entry cannot accept terms for the owner. Gated/authenticated artifacts
remain an expert flow with an explicit pre-existing grant and separately ruled
copy.

Before a preset is publishable, build fixtures prove its immutable repository
commit, format/architecture, runtime compatibility, license metadata, download
and installed byte counts, complete allow-listed manifest, and independent
per-file digest provenance (including LFS object IDs where applicable). Loading
uses `trust_remote_code=False`; model inspection never imports repository code,
pickle objects, plugins, or executable setup artifacts.

## Download, verification, and installation

### Operation state

```text
requested
  -> resolving_source
  -> downloading
  -> verifying
  -> installing
  -> ready

requested/resolving_source/downloading -> cancelled
any state             -> failed
physical completion with unknown receipt -> indeterminate
```

Pause is not part of the ruled first acquisition slice. Cancel and safe retry
are complete; a future Pause must add durable `pausing/paused/resuming` states,
commands, range-integrity rules, and restart tests before it appears on glass.

The service persists the owner action and canonical payload before network
access. Pre-resolution concurrency is keyed by the signed source-recipe hash
(`preset_id + catalog_revision + recipe_sha256`). After immutable commit and
manifest resolution, jobs converge on the content identity
`(source kind, repository, commit, manifest hash, runtime/format requirement)`.
Two presets resolving to the same content share bytes without sharing route
intent. Repeating the same owner request returns the same job; changed payload
under one request ID refuses.

Cancel is available only in `requested`, `resolving_source`, or `downloading`.
Once verification begins, Cancel disappears and the fixed seat reports
non-action status **Verifying…** or **Installing…**. A cancellation racing that
boundary returns typed `cancellation_too_late` plus current job truth; it never
relabels verified/adopted bytes as cancelled. After atomic rename or artifact
adoption, removal is a separate explicit operation.

### Source resolution

The service resolves the preset's repository through HTTPS, freezes the exact
commit and complete allow-listed file manifest, validates declared sizes and
license metadata, then persists the download plan before fetching bytes. MLX
snapshots may contain several required files. GGUF presets ordinarily name one
model file plus bounded metadata.

Redirects may not change to an unapproved scheme or host class. Repository file
paths are normalized and cannot escape the staging directory. Symlinks,
executables, pickle-like artifacts, and files outside the runtime allow-list are
refused unless a separately reviewed runtime requires them.

The frozen source plan binds allowed schemes/redirect hosts, credential
stripping, DNS/IP boundary policy, immutable commit, per-file trusted digest and
size, file/count/total/unpacked byte caps, runtime/format requirement, and
license/grant state. DNS rebinding, cross-boundary redirects, decompression
bombs, custom code, and mutable-ref retargeting refuse before adoption.

### Storage

Downloads land under one owner-private HoldSpeak model root, never `$HOME`, `/`,
or a user-supplied broad directory. Staging uses a unique job directory. A
verified manifest is atomically renamed into a content-addressed installation
directory; configuration points only at that final directory/file.

Cancel removes recoverable staging bytes or retains a clearly labelled partial
only when resumable-range integrity is proven. Removing an installed model is a
separate explicit action and refuses while a live deployment revision uses it.

Before the request, the card shows required peak storage: staged bytes plus
installed bytes plus filesystem safety margin, compared with a frozen current
storage observation. Insufficient space refuses before download and nominates a
smaller preset. Free space is checked again before each materialization step.

Deletion requires durable artifact, deployment, historical-local-availability,
and live resource-lease reference checks. Only a content directory carrying the
expected HoldSpeak owned-root marker and exact manifest may move to hub-local
trash/quarantine. Symlinks are never followed. Historical execution metadata
remains resolvable even after local bytes become unavailable.

### Integrity receipt

The installation receipt binds:

* owner request ID;
* preset/catalog revision;
* repository and immutable source commit;
* ordered file paths, sizes, and hashes/ETags under a canonical manifest hash;
* downloaded and installed byte counts;
* artifact format and inspected architecture;
* runtime capability revision;
* final artifact ID; and
* activation/deployment receipt when **Download & use** completes.

Model bytes, credentials, local paths, and provider-native error bodies never
enter public receipts.

### Download-and-use saga

**Download & use** is one owner intent implemented as durable stages, not one
filesystem/database transaction:

1. persist request, recipe, source plan, expected Thoughts route/head revision;
2. download and verify staged bytes;
3. atomically rename the content-addressed artifact directory;
4. adopt the artifact ledger row in SQLite;
5. in one later SQLite transaction create the immutable execution revision,
   advance the mutable deployment definition, CAS only the relevant Thoughts
   route revision, and persist the activation receipt; and
6. return a fresh setup projection.

Unrelated setup changes during a long download do not defeat activation; route
and deployment-head CAS values are separate rather than one global setup
revision. Crash after rename adopts the exact verified manifest or quarantines
it. Crash after artifact adoption leaves a reusable verified artifact. Route
conflict leaves the artifact/deployment ready but not **In use**. Lost response
replays immutable effects and returns the fresh current projection.

Progress events are advisory; the acquisition GET is authority. UI reports
verified logical bytes and explicit transport restart rather than inventing a
monotonic network percentage when a file safely restarts.

## Models experience

### Information architecture

```text
CHOOSE YOUR AI
  Current route and readiness

THIS DEVICE
  Detected hardware sentence
  Quick | Balanced · Recommended | Deep  (one radiogroup)
  [one fixed action seat]
  Other local formats…

OTHER DESTINATIONS
  OpenRouter presets
  Local/private endpoint
  Paired device / mesh
  Define your own provider

CHOOSE AI FOR EACH JOB
  Thoughts & notes
  Writing & dictation
  Meetings

ADVANCED
  Installed artifacts
  Deployment/context details
  Connection matrix
  Technical diagnostics
```

The current destination matrix survives under Advanced; it no longer defines
the first impression.

At 1440 the exact order is: **Choose your AI**; compact current-route strip;
**This device** with stable hardware sentence; three radio cards; one action
seat; then closed **Other local formats**, **Other destinations**, and
**Advanced** disclosures. On Apple Silicon the primary family is MLX and Mac
GGUF Quick/Balanced plus **Use an existing model** live under **Other local
formats**. On Linux the primary family is GGUF and names only proven execution,
such as `llama.cpp · NVIDIA acceleration`, `ROCm`, or `CPU`.

At 393 the route strip comes first and cards stack. Only the selected card
expands to full facts; unselected choices show name and one outcome sentence.
The full-width fixed action seat follows the group. No layer covers the Desk
dock, every control is at least 44px, and progress never scrolls horizontally.

### Local preset card

```text
BALANCED · RECOMMENDED
Balanced local AI

Substantial Thought interviews and everyday writing.

MLX · This Mac only       Download 6.2 GB
16K context recommended  About 10 GB working memory
Private · Apache-2.0

[ selected ]
```

One fixed seat below the radiogroup reads **Download & use Balanced**. Selection
by pointer, arrow keys, or Space performs no download or route mutation.

The same card after activation:

```text
READY · IN USE
Measured 28 tok/s · 16K context
[ selected ]

Fixed seat: READY · IN USE FOR THOUGHTS
Quiet: Try it · Details
```

Cards do not show repository IDs or quantization strings in the primary scan.
Technical details disclose them. **Quick**, **Balanced**, and **Deep** describe
an owner outcome; their actual models may evolve with catalog revisions.

Ordinary facts use this hierarchy:

```text
BALANCED · RECOMMENDED
Balanced local AI
Strong Thought interviews and everyday writing.
MLX · about 10 GB while running
16K context · leaves about 9 GB for your apps
Runs only on this Mac. Note text does not leave it.
From Hugging Face · MLX Community · Apache-2.0
6.2 GB download · 7.8 GB installed
```

Exact values come from the verified catalog and frozen recommendation; these
numbers are illustrative and cannot ship as placeholders. Details explains:
`16K is the runtime ceiling. HoldSpeak checks the exact saved Note, attached
context, answer, and output space before every turn.`

### Responsive law

At 1440, three cards share one row only when each retains a readable measure.
At 393, cards stack; the primary fills the card width and every target is at
least 44px. Download progress never creates horizontal overflow. Advanced
details are closed by default but keyboard reachable.

The group has exactly one visible primary in every state. During source
resolution/download the seat shows state/progress and exposes quiet Cancel;
verification/install shows status with no Cancel. Network failure promotes
**Try again**; integrity failure promotes **Download again**; route conflict
promotes **Use Balanced for Thoughts**. When Models was opened from a Thought,
successful activation promotes **Return to Thought** and never navigates back
automatically.

### Failure copy

Bad:

```text
Not ready · No working model was found.
```

Required:

```text
This is an Apple MLX model, but Thoughts are currently set to GGUF.
[Use with MLX]  [Choose another model]
```

Additional exact states:

```text
Downloading Balanced · 2.1 of 6.2 GB · 34%
Verifying Balanced · 8 files
Installing Balanced
Making Balanced the AI for Thoughts

Download stopped at 2.1 of 6.2 GB. HoldSpeak couldn't reach Hugging Face.
Your verified partial download is kept.  [Try again]

The partial file could not be safely resumed. HoldSpeak will restart this file.
[Try again]

Balanced needs 8.4 GB free to download and install safely.
This Mac has 5.1 GB free.  [Choose Quick]

The downloaded files did not match the published model.
They will not be used.  [Download again]

Balanced is downloaded and verified, but Thoughts still use This Mac · Quick.
[Use Balanced for Thoughts]
```

Progress is a semantic progressbar with coarse announcements and byte-valuetext;
no invented ETA. Card transitions preserve focus. Reduced motion preserves all
state truth. Cached shell target is under 100ms; local setup projection under
300ms; selection and disclosures under 100ms; acquisition acknowledgement under
300ms; first progress truth under 500ms after bytes begin; restart reconciliation
visible under 1s on the test hardware.

or:

```text
This model needs about 22 GB; this Mac currently has 13 GB available.
[Use the Balanced model]  [Keep it installed]
```

Errors always preserve a useful next action and name whether the problem is
artifact, runtime, memory, credentials, endpoint, or routing.

## Thought Workbench integration

The Workbench gains one compact, persistent destination row immediately above
the fixed command strip at both widths. It remains visible on Note and Interview
tabs, so an owner never starts Ask under a hidden target:

```text
Next question · This Mac · Balanced · 16K     [Change]
```

**Change** opens **AI for this Thought**, a bounded chooser of ready deployments.
**Use for this Thought** persists a hub-local per-Thought override for every
future AI turn in that Thought. **Use default** clears it. Only Models changes
the hub-local default Thoughts route. A per-Thought-looking control may never
silently change that global route.

Rows name outcome and boundary: `This Mac · Balanced / 16K · no network`,
`Office server · Qwen / 32K · private network`, or
`OpenRouter · Qwen / Cloud · saved Note and attached context may leave this
hub`. The footer names `Default for new Thoughts: This Mac · Balanced`.

At 1440 the chooser is a popover; at 393 it is a full-width sheet. Both are
radio groups with one fixed **Use for this Thought** primary. Escape/Close
returns focus to the destination row and mobile does not autofocus search.

Rules:

* an in-flight turn remains bound to its frozen deployment;
* changing destination affects the next turn only;
* a ready question remains answerable under its original receipt;
* **Add & ask next** freezes the currently displayed per-Thought override (or
  default) atomically with its existing answer/reservation transaction;
* unavailable destination promotes **Set up AI** into the fixed action seat;
* **Set up AI** deep-links to the relevant Models section and carries a
  return-to-Thought token; and
* successful setup returns to the same Thought with the Note and answer draft
  intact, then refreshes the authoritative Workbench projection.

Models never yanks the owner back when a minutes-long download finishes. It
changes its fixed seat to **Return to Thought**. Return restores Thought ID,
retained Note draft, answer, caret, focus target, and then refreshes the
authoritative Workbench projection. The no-model explanation reads:
`Opens Models. Your Note and answer stay here.`

During execution the row distinguishes `Running on This Mac · Balanced` from a
concurrently changed `Next question: Office server · Qwen`. The returned result
alone says `Ran on This Mac · MLX · <model>` from its actual receipt.

No model card, download progress, API-key field, or runtime diagnostic renders
inside Thought Workbench.

## Transport-neutral application API

One `InferenceSetupApplicationService` owns the setup/read/acquisition/
activation/routing operations below; admitted Measure/Try-it are the explicit
exception owned by `InferenceApplicationService`. HTTP and MCP are
closed adapters over the same methods; neither adapter reads/writes Config
directly. Capability Truth's application projection may read today's canonical
Config routes until the separately ruled route migration.

Capability Truth initially implements only `get_inference_setup()`. It may read
current Config and SQLite through one application projection but writes nothing.
The exact v1 DTO is closed and versioned:

```text
schema_version, observed_at
hardware { capability, observation, detection_state, reason }
runtimes[] { id, revision, formats, capability states, reason }
current_routes { authority:"config", thoughts, dictation, meetings }
current_thought_deployment { target, v1 revision, configured/readiness truth }
detected_local_artifacts[] { safe display facts, Thought support state }
presets[] { only verified/applicable packaged entries }
limitations[] { code, title, repair }
```

It exposes no secret, environment value, absolute locator, mutable browser fact,
model body, network-derived catalog refresh, or fake recommendation. HTTP
`GET /api/inference/setup` and owner-only MCP resource
`holdspeak://inference/setup` return identical inner DTOs. The read performs
zero database/config writes, model loads, provider calls, downloads, or probes.

### Read projections

```text
get_inference_setup()
  -> hardware profile
  -> runtime capabilities
  -> curated applicable presets
  -> installed artifacts/deployments
  -> job routes
  -> active acquisition summaries

get_acquisition(job_id)
get_deployment(deployment_id)
```

Reads do not download, load, probe, benchmark, mutate, or invoke.

### Commands

```text
begin_model_acquisition(request_id, preset_id, catalog_revision)
cancel_model_acquisition(request_id, job_id, expected_revision)
activate_model_artifact(request_id, artifact_id, runtime_id, context_tier,
                        expected_deployment_head_revision,
                        expected_route_revision)
download_and_use(request_id, preset_id, catalog_revision, context_choice,
                 expected_route_revision)
register_existing_artifact(request_id, path_grant, runtime_id,
                           expected_artifact_ledger_revision)
probe_deployment(request_id, deployment_id, expected_deployment_revision)
set_job_route(request_id, job, deployment_id, expected_route_revision)
set_thought_route(request_id, thought_id, deployment_id_or_null,
                  expected_thought_route_revision)
```

The separate admitted `InferenceApplicationService` owns:

```text
measure_deployment(request_id, deployment_id, expected_deployment_revision)
try_deployment(request_id, deployment_id, expected_deployment_revision)
```

The setup service may orchestrate/delegate to those methods for its UI, but can
never construct an engine or call a runtime leaf. HTTP and MCP measurement/test
twins call the admitted service and return its normal kernel operation/receipt.

`path_grant` is an owner-issued, bounded local-file selection result, not an
arbitrary browser string. If the current platform lacks a native file picker
grant, manual paths remain an explicit expert-only compatibility seam with
strict normalization and format inspection.

### Suggested HTTP surface

```text
GET  /api/inference/setup
POST /api/inference/acquisitions
POST /api/inference/acquisitions/download-and-use
GET  /api/inference/acquisitions/{id}
POST /api/inference/acquisitions/{id}/cancel
POST /api/inference/artifacts/register-existing
POST /api/inference/deployments/activate
GET  /api/inference/deployments/{id}
POST /api/inference/deployments/{id}/probe
POST /api/inference/deployments/{id}/measure
POST /api/inference/deployments/{id}/try
PUT  /api/inference/routes/{job}
PUT  /api/thoughts/{thought_id}/inference-route
GET  /api/inference/artifacts/{id}/technical
```

Progress uses the existing event stream with a pollable GET as authority.
Browser disconnect never cancels a download.

### MCP parity

Owner MCP twins expose the same projections and commands with recursive
`additionalProperties:false` schemas. A model running inside HoldSpeak never
receives these owner setup tools. Download and activation are owner operations,
not provider capabilities.

Later-slice parity is exact:

| Application method | HTTP | MCP twin |
|---|---|---|
| `get_inference_setup` | `GET /api/inference/setup` | resource `holdspeak://inference/setup` |
| `begin_model_acquisition` | `POST /api/inference/acquisitions` | `inference.begin_model_acquisition` |
| `download_and_use` | `POST /api/inference/acquisitions/download-and-use` | `inference.download_and_use` |
| `get_acquisition` | `GET /api/inference/acquisitions/{id}` | resource template `holdspeak://inference/acquisitions/{id}` |
| `cancel_model_acquisition` | `POST .../{id}/cancel` | `inference.cancel_model_acquisition` |
| `register_existing_artifact` | `POST /api/inference/artifacts/register-existing` | `inference.register_existing_artifact` |
| `get_artifact_technical` | `GET /api/inference/artifacts/{id}/technical` | resource template `holdspeak://inference/artifacts/{id}/technical` |
| `activate_model_artifact` | `POST /api/inference/deployments/activate` | `inference.activate_model_artifact` |
| `get_deployment` | `GET /api/inference/deployments/{id}` | resource template `holdspeak://inference/deployments/{id}` |
| `probe_deployment` | `POST .../{id}/probe` | `inference.probe_deployment` |
| `InferenceApplicationService.measure_deployment` | `POST .../{id}/measure` | `inference.measure_deployment` |
| `InferenceApplicationService.try_deployment` | `POST .../{id}/try` | `inference.try_deployment` |
| `set_job_route` | `PUT /api/inference/routes/{job}` | `inference.set_job_route` |
| `set_thought_route` | `PUT /api/thoughts/{id}/inference-route` | `thought.set_inference_route` |

Canonical envelopes are:

```text
GET setup / MCP setup resource        { setup }
GET acquisition / resource            { acquisition }
GET deployment / resource             { deployment }
GET technical artifact / resource     { artifact }
begin/download-and-use                { acquisition, receipt, setup }
cancel                                { acquisition, receipt, setup }
register/activate/route/probe/measure  { receipt, setup, subject? }
error                                 { code, message, recovery, current? }
```

HTTP creation/saga acknowledgement is 202, completed synchronous mutation is
200, stale/payload conflict is 409, recursive schema failure is 400, authority
denial is 403, and missing owner-visible subject is 404. MCP uses the same code,
message, recovery, and current inner objects in its error result. No adapter
coerces strings, numbers, arrays, or nested objects.

Every command body is a recursively closed object with stable `request_id`,
operation-specific fields, and the narrow expected route/deployment/job
revision it mutates. Same request/payload returns immutable effect evidence plus
fresh projection; changed payload returns `request_payload_mismatch`. Stale CAS,
unknown preset/artifact/deployment, incompatible runtime, insufficient disk or
capacity, source-integrity failure, gated-license requirement, and unavailable
destination have fixed codes shared across HTTP and MCP. HTTP status and MCP
error envelopes are golden-fixtured. Events may be lost; GET reconstructs truth.

Cancel is idempotent and owner-only. Technical locator is available only through
the explicit technical projection, never ordinary setup, receipts, events, or
model-facing resources. Internal MODEL_TURN/SERVICE principals receive none of
these owner resources or tools.

## Persistence and authority

Capability Truth preserves today's canonical Config authority for
`thoughts.inference_target_id`, meeting placement, and dictation runtime. It
does not dual-write or mirror those routes into new tables. A later one-way
route migration requires a durable migration marker, exact Config-to-SQLite
mapping, restart/rollback policy, and an explicit end to Config authority;
indefinite dual-write is forbidden.

After that ruled migration, use SQLite for mutable local setup authority:

```text
inference_setup_head
  revision, catalog_revision, updated_at

inference_model_artifacts
  artifact_id, format, source_kind, source_repository, source_revision,
  manifest_json, manifest_sha256, installed_bytes, state, local_locator,
  created_at, verified_at

inference_model_acquisitions
  job_id, request_id, request_sha256, intent, preset_id, catalog_revision,
  recipe_sha256, source_plan_json, source_plan_sha256, content_identity,
  state, verified_bytes, transport_bytes, bytes_total, staging_locator,
  artifact_id, activation_state, expected_route_revision, activation_receipt_json,
  error_code, revision, created_at, updated_at

inference_deployments
  deployment_id, destination_id, runtime_id, runtime_revision, artifact_id,
  model_identity, context_ceiling, recommended_context, capability_json,
  capability_sha256, configuration_revision, active, created_at, updated_at

inference_job_routes
  job, deployment_id, revision, updated_at

refinement_thought_inference_routes
  thought_id, deployment_id, revision, updated_at

inference_calibrations
  calibration_id, deployment_id, deployment_revision, hardware_profile_sha256,
  measurement_json, measurement_sha256, created_at

inference_runtime_leases
  lease_id, operation_id, deployment_revision_id, runtime_revision,
  resident_bytes, working_bytes, context_bytes, state, host_epoch,
  expires_at, created_at, updated_at

inference_setup_actions
  request_id, request_sha256, action, prior_revision, post_revision,
  receipt_json, created_at
```

Secrets remain in the existing key store. Local locators are owner-private and
excluded from sync/API projections. Artifact/deployment/action integrity is
validated before projection or execution; corrupt proof refuses rather than
falling back to mutable Config.

`inference_deployments.configuration_revision` is mutable setup state and must
never be confused with the canonical immutable execution `DeploymentRevision`
captured by the runner.

### Sync classification

| Fact | Sync law |
|---|---|
| artifact-ledger bytes/locators and all v2 locators | hub-local; never sync |
| legacy v1 `DeploymentRevision.model_path` | explicit preserved historical sync exception; never copied into new setup projections/receipts |
| acquisitions/staging/jobs | hub-local; never sync or resume remotely |
| hardware profiles/observations/calibrations | hub-local |
| setup actions and job/per-Thought routes | hub-local in this design |
| live invocations, continuity, attempts, reviews | existing Phase 141 hub-local law |
| immutable nonsecret v2 execution metadata | may sync only for historical receipt resolution |

Two hubs may choose different routes and independently infer, as Phase 141
already discloses. Sync import never downloads, activates, probes, measures,
starts, resumes, reconciles, Stops, or otherwise triggers model/network work.
A synced Thought whose referenced deployment is unavailable locally refuses by
name; it never auto-downloads or retargets.

## Concurrency, restart, and updates

* A request ID plus canonical payload hash gives exact idempotency.
* Same request and payload returns the same effect receipt plus fresh current
  projection; changed payload refuses.
* Every mutation uses only its relevant expected revision: acquisition job,
  artifact ledger, deployment head, hub job route, or per-Thought route.
  Unrelated setup changes never invalidate a long-running acquisition.
* One artifact identity has at most one nonterminal acquisition.
* Restart rehydrates downloads from durable jobs and on-disk staging facts.
* A byte range is resumed only when source commit, ETag/hash, length, and local
  prefix evidence still agree. Otherwise the job restarts that file safely.
* Unknown physical completion becomes `indeterminate`; it is never declared
  verified without a complete manifest pass.
* Catalog updates never replace an installed artifact or active deployment.
  They offer an explicit update, installed beside the previous revision.
* Removing a deployment cannot strand a job route or an in-flight invocation.
* Changing runtime packages invalidates inspection/calibration by runtime
  revision but does not delete model bytes.

## Privacy, security, and supply chain

* Hardware inspection and local catalog matching remain on the hub.
* Model download is owner-triggered network egress and names repository/bytes.
* Repository source is allow-listed by the selected catalog entry; custom
  sources require expert registration and identical verification.
* Credentials never enter URLs, browser storage, receipts, logs, or model files.
* Downloaded content is data, never executed setup code.
* Safe model formats and required metadata files are allow-listed per runtime.
* Runtime drivers run under the kernel principal/operation context and receive
  no owner token, MCP sidecar, Settings mutation authority, or arbitrary file
  access.
* Prompt, Note, attachments, and tool results remain untrusted data under the
  existing context delimiter and capability laws.
* Cloud egress is computed from exact admitted data classes and actual child
  receipts, not from a provider logo.

## Delivery slices

### Inference Instrument I — Capability Truth

This is a separate next phase, not an insertion into Phase 141:

1. **Authority and compatibility:** freeze v1 revision compatibility, future v2
   law, Config/SQLite boundary, runtime-factory seam, sync/privacy classification,
   and exact setup DTO.
2. **Bounded inspection:** stable/volatile hardware facts and runtime/artifact
   inspection with nullable reasons; zero model load/network/write.
3. **Packaged verified catalog:** canonical schema/signature fixtures and zero to
   three platform/runtime-compatible entries; mutable/unverified examples never
   project. This slice does not label memory fit, **Recommended**, native
   context, measured speed, or readiness from an estimate.
4. **Existing GGUF truth:** report today's configured Thought target/revision and
   distinguish detected, configured, ready, and executable. Detected MLX is
   explicitly unsupported for Thoughts until Slice 3.
5. **Read-only application boundary:** one `get_inference_setup`, exact HTTP/MCP
   resource parity, owner-only, zero-write.
6. **Models integration:** consume the server projection, remove browser catalog
   authority, preserve existing mutation endpoints and Config routing, decompose
   the oversized component, and implement the selected-card/fixed-seat grammar
   without enabling nonexistent download actions.
7. **Cold walk and counsel:** real current GGUF, missing dependency/path, no
   model, detected unsupported MLX, restart, 1440/393, and 0/1/2/3 preset truth.

Capability Truth may show a verified preset as informational/upcoming only if no
download command exists; it must not render a disabled or deceptive primary.

### Slice 2 — Durable acquisition and activation

* acquisition ledger, secure staging, progress/cancel/restart, verification;
* GGUF **Download & use** end to end;
* final SQLite deployment creation and Thoughts route-CAS transaction;
* a crash/cancellation-safe hub-local lease that serializes all newly activated
  local-artifact execution before any new physical leaf may run;
* exact receipts and failure recovery.

Here “atomic deployment creation” means the final SQLite activation transaction
inside the already specified filesystem/SQLite saga—not atomic network or
filesystem work.

### Slice 3 — First-class MLX inference

* shared runtime-factory/PromptEngine contract beneath the existing
  `InferenceRunner`/`CanonicalPromptAdapter` waist;
* MLX inspection/tokenization/PromptEngine path under existing runner-owned
  dispatch/cancellation/receipts;
* reuse of Slice 2's mandatory serialized local-execution lease;
* one compatible Quick and Balanced Apple Silicon preset;
* same canonical question/synthesis contract and no UI branch;
* GGUF remains offered on macOS.

### Slice 4 — Context admission and calibration

* model/runtime-specific memory estimator;
* hardware-aware exact 8K/16K/32K context recommendation;
* exact tokenizer-driven per-turn context plan and refusal repair;
* removal of the current silent 6,000-character material cut;
* upgrade of the Slice 2 serialized lease to per-pool capacity-vector-aware
  sharing, compatible-cache ownership, and concurrent-load refusal/queue law;
* optional local calibration with synthetic input;
* Advanced custom context override.

### Slice 4A — Tool Capability Foundation

This is a separately ruled prerequisite before any deployment can project
executable structured tool use:

* authority-specific canonical capability registry derived from the same
  application operations as HTTP/MCP, with owner-only operations impossible to
  project to a model;
* unexportable server-verified `TurnCapabilityLease` bound to exact descriptors,
  schemas, scopes, data classes, placement/egress, owner intent, policy, call/
  result/step/deadline budgets, nonce, epoch, and expiry;
* durable hub-local `ToolTurnController` and turn/model-step/tool-call ledger;
* every model continuation as a separately admitted/receipted `InferenceRunner`
  child and every tool call as a separately Broker-admitted/receipted
  application child;
* evidence-read, candidate-builder, and effect-proposal classes; generic Ask
  never authorizes an effect, and the model never approves its proposal;
* crash/restart/replay/cancellation/indeterminate/sync-inert laws; and
* runtime dialect adapters that translate frozen schemas/results but never
  execute tools or privately loop provider calls.

Until this slice lands, Capability Truth and later runtime slices may show tool
support only as unavailable/candidate qualification metadata. Offline model
evaluation cannot make it executable or owner-visible as qualified.

### Slice 5 — Workbench destination control

* compact ready-deployment chooser;
* persistent hub-local per-Thought override plus `Use default` clear;
* next-turn-only freeze and composite reservation behavior;
* **Set up AI** deep link with draft-preserving return;
* actual placement/context-plan receipt disclosure.

Each slice is independently truthful. No disabled MLX card, fake progress,
estimated readiness presented as measured, or destination chooser that still
executes the old global default is permitted.

## Required tests

### Capability Truth gate (Inference Instrument I only)

1. Existing v1 deployment hashes, serialized rows, replay, current GGUF target
   resolution, Ask execution, and current legacy sync export (including its
   known `model_path`) remain byte/behavior compatible; no new setup projection
   repeats that locator.
2. Setup GET and owner MCP resource return identical closed projections and make
   zero database/Config writes, network calls, model loads, probes, downloads,
   calibration, or inference.
3. Projection is restart-stable except `observed_at` and volatile observation;
   Config remains canonical for Thought/dictation/meeting routes and projection
   never changes it.
4. Hardware/runtime inspection is bounded and covers Apple Silicon, Linux CPU,
   missing/unsupported telemetry, absent dependency, missing/corrupt artifact,
   and nullable reasons without throwing.
5. Detected MLX never projects Thought-ready; current valid GGUF distinguishes
   detected/configured/ready/executable honestly.
6. Catalog union/schema/signature fixtures reject unsafe local entries and
   malformed hosted entries; server returns honestly 0/1/2/3 applicable entries
   without inventing memory fit, recommendation, native context, or measured
   readiness.
7. Existing hosted profile presets retain their profile/Config mutation behavior
   after moving out of browser constants; no hosted ID gains artifact fields.
8. Ordinary projection/DOM/log fixtures contain no secret, environment value,
   absolute artifact/model path, provider credential, or browser-authored fact.
9. 1440/393 component tests enforce one radiogroup/action-seat composition,
   honest unsupported actions, >=44px mobile targets, focus order, and no
   horizontal overflow—without exposing a fake Download/MLX execution action.

The following gates apply only as their named later slices introduce the
capability. They do not block Capability Truth.

### Later slices — domain and service

1. Product/domain services invoke the same application command for MLX, GGUF,
   OpenAI-compatible, paired, and mesh deployments; no runtime branch exists
   above deployment execution.
   Existing v1 deployment hashes/serialization/replay remain byte-identical;
   v2 forgery, mutable-head change after capture, sync roundtrip, and a peer
   without the local artifact preserve or refuse exact historical truth.
2. Hardware profiles cover Apple Silicon unified memory, Linux CPU-only,
   NVIDIA/AMD when genuinely detectable, unsupported architecture, missing
   telemetry, and changing available memory.
3. Preset publication refuses mutable/unresolved source, missing byte count,
   unknown license, incompatible runtime/architecture, zero context, or memory
   policy without a version.
4. Recommendation is deterministic for the same hardware/model/runtime/policy
   revisions and explains every selected tier.
5. MLX folder through GGUF driver and GGUF through MLX driver refuse by exact
   format before load or inference.
6. Context estimates use driver architecture facts; overflow, output reserve,
   exact-boundary, tokenizer mismatch, and attachment whole-set behavior are
   covered.
7. Turn admission freezes deployment and context plan; settings/catalog/runtime
   change before dispatch refuses or uses exact frozen lawful evidence—never
   retargets.
   Exact-plan fixtures include boundary ±1, Unicode, BOS/EOS/chat template,
   response/tool schema overhead, output reserve, tokenizer/template swap,
   provider reserialization, complete attachment containers, and the current
   >6,000-character path with zero silent truncation.
   Altering, omitting, or reordering any plan/request field at the
   `CanonicalPromptAdapter` → `PlannedPromptEngine` boundary refuses before the
   physical generation/provider leaf.
   Slice 2 gates prove no newly activated local artifact reaches a physical leaf
   without the minimal serialized lease and that cancellation/crash releases or
   reconciles it. Slice 4 migration preserves active/restart truth while adding
   concurrent different-model vector refusal, safe same-model reuse,
   cancellation, OOM/unknown load, restart cleanup, runtime update while an old
   lease lives, and zero cross-child DispatchContext binding.

### Later slices — download and supply chain

8. Exact source plan, redirect allow-list, path traversal, symlink, duplicate
   path, size mismatch, hash mismatch, truncated body, oversized manifest,
   unknown file type, and credential-leak cases.
   Signed-catalog fixtures include unknown/rotated keys, rollback, revoked or
   expired entries, mutable refs, LFS mismatch, DNS rebinding, redirect
   credential stripping, count/size/unpacked bombs, custom code/pickle, and
   gated-license exclusion.
9. Cancel before first byte, during source resolution, mid-file, and between
   files reaches `cancelled`. A race after verification starts returns
   `cancellation_too_late` and current truth. Verification/install exposes no
   Cancel; after rename/adoption removal is separate. Installed artifacts are
   never partially visible. “Verified partial kept” is asserted only with valid
   resumable-prefix proof; otherwise the UI names that the file will restart.
10. Crash/restart at every state; valid range resume; changed remote commit/ETag
    restarts safely; ambiguous completion requires verification.
11. Concurrent same-preset requests produce one acquisition; request replay is
    exact; key/payload mismatch refuses; two different artifacts remain isolated.
    Concurrent recipe resolution, two presets converging on one content identity,
    competing route activations, crash after rename/adoption, orphan quarantine,
    and stale route CAS never duplicate bytes or claim **In use**.
12. Download success plus activation failure leaves a verified reusable artifact
    and no false route change.
13. Removal refuses while referenced/live and never recursively targets a broad
    directory.

### Later slices — runtime execution

14. Same canonical prompt/result fixtures through MLX and GGUF drivers; provider
    dialect differs but typed result and receipt requirements do not.
    Factory/physical-leaf spies prove admission → claim → exact DispatchContext
    → existing runner dispatch. Direct setup/factory execution refuses; Probe
    makes zero load/network/inference; Measure/Try-it use ordinary admitted
    children; compatibility uses at most two separately receipted attempts.
15. One physical dispatch per admitted child; cancel/result, timeout/result,
    runtime unload, OOM, malformed structured output, and restart ambiguity.
16. Runtime reports actual model/engine; mutable Settings cannot rename or
    retarget a frozen turn.
17. No runtime can access owner MCP, key store enumeration, Desk repositories,
    setup mutation, or arbitrary tool invocation.

### Later slices — HTTP/MCP and privacy

18. Reciprocal closed schemas, owner-only authority, exact idempotency/errors,
    and no browser-only setup mutation.
19. Projections/receipts contain no keys, Note/context body, local absolute path,
    staging path, provider-native secret, or hardware fact beyond the bounded
    owner projection.
20. Reads perform zero downloads, model loads, inference, calibration, or setup
    writes.
    Capability Truth HTTP/MCP projections are identical and restart-stable except
    timestamped observation; Config remains route authority and no browser
    constant or setup read switches it.

### Later slices — UI/controller

21. Mac shows MLX first and GGUF honestly; Linux shows GGUF first; unsupported
    runtime is absent or named with a real enable action, never selectable fake
    capability.
22. Recommended card changes with hardware profile; inaccessible Deep card
    explains the smaller fit; owner can still inspect Advanced custom choices.
23. One click begins download; verified logical progress is honest; Cancel/Retry and
    restart retain authority; success activates exactly once.
    If transport restarts, UI distinguishes transport bytes from verified
    logical progress rather than forcing a false monotonic percentage.
24. 393 targets are at least 44px, progress has no horizontal overflow, focus
    survives card state transitions, and reduced motion preserves status truth.
25. Workbench changer affects next turn only; in-flight receipt remains original;
    setup deep-link round trip preserves Note, answer, focus, and Thought ID.
26. Presets are one labelled radiogroup with one fixed action seat; arrows move
    selection, Space selects, and selection sends zero mutation.
27. Setup completion never auto-navigates; explicit Return restores exact dirty
    Note, answer, caret, focus, and authoritative Workbench refresh.

## Required glass

### Capability Truth glass

Use isolated HOME/database roots and actual application HTTP/MCP reads. Capture
1440 × 900 and 393 × 900 for: current valid GGUF; missing dependency/path; no
model; detected MLX explicitly unsupported for Thoughts; packaged hosted/local
catalog with 0/1/2/3 applicable entries; Apple Silicon and Linux CPU hardware
facts with nullable reasons; Advanced/current destination truth. Assert one
setup request, zero write/network/load/inference side effects, Config unchanged,
no fake recommendation/download primary, no absolute locator/secret, >=44px
targets, focus/keyboard truth, and no horizontal overflow.

### Later-slice glass

Use isolated HOME/database/model roots and mocked small byte artifacts for the
ordinary automated walk; real-model metal walks are separately opt-in. The
following applies only when Slices 2–5 introduce each capability.

Capture at 1440 × 900 and 393 × 900:

1. Apple Silicon projection: MLX recommended, Mac GGUF under **Other local
   formats**, exact explanation and one selected-card/action-seat geometry;
2. Linux CPU projection: GGUF recommended, no invented GPU capability; separate
   proven NVIDIA/ROCm acceleration capture when claimed;
3. local cards resting, radio keyboard state, technical disclosure, resolving,
   byte progress, transport restart, verifying, installing, cancelled, network/
   disk/integrity/activation failure, and Ready/In use;
4. incompatible existing MLX/GGUF selection with one useful repair;
5. hardware-too-small Deep choice with Balanced alternative;
6. Workbench persistent pre-action destination row on Note and Interview at both
   widths, selector, in-flight immutable actual target versus changed next
   target, composite freeze, and post-turn actual receipt;
7. no-model **Set up AI** deep link and successful return with draft intact;
8. oversized context refusal naming exact limiting attachment and available
   larger deployment;
9. restart mid-download and restart with a review-ready Thought, proving neither
   download nor inference duplicates; and
10. keyboard/screen-reader traversal, coarse progress announcements, 200% zoom,
    reduced motion, every 393 target >=44px, and one visual primary per state.

Network/authority assertions prove setup GET performs zero download/load/
inference/network, no acquisition starts before the gesture, Workbench never
fetches artifact/path/key details, and ordinary DOM/log/API projections contain
no secret or absolute locator.

Real hardware acceptance matrix:

* one Apple Silicon machine at a modest unified-memory tier;
* one Apple Silicon machine capable of the Deep tier;
* one Linux CPU-only machine;
* one Linux accelerated machine when that runtime is claimed;
* one custom OpenAI-compatible endpoint; and
* one unavailable/offline endpoint.

The metal record captures model/runtime revision, machine profile hash,
recommended tier, measured throughput, peak memory when available, exact context
plan, and actual placement receipt. Scores are never compared across different
runtimes as if they were controlled benchmarks.

## Kill criteria

Capability Truth stops on any v1 execution/hash regression, Config route
mutation/dual-write, setup-read side effect, fake MLX/GGUF readiness, unsafe or
browser-authoritative catalog entry, HTTP/MCP projection drift, locator/secret
leak, or dishonest first-width/393 glass.

For later slices, each criterion becomes active when that slice introduces the
named capability. Capability Truth is not blocked merely because acquisition,
MLX execution, exact token admission, resource leases, or Workbench routing do
not exist yet. Do not ship an applicable slice if any of these is true:

* a product component contains an MLX/GGUF/provider execution branch;
* a second executable deployment-revision registry or runtime dispatch waist
  bypasses the existing Phase 131 revision/runner path;
* a discovered model appears selectable before a compatible executable runtime
  exists;
* setup readiness invokes a model without an explicit owner test action;
* a download begins before the owner gesture or installs unverified bytes;
* filesystem/network work is described as atomic with SQLite, disk preflight is
  absent, gated terms are silently accepted, or Pause appears without a durable
  pause/resume state machine;
* a preset hides source, license, bytes, material memory estimate, or boundary;
* “Automatic” cannot explain its hardware/model/runtime inputs;
* context admission uses characters, filenames, or configured maximum instead
  of the exact tokenizer plan;
* a surface claims exact/native/recommended context before runtime proof exists;
* important Note/attachment material is silently truncated;
* changing destination mutates an in-flight turn;
* a runtime reads mutable Settings after deployment freeze;
* local model selection grants tool/effect authority;
* Workbench contains setup infrastructure or more than one primary;
* Models renders more than one primary action seat or hides the next-turn
  destination on either 393 tab;
* HTTP and MCP can produce different setup/deployment effects; or
* sync/download/restart starts or repeats inference.

## Explicit non-goals

* a public model marketplace or arbitrary repository browser;
* silent background model downloads or automatic model replacement;
* automatic benchmark competition between providers;
* training, fine-tuning, conversion, or quantization inside HoldSpeak;
* image/audio model inputs merely because an MLX artifact supports them;
* distributing model licenses or asserting a license beyond source metadata and
  reviewed catalog policy;
* global autonomous model routing in the first delivery slices;
* giving internal models the owner MCP catalog or setup commands; and
* making remote inference globally exclusive across synced hubs.

## Settled implementation implications

1. The existing `this_machine` destination must stop meaning “the one meeting
   GGUF path” only after the v2 execution/deployment migration lands. Capability
   Truth reports the current limitation without changing it. The north-star
   destination's active definition may then use any locally supported runtime.
2. Existing `meeting.intel_realtime_model`, `thoughts.inference_target_id`, and
   dictation runtime fields remain canonical through Capability Truth. Their
   later one-way migration is explicit and never an indefinite dual write.
3. `build_intel_for_revision` evolves toward a runtime-factory registry keyed by
   frozen v2 capability while `InferenceRunner` and `CanonicalPromptAdapter`
   retain dispatch; no Workbench conditional or second waist is added.
4. The current MLX dictation runtime contributes loader knowledge but is not
   promoted wholesale into Thought orchestration.
5. Models setup mutations move behind a shared application service and durable
   SQLite authority so downloads, deployment activation, routing, and receipts
   can be atomic and restart-safe.
6. Context recommendation and per-turn admission live server-side. The browser
   renders facts and choices; it does not estimate memory or tokens.
7. Curated model identities are catalog data with pinned revisions, not JSX
   constants. Hosted and local presets use the same presentation grammar while
   preserving different acquisition and egress semantics.
8. Existing deployment v1 hashes and rows remain immutable/executable. V2 is
   additive and locator-free, and exists only once its execution consumer lands.
9. Runtime capacity needs a hub-local lease manager; a recommendation alone is
   never concurrent-load authority.

## Source notes for catalog investigation

These sources establish current artifact availability only. They do not approve
a preset until the catalog process freezes an immutable revision, complete
manifest, runtime compatibility, size, license, and hardware policy.

* MLX Community Qwen3.5 4B MLX 4-bit:
  <https://huggingface.co/mlx-community/Qwen3.5-4B-MLX-4bit>
* MLX Community Qwen3.8 27B MLX 4-bit:
  <https://huggingface.co/mlx-community/Qwen3.8-27B-4bit>
* Unsloth Qwen3.5 4B GGUF family:
  <https://huggingface.co/unsloth/Qwen3.5-4B-GGUF>
* MLX Community model index:
  <https://huggingface.co/mlx-community/models>

## Owner ruling requested

### Guru Meditation review record — 2026-08-20

Three independent read-only reviews initially returned **AMEND**. Their findings
were reconciled into this same canonical artifact rather than stored as optional
alternatives:

* architecture/authority closed the v1/v2 deployment law, existing-runner waist,
  acquisition saga and catalog trust, exact request/token binding, route/sync
  authority, transport parity, and concurrent runtime resource leases;
* implementation/scope separated read-only Capability Truth from later
  acquisition/MLX/context/Workbench slices, preserved Config and v1 behavior,
  aligned the exact engine-factory seam, and split hosted/local catalog schemas;
* cold-owner craft settled preset versus context vocabulary, one fixed action
  seat, Mac MLX plus progressive GGUF, proven Linux runtime copy, disk/license/
  cancellation truth, persistent pre-Ask per-Thought routing, and draft-preserving
  setup return at both widths.

The amended artifact then received **RATIFY** from all three reviewers with no
remaining blocker. This is technical/product design ratification, not an owner
status flip or implementation claim.

Ratify the following product decisions together:

1. **Inference Instrument** is the shared platform name and architectural waist.
2. Mac offers MLX first and GGUF alongside it; Linux offers GGUF first.
3. Local presets are Quick/Balanced/Deep experiences backed by a small reviewed
   catalog, not an open model marketplace; context is separately named by exact
   8K/16K/32K/Custom choices.
4. **Download & use** is one informed, confirmation-free owner action.
5. Hardware-aware context recommendation and exact per-turn token admission are
   required platform behavior, not optional polish.
6. Models uses one radiogroup and one fixed action seat. Workbench gains a
   persistent hub-local per-Thought next-turn override plus **Use default**, but
   no setup machinery.
7. Runtime format, acquisition, tool authority, and product domain remain four
   separate concerns joined only through frozen deployment and kernel receipts.
8. Capability Truth ships first as a read-only, Config-compatible projection;
   later authority migrations cannot destabilize Phase 141 or v1 execution proof.
