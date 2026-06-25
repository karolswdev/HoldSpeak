# Story 25 — The Desk Interaction System (gestures · routing · integrations)

**Status:** design (drafted 2026-06-24 in response to the owner: "start thinking about the entire
gesture library. All the integrations. The intelligence engine where you can use any of the outputs and
route them to an LLM.")

This is the **coherence layer**. The diorama has objects, zones, a dive, and pull-outs — but each
interaction was built one-off, so it "feels weird." This story defines the *grammar* that makes every
primitive behave the same way and makes the whole desk composable. It does not add a feature; it makes the
features one system. Grounds in [[story-20-the-desk-object-model]] (the object convention),
[[story-15-workbench]] / [[story-16-workbench-blueprints]] (visual routing), and the shipped actuator /
connector / provider work (Phases 37/38/61, the inference-target settings).

## 1. The premise (the one idea)

**Everything on the desk is a typed object that CONSUMES and EMITS typed outputs, and the model is just
another object you feed.** Capture makes objects; gestures route objects into other objects; some objects
(the AI core, a workflow) transform what you drop on them into new objects; some objects (connectors) send
what you drop on them out of the app. One grammar, end to end:

> **capture → objects → route (into the AI core / a workflow / a KB) → judge (keep / bin) → act (into a
> connector).**

## 2. The Primitive contract (the standard UI pattern you rely on)

**Literally everything in the platform is a `DeskPrimitive`** — a meeting, a summary, an action, a
transcript, a note, the AI core, a KB, a workflow, a Slack connector, a command, even a setting. Each one
**declares the same small set of facets**, and the *entire UI is derived from that declaration* — nothing is
hand-built per type. That derivation is the "standard UI integration pattern that can be relied upon": you
learn how one primitive looks and behaves, and you know all of them.

```swift
protocol DeskPrimitive: Identifiable {
    var id: String { get }
    var kind: PrimitiveKind { get }            // → type colour + glyph (one source of truth)
    var title: String { get }
    var preview: String? { get }               // one-line content snippet (the card face)
    var sections: [PrimitiveSection] { get }   // the pull-out body, rendered uniformly
    var actions:  [PrimitiveAction]  { get }   // the long-press menu / drawer buttons
    var emits:    [PrimitiveKind]    { get }   // outputs you can pull off / drag away
    var accepts:  [PrimitiveKind]    { get }   // what it consumes when something is dropped on it
    func receive(_ other: DeskPrimitive) -> RouteResult   // what dropping X on me does
}
```

**One declaration drives every surface — identically, for every primitive:**

| Surface | Derived from | Always the same shape |
|---|---|---|
| **Canvas object** | `kind` (glyph + colour) + `title` | breathing sprite, type-colour glow, title chip |
| **Card / list / zone row** | `kind` + `title` + `preview` | glyph, title, one-line snippet, type badge |
| **The pull-out (tap)** | `sections` + `actions` | header (glyph/title/egress) → uniform sections → action buttons |
| **The menu (long-press)** | `actions` + route targets | "Route to…", "Send to…", "Ask…" |
| **Routing (drag onto X)** | `target.receive(self)` | compatible (`target.accepts ∋ self.kind`) → a result; else spring back |

So adding a new concept to the platform = **declaring one primitive**. Its object, its card, its pull-out,
its menu, and how it routes all appear for free, consistent with everything else. No new bespoke screen, ever
— that is the reliability the owner is asking for.

Compatibility is just `target.accepts ∋ source.kind`; an incompatible drop springs back with a shake.

## 3. The gesture library (consistent across EVERY primitive)

Refined from [[story-20-the-desk-object-model]] for the 2.5D desk. The promise: learn it once, it works on
everything.

| Gesture | Meaning | Notes |
|---|---|---|
| **Tap** | open → the **pull-out** (inspect contents in the right-edge drawer) | the universal "look inside" |
| **Drag** | move / free-place | persisted position |
| **Drag → onto a zone tray** | file / classify | drop-to-tag (shipped) |
| **Drag → onto another object** | **combine / route** (the keystone) | onto AI core = transform; onto connector = send; onto KB = file/ground; onto workflow = run |
| **Long-press** | the object's **action menu** | "Route to…", "Send to…", "Ask…", reshape — the discoverable path to everything drag does |
| **Lasso** (drag on empty canvas / Pencil) | select many → a **context bundle** | the Ask-AI atom: lasso → drop on AI core → ask over all of it |
| **Tap a zone** | dive in | recursive (shipped) |
| **Swipe a printed card** | **keep / bin** | judge a generated output: keep → it becomes a real object; bin → discard |
| **Pencil** | annotate / sketch | → the diagram language [[story-08-pencil-diagram-language]] |
| **Back / breadcrumb** | climb out of a zone | always-on-top (shipped) |

Two ways to do everything: **direct manipulation** (drag onto the target — tactile, discoverable by trying)
and the **long-press menu** (for when the target is off-screen or you forget). They produce identical
routes.

## 4. The intelligence engine (route any output → an LLM → a new output)

The keystone. The **AI core** (cartridge) is a live `ILLMProvider` — on-device `LlamaProvider` **or** an
OpenAI-compatible endpoint, per the inference-target setting (already shipped). Routing into it:

1. **Drop** an output (or a lasso bundle, or a whole meeting) **onto the AI core** — or long-press → "Route
   to AI".
2. A **prompt sheet** opens: a free prompt, or one of your saved **lenses / workflow presets**
   ([[story-15-workbench]]); the dropped object is the grounded `{input}`.
3. It runs through the provider with the **generation-theater** treatment (the existing on-device
   thinking-orb), the route drawn as a **visible arc** source → core → result (the gamified Blueprints flow,
   [[story-16-workbench-blueprints]]).
4. A **new card prints** onto the desk — a first-class object (its own type, emits, pull-out). **Keep / bin**.

A **workflow** object is a saved multi-step pipeline you can drop onto exactly the same way (it just runs
several core calls). So "ask once" and "run my pipeline" are the same gesture at different power levels.

**This makes the desk a programming surface without a programming UI:** outputs are values, the core is a
function, dropping is application, keep/bin is the assertion.

## 5. Integrations (route an output OUT)

Connectors are **objects on the desk too** — a Slack tile, a GitHub tile, a webhook tile — gated by the
existing actuator permission framework (Phases 37/38) and the Slack executor (Phase 61). Dropping an output
onto a connector runs **propose → approve → execute**: a confirm card (what, where, the **egress badge** —
local / local+cloud / cloud+target, per [[feedback_no_privacy_novels]]) → approve → it sends. Same grammar
as routing to the AI core; the only difference is the target *emits to the world* instead of *to the desk*.

Connectors are added/authorised in settings; an unconfigured connector shows as a dashed "+ add" tile, like
"+ New Zone".

## 6. The through-line (why it all fits)

```
record ─▶ MEETING ─▶ (emits) summary · actions · transcript · topics
                         │
        drag an output ──┼──▶ AI CORE ─▶ generation-theater ─▶ NEW CARD ─▶ keep/bin ─▶ real object
                         │       ▲                                              │
                         │   prompt / lens / workflow                          └─ drag ─▶ SLACK ─▶ approve ─▶ sent
                         └──▶ KB CRYSTAL (file / ground)
```

Every arrow is the same gesture (**drag onto a target**, or **long-press → route**). Nothing is a dead end;
every output can become an input.

## 7. Build order (proposed)

1. **The keystone gesture — route to the AI core.** Drag an output (start: a meeting / its summary) onto the
   AI core → prompt sheet → run through the real provider → a new card prints, keep/bin. Proven on the LAN
   endpoint and on-device. *This is the smallest thing that makes the whole model real.*
2. **The route is visible.** Draw the arc + carry the generation-theater so the routing reads as motion.
3. **Long-press menu** parity (Route to… / Send to… / Ask…) so direct-manipulation has a discoverable twin.
4. **Connectors as objects** — Slack tile, drop-to-send via the shipped executor + egress badge.
5. **Lasso → bundle → Ask** (the Ask-AI atom, [[story-09-the-ask-ai-atom]]).
6. **Workflow object** — drop a meeting on a saved pipeline; run it; results print.

## 8. Acceptance (when this is real)

- One written gesture grammar that every primitive obeys; no primitive has a bespoke interaction.
- Any output can be dropped on the AI core and returns a new first-class object, on real metal.
- Any output can be dropped on a connector and sends via propose→approve→execute with an egress badge.
- The routes are *visible* (you can see what fed what), and nothing is a dead end.
