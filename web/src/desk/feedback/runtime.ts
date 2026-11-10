import { useSyncExternalStore } from "react";
import { apiFetch } from "../../lib/api";

export interface UiFeedbackStatus {
  enabled: boolean;
  transcription_egress?: Array<{label:string;boundary:string}>;
}

type State = UiFeedbackStatus & {loading:boolean};
let state: State = { enabled: false, loading: true };
const SERVER_STATE = { enabled: false, loading: true };
let attempted = false;
const listeners = new Set<() => void>();
export interface GuideFeedbackContext {app:string;step:number;of:number;target:string;words:string}
export interface FeedbackRequest {guide?:GuideFeedbackContext;mount?:HTMLElement;onFinish?:(saved:boolean)=>void;signal?:AbortSignal}
let launcher: ((target?: Element, request?: FeedbackRequest) => void) | null = null;

function notify(): void {
  listeners.forEach((listener) => listener());
}

export function subscribeUiFeedback(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function uiFeedbackState(): State {
  return state;
}

export function useUiFeedbackState(): State {
  return useSyncExternalStore(
    subscribeUiFeedback,
    uiFeedbackState,
    () => SERVER_STATE,
  );
}

/** Read the flag and owner speech disclosure. Record refreshes the current chain. */
export async function hydrateUiFeedback(refresh = false): Promise<void> {
  if (attempted && !refresh) return;
  attempted = true;
  try {
    const status = await apiFetch<UiFeedbackStatus>("/api/ui-feedback/status");
    state = { enabled: status?.enabled === true, loading: false, transcription_egress: status?.transcription_egress };
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

export function bindUiFeedbackLauncher(next: ((target?: Element, request?: FeedbackRequest) => void) | null): () => void {
  launcher = next;
  return () => {
    if (launcher === next) launcher = null;
  };
}

export function requestUiFeedback(target?: Element, request?: FeedbackRequest): void {
  if (state.enabled) launcher?.(target,request);
}

export function resetUiFeedbackRuntimeForTests(): void {
  state = SERVER_STATE;
  attempted = false;
  notify();
}
