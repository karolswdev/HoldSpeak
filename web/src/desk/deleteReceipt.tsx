/** PHILO-8-02 — one delete everywhere.
 *
 * `object.delete` is hook-free: it dispatches `OBJECT_DELETE_REQUEST`
 * (`verbRegistry.ts`). This module holds the ONE listener and the ONE
 * undo receipt for it. `DeskDeleteHost` mounts once, in `DeskApp`; the
 * Screen (the one desk, PHILO-17) places `DeskDeleteSeat` in its foot, the
 * seat the owner ratified in #665 for the Floor (now parked).
 *
 * The rules (the Astra-role ruling, phase 8 story 02):
 * - the queued object leaves the selection, so the next select-and-Delete
 *   targets only the next object;
 * - a second delete commits the first at once (the receipt keeps one slot);
 * - a seat that unmounts (a failed refresh redraws the desk) keeps the Undo;
 * - where no seat is mounted the delete is WITHHELD: the verb is
 *   greyed with its reason (`verbRegistry.ts`) and nothing is deleted.
 */
import { useEffect, useSyncExternalStore, type ReactNode } from "react";
import { useDesk } from "./store";
import { qualifiedRef } from "./api";
import { OBJECT_DELETE_REQUEST } from "./verbRegistry";
import { objectByRef } from "./world";
import { useUndoReceipt } from "./hooks/useUndoReceipt";
import { deleteSeatShown, seatMounted, seatUnmounted } from "./deleteSeat";

let current: ReactNode = null;
const listeners = new Set<() => void>();

function publish(node: ReactNode) {
  current = node;
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** The one listener and the one hook. Renders nothing itself. */
export function DeskDeleteHost() {
  const { remove, receipt } = useUndoReceipt();

  useEffect(() => {
    publish(receipt);
  }, [receipt]);

  useEffect(() => () => publish(null), []);

  useEffect(() => {
    const onDeleteRequest = (event: Event) => {
      const ref = (event as CustomEvent<{ ref?: string | null }>).detail?.ref;
      if (!ref) return;
      // Round two: no face shows the receipt, so no delete (UX-CANON A.11).
      if (!deleteSeatShown()) return;
      const desk = useDesk.getState();
      const object = objectByRef(desk.items, ref);
      if (!object) return;
      const qualified = qualifiedRef(object.kind, object.id);
      desk.setSelected(
        desk.selectedIds.filter(
          (id) => id !== ref && id !== qualified && id !== object.id,
        ),
      );
      // Keyed by the object: a repeated Delete never opens a second Undo.
      remove(
        object.title,
        () => useDesk.getState().deletePrimitive(object.id, object.kind),
        () => undefined,
        qualified,
      );
    };
    window.addEventListener(OBJECT_DELETE_REQUEST, onDeleteRequest);
    return () => window.removeEventListener(OBJECT_DELETE_REQUEST, onDeleteRequest);
  }, [remove]);

  return null;
}

/** The receipt, where a face seats it. */
export function DeskDeleteSeat() {
  const node = useSyncExternalStore(subscribe, () => current);
  useEffect(() => {
    seatMounted();
    return () => {
      seatUnmounted();
    };
  }, []);
  return <>{node}</>;
}
