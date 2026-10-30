import { readTerminalSessions, type TerminalSessionsResponse } from "./api";
import type { TerminalDescriptor } from "./types";

/** Native terminal window identity. The descriptor id is opaque and stable;
 * it is never a pane selector and must not be rewritten when metadata changes. */

export const TERMINALS_APPLICATION_KEY = "open-terminals";
export const TERMINALS_WINDOW_ID = "surface-terminals";
export const TERMINAL_WINDOW_PREFIX = "terminal:";

export interface TerminalWindowEntry {
  id: string;
  origin: { x: number; y: number } | null;
}

export function terminalWindowId(descriptorId: string): string {
  return `${TERMINAL_WINDOW_PREFIX}${descriptorId}`;
}

export function terminalDescriptorId(windowId: string): string | null {
  if (!windowId.startsWith(TERMINAL_WINDOW_PREFIX)) return null;
  const id = windowId.slice(TERMINAL_WINDOW_PREFIX.length);
  return id || null;
}

export function isTerminalWindowId(windowId: string): boolean {
  return terminalDescriptorId(windowId) !== null;
}

export function terminalWindowEntry(
  descriptorId: string,
  origin?: { x: number; y: number },
): TerminalWindowEntry {
  return { id: descriptorId, origin: origin ?? null };
}

export interface TerminalInventoryState {
  status: "idle" | "loading" | "ok" | "tmux_absent" | "error";
  detail: string | null;
  sessions: TerminalDescriptor[];
}

const EMPTY_INVENTORY: TerminalInventoryState = {
  status: "idle",
  detail: null,
  sessions: [],
};
let inventory: TerminalInventoryState = EMPTY_INVENTORY;
let inventoryRead: Promise<void> | null = null;
const inventoryListeners = new Set<() => void>();

export function terminalInventorySnapshot(): TerminalInventoryState {
  return inventory;
}

export function subscribeTerminalInventory(listener: () => void): () => void {
  inventoryListeners.add(listener);
  return () => inventoryListeners.delete(listener);
}

function publishTerminalInventory(next: TerminalInventoryState): void {
  inventory = next;
  for (const listener of inventoryListeners) listener();
}

export function refreshTerminalInventory(): Promise<void> {
  if (inventoryRead) return inventoryRead;
  publishTerminalInventory({ ...inventory, status: "loading", detail: null });
  inventoryRead = readTerminalSessions()
    .then((answer: TerminalSessionsResponse) => {
      const status = answer.status === "tmux_absent" || answer.status === "error" ? answer.status : "ok";
      publishTerminalInventory({ status, detail: answer.detail ?? null, sessions: answer.sessions });
    })
    .catch((error: unknown) => {
      publishTerminalInventory({ status: "error", detail: error instanceof Error ? error.message : "terminal inventory unavailable", sessions: [] });
    })
    .finally(() => {
      inventoryRead = null;
    });
  return inventoryRead;
}
