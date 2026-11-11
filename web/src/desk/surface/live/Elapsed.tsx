import { useEffect, useRef, useState, type HTMLAttributes } from "react";
import "./elapsed.css";

// One clock for every visible subscriber. No row owns an interval.
const listeners = new Set<(now: number) => void>();
let timer: ReturnType<typeof setInterval> | undefined;
function updateClock() {
  if (document.hidden || !listeners.size) { clearInterval(timer); timer = undefined; }
  else if (timer === undefined) timer = setInterval(() => { for (const notify of listeners) notify(Date.now()); }, 1000);
  if (!document.hidden) for (const notify of listeners) notify(Date.now());
}
function subscribe(notify: (now: number) => void) {
  if (!listeners.size) document.addEventListener("visibilitychange", updateClock);
  listeners.add(notify); updateClock();
  return () => {
    listeners.delete(notify); updateClock();
    if (!listeners.size) document.removeEventListener("visibilitychange", updateClock);
  };
}
export type ElapsedProps = Omit<HTMLAttributes<HTMLSpanElement>, "children"> & {
  /** Epoch milliseconds or an ISO date. */ start: number | string;
  /** Stop at the acknowledged finish time. */ end?: number | string;
  running?: boolean;
};
export function Elapsed({ start, end, running = true, hidden, className = "", ...props }: ElapsedProps) {
  const ref = useRef<HTMLSpanElement>(null), [visible, setVisible] = useState(true), [now, setNow] = useState(Date.now);
  useEffect(() => {
    const node = ref.current;
    if (!node || typeof IntersectionObserver === "undefined") return;
    const observer = new IntersectionObserver(entries => { for (const entry of entries) if (entry.target === node) setVisible(entry.isIntersecting); });
    observer.observe(node); return () => observer.disconnect();
  }, []);
  useEffect(() => { if (running && end === undefined && !hidden && visible) return subscribe(setNow); }, [running, end, hidden, visible]);
  const since = typeof start === "number" ? start : Date.parse(start);
  const until = end === undefined ? now : typeof end === "number" ? end : Date.parse(end);
  const seconds = Number.isFinite(since) && Number.isFinite(until) ? Math.max(0, Math.floor((until - since) / 1000)) : null;
  const words = seconds === null ? "—" : `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
  return <span {...props} ref={ref} hidden={hidden} className={`surface-elapsed ${className}`} aria-live="off">{words}</span>;
}
