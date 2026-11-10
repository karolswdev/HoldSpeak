// Compatibility declaration for app hosts. The menu bar owns the verb.
import { useEffect, useId, useState } from "react";
import { useWindowId } from "../components/window/windowIdContext";
import { publishWindowWalk, clearWindowWalk } from "../components/window/listMenu";
import { useCompactViewport } from "../useCompactViewport";
import { appWalk, startAppWalk } from "./appWalks";
export const SHOW_ME = "Show me";
export function useShowMe(app: string) {
  const origin = useWindowId();
  const owner = useId();
  const compact = useCompactViewport();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const declared = Boolean(appWalk(app));
  useEffect(() => {
    if (!origin || !declared) return;
    publishWindowWalk(origin, owner, app);
    return () => clearWindowWalk(origin, owner);
  }, [origin, owner, app, declared]);
  const start = () => {
    if (busy) return;
    setBusy(true); setFailed(false);
    startAppWalk(app, origin).catch(() => setFailed(true)).finally(() => setBusy(false));
  };
  return { declared, compact, busy, failed, start, entry: null };
}
export function ShowMe({ app }: { app: string; inMore?: boolean }) {
  useShowMe(app);
  return null;
}
