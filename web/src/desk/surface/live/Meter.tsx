import { activity } from "./activity";
import "./meter.css";
export type MeterProps = { total: number; /** Zero-based; -1 before start, total when finished. */ current: number; state: string; label?: string };
export function Meter({ total, current, state, label }: MeterProps) {
  const count = Math.max(0, Math.floor(Number.isFinite(total) ? total : 0));
  const at = Math.max(-1, Math.min(count, Math.floor(Number.isFinite(current) ? current : -1)));
  const tone = activity(state), done = tone === "done" ? count : Math.max(0, at);
  const words = label ?? (done === count ? `${count} steps done` : at < 0 ? `${count} steps, not started` : `Step ${at + 1} of ${count}`);
  return <span className="surface-meter" role="img" aria-label={words} data-mode={count > 12 ? "bar" : "segments"} data-single={count === 1 || undefined}>
    {count > 12 ? <><i data-state="done" style={{ width: `${done / count * 100}%` }} />{at >= 0 && at < count && tone !== "done" ? <i data-state={tone} style={{ width: `${100 / count}%` }} /> : null}</>
      : Array.from({ length: count }, (_, i) => <i key={i} aria-hidden="true" data-state={i < done ? "done" : i === at ? tone : "planned"} />)}
  </span>;
}
