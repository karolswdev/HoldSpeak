/** Spine (the language, 2026-11-08): a 4 px bar under a mast or inside an
 *  object row. It shows where a thing stands in the six meaning colours:
 *  steel (ours, running), brass (waits on you), moss (done), coral (at
 *  risk), graphite (parked), idle (not yet). Give it `segments` (each a
 *  tone and a share), or one `tone` and a `fill` from 0 to 1. */
import "./spine.css";

export type SpineTone = "steel" | "brass" | "moss" | "coral" | "graphite" | "idle";
export type SpineSegment = { tone: SpineTone; share: number };

export type SpineProps = {
  segments?: ReadonlyArray<SpineSegment>;
  tone?: SpineTone;
  /** 0..1, with `tone`: the filled part; the rest is idle. */
  fill?: number;
  /** The accessible words ("3 of 5 done"). Without it the spine is hidden
   *  from assistive technology (the face says it in words elsewhere). */
  label?: string;
  className?: string;
  "data-testid"?: string;
  [data: `data-${string}`]: string | undefined;
};

function clamp01(value: number): number {
  return Number.isFinite(value) ? Math.min(1, Math.max(0, value)) : 0;
}

export function spineSegments({ segments, tone = "steel", fill = 1 }: Pick<SpineProps, "segments" | "tone" | "fill">): SpineSegment[] {
  if (segments) return segments.filter((s) => Number.isFinite(s.share) && s.share > 0);
  const filled = clamp01(fill);
  const out: SpineSegment[] = [];
  if (filled > 0) out.push({ tone, share: filled });
  if (filled < 1) out.push({ tone: "idle", share: 1 - filled });
  return out;
}

export function Spine({ segments, tone, fill, label, className, ...data }: SpineProps) {
  const parts = spineSegments({ segments, tone, fill });
  return (
    <span
      {...data}
      className={className ? `surface-spine ${className}` : "surface-spine"}
      data-mode={segments ? "segments" : "fill"}
      role={label ? "img" : undefined}
      aria-label={label || undefined}
      aria-hidden={label ? undefined : true}
    >
      {parts.map((part, index) => (
        <span
          key={index}
          className="surface-spine-part"
          data-tone={part.tone}
          style={{ flexGrow: part.share }}
        />
      ))}
    </span>
  );
}
