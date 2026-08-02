/** HS-110-02 — the system sprite sheet. Every system chrome element
 * rendered as pixel art in the same language as the icon family. */

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
  recordOrb: `${BASE}record-orb.png`,
} as const;

export const DOCK_SPRITES: Record<string, string> = {
  "surface-dictation": SYSTEM.dockSpeak,
  "surface-meetings": SYSTEM.dockMeetings,
  "surface-companion": SYSTEM.dockAgents,
  "surface-settings": SYSTEM.dockSettings,
};
