/** Debounced save for inline editors (HS-117-15). */
import { useRef } from "react";
import { useDesk } from "../../store";

export function useDebouncedSave(kind: string, id: string) {
  const { updatePrimitive } = useDesk.getState();
  const timer = useRef<number | null>(null);
  const pending = useRef<Record<string, unknown>>({});
  return (patch: Record<string, unknown>) => {
    pending.current = { ...pending.current, ...patch };
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => {
      const body = pending.current;
      pending.current = {};
      void updatePrimitive(kind, id, body);
    }, 450);
  };
}
