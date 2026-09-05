# The Concierge — the settled design (Phase 170, story 03)

The owner's words (2026-08-31): the co-creator "doesn't know how to use
this product"; his ruling: "A) Let me download it for you... B) Easy
to then go in and dig into some 'advanced'... This is what matters,
man." The face canon binds (docs/internal/UX-CANON.md); the Door's
grammar (Phase 169) is the ratified precedent; recon anchors in the
HS-170-03 research (front_door_service.py:27-34 the seven groups;
setup_runtime.py:41/121 detection; profile_service.py:104 the probe;
inference_assignments.set the write).

## D0 — the job

Settings → Models becomes ONE screen: **what was found · one proposed
set · `Use these`.** From "I have a .43 box" to "everything uses it,
dictation on the fast one" in TWO clicks (today: 4 for a uniform pack,
7 for one group). Advanced lives under `Adjust`. Nothing downloads,
probes a paid key, or leaves the machine without a named host on the
row.

## D1 — what is cut (and where it goes)

| Cut | Where it goes |
|---|---|
| The three pack cards (Light / Balanced / Full) | One proposed SET — a row per capability group with the best engine per group (packs assigned one engine to everything; dictation on a 35B is 1–2 s of visible latency) |
| `Set up my own` → Map / Table tabs → per-row editor | `Adjust` unfolds the capability table in place (parked, not removed) |
| Profile ids on the face (`lan-qwen36-35b-a3b`, `legacy-legacy-intel`) | Engine NAMES with their host: `Qwen3.6 35B · 192.168.1.43` |
| The silent global fallback to a cloud model | Every group shows its ENGINE and its state; an unset key reads `KEY NOT SET` on the row, never silence |
| The dual authority (legacy `profiles` vs the Model Library) | Collapsed additively: v2 revisions for the legacy ids, assignments migrated to schema 2, tombstones; `resolve_inference_target` unchanged until a later cleanup |

## D2 — the face (window "Models", 640 wide at 1440; 393 glass)

1. **The headline** at display step ONCE: `5 engines found` (accent) —
   the count IS the FOUND count (every found item is an engine: LAN,
   local, cloud key; presets not yet downloaded are listed but not
   counted)
   or `No engine yet` (muted). Under it the chip row: `THIS MAC · M‑series
   · 36 GB` (hardware fact) · `CHECKED 9:41`.
2. **FOUND** (caption + count): one ledger row per engine: lead = a kind
   glyph (LAN / THIS MAC / CLOUD from the library vocabulary); primary =
   the engine name (`Qwen3.6 35B`, `Whisper base`, `Qwythos 9B vision`,
   `OpenRouter`, `Anthropic`); cells = `41 MS` latency token when
   probed, a size token for files (`26.5 GB`), a runtime token for a
   local engine (`MLX`, `LLAMA.CPP`), `KEY SET` / `KEY NOT SET` for
   cloud (a cloud row also carries a ghost `Check` with the cost chip
   `1 TOKEN · $` — the only way a paid key is ever probed); trailing = EgressChip host (`192.168.1.43 · LAN` /
   `THIS DEVICE` / `openrouter.ai`) + StateChip `● READY` /
   `⚠ UNREACHABLE`. A catalog preset that is not on disk is a row too:
   `Qwen 3.5 0.8B · 532 MB` with the primary verb `Download` (his A) and
   an inline progress token while it pulls. Detection reads known
   endpoints, local model dirs, runtimes and key presence — never a
   network scan (the front-door law); the .43 box appears because its
   host is known; an unknown LAN host is added by one row `Add an
   engine…` → a StringGadget for the base URL + `Check` (the probe).
3. **THE SET** (caption; the proposal): one row per capability group in
   plain names — `Thoughts & notes` · `Chat` (the wire's `chat_practice` label becomes `Chat` in the build) · `Writing & dictation` ·
   `Speech recognition` · `Meetings` · `Agents & tools` · `Background`
   — lead = the group glyph; primary = the group name; the PICKER (the
   Door's beveled control with the stroke chevron) holding the proposed
   engine name; cells = the engine's latency token and its EgressChip;
   trailing = StateChip `● READY` / `○ CHECKING` / `⚠ KEY NOT SET`.
   **The proposal rule, per group:** `Speech recognition` = local
   Whisper only (its boundary is local — never LAN/cloud); `Writing &
   dictation` = the smallest reachable low-latency engine (a local
   ≤1B preset if present, else the LAN box); every other group = the
   strongest reachable LAN engine; cloud ONLY where he picks it in the
   picker. The picker lists: found engines first (with latency), then
   `Download` presets (with size), then cloud keys that are set. Picking
   fires the probe for that row (CHECKING → READY · 41 MS).
4. **The probe is the count-as-test** — a bounded read (`/v1/models`
   with latency) for every engine; a ONE-TOKEN generation probe only for
   LAN and local engines (never a paid key by default; a cloud row
   probes on his explicit `Check` with the cost named on the chip:
   `1 TOKEN · $`). The receipt records every probe (Article XI).
5. **`Adjust`** (ghost, by THE SET's caption) unfolds the capability
   table in place UNDER the set rows (the set stays visible; every
   capability row carries its engine's host chip) — every capability, its group, its explicit override,
   the 143 map — for the "advanced" B. It never replaces the set; it
   edits it.
6. **Footer**: receipt `7 GROUPS · 3 ENGINES` (`NO ENGINE · SET UP
   NOTHING` when nothing found); egress slot empty (rows carry hosts);
   verbs `Cancel` (ghost, when the set changed) · **`Use these`**
   (primary; disabled until every group has a READY engine or an
   explicit `None` — a group may be set to `None` with the token
   `OFF`). `Use these` writes the whole set in ONE call (a CAS chain per
   group; schema 2), then the rows read READY with their latency.
7. **States**: first open on a cold Mac = `No engine yet` + FOUND
   listing the catalog `Download` rows and `Add an engine…`; `Use these`
   disabled; the receipt says so. Mid-download: the progress token on
   the row, the set's dependent rows `○ WAITING`. After apply: the
   headline becomes `7 groups set` for one settle, then back to the
   found count.
8. **393**: rows stack (the Door's four-line grammar: name / picker /
   tokens / host + state); the footer stacks; the headline never wraps.

## D3 — the wire

- `GET /api/concierge/detect` → `{engines:[{id,kind:lan|local|cloud|
  preset,name,host,latencyMs?,sizeBytes?,state,keySet?}], hardware,
  runtimes, checkedAt}` — composed from setup_runtime.discover_*,
  the known-endpoint list, key presence booleans (never a key), the
  catalog presets. No network scan.
- `POST /api/concierge/propose` → `{rows:[{group,label,engineId,
  alternatives:[…],state}]}` (the per-group rule above; replaces the
  pack `recommend()`, which stays for its MCP callers until 07).
- `POST /api/concierge/probe {engineId, generate?:bool}` → `{latencyMs,
  state, receiptId}` — generation only for lan/local unless
  `generate:true` is explicit (the cloud `Check`).
- `POST /api/concierge/apply {rows}` → the assignment set (schema 2) in
  one CAS transaction + receipts; returns the summary the router
  reads.
- `POST /api/concierge/download {presetId}` → the library's existing
  download job; progress via the existing job route.
- MCP twins: `concierge.detect/propose/probe/apply` on the same service.
- The collapse: v2 `model_profile_revisions` for `legacy-intel` and
  `target_a46b…`; heads migrated via the existing migration family;
  tombstones written; `profiles` becomes read-only history.

## D4 — laws and counsel's hunts

Counsel (2026-09-05): RATIFY-W-C — M-1 `Use these` enabled beside a
WAITING row; M-2 Anthropic's set key absent from FOUND; S-1 `Chat` vs
the wire's `Chat practice`; S-2 headline vs FOUND count; S-3 Adjust
replacing the set; S-4 no hosts on Adjust rows; S-5 no cloud `Check`;
N-1 the `MLX` token; N-2 the phone board's abbreviation; N-3 no
mid-download board. All paid on the boards and above.

- Speech recognition is local-only by boundary; a proposal that puts it
  anywhere else is a defect.
- No paid probe without his explicit verb and the cost on the chip.
- No profile id, no key value, no schema word on the face.
- Every engine row names its host; every set row names the host of its
  engine (Article III at the point of decision).
- The set is written once and completely; a half-applied set is a
  defect (one transaction).
- Counsel hunts: a second recommendation path (the pack `recommend()`
  vs `propose`); an unset key silently falling back; a probe that
  generates on a cloud key; a group left unassigned without the `OFF`
  token; the legacy profile still read by a face after the collapse;
  a `Download` that does not report progress or failure honestly.

## D5 — artboards (640 at 1440; 393)

1. Models · found + proposed (his desk: .43 Qwen 35B, .43 Qwythos 9B,
   Whisper base, 7 files, OpenRouter/Anthropic keys set; the set with
   dictation on the 0.8B preset marked `Download · 532 MB` — WAITING
   until it pulls, so the proposal shows the honest dependency)
2. Models · picker open (Writing & dictation: the 0.8B preset · 532 MB ·
   Download, Qwen3.6 35B · 41 MS, Anthropic · KEY SET · $)
3. Models · Adjust open (the capability table folded under the set)
4. Models · first open, cold Mac (`No engine yet`; Download rows; Add an
   engine…)
5. Models · 393 (found + proposed)
