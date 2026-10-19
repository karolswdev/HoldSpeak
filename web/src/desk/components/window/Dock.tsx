// Dock — the application launcher + running window toolbar.
// Extracted from DeskWindow.tsx (HS-117-04).
import { useCallback, useEffect, useRef, useState, type MouseEvent as ReactMouseEvent, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import { openIntelligence } from "../../intelligenceNavigation";
import { refreshNeedsYou, useNeedsYou } from "../../needsYou";
import { useOptionalRuntimeBus } from "../../../runtime/RuntimeBus";
import { DOCK_SPRITES } from "../../systemSprites";
import { useDesk } from "../../store";
import { useSettleState } from "../../settleState";
import { useShortcutSheet } from "../../chromeState";
import { useKeymap } from "../../keymap";
import { WorkMenu } from "../DeskMenu";
import { dockChipMenuEntries } from "../../windowMenuAdapter";
import { useOpenWindows, useShownName, chipEls } from "./windowRegistry";
import { windowIcons } from "./seatIcons";
import { toggleExpose } from "./Expose";
import { VerbGlyph } from "./VerbGlyph";
import { ShortcutSheet } from "./ShortcutSheet";
import { DOCK_APPLICATIONS, applicationForAction } from "../../applications";
import { useAutomationNews } from "../../automationNews";
import { useAgentsTile } from "../../conductor/fleetTile";
import { useCompactViewport } from "../../useCompactViewport";
import { openChairWindow, useChairWindows } from "../../chair/chairWindows";
import {
  EMPTY_DOCK_LIVE,
  deskChanges,
  formatDockTime,
  reduceDockFrame,
  type DockLiveState,
} from "./dockState";
import { burstTimer } from "../../burstTimer";
import { DOCK_HEIGHT_EVENT } from "./windowGeometry";

const DOCK_LIVE_FRAMES = [
  "aftercare_ready",
  "desk_changed",
  "intel_complete",
  "meeting_started",
  "scheduled_recording.refused",
  "scheduled_recording.started",
  "scheduled_recording.stopped",
  "stopped",
] as const;

/* Betterment send S1: the Dock no longer reads every send on each refresh
 * (nothing drew it; its SENT badge was cut). The send frame reducer and
 * `latestSendSettle` stay parked in dockState.ts. */
interface DockReadState {
  readyMeetingIds: string[];
  readyReadAt: number | null;
}

const EMPTY_DOCK_READ: DockReadState = {
  readyMeetingIds: [],
  readyReadAt: null,
};

function wireRows<T>(body: unknown, key: string): T[] {
  if (Array.isArray(body)) return body as T[];
  if (!body || typeof body !== "object") return [];
  const rows = (body as Record<string, unknown>)[key];
  return Array.isArray(rows) ? rows as T[] : [];
}

async function readUnreadReadyMeetings(): Promise<string[]> {
  const body = await apiFetch<unknown>("/api/meetings/ready");
  return wireRows<{ id?: string }>(body, "meetings")
    .map((row) => typeof row.id === "string" ? row.id : "")
    .filter(Boolean);
}

/** HS-100-11 — the dock IS the launcher. PHILO-17 (doors): one primary
 * door per application. Speak, Meetings and Intelligence ride the Dock;
 * People, the Conductor and the projects are drawers on the desk; Settings
 * is in the HoldSpeak menu. Go lists them all. */
const DOCK_APP_IDS = new Set<string>(
  DOCK_APPLICATIONS.map((application) => application.windowId),
);
/** PHILO-16 (A1): parked, seats live in the dock (§5). The window chips
 * after the separator (one per open window that is not an application) are
 * not drawn; a seated window shows on its tile as the seat lamp instead.
 * The code below stays behind this flag. */
const NUB_CHIPS = false;
/** PHILO-16 (A1) §5: a tile is the seat of its window: the minimize and
 * restore motion flies to it (DeskWindow.tsx reads chipEls). */
const seatRef = (windowId: string) => (el: HTMLElement | null) => {
  if (NUB_CHIPS) return;
  if (el) chipEls.set(windowId, el);
  else chipEls.delete(windowId);
};
const seatLamp = <span className="desk-dock-seat" aria-hidden="true" />;

/** PHILO-16 (A1) §5: a seated window whose application has no Dock tile
 * gets its own seat tile: its icon (the title bar's), its shown name, the
 * seat lamp. A press restores it to the front, like every tile. The tile
 * goes when the window closes or comes back. */
function SeatTile({
  window: w,
  onMenu,
}: {
  window: { id: string; label: string; glyph: string; close: () => void };
  onMenu: (e: ReactMouseEvent, name: string) => void;
}) {
  const name = useShownName(w.id, w.label);
  const icon = windowIcons.get(w.id);
  return (
    <Button
      ref={seatRef(w.id)}
      variant="chrome"
      data-seat={w.id}
      className="desk-dock-launch desk-dock-seat-tile is-seated"
      aria-label={`${name}, iconified`}
      onClick={() => useDesk.getState().restorePanel(w.id)}
      onContextMenu={(e) => onMenu(e, name)}
    >
      {icon != null ? (
        <span className="desk-dock-seat-icon" aria-hidden="true">{icon}</span>
      ) : (
        <span aria-hidden="true">{w.glyph}</span>
      )}
      <span className="desk-dock-label">{name}</span>
      {seatLamp}
    </Button>
  );
}
const DOCK_FACE_APPLICATIONS = DOCK_APPLICATIONS;

/** Read the two Dock-only projections after a live invalidation.  The
 * membership read itself is owned by useNeedsYou; this function only reads
 * the existing Send and People boundaries needed for their AppIcon marks. */
function useDockLiveReads(): {
  live: DockLiveState;
  reads: DockReadState;
  offline: boolean;
  lastSuccessfulAt: number | null;
  needsYouCount: number;
  needsYouItems: ReturnType<typeof useNeedsYou>["unmutedItems"];
} {
  const runtime = useOptionalRuntimeBus();
  const runtimeState = runtime?.state ?? "offline";
  const subscribe = runtime?.subscribe;
  const needs = useNeedsYou({ poll: false });
  const [live, setLive] = useState<DockLiveState>(EMPTY_DOCK_LIVE);
  const [reads, setReads] = useState<DockReadState>(EMPTY_DOCK_READ);
  const lastState = useRef<string | null>(runtimeState);
  const readyReadGeneration = useRef(0);

  const refresh = useCallback(async () => {
    if (runtimeState !== "connected") return;
    const requestedReadyGeneration = readyReadGeneration.current;
    const [ready] = await Promise.allSettled([readUnreadReadyMeetings()]);
    // A live invalidation always refreshes A2 through its shared read. This
    // explicit refresh is the event path; the Dock does not start the hook's
    // minute poll.
    await refreshNeedsYou(true).catch(() => undefined);
    const readAt = Date.now();
    setReads((previous) => ({
      ...previous,
      ...(ready.status === "fulfilled" &&
        requestedReadyGeneration === readyReadGeneration.current ? {
        readyMeetingIds: ready.value,
        readyReadAt: readAt,
      } : {}),
    }));
    if (ready.status === "fulfilled" &&
      requestedReadyGeneration === readyReadGeneration.current) {
      // The durable snapshot is authoritative. Reconcile live frame IDs so a
      // replayed frame cannot resurrect an acknowledged row.
      setLive((previous) => ({ ...previous, readyMeetingIds: ready.value }));
    }
  }, [runtimeState]);

  useEffect(() => {
    if (!subscribe) {
      void refresh();
      return;
    }
    const burst = burstTimer(() => { void refresh(); }, 250);
    const unsubscribers = DOCK_LIVE_FRAMES.map((type) =>
      subscribe(type, (frame) => {
        setLive((previous) => reduceDockFrame(previous, frame));
        if (frame.type === "desk_changed") {
          for (const value of deskChanges(frame.data)) {
            if (value.kind !== "meeting_ready_read") continue;
            const readId = typeof value.id === "string"
              ? value.id
              : typeof value.meeting_id === "string" ? value.meeting_id : "";
            if (readId) {
              readyReadGeneration.current += 1;
              setReads((previous) => ({
                ...previous,
                readyMeetingIds: previous.readyMeetingIds.filter((id) => id !== readId),
              }));
            }
          }
        }
        burst.bump();
      }),
    );
    return () => {
      unsubscribers.forEach((unsubscribe) => unsubscribe());
      burst.cancel();
    };
  }, [refresh, subscribe]);

  useEffect(() => {
    const state = runtimeState;
    const reconnected = state === "connected" && lastState.current !== "connected";
    lastState.current = state;
    const hasSnapshot = reads.readyReadAt !== null;
    if (state === "connected" && (reconnected || !hasSnapshot)) {
      void refresh();
    }
  }, [reads.readyReadAt, refresh, runtimeState]);

  const lastSuccessfulAt = reads.readyReadAt ?? null;

  return {
    live,
    reads,
    offline: Boolean(lastSuccessfulAt !== null && runtimeState !== "connected"),
    lastSuccessfulAt,
    needsYouCount: needs.count,
    // Betterment D1: the badge counts the rows the hub's one rule counts.
    needsYouItems: needs.unmutedItems.filter((item) => !item.waiting && !item.foldedInto && item.counted !== false),
  };
}

/** The dock (HS-95-03): every open window as a chip -- tap focuses (or
 * restores a parked one), x closes, loop resets the layout. Ctrl+` cycles
 * focus in MRU order, restoring as it lands. Shell furniture: it rides
 * above the window band, and it is invisible while nothing is open. */
export function Dock({ center }: { center?: ReactNode } = {}) {
  const panelMin = useDesk((s) => s.panelMin);
  const panelOrder = useDesk((s) => s.panelOrder);
  const windowsById = useDesk((s) => s.windowsById);
  const recordingState = useDesk((s) => s.recording);
  const recordingStartedAt = useDesk((s) => s.recordingStartedAt);
  const windows = useOpenWindows();
  const compact = useCompactViewport();
  // HS-111-07 — the HS-101 B8 keyboard grammar (Cmd+1-Cmd+4, Cmd+W, Cmd+M, Ctrl+`,
  // Cmd+/) moved into desk/keymap.ts, driven by the registry's key
  // fields: ONE binder (refcounted -- the chrome mounts it too). The
  // sheet's open state is shared chrome state so the system.sheet
  // verb can draw it.
  useKeymap();
  const sheetOpen = useShortcutSheet((s) => s.open);
  const chair = useChairWindows();
  // PHILO-13-03 / C3: every Desk face reads the same membership snapshot.
  // The Dock opts out of the hook's minute poll; RuntimeBus invalidations
  // call the explicit refresh path in useDockLiveReads.
  const { live, reads, offline, lastSuccessfulAt } = useDockLiveReads();
  // Betterment A6: the Automations tile stands on the Dock while a result is
  // NEW, with the NEW count (absent at zero: no tile, no "0").
  const news = useAutomationNews();
  // Betterment AG8: the Agents tile carries the fleet's worst state, a mark
  // for New and the count that needs him (nothing with no live agent).
  const agentsTile = useAgentsTile();
  // PHILO-17 (needsyou, walker TAXES): the one number is on the Needs-you
  // icon and the bell only; the Intelligence tile carries no copy of it.
  // HS-99-04 — the dock chip menu (one menu vocabulary).
  const [chipMenu, setChipMenu] = useState<{
    id: string;
    label: string;
    x: number;
    y: number;
    minimized: boolean;
    close: () => void;
  } | null>(null);
  const settled = useSettleState((s) => s.settled);
  useEffect(() => {
    if (settled) setChipMenu(null);
  }, [settled]);
  useEffect(() => {
    if (!chipMenu) return;
    const close = () => setChipMenu(null);
    window.addEventListener("pointerdown", close);
    return () => window.removeEventListener("pointerdown", close);
  }, [chipMenu]);

  // HS-202-02 — publish the dock's own height as `--desk-dock-h`. At
  // phone width the dock wraps, so its height is not a constant any
  // stylesheet can guess; the sheets read this to stop above it instead
  // of burying the only persistent door the phone has.
  //
  // Publish ONCE per mount; the ResizeObserver follows every later size
  // change. With no dependency list this effect re-ran on every Dock
  // render (a tap in any window re-renders it through `focusPanel`), and
  // its cleanup removed the property just before `publish` read
  // `offsetHeight`. That forced a layout with the sheet taller than it is,
  // which clamped a window scrolled to its end up by the difference —
  // between pointerdown and click — so the tap landed on another element
  // and did nothing (NOT INCLUDED in a kept brief at 393).
  const dockRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const el = dockRef.current;
    const root = document.documentElement;
    if (!el) return;
    const publish = () => {
      const next = `${Math.ceil(el.offsetHeight)}px`;
      if (root.style.getPropertyValue("--desk-dock-h") === next) return;
      root.style.setProperty("--desk-dock-h", next);
      // The working band moved: open windows clamp above the Dock again.
      window.dispatchEvent(new Event(DOCK_HEIGHT_EVENT));
    };
    publish();
    if (typeof ResizeObserver !== "function") return;
    const observer = new ResizeObserver(publish);
    observer.observe(el);
    return () => {
      observer.disconnect();
      root.style.removeProperty("--desk-dock-h");
    };
  }, []);

  // 393 (C1-8, Astra on #869): the LAST page of the shelf starts on a whole
  // item too. The shelf's end is wherever its tail (Hide the menus, Places,
  // the orb, window chips) happens to end, so scrolled to its end the left
  // gutter showed a strip of the item before it. A spacer before More
  // (`--desk-dock-end-pad`, dock.css) moves the end so the gutter lands on
  // an item's left edge. Desktop: no spacer.
  useEffect(() => {
    const el = dockRef.current;
    if (!el) return;
    const GUTTER = 4;
    const align = () => {
      const phone = typeof window.matchMedia === "function" && window.matchMedia("(max-width: 720px)").matches;
      const current = parseFloat(el.style.getPropertyValue("--desk-dock-end-pad")) || 0;
      let pad = 0;
      if (phone) {
        const end = el.scrollWidth - current - el.clientWidth + GUTTER;
        if (end > GUTTER) {
          const origin = el.getBoundingClientRect().left - el.scrollLeft;
          const edges = [...el.children]
            .filter((k) => !k.classList.contains("desk-dock-more"))
            .map((k) => k.getBoundingClientRect().left - origin)
            .filter((x) => x >= end - 0.5)
            .sort((a, b) => a - b);
          if (edges.length) pad = Math.max(0, Math.round(edges[0] - end));
        }
      }
      const next = `${pad}px`;
      if (el.style.getPropertyValue("--desk-dock-end-pad") !== next) el.style.setProperty("--desk-dock-end-pad", next);
    };
    align();
    if (typeof ResizeObserver !== "function" || typeof MutationObserver !== "function") return;
    const sizes = new ResizeObserver(align);
    const watch = () => {
      sizes.disconnect();
      sizes.observe(el);
      for (const child of el.children) sizes.observe(child);
    };
    watch();
    const children = new MutationObserver(() => { watch(); align(); });
    children.observe(el, { childList: true });
    return () => {
      sizes.disconnect();
      children.disconnect();
    };
  }, []);

  // The front chip mirrors the shell's is-front rule: the last id in
  // the order that is open here and not minimized (HS-97-04).
  let front: string | undefined;
  for (let i = panelOrder.length - 1; i >= 0; i--) {
    const oid = panelOrder[i];
    if (panelMin.includes(oid)) continue;
    if (!windows.some((w) => w.id === oid)) continue;
    front = oid;
    break;
  }
  // A launcher whose surface is already a window folds into that chip;
  // it only renders as a launcher while its surface is closed.
  // PHILO-16 (A1): with the chips parked the launcher stays; it is the
  // window's seat.
  // A3 sets "recording" only after res.ok or the hub's meeting_live read.
  // That shared read also covers a Dock mounted after the start frame.
  // The optimistic press is "busy", so it cannot create REC here.
  const recording = !offline && (live.recording || (recordingState === "recording"
    ? { meetingId: "hub-confirmed", startedAt: recordingStartedAt
      ? new Date(recordingStartedAt).toISOString() : null }
    : null));
  const recordingLabel = recording
    ? `REC${recording.startedAt ? ` ${formatDockTime(recording.startedAt)}` : ""}`
    : null;
  // PHILO-17 (doors): projects left the Dock (they are desk drawers and
  // Go ▸ Projects); an open Room is a window like any other, so iconified it
  // has its own seat tile.
  const visibleWindowChips = windows.filter((window) => !DOCK_APP_IDS.has(window.id));
  // PHILO-16 (A1) §5: the seated windows no tile above seats (an application
  // opened as a pullout, a launcher, or a project already has its tile).
  const automations = !compact && !offline && news.count > 0 ? applicationForAction("open-workbenches") : undefined;
  const tiledIds = new Set<string>([
    ...DOCK_FACE_APPLICATIONS.map((application) => `pullout:${application.windowId}`),
    ...(automations ? [automations.windowId] : []),
  ]);
  const seatedWithoutTile = NUB_CHIPS
    ? []
    : visibleWindowChips.filter((w) => panelMin.includes(w.id) && !tiledIds.has(w.id));
  return (
    <div
      ref={dockRef}
      className="desk-dock"
      role="toolbar"
      aria-label="Dock"
      /* HS-110-04: magnification swell removed -- the shelf is flat. */
    >
      {offline ? (
        <span className="desk-dock-offline" data-testid="desk-dock-offline" role="status">
          OFFLINE · AS OF {formatDockTime(lastSuccessfulAt)}
        </span>
      ) : null}
        {!compact && DOCK_FACE_APPLICATIONS.map((application) => {
        // PHILO-16 (A1): an application that opens as a pullout (Intelligence)
        // has the window id `pullout:<windowId>`; its tile is that window's seat.
        const pulloutId = `pullout:${application.windowId}`;
        const winId = windows.some((w) => w.id === pulloutId) ? pulloutId : application.windowId;
        const win = windows.find((w) => w.id === winId);
        // Mounted DOM refs are runtime detail; the compositor owns whether a
        // hosted application is open. Intelligence is not yet a hosted surface.
        const running = application.surface
          ? Boolean(windowsById[application.windowId])
          : Boolean(win);
        const minimized = running && panelMin.includes(winId);
        return (
          <Button
            key={application.windowId}
            ref={seatRef(winId)}
            variant="chrome"
            data-app={application.windowId}
            className={
              "desk-dock-launch desk-dock-app" +
              (running && !minimized ? " is-run" : "") +
              (minimized ? " is-seated" : "") +
              (running && winId === front && !minimized ? " is-front" : "") +
              ""
            }
            aria-label={`${application.label}${application.windowId === "conductor" && agentsTile.words ? `, ${agentsTile.words}` : ""}${minimized ? ", iconified" : ""}`}
            onClick={() => {
              const s = useDesk.getState();
              if (running && minimized) s.restorePanel(winId);
              else if (running) s.focusPanel(winId);
              else if (application.dock.launch === "intelligence")
                openIntelligence({ view: "today" });
              else
                void import("../../shell").then((m) =>
                  m.openSurfaceOr(application.action, application.href, undefined, {
                    origin: "dock",
                  }),
                );
            }}
            onContextMenu={(e) => {
              if (!running) return;
              e.preventDefault();
              setChipMenu({
                id: winId,
                label: application.label,
                x: e.clientX,
                y: e.clientY,
                minimized,
                close: win?.close ?? (() => useDesk.getState().closeSurfaceWindow(application.action)),
              });
            }}
          >
            {/* The owner's 2026-10-16 density direction draws desktop art
                at 24 CSS px; the phone keeps 32 px. CSS owns that size;
                the intrinsic 32 px source stays unchanged. */}
            {DOCK_SPRITES[application.windowId] ? (
              <img src={DOCK_SPRITES[application.windowId]} alt="" width={32} height={32} className="desk-dock-sprite" draggable={false} />
            ) : (
              <span aria-hidden="true">{application.glyph}</span>
            )}
            <span className="desk-dock-label">{application.label}</span>
            {minimized ? seatLamp : null}
            {application.windowId === "conductor" && agentsTile.lamp ? (
              <span className="desk-dock-fleet" data-tone={agentsTile.lamp} data-testid="desk-dock-agents-lamp" aria-hidden="true" />
            ) : null}
            {application.windowId === "conductor" && agentsTile.needYou ? (
              <span className="desk-dock-badge" data-tone="ask" data-testid="desk-dock-agents-count" aria-hidden="true">
                {agentsTile.needYou}
              </span>
            ) : null}
            {application.windowId === "surface-meetings" && recordingLabel ? (
              <span
                className="desk-dock-state"
                data-testid="desk-dock-meetings-state"
                data-tone="rec"
              >
                {recordingLabel}
              </span>
            ) : null}
          </Button>
        );
        })}
      {automations ? (() => {
        const winId = automations.windowId;
        const running = Boolean(windowsById[winId]);
        const minimized = running && panelMin.includes(winId);
        const words = `${news.count} new ${news.count === 1 ? "result" : "results"}`;
        return (
          <Button
            key={winId}
            ref={seatRef(winId)}
            variant="chrome"
            data-app={winId}
            data-testid="desk-dock-automations"
            className={
              "desk-dock-launch desk-dock-app" +
              (running && !minimized ? " is-run" : "") +
              (minimized ? " is-seated" : "") +
              (running && winId === front && !minimized ? " is-front" : "")
            }
            aria-label={`${automations.label}, ${words}${minimized ? ", iconified" : ""}`}
            onClick={() => {
              const s = useDesk.getState();
              if (running && minimized) s.restorePanel(winId);
              else if (running) s.focusPanel(winId);
              else
                void import("../../shell").then((m) =>
                  m.openSurfaceOr(automations.action, automations.href, undefined, { origin: "dock" }),
                );
            }}
          >
            <span aria-hidden="true">{automations.glyph}</span>
            <span className="desk-dock-label">{automations.label}</span>
            {minimized ? seatLamp : null}
            <span className="desk-dock-badge" data-tone="new" data-testid="desk-dock-automations-new" aria-hidden="true">
              {news.count}
            </span>
          </Button>
        );
      })() : null}
      {compact ? (
        <>
          {/* The phone has four doors: Today, Capture, Meetings and People. */}
          {[
            { id: "intelligence:desk", label: "Today", glyph: "◈", click: () => openIntelligence({ view: "today" }), running: windows.some((w) => w.id === "pullout:intelligence:desk"), minimized: panelMin.includes("pullout:intelligence:desk") },
            { id: "chair:capture", label: "Capture", glyph: "●", click: () => openChairWindow("chair:capture"), running: !chair.closed["chair:capture"], minimized: panelMin.includes("chair:capture") },
            { id: "surface-meetings", label: "Meetings", glyph: "▣", click: () => void import("../../shell").then((m) => m.openSurfaceOr("review-meetings", "/history", undefined, { origin: "dock" })), running: Boolean(windowsById["surface-meetings"]), minimized: panelMin.includes("surface-meetings") },
            { id: "surface-people", label: "People", glyph: "♧", click: () => void import("../../shell").then((m) => m.openSurfaceOr("open-people", "/", undefined, { origin: "dock" })), running: Boolean(windowsById["surface-people"]), minimized: panelMin.includes("surface-people") },
          ].map((tile) => {
            const winId = tile.id === "intelligence:desk" ? "pullout:intelligence:desk" : tile.id;
            return (
            <Button
              key={tile.id}
              ref={seatRef(winId)}
              variant="chrome"
              data-app={tile.id}
              className={`desk-dock-launch desk-dock-app${tile.running && !tile.minimized ? " is-run" : ""}${tile.minimized ? " is-seated" : ""}`}
              aria-label={`${tile.label}${tile.minimized ? ", iconified" : ""}`}
              onClick={() => {
                if (tile.id === "chair:capture") tile.click();
                else if (tile.running && tile.minimized) useDesk.getState().restorePanel(winId);
                else if (tile.running) useDesk.getState().focusPanel(winId);
                else tile.click();
              }}
            >
              <span aria-hidden="true">{tile.glyph}</span>
              <span className="desk-dock-label">{tile.label}</span>
              {tile.minimized ? seatLamp : null}
            </Button>
            );
          })}
        </>
      ) : null}
      {/* PHILO-16 (A1) §5: a seated window always has a seat. One whose
          application has no tile here gets its own. */}
      {seatedWithoutTile.map((w) => (
        <SeatTile
          key={`seat:${w.id}`}
          window={w}
          onMenu={(e, name) => {
            e.preventDefault();
            setChipMenu({ id: w.id, label: name, x: e.clientX, y: e.clientY, minimized: true, close: w.close });
          }}
        />
      ))}
      {/* PHILO-17 (owner 2026-10-10, "everything must become one desk"):
          the Chair/Floor toggle is gone; the Screen is the one desk. */}
      {center}
      {NUB_CHIPS && visibleWindowChips.length > 0 ? (
        <span className="desk-dock-sep" aria-hidden="true" />
      ) : null}
      {(NUB_CHIPS ? visibleWindowChips : []).map((c) => {
        const minimized = panelMin.includes(c.id);
        return (
          <span
            key={c.id}
            className={
              "desk-dock-chip" +
              (minimized ? " is-min" : "") +
              (c.id === front && !minimized ? " is-front" : "")
            }
          >
            <Button
              variant="chrome"
              className="desk-dock-main"
              ref={(el) => {
                if (el) chipEls.set(c.id, el);
                else chipEls.delete(c.id);
              }}
              aria-label={minimized ? `Restore ${c.label}` : `Focus ${c.label}`}
              onClick={() => {
                const s = useDesk.getState();
                if (minimized) s.restorePanel(c.id);
                else s.focusPanel(c.id);
              }}
              onContextMenu={(e) => {
                e.preventDefault();
                setChipMenu({
                  id: c.id,
                  label: c.label,
                  x: e.clientX,
                  y: e.clientY,
                  minimized,
                  close: c.close,
                });
              }}
            >
              <span aria-hidden="true">{c.glyph}</span>
              <span className="desk-dock-label">{c.label}</span>
            </Button>
            <Button
              variant="chrome"
              className="desk-dock-x"
              aria-label={`Close ${c.label}`}
              onClick={c.close}
            >
              <VerbGlyph kind="close" />
            </Button>
          </span>
        );
      })}
      {windows.length > 0 ? (
        <>
          <Button
            variant="chrome"
            className="desk-dock-reset"
            aria-label="Overview"
            title="Overview"
            onClick={() => toggleExpose(true)}
          >
            <VerbGlyph kind="overview" />
          </Button>
          <Button
            variant="chrome"
            className="desk-dock-reset"
            aria-label="Reset layout"
            title="Reset layout"
            onClick={() => useDesk.getState().resetLayout()}
          >
            <VerbGlyph kind="reset" />
          </Button>
        </>
      ) : null}
      {/* C1 (393): the shelf ends on a whole icon; this gadget moves one
          page. The stylesheet shows it at phone width only. */}
      {!compact ? <Button
        variant="chrome"
        className="desk-dock-more"
        aria-label="More AppIcons"
        data-testid="desk-dock-more"
        onClick={(e) => {
          const shelf = (e.currentTarget as HTMLElement).closest(".desk-dock") as HTMLElement | null;
          if (!shelf) return;
          const page = shelf.clientWidth - (e.currentTarget as HTMLElement).offsetWidth;
          const atEnd = shelf.scrollLeft + shelf.clientWidth >= shelf.scrollWidth - 1;
          shelf.scrollTo({ left: atEnd ? 0 : shelf.scrollLeft + page, behavior: "smooth" });
        }}
      >
        <span aria-hidden="true">▸</span>
      </Button> : null}
      {!settled && chipMenu ? (
        <WorkMenu
          className="desk-dock-menu"
          label={`${chipMenu.label} dock menu`}
          anchor="above"
          x={chipMenu.x}
          y={chipMenu.y}
          entries={dockChipMenuEntries({
            minimized: chipMenu.minimized,
            restore: () => useDesk.getState().restorePanel(chipMenu.id),
            minimize: () => useDesk.getState().minimizePanel(chipMenu.id),
            close: chipMenu.close,
          })}
          onClose={() => setChipMenu(null)}
        />
      ) : null}
      {sheetOpen ? (
        <ShortcutSheet
          onClose={() => useShortcutSheet.getState().setOpen(false)}
        />
      ) : null}
    </div>
  );
}
