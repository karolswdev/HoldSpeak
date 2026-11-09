/** PHILO-16 (16b) — the mount point of the hub's windows: seed on load,
 * follow the hub's `desk_changed` frames of kind `windows`. One display
 * protocol (2026-11-08): it also runs the hub's display requests
 * (`DeskRequests`, the `desk_request` frame). Without a bus (a component
 * test) it seeds and does not follow. */
import { useEffect } from "react";
import { useBusSubscribe } from "../useDeskChangedRefresh";
import { DeskRequests } from "./DeskRequests";
import { hubWindows } from "./hubWindows";

export function HubWindowsSync() {
  const subscribe = useBusSubscribe();
  useEffect(() => {
    const hub = hubWindows();
    void hub.start();
    if (!subscribe) return;
    // The bus hands a windows-only `desk_changed` frame to "*" listeners only.
    const unsubscribe = subscribe("*", (frame) => {
      if (frame.type === "desk_changed") hub.onFrame(frame.data);
    });
    return () => {
      if (typeof unsubscribe === "function") unsubscribe();
    };
  }, [subscribe]);
  return <DeskRequests />;
}
