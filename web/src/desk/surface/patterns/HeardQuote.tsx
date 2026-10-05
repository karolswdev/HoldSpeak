/** HeardQuote — the owner's own words played back as the face's one big fact.
 *
 *  First run, C1 "Heard first" (owner ratified 2026-10-05). The quote is
 *  the display step (once per face: a face that shows a HeardQuote gives
 *  it the display role). Under it, the facts of the take — HEARD, the word
 *  count, the length, the time — and the take's verbs (Play · Again ·
 *  Keep as note on the first-run face). His words are content, not prose.
 */
import type { ReactNode } from "react";
import { StateChip } from "./StateChip";
import { LampGadget } from "../gadgets";
import { countToken } from "../count";
import "./heard-quote.css";

/** Words in a take: whitespace-separated runs. */
export function heardWordCount(text: string): number {
  return text.trim() ? text.trim().split(/\s+/).length : 0;
}

/** `0:04`, `1:12`: the length of a take (minutes:seconds). */
export function heardDuration(seconds: number): string {
  const whole = Math.max(0, Math.round(seconds));
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}

/** The one facts token: `8 WORDS · 0:04 · 14:03`. Each part only when known. */
export function heardFacts({
  text,
  seconds,
  at,
}: {
  text: string;
  seconds?: number | null;
  at?: string | null;
}): string {
  return [
    countToken(heardWordCount(text), "WORD"),
    seconds != null && seconds > 0 ? heardDuration(seconds) : null,
    at || null,
  ]
    .filter(Boolean)
    .join(" · ");
}

export function HeardQuote({
  text,
  seconds,
  at,
  local,
  verbs,
  size = "display",
  className,
}: {
  /** His words, exactly as the transcript gave them. */
  text: string;
  /** The length of the take in seconds. */
  seconds?: number | null;
  /** The clock time of the take (`14:03`). */
  at?: string | null;
  /** The take ran on this device: an ON DEVICE lamp. */
  local?: boolean;
  /** The take's verbs (library Buttons). */
  verbs?: ReactNode;
  /** `display` (the one big fact) or `primary` (a small echo). */
  size?: "display" | "primary";
  className?: string;
}) {
  const facts = heardFacts({ text, seconds, at });
  return (
    <figure
      className={className ? `surface-heard ${className}` : "surface-heard"}
      data-size={size}
      data-testid="heard-quote"
    >
      <blockquote className="surface-heard-quote">
        {"“"}
        {text.trim()}
        {"”"}
      </blockquote>
      <figcaption className="surface-heard-facts">
        <StateChip state="success" label="HEARD" icon="●" />
        {facts ? <span className="surface-token surface-heard-token">{facts}</span> : null}
        {local ? <LampGadget label="ON DEVICE" on /> : null}
      </figcaption>
      {verbs ? <div className="surface-heard-verbs">{verbs}</div> : null}
    </figure>
  );
}
