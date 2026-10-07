/** PHILO-14 C3 — the drag grammar, as DeskIcon props.
 *
 *  HTML drag and drop (the DeskIcon species carries `draggable` and the
 *  drag events). The browser's own drag image is blanked: the DragLayer
 *  draws the ghost and the dotted path. A drop on anything that is not a
 *  target does nothing: the ghost goes, the source returns to rest. */
import type { DragEvent } from "react";
import type { HandOrigin } from "../agentHand";
import { beginHand, agentOfTarget } from "./begin";
import { useDropHand, type HandEnd } from "./store";

/** The drag's data type: a drag from elsewhere (a file, a link) is not a hand. */
export const HAND_MIME = "application/x-holdspeak-hand";

let blank: HTMLImageElement | null = null;
function blankImage(): HTMLImageElement | null {
  if (blank || typeof Image === "undefined") return blank;
  blank = new Image();
  blank.src = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7";
  return blank;
}

type IconDrag = DragEvent<HTMLButtonElement>;

export function handSourceProps(args: { origin: HandOrigin; source: HandEnd; host: string }) {
  return {
    draggable: true,
    onDragStart: (event: IconDrag) => {
      const data = event.dataTransfer;
      if (data) {
        data.setData(HAND_MIME, `${args.origin.kind}:${args.origin.id}`);
        data.effectAllowed = "copy";
        const image = blankImage();
        if (image && typeof data.setDragImage === "function") data.setDragImage(image, 0, 0);
      }
      const box = event.currentTarget.getBoundingClientRect();
      useDropHand.getState().startDrag({
        origin: args.origin,
        source: args.source,
        host: args.host,
        from: { x: box.left + box.width / 2, y: box.top + box.height / 2 },
      });
    },
    onDragEnd: () => useDropHand.getState().endDrag(),
  };
}

/** The drop-target props of the icon `key` (the Conductor drawer, an agent),
 *  or an empty object when `key` is no target. */
export function handTargetProps(key: string) {
  const agent = agentOfTarget(key);
  if (!agent) return {};
  return {
    onDragOver: (event: IconDrag) => {
      if (!useDropHand.getState().drag) return;
      event.preventDefault();
      if (event.dataTransfer) event.dataTransfer.dropEffect = "copy";
      useDropHand.getState().setOver(key);
    },
    onDragLeave: () => useDropHand.getState().leave(key),
    onDrop: (event: IconDrag) => {
      const drag = useDropHand.getState().drag;
      if (!drag) return;
      event.preventDefault();
      useDropHand.getState().endDrag();
      void beginHand(drag.origin, { agent, host: drag.host, source: drag.source });
    },
  };
}
