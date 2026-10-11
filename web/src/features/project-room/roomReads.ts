/** PHILO-17 (phonepass, Astra r1) — the Room's first reads, named.
 *
 *  Each Room section that makes its own read reports when that first read
 *  has resolved (success or failure). The Room body is drawn when every
 *  reported read has resolved, so no section lands above a drawn row. A
 *  section outside a Room (no provider) reports to nobody. */
import { createContext, useContext, useLayoutEffect } from "react";

export type RoomReadReport = (name: string, resolved: boolean) => void;

export const RoomReadsContext = createContext<RoomReadReport | null>(null);

/** Report this section's first read. Call it before any early return. */
export function useRoomRead(name: string, resolved: boolean): void {
  const report = useContext(RoomReadsContext);
  useLayoutEffect(() => {
    report?.(name, resolved);
  }, [report, name, resolved]);
}

/** The Room body is drawn after this long even when a read has not
 *  resolved; a late section then fills its own place at the foot. */
export const ROOM_READS_CAP_MS = 8000;

/** Pure: is every reported read resolved? (No report yet: not yet.) */
export function allResolved(reads: Readonly<Record<string, boolean>>, required: readonly string[]): boolean {
  return required.every((name) => reads[name] === true) && Object.values(reads).every(Boolean);
}
