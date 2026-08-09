// The desk-window contract (Phase 93 UI remediation; HS-95-02 makes it an
// OS): floating desk panels are windows, not fixtures. The `useDeskWindow`
// hook below carries the physics — drag (by the head), resize (corner
// grip), focus-to-front, persisted rect — and `DeskWindowFrame` is the ONE
// container every window renders through: one chrome (icon · title ·
// actions · minimize/maximize/close), a children content slot, lifecycle
// state in the store (`panelMin`/`panelMax`, persisted in the same
// `hs.desk.panels` slot as the rects), and the phone's bottom-sheet form.
// The hook is module-private on purpose: windows do not hand-wire physics.
//
// HS-117-04 — decomposed into focused modules under `window/`. This file
// retains useDeskWindow + DeskWindowFrame + re-exports for API stability.
import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { motion, useReducedMotion } from "motion/react";
import { useDrag } from "@use-gesture/react";
import { useDesk, type PanelRect } from "../store";
import { DeskMenuItem, DeskMenuList } from "./DeskMenu";
import { DESK_WINDOW, DESK_Z } from "../../lib/tokens.gen";

// -- Extracted modules (HS-117-04) --
import {
  MARGIN,
  workBand,
  placeWindow,
  clampIntoBand,
  snapForPointer,
  resizeEdge,
  clampRect,
  exposeLayout,
  mruOrder,
} from "./window/windowGeometry";
import {
  chipEls,
  shellEls,
  windowRegistry,
  registrySnapshot,
  announceWindow,
  retractWindow,
  useOpenWindows,
  frontWindowId,
  openWindowCount,
  closeFrontWindow,
  minimizeFrontWindow,
  cycleWindows as cycleWindowsRaw,
  cycleWindowsReverse as cycleWindowsReverseRaw,
  focusOrRestoreApp,
} from "./window/windowRegistry";
import {
  type DockLauncher,
  announceLauncher,
  retractLauncher,
  activateLauncher,
  useLaunchers,
} from "./window/launcherRegistry";
import { publishGhost, SnapGhost } from "./window/SnapGhost";
import { flashSwitcher, Switcher } from "./window/Switcher";
import { toggleExpose, Expose } from "./window/Expose";
import { VerbGlyph } from "./window/VerbGlyph";
import { Dock } from "./window/Dock";

// -- Re-exports: zero consumer edits (HS-117-04) --
export { placeWindow, clampIntoBand, snapForPointer, resizeEdge, exposeLayout };
export { SnapGhost, Switcher, Expose, Dock };
export { toggleExpose };
export {
  useOpenWindows,
  frontWindowId,
  openWindowCount,
  closeFrontWindow,
  minimizeFrontWindow,
  focusOrRestoreApp,
};
export {
  type DockLauncher,
  announceLauncher,
  retractLauncher,
  activateLauncher,
  useLaunchers,
};

/** Ctrl+` — MRU cycle (binds the switcher's flashSwitcher). */
export function cycleWindows(): void {
  cycleWindowsRaw(flashSwitcher);
}

/** Ctrl+Shift+` — reverse MRU cycle (binds the switcher's flashSwitcher). */
export function cycleWindowsReverse(): void {
  cycleWindowsReverseRaw(flashSwitcher);
}

/** Apply the same working-band geometry as an edge drag to the front window. */
export function snapFrontWindow(side: "left" | "right"): void {
  const id = frontWindowId();
  if (!id || typeof window === "undefined") return;
  const state = useDesk.getState();
  const vw = window.innerWidth || 1280;
  const vh = window.innerHeight || 800;
  const rect = snapForPointer(side === "left" ? 0 : vw, vh / 2, vw, vh);
  if (!rect) return;
  if (state.panelMax.includes(id)) state.toggleMaximizePanel(id);
  if (state.panelMin.includes(id)) state.restorePanel(id);
  state.setPanelRect(id, rect, true);
  state.focusPanel(id);
}

/** Fill the desk working band with the front window. */
export function maximizeFrontWindow(): void {
  const id = frontWindowId();
  if (!id) return;
  const state = useDesk.getState();
  if (state.panelMin.includes(id)) state.restorePanel(id);
  if (!state.panelMax.includes(id)) state.toggleMaximizePanel(id);
  else state.focusPanel(id);
}

/** The desk-window z band (see the ladder note in desk.css). */
const Z_BASE = DESK_Z.windowBase;

export interface DeskWindowOptions {
  minW?: number;
  minH?: number;
  /** Pass false while the panel renders nothing (launcher-only mounts). */
  open?: boolean;
  /** Round 8 — a content-sized card: height stays CSS-driven (the
   * material decides) until the user arranges the window; the HS-97-09
   * max-height seed inflation is skipped. */
  fitContent?: boolean;
  /** Round 9 — the client point this window opened FROM (the tapped
   * desk object). The window seats itself beside it and the open/close
   * motion flies out of and back into it — spatial, not a side dock. */
  origin?: { x: number; y: number } | null;
}

let resizeClampUsers = 0;
let resizeClampTimer: ReturnType<typeof setTimeout> | undefined;

function reClampOpenWindows() {
  const state = useDesk.getState();
  for (const { id } of registrySnapshot) {
    const rect = state.panelRects[id];
    if (!rect || state.panelMax.includes(id)) continue;
    const clamped = clampRect(rect, 320, 220);
    if (
      clamped.x !== rect.x ||
      clamped.y !== rect.y ||
      clamped.w !== rect.w ||
      clamped.h !== rect.h
    )
      state.setPanelRect(id, clamped, state.panelSaved.includes(id));
  }
}

function onWindowResize() {
  clearTimeout(resizeClampTimer);
  resizeClampTimer = setTimeout(reClampOpenWindows, 150);
}

function subscribeResizeClamp() {
  if (resizeClampUsers++ === 0)
    window.addEventListener("resize", onWindowResize);
  return () => {
    if (--resizeClampUsers === 0) {
      window.removeEventListener("resize", onWindowResize);
      clearTimeout(resizeClampTimer);
    }
  };
}

/** The desk-window physics (Phase 93). Module-private since HS-95-02:
 * every window adopts it through `DeskWindowFrame`, never by hand. */
function useDeskWindow(id: string, opts: DeskWindowOptions = {}) {
  const minW = opts.minW ?? 320;
  const minH = opts.minH ?? 220;
  const open = opts.open ?? true;
  const rect = useDesk((s) => s.panelRects[id]);
  const orderIndex = useDesk((s) => s.panelOrder.indexOf(id));
  const arranged = useDesk((s) => s.panelSaved.includes(id));
  // A fit-content card pins its height DURING the first resize drag,
  // before the arrangement persists on pointer-up.
  const [liveResize, setLiveResize] = useState(false);
  const elRef = useRef<HTMLElement | null>(null);

  const measure = (): PanelRect => {
    const cur = useDesk.getState().panelRects[id];
    if (cur) return cur;
    const el = elRef.current;
    const r = el?.getBoundingClientRect();
    if (!el || !r || !r.width) return { x: MARGIN, y: 64, w: 400, h: 480 };
    // The entrance spring translates the panel; strip the live transform so
    // a mid-animation measure still yields the settled rect.
    let tx = 0;
    let ty = 0;
    try {
      const t = getComputedStyle(el).transform;
      if (t && t !== "none") {
        const m = new DOMMatrixReadOnly(t);
        tx = m.m41;
        ty = m.m42;
      }
    } catch {
      /* environments without DOMMatrix just measure as-is */
    }
    return { x: r.left - tx, y: r.top - ty, w: r.width, h: r.height };
  };

  // HS-97-02 — a window lands well. Opening places the window through
  // the engine (seeded at its CSS default home, moved off other title
  // bars, always whole inside the working band); a persisted rect is
  // clamped into the band and otherwise untouched (the arrangement is
  // sacred). Sheets (compact viewports) own their own form.
  // Round 9: a LAYOUT effect — the window never paints a frame at its
  // CSS home before the engine seats it (the teleport flash), and an
  // origin window's entrance motion starts before first paint.
  useLayoutEffect(() => {
    if (!open) return;
    // Present, don't blindly raise: a window rehydrating on reload keeps
    // its remembered plane in the stacking order (HS-97-03).
    useDesk.getState().presentPanel(id);
    if (
      typeof window.matchMedia === "function" &&
      window.matchMedia("(max-width: 720px)").matches
    )
      return;
    const s = useDesk.getState();
    const vw = window.innerWidth || 1280;
    const vh = window.innerHeight || 800;
    const cur = s.panelRects[id];
    if (cur) {
      const kept = clampIntoBand(cur, vw, vh, minW, minH);
      if (
        kept.x !== cur.x ||
        kept.y !== cur.y ||
        kept.w !== cur.w ||
        kept.h !== cur.h
      )
        s.setPanelRect(id, kept, s.panelSaved.includes(id));
    } else {
      const others = registrySnapshot
        .filter((w) => w.id !== id && !s.panelMin.includes(w.id))
        .map((w) => s.panelRects[w.id])
        .filter((r): r is PanelRect => Boolean(r));
      const seed = measure();
      // Lazy cores may still be a Suspense fallback at measure time; a
      // window's geometry comes from its CSS constraint (max-height),
      // never from the transient content height. The default seat is
      // capped below the full band so title bars can stagger — a
      // full-band window is a choice (resize/maximize), not a default
      // (HS-97-09).
      const el = elRef.current;
      if (el && !opts.fitContent) {
        const mh = parseFloat(getComputedStyle(el).maxHeight);
        const cap = Math.max(
          minH,
          Math.round(
            ((vh - workBand().top - workBand().bottom) * 78) / 100,
          ),
        );
        if (Number.isFinite(mh) && mh > seed.h)
          seed.h = Math.min(mh, cap);
      }
      const origin = opts.origin;
      if (origin) {
        // The spatial seat: beside the object it opened from — the
        // right flank when it fits, the left otherwise; placeWindow
        // still nudges it off other title bars and into the band.
        const rightX = origin.x + 28;
        const leftX = origin.x - seed.w - 28;
        seed.x =
          rightX + seed.w <= vw - MARGIN ? rightX : Math.max(MARGIN, leftX);
        seed.y = origin.y - 56;
      }
      const placed = placeWindow(seed, others, vw, vh, minW, minH);
      s.setPanelRect(id, placed);
      if (
        origin &&
        el &&
        typeof el.animate === "function" &&
        !(
          typeof window.matchMedia === "function" &&
          window.matchMedia("(prefers-reduced-motion: reduce)").matches
        )
      ) {
        // The open flies OUT of the object (the minimize grammar,
        // pointed at the world instead of the dock).
        const dx = origin.x - (placed.x + placed.w / 2);
        const dy = origin.y - (placed.y + Math.min(placed.h, 320) / 2);
        el.animate(
          [
            {
              transform: `translate(${dx}px, ${dy}px) scale(0.05)`,
              opacity: 0,
            },
            { transform: "translate(0, 0) scale(1)", opacity: 1 },
          ],
          { duration: 240, easing: "cubic-bezier(.2, .8, .2, 1)" },
        );
      }
    }
    return () => {
      // An unarranged (never persisted) rect is ephemeral: forget it so
      // the panel is re-placed from its default home next time. Closing
      // also leaves the stacking order, so a reopen presents on top.
      const st = useDesk.getState();
      if (!st.panelSaved.includes(id) && st.panelRects[id])
        st.resetPanelRect(id);
      st.retirePanel(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, open]);

  // One compositor listener re-seats open windows after a viewport change.
  // The 150ms debounce keeps browser resize storms out of the layout path.
  useEffect(() => {
    if (!open || typeof window === "undefined") return;
    return subscribeResizeClamp();
  }, [open]);

  // Round 9 — growth settles with motion: a content-sized card whose
  // material arrives async (a meeting detail, a relationships fetch)
  // GROWS smoothly instead of popping. Only while the height is still
  // CSS-driven (unarranged, not mid-resize: those set style.height).
  useEffect(() => {
    if (!opts.fitContent || arranged || !open) return;
    const el = elRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    if (
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    )
      return;
    let last = el.getBoundingClientRect().height;
    let animating = false;
    const ro = new ResizeObserver(() => {
      if (animating) return;
      // An explicit height (arranged pin, live resize, maximize) is the
      // user's geometry — never animated under them.
      if (el.style.height) {
        last = el.getBoundingClientRect().height;
        return;
      }
      const h = el.getBoundingClientRect().height;
      if (!last || Math.abs(h - last) < 3) {
        last = h;
        return;
      }
      const from = last;
      last = h;
      if (typeof el.animate !== "function") return;
      animating = true;
      const anim = el.animate(
        [{ height: `${from}px` }, { height: `${h}px` }],
        { duration: 200, easing: "cubic-bezier(.2, .8, .2, 1)" },
      );
      anim.onfinish = anim.oncancel = () => {
        animating = false;
        last = el.getBoundingClientRect().height;
      };
    });
    ro.observe(el);
    return () => ro.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opts.fitContent, arranged, open]);

  const dragBind = useDrag(
    ({ event, first, last, movement: [mx, my], memo }) => {
      // Buttons and inputs inside the head keep their own gestures.
      if (first) {
        const t = event?.target as HTMLElement | null;
        if (t?.closest("button, a, input, textarea, select, [role='button']"))
          return { skip: true };
      }
      if (memo?.skip) return memo;
      const base: PanelRect = memo?.base ?? measure();
      if (Math.abs(mx) + Math.abs(my) > 3) {
        // A snap region shows its landing tile as a live ghost while
        // dragging (HS-97-05); releasing inside it lands exactly there
        // (HS-95-03); anywhere else parks the dragged rect as before.
        const ev = event as PointerEvent | undefined;
        const tile =
          ev && typeof ev.clientX === "number"
            ? snapForPointer(
                ev.clientX,
                ev.clientY,
                window.innerWidth || 1280,
                window.innerHeight || 800,
              )
            : null;
        publishGhost(last ? null : tile);
        useDesk
          .getState()
          .setPanelRect(
            id,
            (last ? tile : null) ??
              clampRect(
                { ...base, x: base.x + mx, y: base.y + my },
                minW,
                minH,
              ),
            last,
          );
      } else if (last) {
        publishGhost(null);
      }
      return { base, skip: false };
    },
    { pointer: { buttons: 1 } },
  );

  const resizeBind = useDrag(
    ({ movement: [mx, my], last, memo }) => {
      const base: PanelRect = memo?.base ?? measure();
      setLiveResize(!last);
      useDesk
        .getState()
        .setPanelRect(
          id,
          clampRect({ ...base, w: base.w + mx, h: base.h + my }, minW, minH),
          last,
        );
      return { base };
    },
    { pointer: { buttons: 1 } },
  );

  // HS-97-05 — the frame resizes from its edges, not one corner.
  const edgeBind = useDrag(
    ({ args, movement: [mx, my], last, memo }) => {
      const mode = String(args?.[0] ?? "br");
      const base: PanelRect = memo?.base ?? measure();
      setLiveResize(!last);
      useDesk
        .getState()
        .setPanelRect(id, resizeEdge(mode, base, mx, my, minW, minH), last);
      return { base };
    },
    { pointer: { buttons: 1 } },
  );
  const edgeStyle = { touchAction: "none" } as React.CSSProperties;
  const edges = (
    <>
      <span
        className="desk-window-edge desk-window-edge-l"
        {...edgeBind("l")}
        style={edgeStyle}
        aria-hidden="true"
      />
      <span
        className="desk-window-edge desk-window-edge-r"
        {...edgeBind("r")}
        style={edgeStyle}
        aria-hidden="true"
      />
      <span
        className="desk-window-edge desk-window-edge-b"
        {...edgeBind("b")}
        style={edgeStyle}
        aria-hidden="true"
      />
      <span
        className="desk-window-corner desk-window-corner-bl"
        {...edgeBind("bl")}
        style={edgeStyle}
        aria-hidden="true"
      />
    </>
  );

  // HS-129-11 — a fit-content card may grow after placement (async detail
  // content), but its CSS-driven height must still stop at the same lower
  // working-band edge that `placeWindow` used for its rect. Arranged and
  // maximized windows retain their explicit geometry below.
  const cardBandCap = rect
    ? Math.max(minH, (typeof window === "undefined" ? 800 : window.innerHeight) - workBand().bottom - rect.y)
    : undefined;
  const style: React.CSSProperties = rect
    ? {
        top: rect.y,
        left: rect.x,
        width: rect.w,
        right: "auto",
        bottom: "auto",
        zIndex: Z_BASE + Math.max(orderIndex, 0),
        // A content-sized card keeps its CSS height (the material
        // decides) until the user arranges it; arranged rects pin.
        ...(opts.fitContent && !arranged && !liveResize
          ? { maxHeight: cardBandCap }
          : { height: rect.h, maxHeight: "none" }),
      }
    : { zIndex: Z_BASE + Math.max(orderIndex, 0) };

  return {
    /** True when the user (or the cascade) gave this window its own rect. */
    floating: Boolean(rect),
    style,
    setEl: (el: HTMLElement | null) => {
      elRef.current = el;
    },
    focus: () => useDesk.getState().focusPanel(id),
    handleProps: {
      ...dragBind(),
      style: { touchAction: "none" } as React.CSSProperties,
    },
    grip: (
      <span className="desk-window-grip" {...resizeBind()} aria-hidden="true" />
    ),
    edges,
  };
}

function useCompactViewport(): boolean {
  return useSyncExternalStore(
    (cb) => {
      if (typeof window.matchMedia !== "function") return () => {};
      const mq = window.matchMedia("(max-width: 720px)");
      mq.addEventListener("change", cb);
      return () => mq.removeEventListener("change", cb);
    },
    () =>
      typeof window.matchMedia === "function"
        ? window.matchMedia("(max-width: 720px)").matches
        : false,
  );
}

export interface DeskWindowFrameProps {
  id: string;
  /** The head title (any node). Pass `label` when it isn't plain text. */
  title: ReactNode;
  /** Plain-text name for the tray/dock and aria labels. */
  label?: string;
  /** A small leading glyph/avatar node (the window's face). */
  icon?: ReactNode;
  /** One-character dock face when `icon` is a node (default ▢). */
  glyph?: string;
  /** Content before the icon (e.g. a back chip). */
  leading?: ReactNode;
  /** One-word kind eyebrow — DEMOTED from the head (HS-97-07, Article
   * VII.1); accepted for compatibility, no longer rendered. */
  eyebrow?: string;
  /** Extra head content (badges, panel-specific verbs), left of the window verbs. */
  actions?: ReactNode;
  /** HS-100-07 — the application's wing segments, centered in the head
   * (the thesis's posture rule: faces live in the head, never as a tab
   * wall in the body). */
  wings?: ReactNode;
  /** Root classes — keep the panel's legacy class so its content CSS holds. */
  className?: string;
  minW?: number;
  minH?: number;
  /** Content-sized card: see DeskWindowOptions.fitContent. */
  fitContent?: boolean;
  /** The client point this window opened from: see DeskWindowOptions. */
  origin?: { x: number; y: number } | null;
  open: boolean;
  onClose: () => void;
  /** Heavy content may unmount while minimized (default: stays mounted). */
  unmountOnMinimize?: boolean;
  /** Entrance spring (the Phase 93 slide-in). Default true. */
  entrance?: boolean;
  /** Inline style merged under the window geometry (e.g. CSS vars). */
  rootStyle?: React.CSSProperties;
  children?: ReactNode;
}

/** THE window. One chrome, one lifecycle, one physics contract — content
 * plugs in as children (Constitution, Article I: features do not own
 * surfaces). */
export function DeskWindowFrame(props: DeskWindowFrameProps) {
  const {
    id,
    title,
    label,
    icon,
    glyph: glyphProp,
    leading,
    actions,
    wings,
    className,
    minW,
    minH,
    fitContent,
    origin,
    open,
    onClose,
    unmountOnMinimize,
    entrance = true,
    rootStyle,
    children,
  } = props;
  const minimized = useDesk((s) => s.panelMin.includes(id));
  const maximized = useDesk((s) => s.panelMax.includes(id));
  // HS-97-04 — the front window is the last id in the stacking order
  // that is open (announced) and not minimized; it alone wears depth.
  const isFront = useDesk((s) => {
    for (let i = s.panelOrder.length - 1; i >= 0; i--) {
      const oid = s.panelOrder[i];
      if (s.panelMin.includes(oid)) continue;
      if (!windowRegistry.has(oid)) continue;
      return oid === id;
    }
    return false;
  });
  const compact = useCompactViewport();
  const reducedMotion = useReducedMotion();
  const win = useDeskWindow(id, {
    minW,
    minH,
    fitContent,
    origin,
    open: open && !minimized,
  });
  const glyph = glyphProp ?? (typeof icon === "string" ? icon : "▢");
  const name = label ?? (typeof title === "string" ? title : id);

  const closeRef = useRef(onClose);
  closeRef.current = onClose;

  // HS-99-02 — the head's right-click menu (chrome ladder rule 2).
  const [headMenu, setHeadMenu] = useState<{ x: number; y: number } | null>(
    null,
  );
  useEffect(() => {
    if (!headMenu) return;
    const close = () => setHeadMenu(null);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    window.addEventListener("pointerdown", close);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("pointerdown", close);
      window.removeEventListener("keydown", onKey);
    };
  }, [headMenu]);

  // HS-97-04 — motion tells the story: close animates out; minimize
  // contracts toward the window's dock chip and restore returns from
  // it. WAAPI (compositor-only transform/opacity), skipped under
  // reduced motion or where unavailable (jsdom).
  const shellRef = useRef<HTMLDivElement | null>(null);
  const leavingRef = useRef(false);
  const dockChip = () => chipEls.get(id) ?? null;
  const flyToChip = (el: HTMLElement, chip: Element, reverse: boolean) => {
    const c = chip.getBoundingClientRect();
    const r = el.getBoundingClientRect();
    const dx = c.x + c.width / 2 - (r.x + r.width / 2);
    const dy = c.y + c.height / 2 - (r.y + r.height / 2);
    const away = { transform: `translate(${dx}px, ${dy}px) scale(0.06)`, opacity: 0 };
    const home = { transform: "translate(0, 0) scale(1)", opacity: 1 };
    return el.animate(reverse ? [away, home] : [home, away], {
      duration: 220,
      easing: "cubic-bezier(.2, .8, .2, 1)",
      fill: "forwards",
    });
  };
  const requestClose = () => {
    const el = shellRef.current;
    if (leavingRef.current) return;
    if (!el || typeof el.animate !== "function" || reducedMotion) {
      closeRef.current();
      return;
    }
    leavingRef.current = true;
    // Round 9 — a window born from a desk object returns INTO it; the
    // rest keep the quiet scale-fade.
    const r = origin && !compact ? el.getBoundingClientRect() : null;
    const anim = el.animate(
      origin && r
        ? [
            { opacity: 1, transform: "translate(0, 0) scale(1)" },
            {
              opacity: 0,
              transform: `translate(${origin.x - (r.x + r.width / 2)}px, ${
                origin.y - (r.y + r.height / 2)
              }px) scale(0.05)`,
            },
          ]
        : [
            { opacity: 1, transform: "scale(1)" },
            { opacity: 0, transform: "scale(0.96)" },
          ],
      {
        duration: origin && r ? 200 : 140,
        easing: origin && r ? "cubic-bezier(.4, 0, .8, .4)" : "ease-in",
        fill: "forwards",
      },
    );
    anim.onfinish = () => {
      leavingRef.current = false;
      closeRef.current();
    };
  };
  const requestMinimize = () => {
    const el = shellRef.current;
    const chip = dockChip();
    const done = () => useDesk.getState().minimizePanel(id);
    if (!el || typeof el.animate !== "function" || reducedMotion || !chip) {
      done();
      return;
    }
    const anim = flyToChip(el, chip, false);
    anim.onfinish = () => {
      anim.cancel(); // release the forwards fill before display:none
      done();
    };
  };
  const prevMinRef = useRef(false);
  useEffect(() => {
    const was = prevMinRef.current;
    prevMinRef.current = minimized;
    if (!was || minimized) return;
    // Restore: the window returns from its dock chip.
    const el = shellRef.current;
    const chip = dockChip();
    if (el && typeof el.animate === "function" && !reducedMotion && chip)
      flyToChip(el, chip, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [minimized]);

  useEffect(() => {
    if (!open) return;
    announceWindow(id, name, glyph, () => requestClose());
    return () => retractWindow(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, id, name, glyph]);

  // HS-96-05 — window focus management (the ui-styling a11y pattern,
  // WITHOUT a modal trap: windows coexest is the law). Opening moves
  // focus into the window; closing returns it to the opener; Escape
  // anywhere inside closes this window.
  const openerRef = useRef<HTMLElement | null>(null);
  useEffect(() => {
    if (!open) return;
    openerRef.current =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    shellRef.current?.focus({ preventScroll: true });
    return () => {
      const opener = openerRef.current;
      if (opener && document.contains(opener))
        opener.focus({ preventScroll: true });
    };
  }, [open, id]);

  // Opening always PRESENTS the window. A stale in-session minimize
  // (window closed while parked, reopened later) would otherwise open it
  // invisibly parked — a stranded surface. Minimize is session-scoped by
  // design and never persisted (HS-97-03); rects/order/maximize persist.
  useEffect(() => {
    if (open && useDesk.getState().panelMin.includes(id))
      useDesk.getState().restorePanel(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, id]);

  if (!open) return null;
  if (minimized && unmountOnMinimize) return null;

  const maxed = maximized && !compact;
  const style: React.CSSProperties = {
    ...rootStyle,
    ...(compact
      ? { zIndex: (win.style.zIndex as number) ?? 42 }
      : maxed
        ? {
            top: "var(--desk-work-top)",
            left: MARGIN,
            right: MARGIN,
            bottom: "var(--desk-work-bottom)",
            width: "auto",
            height: "auto",
            maxHeight: "none",
            zIndex: win.style.zIndex,
          }
        : win.style),
    ...(minimized ? { display: "none" } : null),
  };

  return (
    <motion.div
      ref={(el: HTMLDivElement | null) => {
        win.setEl(el);
        shellRef.current = el;
        if (el) shellEls.set(id, el);
        else shellEls.delete(id);
      }}
      tabIndex={-1}
      onKeyDown={(e) => {
        if (e.key === "Escape" && !e.defaultPrevented) {
          e.stopPropagation();
          // HS-99-02 — an open head menu absorbs the first Escape; the
          // window only closes on the next one.
          if (headMenu) {
            setHeadMenu(null);
            return;
          }
          requestClose();
        }
      }}
      className={
        (className ? className + " " : "") +
        "desk-window desk-window-shell" +
        (win.floating ? " is-floating" : "") +
        (compact ? " is-sheet" : "") +
        (maxed ? " is-max" : "") +
        (isFront ? " is-front" : "")
      }
      style={style}
      // An origin window's entrance is the fly-out-of-the-object WAAPI
      // (pre-paint, in the placement effect) — never the side slide.
      initial={
        reducedMotion || !entrance || (origin && !compact)
          ? false
          : { x: 60, opacity: 0 }
      }
      animate={{ x: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 320, damping: 30 }}
      onPointerDown={(e) => {
        win.focus();
        e.stopPropagation();
      }}
      role="region"
      aria-label={name}
    >
      <header
        className={`desk-pullout-head desk-window-handle${wings ? " has-wings" : ""}`}
        {...(compact || maxed ? {} : win.handleProps)}
        onDoubleClick={(e) => {
          // HS-97-05 — double-click the head toggles maximize (buttons
          // inside the head keep their own clicks).
          if (compact) return;
          const t = e.target as HTMLElement | null;
          if (t?.closest("button, a, input, textarea, select")) return;
          useDesk.getState().toggleMaximizePanel(id);
        }}
        onContextMenu={(e) => {
          // HS-99-02 — the bar owns its window verbs on right-click.
          const t = e.target as HTMLElement | null;
          if (t?.closest("button, a, input, textarea, select")) return;
          e.preventDefault();
          setHeadMenu({ x: e.clientX, y: e.clientY });
        }}
      >
        <span className="desk-traffic">
          <button
            type="button"
            className="desk-light desk-light-close"
            aria-label={`Close ${name}`}
            onClick={requestClose}
          >
            <VerbGlyph kind="light-close" />
          </button>
          <button
            type="button"
            className="desk-light desk-light-min"
            aria-label={`Minimize ${name}`}
            onClick={requestMinimize}
          >
            <VerbGlyph kind="light-min" />
          </button>
          {!compact ? (
            <button
              type="button"
              className="desk-light desk-light-max"
              aria-label={maximized ? `Restore ${name}` : `Maximize ${name}`}
              onClick={() => useDesk.getState().toggleMaximizePanel(id)}
            >
              <VerbGlyph kind={maximized ? "light-restore" : "light-max"} />
            </button>
          ) : (
            <span aria-hidden="true" />
          )}
        </span>
        {leading}
        {icon}
        {/* HS-97-07 — the eyebrow is demoted: window identity is icon +
            title (Article VII.1); the prop survives for callers/AT. */}
        <span className="desk-pullout-title desk-window-title">{title}</span>
        {wings}
        {actions}
      </header>
      {headMenu ? (
        <DeskMenuList
          className="desk-head-menu"
          label={`${name} window menu`}
          anchor="below"
          style={{
            left: Math.min(headMenu.x, window.innerWidth - 184),
            top: Math.min(headMenu.y, window.innerHeight - 132),
          }}
          onClose={() => setHeadMenu(null)}
        >
          <DeskMenuItem
            glyph={<VerbGlyph kind="minimize" />}
            onSelect={() => {
              setHeadMenu(null);
              requestMinimize();
            }}
          >
            Minimize
          </DeskMenuItem>
          {!compact && (
            <DeskMenuItem
              glyph={<VerbGlyph kind={maximized ? "restore" : "maximize"} />}
              onSelect={() => {
                setHeadMenu(null);
                useDesk.getState().toggleMaximizePanel(id);
              }}
            >
              {maximized ? "Restore" : "Maximize"}
            </DeskMenuItem>
          )}
          <DeskMenuItem
            glyph={<VerbGlyph kind="close" />}
            onSelect={() => {
              setHeadMenu(null);
              requestClose();
            }}
          >
            Close
          </DeskMenuItem>
        </DeskMenuList>
      ) : null}
      {children}
      {!maxed && !compact ? win.grip : null}
      {!maxed && !compact ? win.edges : null}
    </motion.div>
  );
}
