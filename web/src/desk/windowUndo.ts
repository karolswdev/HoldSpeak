import { ApiError, apiFetch } from "../lib/api";
import type { WindowUndo } from "./used";

export class WindowUndoStale extends Error {
  constructor() {
    super("A window changed. Its later state was kept.");
    this.name = "WindowUndoStale";
  }
}

/** The Desk and the Wrote receipt restore through the same atomic service. */
export async function restoreWindowUndo(undo: WindowUndo): Promise<void> {
  try {
    await apiFetch("/api/desk/windows/restore", { method: "POST", json: undo });
  } catch (cause) {
    if (cause instanceof ApiError && cause.status === 409) throw new WindowUndoStale();
    throw cause;
  }
}
