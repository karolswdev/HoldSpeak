/* PHILO-13-11 (C1) — the proposed Workbench look, drawn on the REAL product.
 *
 * Loaded only in CANVAS_MODE=proposal (vite.config.mjs). Every seat in the
 * product calls one `globalThis.__p13*` function defined here. The build
 * moves each piece into the named product file (design/workbench-look.md).
 *
 * WHAT IS REAL: every window body, every list, every count, the brief, the
 * meetings, the people, the projects (a real hub on a scratch HOME, seeded
 * through the product's producers and routes).
 *
 * WHAT IS A STAND-IN (named, so no board claims more than it shows):
 *   - The depth gadget sends a window to the back by reordering the store's
 *     panelOrder here (C2 builds depth in compositorSlice.ts).
 *   - AppIcon live state: `REC 12:04` on Meetings, `1:1 14:30` on People and
 *     the per-project counts are fixed values set by the rig (C3 reads them
 *     from the bus; A3 makes REC honest).
 *   - Park and Restore keep the parked set in this module: no request is sent
 *     (H-A1 builds the routes). The real Delete is never called by the canvas.
 */
import {
  Children,
  isValidElement,
  useState,
  useSyncExternalStore,
  type ReactElement,
  type ReactNode,
} from "react";
import { Button } from "@w/components/signal/Signal";
import { useDesk } from "@w/desk/store";
import { useOpenWindows } from "@w/desk/components/window/windowRegistry";
import { WorkMenu, type WorkMenuEntry } from "@w/desk/components/DeskMenu";
import { verbById, verbLabel } from "@w/desk/verbRegistry";
import {
  SurfaceLedger,
  SurfaceLedgerRow,
  CheckGadget,
} from "@w/desk/surface";
import { useCompactViewport } from "@w/desk/useCompactViewport";
import { openProjectRoom, openSurfaceOr } from "@w/desk/shell";
import { SYSTEM, DOCK_SPRITES } from "@w/desk/systemSprites";
import { createRoot } from "react-dom/client";
import { StateChip, EgressChip } from "@w/desk/surface";
import css from "./canvas.css?inline";

const G = globalThis as any;

/* ── the proposed material: injected LAST so it reads as the product's own rules ── */
const style = document.createElement("style");
style.id = "p13-material";
style.textContent = css;
const keepLast = () => {
  if (document.head.lastElementChild !== style) document.head.appendChild(style);
};
keepLast();
new MutationObserver(keepLast).observe(document.head, { childList: true });
if (import.meta.hot) import.meta.hot.accept();

/* ── one tiny store for the canvas-only state ── */
type ParkKind = "meetings" | "workbench";
type Parked = { id: string; title: string; at: string; detail?: string };
const S = {
  tick: 0,
  chairOrder: ["capture", "week", "brief", "needs"] as string[],
  chairZoom: {} as Record<string, boolean>,
  chairClosed: {} as Record<string, boolean>,
  phoneOpen: "needs",
  deskFront: false,
  frontName: "Chair",
  needsYou: null as number | null,
  parked: { meetings: [] as Parked[], workbench: [] as Parked[] },
  parkedOn: { meetings: false, workbench: false },
  outcome: { meetings: null, workbench: null } as Record<string, unknown>,
  failRestore: false,
  claimed: [] as string[],
  live: { tags: {} as Record<string, { text: string; tone?: "rec" | "ok" | "fail" | "warn" }>, offline: null as string | null, projects: {} as Record<string, number> },
};
const subs = new Set<() => void>();
const bump = () => { S.tick++; subs.forEach((f) => f()); };
function useP13() {
  return useSyncExternalStore((cb) => { subs.add(cb); return () => subs.delete(cb); }, () => S.tick);
}
const clock = () => {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
};

/* THE ONE FRONT WINDOW: the top visible shell (a desk window above the Chair's
   windows; among the Chair's, the top of their order). It wears the blue frame
   and names the screen. Read from the DOM, so the title cannot disagree with
   the glass. */
function markFront() {
  const shown = [...document.querySelectorAll<HTMLElement>(".desk-window-shell")].filter((e) => {
    if (e.closest(".p13-sample-stack")) return false;
    const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(e).display !== "none" && getComputedStyle(e).opacity !== "0";
  });
  const z = (e: HTMLElement) => Number(getComputedStyle(e).zIndex) || 0;
  const tier = (e: HTMLElement) => (e.classList.contains("p13-sheet") ? 2 : e.classList.contains("p13-chairwin") ? 0 : 1);
  let top: HTMLElement | null = null;
  for (const e of shown) if (!top || tier(e) > tier(top) || (tier(e) === tier(top) && z(e) > z(top))) top = e;
  if (top && top.classList.contains("p13-chairwin") && S.deskFront === false) {
    const key = S.chairOrder[S.chairOrder.length - 1];
    top = shown.find((e) => e.dataset.win === key) ?? top;
  }
  for (const e of shown) if (e !== top) e.removeAttribute("data-p13-front");
  if (top && !top.hasAttribute("data-p13-front")) top.setAttribute("data-p13-front", "");
  const name = top?.getAttribute("aria-label") ?? "Chair";
  if (name !== S.frontName) { S.frontName = name; bump(); }
}
setInterval(markFront, 150);

/* A desk window that comes to the front takes the screen title back from the Chair. */
let lastOrder = (useDesk.getState() as any).panelOrder;
useDesk.subscribe((st: any) => {
  if (st.panelOrder !== lastOrder) { lastOrder = st.panelOrder; S.deskFront = true; bump(); }
});

/* ── the gadget glyphs (Workbench 2.0 shapes, drawn crisp at 1x and 2x) ── */
type GlyphKind = "close" | "iconify" | "zoom" | "depth" | "size";
export function GadgetGlyph({ kind }: { kind: GlyphKind }) {
  const p = { width: 14, height: 12, viewBox: "0 0 14 12", "aria-hidden": true, shapeRendering: "crispEdges" } as const;
  switch (kind) {
    case "close": // WB 2.0: a small square in the middle of the gadget
      return <svg {...p}><rect x="4.5" y="3.5" width="5" height="5" fill="var(--wb-paper)" stroke="var(--wb-ink)" /></svg>;
    case "iconify": // WB 3.9: the window falls to a small block, bottom-left
      return <svg {...p}><rect x="1.5" y="1.5" width="11" height="9" fill="none" stroke="var(--wb-ink)" /><rect x="2" y="7" width="5" height="3" fill="var(--wb-ink)" /></svg>;
    case "zoom": // WB 2.0: a small rect at the top-left of a big rect
      return <svg {...p}><rect x="1.5" y="1.5" width="11" height="9" fill="var(--wb-paper)" stroke="var(--wb-ink)" /><rect x="2" y="2" width="5" height="4" fill="var(--wb-ink)" /></svg>;
    case "depth": // WB 2.0: two overlapping rects; the front one filled
      return <svg {...p}><rect x="1.5" y="1.5" width="7" height="6" fill="none" stroke="var(--wb-ink)" /><rect x="5.5" y="4.5" width="7" height="6" fill="var(--wb-paper)" stroke="var(--wb-ink)" /></svg>;
    case "size": // WB 2.0: the sizing gadget, two nested corners
      return <svg {...p}><rect x="5.5" y="4.5" width="7" height="6" fill="var(--wb-paper)" stroke="var(--wb-ink)" /><path d="M2.5 9.5V1.5h8" fill="none" stroke="var(--wb-ink)" /></svg>;
  }
}

function Gadget({ kind, label, onClick }: { kind: GlyphKind; label: string; onClick: () => void }) {
  return (
    <Button variant="chrome" className={`p13-gadget p13-g-${kind}`} aria-label={label} title={label} onClick={onClick}>
      <GadgetGlyph kind={kind} />
    </Button>
  );
}

/* Depth (stand-in for C2): the window goes behind every peer. */
function toBack(id: string) {
  const s = useDesk.getState() as any;
  useDesk.setState({ panelOrder: [id, ...s.panelOrder.filter((x: string) => x !== id)] } as any);
  S.deskFront = true;
  bump();
}

/* (1) ONE gadget set for every DeskWindowFrame host: close at the left; iconify,
   zoom and depth at the right. At 393 a window is a sheet: close and depth. */
G.__p13Gadgets = (side: "left" | "right", w: { id: string; name: string; compact: boolean; maximized: boolean; requestClose: () => void; requestMinimize: () => void }) => {
  if (side === "left") return <span className="p13-gadgets p13-gadgets-left"><Gadget kind="close" label={`Close ${w.name}`} onClick={w.requestClose} /></span>;
  return (
    <span className="p13-gadgets p13-gadgets-right">
      {w.compact ? null : <Gadget kind="iconify" label={`Iconify ${w.name}`} onClick={w.requestMinimize} />}
      {w.compact ? null : <Gadget kind="zoom" label={`Zoom ${w.name}`} onClick={() => useDesk.getState().toggleMaximizePanel(w.id)} />}
      <Gadget kind="depth" label={`To back ${w.name}`} onClick={() => toBack(w.id)} />
    </span>
  );
};

/* C1-2: right button = the window's menu bar, at the pointer, with the Amiga-key column. */
function registryItem(id: string, label?: string): WorkMenuEntry | null {
  const v = verbById(id);
  if (!v) return null;
  return { type: "item", id: v.id, label: label ?? verbLabel(v, { selectedRef: null }), keycap: v.key, onSelect: () => v.run({ selectedRef: null }) };
}
function windowMenu(id: string, base: WorkMenuEntry[]): WorkMenuEntry[] {
  const pick = (vid: string) => base.find((e) => e.type === "item" && e.id === vid) as Extract<WorkMenuEntry, { type: "item" }> | undefined;
  const min = pick("window.minimize");
  const max = pick("window.maximize");
  const close = pick("window.close");
  const items: WorkMenuEntry[] = [];
  if (min) items.push({ ...min, label: "Iconify", glyph: <GadgetGlyph kind="iconify" /> });
  if (max) items.push({ ...max, label: "Zoom", keycap: "⌃M", glyph: <GadgetGlyph kind="zoom" /> });
  items.push({ type: "item", id: "window.depth", label: "To back", keycap: "⌃B", glyph: <GadgetGlyph kind="depth" />, onSelect: () => toBack(id) });
  if (close) items.push({ type: "sep", id: "w-sep" }, { ...close, glyph: <GadgetGlyph kind="close" /> });
  const desk = ["desk.new-note", "desk.new-decision", "system.search", "system.sheet"].map((v) => registryItem(v)).filter(Boolean) as WorkMenuEntry[];
  const go = ["desk.open-intelligence", "desk.open-people", "desk.overview"].map((v) => registryItem(v)).filter(Boolean) as WorkMenuEntry[];
  return [
    ...items,
    { type: "sep", id: "bar-sep" },
    { type: "sub", id: "bar-desk", label: "Desk", entries: desk },
    { type: "sub", id: "bar-go", label: "Go", entries: go },
  ];
}
G.__p13HeadMenu = (id: string, _name: string, base: WorkMenuEntry[]) => windowMenu(id, base);

/* (2) The screen title bar: the front window's name, always. */
function ScreenTitle() {
  useP13();
  const front = S.frontName;
  return (
    <span className="p13-screen-title" data-testid="p13-screen-title" aria-label={`Front window: ${front}`}>
      <span className="p13-screen-name">{front}</span>
    </span>
  );
}
G.__p13ScreenTitle = () => <ScreenTitle />;

/* (4) The Chair composed of windows. The Arrival's REAL sections are routed into
   windows by their test ids; nothing in a section is redrawn.
   ONE WINDOW LIFECYCLE (Muad'Dib R1): close CLOSES a Chair window; depth sends it back.
   A closed Chair window comes back from Window ▸ Chair (a check on the open ones) or
   from the compact reopen Button the Chair's screen draws where the window was.
   THE PHONE (R2): one window at a time fills the work area; Capture is on demand (Speak). */
const CHAIR_WINDOWS = [
  { key: "needs", title: "Needs you", ids: ["arrival-headline", "arrival-blocker", "arrival-coverage", "arrival-needs-you", "arrival-muted"] },
  { key: "brief", title: "Brief", ids: ["arrival-brief"] },
  { key: "week", title: "The week", ids: ["WeekStripSection", "arrival-this-week", "arrival-orphan-section", "arrival-meetings", "arrival-thoughts", "arrival-agents"] },
  { key: "capture", title: "Capture", ids: ["CaptureBar", "arrival-aftercare-slot"] },
];
function routeOf(el: ReactElement): string {
  const id = (el.props as any)?.["data-testid"] ?? (el.type as any)?.name ?? "";
  return CHAIR_WINDOWS.find((w) => w.ids.includes(id))?.key ?? "needs";
}
function chairRaise(key: string) {
  S.chairOrder = [...S.chairOrder.filter((k) => k !== key), key];
  S.deskFront = false;
  S.phoneOpen = key;
}
function chairOpen(key: string) { S.chairClosed[key] = false; chairRaise(key); bump(); }
function chairClose(key: string) {
  S.chairClosed[key] = true;
  S.chairZoom[key] = false;
  // the phone shows the next open Chair window (the top of the order)
  const next = [...S.chairOrder].reverse().find((k) => !S.chairClosed[k] && k !== "capture");
  if (S.phoneOpen === key) S.phoneOpen = next ?? "";
  bump();
}
function chairBack(key: string) { S.chairOrder = [key, ...S.chairOrder.filter((k) => k !== key)]; bump(); }
function ChairWindow({ win, children, compact }: { win: (typeof CHAIR_WINDOWS)[number]; children: ReactNode; compact: boolean }) {
  useP13();
  const [menu, setMenu] = useState<{ x: number; y: number } | null>(null);
  const z = S.chairOrder.indexOf(win.key);
  const zoomed = Boolean(S.chairZoom[win.key]);
  const closed = Boolean(S.chairClosed[win.key]);
  if (compact && (win.key === "capture" || S.phoneOpen !== win.key)) return null; // one window at a time
  if (closed) {
    // the closed window's place on the Chair's screen holds its reopen Button
    return (
      <div className="p13-chair-closed" data-win={win.key} data-testid={`p13-chair-closed-${win.key}`}>
        <Button dense onClick={() => chairOpen(win.key)} aria-label={`Open ${win.title}`}>
          <GadgetGlyph kind="zoom" /> {win.title}
        </Button>
      </div>
    );
  }
  const zoom = () => { S.chairZoom[win.key] = !zoomed; chairRaise(win.key); bump(); };
  const entries: WorkMenuEntry[] = [
    { type: "item", id: "c-zoom", label: "Zoom", keycap: "⌃M", glyph: <GadgetGlyph kind="zoom" />, onSelect: zoom },
    { type: "item", id: "c-back", label: "To back", keycap: "⌃B", glyph: <GadgetGlyph kind="depth" />, onSelect: () => chairBack(win.key) },
    { type: "sep", id: "c-sep" },
    { type: "item", id: "c-close", label: "Close window", keycap: "⌘W", glyph: <GadgetGlyph kind="close" />, onSelect: () => chairClose(win.key) },
  ];
  return (
    <section
      className="desk-window desk-window-shell p13-chairwin"
      data-win={win.key}
      data-zoomed={zoomed && !compact ? "true" : undefined}
      data-phone-open={compact ? "" : undefined}
      data-testid={`p13-chair-${win.key}`}
      style={{ zIndex: 20 + z }}
      onPointerDown={() => { chairRaise(win.key); bump(); }}
      role="region"
      aria-label={win.title}
    >
      <header
        className="desk-pullout-head desk-window-handle"
        onContextMenu={(e) => { e.preventDefault(); setMenu({ x: e.clientX, y: e.clientY }); }}
      >
        <span className="p13-gadgets p13-gadgets-left"><Gadget kind="close" label={`Close ${win.title}`} onClick={() => chairClose(win.key)} /></span>
        <span className="desk-pullout-title desk-window-title">{win.title}</span>
        <span className="p13-gadgets p13-gadgets-right">
          {compact ? null : <Gadget kind="zoom" label={`Zoom ${win.title}`} onClick={zoom} />}
          <Gadget kind="depth" label={`To back ${win.title}`} onClick={() => chairBack(win.key)} />
        </span>
      </header>
      {menu ? <WorkMenu className="desk-head-menu" label={`${win.title} window menu`} x={menu.x} y={menu.y} entries={entries} onClose={() => setMenu(null)} /> : null}
      <div className="desk-surface-body p13-chairwin-body">{children}</div>
      {compact ? null : <span className="p13-sizer" aria-hidden="true"><GadgetGlyph kind="size" /></span>}
    </section>
  );
}
function ChairDesk({ children }: { children: ReactNode }) {
  useP13();
  const compact = useCompactViewport();
  const groups: Record<string, ReactNode[]> = { needs: [], brief: [], week: [], capture: [] };
  Children.forEach(children, (c) => {
    if (!isValidElement(c)) return;
    groups[routeOf(c)].push(c);
  });
  const noneOpen = compact && (!S.phoneOpen || S.chairClosed[S.phoneOpen]);
  return (
    <div className="p13-chairdesk" data-testid="p13-chairdesk">
      {CHAIR_WINDOWS.map((w) => (
        <ChairWindow key={w.key} win={w} compact={compact}>{groups[w.key]}</ChairWindow>
      ))}
      {noneOpen ? (
        <div className="p13-chair-reopen-list">
          {CHAIR_WINDOWS.filter((w) => w.key !== "capture").map((w) => (
            <Button key={w.key} onClick={() => chairOpen(w.key)} aria-label={`Open ${w.title}`}>{w.title}</Button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
/* Window ▸ Chair (and, at 393, inside Go): the four Chair windows, a check on each open one.
   Picking one opens it if closed and brings it to the front. */
G.__p13ChairMenu = (out: WorkMenuEntry[], compact: boolean) => {
  const sub: WorkMenuEntry = {
    type: "sub", id: "chair-windows", label: "Chair",
    entries: CHAIR_WINDOWS.filter((w) => !compact || w.key !== "capture").map((w) => ({
      type: "item" as const, id: `chair-${w.key}`, label: w.title, checked: !S.chairClosed[w.key],
      onSelect: () => {
        // at 393 one window at a time: the window in front iconifies to its Dock chip (never closed)
        if (compact) { const st = useDesk.getState() as any; for (const id of st.panelOrder) if (!st.panelMin.includes(id)) st.minimizePanel(id); }
        chairOpen(w.key);
      },
    })),
  };
  if (compact) out.unshift(sub, { type: "sep", id: "chair-sep" });
  else out.push({ type: "sep", id: "chair-sep" }, sub);
};
G.__p13ChairDesk = ChairDesk;

/* (A2, drawn fixed) ONE number for "needs you": the Chair's membership (story 03, R1 + R2 + R3)
   is published here; the bell, the Dock's Intelligence icon and the Desk memory icon read it.
   Stand-in for needsYou.ts (H-A2), which the build reads instead. */
G.__p13PublishNeedsYou = (n: number) => {
  if (S.needsYou === n) return;
  S.needsYou = n;
  queueMicrotask(bump);
};
G.__p13UseNeedsYou = (): number | undefined => {
  useP13();
  return S.needsYou ?? undefined;
};

/* (7) AppIcons: live state drawn on the icon (C3's states; the values are stand-ins).
   A tag sits on the icon that owns the thing: REC / READY / SENT / SEND FAILED / UNKNOWN on
   Meetings or Intelligence (the window the send left from), 1:1 on People. Disconnected: no
   tag and no count claims to be fresh; one OFFLINE · AS OF hh:mm tag heads the shelf. */
type Tag = { text: string; tone?: "rec" | "ok" | "fail" | "warn" };
function TagView({ t }: { t: Tag }) {
  const compact = useCompactViewport();
  // 393: a tag never runs wider than its 85 px icon ("SEND FAILED" → "FAILED"; the icon's name says Meetings)
  const text = compact ? t.text.replace(/^SEND FAILED$/, "FAILED") : t.text;
  return <span className="p13-appstate" data-tone={t.tone} data-p13-standin="C3">{text}</span>;
}
function AppState({ windowId }: { windowId: string }) {
  useP13();
  const t = S.live.tags[windowId];
  if (!t || S.live.offline) return null;
  return <TagView t={t} />;
}
G.__p13AppState = (windowId: string) => <AppState windowId={windowId} />;

function AppIcons() {
  useP13();
  const compact = useCompactViewport();
  const projects = useDesk((s) => ((s as any).items?.project ?? []) as Array<{ id: string; title?: string; name?: string }>);
  const people = S.live.tags["surface-people"];
  return (
    <>
      {S.live.offline ? (
        <span className="p13-offline" data-testid="p13-offline" role="status">{`OFFLINE · AS OF ${S.live.offline}`}</span>
      ) : null}
      <Button variant="chrome" className="desk-dock-launch desk-dock-app p13-appicon" aria-label={people && !S.live.offline ? `People, ${people.text}` : "People"}
        onClick={() => openSurfaceOr("open-people", "/")}>
        <img src={SYSTEM.dockPeople} alt="" width={32} height={32} className="desk-dock-sprite" draggable={false} />
        <span className="desk-dock-label">People</span>
        {people && !S.live.offline ? <TagView t={people} /> : null}
      </Button>
      {/* every active project keeps its AppIcon; a count only when it is not zero (A.8) */}
      {projects.map((p) => {
        const n = S.live.projects[p.id] ?? 0;
        const name = p.title ?? p.name;
        return (
          <Button key={p.id} variant="chrome" className="desk-dock-launch desk-dock-app p13-appicon p13-appicon-project"
            data-project={p.id} aria-label={n ? `${name}, ${n} need you` : String(name)} onClick={() => openProjectRoom(p.id)}>
            <img src="/desk/sprites/drawer.png" alt="" width={32} height={32} className="desk-dock-sprite" draggable={false} />
            <span className="desk-dock-label">{name}</span>
            {n ? <span className="desk-chip desk-dock-badge" data-tone="warn" data-p13-standin="C3">{n}</span> : null}
          </Button>
        );
      })}
      {compact ? (
        /* 393: the shelf ends on a whole icon; this gadget says there is more and moves one page. */
        <Button variant="chrome" className="p13-dock-more" aria-label="More AppIcons" data-testid="p13-dock-more"
          onClick={(e) => { const d = (e.currentTarget as HTMLElement).closest(".desk-dock") as HTMLElement | null; d?.scrollBy({ left: d.clientWidth - 48, behavior: "smooth" }); }}>
          <span aria-hidden="true">▸</span>
        </Button>
      ) : null}
    </>
  );
}
G.__p13AppIcons = () => <AppIcons />;

/* (A1-F) Parked and Restore. Park replaces Delete; every outcome is a compact receipt in the
   footer's receipt slot (the existing surface-footer-receipt-line species):
     PARKED hh:mm + Restore · PARKED n · hh:mm + Restore (bulk) · RESTORED hh:mm (the row comes
     into view, selected) · NOT RESTORED · <reason> + Retry · NOT PARKED · CLAIMED BY A RUN. */
type Outcome = { kind: "parked" | "bulk" | "restored" | "restore-failed" | "refused"; text: string; ids: string[]; tone?: "danger" };
G.__p13UseTick = () => useP13();
G.__p13ParkedOn = (kind: ParkKind) => S.parkedOn[kind];
G.__p13Unparked = <T extends { id?: unknown }>(kind: ParkKind, rows: T[], ignoreFilter = false): T[] => {
  if (S.parkedOn[kind] && !ignoreFilter) return [];
  const gone = new Set(S.parked[kind].map((p) => p.id));
  return rows.filter((r) => !gone.has(String(r.id)));
};
function setOutcome(kind: ParkKind, o: Outcome) { (S.outcome as any)[kind] = o; bump(); }
function park(kind: ParkKind, items: Array<{ id: string; title: string }>) {
  const claimed = items.filter((i) => S.claimed.includes(i.title));
  if (claimed.length) {
    setOutcome(kind, { kind: "refused", text: "NOT PARKED · CLAIMED BY A RUN", ids: [], tone: "danger" });
    return;
  }
  const at = clock();
  const ps = items.map((i) => ({ id: String(i.id), title: String(i.title), at }));
  S.parked[kind] = [...ps, ...S.parked[kind].filter((x) => !ps.some((p) => p.id === x.id))];
  setOutcome(kind, items.length > 1
    ? { kind: "bulk", text: `PARKED ${items.length} · ${at}`, ids: ps.map((p) => p.id) }
    : { kind: "parked", text: `PARKED ${at}`, ids: ps.map((p) => p.id) });
}
function restore(kind: ParkKind, ids: string[]) {
  if (S.failRestore) {
    setOutcome(kind, { kind: "restore-failed", text: "NOT RESTORED · THE HUB DID NOT ACCEPT THE CHANGE", ids, tone: "danger" });
    return;
  }
  const titles = S.parked[kind].filter((x) => ids.includes(x.id)).map((x) => x.title);
  S.parked[kind] = S.parked[kind].filter((x) => !ids.includes(x.id));
  if (!S.parked[kind].length) S.parkedOn[kind] = false;
  setOutcome(kind, { kind: "restored", text: `RESTORED ${clock()}`, ids });
  // the restored row comes into view, marked as the selection
  window.setTimeout(() => {
    const host = kind === "meetings" ? document.querySelector('.desk-window-shell[aria-label="Meetings"]') : document.querySelector(".desk-window-shell[data-p13-front]");
    const leaf = host && [...host.querySelectorAll("*")].find((e) => e.children.length === 0 && titles.includes((e.textContent || "").trim()));
    const row = leaf?.closest(".surface-ledger-row, .wb-item, [class*=row], [class*=card]") as HTMLElement | null;
    (row ?? (leaf as HTMLElement | null))?.scrollIntoView({ block: "center" });
    if (row) row.dataset.p13Restored = "";
  }, 350);
}
G.__p13ParkVerb = (kind: ParkKind, row: any, after: () => void) => (
  <Button dense variant="ghost" data-testid="p13-park" onClick={() => { park(kind, [{ id: String(row.id), title: String(row.title ?? row.name ?? "Untitled") }]); after(); }}>
    Park
  </Button>
);
G.__p13Park = (kind: ParkKind, item: { id: string; title: string }) => { park(kind, [item]); return true; };
G.__p13ParkMany = (kind: ParkKind, items: Array<{ id: string; title: string }>) => { park(kind, items); return true; };
function ParkReceipt({ kind }: { kind: ParkKind }) {
  useP13();
  const o = (S.outcome as any)[kind] as Outcome | null;
  if (!o) return null;
  return (
    <span className="p13-park-receipt" data-testid={`p13-park-receipt-${kind}`} data-outcome={o.kind}>
      <span className="surface-footer-receipt-line" role="status" data-tone={o.tone}>{o.text}</span>
      {o.kind === "parked" || o.kind === "bulk" ? <Button dense variant="ghost" onClick={() => restore(kind, o.ids)}>Restore</Button> : null}
      {o.kind === "restore-failed" ? <Button dense variant="ghost" onClick={() => { S.failRestore = false; restore(kind, o.ids); }}>Retry</Button> : null}
    </span>
  );
}
G.__p13Receipt = (kind: ParkKind) => ((S.outcome as any)[kind] ? <ParkReceipt kind={kind} /> : null);
G.__p13FootVerbs = (kind: ParkKind) => ((S.outcome as any)[kind] ? <ParkReceipt kind={kind} /> : undefined);
function ParkedStrip({ kind }: { kind: ParkKind }) {
  useP13();
  const list = S.parked[kind];
  if (!list.length) return null; // no counter of zero: no PARKED token until something is parked
  return (
    <div className="p13-parked" data-testid={`p13-parked-${kind}`}>
      <div className="meetings-facets p13-parked-facet">
        <CheckGadget label={`PARKED ${list.length}`} variant="token" checked={S.parkedOn[kind]}
          onChange={(next) => { S.parkedOn[kind] = next; bump(); }} />
      </div>
      {S.parkedOn[kind] ? (
        <SurfaceLedger count={null} cols="room">
          {list.map((p) => (
            <SurfaceLedgerRow key={p.id} time={p.at} primary={p.title}
              cells={<span className="desk-chip p13-parked-chip">PARKED</span>}
              trailing={<Button dense variant="ghost" onClick={() => restore(kind, [p.id])}>Restore</Button>}
              expands={false} data-testid="p13-parked-row" />
          ))}
        </SurfaceLedger>
      ) : null}
    </div>
  );
}
G.__p13ParkedStrip = (kind: ParkKind) => <ParkedStrip kind={kind} />;
/* Bulk park's verb: the voice intent "Clear done" made visible while done items exist. */
G.__p13ClearDone = (items: Array<{ status?: string }>, run: () => void) => {
  const done = items.filter((i) => i.status === "done" || i.status === "dismissed").length;
  return done ? <div className="p13-clear-done"><Button dense variant="ghost" data-testid="p13-clear-done" onClick={run}>Clear done</Button></div> : null;
};

/* C1-3: THE MATERIAL SHEET — the tokens, drawn with the species that wear them.
   Every value is read back from the live :root, so the sheet cannot drift from the CSS. */
const PENS: Array<[string, string]> = [
  ["--wb-steel", "PEN 0 · FRAME"],
  ["--wb-ink", "PEN 1 · LINE + WORD"],
  ["--wb-paper", "PEN 2 · SCREEN + MENU"],
  ["--wb-blue", "PEN 3 · FRONT WINDOW"],
  ["--wb-backdrop", "CHAIR SCREEN"],
  ["--surface-1", "WINDOW WELL"],
  ["--accent-ink", "VERB + ATTENTION"],
  ["--wb-rec", "REC"],
];
const SIZES: Array<[string, string]> = [
  ["--wb-screen-h", "SCREEN BAR"],
  ["--wb-bar-h", "TITLE BAR"],
  ["--wb-gadget-w", "GADGET"],
  ["--wb-frame", "FRAME"],
];
function tok(name: string) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
function Bar({ title, front }: { title: string; front?: boolean }) {
  return (
    <div className={`desk-window-shell p13-sample-win${front ? " is-front" : ""}`} data-p13-front={front ? "" : undefined}>
      <header className="desk-pullout-head">
        <span className="p13-gadgets p13-gadgets-left"><Gadget kind="close" label={`Close ${title}`} onClick={() => undefined} /></span>
        <span className="desk-pullout-title desk-window-title">{title}</span>
        <span className="p13-gadgets p13-gadgets-right">
          <Gadget kind="iconify" label={`Iconify ${title}`} onClick={() => undefined} />
          <Gadget kind="zoom" label={`Zoom ${title}`} onClick={() => undefined} />
          <Gadget kind="depth" label={`To back ${title}`} onClick={() => undefined} />
        </span>
      </header>
      <div className="p13-sample-body">{front ? "FRONT" : "BEHIND"}</div>
      <span className="p13-sizer" aria-hidden="true"><GadgetGlyph kind="size" /></span>
    </div>
  );
}
function Sheet() {
  useP13();
  return (
    <div className="p13-sheet-host">
      <section className="desk-window desk-window-shell p13-chairwin p13-sheet" data-phone-open="" data-testid="p13-sheet" role="region" aria-label="Material">
        <header className="desk-pullout-head desk-window-handle">
          <span className="p13-gadgets p13-gadgets-left"><Gadget kind="close" label="Close Material" onClick={() => G.__p13.sheet(false)} /></span>
          <span className="desk-pullout-title desk-window-title">Material · Workbench Steel</span>
          <span className="p13-gadgets p13-gadgets-right">
            <Gadget kind="zoom" label="Zoom Material" onClick={() => undefined} />
            <Gadget kind="depth" label="To back Material" onClick={() => G.__p13.sheet(false)} />
          </span>
        </header>
        <div className="desk-surface-body p13-chairwin-body p13-sheet-body">
          <div className="p13-sheet-group" data-testid="p13-sheet-pens">
            <span className="surface-section-label p13-cap">PENS</span>
            <div className="p13-swatches">
              {PENS.map(([n, role]) => (
                <div key={n} className="p13-swatch">
                  <span className="p13-swatch-chip" style={{ background: `var(${n})` }} />
                  <span className="p13-swatch-name">{n}</span>
                  <span className="p13-swatch-val">{tok(n)}</span>
                  <span className="p13-swatch-role">{role}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="p13-sheet-row">
            <div className="p13-sheet-group">
              <span className="p13-cap">GADGETS</span>
              <div className="p13-gadget-row">
                {([["close", "CLOSE", "⌘W"], ["iconify", "ICONIFY", "⌘M"], ["zoom", "ZOOM", "⌃M"], ["depth", "TO BACK", "⌃B"], ["size", "SIZE", "DRAG"]] as const).map(([k, l, key]) => (
                  <div key={k} className="p13-gadget-cell">
                    <span className="p13-gadget-big"><GadgetGlyph kind={k} /></span>
                    <span className="p13-swatch-name">{l}</span>
                    <kbd className="desk-menu-well">{key}</kbd>
                  </div>
                ))}
              </div>
            </div>
            <div className="p13-sheet-group">
              <span className="p13-cap">BEVEL</span>
              <div className="p13-gadget-row">
                <div className="p13-gadget-cell"><span className="p13-bevel" data-b="raised" /><span className="p13-swatch-name">--wb-raised</span></div>
                <div className="p13-gadget-cell"><span className="p13-bevel" data-b="sunken" /><span className="p13-swatch-name">--wb-sunken</span></div>
                <div className="p13-gadget-cell"><span className="p13-bevel" data-b="drop" /><span className="p13-swatch-name">--wb-drop</span></div>
              </div>
            </div>
          </div>
          <div className="p13-sheet-row">
            <div className="p13-sheet-group p13-grow">
              <span className="p13-cap">WINDOWS</span>
              <div className="p13-sample-stack">
                <Bar title="Meetings" />
                <Bar title="Payments ledger cutover" front />
              </div>
            </div>
            <div className="p13-sheet-group">
              <span className="p13-cap">SIZES</span>
              <div className="p13-sizes">
                {SIZES.map(([n, l]) => (
                  <div key={n} className="p13-size"><span className="p13-swatch-name">{l}</span><span className="p13-swatch-val">{`${n} · ${tok(n)}`}</span></div>
                ))}
              </div>
            </div>
          </div>
          <div className="p13-sheet-row">
            <div className="p13-sheet-group">
              <span className="p13-cap">VERBS · LIBRARY BUTTON</span>
              <div className="p13-verbs">
                <Button variant="primary">Done</Button>
                <Button>Generate</Button>
                <Button variant="ghost">Restore</Button>
                <Button dense>Open</Button>
                <Button variant="danger" dense>Cancel</Button>
              </div>
              <div className="p13-verbs">
                <StateChip state="success" icon="●" label="ON TRACK" />
                <StateChip state="warning" label="DUE TODAY" />
                <CheckGadget label="PARKED 2" variant="token" checked onChange={() => undefined} />
                <EgressChip label="THIS DEVICE" scope="local" />
              </div>
            </div>
            <div className="p13-sheet-group">
              <span className="p13-cap">APPICONS · LIVE STATE</span>
              <div className="desk-dock p13-dock-sample">
                <span className="desk-dock-launch desk-dock-app"><img src={DOCK_SPRITES["surface-meetings"]} alt="" width={32} height={32} className="desk-dock-sprite" /><span className="desk-dock-label">Meetings</span></span>
                <span className="desk-dock-launch desk-dock-app is-run"><img src={DOCK_SPRITES["surface-meetings"]} alt="" width={32} height={32} className="desk-dock-sprite" /><span className="desk-dock-label">Meetings</span><span className="p13-appstate" data-tone="rec">● REC 12:04</span></span>
                <span className="desk-dock-launch desk-dock-app is-run is-front"><img src={SYSTEM.dockPeople} alt="" width={32} height={32} className="desk-dock-sprite" /><span className="desk-dock-label">People</span><span className="p13-appstate">1:1 14:30</span></span>
                <span className="desk-dock-launch desk-dock-app"><img src="/desk/sprites/drawer.png" alt="" width={32} height={32} className="desk-dock-sprite" /><span className="desk-dock-label">Payments ledger</span><span className="desk-chip desk-dock-badge" data-tone="warn">3</span></span>
              </div>
              <span className="p13-swatch-role">REST · RUNNING · FRONT · COUNT</span>
            </div>
          </div>
          <div className="p13-sheet-group">
            <span className="p13-cap">TYPE · 12 PX FLOOR</span>
            <div className="p13-type">
              <span className="arrival-display arrival-display--accent">8 need you · 26</span>
              <span className="p13-type-primary">Freeze the old ledger on Nov 5 · 15</span>
              <span className="p13-type-body">Dual-write is stable · 13</span>
              <span className="p13-cap">CAPTION · 12 MONO</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
let sheetRoot: ReturnType<typeof createRoot> | null = null;
let sheetHost: HTMLElement | null = null;

/* R 3b: THE STRIP MENU. At 393 a strip of more than two choices (window tabs, the ranking
   filters) is ONE library Button with the current choice and ▾, 44 px tall; it opens the
   DeskMenu species with every choice and a check on the current one. The build measures "does
   not fit"; the canvas draws the rule as "more than two choices at 393". */
type StripProps = { label: string; value: string; options: Array<{ value: string; label: string }>; onChange: (v: string) => void;
  kind: "filter" | "wings"; className?: string; door?: string; doorOpen?: boolean; onDoor?: () => void };
function StripMenu(p: StripProps) {
  const [at, setAt] = useState<{ x: number; y: number } | null>(null);
  const cur = p.options.find((o) => o.value === p.value);
  const shown = p.doorOpen && p.door ? p.door.toUpperCase() : (cur?.label ?? p.options[0]?.label ?? "");
  const entries: WorkMenuEntry[] = p.options.map((o) => ({
    type: "item" as const, id: `strip-${o.value || "all"}`, label: o.label, checked: !p.doorOpen && o.value === p.value,
    onSelect: () => p.onChange(o.value),
  }));
  if (p.door && p.onDoor) entries.push({ type: "sep", id: "strip-sep" }, { type: "item", id: "strip-door", label: p.door, checked: Boolean(p.doorOpen), onSelect: () => p.onDoor?.() });
  return (
    <span className={`p13-strip-menu p13-strip-${p.kind}${p.kind === "wings" ? " desk-wings" : ""}`} data-testid={`p13-strip-${p.kind}`}>
      <Button variant={p.kind === "wings" ? "chrome" : "secondary"} dense={p.kind !== "wings"} className="p13-strip-button" aria-haspopup="menu"
        aria-expanded={Boolean(at)} aria-label={`${p.label}: ${shown}`}
        onClick={(e) => { const r = (e.currentTarget as HTMLElement).getBoundingClientRect(); setAt(at ? null : { x: r.left, y: r.bottom }); }}>
        {shown} ▾
      </Button>
      {at ? <WorkMenu className="desk-head-menu" label={p.label} x={at.x} y={at.y} entries={entries} onClose={() => setAt(null)} /> : null}
    </span>
  );
}
G.__p13StripMenu = (p: StripProps) => {
  if (!window.matchMedia("(max-width: 720px)").matches || p.options.length <= 2) return null;
  return <StripMenu {...p} />;
};

/* ── the rig's hands (the canvas's own state; never a product write) ── */
G.__p13 = {
  live(v: Partial<typeof S.live>) {
    Object.assign(S.live, v);
    if (S.live.offline) document.documentElement.dataset.p13Offline = ""; else delete document.documentElement.dataset.p13Offline;
    bump();
  },
  chairFront(key: string) { S.chairOrder = [...S.chairOrder.filter((k) => k !== key), key]; S.deskFront = false; bump(); },
  chairZoom(key: string, on: boolean) { S.chairZoom[key] = on; bump(); },
  phoneOpen(key: string) { S.phoneOpen = key; bump(); },
  deskFront() { S.deskFront = true; bump(); },
  parkedOn(kind: ParkKind, on: boolean) { S.parkedOn[kind] = on; bump(); },
  failRestore(on: boolean) { S.failRestore = on; bump(); },
  claim(title: string) { S.claimed.push(title); bump(); },
  closeChair(key: string) { chairClose(key); },
  openChair(key: string) { chairOpen(key); },
  theme(name: string | null) {
    if (name) document.documentElement.dataset.p13Theme = name;
    else delete document.documentElement.dataset.p13Theme;
  },
  sheet(on: boolean) {
    if (on && !sheetRoot) {
      sheetHost = document.createElement("div");
      (document.querySelector(".desk-next") ?? document.body).appendChild(sheetHost);
      sheetRoot = createRoot(sheetHost);
      sheetRoot.render(<Sheet />);
    } else if (!on && sheetRoot) {
      sheetRoot.unmount(); sheetHost?.remove(); sheetRoot = null; sheetHost = null;
    }
  },
  state: () => JSON.parse(JSON.stringify({ ...S, tick: undefined })),
};
