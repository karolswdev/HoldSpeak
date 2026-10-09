// Exposé — every shown window as a live plate (PHILO-16 §5; HS-97-06 before).
//
// The plates are the windows themselves: the compositor draws each window's
// own element at its own size, scaled by `--k` into its grid cell (it
// scales, it never reflows), with its own title bar (§7: no extra label).
// This overlay adds only the scrim and one pick target per plate: a press or
// Enter picks that window; Esc (the compositor) returns every window to its
// remembered rect.
import { useEffect, useRef } from "react";
import { useAllOpenWindows } from "./windowRegistry";
import { Button } from "../../../components/signal/Signal";
import {
  exposePick,
  toggleExposeMode,
  usePresentation,
} from "../../compositor/useCompositor";
import { plateVisual } from "../../compositor/geometry";

/** The Overview verb, the Dock's button and ⌘⇧E (⌃↑) reach this one toggle. */
export function toggleExpose(force?: boolean) {
  toggleExposeMode(force);
}

export function Expose() {
  const presentation = usePresentation();
  const windows = useAllOpenWindows();
  const firstBtnRef = useRef<HTMLButtonElement | null>(null);
  const active = presentation.mode === "expose";

  useEffect(() => {
    if (active) firstBtnRef.current?.focus({ preventScroll: true });
  }, [active]);

  if (!active) return null;
  const entries = windows.filter((w) => presentation.plates[w.id]);
  if (entries.length === 0) return null;
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
        {entries.map((en, i) => {
          const plate = presentation.plates[en.id];
          const v = plateVisual(plate.rect, plate.k ?? 1);
          return (
            <Button
              variant="chrome"
              key={en.id}
              ref={i === 0 ? firstBtnRef : undefined}
              className="desk-expose-cell is-plate"
              style={{ top: v.y, left: v.x, width: v.w, height: v.h }}
              aria-label={`Focus ${en.label}`}
              title={en.label}
              onClick={() => exposePick(en.id)}
            >
              <span className="sr-only">{en.label}</span>
            </Button>
          );
        })}
      </div>
    </>
  );
}
