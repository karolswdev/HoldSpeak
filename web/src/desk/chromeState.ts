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

/** PHILO-13-08 (B3) — the palette asks a name before a create.
 *
 * `New Decision` wrote a `New decision` record at once (grounding F9). Now
 * the create asks its title in the ⌘K well first; Enter with a title runs
 * `submit`, and closing the palette abandons it (nothing is written). */
export interface NamePrompt {
  /** The well's label and placeholder (`Decision title`). */
  label: string;
  submit(name: string): void;
}

interface NamePromptState {
  prompt: NamePrompt | null;
  ask(prompt: NamePrompt): void;
  clear(): void;
}

export const useNamePrompt = create<NamePromptState>((set) => ({
  prompt: null,
  ask: (prompt) => {
    set({ prompt });
    usePalette.getState().setOpen(true);
  },
  clear: () => set({ prompt: null }),
}));

// A palette that closes (Escape, outside, ⌘K, a run) abandons the prompt.
usePalette.subscribe((state, previous) => {
  if (previous.open && !state.open && useNamePrompt.getState().prompt)
    useNamePrompt.getState().clear();
});
