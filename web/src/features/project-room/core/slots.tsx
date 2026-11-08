// The Room's slots and its first-read gate (PHILO-17 phonepass): the body is
// drawn when every registered read has resolved, or at the cap.
import React, { useCallback, useEffect, useLayoutEffect, useReducer, useRef, useState } from "react";
import {
  PENDING_PLACE, ROOM_READS_CAP_MS, RoomSlotContext, placeResolved, unresolvedSlots,
  useRoomRead, withRead, type SlotReads,
} from "../roomReads";

/** PHILO-17 (phonepass): one Room section's place. The reads its section
 *  makes register in this slot (RoomSlotContext); `own` are the Room's own
 *  reads that belong to it. A slot whose reads were still out when the body
 *  was first drawn stands at the foot (`order`), and a fixed line holds its
 *  place until they resolve; its section stays mounted (its reads run) but
 *  is not drawn. */
export type SlotPlace = { style?: React.CSSProperties; waiting: boolean };

function OwnRead({ name, resolved }: { name: string; resolved: boolean }) {
  useRoomRead(name, resolved);
  return null;
}

export function RoomSlot({
  id,
  place,
  own,
  empty = false,
  delay,
  children,
  ...rest
}: {
  id: string;
  place: SlotPlace;
  own?: Record<string, boolean>;
  /** Nothing to draw: the slot takes no place (no gap) unless it waits. */
  empty?: boolean;
  delay: string;
  children?: React.ReactNode;
} & React.HTMLAttributes<HTMLDivElement> & { "data-section"?: string }) {
  const hide = empty && !place.waiting ? { display: "none" } : undefined;
  return (
    <RoomSlotContext.Provider value={id}>
      {Object.entries(own ?? {}).map(([name, resolved]) => <OwnRead key={name} name={name} resolved={resolved} />)}
      <div className="room-section-rise" data-room-slot={id}
        style={{ animationDelay: delay, ...place.style, ...hide }} {...rest}>
        {place.waiting ? <p className="room-empty-line room-late-line" data-testid="room-late-line">Loading…</p> : null}
        <div style={{ display: place.waiting ? "none" : "contents" }}>{children}</div>
      </div>
    </RoomSlotContext.Provider>
  );
}

/** PHILO-17 (phonepass): the body is not drawn until its sections' reads
 *  stop moving its rows (a tap never lands on a row that moved under it).
 *  Astra r1/r2: an explicit gate, not a timer. Each read registers when
 *  its section mounts, in the slot it mounts in (roomReads.ts); the body is
 *  drawn when every registered read has resolved, or at the cap. A slot
 *  still out at the cap stands at the foot; each that resolves later takes
 *  the next place there, below every slot already drawn. */
export function useRoomReadsGate(hasRoom: boolean) {
  const readsRef = useRef<SlotReads>({});
  const [, bumpReads] = useReducer((n: number) => n + 1, 0);
  const reportRead = useCallback((slot: string, name: string, resolved: boolean | null) => {
    const next = withRead(readsRef.current, slot, name, resolved);
    if (next === readsRef.current) return;
    readsRef.current = next;
    bumpReads();
  }, []);
  const [gate, setGate] = useState<{ shown: boolean; late: string[]; places: Record<string, number> }>(
    { shown: false, late: [], places: {} });
  const [capped, setCapped] = useState(false);
  useEffect(() => {
    if (!hasRoom) return;
    const timer = window.setTimeout(() => setCapped(true), ROOM_READS_CAP_MS);
    return () => window.clearTimeout(timer);
  }, [hasRoom]);
  // After the children's layout effects (their registrations), before paint.
  useLayoutEffect(() => {
    if (!hasRoom) return;
    const reads = readsRef.current;
    if (!gate.shown) {
      const late = unresolvedSlots(reads);
      if (!late.length || capped) setGate({ shown: true, late, places: {} });
      return;
    }
    const places = placeResolved(gate.late, gate.places, reads);
    if (places) setGate((now) => ({ ...now, places }));
  });
  const place = (id: string): SlotPlace => {
    if (!gate.shown || !gate.late.includes(id)) return { waiting: false };
    const at = gate.places[id];
    return { style: { order: at ?? PENDING_PLACE }, waiting: at === undefined };
  };
  return { reportRead, shown: gate.shown, place };
}
