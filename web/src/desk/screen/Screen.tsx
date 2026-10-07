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
 *  (screen/open.ts). The screen keeps no state beyond the selection. */
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { useAgentFlights } from "../agentFlights";
import { projectOpenHere, useNeedsYou } from "../needsYou";
import { Button } from "../../components/signal/Signal";
import { MicButton } from "../components/MicButton";
import { useDesk } from "../store";
import { DeskIcon, IconGrid, iconsInRect, type GridRect } from "../surface";
import { useCompactViewport } from "../useCompactViewport";
import { composeScreen, screenIsBare } from "./compose";
import { layoutScreen } from "./layout";
import { retryPeople, retryProject, useScreenMembers } from "./members";
import { openTarget } from "./open";
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

  const [selected, setSelected] = useState<ReadonlySet<string>>(new Set());
  const [marquee, setMarquee] = useState<GridRect | null>(null);
  // The selection holds only what is on the screen.
  useEffect(() => {
    setSelected((prev) => {
      const keys = new Set(objects.map((o) => o.key));
      const next = new Set([...prev].filter((k) => keys.has(k)));
      return next.size === prev.size ? prev : next;
    });
  }, [objects]);

  const ref = useRef<HTMLDivElement>(null);
  const size = useSize(ref);
  const placed = compact
    ? null
    : layoutScreen(objects, size.w || FALLBACK.w, size.h || FALLBACK.h);

  const bare = members.loaded && screenIsBare(objects);

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
          return (
            <div
              key={o.key}
              className={`desk-screen-cell${at ? " desk-screen-placed" : ""}`}
              style={at ? { left: at.x, top: at.y } : undefined}
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
