# HS-111-09 — the judgment sheet (implement leg)

Before crops: `.tmp/hs-111-09-shots/` (the audit). After crops: this
directory, live hub 127.0.0.1:8765, DPR 2. Every changed asset was
judged ON THE REAL DESK at rendered size and at 4x — never in the
generator preview. Full after-sheet: `sources-system-strip-after-4x.png`.
Integer proof: `measurements-after.json` — every sprite now renders
natural == rendered CSS px (16=16, 32=32, 40=40) at DPR 2.

| Asset | Before | After | What changed | Verdict |
|---|---|---|---|---|
| dock-speak | ../hs-111-09-shots/close-dock-rest-4x.png | close-el-dock-speak-4x.png | render 24→32 (1.5x→1x); the "dithered noise" grille resolves into a real grille at 1:1 — the mud WAS the scaling | **KEPT** (optional A4 regen not needed) |
| dock-meetings | same before strip | desktop-02-dock-rest.png | render 24→32 | **KEPT** |
| dock-agents | same before strip | close-el-dock-agents-4x.png | render 24→32; family anchor, crisp | **KEPT** |
| dock-settings | same before strip | desktop-02-dock-rest.png | render 24→32; stair-steps gone | **KEPT** |
| dock hover | ../hs-111-09-shots/close-dock-hover-4x.png | desktop-03-dock-hover.png | sprite itself now brightens 1.15 on hover (the `_sel` treatment), plus the tint | **WIRED** (CSS) |
| menu-mark | ../hs-111-09-shots/close-menubar-left-4x.png | close-el-menu-mark-4x.png | REGENERATED (pixen, 2 rounds + local dot cleanup): a bold signal-orange speech bubble — the brand finally reads at 16px; render 14→16 | **REGENERATED** |
| menu-bell | ../hs-111-09-shots/close-menubar-right-4x.png | close-el-menu-bell-4x.png | zero-credit local palette map: cartoon gold → paper-white/slate body, signal-orange clapper; render 14→16 | **RECOLORED** (local, 0 credits) |
| menu-search | same before | close-el-menu-search-4x.png | REGENERATED (pixen, 1 round): a real magnifier — lens ring + thick slate handle; render 14→16 | **REGENERATED** |
| record orb | ../hs-111-09-shots/close-record-orb-4x.png | close-desktop-06-record-orb-4x.png, close-desktop-06b-record-orb-hover-4x.png | the CSS gloss-gradient orb (the last macOS survivor) RETIRED; new 40×40 sprite: signal-orange dot on a dark beveled key well (pixen + local corner recolor to palette); recording pulse = flat brightness steps, no glow | **REGENERATED + WIRED** |
| gadget-close/min/max sprites | ../hs-111-09-shots/sources-system-strip-4x.png (green maximize) | close-el-gadgets-4x.png | RULING: the SVG VerbGlyphs won — correct Workbench material on the desk; the sprites (incl. the traffic-light-green maximize) deleted; ICON-DISCIPLINE §HS-110-02 amended | **RETIRED** |
| backdrop-tile | (never rendered) | — | CSS crosshatch won; file + registry key deleted | **RETIRED** |
| ⊞ / ⟲ dock verbs | (dingbats) | close-el-dock-overview-4x.png, close-el-dock-reset-4x.png | new VerbGlyph SVG paths: overview = 2×2 window grid, reset = return loop | **WIRED** (SVG, 0 credits) |
| ✕ dock chip close | (dingbat) | desktop-10-dock-with-window.png | VerbGlyph `close` | **WIRED** |
| 🎙 MicButton | (emoji, every input + TALK key) | close-el-mic-4x.png, desktop-11-speak-window.png, mobile-01-desk-full.png (FILTER field + TALK) | NEW 16×16 mic sprite (pixen, 3 rounds — kept the handheld-mic round 3) | **NEW ART** |
| 🤖 default avatars | (emoji) | — (data-dependent; AgentAvatar.test.tsx locks it) | new `AgentAvatar`: empty/legacy-🤖 avatars wear the deterministic automaton sprite (`spriteUrl("agent", id)`), model chats wear the cartridge; custom text avatars survive; wire default now "" (matches the server's own default) | **WIRED** (0 credits) |
| 🖥️ model-chat avatar | (emoji) | — | cartridge sprite via AgentAvatar | **WIRED** |
| 💬 chat window glyph | (emoji) | — | type-scale "❝" (see deviations) | **SWAPPED** |
| 🤝 Agents window glyph | (emoji) | — | type-scale "◉" (the dock's own Agents fallback character) | **SWAPPED** |
| 🔍 tool inspector glyph | (emoji) | — | type-scale "⌕" | **SWAPPED** |
| Icon family (174 files) | ../hs-111-09-shots/desktop-07-object-field.png | desktop-01-desk-full.png | untouched — the standard everything above was judged against | **KEPT** |

## Held for the owner

- **Alternate brand mark**: a crisp 4-pointed signal spark also
  generated (scratchpad `gen1/spark.png`) — the bubble shipped; the
  spark is banked if the owner prefers a more abstract mark.
- **Chat/handshake as sprites**: the audit's NEW-ART table proposed
  16px sprites for 💬/🤝, but window `glyph` is a type-scale string
  woven through the registry (dock chips, menus, announceWindow).
  Shipping strings keeps the grammar; a registry-wide sprite-face
  ruling is a bigger architectural call — held.
- **⚙ / ✓ / ✦ type-scale characters**: left per the audit's own
  proposed ruling (status characters in type are not text-as-graphics).
- **Qlippy ◉ face** (flag-gated, off): untouched; real art if the
  mascot ever ships.

## Deviations from the audit plan

- edit_image was NOT used for the bell (it costs 20-40 generations vs
  pixen's 1); a local PIL palette map did it for zero credits.
- record-orb generated at 40×40 (pixen requires multiples of 4; 40
  measured = 40 rendered, exact).
- The old 62px non-dock orb CSS collapsed to the one 40px rule — the
  orb only mounts in the dock (DeskApp:72).
- mobile-02-dock clip overlapped a sheet (the dock z-yields under
  sheets on phones); mobile-01-desk-full carries the mobile truth.
