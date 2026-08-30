/** Re-export shim (HS-117-02): the store now lives in `store/` as focused
 * slices. This file preserves every existing import path. */
export {
  useDesk,
  defaultViewFor,
  loadPanelLayout,
  loadDeskWorkspace,
  DESK_WORKSPACE_STORAGE_KEY,
  DESK_WORKSPACE_VERSION,
  GHOST_LAYOUT_KEYS,
  COMPACT_LIST_THRESHOLD,
} from "./store/index";

export type {
  UnitPos,
  PanelRect,
  DeskView,
  ZoneViewPref,
  WindowInstance,
  DeskState,
} from "./store/types";
