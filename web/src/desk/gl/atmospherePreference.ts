import { useCallback, useEffect, useState } from "react";
import {
  DEFAULT_ATMOSPHERE_ID,
  isAtmosphereId,
  type AtmosphereId,
} from "./atmosphereRegistry";

export const ATMOSPHERE_STORAGE_KEY = "hs.desk.atmosphere";
export const ATMOSPHERE_PREFERENCE_EVENT = "holdspeak:atmosphere-preference";

type PreferenceStorage = Pick<Storage, "getItem" | "setItem">;

function browserStorage(): PreferenceStorage | undefined {
  if (typeof window === "undefined") return undefined;
  try {
    return window.localStorage;
  } catch {
    return undefined;
  }
}

export function readAtmospherePreference(
  storage: Pick<PreferenceStorage, "getItem"> | undefined = browserStorage(),
): AtmosphereId {
  try {
    const saved = storage?.getItem(ATMOSPHERE_STORAGE_KEY);
    return saved && isAtmosphereId(saved) ? saved : DEFAULT_ATMOSPHERE_ID;
  } catch {
    return DEFAULT_ATMOSPHERE_ID;
  }
}

export function persistAtmospherePreference(
  id: AtmosphereId,
  storage: Pick<PreferenceStorage, "setItem"> | undefined = browserStorage(),
): void {
  try {
    storage?.setItem(ATMOSPHERE_STORAGE_KEY, id);
  } catch {
    // The live selection still works; this browser simply cannot retain it.
  }
}

/** One view preference shared by the Settings picker and the lazy Floor host.
 * The custom event covers same-tab changes; `storage` covers other tabs. */
export function useAtmospherePreference(): readonly [
  AtmosphereId,
  (id: AtmosphereId) => void,
] {
  const [id, setId] = useState<AtmosphereId>(readAtmospherePreference);

  useEffect(() => {
    const syncStoredPreference = () => setId(readAtmospherePreference());
    const syncLivePreference = (event: Event) => {
      const next = (event as CustomEvent<{ id?: string }>).detail?.id;
      setId(next && isAtmosphereId(next) ? next : readAtmospherePreference());
    };
    window.addEventListener("storage", syncStoredPreference);
    window.addEventListener(ATMOSPHERE_PREFERENCE_EVENT, syncLivePreference);
    return () => {
      window.removeEventListener("storage", syncStoredPreference);
      window.removeEventListener(
        ATMOSPHERE_PREFERENCE_EVENT,
        syncLivePreference,
      );
    };
  }, []);

  const select = useCallback((next: AtmosphereId) => {
    persistAtmospherePreference(next);
    setId(next);
    window.dispatchEvent(
      new CustomEvent(ATMOSPHERE_PREFERENCE_EVENT, {
        detail: { id: next },
      }),
    );
  }, []);

  return [id, select] as const;
}
