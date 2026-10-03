/* PHILO-13-17 (C7) canvas: the phone desk, drawn on the REAL product as it is on main
 * (the C1 frame at 393 is BUILT there: a 44 px screen bar, a 56 px shelf, one window at a
 * time, Capture on demand, the two-row footer).
 *
 * Loaded only in CANVAS_MODE=proposal with CANVAS_SHIMS=c7. Every seat (seats-c7.mjs)
 * calls one `globalThis.__c7*` function defined here; the build moves each piece into the
 * named product file (story 17, Scope).
 *
 * THE PROPOSED COMPOSITION (stated here; story 17 builds it), 393 only:
 *   Q1 THE SWIPE: a horizontal touch swipe on the front window moves to the next open window
 *      (finger to the left) or the previous one (to the right). The ring: the open Chair
 *      windows in the Chair's order (Needs you, Brief, The week, Capture when open), then the
 *      open desk windows in the order they opened. It wraps. A Chair window takes the work
 *      area as Go ▸ Chair does (the desk window in front iconifies to its Dock chip, never
 *      closes); a desk window comes to the front. (web/src/desk/components/DeskWindow.tsx
 *      compact branch; web/src/desk/chair/chairWindows.ts.)
 *   Q2 THE SWITCHER: the screen title is a library menu Button, `<front window> ▾`; its menu
 *      lists the same ring, a check on the front one. Any open window in two taps.
 *      (web/src/desk/components/DeskChrome.tsx ScreenTitle.)
 *   Q3 GO, GROUPED: Go leads with `Chair ▸`, `Desk ▸`, `Object ▸`, `Window ▸`, then its own
 *      rows; today Desk, Object and Window ride flat inside Go (48 rows; Chair last).
 *      (web/src/desk/components/DeskMenuBar.tsx.)
 *   Q4 AFTERCARE: an arriving aftercare card opens the Capture window at 393 (the owner's
 *      ruling), so the card lands in its slot and never floats over work.
 *      (web/src/components/AmbientLayer.tsx / chairWindows.ts openCaptureOnPhone.)
 *   Q5 44 PX IN EVERY WINDOW: at 393 every control in a window's body and footer owns 44 x 44
 *      (C1 R2's rule, not yet applied to every host on main: the meeting window's `Dictate about
 *      this` / `Record follow-up` are 27 px tall, its artifact rows 38 px, Meetings' `Open` 24 px).
 *      (web/src/desk/surface/surface.css, surface-footer.css, pullout.css.)
 *   Q6 the aftercare card's eyebrow `Meeting ready` on `--accent-text` (4.26:1 on main).
 *
 * STAND-INS: none for the data. The aftercare card is published through the product's own
 * `publishAftercare` with a meeting the seed made (the bus frame a finished meeting sends).
 */
import { useState } from "react";
import { Button } from "@w/components/signal/Signal";
import { WorkMenu, type WorkMenuEntry } from "@w/desk/components/DeskMenu";
import { useDesk } from "@w/desk/store";
import { useAllOpenWindows, registrySnapshot, frontWindowId } from "@w/desk/components/window/windowRegistry";
import { CHAIR_WINDOWS, openChairWindow, useChairWindows } from "@w/desk/chair/chairWindows";
import { useChairState } from "@w/desk/chairState";
import { useCompactViewport } from "@w/desk/useCompactViewport";

const G = globalThis as any;
const compactNow = () => window.matchMedia("(max-width: 720px)").matches;

/* Q5: the proposal's one CSS rule, injected last so it reads as the product's own. */
const q5 = document.createElement("style");
q5.id = "c7-proposal";
q5.textContent = `@media (max-width: 720px) {
  .desk-next .desk-window-shell.is-sheet :is(.surface-footer-verbs, .desk-pullout-body, .desk-surface-body) :is(button, [role=button], a[href]) { min-height: 44px; min-width: 44px; }
}
.desk-next .ambient-aftercare .signal-eyebrow { color: var(--accent-text); }`;
const keepLast = () => { if (document.head.lastElementChild !== q5) document.head.appendChild(q5); };
keepLast();
new MutationObserver(keepLast).observe(document.head, { childList: true });

/* ── the ring of open windows (Q1, Q2) ── */
type Ring = { id: string; label: string; chair: boolean }[];
function ring(): Ring {
  const closed = useChairWindows.getState().closed;
  const onChair = useChairState.getState().surface === "chair";
  const chair = onChair
    ? CHAIR_WINDOWS.filter((w) => !closed[w.id] && (w.phone || useChairWindows.getState().phone === w.id))
      .map((w) => ({ id: w.id, label: w.title, chair: true }))
    : [];
  const desk = registrySnapshot.filter((w) => w.dock && !w.id.startsWith("chair:")).map((w) => ({ id: w.id, label: w.label, chair: false }));
  return [...chair, ...desk];
}
/** The window that fills the work area now: the front desk window, else the phone's Chair window. */
function current(): string | null {
  const s = useDesk.getState();
  const f = frontWindowId();
  if (f && !f.startsWith("chair:") && !s.panelMin.includes(f)) return f;
  return useChairWindows.getState().phone || null;
}
function show(id: string) {
  if (id.startsWith("chair:")) { openChairWindow(id); return; }
  const s = useDesk.getState();
  if (s.panelMin.includes(id)) s.restorePanel(id); else s.focusPanel(id);
}
function step(dir: 1 | -1): string | null {
  const r = ring();
  if (r.length < 2) return null;
  const at = Math.max(0, r.findIndex((w) => w.id === current()));
  const next = r[(at + dir + r.length) % r.length];
  show(next.id);
  return next.id;
}

/* Q1: the swipe. Horizontal, on the front window, more than 64 px and twice as wide as tall. */
let t0: { x: number; y: number; t: number } | null = null;
document.addEventListener("touchstart", (e) => {
  if (!compactNow() || e.touches.length !== 1) { t0 = null; return; }
  const el = (e.target as Element | null)?.closest?.(".desk-window-shell");
  if (!el || (e.target as Element).closest("input, textarea, select, [role=menu], .desk-dock")) { t0 = null; return; }
  t0 = { x: e.touches[0].clientX, y: e.touches[0].clientY, t: performance.now() };
}, { capture: true, passive: true });
document.addEventListener("touchend", (e) => {
  if (!t0) return;
  const t = e.changedTouches[0];
  const dx = t.clientX - t0.x, dy = t.clientY - t0.y;
  t0 = null;
  if (Math.abs(dx) < 64 || Math.abs(dx) < 2 * Math.abs(dy)) return;
  G.__c7LastSwipe = { dir: dx < 0 ? "next" : "previous", to: step(dx < 0 ? 1 : -1) };
}, { capture: true, passive: true });

/* Q2: the switcher in the screen title. */
function Switcher({ name }: { name: string }) {
  useAllOpenWindows();
  useChairWindows((s) => s.phone);
  useDesk((s) => s.panelOrder);
  const [at, setAt] = useState<{ x: number; y: number } | null>(null);
  const cur = current();
  const entries: WorkMenuEntry[] = ring().map((w) => ({
    type: "item" as const, id: `c7-win-${w.id}`, label: w.label, checked: w.id === cur, onSelect: () => show(w.id),
  }));
  return (
    <span className="desk-screen-title" data-testid="desk-screen-title">
      <Button variant="chrome" className="desk-screen-name c7-switcher" aria-haspopup="menu" aria-expanded={Boolean(at)}
        aria-label={`Windows: ${name}`} data-testid="c7-switcher"
        onClick={(e) => { const r = (e.currentTarget as HTMLElement).getBoundingClientRect(); setAt(at ? null : { x: r.left, y: r.bottom }); }}>
        {name} ▾
      </Button>
      {at ? <WorkMenu className="desk-head-menu" label="Open windows" x={at.x} y={at.y} entries={entries} onClose={() => setAt(null)} /> : null}
    </span>
  );
}
function ScreenTitleSeat({ name }: { name: string }) {
  const compact = useCompactViewport();
  return compact ? <Switcher name={name} /> : null;
}
G.__c7ScreenTitle = (name: string) => (compactNow() ? <ScreenTitleSeat name={name} /> : null);

/* Q3: Go, grouped. `menuEntries(id, out)` is DeskMenuBar's own builder (the one registry). */
G.__c7GoGroups = (out: WorkMenuEntry[], menuEntries: (id: string, out: WorkMenuEntry[]) => void) => {
  const group = (id: string) => { const e: WorkMenuEntry[] = []; menuEntries(id, e); return e; };
  const win = group("window");
  const chairAt = win.findIndex((e) => e.type === "sub" && e.label === "Chair");
  const chair = chairAt >= 0 ? win.splice(chairAt, 1)[0] : null;
  while (win.length && win[win.length - 1].type === "sep") win.pop();
  const heads: WorkMenuEntry[] = [
    ...(chair ? [chair] : []),
    { type: "sub", id: "c7-go-desk", label: "Desk", entries: group("desk") },
    { type: "sub", id: "c7-go-object", label: "Object", entries: group("object") },
    { type: "sub", id: "c7-go-window", label: "Window", entries: win },
    { type: "sep", id: "c7-go-sep" },
  ];
  out.unshift(...heads);
};

/* Q4: an arriving aftercare card opens Capture at 393. */
G.__c7Aftercare = (next: unknown, was: unknown) => {
  if (next && !was && compactNow() && useChairState.getState().surface === "chair") openChairWindow("chair:capture");
};

/* rig reads (no behaviour) */
G.__c7 = { ring: () => ring(), current: () => current(), step };
