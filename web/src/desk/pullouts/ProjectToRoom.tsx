/** W1-DOORS (atlas 2026-10-27, Part B): a Project opens in its Room. A
 * `pullout:project:<id>` window (a restored desk, an older hub row) opens the
 * Room scoped `project:<id>`, as the floor icon does, and closes itself. The
 * hub opens the Room in place of the pullout (desk_window_service
 * `canonical_open`); this keeps an old row honest. Before, the window said
 * "No detail view for project". */
import { useEffect } from "react";
import { useDesk } from "../store";
import type { PulloutContentProps } from "./types";

export function ProjectToRoom({ object, onClose }: PulloutContentProps) {
  useEffect(() => {
    useDesk.getState().openPullout(`project:${object.id}`);
    onClose();
  }, [object.id, onClose]);
  return null;
}
