/** PHILO-16 — the compositor's desk layer: mounts `useCompositor()` once and
 * draws the shared-resize dividers (L8). A divider is derived, never a mode:
 * wherever two shown windows' edges touch (Tile and Gather make them touch),
 * ONE steel divider sits on the seam; dragging it moves every near edge of
 * the boundary and keeps every far edge. */
import { useRef, useSyncExternalStore } from "react";
import { useDesk } from "../store";
import { useCompactViewport } from "../useCompactViewport";
import { boundaries, resizeBoundary, type Boundary, type ResizeWindow } from "./sharedResize";
import { computePlanes, liveVersion, subscribeLive, zOfWindow } from "./live";
import { Z } from "./layers";
import { bandNow, minOf, stillUnderPointer, useCompositor, useMode } from "./useCompositor";
import { shellEls } from "../components/window/windowRegistry";

const KEY_STEP = 16;

function Divider({ b, wins, z }: { b: Boundary; wins: ResizeWindow[]; z: number }) {
  const drag = useRef<{ start: number; base: ResizeWindow[] } | null>(null);
  const v = b.axis === "v";
  const write = (delta: number, persist: boolean, base: ResizeWindow[]) => {
    const s = useDesk.getState();
    for (const [id, r] of resizeBoundary(b, base, delta, { band: bandNow() })) s.setPanelRect(id, r, persist);
  };
  const ids = [...b.before, ...b.after];
  return (
    <div
      className={`desk-window-divider is-${v ? "v" : "h"}`}
      role="separator"
      aria-orientation={v ? "vertical" : "horizontal"}
      aria-label="Resize the windows on both sides"
      tabIndex={0}
      style={
        v
          ? { left: b.at - 3, top: b.start, width: 6, height: b.end - b.start, zIndex: z }
          : { top: b.at - 3, left: b.start, height: 6, width: b.end - b.start, zIndex: z }
      }
      onPointerDown={(e) => {
        if (e.button !== 0) return;
        e.preventDefault();
        e.stopPropagation();
        (e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId);
        for (const id of ids) stillUnderPointer(shellEls.get(id) ?? null);
        drag.current = { start: v ? e.clientX : e.clientY, base: wins };
      }}
      onPointerMove={(e) => {
        const d = drag.current;
        if (!d) return;
        write((v ? e.clientX : e.clientY) - d.start, false, d.base);
      }}
      onPointerUp={(e) => {
        const d = drag.current;
        drag.current = null;
        if (d) write((v ? e.clientX : e.clientY) - d.start, true, d.base);
      }}
      onPointerCancel={() => {
        drag.current = null;
      }}
      onKeyDown={(e) => {
        const back = v ? "ArrowLeft" : "ArrowUp";
        const fwd = v ? "ArrowRight" : "ArrowDown";
        if (e.key !== back && e.key !== fwd) return;
        e.preventDefault();
        write(e.key === fwd ? KEY_STEP : -KEY_STEP, true, wins);
      }}
    />
  );
}

export function CompositorLayer() {
  useCompositor();
  const mode = useMode();
  const compact = useCompactViewport();
  useSyncExternalStore(subscribeLive, liveVersion);
  const rects = useDesk((s) => s.panelRects);
  const depth = useDesk((s) => s.panelDepth);
  const min = useDesk((s) => s.panelMin);
  const max = useDesk((s) => s.panelMax);
  if (compact || mode === "stage" || mode === "expose") return null;
  const live = computePlanes(depth, min);
  // Astra M2: each window's real minimum, the larger of its frame's minW /
  // minH and its CSS min-width / min-height (a surface window is 420 wide).
  const wins: ResizeWindow[] = live.shown
    .filter((id) => !max.includes(id) && rects[id])
    .map((id) => {
      const min = minOf(id);
      return { id, rect: rects[id], minW: min.w, minH: min.h };
    });
  const found = boundaries(wins);
  if (!found.length) return null;
  return (
    <>
      {found.map((b) => {
        // Above both windows (Astra M3: z from the shown order); the divider
        // renders after every window, so a tie at the band's top still paints it.
        const z = Math.min(Z.windowTop, Math.max(...[...b.before, ...b.after].map((id) => zOfWindow(id, live))) + 1);
        return (
          <Divider
            key={`${b.axis}:${[...b.before].sort().join(",")}|${[...b.after].sort().join(",")}`}
            b={b}
            wins={wins}
            z={z}
          />
        );
      })}
    </>
  );
}
