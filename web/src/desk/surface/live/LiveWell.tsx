import { useLayoutEffect, useRef, type CSSProperties } from "react";
import "./live-well.css";
export type LiveLine = { id: string; text: string };
export type LiveWellProps = { lines: readonly LiveLine[]; show?: number; label: string; working?: boolean; "data-feedback-redact"?: "true" | "false" | boolean };
/** A content-sized tail of a producer's screen, never a terminal controller. */
export function LiveWell({ lines, show = 7, label, working = false, "data-feedback-redact": redact }: LiveWellProps) {
  const count = Number.isFinite(show) ? Math.max(1, Math.floor(show)) : 7;
  const seen = useRef(new Set(lines.map(line => line.id)));
  const visible = lines.slice(-count);
  useLayoutEffect(() => { seen.current = new Set(lines.map(line => line.id)); }, [lines]);
  return <div className="surface-live-well" role="log" aria-label={label} aria-live="off" data-working={working || undefined}
    data-feedback-redact={redact} style={{ "--live-well-lines": Math.max(2, visible.length), "--live-well-max-lines": count } as CSSProperties}>
    {visible.map((line, index) => <div key={line.id} className="surface-live-line" data-new={working && !seen.current.has(line.id) || undefined}
      data-cursor={working && index === visible.length - 1 || undefined} title={line.text}>{line.text || "\u00a0"}</div>)}
  </div>;
}
