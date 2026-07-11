import { useCallback, useEffect, useState, type SetStateAction } from "react";

const VERSION = 1;
const PREFIX = "hs.draft.v1.";

export interface DurableDraftRecord {
  version: 1;
  text: string;
  updatedAt: string;
}

function storage(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.localStorage;
  } catch {
    return null;
  }
}

export function durableDraftKey(scope: string): string {
  return `${PREFIX}${encodeURIComponent(scope.trim() || "default")}`;
}

export function readDurableDraft(scope: string): DurableDraftRecord | null {
  try {
    const raw = storage()?.getItem(durableDraftKey(scope));
    if (!raw) return null;
    const value = JSON.parse(raw) as Partial<DurableDraftRecord>;
    if (value.version !== VERSION || typeof value.text !== "string")
      return null;
    return {
      version: VERSION,
      text: value.text,
      updatedAt: String(value.updatedAt || ""),
    };
  } catch {
    return null;
  }
}

export function writeDurableDraft(scope: string, text: string): void {
  try {
    const target = storage();
    if (!target) return;
    if (!text) {
      target.removeItem(durableDraftKey(scope));
      return;
    }
    const record: DurableDraftRecord = {
      version: VERSION,
      text,
      updatedAt: new Date().toISOString(),
    };
    target.setItem(durableDraftKey(scope), JSON.stringify(record));
  } catch {
    // Storage can be disabled or full. The live editor remains authoritative.
  }
}

export function clearDurableDraft(scope: string): void {
  try {
    storage()?.removeItem(durableDraftKey(scope));
  } catch {
    // The caller still retains its live value.
  }
}

/**
 * A tiny device-local draft primitive. Every change is persisted synchronously,
 * so a background/suspend event does not have to win a race with an effect.
 */
export function useDurableDraft(scope: string, fallback = "") {
  const initial = readDurableDraft(scope);
  const [value, setValue] = useState(initial?.text ?? fallback);
  const [recovered, setRecovered] = useState(Boolean(initial?.text));

  useEffect(() => {
    const next = readDurableDraft(scope);
    setValue(next?.text ?? fallback);
    setRecovered(Boolean(next?.text));
  }, [scope, fallback]);

  const setDraft = useCallback(
    (next: SetStateAction<string>) => {
      setValue((current) => {
        const resolved = typeof next === "function" ? next(current) : next;
        writeDurableDraft(scope, resolved);
        return resolved;
      });
      setRecovered(false);
    },
    [scope],
  );

  const clearPersisted = useCallback(() => {
    clearDurableDraft(scope);
    setRecovered(false);
  }, [scope]);

  return { value, setDraft, recovered, clearPersisted };
}
