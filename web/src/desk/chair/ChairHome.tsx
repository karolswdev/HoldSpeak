// HS-135-06 -- ChairHome: the landing surface at `/`. Instantiates the
// Chair with lanes built generically from the LANE_COMPONENTS registry.
// Missing lanes (not yet shipped by stories 07-10) render nothing; the
// Chair's 300ms fallback owns the all-blank case.
// HS-135-11 -- the capture hero fills the hero slot: tap records, voice
// "start meeting" triggers it, Ask AI one tap away.

import type { ReactNode } from "react";
import { Chair } from "./Chair";
import { LANE_ORDER, type LaneId } from "./laneContract";
import { LANE_COMPONENTS } from "./lanes";
import { CaptureHero } from "./hero";
import { useDesk } from "../store";

/** Build the lanes prop by mapping LANE_ORDER over the registry. */
function buildLanes(): Partial<Record<LaneId, ReactNode>> {
  const lanes: Partial<Record<LaneId, ReactNode>> = {};
  for (const id of LANE_ORDER) {
    const Comp = LANE_COMPONENTS[id];
    if (Comp) lanes[id] = <Comp />;
  }
  return lanes;
}

export function ChairHome() {
  const lanes = buildLanes();
  return (
    <Chair
      hero={<CaptureHero onAskAI={() => useDesk.getState().openAsk()} />}
      lanes={lanes}
    />
  );
}
