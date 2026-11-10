// A mounted list contributes its declared verbs to its window's app menu.
// This is transient selection state, not an application or verb registry.
import { useSyncExternalStore } from "react";
import type { WorkMenuEntry } from "../DeskMenu";
const rows = new Map<string, { owner: string; entries: WorkMenuEntry[] }>();
const listeners = new Set<() => void>();
const empty: WorkMenuEntry[] = [];
const changed = () => listeners.forEach((listener) => listener());
export function publishListMenu(windowId: string, owner: string, entries: WorkMenuEntry[]) {
  rows.set(windowId, { owner, entries }); changed();
}
export function ownsListMenu(windowId: string, owner: string) { return rows.get(windowId)?.owner === owner; }
export function clearListMenu(windowId: string, owner: string) {
  if (ownsListMenu(windowId, owner)) { rows.delete(windowId); changed(); }
}
export function useListMenu(windowId: string | null) {
  return useSyncExternalStore((listener) => { listeners.add(listener); return () => { listeners.delete(listener); }; },
    () => windowId ? rows.get(windowId)?.entries ?? empty : empty, () => empty);
}

const walks = new Map<string, { owner: string; app: string }>();
export function publishWindowWalk(windowId: string, owner: string, app: string) {
  walks.set(windowId, { owner, app }); changed();
}
export function clearWindowWalk(windowId: string, owner: string) {
  if (walks.get(windowId)?.owner === owner) { walks.delete(windowId); changed(); }
}
export function useWindowWalk(windowId: string | null) {
  return useSyncExternalStore((listener) => { listeners.add(listener); return () => { listeners.delete(listener); }; },
    () => windowId ? walks.get(windowId)?.app : undefined, () => undefined);
}

export function windowWalkApp(windowId:string|null):string|undefined {return windowId ? walks.get(windowId)?.app ?? windowId : undefined;}
