import { create } from "zustand";
import { apiFetch } from "../lib/api";

/** Retained only so an older browser value can be ignored safely during the
 * migration. Builder tools are a hub preference, never browser state. */
export const BUILDER_TOOLS_STORAGE_KEY = "hs.desk.builderTools";

type BuilderToolsState = {
  on: boolean;
  /** Optimistic cache update after the canonical Settings writer queues a
   * change. It does not write a second preference store. */
  setOn(on: boolean): void;
  /** Read the canonical hub value for this browser. */
  hydrate(): Promise<void>;
};

export const useBuilderTools = create<BuilderToolsState>((set) => ({
  on: false,
  setOn: (on) => set({ on }),
  hydrate: async () => {
    try {
      const data = await apiFetch<{ ui?: { builder_tools?: unknown } }>("/api/settings");
      if (typeof data?.ui?.builder_tools === "boolean") set({ on: data.ui.builder_tools });
    } catch {
      // The existing Desk remains usable while Settings is unavailable.
    }
  },
}));

export const builderToolsOn = (): boolean => useBuilderTools.getState().on;

/** Start one canonical read without making browser storage authoritative. */
export function hydrateBuilderTools(): void {
  void useBuilderTools.getState().hydrate();
}
