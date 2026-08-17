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

export const DOCK_SPRITES: Record<string, string> = {
  "surface-dictation": SYSTEM.dockSpeak,
  "surface-meetings": SYSTEM.dockMeetings,
  "surface-companion": SYSTEM.dockAgents,
  "surface-settings": SYSTEM.dockSettings,
};
