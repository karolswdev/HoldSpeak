# Phase 156 settled design — The Front Door

Ruled by the OWNER 2026-08-31, verbatim: "A) Let me download it for
you, a recommended pack based on your hardware…, and maybe A/B/C
options. B) Easy to then go in and dig into some 'advanced' models,
fallbacks, and what not. This is what matters, man." Grounded in the
owner data point (the co-creator got lost in Settings → Models on his
real desk: 7 groups all no_assignment, zero profiles, his known
engines nowhere) and the concierge UX-evidence log (assets/, from the
2026-08-31 live-desk configuration). This phase OUTRANKS 155 The Crew
(value-era pivot). Builders implement.

## The one sentence

The desk earns its first minute: it looks at your machine and what you
already have, offers a recommended pack — A, B, or C — downloads and
wires everything on one confirmation, and folds the whole existing
Library/Assignments machinery underneath as the advanced layer it was
always meant to be.

## D1 — the recommendation (story 01)

- A pure server-side recommender over facts the desk ALREADY has:
  the hardware snapshot (`/api/inference/setup` — apple_silicon,
  memory, accelerators), the catalog, what is already downloaded/
  connected, the LEGACY config (models it named before 143), and
  reachable LAN OpenAI-compatible servers (probe the configured/known
  endpoints — never a network-wide scan; a one-line "add your server"
  field covers the rest).
- Output: up to three PACKS — e.g. **A · Light** (fits comfortably,
  fastest), **B · Balanced** (recommended for this hardware),
  **C · Full** (the most capable that fits) — each a COMPLETE plan:
  which models (with download sizes), which engine per job group, all
  seven groups covered, TTS/speech included. Plain words, one line per
  job: "Chat & agents → Qwen server on .43 · Speech → whisper small
  (140 MB) · …". Detected-but-unused facts surface as pack
  ingredients ("your .43 server", "your gemma file"), never as chores.
- The recommender is a capability-free pure function + one GET route;
  the truth table of what each pack assigns is a fixture the tests pin.

## D2 — one confirmation applies everything (story 02)

- POST apply(pack) drives ONLY the existing machinery: Model Library
  downloads (egress-badged, receipted, resumable), profile creation,
  and the assignments editor/set flow for all seven groups — no new
  authority, no parallel writer, every step receipted. Progress is one
  visible plan with per-item state (queued → downloading MB/s → wired);
  failures leave a resumable plan, never a half-desk (each item is
  idempotent; re-apply continues).
- The apply is inspectable before confirmation: the pack card IS the
  plan (sizes, destinations, what gets assigned where).

## D3 — the door surface (story 03)

- Settings → Models opens on the DOOR when anything is unconfigured:
  the three pack cards + "your own setup" (the advanced layer). After
  setup, the door collapses to a one-line health strip ("Everything
  wired · Balanced pack · change") above the advanced view.
- "Needs attention" is abolished as a mood: any attention state names
  ONE next action and carries its button ("Speech has no model —
  Fix it").
- The advanced layer (B) is the EXISTING Library + Assignments,
  unchanged in power: fallback chains, per-group overrides, hosted
  connects, endpoint definition. One fold, zero features removed.

## D4 — plain words everywhere (story 04)

- The jargon purge on the door path: "catalog · available" → "not
  downloaded"; group labels stay human ("Chat & agents", "Speech
  recognition"); statuses say what happens next, not what schema row
  exists. POSITIONING voice rules; no prose novels; the egress badge
  law untouched.
- The concierge UX-evidence log is the checklist: every logged rough
  edge is either fixed by D1–D3 or fixed here, each with a test or an
  explicit recorded-not-fixed entry.

## D6 — the topology (story 05) — OWNER, mid-charter, verbatim: "we have
home-lab (.43), we have this Mac with MLX. I feel like I need a visual
topography editor almost for some advanced scenarios. Where 'this
PC/(Mac)' is displayed, and then we can 'add nodes'. … All workbench
2.0+ on steroids, elegance to the max"

- The advanced layer opens on a MAP, not a table: **this Mac** as the
  home node (its runtimes — MLX, llama.cpp-local — and downloaded
  models drawn on it), each connected endpoint/device as a node
  (the .43 home-lab server, cloud connections, paired devices), and
  the seven job groups as visible flows to the node that serves them.
- **Add node** on the map IS the existing connect grammar
  (define-endpoint / connect-hosted / paired device) — the map is a
  VIEW + verb surface over the same authorities, never a new one.
  Selecting a node shows what runs there and lets a job flow be
  re-pointed (the assignments editor, in place, in-world, no modal).
- OWNER (mid-charter, second beat): "the vis is not only viz, it's
  also a configuration interface… let's just be cohesive with the
  style, the component library, and so on." The map IS configuration:
  every gesture on it (add node, re-point a flow, fix an unreachable
  node) performs the real operation through the same authorities —
  there is no read-only mode with a separate form behind it.
- Cohesion law: built FROM the desk's existing component library and
  tokens (the surface gadgets, pullout grammar, chip/badge language,
  the workbench node-graph visual lineage) — no bespoke widget
  kingdom, no second design system. Beautiful at 1440, honest at 393
  (the map pans; the page never scrolls sideways).

## D7 — the walk (story 06)

- THE STOPWATCH BAR (unchanged by D6 — the map is layer B): from a fresh desk (and from the owner's
  real-shape desk: legacy config + LAN server present), a cold owner
  reaches a working chat turn AND a working dictation in **under 60
  seconds** without reading anything twice. The walk measures it (the
  glass rig drives the door path and asserts the wall clock, minus
  download time which is reported separately).
- Glass 1440 + 393 (the pack cards, the plan, the health strip, the
  advanced fold); metal: apply a pack that wires the .43 server and
  prove a real turn; docs (README quick start rewritten around the
  door); close counsel; honest sweep incl. `npm --prefix web run
  check`.

Recorded: no network-wide LAN scanning (explicit endpoints only);
packs never auto-change after setup (the desk proposes, the owner
disposes); cloud packs only when a credential already exists — the
door never asks for an API key on the A path.
