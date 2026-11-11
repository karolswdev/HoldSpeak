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
/** The note owns the bottom band; pane content ends at its top. */
export function guideSeat(
  window: GuideBox,
  _part: GuideBox | null,
  note: { width: number; height: number },
  floor: number,
  visible = { left: 0, top: 36, width: window.width, height: floor - 36 },
) {
  return {
    left: visible.left,
    top: Math.max(visible.top, Math.min(floor, visible.top + visible.height) - note.height),
    width: visible.width,
    side: "bottom",
  };
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
  /** Capture lends more of the seat to the words field and its completion row. */
  capture?: boolean;
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
  capture = false,
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
    if (owner.hasAttribute("data-guide-running"))
      owner.style.minHeight = `${Math.min(600, Math.max(220, innerHeight - owner.getBoundingClientRect().top - 48))}px`;
    const originalHeight = owner.style.height;
    // A content-sized frame must not grow by its new padding. Hold its
    // current outside size while its body lends height to the note.
    const heldHeight = owner.dataset.fitContent === "true" && (!originalHeight || originalHeight === "auto")
      ? `${owner.offsetHeight}px` : null;
    if (heldHeight) owner.style.height = heldHeight;
    const originalSeat = owner.style.getPropertyValue("--guide-seat-height");
    const hadSeat = owner.hasAttribute("data-guide-seat");
    owner.setAttribute("data-guide-seat", "");
    let queued = 0;
    const place = () => {
      if (!alive || !note.current) return;
      const win = owner.getBoundingClientRect();
      const scale =
        win.width > 0 ? win.width / (owner.offsetWidth || win.width) : 1;
      const origin = {left: win.left + owner.clientLeft * scale, top: win.top + owner.clientTop * scale};
      const box = {
        left: 0,
        top: 0,
        width: owner.clientWidth,
        height: owner.clientHeight,
      };
      const head = owner.querySelector<HTMLElement>(":scope > .desk-pullout-head")?.getBoundingClientRect();
      const visible = {
        left: Math.max(0, -origin.left / scale),
        top: Math.max(head ? (head.bottom - origin.top) / scale : 36, -origin.top / scale),
        width: Math.min(box.width, (innerWidth - origin.left) / scale) - Math.max(0, -origin.left / scale),
        height: 0,
      };
      const floor = Math.min(box.height, (innerHeight - origin.top) / scale);
      visible.height = floor - visible.top;
      // Set width before measuring: wrapping and capture growth determine the
      // band the frame gives back. No app body or list gets a special rule.
      note.current.style.width = `${visible.width}px`;
      const height = note.current.getBoundingClientRect().height / scale;
      const reserve = `${Math.max(0, box.height - floor) + height}px`;
      if (owner.style.getPropertyValue("--guide-seat-height") !== reserve)
        owner.style.setProperty("--guide-seat-height", reserve);
      const seat = guideSeat(box, null, { width: visible.width, height }, floor, visible);
      // Reflow first, then reveal the part in its own scroll well. Never
      // scroll the window, the desk or an unrelated pane.
      const marked = target?.matches('input[type="checkbox"],input[type="radio"]')
        ? target.closest(".gadget-check")?.querySelector<HTMLElement>(".gadget-check-well") ?? target
        : target;
      if (marked?.isConnected && !note.current.contains(marked)) {
        for (let el = marked.parentElement; el && el !== owner; el = el.parentElement) {
          if (!/auto|scroll/.test(getComputedStyle(el).overflowY) || el.scrollHeight <= el.clientHeight) continue;
          const part = marked.getBoundingClientRect(), well = el.getBoundingClientRect();
          const bottom = Math.min(well.bottom, origin.top + seat.top * scale);
          if (part.bottom > bottom) el.scrollTop += Math.min(part.bottom - bottom, part.top - well.top);
          else if (part.top < well.top) el.scrollTop += part.top - well.top;
        }
      }
      const part = marked?.isConnected ? marked.getBoundingClientRect() : null;
      let ring: GuideBox | null = null;
      if (part) {
        let left = Math.max(visible.left, (part.left - origin.left) / scale);
        let top = Math.max(visible.top, (part.top - origin.top) / scale);
        let right = Math.min(visible.left + visible.width, (part.right - origin.left) / scale);
        let bottom = Math.min(seat.top, (part.bottom - origin.top) / scale);
        for (let el = marked!.parentElement; el && el !== owner; el = el.parentElement) {
          const style = getComputedStyle(el), well = el.getBoundingClientRect();
          if (/auto|scroll|hidden|clip/.test(style.overflowY)) {
            top = Math.max(top, (well.top - origin.top) / scale);
            bottom = Math.min(bottom, (well.bottom - origin.top) / scale);
          }
          if (/auto|scroll|hidden|clip/.test(style.overflowX)) {
            left = Math.max(left, (well.left - origin.left) / scale);
            right = Math.min(right, (well.right - origin.left) / scale);
          }
        }
        // An inset stroke hugs the marked control, including a small checkbox.
        ring = { left, top, width: Math.max(0, right - left), height: Math.max(0, bottom - top) };
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
      if (heldHeight && owner.style.height === heldHeight) owner.style.height = originalHeight;
      if (originalSeat) owner.style.setProperty("--guide-seat-height", originalSeat);
      else owner.style.removeProperty("--guide-seat-height");
      if (!hadSeat) owner.removeAttribute("data-guide-seat");
      cancelAnimationFrame(queued);
      observer?.disconnect();
      mutation?.disconnect();
      owner.removeEventListener("scroll", queue, true);
      window.removeEventListener("resize", queue);
    };
  }, [owner, target]);
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
        data-capture={capture || undefined}
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
