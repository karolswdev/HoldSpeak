/** HS-110-02 — the system sprite sheet. Every system chrome element
 * rendered as pixel art in the same language as the icon family.
 * HS-135-14 — the bright mold: every sprite recast at 32×32 through
 * the owner-ratified bright palette (silver-forward, cheerful, crisp).
 * New: mic states, floor grid, cadence identity, per-meaning empties. */

const BASE = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/system/`;

export const SYSTEM = {
  dockSpeak: `${BASE}dock-speak.png`,
  dockMeetings: `${BASE}dock-meetings.png`,
  dockAgents: `${BASE}dock-agents.png`,
  dockSettings: `${BASE}dock-settings.png`,
  dockPeople: `${BASE}dock-people.png`,
  /** PHILO-15 lane 12 (B19): the four Dock items that wore a text glyph. */
  dockIntelligence: `${BASE}dock-intelligence.png`,
  dockDeskMemory: `${BASE}dock-desk-memory.png`,
  dockDelivery: `${BASE}dock-delivery.png`,
  dockPanes: `${BASE}dock-panes.png`,
  // HS-111-09 — the gadget sprites and backdrop tile are RETIRED: the
  // SVG VerbGlyph gadgets and the CSS crosshatch won on the desk (see
  // ICON-DISCIPLINE §HS-110-02, amended). Registered sprites RENDER —
  // no orphans (systemSprites.test.ts guards both directions).
  menuMark: `${BASE}menu-mark.png`,
  menuBell: `${BASE}menu-bell.png`,
  menuSearch: `${BASE}menu-search.png`,
  micGlyph: `${BASE}mic.png`,
  /** HS-135-14 — mic state sprites: idle (micGlyph), listening, recording. */
  micListening: `${BASE}mic-listening.png`,
  micRecording: `${BASE}mic-recording.png`,
  recordOrb: `${BASE}record-orb.png`,
  /** HS-135-14 — the dock Floor toggle glyph (replaces the ▦ character). */
  floorGrid: `${BASE}floor-grid.png`,
  /** HS-135-14 — cadence identity + per-meaning empty-state glyphs. */
  cadenceMetronome: `${BASE}cadence-metronome.png`,
  emptyLoops: `${BASE}empty-loops.png`,
  emptyNudges: `${BASE}empty-nudges.png`,
} as const;

/** Every Dock item wears a sprite: the applications (by window id) and the
 * launchers (by launcher id). A text glyph on the Dock is a bounce (B19). */
export const DOCK_SPRITES: Record<string, string> = {
  "intelligence:desk": SYSTEM.dockIntelligence,
  "surface-dictation": SYSTEM.dockSpeak,
  "surface-meetings": SYSTEM.dockMeetings,
  "surface-companion": SYSTEM.dockAgents,
  // PHILO-14 C4: the Dock's Conductor wears the same D1 glyph.
  conductor: SYSTEM.dockAgents,
  "surface-settings": SYSTEM.dockSettings,
  "surface-people": SYSTEM.dockPeople,
  // The launchers (launcherRegistry.ts): Desk memory, Delivery, Panes.
  attention: SYSTEM.dockDeskMemory,
  "delivery-board": SYSTEM.dockDelivery,
  panes: SYSTEM.dockPanes,
  // W1-KIT: the Capture window (a Chair door) wears the Record orb in its
  // title bar, as its phone Dock door does.
  "chair:capture": SYSTEM.recordOrb,
};

/** The floating dock (owner pick 2026-10-26, dock-direction canvas D1): its
 * tiles and the Record orb wear the D drawing at 48 px (`system/48/`, a
 * two-pixel bevel; web/scripts/gen-illustrated-icons.py `system48`). The
 * registry test guards this set in both directions too. */
const BASE_48 = `${BASE}48/`;
export const SYSTEM_48 = {
  dockSpeak: `${BASE_48}dock-speak.png`,
  dockMeetings: `${BASE_48}dock-meetings.png`,
  dockAgents: `${BASE_48}dock-agents.png`,
  dockSettings: `${BASE_48}dock-settings.png`,
  dockPeople: `${BASE_48}dock-people.png`,
  dockIntelligence: `${BASE_48}dock-intelligence.png`,
  dockDeskMemory: `${BASE_48}dock-desk-memory.png`,
  dockDelivery: `${BASE_48}dock-delivery.png`,
  dockPanes: `${BASE_48}dock-panes.png`,
  recordOrb: `${BASE_48}record-orb.png`,
} as const;

/** The 48 px dock tile of each Dock item (the same keys as DOCK_SPRITES). */
export const DOCK_SPRITES_48: Record<string, string> = {
  "intelligence:desk": SYSTEM_48.dockIntelligence,
  "surface-dictation": SYSTEM_48.dockSpeak,
  "surface-meetings": SYSTEM_48.dockMeetings,
  "surface-companion": SYSTEM_48.dockAgents,
  conductor: SYSTEM_48.dockAgents,
  "surface-settings": SYSTEM_48.dockSettings,
  "surface-people": SYSTEM_48.dockPeople,
  attention: SYSTEM_48.dockDeskMemory,
  "delivery-board": SYSTEM_48.dockDelivery,
  panes: SYSTEM_48.dockPanes,
  /* The phone's Capture door is its Record door (the desktop Record tile
     leaves the phone projection): it wears the Record orb. */
  "chair:capture": SYSTEM_48.recordOrb,
};

/** The 48 px sibling of a system sprite URL (a seated window's title-bar
 * icon on its dock tile). Any other URL comes back unchanged. */
export function dockSprite48(url: string): string {
  if (!url.startsWith(BASE)) return url;
  const file = url.slice(BASE.length).replace(/^(?:20|48)\//, "");
  const match = Object.values(SYSTEM_48).find((u) => u.endsWith(`/48/${file}`));
  return match ?? url;
}
