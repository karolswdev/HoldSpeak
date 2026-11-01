// The thin kit (PG-DIRECTION DIR2, 2026-10-31): the surface species a page
// outside the desk composes (the briefing page, web/briefing.html). Nothing
// here reaches the desk's auth client (src/lib/auth.ts) or the microphone:
// the guard web/src/briefing/__tests__/briefing.app.test.tsx walks the
// imports. Desk code keeps importing from ./index.ts. No module here imports
// a stylesheet: the page brings the material in web/src/briefing/briefing.css,
// so the desk's own stylesheet order is unchanged.
export { FoldGadget } from "./fold";
export { SurfaceCode } from "./code";
export { DotWord, StatusBar, Toolbar, type StatusBarItem } from "./kit";
export { sentenceChildren } from "./words";
// The briefing page's step line (2026-10-31): the Programs station track.
export { StationTrack, trackLabel, type TrackStation } from "./programTrack";
