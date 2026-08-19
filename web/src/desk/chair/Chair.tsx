// HS-135-05 -- the Chair surface: HOME at every width (L2). A
// jobs-first composite surface, not a new data model. The capture
// hero is a placeholder slot (story 11 fills it). Four ordered lane
// slots render from a static array (counsel ruling B.Q2). Ember-only
// on the Chair (no accent-cool, no accent-gradient on the shell --
// accent-gradient is hero-only, story 11).
//
// The all-blank state (counsel condition 2, mechanism revised at the
// acceptance review): the invitation renders always and chair.css
// shows it -- and scales the hero -- only when no lane carries a
// .surface-section, via the same :has() gate. One calm state, no
// per-lane spinners, and reachable through ChairHome (the old JS
// timer fallback could never fire once all four lanes registered).

import { type ReactNode } from "react";
import { LANE_ORDER, type LaneId } from "./laneContract";
import "./chair.css";

export interface ChairProps {
  /** The capture hero slot (story 11 fills this with mic/record). */
  hero?: ReactNode;
  /** Lane render slots keyed by lane id. The Chair renders them in
   *  the fixed LANE_ORDER; missing lanes render nothing (the CSS
   *  empty gate owns the all-blank presentation). */
  lanes: Partial<Record<LaneId, ReactNode>>;
}

export function Chair({ hero, lanes }: ChairProps) {
  return (
    <div className="chair" data-testid="chair">
      {/* The capture hero placeholder (story 11 fills it). */}
      <div className="chair-hero" data-testid="chair-hero">
        {hero}
      </div>

      {/* Always rendered; visible only in the all-blank state (CSS). */}
      <div className="chair-empty-invitation">
        <span className="chair-empty-invitation-text">Start rough. Keep developing it.</span>
      </div>

      {/* The four ordered lane slots. */}
      <div className="chair-lanes" data-testid="chair-lanes">
        {LANE_ORDER.map((id) => {
          const content = lanes[id];
          return content != null ? (
            <div key={id} className="chair-lane" data-lane={id}>
              {content}
            </div>
          ) : null;
        })}
      </div>
    </div>
  );
}
