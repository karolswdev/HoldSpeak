// HS-135 — the lane registry. Each lane story (07-10) adds exactly one
// entry at its SHIP; the home surface (story 06) instantiates the Chair
// from this map generically. Missing lanes render nothing (the Chair's
// 300ms fallback owns the all-blank case).
import type { ComponentType } from "react";
import type { LaneId, LaneProps } from "../laneContract";
import { BriefLane } from "./BriefLane";
import { DoorBoardLane } from "./DoorBoardLane";
import { MeetingsLane } from "./MeetingsLane";
import { AgentsLane } from "./AgentsLane";

export const LANE_COMPONENTS: Partial<Record<LaneId, ComponentType<LaneProps>>> = {
  door: DoorBoardLane,
  brief: BriefLane, // HS-150-03
  meetings: MeetingsLane, // HS-135-09
  agents: AgentsLane, // HS-135-10
};
