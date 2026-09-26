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
 * - when the last seat unmounts (a face change), a pending delete commits;
 *   a delete asked for where no seat is mounted commits at once.
 */
import { useEffect, useSyncExternalStore, type ReactNode } from "react";
import { useDesk } from "./store";
import { qualifiedRef } from "./api";
import { OBJECT_DELETE_REQUEST } from "./verbRegistry";
import { objectByRef } from "./world";
import { useUndoReceipt } from "./hooks/useUndoReceipt";

let current: ReactNode = null;
let seats = 0;
let flushPending: () => void = () => undefined;
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

  useEffect(() => {
    flushPending = flush;
  }, [flush]);

  useEffect(() => {
    publish(receipt);
  }, [receipt]);

  useEffect(() => () => publish(null), []);

  useEffect(() => {
    const onDeleteRequest = (event: Event) => {
      const ref = (event as CustomEvent<{ ref?: string | null }>).detail?.ref;
      if (!ref) return;
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
      // No face seats the receipt (the Chair with a selection left from the
      // Floor): no Undo is in reach, so the delete commits at once.
      if (seats === 0) flush();
    };
    window.addEventListener(OBJECT_DELETE_REQUEST, onDeleteRequest);
    return () => window.removeEventListener(OBJECT_DELETE_REQUEST, onDeleteRequest);
  }, [remove, flush]);

  return null;
}

/** The receipt, where a face seats it. */
export function DeskDeleteSeat() {
  const node = useSyncExternalStore(subscribe, () => current);
  useEffect(() => {
    seats += 1;
    return () => {
      seats -= 1;
      // A face change: no seat shows the receipt, so no Undo is in reach.
      if (seats === 0) flushPending();
    };
  }, []);
  return <>{node}</>;
}
