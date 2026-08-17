// HS-135-05 -- the Chair surface: HOME at every width (L2). A
// jobs-first composite surface, not a new data model. The capture
// hero is a placeholder slot (story 11 fills it). Four ordered lane
// slots render from a static array (counsel ruling B.Q2). Ember-only
// on the Chair (no accent-cool, no accent-gradient on the shell --
// accent-gradient is hero-only, story 11).

import { useEffect, useRef, useState, type ReactNode } from "react";
import { SurfaceState } from "../surface/Surface";
import { LANE_ORDER, type LaneId } from "./laneContract";
import "./chair.css";

export interface ChairProps {
  /** The capture hero slot (story 11 fills this with mic/record). */
  hero?: ReactNode;
  /** Lane render slots keyed by lane id. The Chair renders them in
   *  the fixed LANE_ORDER; missing lanes return null (the Chair waits
   *  for data). */
  lanes: Partial<Record<LaneId, ReactNode>>;
}

/** The 300ms all-blank fallback (counsel condition 2): if ALL lanes
 *  are null/empty after 300ms, show exactly ONE SurfaceState. */
const ALL_BLANK_DELAY_MS = 300;

export function Chair({ hero, lanes }: ChairProps) {
  const [showFallback, setShowFallback] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const hasAnyLane = LANE_ORDER.some((id) => lanes[id] != null);

  useEffect(() => {
    if (hasAnyLane) {
      // At least one lane is rendering -- clear the fallback.
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      setShowFallback(false);
      return;
    }
    // All lanes blank -- start the 300ms timer.
    if (!timerRef.current) {
      timerRef.current = setTimeout(() => {
        setShowFallback(true);
        timerRef.current = null;
      }, ALL_BLANK_DELAY_MS);
    }
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [hasAnyLane]);

  return (
    <div className="chair" data-testid="chair">
      {/* The capture hero placeholder (story 11 fills it). */}
      <div className="chair-hero" data-testid="chair-hero">
        {hero}
      </div>

      {/* The four ordered lane slots. */}
      <div className="chair-lanes" data-testid="chair-lanes">
        {hasAnyLane
          ? LANE_ORDER.map((id) => {
              const content = lanes[id];
              return content != null ? (
                <div key={id} className="chair-lane" data-lane={id}>
                  {content}
                </div>
              ) : null;
            })
          : showFallback
            ? (
              <SurfaceState empty emptyLabel="Nothing yet" />
            )
            : null}
      </div>
    </div>
  );
}
