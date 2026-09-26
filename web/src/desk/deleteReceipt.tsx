/** PHILO-8-02 — one delete everywhere.
 *
 * `object.delete` is hook-free: it dispatches `OBJECT_DELETE_REQUEST`
 * (`verbRegistry.ts`). This module holds the ONE listener and the ONE
 * undo receipt for it. `DeskDeleteHost` mounts once, in `DeskApp`, so it
 * survives every face change; each face that shows the receipt (the
 * spatial Floor and the list) places `DeskDeleteSeat` in its foot, directly
 * above its AskBar (the seat the owner ratified in #665).
 *
 * The rules (the Astra-role ruling, phase 8 story 02):
 * - the queued object leaves the selection, so the next select-and-Delete
 *   targets only the next object;
 * - a second delete commits the first at once (the receipt keeps one slot);
 * - a face change (Chair/Floor, list/spatial) commits a pending delete (it
 *   was queued on a face that showed its receipt). The face is read from the
 *   face state itself, never from a seat unmounting: a seat that unmounts
 *   for another reason (a failed refresh redraws the desk) keeps the Undo;
 * - where no seat is mounted (the Chair) the delete is WITHHELD: the verb is
 *   greyed with its reason (`verbRegistry.ts`) and nothing is deleted.
 */
import { useEffect, useRef, useSyncExternalStore, type ReactNode } from "react";
import { useDesk } from "./store";
import { useChairState } from "./chairState";
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
  const { remove, flush, receipt } = useUndoReceipt();

  // A face change commits a pending delete. The first run is the mount.
  const surface = useChairState((s) => s.surface);
  const viewMode = useDesk((s) => s.viewMode);
  const face = `${surface}:${viewMode}`;
  const faceRef = useRef(face);
  useEffect(() => {
    if (faceRef.current === face) return;
    faceRef.current = face;
    flush();
  }, [face, flush]);

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
      remove(
        object.title,
        () => void useDesk.getState().deletePrimitive(object.id, object.kind),
        () => undefined,
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
