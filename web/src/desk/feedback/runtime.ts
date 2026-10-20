import { useSyncExternalStore } from "react";
import { apiFetch } from "../../lib/api";

export interface UiFeedbackStatus {
  enabled: boolean;
}

let state = { enabled: false, loading: true };
const SERVER_STATE = { enabled: false, loading: true };
let attempted = false;
const listeners = new Set<() => void>();
let launcher: (() => void) | null = null;

function notify(): void {
  listeners.forEach((listener) => listener());
}

export function subscribeUiFeedback(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function uiFeedbackState(): { enabled: boolean; loading: boolean } {
  return state;
}

export function useUiFeedbackState(): { enabled: boolean; loading: boolean } {
  return useSyncExternalStore(
    subscribeUiFeedback,
    uiFeedbackState,
    () => SERVER_STATE,
  );
}

/** Read the server runtime flag once. A missing route is the normal disabled state. */
export async function hydrateUiFeedback(): Promise<void> {
  if (attempted) return;
  attempted = true;
  try {
    const status = await apiFetch<UiFeedbackStatus>("/api/ui-feedback/status");
    state = { enabled: status?.enabled === true, loading: false };
  } catch {
    state = { enabled: false, loading: false };
  } finally {
    if (state.loading) state = { ...state, loading: false };
    notify();
  }
}

export function uiFeedbackGhost(): string | null {
  return state.enabled ? null : "Feedback is unavailable";
}

export function bindUiFeedbackLauncher(next: (() => void) | null): () => void {
  launcher = next;
  return () => {
    if (launcher === next) launcher = null;
  };
}

export function requestUiFeedback(): void {
  launcher?.();
}

export function resetUiFeedbackRuntimeForTests(): void {
  state = SERVER_STATE;
  attempted = false;
  notify();
}
