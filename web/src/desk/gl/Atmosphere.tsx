import { useEffect, useMemo, useRef } from "react";
import {
  DEFAULT_ATMOSPHERE_ID,
  resolveAtmosphere,
  type AtmosphereId,
} from "./atmosphereRegistry";
import { mountAtmosphereScene } from "./atmosphereRuntime";

/** The Floor's decorative world backdrop. Product objects remain in the
 * independent Pixi canvas above this layer, so scenery can never intercept a
 * Desk gesture or become application state. */
export interface AtmosphereProps {
  /** Personalization seam: callers select any registered lazy atmosphere. */
  id?: AtmosphereId;
}

export function Atmosphere({ id = DEFAULT_ATMOSPHERE_ID }: AtmosphereProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const definition = useMemo(() => resolveAtmosphere(id), [id]);

  useEffect(() => {
    const load = definition.load;
    if (!load) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    let cancelled = false;
    let cleanup: (() => void) | undefined;
    void load()
      .then((factory) => {
        if (cancelled) return;
        cleanup = mountAtmosphereScene(canvas, factory, {
          seed: definition.seed,
        });
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
      cleanup?.();
    };
  }, [definition]);

  return (
    <div
      className="desk-stage"
      data-atmosphere={definition.id}
      aria-hidden="true"
    >
      {definition.load ? (
        <canvas ref={canvasRef} className="desk-atmosphere-canvas" />
      ) : null}
      <div className={`desk-atmosphere-grade ${definition.gradeClassName}`} />
    </div>
  );
}
