import type { HTMLAttributes } from "react";
import "./lamp.css";
export type LampState = "working" | "waiting" | "done" | "failed" | "tonight" | "off";
export type LampProps = Omit<HTMLAttributes<HTMLSpanElement>, "children"> & { state: LampState; label: string };
/** A mark beside a visible state word, never a replacement for that word. */
export function Lamp({ state, label, className = "", ...props }: LampProps) {
  return <span {...props} className={`surface-lamp ${className}`} data-state={state} role="img" aria-label={label} />;
}
