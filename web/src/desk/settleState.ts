import { create } from "zustand";

/** Presentation only. Never persists, rearranges windows, or controls capture. */
export const useSettleState = create<{
  settled: boolean;
  setSettled(value: boolean): void;
  toggle(): void;
}>((set) => ({
  settled: false,
  setSettled: (settled) => set({ settled }),
  toggle: () => set((state) => ({ settled: !state.settled })),
}));
