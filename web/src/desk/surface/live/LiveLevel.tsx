import type { ReactNode } from "react";
import { LedMeter } from "../gadgets";
import "./live-level.css";

/** The producer's 0..1 audio level. No invented waveform or idle motion. */
export function LiveLevel({ level, label, expanded = false, children }: { level: number; label: string; expanded?: boolean; children?: ReactNode }) {
  return <span className="surface-live-level" data-expanded={expanded || undefined} data-testid="live-level">
    <LedMeter label={label} labelHidden value={Number.isFinite(level) ? level : 0} segments={expanded ? 40 : 5} />
    {children}
  </span>;
}
