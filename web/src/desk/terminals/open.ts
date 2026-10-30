import { terminalWindowEntry, terminalWindowId } from "./windows";
import type { DeskState, SliceCreator } from "../store/types";

/** Open/close helpers for the dynamic terminal window family. The compositor
 * remains the only owner of planes and geometry; these helpers only maintain
 * the additive descriptor list and restore/focus the native frame. */
export function openTerminalWindow(
  descriptorId: string,
  origin: { x: number; y: number } | undefined,
  set: (partial: Partial<DeskState>) => void,
  get: () => DeskState,
): void {
  const id = descriptorId.trim();
  if (!id) return;
  const windows = get().terminalWindows;
  if (!windows.some((window) => window.id === id)) {
    set({ terminalWindows: [...windows, terminalWindowEntry(id, origin)] });
  }
  get().restorePanel(terminalWindowId(id));
  get().recordRecentOpen(`terminal:${id}`);
}

export function closeTerminalWindow(
  descriptorId: string,
  set: (partial: Partial<DeskState>) => void,
  get: () => DeskState,
): void {
  const id = descriptorId.trim();
  if (!id) return;
  const next = get().terminalWindows.filter((window) => window.id !== id);
  if (next.length === get().terminalWindows.length) return;
  set({ terminalWindows: next });
  get().retirePanel(terminalWindowId(id));
}

export type TerminalWindowSlice = Pick<DeskState, "terminalWindows" | "openTerminalWindow" | "closeTerminalWindow">;

export function createTerminalWindowSlice(set: Parameters<SliceCreator<TerminalWindowSlice>>[0], get: Parameters<SliceCreator<TerminalWindowSlice>>[1]): TerminalWindowSlice {
  return {
    terminalWindows: [],
    openTerminalWindow: (id, origin) => openTerminalWindow(id, origin, set, get),
    closeTerminalWindow: (id) => closeTerminalWindow(id, set, get),
  };
}
