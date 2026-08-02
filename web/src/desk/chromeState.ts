/** HS-111-07 - shared chrome transients (a leaf module, no component
 * imports): the ⌘K palette and the ⌘/ shortcut sheet open state. The
 * registry's system verbs and the components both drive these, so the
 * one keymap can toggle them without a component import cycle. */
import { create } from "zustand";

interface Transient {
  open: boolean;
  setOpen(open: boolean): void;
  toggle(): void;
}

const transient = () =>
  create<Transient>((set) => ({
    open: false,
    setOpen: (open) => set({ open }),
    toggle: () => set((s) => ({ open: !s.open })),
  }));

/** The ⌘K command deck. */
export const usePalette = transient();

/** The ⌘/ shortcut sheet. */
export const useShortcutSheet = transient();
