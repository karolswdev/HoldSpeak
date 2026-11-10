const KEY = "hs:walk-voice";
const listeners = new Set<() => void>();
export function guideVoice(): boolean {
  try {
    return localStorage.getItem(KEY) === "on";
  } catch {
    return false;
  }
}
export function setGuideVoice(on: boolean): void {
  try {
    localStorage.setItem(KEY, on ? "on" : "off");
  } catch {
    /* local choice */
  }
  listeners.forEach((fn) => fn());
}
export function subscribeGuideVoice(fn: () => void): () => void {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}
