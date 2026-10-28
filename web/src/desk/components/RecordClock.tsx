// W7 (canvas 2026-10-28 (b), direction A "The ring and the clock"): the
// elapsed time of the meeting that records now, and the red clock pill that
// shows it above the Record tile (the RecordOrb at the desk, the Capture
// tile on the phone).
import { useEffect, useLayoutEffect, useState, type RefObject } from "react";
import { createPortal } from "react-dom";
import { useDesk } from "../store";
import { TickNumber } from "../surface/kit";

/** The clock pill's air above the Record tile (canvas 2026-10-28 (b)). */
const CLOCK_AIR = 13;
const CLOCK_AIR_PHONE = 12;

function elapsedText(startedAt: number): string {
  const s = Math.max(0, Math.floor((Date.now() - startedAt) / 1000));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

type ClockSpot = { left: number; bottom: number; shown: boolean };

/** The elapsed time of the meeting that records now ("12:04"), or "" when
 * nothing records or the hub gave no start time (never 0:00 by guess). */
export function useRecordingElapsed(
  /** A start the caller already knows (the Dock's live read); else the store's. */
  known?: number | null,
): string {
  const state = useDesk((s) => s.recording);
  const stored = useDesk((s) => s.recordingStartedAt);
  const startedAt = known !== undefined ? known : state === "recording" ? stored : null;
  const [elapsed, setElapsed] = useState("");
  useEffect(() => {
    if (startedAt == null || Number.isNaN(startedAt)) {
      setElapsed("");
      return;
    }
    setElapsed(elapsedText(startedAt));
    const t = window.setInterval(() => setElapsed(elapsedText(startedAt)), 1000);
    return () => window.clearInterval(t);
  }, [startedAt]);
  return elapsed;
}

/** W7 (canvas 2026-10-28 (b), direction A): the red clock pill above the
 * Record tile (the RecordOrb at the desk, the Capture tile on the phone)
 * while a meeting records. It sits outside the dock plate; the phone's plate
 * scrolls (it clips what rises above it), so the pill is drawn in the desk
 * root at the tile's place, read again when the dock scrolls or resizes and
 * when the window resizes. aria-hidden: the tile's aria-label says it. */
export function RecordClock({ target, startedAt }: {
  target: RefObject<HTMLElement | null>;
  /** The start the caller knows (ms); omitted, the store's recording start. */
  startedAt?: number | null;
}) {
  const elapsed = useRecordingElapsed(startedAt);
  const [clock, setClock] = useState<ClockSpot | null>(null);
  const showClock = elapsed !== "";

  useLayoutEffect(() => {
    if (!showClock) {
      setClock(null);
      return;
    }
    const place = () => {
      const tile = target.current;
      if (!tile) return;
      const r = tile.getBoundingClientRect();
      const dock = tile.closest(".desk-dock")?.getBoundingClientRect();
      const mid = r.left + r.width / 2;
      const phone = window.innerWidth <= 720;
      const next: ClockSpot = {
        left: Math.round(mid),
        bottom: Math.round(window.innerHeight - r.top + (phone ? CLOCK_AIR_PHONE : CLOCK_AIR)),
        // A tile scrolled out of the phone's plate has no clock over it.
        shown: !dock || (mid >= dock.left && mid <= dock.right),
      };
      setClock((was) => (was && was.left === next.left && was.bottom === next.bottom && was.shown === next.shown ? was : next));
    };
    place();
    const dock = target.current?.closest(".desk-dock");
    window.addEventListener("resize", place);
    dock?.addEventListener("scroll", place, { passive: true });
    const observer = typeof ResizeObserver === "function" && dock ? new ResizeObserver(place) : null;
    if (observer && dock) observer.observe(dock);
    return () => {
      window.removeEventListener("resize", place);
      dock?.removeEventListener("scroll", place);
      observer?.disconnect();
    };
  }, [showClock, target]);

  const host = showClock ? target.current?.closest(".desk-next") ?? document.body : null;
  if (!host || !clock?.shown) return null;
  return createPortal(
    <span
      className="desk-orb-clock"
      data-testid="desk-orb-clock"
      aria-hidden="true"
      style={{ left: clock.left, bottom: clock.bottom }}
    >
      <TickNumber value={elapsed} />
    </span>,
    host,
  );
}
