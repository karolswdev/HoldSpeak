import { useEffect, useRef } from "react";
import { mountRainyCityScene } from "./rainyCityScene";

/** The Floor's decorative world backdrop. Product objects remain in the
 * independent Pixi canvas above this layer, so scenery can never intercept a
 * Desk gesture or become application state. */
export function Atmosphere() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    return mountRainyCityScene(canvas);
  }, []);

  return (
    <div className="desk-stage" aria-hidden="true">
      <canvas ref={canvasRef} className="desk-rain-city" />
      <div className="desk-rain-city-grade" />
    </div>
  );
}
