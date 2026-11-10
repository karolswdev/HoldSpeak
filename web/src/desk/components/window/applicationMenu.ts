// List verbs belong to the app menu. Help belongs to Help.
import { DESK_APPLICATIONS } from "../../applications";
import { useListMenu, useWindowWalk } from "./listMenu";
export function useApplicationMenu(windowId: string | null, name?: string) {
  const entries = useListMenu(windowId);
  const declared = useWindowWalk(windowId) ?? windowId;
  const app = DESK_APPLICATIONS.find(
    (row) => row.windowId === declared || row.action === declared,
  );
  return { label: app?.label ?? name ?? "Application", entries, failed: false };
}
