/** A guide belongs to its window. Its ring and note share an unclipped layer. */
import { useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { Button } from "../../components/signal/Signal";
import "./GuideNote.css";

export interface GuideBox {
  left: number;
  top: number;
  width: number;
  height: number;
}
const GAP = 12;
const EDGE = 8;

/** Pick a free side, keeping both the note and its target inside the window. */
export function guideSeat(
  window: GuideBox,
  part: GuideBox | null,
  note: { width: number; height: number },
  floor: number,
) {
  const width = Math.min(note.width, window.width - EDGE * 2);
  const clampX = (x: number) =>
    Math.max(EDGE, Math.min(x, window.width - width - EDGE));
  const clampY = (y: number) =>
    Math.max(36, Math.min(y, floor - note.height - EDGE));
  if (window.width <= 480 || !part)
    return {
      left: clampX(window.width - width - EDGE),
      top: clampY(floor - note.height - EDGE),
      side: "dock",
    };
  const sides = [
    {
      left: clampX(part.left + part.width - width),
      top: part.top + part.height + GAP,
      side: "below",
    },
    {
      left: clampX(part.left + part.width - width),
      top: part.top - note.height - GAP,
      side: "above",
    },
    {
      left: part.left + part.width + GAP,
      top: clampY(part.top),
      side: "right",
    },
    { left: part.left - width - GAP, top: clampY(part.top), side: "left" },
  ];
  return (
    sides.find(
      (s) =>
        s.left >= EDGE &&
        s.top >= 36 &&
        s.left + width <= window.width - EDGE &&
        s.top + note.height <= floor - EDGE,
    ) ?? {
      left: clampX(window.width - width - EDGE),
      top: clampY(floor - note.height - EDGE),
      side: "dock",
    }
  );
}

export interface GuideNoteProps {
  owner: HTMLElement;
  target?: HTMLElement | null;
  words: string;
  count?: string;
  last?: boolean;
  onStop(): void;
  onNext?: () => void;
  onFeedback?: () => void;
  children?: ReactNode;
  /** Capture or link-answer controls replace the guide's completion row. */
  actions?: ReactNode;
  busy?: boolean;
  focusNext?: boolean;
}

export function GuideNote({
  owner,
  target,
  words,
  count,
  last,
  onStop,
  onNext,
  onFeedback,
  children,
  actions,
  busy,
  focusNext = true,
}: GuideNoteProps) {
  const note = useRef<HTMLElement>(null);
  const next = useRef<HTMLButtonElement>(null);
  const [geometry, setGeometry] = useState<{
    ring: GuideBox | null;
    seat: ReturnType<typeof guideSeat>;
    tail: number;
  }>({ ring: null, seat: { left: 8, top: 36, side: "dock" }, tail: 20 });
  useLayoutEffect(() => {
    let alive = true;
    let queued = 0;
    const place = () => {
      if (!alive || !note.current) return;
      const win = owner.getBoundingClientRect();
      const scale =
        win.width > 0 ? win.width / (owner.offsetWidth || win.width) : 1;
      const box = {
        left: 0,
        top: 0,
        width: win.width / scale,
        height: win.height / scale,
      };
      const bars = [
        ...owner.querySelectorAll<HTMLElement>(".kit-statusbar"),
      ].filter((el) => el.getBoundingClientRect().height > 0);
      const floor = Math.min(
        box.height,
        ...bars.map((el) => (el.getBoundingClientRect().top - win.top) / scale),
      );
      const part = target?.isConnected ? target.getBoundingClientRect() : null;
      let ring = part
        ? {
            left: (part.left - win.left) / scale,
            top: (part.top - win.top) / scale,
            width: part.width / scale,
            height: part.height / scale,
          }
        : null;
      const size = {
        width: note.current.offsetWidth,
        height: note.current.offsetHeight,
      };
      let seat = guideSeat(box, ring, size, floor);
      // A docked note reserves the bottom of the window. Scroll the well,
      // never the page, until the selected part is above that reservation.
      if (
        target &&
        ring &&
        seat.side === "dock" &&
        ring.top + ring.height > seat.top - GAP
      ) {
        for (
          let el = target.parentElement;
          el && el !== owner;
          el = el.parentElement
        ) {
          if (
            /auto|scroll/.test(getComputedStyle(el).overflowY) &&
            el.scrollHeight > el.clientHeight
          ) {
            el.scrollTop += ring.top + ring.height - seat.top + GAP;
            break;
          }
        }
        const moved = target.getBoundingClientRect();
        ring = {
          left: (moved.left - win.left) / scale,
          top: (moved.top - win.top) / scale,
          width: moved.width / scale,
          height: moved.height / scale,
        };
      }
      if (ring) {
        // Ring is on this layer, not a child of the well. Keep its four
        // edges inside the window even for an edge-to-edge toolbar.
        const left = Math.max(4, ring.left - 3),
          top = Math.max(34, ring.top - 3);
        ring = {
          left,
          top,
          width: Math.max(
            0,
            Math.min(box.width - 4, ring.left + ring.width + 3) - left,
          ),
          height: Math.max(
            0,
            Math.min(floor - 4, ring.top + ring.height + 3) - top,
          ),
        };
      }
      const tail = ring
        ? Math.max(
            16,
            Math.min(
              size.width - 16,
              ring.left + Math.min(ring.width / 2, 120) - seat.left,
            ),
          )
        : 20;
      const value = { ring, seat, tail };
      setGeometry((old) =>
        JSON.stringify(old) === JSON.stringify(value) ? old : value,
      );
    };
    const queue = () => {
      cancelAnimationFrame(queued);
      queued = requestAnimationFrame(place);
    };
    place();
    const observer =
      typeof ResizeObserver === "function" ? new ResizeObserver(queue) : null;
    observer?.observe(owner);
    if (note.current) observer?.observe(note.current);
    if (target) observer?.observe(target);
    owner.addEventListener("scroll", queue, true);
    window.addEventListener("resize", queue);
    return () => {
      alive = false;
      cancelAnimationFrame(queued);
      observer?.disconnect();
      owner.removeEventListener("scroll", queue, true);
      window.removeEventListener("resize", queue);
    };
  }, [owner, target, words, count, children, actions]);
  useLayoutEffect(() => {
    if (focusNext && !busy) next.current?.focus({ preventScroll: true });
  }, [target, words, focusNext, busy]);
  const { ring, seat, tail } = geometry;
  return createPortal(
    <div className="guide-layer" data-guide-layer data-testid="guide-layer">
      {ring && ring.width > 0 && ring.height > 0 ? (
        <>
          <div
            className="guide-ring"
            data-testid="guide-ring"
            style={ring}
            aria-hidden="true"
          />
          <span
            className="guide-pointer"
            style={{
              left: ring.left + Math.min(ring.width / 2, 120),
              top: ring.top + ring.height / 2,
            }}
            aria-hidden="true"
          >
            ↖
          </span>
        </>
      ) : null}
      <aside
        ref={note}
        className="guide-note"
        data-testid="guide-note"
        data-side={seat.side}
        style={
          {
            left: seat.left,
            top: seat.top,
            "--guide-tail": `${tail}px`,
          } as React.CSSProperties
        }
        aria-label="Guide"
      >
        {words ? (
          <p
            className="guide-words"
            data-testid="walk-caption"
            aria-live="polite"
          >
            {words}
          </p>
        ) : null}
        {children}
        {actions ?? (
          <div className="guide-bar">
            <span className="guide-count" data-testid="walk-count">
              {count}
            </span>
            {onFeedback ? (
              <Button
                dense
                variant="secondary"
                disabled={busy}
                onClick={onFeedback}
                data-testid="guide-feedback"
              >
                Say what is off
              </Button>
            ) : null}
            <Button
              dense
              variant="secondary"
              disabled={busy}
              onClick={onStop}
              data-testid="walk-stop"
            >
              Stop
            </Button>
            {onNext ? (
              <Button
                ref={next}
                dense
                variant="primary"
                disabled={busy}
                onClick={onNext}
                data-testid="walk-next"
              >
                {last ? "Done" : "Next"}
              </Button>
            ) : null}
          </div>
        )}
      </aside>
    </div>,
    owner,
  );
}
