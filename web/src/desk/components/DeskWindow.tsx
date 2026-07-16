// The desk-window contract (Phase 93 UI remediation): floating desk panels
// are windows, not fixtures. One hook gives a panel drag (by its head),
// resize (by a corner grip), focus-to-front, and a persisted rect — reusing
// the exact machinery desk objects already trust: @use-gesture pointer drags
// with a tap threshold, and a localStorage-backed rect map in the store
// (`hs.desk.panels`, the panel sibling of `hs.diorama.pos`). A panel the
// user never arranged keeps its CSS default corner, so the desk looks
// unchanged until someone reaches for a window.
import { useEffect, useRef } from "react";
import { useDrag } from "@use-gesture/react";
import { useDesk, type PanelRect } from "../store";

/** Viewport margin windows are clamped inside. */
const MARGIN = 10;
/** Minimum visible head strip so a window can always be grabbed back. */
const GRAB = 72;
/** The desk-window z band (see the ladder note in desk.css). */
const Z_BASE = 42;
/** Cascade step when several default-corner windows are open at once. */
const CASCADE = 26;

/** Windows currently mounted at their CSS default corner (no rect yet). */
const defaultCorner = new Set<string>();

function clampRect(r: PanelRect, minW: number, minH: number): PanelRect {
  const vw = window.innerWidth || 1280;
  const vh = window.innerHeight || 800;
  let w = Math.min(Math.max(r.w, minW), vw - MARGIN * 2);
  let h = Math.min(Math.max(r.h, minH), vh - MARGIN * 2);
  const x = Math.min(Math.max(r.x, MARGIN - w + GRAB), vw - GRAB);
  const y = Math.min(Math.max(r.y, MARGIN), vh - 48);
  // Keep the resize grip reachable: a window dragged toward an edge
  // shrinks to fit the viewport (floored at its minimum) rather than
  // sliding its bottom-right corner off-screen.
  w = Math.max(minW, Math.min(w, vw - MARGIN - x));
  h = Math.max(minH, Math.min(h, vh - MARGIN - y));
  return { x, y, w, h };
}

export interface DeskWindowOptions {
  minW?: number;
  minH?: number;
  /** Pass false while the panel renders nothing (launcher-only mounts). */
  open?: boolean;
}

/** Adopt the desk-window contract. Spread `handleProps` on the panel's head
 * (it becomes the drag handle), call `setEl` from the root's ref, apply
 * `style`/`floating` to the root, call `focus` on pointer-down, and render
 * `grip` as the root's last child. */
export function useDeskWindow(id: string, opts: DeskWindowOptions = {}) {
  const minW = opts.minW ?? 320;
  const minH = opts.minH ?? 220;
  const open = opts.open ?? true;
  const rect = useDesk((s) => s.panelRects[id]);
  const orderIndex = useDesk((s) => s.panelOrder.indexOf(id));
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

  // Cascade: a second window opening onto the same default corner steps
  // down-left so windows never pile up pixel-for-pixel (UX-01/02).
  useEffect(() => {
    if (!open) return;
    useDesk.getState().focusPanel(id);
    if (useDesk.getState().panelRects[id]) return;
    const behind = defaultCorner.size;
    defaultCorner.add(id);
    if (behind > 0) {
      const base = measure();
      useDesk.getState().setPanelRect(
        id,
        clampRect(
          {
            ...base,
            x: base.x - CASCADE * behind,
            y: base.y + CASCADE * behind,
            h: Math.max(minH, base.h - CASCADE * behind * 2),
          },
          minW,
          minH,
        ),
      );
    }
    return () => {
      defaultCorner.delete(id);
      // An unarranged (never persisted) rect is ephemeral: forget it so the
      // panel comes back at its default corner next time.
      const s = useDesk.getState();
      if (!s.panelSaved.includes(id) && s.panelRects[id]) s.resetPanelRect(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, open]);

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
        useDesk
          .getState()
          .setPanelRect(
            id,
            clampRect({ ...base, x: base.x + mx, y: base.y + my }, minW, minH),
            last,
          );
      }
      return { base, skip: false };
    },
    { pointer: { buttons: 1 } },
  );

  const resizeBind = useDrag(
    ({ movement: [mx, my], last, memo }) => {
      const base: PanelRect = memo?.base ?? measure();
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

  const style: React.CSSProperties = rect
    ? {
        top: rect.y,
        left: rect.x,
        width: rect.w,
        height: rect.h,
        right: "auto",
        bottom: "auto",
        maxHeight: "none",
        zIndex: Z_BASE + Math.max(orderIndex, 0),
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
  };
}
