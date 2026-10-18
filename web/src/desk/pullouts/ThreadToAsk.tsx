/** Betterment Q4: Ask and Thread are one window. A `pullout:thread:<id>`
 * window (a restored desk, a hub-owned window, an agent's open) opens that
 * thread in Ask and closes itself. The Thread window is parked
 * (`_parked/ThreadPullout.tsx`). */
import { useEffect } from "react";
import { useDesk } from "../store";
import type { PulloutContentProps } from "./types";

export function ThreadToAsk({ object, onClose }: PulloutContentProps) {
  useEffect(() => {
    useDesk.getState().openAskThread(object.id);
    onClose();
  }, [object.id, onClose]);
  return null;
}
