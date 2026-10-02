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
  phoneOpen: "needs",
  deskFront: false,
  frontName: "Chair",
  needsYou: null as number | null,
  parked: { meetings: [] as Parked[], workbench: [] as Parked[] },
  parkedOn: { meetings: false, workbench: false },
  receipt: { meetings: null as Parked | null, workbench: null as Parked | null },
  live: { rec: null as string | null, oneOnOne: null as string | null, projects: {} as Record<string, number> },
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
   four windows by their test ids; nothing in a section is redrawn. */
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
function ChairWindow({ win, children, compact }: { win: (typeof CHAIR_WINDOWS)[number]; children: ReactNode; compact: boolean }) {
  useP13();
  const [menu, setMenu] = useState<{ x: number; y: number } | null>(null);
  const z = S.chairOrder.indexOf(win.key);
  const windows = useOpenWindows();
  const min = useDesk((st) => (st as any).panelMin as string[]);
  const deskShown = windows.some((w) => !min.includes(w.id));
  const front = (!S.deskFront || !deskShown) && z === S.chairOrder.length - 1;
  const zoomed = Boolean(S.chairZoom[win.key]);
  const raise = () => { S.chairOrder = [...S.chairOrder.filter((k) => k !== win.key), win.key]; S.deskFront = false; bump(); };
  const back = () => { S.chairOrder = [win.key, ...S.chairOrder.filter((k) => k !== win.key)]; bump(); };
  const zoom = () => {
    if (compact) S.phoneOpen = win.key;
    else S.chairZoom[win.key] = !zoomed;
    raise();
  };
  const entries: WorkMenuEntry[] = [
    { type: "item", id: "c-zoom", label: "Zoom", keycap: "⌃M", glyph: <GadgetGlyph kind="zoom" />, onSelect: zoom },
    { type: "item", id: "c-back", label: "To back", keycap: "⌃B", glyph: <GadgetGlyph kind="depth" />, onSelect: back },
  ];
  return (
    <section
      className="desk-window desk-window-shell p13-chairwin"
      data-win={win.key}
      data-zoomed={zoomed && !compact ? "true" : undefined}
      data-phone-open={compact && S.phoneOpen === win.key ? "" : undefined}
      data-testid={`p13-chair-${win.key}`}
      style={{ zIndex: 20 + z }}
      onPointerDown={raise}
      role="region"
      aria-label={win.title}
    >
      <header
        className="desk-pullout-head desk-window-handle"
        onContextMenu={(e) => { e.preventDefault(); setMenu({ x: e.clientX, y: e.clientY }); }}
      >
        <span className="p13-gadgets p13-gadgets-left"><Gadget kind="close" label={`Close ${win.title}`} onClick={back} /></span>
        <span className="desk-pullout-title desk-window-title">{win.title}</span>
        <span className="p13-gadgets p13-gadgets-right">
          <Gadget kind="zoom" label={`Zoom ${win.title}`} onClick={zoom} />
          <Gadget kind="depth" label={`To back ${win.title}`} onClick={back} />
        </span>
      </header>
      {menu ? <WorkMenu className="desk-head-menu" label={`${win.title} window menu`} x={menu.x} y={menu.y} entries={entries} onClose={() => setMenu(null)} /> : null}
      <div className="desk-surface-body p13-chairwin-body">{children}</div>
      {compact ? null : <span className="p13-sizer" aria-hidden="true"><GadgetGlyph kind="size" /></span>}
    </section>
  );
}
function ChairDesk({ children }: { children: ReactNode }) {
  const compact = useCompactViewport();
  const groups: Record<string, ReactNode[]> = { needs: [], brief: [], week: [], capture: [] };
  Children.forEach(children, (c) => {
    if (!isValidElement(c)) return;
    groups[routeOf(c)].push(c);
  });
  return (
    <div className="p13-chairdesk" data-testid="p13-chairdesk">
      {CHAIR_WINDOWS.map((w) => (
        <ChairWindow key={w.key} win={w} compact={compact}>{groups[w.key]}</ChairWindow>
      ))}
    </div>
  );
}
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

/* (7) AppIcons: live state drawn on the icon. */
function AppState({ windowId }: { windowId: string }) {
  useP13();
  const compact = useCompactViewport();
  if (windowId === "surface-meetings" && S.live.rec)
    return <span className="p13-appstate" data-tone="rec" data-p13-standin="C3">{`${compact ? "" : "● "}REC ${S.live.rec}`}</span>;
  return null;
}
G.__p13AppState = (windowId: string) => <AppState windowId={windowId} />;

function AppIcons() {
  useP13();
  const compact = useCompactViewport();
  const projects = useDesk((s) => ((s as any).items?.project ?? []) as Array<{ id: string; title?: string; name?: string }>);
  const shown = projects.filter((p) => S.live.projects[p.id]);
  return (
    <>
      <Button variant="chrome" className="desk-dock-launch desk-dock-app p13-appicon" aria-label={S.live.oneOnOne ? `People, 1:1 at ${S.live.oneOnOne}` : "People"}
        onClick={() => openSurfaceOr("open-people", "/")}>
        <img src={SYSTEM.dockPeople} alt="" width={32} height={32} className="desk-dock-sprite" draggable={false} />
        <span className="desk-dock-label">People</span>
        {S.live.oneOnOne ? <span className="p13-appstate" data-tone="next" data-p13-standin="C3">{`1:1 ${S.live.oneOnOne}`}</span> : null}
      </Button>
      {shown.map((p) => (
        <Button key={p.id} variant="chrome" className="desk-dock-launch desk-dock-app p13-appicon p13-appicon-project"
          aria-label={`${p.title ?? p.name}, ${S.live.projects[p.id]} need you`} onClick={() => openProjectRoom(p.id)}>
          <img src="/desk/sprites/drawer.png" alt="" width={32} height={32} className="desk-dock-sprite" draggable={false} />
          <span className="desk-dock-label">{p.title ?? p.name}</span>
          <span className="desk-chip desk-dock-badge" data-tone="warn" data-p13-standin="C3">{S.live.projects[p.id]}</span>
        </Button>
      ))}
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

/* (A1-F) Parked and Restore. Park replaces Delete; the receipt says PARKED. */
G.__p13UseTick = () => useP13();
G.__p13ParkedOn = (kind: ParkKind) => S.parkedOn[kind];
G.__p13Unparked = <T extends { id?: unknown }>(kind: ParkKind, rows: T[], ignoreFilter = false): T[] => {
  if (S.parkedOn[kind] && !ignoreFilter) return [];
  const gone = new Set(S.parked[kind].map((p) => p.id));
  return rows.filter((r) => !gone.has(String(r.id)));
};
function park(kind: ParkKind, id: string, title: string, detail?: string) {
  const p = { id, title, at: clock(), detail };
  S.parked[kind] = [p, ...S.parked[kind].filter((x) => x.id !== id)];
  S.receipt[kind] = p;
  bump();
}
function restore(kind: ParkKind, id: string) {
  S.parked[kind] = S.parked[kind].filter((x) => x.id !== id);
  if (S.receipt[kind]?.id === id) S.receipt[kind] = null;
  if (!S.parked[kind].length) S.parkedOn[kind] = false;
  bump();
}
G.__p13ParkVerb = (kind: ParkKind, row: any, after: () => void) => (
  <Button dense variant="ghost" data-testid="p13-park" onClick={() => { park(kind, String(row.id), String(row.title ?? row.name ?? "Untitled")); after(); }}>
    Park
  </Button>
);
G.__p13Park = (kind: ParkKind, item: { id: string; title: string }) => { park(kind, item.id, item.title); return true; };
function ParkReceipt({ kind }: { kind: ParkKind }) {
  useP13();
  const r = S.receipt[kind];
  if (!r) return null;
  return (
    <span className="p13-park-receipt" data-testid={`p13-park-receipt-${kind}`}>
      <span className="surface-footer-receipt-line" role="status">{`PARKED ${r.at}`}</span>
      <Button dense variant="ghost" onClick={() => restore(kind, r.id)}>Restore</Button>
    </span>
  );
}
G.__p13Receipt = (kind: ParkKind) => (S.receipt[kind] ? <ParkReceipt kind={kind} /> : null);
G.__p13FootVerbs = (kind: ParkKind) => (S.receipt[kind] ? <ParkReceipt kind={kind} /> : undefined);
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
              trailing={<Button dense variant="ghost" onClick={() => restore(kind, p.id)}>Restore</Button>}
              expands={false} data-testid="p13-parked-row" />
          ))}
        </SurfaceLedger>
      ) : null}
    </div>
  );
}
G.__p13ParkedStrip = (kind: ParkKind) => <ParkedStrip kind={kind} />;


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
      <section className="desk-window desk-window-shell p13-chairwin is-front p13-sheet" data-testid="p13-sheet" role="region" aria-label="Material">
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

/* ── the rig's hands (the canvas's own state; never a product write) ── */
G.__p13 = {
  live(v: Partial<typeof S.live>) { Object.assign(S.live, v); bump(); },
  chairFront(key: string) { S.chairOrder = [...S.chairOrder.filter((k) => k !== key), key]; S.deskFront = false; bump(); },
  chairZoom(key: string, on: boolean) { S.chairZoom[key] = on; bump(); },
  phoneOpen(key: string) { S.phoneOpen = key; bump(); },
  deskFront() { S.deskFront = true; bump(); },
  parkedOn(kind: ParkKind, on: boolean) { S.parkedOn[kind] = on; bump(); },
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
