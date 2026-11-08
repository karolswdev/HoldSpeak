/** The one decision face (2026-11-08): a Desk decision opens its record in
 * the Decisions window reader (`openDeskDecisionRecord`). A
 * `pullout:decision:<id>` window (a restored desk, a hub window row) opens the
 * reader and closes itself. The Decision pullout is parked
 * (`_parked/DecisionPullout.tsx`). */
import { useEffect } from "react";
import { openDeskDecisionRecord } from "../openObject";
import type { PulloutContentProps } from "./types";

export function DecisionToReader({ object, onClose }: PulloutContentProps) {
  useEffect(() => {
    openDeskDecisionRecord(object.id);
    onClose();
  }, [object.id, onClose]);
  return null;
}
