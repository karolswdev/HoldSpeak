import { useEffect, useRef, type MouseEvent, type PointerEvent, type KeyboardEvent } from "react";

/** Shared activation guard: a multi-click or held key belongs to its saved target. A new
 * pointer press (outside a multi-click) or key press after release may act. */
export function useActivationGesture(revision: string | null, selector = "button", enabled = true) {
  const pointer = useRef<string | null>(null);
  const key = useRef<{word:string; revision:string | null} | null>(null);
  const current = useRef(revision); current.current = revision;
  useEffect(() => {
    if (!enabled) return;
    const released = (event: globalThis.KeyboardEvent) => {
      if (event.key === key.current?.word) queueMicrotask(() => {key.current = null;});
    };
    window.addEventListener("keyup", released, true);
    return () => window.removeEventListener("keyup", released, true);
  }, [enabled]);
  const button = (target: EventTarget) => target instanceof Element && target.closest(selector);
  const stop = (event: {preventDefault():void; stopPropagation():void}) => {event.preventDefault(); event.stopPropagation();};
  return {
    onPointerDownCapture(event: PointerEvent) {if (button(event.target)) pointer.current = current.current;},
    onKeyDownCapture(event: KeyboardEvent) {
      if (!button(event.target) || !["Enter", " "].includes(event.key)) return;
      if (event.repeat || key.current) {stop(event); if (!key.current) key.current={word:event.key, revision:null};}
      else key.current={word:event.key, revision:current.current};
    },
    onKeyUpCapture(event: KeyboardEvent) {
      if (button(event.target) && key.current && key.current.revision !== current.current) stop(event);
    },
    onClickCapture(event: MouseEvent) {
      if (!button(event.target)) return;
      if (event.detail > 1 || event.detail > 0 && pointer.current !== null && pointer.current !== current.current
        || event.detail === 0 && key.current && key.current.revision !== current.current) stop(event);
    },
  };
}
