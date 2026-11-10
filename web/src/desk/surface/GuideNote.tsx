/** A guide belongs to its window. Its ring and note share an unclipped layer. */
import { useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { createPortal, flushSync } from "react-dom";
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

/** One trailing seat, bounded by the visible window content. */
export function guideSeat(
  window: GuideBox,
  part: GuideBox | null,
  note: { width: number; height: number },
  floor: number,
  visible = { left: 0, top: 36, width: window.width, height: floor - 36 },
) {
  const width = Math.min(note.width, visible.width - EDGE * 2);
  const left = visible.left + visible.width - width - EDGE;
  const bottom = Math.min(floor, visible.top + visible.height);
  const top = Math.max(visible.top + EDGE, bottom - note.height - EDGE);
  const intersects = part && part.left < left + width && part.left + part.width > left
    && part.top < top + note.height && part.top + part.height > top;
  return { left, top: intersects ? visible.top + EDGE : top, side: intersects ? "top" : "bottom", width };
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
  }>({ ring: null, seat: { left: 8, top: 36, side: "bottom", width: 360 } });
  useLayoutEffect(() => {
    let alive = true;
    const originalMinimum = owner.style.minHeight;
    if (owner.hasAttribute("data-guide-running")) owner.style.minHeight = `${Math.min(600, Math.max(220, innerHeight-owner.getBoundingClientRect().top-48))}px`;
    let queued = 0;
    let borrowed: {style: string | null; scroll: number} | null = null;
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
        box.height - 48, // Keep one seat even when the status line gains a second row.
        ...bars.map((el) => (el.getBoundingClientRect().top - win.top) / scale),
      );
      const head = owner.querySelector<HTMLElement>(":scope > .desk-pullout-head")?.getBoundingClientRect();
      const visible = {
        left: Math.max(0, -win.left / scale),
        top: Math.max(head ? (head.bottom - win.top) / scale : 36, -win.top / scale),
        width: Math.min(box.width, (innerWidth - win.left) / scale) - Math.max(0, -win.left / scale),
        height: 0,
      };
      visible.height = Math.min(floor, (innerHeight - win.top) / scale) - visible.top;
      const size = { width: box.width <= 480 ? visible.width - EDGE * 2 : 360, height: note.current.offsetHeight };
      const measurePart = () => {
        const part = target?.isConnected ? target.getBoundingClientRect() : null;
        return part ? {left: (part.left-win.left)/scale, top: (part.top-win.top)/scale, width: part.width/scale, height: part.height/scale} : null;
      };
      let ring = measurePart();
      // A tall list owns a smaller scroll well while help uses the foot.
      // Its style and original scroll position are returned on this step's cleanup.
      const bottomSeat = guideSeat(box, null, size, floor, visible);
      if (target && ring && target.matches('.object-list,[role="grid"],.surface-rail')
        && ring.top < visible.top + size.height + EDGE && ring.top + ring.height > bottomSeat.top) {
        if (!borrowed) borrowed = { style: target.getAttribute("style"), scroll: target.scrollTop };
        target.style.maxHeight = `${Math.max(88, bottomSeat.top - ring.top - GAP)}px`;
        target.style.minHeight = "0";
        target.style.overflowY = "auto";
        ring = measurePart();
      }
      let seat = guideSeat(box, ring, size, floor, visible);
      // On a phone, scroll only the target's well before using the top seat.
      if (target && ring && box.width <= 480 && seat.side === "top") {
        for (let el = target.parentElement; el && el !== owner; el = el.parentElement) {
          if (/auto|scroll/.test(getComputedStyle(el).overflowY) && el.scrollHeight > el.clientHeight) {
            el.scrollTop += Math.max(0, ring.top + ring.height - bottomSeat.top + GAP);
            break;
          }
        }
        ring = measurePart();
        seat = guideSeat(box, ring, size, floor, visible);
      }
      if (ring) {
        const left = Math.max(visible.left + 4, ring.left - 3), top = Math.max(visible.top, ring.top - 3);
        ring = {left, top,
          width: Math.max(0, Math.min(visible.left+visible.width-4, ring.left+ring.width+3)-left),
          height: Math.max(0, Math.min(floor-4, ring.top+ring.height+3)-top)};
        // Include the ring's edge, not only the part's content, in the overlap law.
        seat = guideSeat(box, ring, size, floor, visible);
      }
      const value = { ring, seat };
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
      typeof ResizeObserver === "function" ? new ResizeObserver(() => flushSync(place)) : null;
    observer?.observe(owner);
    if (note.current) observer?.observe(note.current);
    if (target) observer?.observe(target);
    const mutation = typeof MutationObserver === "function" ? new MutationObserver(() => flushSync(place)) : null;
    if (note.current) mutation?.observe(note.current, {childList: true, subtree: true, characterData: true});
    owner.addEventListener("scroll", queue, true);
    window.addEventListener("resize", queue);
    return () => {
      alive = false;
      owner.style.minHeight = originalMinimum;
      cancelAnimationFrame(queued);
      observer?.disconnect();
      mutation?.disconnect();
      if (target && borrowed) {
        if (borrowed.style === null) target.removeAttribute("style");
        else target.setAttribute("style", borrowed.style);
        target.scrollTop = borrowed.scroll;
      }
      owner.removeEventListener("scroll", queue, true);
      window.removeEventListener("resize", queue);
    };
  }, [owner, target, words, count, children, actions]);
  useLayoutEffect(() => {
    if (focusNext && !busy) next.current?.focus({ preventScroll: true });
  }, [target, words, focusNext, busy]);
  const { ring, seat } = geometry;
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
        </>
      ) : null}
      <aside
        ref={note}
        className="guide-note"
        data-testid="guide-note"
        data-side={seat.side}
        style={{ left: seat.left, top: seat.top, width: seat.width }}
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
                className="guide-next"
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
