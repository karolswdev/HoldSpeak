import { useLayoutEffect, useMemo, useRef, useState } from "react";
import {
  DEFAULT_ATMOSPHERE_ID,
  resolveAtmosphere,
  type AtmosphereId,
} from "./atmosphereRegistry";
import { mountAtmosphereScene } from "./atmosphereRuntime";
import { observeAtmosphereActivity } from "./atmosphereActivity";
import { useAtmosphereControls } from "./atmosphereControls";
import { useAtmosphereSound } from "./atmosphereSound";

/** The Desk's decorative backdrop. The Screen owns all product gestures;
 * this host only loads the selected scene and observes existing activity. */
export interface AtmosphereProps {
  /** Personalization seam: callers select any registered lazy atmosphere. */
  id?: AtmosphereId;
  /** The chosen still stays visible until the runtime's first render succeeds. */
  onReadyChange?: (ready: boolean) => void;
}

export function Atmosphere({ id = DEFAULT_ATMOSPHERE_ID, onReadyChange }: AtmosphereProps) {
  const { motion } = useAtmosphereControls();
  useAtmosphereSound(id);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const definition = useMemo(() => resolveAtmosphere(id), [id]);
  const [state, setState] = useState<"quiet" | "loading" | "ready" | "failed">(
    definition.load ? "loading" : "quiet",
  );

  useLayoutEffect(() => {
    const load = definition.load;
    // Reset before paint when a place or its motion choice replaces the canvas.
    setState(load ? "loading" : "quiet");
    onReadyChange?.(false);
    if (!load) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    let cancelled = false;
    let released = false;
    let cleanup: (() => void) | undefined;
    const activity = observeAtmosphereActivity();
    const release = () => {
      if (released) return;
      released = true;
      cleanup?.();
      activity.dispose();
    };
    const mount = async () => {
      try {
        const factory = await load();
        if (cancelled) return;
        cleanup = mountAtmosphereScene(canvas, factory, {
          seed: definition.seed,
          activity,
          motion,
        });
        canvas.dataset.ready = "true";
        setState("ready");
        onReadyChange?.(true);
      } catch {
        if (cancelled) return;
        release();
        setState("failed");
        onReadyChange?.(false);
      }
    };
    void mount();
    return () => {
      cancelled = true;
      release();
      onReadyChange?.(false);
    };
  }, [definition, motion, onReadyChange]);

  return (
    <div
      className="desk-stage"
      data-atmosphere={definition.id}
      data-atmosphere-state={state}
      aria-hidden="true"
    >
      {definition.load ? (
        <canvas
          key={`${definition.id}:${motion}`}
          ref={canvasRef}
          className="desk-atmosphere-canvas"
        />
      ) : null}
      <div className={`desk-atmosphere-grade ${definition.gradeClassName}`} />
    </div>
  );
}
