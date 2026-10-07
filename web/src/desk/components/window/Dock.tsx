// Dock — the application launcher + running window toolbar.
// Extracted from DeskWindow.tsx (HS-117-04).
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import { openIntelligence } from "../../intelligenceNavigation";
import { projectOpenHere, refreshNeedsYou, useNeedsYou } from "../../needsYou";
import { useOptionalRuntimeBus } from "../../../runtime/RuntimeBus";
import { DOCK_SPRITES, SYSTEM } from "../../systemSprites";
import { spriteUrl } from "../../sprites";
import { useDesk } from "../../store";
import { useSettleState } from "../../settleState";
import { useChairState } from "../../chairState";
import { useShortcutSheet } from "../../chromeState";
import { useKeymap } from "../../keymap";
import { WorkMenu } from "../DeskMenu";
import { dockChipMenuEntries } from "../../windowMenuAdapter";
import { useOpenWindows, chipEls } from "./windowRegistry";
import { useLaunchers } from "./launcherRegistry";
import { toggleExpose } from "./Expose";
import { VerbGlyph } from "./VerbGlyph";
import { ShortcutSheet } from "./ShortcutSheet";
import { DOCK_APPLICATIONS, applicationForAction } from "../../applications";
import { drawerWindowId, openDrawer } from "../../drawer/store";
import { RoomActions } from "./RoomActions";
import {
  dockStateLabel,
  EMPTY_DOCK_LIVE,
  deskChanges,
  formatDockTime,
  latestSendSettle,
  nextOneOnOneLabel,
  reduceDockFrame,
  type DockRelationshipRead,
  type DockSendOutcome,
  type DockSendRead,
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

interface DockReadState {
  sendOutcome: DockSendOutcome | null;
  sendSettledAt: string | null;
  nextOneOnOne: string | null;
  peopleReadiness: PeopleReadinessState | null;
  readyMeetingIds: string[];
  sendReadAt: number | null;
  peopleReadAt: number | null;
  readyReadAt: number | null;
}

const EMPTY_DOCK_READ: DockReadState = {
  sendOutcome: null,
  sendSettledAt: null,
  nextOneOnOne: null,
  peopleReadiness: null,
  readyMeetingIds: [],
  sendReadAt: null,
  peopleReadAt: null,
  readyReadAt: null,
};

function wireRows<T>(body: unknown, key: string): T[] {
  if (Array.isArray(body)) return body as T[];
  if (!body || typeof body !== "object") return [];
  const rows = (body as Record<string, unknown>)[key];
  return Array.isArray(rows) ? rows as T[] : [];
}

type PeopleReadinessState = "unconfigured" | "locked" | "key_unavailable" | "corrupt" | "unavailable" | "ready";
const PEOPLE_READINESS_STATES: readonly PeopleReadinessState[] = [
  "unconfigured",
  "locked",
  "key_unavailable",
  "corrupt",
  "unavailable",
  "ready",
];

interface PeopleProjectionRead {
  readiness: PeopleReadinessState | null;
  nextOneOnOne: string | null;
  complete: boolean;
}

function peopleReadinessOf(body: unknown): PeopleReadinessState | null {
  if (!body || typeof body !== "object") return null;
  const value = (body as Record<string, unknown>).state ??
    (body as Record<string, unknown>).readiness;
  return PEOPLE_READINESS_STATES.includes(value as PeopleReadinessState)
    ? value as PeopleReadinessState
    : null;
}

async function readPeopleProjection(): Promise<PeopleProjectionRead> {
  const readinessBody = await apiFetch<unknown>("/api/people/readiness");
  const readiness = peopleReadinessOf(readinessBody);
  if (readiness !== "ready") return { readiness, nextOneOnOne: null, complete: readiness !== null };

  const body = await apiFetch<unknown>("/api/people/relationships");
  const relationships = wireRows<DockRelationshipRead>(body, "relationships");
  const direct = relationships.filter((relationship) =>
    relationship.next_one_on_one !== undefined || relationship.nextOneOnOne !== undefined,
  );
  const ids = relationships
    .map((relationship) => relationship.id)
    .filter((id): id is string => Boolean(id));
  const details = await Promise.allSettled(
    ids.map((id) => apiFetch<unknown>(
      `/api/people/relationships/${encodeURIComponent(id)}/brief`,
    )),
  );
  const successfulDetails = details
    .filter((detail): detail is PromiseFulfilledResult<unknown> => detail.status === "fulfilled")
    .map((detail) => detail.value)
    .flatMap((value) => {
      const row = value && typeof value === "object"
        ? value as Record<string, unknown>
        : {};
      return [{
        brief: (row.brief && typeof row.brief === "object"
          ? row.brief
          : {}) as DockRelationshipRead,
      }];
    });
  const complete = relationships.length === 0 || direct.length === relationships.length ||
    (ids.length === relationships.length && successfulDetails.length === ids.length);
  return {
    readiness,
    nextOneOnOne: nextOneOnOneLabel([...relationships, ...successfulDetails]),
    complete,
  };
}

async function readUnreadReadyMeetings(): Promise<string[]> {
  const body = await apiFetch<unknown>("/api/meetings/ready");
  return wireRows<{ id?: string }>(body, "meetings")
    .map((row) => typeof row.id === "string" ? row.id : "")
    .filter(Boolean);
}

/** HS-100-11 — the dock IS the launcher: the four applications ride it
 * always (running mark when their window is open); drawers and tools
 * moved to the menu-bar bell and the search shelf. */
const DOCK_APP_IDS = new Set<string>(
  [...DOCK_APPLICATIONS.map((application) => application.windowId), "surface-people"],
);
const ACTIONABLE_LAUNCHERS = new Set(["attention", "delivery-board"]);
const PEOPLE_APPLICATION = applicationForAction("open-people");
const DOCK_FACE_APPLICATIONS = [
  ...DOCK_APPLICATIONS,
  ...(PEOPLE_APPLICATION
    ? [{ ...PEOPLE_APPLICATION, dock: { order: 2.5, launch: "surface" as const } }]
    : []),
].sort((left, right) => left.dock.order - right.dock.order);

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
  /** PHILO-14 A1: each Project's Room count (its head's number). */
  projectOpen: Record<string, number>;
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
    const [sends, people, ready] = await Promise.allSettled([
      apiFetch<unknown>("/api/channels/sends"),
      readPeopleProjection(),
      readUnreadReadyMeetings(),
    ]);
    // A live invalidation always refreshes A2 through its shared read. This
    // explicit refresh is the event path; the Dock does not start the hook's
    // minute poll.
    await refreshNeedsYou(true).catch(() => undefined);
    const readAt = Date.now();
    setReads((previous) => ({
      ...previous,
      ...(sends.status === "fulfilled" ? (() => {
        const settle = latestSendSettle(wireRows<DockSendRead>(sends.value, "sends"));
        return {
          sendOutcome: settle?.outcome ?? null,
          sendSettledAt: settle?.at ?? null,
          sendReadAt: readAt,
        };
      })() : {}),
      ...(people.status === "fulfilled" ? {
        peopleReadiness: people.value.readiness,
        ...(people.value.complete ? {
          nextOneOnOne: people.value.nextOneOnOne,
          peopleReadAt: readAt,
        } : { nextOneOnOne: null }),
      } : {
        nextOneOnOne: null,
        peopleReadiness: null,
      }),
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
    const hasSnapshot = reads.sendReadAt !== null || reads.peopleReadAt !== null || reads.readyReadAt !== null;
    if (state === "connected" && (reconnected || !hasSnapshot)) {
      void refresh();
    }
  }, [reads.peopleReadAt, reads.readyReadAt, reads.sendReadAt, refresh, runtimeState]);

  const lastSuccessfulAt = Math.max(
    reads.sendReadAt ?? 0,
    reads.peopleReadAt ?? 0,
    reads.readyReadAt ?? 0,
  ) || null;

  return {
    live,
    reads,
    offline: Boolean(lastSuccessfulAt !== null && runtimeState !== "connected"),
    lastSuccessfulAt,
    needsYouCount: needs.count,
    // A row the owner waits on someone else for is not counted on a badge.
    needsYouItems: needs.unmutedItems.filter((item) => !item.waiting),
    projectOpen: projectOpenHere(needs),
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
  const launchers = useLaunchers();
  // HS-111-07 — the HS-101 B8 keyboard grammar (Cmd+1-Cmd+4, Cmd+W, Cmd+M, Ctrl+`,
  // Cmd+/) moved into desk/keymap.ts, driven by the registry's key
  // fields: ONE binder (refcounted -- the chrome mounts it too). The
  // sheet's open state is shared chrome state so the system.sheet
  // verb can draw it.
  useKeymap();
  const sheetOpen = useShortcutSheet((s) => s.open);
  // HS-135-06: the Chair/Floor dock toggle (counsel ruling B.Q1).
  const chairSurface = useChairState((s) => s.surface);
  const toggleSurface = useChairState((s) => s.toggle);
  // PHILO-13-03 / C3: every Desk face reads the same membership snapshot.
  // The Dock opts out of the hook's minute poll; RuntimeBus invalidations
  // call the explicit refresh path in useDockLiveReads.
  const { live, reads, offline, lastSuccessfulAt, needsYouCount, projectOpen } = useDockLiveReads();
  const intelligenceBadge = !offline && needsYouCount > 0
    ? String(needsYouCount)
    : null;
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
  const shown = launchers.filter((l) => !windows.some((w) => w.id === l.id));
  const activeProjects = useDesk((s) => s.projects).filter((project) => !project.is_archived);
  // PHILO-14 A1: one Project, one number: the Room's own count.
  const projectCounts = projectOpen;
  const readyMeetingIds = new Set([...live.readyMeetingIds, ...reads.readyMeetingIds]);
  const readyMeetingBadge = !offline && readyMeetingIds.size > 0
    ? `READY ${readyMeetingIds.size}`
    : null;
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
  const sendOutcome = live.sendOutcome || reads.sendOutcome;
  // C3-W (C1-8a): SENT carries the settle time of the durable read; a frame
  // newer than that read shows its outcome alone until the read lands.
  const sendLabel = !offline
    ? dockStateLabel(sendOutcome, sendOutcome === reads.sendOutcome ? reads.sendSettledAt : null)
    : null;
  const sendTone = sendOutcome === "sent" ? "ok" : sendOutcome === "failed" ? "fail" : "warn";
  const peopleLabel = !offline && reads.peopleReadiness === "ready" && reads.nextOneOnOne
    ? `1:1 ${formatDockTime(reads.nextOneOnOne)}`
    : null;
  const hiddenProjectWindowIds = new Set(
    activeProjects
      .filter((project) => windowsById["surface-project-memory"]?.scope === `project:${project.id}`)
      .map((project) => `project:${project.id}`),
  );
  // PHILO-14 A2: an open drawer is its Project's launcher running (no second chip).
  const activeDrawerIds = new Set(activeProjects.map((project) => drawerWindowId(project.id)));
  const visibleWindowChips = windows.filter((window) =>
    !DOCK_APP_IDS.has(window.id) &&
      !activeDrawerIds.has(window.id) &&
      !hiddenProjectWindowIds.has(windowsById[window.id]?.scope || ""),
  );
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
      {DOCK_FACE_APPLICATIONS.map((application) => {
        const win = windows.find((w) => w.id === application.windowId);
        // Mounted DOM refs are runtime detail; the compositor owns whether a
        // hosted application is open. Intelligence is not yet a hosted surface.
        const running = application.surface
          ? Boolean(windowsById[application.windowId])
          : Boolean(win);
        const minimized = running && panelMin.includes(application.windowId);
        const badge =
            application.windowId === "intelligence:desk"
            ? intelligenceBadge
            : null;
        const needsYouBadge = badge !== null && badge !== "•";
        return (
          <Button
            key={application.windowId}
            variant="chrome"
            data-app={application.windowId}
            className={
              "desk-dock-launch desk-dock-app" +
              (running ? " is-run" : "") +
              (running && application.windowId === front && !minimized ? " is-front" : "") +
              (needsYouBadge ? " is-attention" : "")
            }
            aria-label={badge ? `${application.label}, ${needsYouBadge ? `${badge} need you` : "brief ready"}` : application.label}
            aria-describedby={application.windowId === "intelligence:desk" && sendLabel === "SEND FAILED"
              ? "desk-dock-send-failed-desc"
              : undefined}
            onClick={() => {
              const s = useDesk.getState();
              if (running && minimized) s.restorePanel(application.windowId);
              else if (running) s.focusPanel(application.windowId);
              else if (application.dock.launch === "intelligence")
                openIntelligence({ view: "brief" });
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
                id: application.windowId,
                label: application.label,
                x: e.clientX,
                y: e.clientY,
                minimized,
                close: win?.close ?? (() => useDesk.getState().closeSurfaceWindow(application.action)),
              });
            }}
          >
            {/* HS-111-09 — integer-true: the 32px source renders at 32
                CSS px (64 device px at DPR 2 = exact 2x); 24 was a 1.5x
                smear. */}
            {DOCK_SPRITES[application.windowId] ? (
              <img src={DOCK_SPRITES[application.windowId]} alt="" width={32} height={32} className="desk-dock-sprite" draggable={false} />
            ) : (
              <span aria-hidden="true">{application.glyph}</span>
            )}
            <span className="desk-dock-label">{application.label}</span>
            {badge ? (
              <span className="desk-chip desk-dock-badge" data-tone={needsYouBadge ? "warn" : undefined}>
                {badge}
              </span>
            ) : null}
            {application.windowId === "surface-meetings" && (recordingLabel || readyMeetingBadge) ? (
              <span
                className="desk-dock-state"
                data-testid="desk-dock-meetings-state"
                data-tone={recordingLabel ? "rec" : "ok"}
              >
                {recordingLabel || readyMeetingBadge}
              </span>
            ) : null}
            {application.windowId === "intelligence:desk" && sendLabel ? (
              <span className="desk-dock-state" data-testid="desk-dock-send-state" data-tone={sendTone}>
                {/* 393 reads the ratified short label FAILED (C1-8b); both
                    labels are whole words, one shown per width. */}
                {sendLabel === "SEND FAILED" ? (
                  <>
                    <span className="desk-dock-state-wide">SEND FAILED</span>
                    <span className="desk-dock-state-short">FAILED</span>
                  </>
                ) : sendLabel}
              </span>
            ) : null}
            {application.windowId === "intelligence:desk" && sendLabel === "SEND FAILED" ? (
              <span id="desk-dock-send-failed-desc" hidden>Send failed</span>
            ) : null}
            {application.windowId === "surface-people" && peopleLabel ? (
              <span className="desk-dock-state" data-testid="desk-dock-people-state">
                {peopleLabel}
              </span>
            ) : null}
          </Button>
        );
      })}
      {activeProjects.map((project) => {
        const projectWindow = windows.find(
          (window) => window.id === drawerWindowId(project.id) || (window.id === "surface-project-memory" &&
            windowsById["surface-project-memory"]?.scope === `project:${project.id}`),
        );
        const count = !offline ? projectCounts[project.id] || 0 : 0;
        return (
          <Button
            key={`project:${project.id}`}
            variant="chrome"
            data-app="project"
            className={`desk-dock-launch desk-dock-project${projectWindow ? " is-run" : ""}`}
            aria-label={count > 0 ? `${project.name}, ${count} open here` : project.name}
            // PHILO-14 A2: the Dock opens a Project as its drawer.
            onClick={() => openDrawer(project.id)}
          >
            {/* C1: a project is a drawer (the Workbench silhouette rule). */}
            <img src={spriteUrl("directory", project.id)} alt="" width={32} height={32} className="desk-dock-sprite" draggable={false} />
            <span className="desk-dock-label">{project.name}</span>
            {count > 0 ? (
              <span className="desk-chip desk-dock-badge" data-tone="warn">
                {count}
              </span>
            ) : null}
          </Button>
        );
      })}
      {/* HS-135-06 + HS-135-14: Floor/Chair toggle — the floor-grid
          sprite replaces the ▦ glyph character. */}
      <Button
        key="chair-floor-toggle"
        variant="chrome"
        className={
          "desk-dock-launch" +
          (chairSurface === "floor" ? " is-run" : "")
        }
        aria-label={chairSurface === "chair" ? "Floor" : "Chair"}
        aria-pressed={chairSurface === "floor"}
        onClick={toggleSurface}
        data-testid="chair-floor-toggle"
      >
        <img src={SYSTEM.floorGrid} alt="" width={32} height={32} className="desk-dock-sprite" draggable={false} />
        <span className="desk-dock-label">
          {chairSurface === "chair" ? "Floor" : "Chair"}
        </span>
      </Button>
      {shown.map((launcher) => {
        const actionable = ACTIONABLE_LAUNCHERS.has(launcher.id);
        return (
          <Button
            key={launcher.id}
            variant="chrome"
            className={
              "desk-dock-launch" +
              (launcher.open ? " is-run" : "") +
              (launcher.badge && actionable ? " is-attention" : "")
            }
            aria-label={
              launcher.badge
                ? `${launcher.label}, ${launcher.badge} ${actionable ? "need attention" : "items"}`
                : launcher.label
            }
            onClick={launcher.activate}
          >
            {DOCK_SPRITES[launcher.id] ? (
              <img src={DOCK_SPRITES[launcher.id]} alt="" width={32} height={32} className="desk-dock-sprite" draggable={false} />
            ) : (
              <span aria-hidden="true">{launcher.glyph}</span>
            )}
            <span className="desk-dock-label">{launcher.label}</span>
            {launcher.badge ? (
              <span
                className="desk-chip desk-dock-badge"
                data-tone={actionable ? "warn" : undefined}
              >
                {launcher.badge}
              </span>
            ) : null}
          </Button>
        );
      })}
      <RoomActions />
      {center}
      {visibleWindowChips.length > 0 ? (
        <span className="desk-dock-sep" aria-hidden="true" />
      ) : null}
      {visibleWindowChips.map((c) => {
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
      <Button
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
      </Button>
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
