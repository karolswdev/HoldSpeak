/** PHILO-14 C3 — the drag on the glass: the ghost under the pointer and the
 *  dotted path back to the source (board A-3). Mounted once on the desk. */
import { useEffect } from "react";
import { DragGhost } from "../surface";
import { useDropHand } from "./store";

/** Half the ghost (64 px): the sprite is centred on the pointer. */
const HALF = 32;

export function DragLayer() {
  const drag = useDropHand((s) => s.drag);
  const dragging = drag !== null;
  useEffect(() => {
    if (!dragging) return;
    const move = (event: DragEvent) => {
      // The last dragover of some engines reports 0,0: keep the last point.
      if (event.clientX || event.clientY) useDropHand.getState().moveDrag({ x: event.clientX, y: event.clientY });
    };
    // A drag that ends where no handler sees it (the source left the glass).
    const end = () => useDropHand.getState().endDrag();
    document.addEventListener("dragover", move);
    document.addEventListener("dragend", end);
    document.addEventListener("drop", end);
    return () => {
      document.removeEventListener("dragover", move);
      document.removeEventListener("dragend", end);
      document.removeEventListener("drop", end);
    };
  }, [dragging]);
  if (!drag?.at) return null;
  return (
    <DragGhost
      kind={drag.source.kind}
      id={drag.source.id}
      sprite={drag.source.sprite}
      x={drag.at.x - HALF}
      y={drag.at.y - HALF}
      from={drag.from}
    />
  );
}
