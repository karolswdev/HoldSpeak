import { useMemo, useSyncExternalStore } from "react";
import { isAtmosphereId, type AtmosphereId } from "./atmosphereRegistry";

export const ATMOSPHERE_FAVORITES_KEY = "hs.desk.atmosphere.favorites";
const changed = "holdspeak:atmosphere-favorites";
let volatile: string | undefined;
function snapshot() {
  if (volatile !== undefined) return volatile;
  try {
    return localStorage.getItem(ATMOSPHERE_FAVORITES_KEY) ?? "[]";
  } catch {
    return "[]";
  }
}
export function parseAtmosphereFavorites(raw: string): AtmosphereId[] {
  try {
    const value: unknown = JSON.parse(raw);
    return Array.isArray(value)
      ? [
          ...new Set(
            value.filter(
              (id): id is AtmosphereId =>
                typeof id === "string" && isAtmosphereId(id),
            ),
          ),
        ]
      : [];
  } catch {
    return [];
  }
}
function subscribe(listener: () => void) {
  const storage = (event: StorageEvent) => {
    if (event.key !== null && event.key !== ATMOSPHERE_FAVORITES_KEY) return;
    volatile = undefined;
    listener();
  };
  window.addEventListener(changed, listener);
  window.addEventListener("storage", storage);
  return () => {
    window.removeEventListener(changed, listener);
    window.removeEventListener("storage", storage);
  };
}
export function useAtmosphereFavorites() {
  const raw = useSyncExternalStore(subscribe, snapshot, () => "[]");
  const favorites = useMemo(() => parseAtmosphereFavorites(raw), [raw]);
  const toggle = (id: AtmosphereId) => {
    const current = parseAtmosphereFavorites(snapshot());
    const next = current.includes(id)
      ? current.filter((entry) => entry !== id)
      : [...current, id];
    const rawNext = JSON.stringify(next);
    try {
      localStorage.setItem(ATMOSPHERE_FAVORITES_KEY, rawNext);
      volatile = undefined;
    } catch {
      volatile = rawNext;
    }
    window.dispatchEvent(new Event(changed));
  };
  return { favorites, toggle };
}
