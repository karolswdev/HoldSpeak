# The Desk — the whole picture

> The holistic map of DeskOS: what it is, the one model everything rides, the gesture grammar, the
> intelligence engine, how integrations are grounded, the two-layer mesh, and the through-line. Read this to
> see how every shipped piece fits one coherent system — and where it's going. Companion to
> [[story-25-the-desk-interaction-system]] (the contract detail) and [[DESK_HANDOVER]] (the build state).

## 1. What it is

**DeskOS** turns the iPad into a spatial, gamified **command center for your work**: your meetings, the
intelligence drawn from them, the AI itself, your knowledge, and your integrations are all **manipulable
objects on one living desk**. The iPad is a **companion to your Mac** — the Mac is the host that owns the
heavier runtime, the actuator framework, and every credential.

The bar: *would a senior engineer keep their real meetings here and enjoy it?* Not a viewer — an **engine**.

## 2. The one model — everything is a `DeskPrimitive`

The spine. **Every concept on the desk declares the same small facet set, and the entire UI is derived from
that declaration** — the canvas object, the card, the pull-out, the menu, and the routing. Add a concept to
the platform = declare one primitive; its whole UI and behaviour appear for free, consistent with everything.

| Facet | Meaning |
|---|---|
| `kind` | type → glyph + colour (meeting=cassette, model=AI-core, kb=crystal, output=note, connector=tool) |
| `title` / `subtitle` / `preview` | identity + one-line content snippet |
| `sections` | the pull-out body (text / actions / chips / transcript) — one renderer, any primitive |
| `actions` | the menu / drawer buttons |
| **`emits`** | the outputs you can pull off it |
| **`accepts`** | what it consumes when something is dropped on it → `target.receive(source)` |

## 3. The gesture grammar — one language, every primitive

| Gesture | Meaning |
|---|---|
| **Tap** | open → the pull-out (inspect) |
| **Drag** | move / free-place; **onto a zone** = file; **onto a target** = route |
| **Lasso** (drag empty desk) | multi-select → a bundle |
| **Long-press** | the action menu (Route to… / Send to… / Open) — the discoverable twin of the drag |
| **Tap a zone** | dive in (fractal, recursive); **tap empty** = climb out |
| **Swipe a printed card** | keep / bin (judge a generated output) |

Three ways into the same engine: **drag a target, lasso a bundle, or long-press a menu.**

## 4. The intelligence engine — route anything → an LLM → a new thing

The **AI core** (`accepts` everything) is a live `ILLMProvider` — on-device GGUF **or** an endpoint, per
settings. Drop a primitive (or a lasso bundle, or a meeting) on it → pick a **lens** or write a prompt → it
runs **grounded in the source's `routableText`**, with a **visible cable** (a token travels the wire) → a new
primitive **prints** → keep (it lands, persisted, and is itself routable) or bin. **Every output is an input.**
A saved **workflow** is the same gesture at higher power (a pipeline of core calls).

## 5. Integrations — act into the world, grounded + host-gated

Connectors are primitives too — but they **do not act from the iPad**. They route through your **Mac (the
host)**, which owns the HoldSpeak **actuator framework** (propose → approve → execute, a permission manifest,
a guarded executor) and the **credential** (e.g. the Slack webhook), joined in memory **on the Mac** at
execute time — never on the iPad. The connector tile is **gated on host connectivity**. One **egress badge**
(local / cloud · target), no privacy prose.

> Drop an output on the Slack tile → the iPad **proposes** to the Mac (preview only) → you **approve** →
> the Mac **executes** through the real guarded connector → the message posts. The iPad sends only text.

## 6. The two layers — the mesh

```
📱 iPad  — the spatial companion: capture, on-device intelligence, the desk, the gestures
   │  (companion API, gated on connectivity; credentials never cross)
💻 Mac   — the host: the actuator framework, every credential, the heavier runtime, web parity
```

## 7. The through-line

**record → route (into the core / a workflow / a KB) → keep / judge → act (out to a connector).**
One grammar end to end. Nothing is a dead end; every output is an input.

## 8. Where it stands (✅ built) and where it's going (▶ next)

- ✅ The `DeskPrimitive` contract — UI derived from one declaration
- ✅ The fractal desk — low-profile zone shelves, drop-to-file, dive-in (recursive), breadcrumb
- ✅ The pull-out — any primitive's sections/actions, one renderer (the right-edge drawer)
- ✅ The keystone — drag → AI core → real on-device/endpoint LLM → a new primitive prints → keep/bin
- ✅ The visible route — a cable with a traveling token (one mechanism for routing-in and sending-out)
- ✅ The Ask-AI atom — lasso a bundle → ask the model about all of it at once
- ✅ The long-press menu — Route to… / Send to… / Open (the discoverable twin)
- ✅ Three connectors grounded — **Slack · Webhook · GitHub issue**, all via the **Mac's actuator
  framework** (propose→approve→execute), host-gated, credential on the Mac, target-scoped (30 tests). Adding
  the next is "one primitive + one thin host endpoint."
- ✅ Workflows as primitives — "Save as a tool" → a tile; drop a meeting on it and it runs the saved Ask
- ✅ Act-on-section — route a single facet (just the actions, just the summary) through the core
- ▶ Web parity + mesh sync (Phase 16) — the desk everywhere, one approval + egress contract — **the next big track**
- ▶ Real-metal proof — the on-device LLM route + a live send via the Mac, walked on the iPad

## 9. The map

See `the-desk-map.png` (rendered from `the-desk-map.mmd`) — the same system as a single diagram: capture →
the desk of primitives → the intelligence engine → keep → act out through the Mac host to the world.
