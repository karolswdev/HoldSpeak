# HS-114-07 Walk Shot List

Run `bash scripts/walk-prep-114.sh` first. Then `uv run holdspeak serve`.
Open `http://localhost:8766` at 1440×900. Verify .43 is reachable.

Every shot proves a specific finding from the applicability study.

## Shots

- [ ] **Shot 01 — Fresh seeded desk.**
  The floor shows: Architecture reviewer (automaton sprite), Summarize
  material (cartridge sprite), 6 drawers. Open Settings > Models:
  Homelab row visible with endpoint + model + READY state.
  *Proves: HS-114-01 (seeded nerve)*

- [ ] **Shot 02 — Cmd+I opens Ask.**
  Press Cmd+I with nothing selected. Ask panel opens: empty composer,
  RunsOnPicker showing HOMELAB, egress lamp showing ● LAN.
  *Proves: HS-114-02 (keyboard shortcut, empty-context Ask)*

- [ ] **Shot 03 — Ask result with egress lamp.**
  Type a question and press Enter. HUB> response appears with inline
  receipt: `ran on ● LAN HOMELAB · Qwythos-9B · Xms`.
  Egress lamp in footer shows ● LAN.
  *Proves: HS-114-04 (egress readout in instrument footer)*

- [ ] **Shot 04 — "Ask this" context verb.**
  Right-click the "Working rules" note. Context menu shows "Ask AI".
  *Proves: HS-114-02 (context verb on Notes)*

- [ ] **Shot 05 — Agent chat with egress lamp.**
  Open the Architecture reviewer. Chat with it. Footer shows
  RunsOnPicker (HOMELAB) + ● LAN egress lamp.
  *Proves: HS-114-04 (persona egress)*

- [ ] **Shot 06 — Per-destination TEST.**
  Open Settings > Models. Click TEST on the Homelab row.
  State shows ● READY {latency}ms.
  *Proves: HS-114-03 (per-row probe)*

- [ ] **Shot 07 — Model discovery dropdown.**
  After TEST succeeds, click the MODEL cell.
  CycleGadget dropdown shows models discovered from .43.
  *Proves: HS-114-03 (model discovery)*

- [ ] **Shot 08 — Editor transform proposal.**
  Open a Note, select text, trigger Rewrite (or Cmd+J > Rewrite).
  Aerogel inset appears with proposed text + ACCEPT/REJECT + receipt.
  RunsOnPicker and ● LAN lamp visible in the AI bar.
  *Proves: HS-114-05 (propose don't replace) + HS-114-04 (editor egress)*

- [ ] **Shot 09 — Hub default resolution.**
  Open Settings > Models > Runs on section.
  Dictation and Meetings show ↻ HOMELAB (adopted).
  The hub-default option reads "HUB DEFAULT · NO MODEL" or the
  resolved engine name.
  *Proves: HS-114-06 (honest hub default label)*

- [ ] **Shot 10 — Floor Launch menu.**
  Right-click the floor > Launch. "Ask AI" visible in the menu.
  *Proves: HS-114-02 (floor menu entry)*

## Save shots

Save all 10 under `pm/roadmap/holdspeak/phase-114-the-nerve/assets/hs-114-07/`.
