import { useSyncExternalStore } from "react";

export const ATMOSPHERE_SOUND_KEY = "hs.desk.atmosphere.sound";
export const ATMOSPHERE_MOTION_KEY = "hs.desk.atmosphere.motion";
const eventName = "holdspeak:atmosphere-controls";
const local: Record<string, boolean> = {};

function read(key: string, fallback: boolean): boolean {
  if (key in local) return local[key];
  try {
    const saved = localStorage.getItem(key);
    return saved === null ? fallback : saved === "true";
  } catch {
    return fallback;
  }
}

function subscribe(listener: () => void) {
  const syncStorage = () => {
    delete local[ATMOSPHERE_SOUND_KEY];
    delete local[ATMOSPHERE_MOTION_KEY];
    listener();
  };
  window.addEventListener(eventName, listener);
  window.addEventListener("storage", syncStorage);
  return () => {
    window.removeEventListener(eventName, listener);
    window.removeEventListener("storage", syncStorage);
  };
}

function write(key: string, value: boolean) {
  local[key] = value;
  try {
    localStorage.setItem(key, String(value));
  } catch {
    /* Live choice remains available. */
  }
  window.dispatchEvent(new Event(eventName));
}

export function useAtmosphereControls() {
  const sound = useSyncExternalStore(
    subscribe,
    () => read(ATMOSPHERE_SOUND_KEY, false),
    () => false,
  );
  const motion = useSyncExternalStore(
    subscribe,
    () => read(ATMOSPHERE_MOTION_KEY, true),
    () => true,
  );
  return {
    sound,
    motion,
    setSound: (value: boolean) => write(ATMOSPHERE_SOUND_KEY, value),
    setMotion: (value: boolean) => write(ATMOSPHERE_MOTION_KEY, value),
  };
}
