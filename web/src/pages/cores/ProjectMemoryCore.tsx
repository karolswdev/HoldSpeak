// HS-158-05 — thin compatibility re-export.  The implementation
// graduated into features/project-room/ (WEB-ARC-001..004); this file
// preserves every import path that tests, the barrel, and the lazy
// application loader depend on.
export {
  ProjectRoomCore as ProjectMemoryCore,
  LifecycleChip,
  DecisionPromotionSlot,
} from "../../features/project-room/ProjectRoomCore";

export {
  composeProjectTimeline,
  lifecycleLabel,
} from "../../features/project-room/model";

export type { ProjectTimelineEntry } from "../../features/project-room/model";
