// Dock — the application launcher + running window toolbar.
// Extracted from DeskWindow.tsx (HS-117-04).
import { cloneElement, isValidElement, useCallback, useEffect, useRef, useState, useSyncExternalStore, type MouseEvent as ReactMouseEvent, type ReactElement, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import { openIntelligence } from "../../intelligenceNavigation";
import { refreshNeedsYou, useNeedsYou } from "../../needsYou";
import { useNextOneOnOneRead } from "../../screen/nextOneOnOne";
import { micPhase, subscribeMicPhase } from "../../../lib/micSession";
import { useOptionalRuntimeBus } from "../../../runtime/RuntimeBus";
import { DOCK_SPRITES, DOCK_SPRITES_48 } from "../../systemSprites";
import { seatSprite } from "../../sprites";
import { useDesk } from "../../store";
import { useSettleState } from "../../settleState";
import { useShortcutSheet } from "../../chromeState";
import { useKeymap } from "../../keymap";
import { WorkMenu } from "../DeskMenu";
import { dockChipMenuEntries } from "../../windowMenuAdapter";
import { useOpenWindows, useShownName, useFrontWindowId, chipEls } from "./windowRegistry";
import { windowIcons } from "./seatIcons";
import { VerbGlyph } from "./VerbGlyph";
import { TickNumber } from "../../surface/kit";
import { RecordClock } from "../RecordClock";
import { ShortcutSheet } from "./ShortcutSheet";
import { DOCK_APPLICATIONS, PHONE_DOCK_APPLICATIONS } from "../../applications";
import { useAgentsTile } from "../../conductor/fleetTile";
import { useProgramsLamp, worseLamp } from "../../programs/lamp";
import { handTargetProps } from "../../hand/drag";
import { useDropHand } from "../../hand/store";
import { useCompactViewport } from "../../useCompactViewport";
import { closeChairWindow, openChairWindow, useChairWindows } from "../../chair/chairWindows";
import {
  EMPTY_DOCK_LIVE,
  deskChanges,
  formatDockTime,
  onlyWindowChanges,
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

/** HS-100-11 — the dock IS the launcher. Betterment shell S3 gives it one
 * primary door per daily application; the desktop and phone projections come
 * from the manifest. Settings is in the HoldSpeak menu. Go lists them all. */
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
/** The floating dock (2026-10-26): a seated window's mark is the hollow dot
 * under its tile, where a running app has its filled dot. */
const seatLamp = <span className="desk-dock-seat" aria-hidden="true" />;

/** The 48 px picture of a dock tile: the D drawing at 48 when there is one,
 * else the 32 px drawing drawn up, smooth (dock.css). */
function dockSpriteFor(windowId: string): string | undefined {
  return DOCK_SPRITES_48[windowId] ?? DOCK_SPRITES[windowId];
}

/** A seated window's title-bar icon at the tile's 48 px. */
function seatFace(icon: ReactNode): ReactNode {
  if (isValidElement<{ src?: unknown }>(icon) && icon.type === "img" && typeof icon.props.src === "string") {
    return cloneElement(icon as ReactElement<Record<string, unknown>>, {
      src: seatSprite(icon.props.src),
      width: 48,
      height: 48,
    });
  }
  return icon;
}

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
        <span className="desk-dock-seat-icon" aria-hidden="true">{seatFace(icon)}</span>
      ) : (
        <span aria-hidden="true">{w.glyph}</span>
      )}
      {/* The name shows on hover and focus, above the tile (dock.css). */}
      <span className="desk-dock-label" aria-hidden="true">{name}</span>
      {seatLamp}
    </Button>
  );
}
const DOCK_FACE_APPLICATIONS = DOCK_APPLICATIONS;
const PHONE_FACE_APPLICATIONS = PHONE_DOCK_APPLICATIONS;

/** The next 1:1 is near: it starts within 30 minutes (the People tag's
 *  lamp). Re-read each minute while there is a start to watch. */
const ONE_ON_ONE_NEAR_MS = 30 * 60_000;
function useNearStart(at: string | null): boolean {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!at) return;
    setNow(Date.now());
    const timer = window.setInterval(() => setNow(Date.now()), 60_000);
    return () => window.clearInterval(timer);
  }, [at]);
  if (!at) return false;
  const until = new Date(at).getTime() - now;
  return Number.isFinite(until) && until >= 0 && until <= ONE_ON_ONE_NEAR_MS;
}


function useDockMicPhase(): ReturnType<typeof micPhase> {
  return useSyncExternalStore(subscribeMicPhase, micPhase, micPhase);
}

function micIsLive(phase: ReturnType<typeof micPhase>): boolean {
  return phase === "open" || phase === "segmenting" || phase === "held";
}

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
    // A live invalidation refreshes A2 through its shared read. This is the
    // event path; the Dock does not start the hook's minute poll. It never
    // forces a rebuild: a hub write that changes the answer marks the hub's
    // cache dirty, so the plain read is current (PERF-DOCK 2026-10-28).
    await refreshNeedsYou(false).catch(() => undefined);
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
        // A window open, close or move changes nothing the Dock reads.
        if (frame.type === "desk_changed" && onlyWindowChanges(frame.data)) return;
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
  const windowsById = useDesk((s) => s.windowsById);
  const recordingState = useDesk((s) => s.recording);
  const recordingStartedAt = useDesk((s) => s.recordingStartedAt);
  const windows = useOpenWindows();
  const front = useFrontWindowId();
  const compact = useCompactViewport();
  // W7: the phone's Record tile (Capture), for the clock above it.
  const captureTile = useRef<HTMLElement | null>(null);
  const captureRef = useCallback((winId: string) => (el: HTMLElement | null) => {
    seatRef(winId)(el);
    captureTile.current = el;
  }, []);
  // HS-111-07 — the HS-101 B8 keyboard grammar (Cmd+1-Cmd+4, Cmd+W, Cmd+M, Ctrl+`,
  // Cmd+/) moved into desk/keymap.ts, driven by the registry's key
  // fields: ONE binder (refcounted -- the chrome mounts it too). The
  // sheet's open state is shared chrome state so the system.sheet
  // verb can draw it.
  useKeymap();
  const sheetOpen = useShortcutSheet((s) => s.open);
  const chair = useChairWindows();
  const mic = useDockMicPhase();
  const people = useNextOneOnOneRead(true);
  const peopleNear = useNearStart(people.at);
  // PHILO-13-03 / C3: every Desk face reads the same membership snapshot.
  // The Dock opts out of the hook's minute poll; RuntimeBus invalidations
  // call the explicit refresh path in useDockLiveReads.
  const { live, reads, offline, lastSuccessfulAt, needsYouCount } = useDockLiveReads();
  // Betterment AG8: the Agents tile carries the fleet's worst state, a mark
  // for New and the count that needs him (nothing with no live agent).
  const fleetTile = useAgentsTile();
  // Programs (2026-10-28): the worst Program state joins the Agents lamp.
  const programsLamp = useProgramsLamp();
  const agentsTile = {
    ...fleetTile,
    lamp: worseLamp(fleetTile.lamp, programsLamp.lamp),
    words: [fleetTile.words, programsLamp.words].filter(Boolean).join(", "),
  };
  const handOver = useDropHand((state) => state.drag?.over);
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

  // HS-202-02 — publish the dock's own reserve as `--desk-dock-h`. At
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
      // The floating dock (2026-10-26): the plate floats `bottom` above the
      // edge, so the reserve is its height, that inset and the same air
      // above it (1440: 64 + 10 + 10 = 84 px).
      const inset = parseFloat(getComputedStyle(el).bottom) || 0;
      const next = `${Math.ceil(el.offsetHeight + 2 * inset)}px`;
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
      const phone = compact;
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
  }, [compact]);
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
  const tiledIds = new Set<string>([
    ...DOCK_FACE_APPLICATIONS.map((application) => `pullout:${application.windowId}`),
  ]);
  const seatedWithoutTile = NUB_CHIPS
    ? []
    : visibleWindowChips.filter((w) => panelMin.includes(w.id) && !tiledIds.has(w.id));
  // The floating dock (owner pick 2026-10-26, canvas D1): a tile is the 48 px
  // D picture and nothing under it. The name, and a live fact (REC 10:42,
  // 1:1 15:00), show on hover and focus as a label above the tile; the
  // tile's aria-label says the same. A count rides the icon's top-right
  // corner; a running app has a dot under its tile (dock.css).
  const face = (application: (typeof DOCK_FACE_APPLICATIONS)[number], minimized: boolean) => {
    const sprite = dockSpriteFor(application.windowId);
    const id = application.windowId;
    return (
      <>
        {sprite ? (
          <img src={sprite} alt="" width={48} height={48} className="desk-dock-sprite" draggable={false} />
        ) : (
          <span aria-hidden="true">{application.glyph}</span>
        )}
        <span className="desk-dock-label" aria-hidden="true">
          {application.label}
          {id === "surface-meetings" && recordingLabel ? (
            <span className="desk-dock-state" data-testid="desk-dock-meetings-state" data-tone="rec">
              {recordingLabel}
            </span>
          ) : null}
          {id === "surface-people" && people.label ? (
            <span className="desk-dock-state" data-testid="desk-dock-people-state" data-tone="ok" data-soon={peopleNear ? "" : undefined}>
              {people.label}
            </span>
          ) : null}
        </span>
        {minimized ? seatLamp : null}
        {id === "intelligence:desk" && needsYouCount > 0 ? (
          <span className="desk-dock-badge" data-tone="ask" data-testid="desk-dock-today-count" aria-hidden="true">
            <TickNumber value={needsYouCount} />
          </span>
        ) : null}
        {id === "conductor" && agentsTile.lamp ? (
          <span className="desk-dock-fleet" data-tone={agentsTile.lamp} data-testid="desk-dock-agents-lamp" aria-hidden="true" />
        ) : null}
        {id === "conductor" && agentsTile.needYou ? (
          <span className="desk-dock-badge" data-tone="ask" data-testid="desk-dock-agents-count" aria-hidden="true">
            <TickNumber value={agentsTile.needYou} />
          </span>
        ) : null}
        {!compact && id === "surface-dictation" && micIsLive(mic) ? (
          <span className="desk-dock-mic-lamp" data-testid="desk-dock-speak-lamp" aria-label="Mic open" />
        ) : null}
      </>
    );
  };
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
        const isChair = application.dock.launch === "chair";
        const winId = isChair
          ? application.windowId
          : windows.some((w) => w.id === pulloutId) ? pulloutId : application.windowId;
        const win = windows.find((w) => w.id === winId);
        // Mounted DOM refs are runtime detail; the compositor owns whether a
        // hosted application is open. Intelligence is not yet a hosted surface.
        const running = isChair
          ? !chair.closed[application.windowId]
          : application.surface
          ? Boolean(windowsById[application.windowId])
          : Boolean(win);
        const minimized = running && panelMin.includes(winId);
        return (
          <Button
            key={application.windowId}
            ref={seatRef(winId)}
            variant="chrome"
            data-app={application.windowId}
            data-drop={application.windowId === "conductor" && handOver === "drawer:conductor" ? true : undefined}
            {...(application.windowId === "conductor" ? handTargetProps("drawer:conductor") : {})}
            className={
              "desk-dock-launch desk-dock-app" +
              (running && !minimized ? " is-run" : "") +
              (minimized ? " is-seated" : "") +
              (running && winId === front && !minimized ? " is-front" : "") +
              ""
            }
            aria-label={`${application.label}${application.windowId === "conductor" && agentsTile.words ? `, ${agentsTile.words}` : ""}${application.windowId === "intelligence:desk" && needsYouCount > 0 ? `, ${needsYouCount} needs you` : ""}${application.windowId === "surface-people" && people.label ? `, ${people.label}` : ""}${application.windowId === "surface-meetings" && recordingLabel ? `, ${recordingLabel}` : ""}${application.windowId === "surface-dictation" && micIsLive(mic) ? ", mic open" : ""}${minimized ? ", iconified" : ""}`}
            onClick={() => {
              const s = useDesk.getState();
              if (isChair) openChairWindow(application.windowId);
              else if (running && minimized) s.restorePanel(winId);
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
                close: win?.close ?? (() => isChair
                  ? closeChairWindow(application.windowId)
                  : useDesk.getState().closeSurfaceWindow(application.action)),
              });
            }}
          >
            {face(application, minimized)}
          </Button>
        );
        })}
      {compact ? (
        <>
          {PHONE_FACE_APPLICATIONS.map((application) => {
            const isChair = application.dock.launch === "chair";
            const pulloutId = `pullout:${application.windowId}`;
            const winId = isChair
              ? application.windowId
              : application.windowId === "intelligence:desk" ? pulloutId : application.windowId;
            const running = isChair
              ? !chair.closed[application.windowId]
              : application.surface
                ? Boolean(windowsById[application.windowId])
                : Boolean(windows.some((w) => w.id === winId));
            const minimized = running && panelMin.includes(winId);
            // W7 (canvas 2026-10-28 (b)): on the phone the Capture tile is
            // the Record tile; while a meeting records it wears the red ring
            // (record-orb.css) and the clock above it.
            const recordTile = application.windowId === "chair:capture";
            return (
              <Button
                key={application.windowId}
                ref={recordTile ? captureRef(winId) : seatRef(winId)}
                data-recording={recordTile && recording ? "" : undefined}
                variant="chrome"
                data-app={application.windowId}
                data-drop={application.windowId === "conductor" && handOver === "drawer:conductor" ? true : undefined}
                {...(application.windowId === "conductor" ? handTargetProps("drawer:conductor") : {})}
                className={`desk-dock-launch desk-dock-app${running && !minimized ? " is-run" : ""}${minimized ? " is-seated" : ""}${running && winId === front && !minimized ? " is-front" : ""}`}
                aria-label={`${application.label}${application.windowId === "intelligence:desk" && needsYouCount > 0 ? `, ${needsYouCount} needs you` : ""}${application.windowId === "surface-people" && people.label ? `, ${people.label}` : ""}${application.windowId === "conductor" && agentsTile.words ? `, ${agentsTile.words}` : ""}${application.windowId === "surface-meetings" && recordingLabel ? `, ${recordingLabel}` : ""}${minimized ? ", iconified" : ""}`}
                onClick={() => {
                  if (isChair) openChairWindow(application.windowId);
                  else if (running && minimized) useDesk.getState().restorePanel(winId);
                  else if (running) useDesk.getState().focusPanel(winId);
                  else if (application.dock.launch === "intelligence") openIntelligence({ view: "today" });
                  else void import("../../shell").then((m) =>
                    m.openSurfaceOr(application.action, application.href, undefined, { origin: "dock" }),
                  );
                }}
              >
                {face(application, minimized)}
              </Button>
            );
          })}
        </>
      ) : null}
      {compact && recording ? (
        <RecordClock
          target={captureTile}
          startedAt={recording.startedAt ? Date.parse(recording.startedAt) : null}
        />
      ) : null}
      {/* The Record tile ends the applications (canvas D1). PHILO-17 (owner
          2026-10-10, "everything must become one desk"): the Chair/Floor
          toggle is gone; the Screen is the one desk. */}
      {!compact ? center : null}
      {/* PHILO-16 (A1) §5: a seated window always has a seat. One whose
          application has no tile here gets its own, after a thin rule. */}
      {seatedWithoutTile.length > 0 ? (
        <span className="desk-dock-sep desk-dock-seat-sep" aria-hidden="true" />
      ) : null}
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
