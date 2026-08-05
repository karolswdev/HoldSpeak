// Expose overlay — fans open windows into a pick grid.
// Extracted from DeskWindow.tsx (HS-117-04).
import { useEffect, useRef } from "react";
import { useSyncExternalStore } from "react";
import { useReducedMotion } from "motion/react";
import { useDesk } from "../../store";
import { exposeLayout } from "./windowGeometry";
import { useOpenWindows, shellEls } from "./windowRegistry";

/** HS-97-06 — expose state (module-level so the dock verb and the
 * keyboard share one truth). */
let exposeActive = false;
const exposeListeners = new Set<() => void>();

export function toggleExpose(force?: boolean) {
  const next = force ?? !exposeActive;
  if (next === exposeActive) return;
  exposeActive = next;
  for (const l of exposeListeners) l();
}

/** The expose (HS-97-06): fans every open window into a pick grid --
 * live shells scale into their cells (compositor transforms), minimized
 * windows join as dimmed cards; click or Enter focuses, Escape cancels. */
export function Expose() {
  const active = useSyncExternalStore(
    (cb) => {
      exposeListeners.add(cb);
      return () => exposeListeners.delete(cb);
    },
    () => exposeActive,
  );
  const windows = useOpenWindows();
  const panelMin = useDesk((s) => s.panelMin);
  const reducedMotion = useReducedMotion();
  const firstBtnRef = useRef<HTMLButtonElement | null>(null);
  const fannedRef = useRef<
    { el: HTMLElement; anim: Animation }[]
  >([]);

  useEffect(() => {
    // Ctrl+Up itself now arrives through desk/keymap.ts (the one binder,
    // registry verb desk.overview); the expose keeps only its Escape.
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && exposeActive) {
        e.preventDefault();
        toggleExpose(false);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  const entries = windows.map((w) => ({
    ...w,
    minimized: panelMin.includes(w.id),
  }));
  const vw = typeof window === "undefined" ? 1280 : window.innerWidth || 1280;
  const vh = typeof window === "undefined" ? 800 : window.innerHeight || 800;
  const cells = exposeLayout(Math.max(entries.length, 1), vw, vh);

  useEffect(() => {
    if (!active) return;
    const fanned: { el: HTMLElement; anim: Animation }[] = [];
    entries.forEach((en, i) => {
      if (en.minimized) return;
      const el = shellEls.get(en.id);
      if (!el || typeof el.animate !== "function") return;
      const r = el.getBoundingClientRect();
      if (!r.width) return;
      const cell = cells[i];
      const s = Math.min(cell.w / r.width, cell.h / r.height, 1);
      const dx = cell.x + cell.w / 2 - (r.x + r.width / 2);
      const dy = cell.y + cell.h / 2 - (r.y + r.height / 2);
      const anim = el.animate(
        [
          { transform: "translate(0, 0) scale(1)" },
          { transform: `translate(${dx}px, ${dy}px) scale(${s})` },
        ],
        {
          duration: reducedMotion ? 0 : 220,
          easing: "cubic-bezier(.2, .8, .2, 1)",
          fill: "forwards",
        },
      );
      fanned.push({ el, anim });
    });
    fannedRef.current = fanned;
    firstBtnRef.current?.focus();
    return () => {
      for (const { el, anim } of fannedRef.current) {
        try {
          const current = getComputedStyle(el).transform;
          anim.cancel();
          if (!reducedMotion && current && current !== "none")
            el.animate(
              [{ transform: current }, { transform: "none" }],
              { duration: 180, easing: "cubic-bezier(.2, .8, .2, 1)" },
            );
        } catch {
          /* jsdom or torn-down element: nothing to unwind */
        }
      }
      fannedRef.current = [];
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  if (!active || entries.length === 0) return null;
  return (
    <>
      <div className="desk-expose-scrim" aria-hidden="true" />
      <div
        className="desk-expose"
        // A region, not a dialog: the desk's no-modal law holds -- no
        // trap, Escape and the backdrop dismiss (Phase 73 lock).
        role="group"
        aria-label="Window overview"
        onClick={(e) => {
          if (e.target === e.currentTarget) toggleExpose(false);
        }}
      >
        {entries.map((en, i) => (
          <button
            key={en.id}
            type="button"
            ref={i === 0 ? firstBtnRef : undefined}
            className={"desk-expose-cell" + (en.minimized ? " is-min" : "")}
            style={{
              top: cells[i].y,
              left: cells[i].x,
              width: cells[i].w,
              height: cells[i].h,
            }}
            aria-label={`Focus ${en.label}`}
            onClick={() => {
              toggleExpose(false);
              const s = useDesk.getState();
              if (s.panelMin.includes(en.id)) s.restorePanel(en.id);
              else s.focusPanel(en.id);
            }}
          >
            <span className="desk-expose-name">
              <span aria-hidden="true">{en.glyph}</span> {en.label}
            </span>
          </button>
        ))}
      </div>
    </>
  );
}
