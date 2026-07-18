// The desk-window contract (Phase 93 UI remediation; HS-95-02 makes it an
// OS): floating desk panels are windows, not fixtures. The `useDeskWindow`
// hook below carries the physics — drag (by the head), resize (corner
// grip), focus-to-front, persisted rect — and `DeskWindowFrame` is the ONE
// container every window renders through: one chrome (icon · title ·
// actions · minimize/maximize/close), a children content slot, lifecycle
// state in the store (`panelMin`/`panelMax`, persisted in the same
// `hs.desk.panels` slot as the rects), and the phone's bottom-sheet form.
// The hook is module-private on purpose: windows do not hand-wire physics.
import {
  useEffect,
  useRef,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { motion, useReducedMotion } from "motion/react";
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

/** The desk-window physics (Phase 93). Module-private since HS-95-02:
 * every window adopts it through `DeskWindowFrame`, never by hand. */
function useDeskWindow(id: string, opts: DeskWindowOptions = {}) {
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

/** Open windows announce themselves (title/icon) so the minimized tray —
 * and HS-95-03's dock — can name them without a parallel registry. */
const windowRegistry = new Map<string, { label: string; glyph: string }>();
const registryListeners = new Set<() => void>();
let registrySnapshot: { id: string; label: string; glyph: string }[] = [];

function announceWindow(id: string, label: string, glyph: string) {
  windowRegistry.set(id, { label, glyph });
  publishRegistry();
}

function retractWindow(id: string) {
  windowRegistry.delete(id);
  publishRegistry();
}

function publishRegistry() {
  registrySnapshot = Array.from(windowRegistry.entries()).map(
    ([id, v]) => ({ id, ...v }),
  );
  for (const l of registryListeners) l();
}

export function useOpenWindows() {
  return useSyncExternalStore(
    (cb) => {
      registryListeners.add(cb);
      return () => registryListeners.delete(cb);
    },
    () => registrySnapshot,
  );
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
  /** Content before the icon (e.g. a back chip). */
  leading?: ReactNode;
  /** One-word kind eyebrow above/beside the title (optional). */
  eyebrow?: string;
  /** Extra head content (badges, panel-specific verbs), left of the window verbs. */
  actions?: ReactNode;
  /** Root classes — keep the panel's legacy class so its content CSS holds. */
  className?: string;
  minW?: number;
  minH?: number;
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
    leading,
    eyebrow,
    actions,
    className,
    minW,
    minH,
    open,
    onClose,
    unmountOnMinimize,
    entrance = true,
    rootStyle,
    children,
  } = props;
  const minimized = useDesk((s) => s.panelMin.includes(id));
  const maximized = useDesk((s) => s.panelMax.includes(id));
  const compact = useCompactViewport();
  const reducedMotion = useReducedMotion();
  const win = useDeskWindow(id, { minW, minH, open: open && !minimized });
  const glyph = typeof icon === "string" ? icon : "▢";
  const name = label ?? (typeof title === "string" ? title : id);

  useEffect(() => {
    if (!open) return;
    announceWindow(id, name, glyph);
    return () => retractWindow(id);
  }, [open, id, name, glyph]);

  // Opening always PRESENTS the window. A stale minimize (e.g. persisted
  // from a prior session whose feature-open state reset on reload) would
  // otherwise open the window invisibly parked — a stranded surface.
  // Minimize is session-scoped by design; rects and maximize persist.
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
            top: 54,
            left: 10,
            right: 10,
            bottom: 10,
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
      ref={(el: HTMLDivElement | null) => win.setEl(el)}
      className={
        (className ? className + " " : "") +
        "desk-window desk-window-shell" +
        (win.floating ? " is-floating" : "") +
        (compact ? " is-sheet" : "") +
        (maxed ? " is-max" : "")
      }
      style={style}
      initial={reducedMotion || !entrance ? false : { x: 60, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 320, damping: 30 }}
      onPointerDown={(e) => {
        win.focus();
        e.stopPropagation();
      }}
      role="dialog"
      aria-modal={false}
      aria-label={name}
    >
      <header
        className="desk-pullout-head desk-window-handle"
        {...(compact || maxed ? {} : win.handleProps)}
      >
        {leading}
        {icon}
        {eyebrow ? <span className="desk-panel-eyebrow">{eyebrow}</span> : null}
        <span className="desk-pullout-title desk-window-title">{title}</span>
        {actions}
        <span className="desk-window-verbs">
          <button
            type="button"
            className="desk-window-verb"
            aria-label={`Minimize ${name}`}
            onClick={() => useDesk.getState().minimizePanel(id)}
          >
            –
          </button>
          {!compact && (
            <button
              type="button"
              className="desk-window-verb"
              aria-label={maximized ? `Restore ${name}` : `Maximize ${name}`}
              onClick={() => useDesk.getState().toggleMaximizePanel(id)}
            >
              {maximized ? "❐" : "⤢"}
            </button>
          )}
          <button
            type="button"
            className="desk-window-verb desk-window-close"
            aria-label={`Close ${name}`}
            onClick={onClose}
          >
            ✕
          </button>
        </span>
      </header>
      {children}
      {!maxed && !compact ? win.grip : null}
    </motion.div>
  );
}

/** The parked-windows tray: every minimized window as a restorable chip.
 * HS-95-03's dock absorbs this; until then nothing minimized is stranded. */
export function MinimizedTray() {
  const panelMin = useDesk((s) => s.panelMin);
  const windows = useOpenWindows();
  const chips = windows.filter((w) => panelMin.includes(w.id));
  if (chips.length === 0) return null;
  return (
    <div className="desk-min-tray" role="toolbar" aria-label="Minimized windows">
      {chips.map((c) => (
        <button
          key={c.id}
          type="button"
          className="desk-chip desk-min-chip"
          onClick={() => useDesk.getState().restorePanel(c.id)}
        >
          <span aria-hidden="true">{c.glyph}</span> {c.label}
        </button>
      ))}
    </div>
  );
}
