const STORAGE_KEY = "holdspeak.ambient.attention.dismissed-through";
let memoryCutoff = 0;

/** Popup presentation only. The Attention reader keeps its source rows. */
export function readAttentionPopupCutoff(): number {
  try {
    const stored = Number(window.sessionStorage.getItem(STORAGE_KEY));
    if (Number.isFinite(stored) && stored > memoryCutoff) memoryCutoff = stored;
  } catch {
    // Storage can be denied; retain this tab's in-memory dismissal.
  }
  return memoryCutoff;
}

export function recordAttentionPopupCutoff(timestamp: number): number {
  memoryCutoff = Math.max(readAttentionPopupCutoff(), timestamp);
  try {
    window.sessionStorage.setItem(STORAGE_KEY, String(memoryCutoff));
  } catch {
    // Remounts still read memory when the browser refuses session storage.
  }
  return memoryCutoff;
}
