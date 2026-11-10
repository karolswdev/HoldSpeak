// The same app entries feed the desktop title and the phone window menu.
import { useEffect, useState } from "react";
import { DESK_APPLICATIONS } from "../../applications";
import { appWalk, startAppWalk } from "../../walk/appWalks";
import type { WorkMenuEntry } from "../DeskMenu";
import { useListMenu, useWindowWalk } from "./listMenu";

export function useApplicationMenu(windowId: string | null, name?: string) {
  const verbs = useListMenu(windowId);
  const declaredApp = useWindowWalk(windowId) ?? windowId;
  const app = DESK_APPLICATIONS.find((entry) => entry.windowId === declaredApp || entry.action === declaredApp);
  const walk = appWalk(declaredApp);
  const [failed, setFailed] = useState(false);
  const [busy, setBusy] = useState(false);
  useEffect(() => { setFailed(false); }, [windowId]);
  const label = app?.label ?? name ?? walk?.title ?? "Application";
  const entries: WorkMenuEntry[] = [...verbs, ...(verbs.length && walk ? [{ type: "sep" as const, id: "walk-sep" }] : []), ...(walk ? [{
    type: "item" as const, id: "show-me", label: "Show me", disabled: busy, onSelect: () => {
      setBusy(true); setFailed(false);
      startAppWalk(declaredApp!, windowId).catch(() => setFailed(true)).finally(() => setBusy(false));
    },
  }] : [])];
  return { label, entries, failed };
}
