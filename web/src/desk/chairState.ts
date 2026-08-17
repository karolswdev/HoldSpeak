// HS-135-06 -- the Chair/Floor surface toggle. A leaf Zustand store
// (chromeState pattern) so the dock and DeskApp can share the state
// without coupling. Chair is HOME; the floor is one dock-button away
// (counsel ruling B.Q1).
import { create } from "zustand";

export type DeskSurface = "chair" | "floor";

interface ChairState {
  surface: DeskSurface;
  setSurface(surface: DeskSurface): void;
  toggle(): void;
}

export const useChairState = create<ChairState>((set) => ({
  surface: "chair",
  setSurface: (surface) => set({ surface }),
  toggle: () =>
    set((s) => ({ surface: s.surface === "chair" ? "floor" : "chair" })),
}));
