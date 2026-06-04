# Plugin Authoring

> A meeting-intel **plugin** turns a saved meeting's transcript into a
> structured, reviewable artifact — decisions, requirements, a risk
> register, an architecture diagram. The transcript is scored for
> intent, a chain of plugins is selected, and each plugin calls your
> configured LLM to produce typed output that the web UI renders
> read-only at `/history`.

This guide documents the contract you satisfy to write one, and the
testing surface you get for free. It is the public companion to the
internal design RFC,
[`internal/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`](internal/PLAN_ARCHITECT_PLUGIN_SYSTEM.md).
For the analogous *activity-connector* contract, see
[Connector Development](./CONNECTOR_DEVELOPMENT.md).

---

## TL;DR

A plugin is a Python object that:

1. Declares `id`, `version`, and (optionally) `kind`,
   `execution_mode`, and `required_capabilities` as attributes.
2. Implements `run(context: dict) -> dict` — build a JSON-only prompt,
   call the configured intel, parse + validate the response, and
   return structured output carrying a `confidence_hint`.
3. Registers a **synthesis renderer** so its artifact shows up in the
   web `/history` view.
4. Joins one or more **plugin chains** (by profile and/or intent) so it
   fires on the right meetings.

The canonical reference is
[`holdspeak/plugins/builtin/decision_capture.py`](../holdspeak/plugins/builtin/decision_capture.py)
— a real, LLM-backed plugin in ~200 lines. Read it alongside this
guide.

---

## Plugin lifecycle

```
   ┌───────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │  declare  │ → │  route   │ → │   run    │ → │  persist │ → │  render  │
   │ (attrs +  │   │ (chain   │   │ (prompt→ │   │ (artifact│   │ (/history│
   │   run)    │   │  select) │   │  LLM→    │   │  store)  │   │   view)  │
   └───────────┘   └──────────┘   │  parse)  │   └──────────┘   └──────────┘
                                  └──────────┘
```

- **Declare** — your class exposes `id`/`version` (required) plus the
  optional `kind`/`execution_mode`/`required_capabilities` attributes
  the host reads with `getattr`.
- **Route** — the router scores the transcript's intents and assembles
  a plugin chain for the meeting's profile + active intents.
- **Run** — the host calls `run(context)` inside a timeout, after the
  actuator gate and the capability gate pass. You build a prompt, call
  the LLM, and return a dict.
- **Persist** — the host stores your output as a canonical artifact
  keyed by an idempotency hash (a re-run on the same window is a no-op).
- **Render** — your registered renderer turns the stored output into a
  Markdown block in the read-only `/history` view.

Plugins run on **saved/recorded** meetings, never live audio.

---

## The `HostPlugin` contract

The protocol is in
[`holdspeak/plugins/host.py`](../holdspeak/plugins/host.py):

```python
class HostPlugin(Protocol):
    """Minimal plugin contract for host execution."""

    id: str
    version: str

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        ...
```

`PluginHost.register()` only requires a non-empty `id` and a `run`
method. Everything else (`kind`, `execution_mode`,
`required_capabilities`) is read defensively via `getattr` with a
default, so you declare only what you need.

### Attribute reference

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | `str` | **yes** | Unique, stable. Used as the artifact + idempotency key and the chain entry. Lowercase snake_case by convention (e.g. `decision_capture`). |
| `version` | `str` | **yes** | Semver-ish. Recorded on every run result. |
| `kind` | `str` | no | Artifact category — see below. Defaults to unset. |
| `execution_mode` | `str` | no | `"inline"` (default) or `"deferred"`. See "Execution mode". |
| `required_capabilities` | `list[str]` | no | Capabilities the host must have enabled, e.g. `["llm"]`. See "The `llm` capability gate". |

### `kind`

`kind` labels what the plugin produces; it drives the actuator gate and
is a hint for rendering. The built-ins use these values:

| `kind` | Meaning | Example built-ins |
|---|---|---|
| `synthesizer` | Structured intermediate data (decisions, requirements, milestones) | `decision_capture`, `requirements_extractor`, `milestone_planner` |
| `artifact_generator` | A diagram or formatted document | `mermaid_architecture`, `adr_drafter`, `stakeholder_update_drafter` |
| `validator` | Flags gaps or issues | `action_owner_enforcer`, `scope_guard` |
| `signals` | Extracted signals/intelligence | `customer_signal_extractor` |
| `actuator` | Proposes an external side effect (approval-gated) | `followup_ticket_actuator` |

**Actuators propose; they never act on their own.** A plugin whose
`kind` is `actuator` returns an `ActuatorProposal` from `run()` — a
*description* of a side effect — which the host records (status
`proposed`); the effect only happens after an explicit human **approval**
and the governance gate, performed by a separate guarded executor. This
is its own topic — see [Actuators](#actuators) below before authoring one.

### Execution mode

`execution_mode` decides whether the host runs your plugin synchronously
or queues it:

- `"inline"` (default) — `run()` executes during window dispatch and the
  result returns immediately.
- `"deferred"` (synonyms accepted: `"queued"`, `"queue"`, `"heavy"`) —
  the run is queued as a `DeferredPluginRun` and processed later by the
  background worker (`PluginHost.process_next_deferred_run()`). The
  dispatch call returns status `queued` straight away.

Any plugin that makes a real (slow) LLM call should be `deferred` — that
is what `decision_capture` does. Use `inline` only for cheap,
deterministic work.

### `run(context) -> dict`

`context` is a plain `dict` (not a typed envelope), assembled by the
dispatcher in
[`holdspeak/plugins/dispatch.py`](../holdspeak/plugins/dispatch.py).
The fields you can rely on:

| Key | Type | Notes |
|---|---|---|
| `transcript` | `str` | The window's transcript text. Your primary input. |
| `active_intents` | `list[str]` | Intents that fired for this window (subset of the supported intents). |
| `profile` | `str` | The meeting's profile (e.g. `balanced`, `architect`). |
| `meeting_id` | `str` | The owning meeting. |
| `window_id` | `str` | The transcript window. |
| `tags` | `list[str]` | Window metadata tags, if any. |
| `project_name` / `project` | `str` | Associated project, if detected. |

Context providers registered with the host
(`register_context_provider`) may add more keys; read defensively and
default everything. Your return value is a `dict` — the convention is
documented next.

---

## The reference run pattern

Every LLM-backed built-in follows the same four steps. Here is
`decision_capture`, condensed.

**1 — Build a JSON-only prompt.** Pin the exact output shape in the
system prompt and demand a single fenced ```json block, no prose:

````python
_SYSTEM_PROMPT = (
    "You capture the decisions and open questions from a meeting transcript.\n"
    ...
    "Output format — strictly: a single fenced code block tagged ```json "
    "containing an object of the form:\n"
    '{"decisions": [{"decision": "...", "rationale": "why, or null"}], '
    '"open_questions": ["..."]}\n'
    "Output only the JSON block — no prose, no extra fences."
)
````

**2 — Call the configured intel.** Use the shared provider so the
plugin honors whatever LLM the user configured (in-process GGUF, MLX, or
any OpenAI-compatible endpoint). Build it lazily and cache it:

```python
def _call_intel(self, messages: list[dict[str, str]]) -> str:
    if self._intel_call_override is not None:      # test seam — see "Testing"
        return self._intel_call_override(messages)
    if self._cached_provider is None:
        from ...intel import build_configured_meeting_intel  # lazy: optional deps
        self._cached_provider = build_configured_meeting_intel()
    return self._cached_provider._chat_completion_text(
        messages, temperature=0.2, max_tokens=800,
    )
```

`build_configured_meeting_intel()`
([`holdspeak/intel`](../holdspeak/intel/__init__.py)) returns the
configured provider; `_chat_completion_text(messages, *, temperature,
max_tokens)` takes OpenAI-style `{"role", "content"}` messages and
returns the raw response text.

**3 — Parse + validate.** Pull the JSON out of the fenced block (with a
brace-scan fallback), `json.loads` it, and normalize — never trust the
shape. Return `None` on anything unparseable so `run` can emit the
failure shape:

````python
fence = _JSON_FENCE_RE.search(text)          # r"```(?:json)?\s*\n(.*?)```"
candidate = fence.group(1) if fence else text[text.find("{"): text.rfind("}") + 1]
obj = json.loads(candidate)                  # guarded by try/except
# ... coerce each field, drop empties ...
````

**4 — Return structured output.** Two shapes by convention:

- **Success** — your typed keys plus a `summary` string and
  `confidence_hint` of `1.0`:

  ```python
  return {
      "summary": f"{len(decisions)} decision(s); {len(open_questions)} open question(s).",
      "decisions": decisions,
      "open_questions": open_questions,
      "confidence_hint": 1.0,
      "active_intents": active_intents,
  }
  ```

- **Failure** — a `summary` explaining why and `confidence_hint` of
  `0.0`, with the typed keys **absent**:

  ```python
  return {"summary": reason, "confidence_hint": 0.0, "active_intents": active_intents}
  ```

Catch exceptions from the intel call and turn them into the failure
shape — a plugin must never raise out of `run`. `confidence_hint` is a
float in `[0.0, 1.0]` that downstream surfaces use to rank/triage
artifacts; emit `0.0` for failures and a calibrated value otherwise.

The host wraps the whole call in a timeout and records a
`PluginRunResult` with `status` ∈ `success | error | timeout | deduped |
blocked | queued`. A re-run on the same `(meeting, window, plugin,
transcript_hash)` is deduped automatically.

---

## The `llm` capability gate

A plugin that needs the LLM declares it:

```python
class DecisionCapturePlugin:
    required_capabilities: list[str] = ["llm"]
```

At dispatch the host compares each required capability against its
`enabled_capabilities` set. If any is missing, the plugin is **not run**
— it returns status `blocked` with `error="Missing capabilities: llm"`,
duration `0.0`, no output. "Blocked" is a clean skip, not a failure:
the meeting still completes; the artifact simply isn't produced.

In production the host's capabilities are resolved from the user's
config: `resolve_llm_capability(config.meeting)` decides whether an LLM
endpoint is actually configured, and only then is the host built with
`enabled_capabilities={"llm"}` (see
[`holdspeak/web_runtime.py`](../holdspeak/web_runtime.py)). So with no
endpoint configured, every `llm`-gated plugin is uniformly skipped — by
design.

---

## Rendering the artifact

Stored output is rendered for the read-only `/history` view by
[`holdspeak/plugins/synthesis.py`](../holdspeak/plugins/synthesis.py).
Two registries connect a plugin to its renderer:

```python
# 1. plugin id  →  artifact type
_ARTIFACT_TYPE_BY_PLUGIN: dict[str, str] = {
    ...
    "decision_capture": "decisions",
    ...
}

# 2. artifact type  →  renderer function
_ARTIFACT_RENDERERS: dict[str, Callable[[_RenderContext], _Rendered]] = {
    ...
    "decisions": _render_decisions,
    ...
}
```

A renderer takes a `_RenderContext` (which carries `output` — your
`run` return value) and returns `_Rendered`, i.e.
`Optional[tuple[str, dict[str, Any]]]`:

- the **first** element is the inner Markdown block for the artifact
  body, and
- the **second** is extra structured keys to attach to the artifact's
  JSON payload.

Return `None` to fall back to the default rendering.

```python
def _render_decisions(ctx: _RenderContext) -> _Rendered:
    decisions = [d for d in (ctx.output.get("decisions") or []) if isinstance(d, dict)] or None
    open_questions = [str(q).strip() for q in (ctx.output.get("open_questions") or []) if str(q).strip()] or None
    if not (decisions or open_questions):
        return None
    extra: dict[str, Any] = {}
    if decisions:
        extra["decisions"] = decisions
    if open_questions:
        extra["open_questions"] = open_questions
    return _decision_body(decisions, open_questions), extra
```

**To wire up a new plugin's rendering:**

1. Add a `your_plugin_id -> "your_artifact_type"` entry to
   `_ARTIFACT_TYPE_BY_PLUGIN`.
2. Write a `_render_*(ctx) -> _Rendered` function.
3. Register it under your artifact type in `_ARTIFACT_RENDERERS`.

If you skip this, the artifact still persists and renders with the
default body — but a bespoke renderer is what makes it readable.

---

## Joining a chain

Which plugins fire on a meeting is decided by the router,
[`holdspeak/plugins/router.py`](../holdspeak/plugins/router.py). The
transcript is scored against the supported intents:

```python
SUPPORTED_INTENTS = ("architecture", "delivery", "product", "incident", "comms")
```

The chain is then assembled from two maps:

```python
PROFILE_PLUGIN_BASE_CHAINS: dict[str, list[str]] = {
    "balanced":  ["requirements_extractor", "action_owner_enforcer", "decision_capture"],
    "architect": ["requirements_extractor", "mermaid_architecture", "adr_drafter"],
    "delivery":  ["action_owner_enforcer", "milestone_planner", "dependency_mapper"],
    "product":   ["scope_guard", "customer_signal_extractor"],
    "incident":  ["incident_timeline", "risk_heatmap", "stakeholder_update_drafter"],
}

_INTENT_PLUGIN_CHAIN: dict[str, list[str]] = {
    "architecture": ["requirements_extractor", "mermaid_architecture", "adr_drafter"],
    "delivery":     ["action_owner_enforcer", "milestone_planner", "dependency_mapper"],
    "product":      ["scope_guard", "customer_signal_extractor"],
    "incident":     ["incident_timeline", "runbook_delta"],
    "comms":        ["stakeholder_update_drafter", "decision_announcement_drafter"],
}
```

`build_plugin_chain(profile, active_intents)` prepends `project_detector`,
appends the profile's base chain, extends with each active intent's
chain, and de-dupes while preserving order. To make a new plugin fire,
add its `id` to the appropriate profile base chain and/or intent chain.

> **⚠ Routing ripple — update tests in lockstep, do not silence.**
> Adding (or suppressing) a plugin id in a chain breaks three test
> surfaces that assert the exact chains:
>
> - `tests/unit/test_intent_dispatch.py` — chain constants + per-window
>   plugin counts,
> - `tests/unit/test_intent_pipeline.py` and
>   `tests/unit/test_multi_intent_routing.py` — full-pipeline tests that
>   register the *union* of plugin ids as test doubles.
>
> Update these to reflect the new expected chains in the same change.
> A `-k`-filtered green that hides the diff is a regression waiting to
> ship.

---

## Registration

Built-ins are registered onto the host by `register_builtin_plugins()`
in
[`holdspeak/plugins/builtin/__init__.py`](../holdspeak/plugins/builtin/__init__.py),
which walks a table of `(plugin_id, kind)` pairs and calls
`host.register(YourPlugin())` for each. To add a first-party plugin:

1. Write the plugin class under `holdspeak/plugins/builtin/`.
2. Add it to the registrar's real-plugin map so a real instance is
   constructed and registered.
3. Wire its renderer (above) and its chain membership (above).

Editing core is the path for a **first-party** plugin. To ship a plugin
*without* editing core, package it as a **plugin pack** (below).

---

## Plugin packs

A pack lets a plugin ship outside the built-in tree — discovered and
registered at startup, mirroring the connector-pack system. The contract
is a manifest plus a factory; the loader is
[`holdspeak/plugin_pack_loader.py`](../holdspeak/plugin_pack_loader.py)
and the manifest SDK is
[`holdspeak/plugin_sdk.py`](../holdspeak/plugin_sdk.py).

A pack is a single `.py` file that exports two names:

```python
from holdspeak.plugin_sdk import validate_manifest

MANIFEST = validate_manifest({
    "id": "my_plugin",            # ^[a-z][a-z0-9_]{0,31}$, unique
    "label": "My Plugin",
    "version": "0.1.0",           # MAJOR.MINOR.PATCH
    "kind": "synthesizer",        # synthesizer|validator|artifact_generator|signals|detector
    "required_capabilities": ["llm"],   # optional; gates execution
    "execution_mode": "deferred",        # inline (default) | deferred
    "intents": ["incident"],             # chain hints (see note below)
    "profiles": ["balanced"],
})

class MyPlugin:
    id = "my_plugin"
    version = "0.1.0"
    kind = "synthesizer"
    required_capabilities = ["llm"]
    def run(self, context): ...

def create_plugin():            # zero-arg factory → a HostPlugin instance
    return MyPlugin()
```

`validate_manifest` collects **every** problem before raising
`PluginManifestError` (each is a `ManifestError` with a stable `code` —
`id_format`, `version_format`, `unknown_kind`, `unknown_capability`,
`invalid_execution_mode`, `unknown_profile`, `unknown_intent`), so you fix
all issues in one pass. `actuator` **is** a valid `kind` (see
[Actuators](#actuators)); a manifest may declare one, but executing its
proposals is approval- and gate-controlled.

**Discovery.** Drop the file into `~/.holdspeak/plugin_packs/`
(override with `HOLDSPEAK_USER_PLUGIN_PACKS_DIR`). At startup the loader
imports each `.py` file, re-validates its `MANIFEST`, checks for a callable
`create_plugin`, and registers the produced plugin on the host alongside
the built-ins. Discovery is honest, not sandboxed — a file under your home
dir is code you trust — but it **never crashes the runtime**: a bad pack
(import error, missing manifest/factory, invalid manifest, id colliding
with a built-in or another pack, id/manifest mismatch) is surfaced as a
structured `DiscoveryError` and skipped. First-party/built-in ids always
win a collision.

> **Chain hints are declarative today.** A pack registers on the host so
> it can execute by id, and its `profiles`/`intents` record where it
> *wants* to fire — but wiring those hints into the live router chains is
> still pending. Until then a pack plugin runs when invoked by id; the
> built-in routing chains above are unchanged.

The committed example at
[`tests/fixtures/plugin_packs/example_user_pack.py`](../tests/fixtures/plugin_packs/example_user_pack.py)
is a complete, working pack.

### Disabling a plugin per project

A team can suppress specific plugins without code: list their ids in
`MeetingConfig.disabled_plugins` (the `meeting.disabled_plugins` config
key). At dispatch a disabled id is recorded as a `skipped` run — distinct
from a capability-`blocked` or a failed run — and never invoked. The
*built* chain is unchanged (the skip is in the *executed* set), so this is
a runtime suppression, not a routing change. An empty list (the default)
runs every chain-selected plugin, exactly as before.

---

## Testing

The contract is built for cheap unit tests — the LLM is injected, so no
network or model is needed.

**Inject a fake intel call** via the plugin's constructor seam
(`intel_call`), returning a canned response string:

````python
from holdspeak.plugins.builtin.decision_capture import DecisionCapturePlugin

def _plugin(response):
    return DecisionCapturePlugin(intel_call=lambda _messages: response)

_GOOD_JSON = """```json
{"decisions": [{"decision": "Adopt the new API gateway", "rationale": "Centralizes auth"}],
 "open_questions": ["Who owns the migration?"]}
```"""
````

**Assert both shapes** — the success keys + `confidence_hint == 1.0`,
and that an unparseable response yields the failure shape with the typed
keys absent:

```python
def test_run_success() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "We made some calls."})
    assert out["confidence_hint"] == 1.0
    assert out["decisions"][0]["decision"] == "Adopt the new API gateway"

def test_run_unparseable_is_failure() -> None:
    out = _plugin("no json here").run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "decisions" not in out
```

**Assert the capability gate** at the host level — without the `llm`
capability enabled, your plugin is `blocked`:

```python
def test_host_blocks_without_llm_capability() -> None:
    host = PluginHost(default_timeout_seconds=0.5)   # no enabled_capabilities
    register_builtin_plugins(host)
    result = host.execute(
        "decision_capture",
        context={"transcript": "We decided things."},
        meeting_id="m-1", window_id="w-1", transcript_hash="abc",
    )
    assert result.status == "blocked"
    assert result.error == "Missing capabilities: llm"
```

See
[`tests/unit/test_decision_capture_plugin.py`](../tests/unit/test_decision_capture_plugin.py)
for the full set.

### The "shipped" bar

A plugin is done — per the RFC's definition-of-done — only when it has
**all** of:

- [ ] A real `run()` that calls the configured intel (not a placeholder
      that fabricates output).
- [ ] A real downstream effect — the artifact persists and is fetched
      by the history view.
- [ ] A registered renderer so the artifact is readable at `/history`.
- [ ] Chain membership so it actually fires on the right meetings.
- [ ] Unit coverage (success + failure + capability gate) **and** the
      routing/pipeline tests updated in lockstep.

All 14 built-ins clear this bar today.

---

## Actuators

An **actuator** is the plugin system's third kind. Where an
`artifact_generator` emits read-only structured data, an actuator
proposes an **external side effect** — file a ticket, post a message,
open a PR comment. Because that *leaves the machine*, actuators are built
around one invariant:

> **No external side effect occurs without an explicit, audited,
> per-action human approval — and what executes is exactly what was
> previewed.**

The contract enforces that invariant by splitting "decide what to do"
from "do it":

```
 actuator.run()        human          guarded executor
 ─────────────►  proposal  ──────►  approve  ──────►  execute  ──► audit
   (proposes)    (persisted)      (HS approval UI)   (connector)
```

### What an actuator returns: `ActuatorProposal`

An actuator's `run(context)` returns a dict that parses into an
[`ActuatorProposal`](../holdspeak/plugins/actuators.py) — a *description*
of the side effect, never the effect itself:

| Field | Meaning |
|---|---|
| `target` | The system the effect lands on (`github` / `jira` / `outbox` / …). |
| `action` | The verb (`create_issue`, `write_followup_ticket`, …). |
| `preview` | A human-readable description of exactly what will happen. |
| `payload` | The machine representation of the effect — the **parity source of truth**. |
| `reversible` | Whether the effect can be undone (shown to the approver). |
| `required_capabilities` | Capabilities the *execution* needs. |

`run()` **must not reach out** — building the proposal is all it does. If
there's nothing to propose, raise; the host records a plain `error` (no
half-formed proposal, no side effect).

### Lifecycle + the gates

A proposal moves through a strict lifecycle, every transition audited:

```
proposed ──► approved ──► executed
   │            │     └──► failed ──► approved  (retry)
   └──► rejected (terminal)
```

Three independent gates stand between a proposal and a side effect:

1. **Capability (`actuator`)** — to even *propose*, the host must have
   `actuator` in `enabled_capabilities`. It's off by default, so a
   registered actuator is `blocked` until an operator opts in.
2. **Human approval** — execution acts only on an `approved` proposal.
   Approve/reject happens in the meeting UI (or
   `POST /api/meetings/{id}/proposals/{pid}/decision`); approving records
   `decided_by` + an audit entry and performs **no** side effect.
3. **Governance (`MeetingConfig`)** — `allow_actuators` is the master
   switch (default `False`); `allowed_actuators` is a per-project
   allow-list of actuator ids. **Default-safe:** off + empty ⇒ no
   external side effect ever runs, even for an approved proposal.

### The guarded executor

[`ActuatorExecutor`](../holdspeak/plugins/actuator_executor.py) is the one
place a side effect happens. `execute(proposal_id)` runs an `approved`
proposal through the full stack: status check → policy gate → **payload
parity** (a hash mismatch between what was approved and the stored payload
aborts to `failed` with no outbound call — a TOCTOU guard) → egress via an
**injected connector** (the executor never opens a socket itself) →
`executed`/`failed`, recorded with the payload hash in the audit trail. A
connector error → `failed` (retryable via `failed → approved`).

The connector is supplied by *you* and is where egress policy lives —
route it through the existing connector surface (`connector_runtime`) so it
honors the Phase-25 provider gate; do not invent a new outbound path.

### Worked example: `followup_ticket_actuator`

The reference actuator
([`followup_ticket_actuator.py`](../holdspeak/plugins/builtin/followup_ticket_actuator.py))
proposes a follow-up ticket for the first action item without an owner:

```python
class FollowupTicketActuator:
    id = "followup_ticket_actuator"
    version = "0.1.0"
    kind = "actuator"
    required_capabilities = ["actuator"]   # off by default → opt-in

    def run(self, context):
        unowned = _first_unowned(context.get("action_items") or [])
        if unowned is None:
            raise ValueError("no unowned action item to follow up on")
        task = unowned["task"]
        return {
            "target": "outbox",
            "action": "write_followup_ticket",
            "preview": f"Draft a follow-up ticket for “{task}”",
            "payload": {"filename": f"followup-{slug(task)}.md", "body": ...},
            "reversible": True,
            "required_capabilities": ["actuator"],
        }
```

Its connector (`build_outbox_connector`) performs the side effect — here a
local **outbox** Markdown file (a real, reversible, network-free artifact).
Wiring the loop:

```python
host = PluginHost(enabled_capabilities={"actuator"})
register_followup_actuator(host)                       # opt-in, NOT in register_builtin_plugins

result = host.execute("followup_ticket_actuator", context=ctx, ...)   # → status "proposed"
record_actuator_proposal(db, run_from(result))         # persist

# ... a human approves in the UI ...
db.actuators.transition_proposal(pid, to_status="approved", actor="karol")

executor = ActuatorExecutor(
    db,
    connector=build_outbox_connector(outbox_dir),
    allow_actuators=True,                              # master switch
    allowed_actuator_ids=["followup_ticket_actuator"], # allow-list
)
executor.execute(pid)                                  # → "executed" + audit; the file is written
```

### Registering + testing

Register actuators **explicitly and opt-in** — `register_followup_actuator`
is *not* part of `register_builtin_plugins`, so the default plugin set and
routing chains stay unchanged. Test the loop end-to-end against a stub or
local connector (no real egress): assert the proposal is faithful, that
executing **before** approval / with the gate off / when not allow-listed
performs **no** side effect, and that approve → execute writes the audited
terminal state. See
[`test_actuator_reference.py`](../tests/unit/test_actuator_reference.py).

---

## Built-in reference implementations

The cleanest references, in order of how much they'll teach you:

| Plugin | File | Why read it |
|---|---|---|
| `decision_capture` | [`decision_capture.py`](../holdspeak/plugins/builtin/decision_capture.py) | The canonical end-to-end pattern: prompt → intel → parse → structured output, deferred, `llm`-gated. |
| `mermaid_architecture` | [`mermaid_architecture.py`](../holdspeak/plugins/builtin/mermaid_architecture.py) | An `artifact_generator` that produces a diagram (Mermaid → SVG). |
| `action_owner_enforcer` | [`action_owner_enforcer.py`](../holdspeak/plugins/builtin/action_owner_enforcer.py) | A `validator` that flags gaps rather than synthesizing prose. |
| `followup_ticket_actuator` | [`followup_ticket_actuator.py`](../holdspeak/plugins/builtin/followup_ticket_actuator.py) | The reference `actuator` — proposes a side effect; see [Actuators](#actuators). |

The full set of 14 lives under
[`holdspeak/plugins/builtin/`](../holdspeak/plugins/builtin/); the
renderers for all of them are in
[`synthesis.py`](../holdspeak/plugins/synthesis.py).

---

## Out of scope

This contract deliberately does **not** cover:

- **Remote/third-party distribution** — there is no marketplace and no
  loader for packages pulled from the internet. Plugin packs (when they
  land) load from a local directory only, matching the connector-pack
  boundary.
- **Changing the built-ins' behavior or the default routing output** —
  new plugins layer on; the 14 built-ins stay behavior-identical.
