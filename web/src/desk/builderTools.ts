import { create } from "zustand";

/** Betterment shell S1: the Builder tools setting (Settings ▸ System). Off by
 * default. On, Go draws Builder ▸ (Activity, Processes, Context, Components,
 * Calendar snapshot, Delivery board, Terminals, Refresh from hub) and Search
 * lists those rows. A per-browser view choice, like the wallpaper: it is kept
 * in this browser's storage and never written to the hub. */
export const BUILDER_TOOLS_STORAGE_KEY = "hs.desk.builderTools";

function read(): boolean {
  try {
    return globalThis.localStorage?.getItem(BUILDER_TOOLS_STORAGE_KEY) === "on";
  } catch {
    return false;
  }
}

export const useBuilderTools = create<{ on: boolean; setOn(on: boolean): void }>((set) => ({
  on: read(),
  setOn: (on) => {
    try {
      if (on) globalThis.localStorage?.setItem(BUILDER_TOOLS_STORAGE_KEY, "on");
      else globalThis.localStorage?.removeItem(BUILDER_TOOLS_STORAGE_KEY);
    } catch {
      // Storage refused (a private window): the switch still holds this session.
    }
    set({ on });
  },
}));

export const builderToolsOn = (): boolean => useBuilderTools.getState().on;
