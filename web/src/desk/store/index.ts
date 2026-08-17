/** Composed desk store (HS-117-02): focused slices, one `useDesk` export.
 * The public API is unchanged -- zero consumer edits. */
import { create } from "zustand";
import type { DeskState } from "./types";
import { createCompositorSlice } from "./compositorSlice";
import { createDataSlice } from "./dataSlice";
import { createDeskSlice } from "./deskSlice";
import { createRecordingSlice } from "./recordingSlice";
import { createScheduledRecordingSlice } from "./scheduledRecordingSlice";

export const useDesk = create<DeskState>()((...args) => ({
  ...createCompositorSlice(...args),
  ...createDataSlice(...args),
  ...createDeskSlice(...args),
  ...createRecordingSlice(...args),
  ...createScheduledRecordingSlice(...args),
}));

// Re-export all public types so consumers importing from the store path
// continue to work unchanged.
export type { UnitPos, PanelRect, DeskView, ZoneViewPref, DeskState, ScheduledRecording, ScheduledArmingState } from "./types";
export { GHOST_LAYOUT_KEYS, COMPACT_LIST_THRESHOLD, defaultViewFor } from "./types";
export { loadPanelLayout } from "./compositorSlice";
