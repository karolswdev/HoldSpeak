// The thin kit (PG-DIRECTION DIR2, 2026-10-31): the surface species a page
// outside the desk composes (the briefing page, web/briefing.html). Nothing
// here reaches the desk's auth client (src/lib/auth.ts) or the microphone:
// the guard web/src/briefing/__tests__/briefing.app.test.tsx walks the
// imports. Desk code keeps importing from ./index.ts. Shared live pieces
// bring their own material; briefing.css supplies the page layout.
export { FoldGadget } from "./fold";
export { SurfaceCode } from "./code";
export { DotWord, StatusBar, Toolbar, type StatusBarItem } from "./kit";
export { sentenceChildren } from "./words";
// The briefing page's step line (2026-10-31): the Programs station track.
export { StepTrack, type TrackStep } from "./live/StepTrack";
