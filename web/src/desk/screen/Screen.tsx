/** PHILO-14 A1 — THE SCREEN: the Chair is the desk of objects (board A-1).
 *
 *  Ratified 2026-10-07 (docs/internal/philo/phase-14/canvas/README.md, A
 *  Workbench). On arrival the owner sees his desk as objects: the drawers
 *  (his Projects with a count notch and a lamp, People, the Conductor), the
 *  loose objects no Project holds, the live agents, Needs you and Parked.
 *  The four former tiles are windows he opens (chair/chairWindows.ts).
 *
 *  Composed of the object species only (DeskIcon, IconGrid). A press
 *  selects; the rubber band selects many; Enter or a double press opens
 *  (screen/open.ts). The selection is the desk's one selection (the store's
 *  selectedIds, PHILO-17): the menu bar Object menu, F2 and the right-click
 *  menu act on it exactly as on the Floor. */
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { useAgentFlights } from "../agentFlights";
import { projectOpenHere, useNeedsYou } from "../needsYou";
import { Button } from "../../components/signal/Signal";
import { MicButton } from "../components/MicButton";
import { useDesk } from "../store";
import { WorkMenu } from "../components/DeskMenu";
import { objectMenuEntries } from "../floorMenu";
import { objectByRef } from "../world";
import { DeskIcon, IconGrid, iconsInRect, type GridRect } from "../surface";
import { useCompactViewport } from "../useCompactViewport";
import { composeScreen, screenIsBare } from "./compose";
import { layoutScreen } from "./layout";
import { retryPeople, retryProject, useScreenMembers } from "./members";
import { openTarget } from "./open";
import { SCREEN_HOST, HandConfirmSlot, handOriginOfRef, handSourceProps, handTargetProps, useDropHand } from "../hand";
import "./screen.css";

/** The A-1 screen measured at 1440 × 900 (a screen that has not laid out yet). */
const FALLBACK = { w: 1440, h: 796 };

function useSize(ref: React.RefObject<HTMLElement | null>) {
  const [size, setSize] = useState({ w: 0, h: 0 });
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const read = () => setSize({ w: el.clientWidth, h: el.clientHeight });
    read();
    if (typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(read);
    ro.observe(el);
    return () => ro.disconnect();
  }, [ref]);
  return size;
}

export function Screen() {
  const items = useDesk((s) => s.items);
  const needs = useNeedsYou();
  // The agents: the one store the Arrival keeps live (useAgentFlightsLive in ChairHome).
  const sessions = useAgentFlights((s) => s.sessions);
  const flights = useAgentFlights((s) => s.flights);
  const compact = useCompactViewport();

  const projects = useMemo(
    () => (items.project ?? []).map((p) => ({ id: p.id, updatedAt: p.updatedAt })),
    [items.project],
  );
  const members = useScreenMembers(projects);

  const objects = useMemo(() => {
    const needsRefs = new Set<string>();
    let heldCalls = 0;
    for (const item of needs.unmutedItems) {
      for (const ref of [item.ref, item.openRef]) if (ref) needsRefs.add(String(ref));
      if (String(item.ref ?? "").startsWith("gate:") && !item.waiting) heldCalls += 1;
    }
    for (const meeting of needs.failedMeetings) needsRefs.add(`meeting:${meeting.id}`);
    return composeScreen({
      items,
      projectCounts: projectOpenHere(needs),
      needsCount: needs.count,
      needsRefs,
      heldCalls,
      sessions,
      flights,
      filed: members.filed,
      persons: members.persons,
      membersLoaded: members.loaded,
      notRead: members.notRead,
      unknownAll: members.unknownAll,
      unknownMeetings: members.unknownMeetings,
      peopleNotRead: members.peopleNotRead,
    });
  }, [items, needs, sessions, flights, members]);

  // PHILO-17: the one selection truth. The menu bar Object menu, the keymap
  // (F2) and the Floor read the store's selectedIds; the screen writes there.
  const selectedIds = useDesk((s) => s.selectedIds);
  const selected = useMemo(() => new Set(selectedIds), [selectedIds]);
  const setSelected = (keys: Iterable<string>) => useDesk.getState().setSelected([...keys]);
  const [marquee, setMarquee] = useState<GridRect | null>(null);
  const [menu, setMenu] = useState<{ key: string; id: string; kind: string; title: string; x: number; y: number } | null>(null);
  // The selection holds only what is on the screen.
  useEffect(() => {
    const prev = useDesk.getState().selectedIds;
    const keys = new Set(objects.map((o) => o.key));
    const next = prev.filter((k) => keys.has(k));
    if (next.length !== prev.length) useDesk.getState().setSelected(next);
  }, [objects]);
  // The right-click menu: the Floor's object menu (floorMenu.ts), for an
  // object the desk can resolve. A drawer with no object keeps no menu.
  const openMenu = (key: string, x: number, y: number): boolean => {
    const o = objectByRef(items, key);
    if (!o) return false;
    setSelected([key]);
    setMenu({ key, id: o.id, kind: o.kind, title: o.title, x, y });
    return true;
  };

  const ref = useRef<HTMLDivElement>(null);
  const size = useSize(ref);
  const placed = compact
    ? null
    : layoutScreen(objects, size.w || FALLBACK.w, size.h || FALLBACK.h);

  const bare = members.loaded && screenIsBare(objects);
  // PHILO-14 C3: drop to hand. A loose work item drags (not at 393: the
  // hand there is the verb); the Conductor drawer and the agents take it.
  const drag = useDropHand((s) => s.drag);

  return (
    <div className="desk-screen" ref={ref} data-testid="desk-screen" data-layout={compact ? "grid" : "free"}>
      <IconGrid
        label="Desk"
        marquee={marquee}
        onMarquee={(rect, grid) => {
          setMarquee(rect);
          if (rect) setSelected(new Set(iconsInRect(grid, rect)));
        }}
        onClear={() => setSelected(new Set())}
      >
        {objects.map((o) => {
          const at = placed?.[o.key];
          const hand = !compact && o.role === "loose" ? handOriginOfRef(o.key, o.name) : null;
          const dragProps = hand
            ? handSourceProps({ origin: hand, source: { kind: o.kind, id: o.key, sprite: o.sprite }, host: SCREEN_HOST })
            : {};
          return (
            <div
              key={o.key}
              className={`desk-screen-cell${at ? " desk-screen-placed" : ""}`}
              style={at ? { left: at.x, top: at.y } : undefined}
              onContextMenu={(event) => {
                if (openMenu(o.key, event.clientX, event.clientY)) event.preventDefault();
              }}
              onKeyDown={(event) => {
                if (event.key !== "ContextMenu" && !(event.shiftKey && event.key === "F10")) return;
                const rect = (event.target as HTMLElement).getBoundingClientRect();
                if (openMenu(o.key, rect.left + 24, rect.bottom)) event.preventDefault();
              }}
            >
              <DeskIcon
                id={o.key}
                kind={o.kind}
                kindWord={o.kindWord}
                name={o.name}
                sprite={o.sprite}
                spriteSelected={o.spriteSelected}
                badge={o.badge}
                lamp={o.lamp}
                count={o.count}
                ariaExtra={o.ariaExtra}
                selected={selected.has(o.key)}
                onSelect={() => setSelected(new Set([o.key]))}
                onOpen={() => openTarget(o.target)}
                drop={drag?.over === o.key}
                ghost={drag?.host === SCREEN_HOST && drag.source.id === o.key}
                {...dragProps}
                {...handTargetProps(o.key)}
              />
              {o.notRead ? (
                <span className="desk-screen-notread" data-testid={`desk-screen-notread-${o.key}`}>
                  <span className="desk-screen-fact">NOT READ</span>
                  <Button
                    dense
                    variant="ghost"
                    aria-label={`Retry ${o.name}`}
                    onClick={() => {
                      const r = o.notRead!.retry;
                      if (r.type === "project") retryProject(r.id);
                      else retryPeople();
                    }}
                  >
                    Retry
                  </Button>
                </span>
              ) : null}
            </div>
          );
        })}
      </IconGrid>
      {menu ? (
        <WorkMenu
          className="desk-world-menu"
          label={`${menu.title} menu`}
          anchor="below"
          x={menu.x}
          y={menu.y}
          autoFocus
          entries={objectMenuEntries({ type: "object", id: menu.id, ref: menu.key, kind: menu.kind, title: menu.title })}
          onClose={() => setMenu(null)}
        />
      ) : null}
      <HandConfirmSlot host={SCREEN_HOST} className="desk-screen-hand" />
      {compact ? null : (
        // Astra's P3 on #939 (ruling): TALK is one press on the Chair. The
        // Capture window's own control, at the screen's foot-left.
        <span className="desk-screen-talk arrival-capture-talk" data-testid="desk-screen-talk">
          <MicButton onText={() => undefined} label="Talk" variant="transport" />
        </span>
      )}
      {bare ? (
        <p className="desk-screen-empty" data-testid="desk-screen-empty">
          The desk is empty. Press Speak to start.
        </p>
      ) : null}
    </div>
  );
}
