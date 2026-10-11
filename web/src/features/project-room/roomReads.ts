/** PHILO-17 (phonepass) — the Room's first reads, registered as they mount.
 *
 *  A read registers when its section mounts, reports when it resolves
 *  (success or failure) and leaves when its section unmounts. There is no
 *  list of names: a section that does not mount (Add sources on a project
 *  that has sources) waits on nothing. Each read belongs to the Room slot
 *  it mounts in (RoomSlotContext). The Room body is drawn when every
 *  registered read has resolved, or at the cap; a slot still out at the cap
 *  stands at the foot, and each late slot that resolves takes the next
 *  place there (below every slot already drawn). A section outside a Room
 *  (no provider) reports to nobody. */
import { createContext, useContext, useLayoutEffect } from "react";

/** `resolved: null` unregisters the read. */
export type RoomReadReport = (slot: string, name: string, resolved: boolean | null) => void;

export const RoomReadsContext = createContext<RoomReadReport | null>(null);
export const RoomSlotContext = createContext<string>("body");

export function useRoomRead(name: string, resolved: boolean): void {
  const report = useContext(RoomReadsContext);
  const slot = useContext(RoomSlotContext);
  useLayoutEffect(() => {
    report?.(slot, name, resolved);
  }, [report, slot, name, resolved]);
  useLayoutEffect(() => () => report?.(slot, name, null), [report, slot, name]);
}

/** The body is drawn after this long even when a read has not resolved. */
export const ROOM_READS_CAP_MS = 8000;

/** slot -> read name -> resolved */
export type SlotReads = Readonly<Record<string, Readonly<Record<string, boolean>>>>;

export function withRead(reads: SlotReads, slot: string, name: string, resolved: boolean | null): SlotReads {
  const now = reads[slot] ?? {};
  if (resolved === null) {
    if (!(name in now)) return reads;
    const { [name]: _gone, ...rest } = now;
    return { ...reads, [slot]: rest };
  }
  if (now[name] === resolved) return reads;
  return { ...reads, [slot]: { ...now, [name]: resolved } };
}

export function slotResolved(reads: SlotReads, slot: string): boolean {
  return Object.values(reads[slot] ?? {}).every(Boolean);
}

export function unresolvedSlots(reads: SlotReads): string[] {
  return Object.keys(reads).filter((slot) => !slotResolved(reads, slot));
}

/** The late slots that resolved since the last call, each given the next
 *  place at the foot, in the order they resolved. */
export function placeResolved(
  late: readonly string[],
  places: Readonly<Record<string, number>>,
  reads: SlotReads,
): Record<string, number> | null {
  const fresh = late.filter((slot) => places[slot] === undefined && slotResolved(reads, slot));
  if (!fresh.length) return null;
  let next = Math.max(0, ...Object.values(places));
  const out = { ...places };
  for (const slot of fresh) out[slot] = ++next;
  return out;
}

/** A late slot that has not resolved sits below every placed one. */
export const PENDING_PLACE = 10000;
