/** Composed desk store (HS-117-02): focused slices, one `useDesk` export.
 * The public API is unchanged -- zero consumer edits. */
import { create } from "zustand";
import type { DeskState } from "./types";
import { createCompositorSlice } from "./compositorSlice";
import { createDataSlice } from "./dataSlice";
import { createDeskSlice } from "./deskSlice";
import { createRecordingSlice } from "./recordingSlice";
import { createScheduledRecordingSlice } from "./scheduledRecordingSlice";
import { depthFromOrder, orderFromDepth } from "../compositor/planes";

export const useDesk = create<DeskState>()((...args) => ({
  ...createCompositorSlice(...args),
  ...createDataSlice(...args),
  ...createDeskSlice(...args),
  ...createRecordingSlice(...args),
  ...createScheduledRecordingSlice(...args),
}));

// PHILO-16 (L3) — `panelDepth` is the stacking; `panelOrder` is derived from
// it for one release. A legacy write of the order alone (`setState({
// panelOrder })`: ChairDesk's Needs-you raise, tests, a reset) is honoured
// here: the depths follow the order. A write of both (the slice) is left be.
useDesk.subscribe((state, prev) => {
  if (state.panelOrder === prev.panelOrder || state.panelDepth !== prev.panelDepth) return;
  const order = state.panelOrder;
  const same =
    order.length === Object.keys(state.panelDepth).length &&
    orderFromDepth(state.panelDepth).every((id, i) => id === order[i]);
  if (!same) useDesk.setState({ panelDepth: depthFromOrder(order) });
});

// Re-export all public types so consumers importing from the store path
// continue to work unchanged.
export type { UnitPos, PanelRect, DeskView, ZoneViewPref, WindowInstance, DeskState, ScheduledRecording, ScheduledArmingState, ZoneRenameError } from "./types";
export { GHOST_LAYOUT_KEYS, COMPACT_LIST_THRESHOLD, defaultViewFor } from "./types";
export { loadPanelLayout, isRehydratedMinimized } from "./compositorSlice";
export {
  DESK_WORKSPACE_STORAGE_KEY,
  DESK_WORKSPACE_VERSION,
  loadDeskWorkspace,
} from "./workspaceStorage";
