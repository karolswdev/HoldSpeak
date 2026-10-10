// HS-135-06 -- the Chair/Floor surface toggle. A leaf Zustand store
// (chromeState pattern) so the dock and DeskApp can share the state
// without coupling. Chair is HOME; the floor is one dock-button away
// (counsel ruling B.Q1).
import { create } from "zustand";
import {
  loadDeskWorkspace,
  saveDeskWorkspaceSection,
} from "./store/workspaceStorage";

export type DeskSurface = "chair" | "floor";

interface ChairState {
  surface: DeskSurface;
  setSurface(surface: DeskSurface): void;
  toggle(): void;
}

// PHILO-13-07 (B2): the screen he was on (Chair or Floor) comes back after a
// reload, in the one workspace document.
export const useChairState = create<ChairState>((set) => ({
  surface: loadDeskWorkspace().screen ?? "chair",
  setSurface: (surface) => set({ surface }),
  toggle: () =>
    set((s) => ({ surface: s.surface === "chair" ? "floor" : "chair" })),
}));

useChairState.subscribe((s, prev) => {
  if (s.surface !== prev.surface) saveDeskWorkspaceSection({ screen: s.surface });
});
