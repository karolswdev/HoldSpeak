// HS-135-05 -- the lane composition contract (design-laws.md L2 +
// counsel ruling A.L2). A lane is a composed surface plugged into the
// Chair's door via this interface. The static order is fixed by
// counsel ruling B.Q2: Brief -> Follow-Through -> Meetings -> Agents.

import type { ReactNode } from "react";

/** The lane composition contract (L2, six-point spec). */
export interface LaneProps {
  /** The curated-dozen bound (counsel: JS prop default, NOT a CSS
   *  property). Above this count the lane renders a "N more" footer. */
  maxItems?: number;
  /** Open a surface/object in a DeskWindow by id. Every row action
   *  that needs deep work calls this; the lane itself never enters
   *  deep work. */
  onOpenInWindow: (id: string) => void;
  /** Optional footer verb (e.g. "Open Intelligence"). */
  footerVerb?: ReactNode;
}

/** Default curated-dozen bound (L2). */
export const DEFAULT_MAX_ITEMS = 12;

/** The fixed lane order (counsel ruling B.Q2). An urgency gradient:
 *  information -> obligations -> calendar -> automation. */
export const LANE_ORDER = [
  "brief",
  "follow-through",
  "meetings",
  "agents",
] as const;

export type LaneId = (typeof LANE_ORDER)[number];
