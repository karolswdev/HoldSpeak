import { useCallback, type SetStateAction } from "react";
import { create } from "zustand";
import type { ResolvedRef } from "../lib/drawerResolver";

interface ComposerDraft {
  text: string;
  chips: Array<{ ref: ResolvedRef }>;
  sending: boolean;
}

type DraftMap = Record<string, ComposerDraft>;

const EMPTY_DRAFT: ComposerDraft = { text: "", chips: [], sending: false };

/* HS-200-41 AC4 — the draft survives a reload and a crash restore.
 *
 * The store is sessionStorage, never localStorage: a draft can hold
 * dictated meeting material (ThreadComposer's handleMicText), so session
 * scope is the custody rule — it survives the reload and the crash
 * restore the design was about and dies with the tab, so an orphaned
 * draft holding meeting content cannot sit on disk unattended. Expiry
 * and multi-tab collision never arise for the same reason.
 *
 * Every access is wrapped: a browser that refuses storage renders with
 * no draft rather than failing. */
const STORAGE_KEY = "hs.threadComposerDrafts";

function session(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.sessionStorage;
  } catch {
    return null;
  }
}

/** Persisted shape: text + chips only, and never an in-flight send. */
function durable(drafts: DraftMap): DraftMap {
  const out: DraftMap = {};
  for (const [threadId, draft] of Object.entries(drafts)) {
    if (!draft.text && !draft.chips.length) continue;
    out[threadId] = { text: draft.text, chips: draft.chips, sending: false };
  }
  return out;
}

function isChip(value: unknown): value is { ref: ResolvedRef } {
  const ref = (value as { ref?: unknown } | null)?.ref as ResolvedRef | undefined;
  return !!ref && typeof ref.name === "string" && typeof ref.id === "string"
    && typeof ref.ref === "string" && typeof ref.kind === "string";
}

function loadDrafts(): DraftMap {
  const store = session();
  if (!store) return {};
  try {
    const raw = store.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
    const out: DraftMap = {};
    for (const [threadId, value] of Object.entries(parsed as Record<string, unknown>)) {
      const stored = value as { text?: unknown; chips?: unknown } | null;
      const text = typeof stored?.text === "string" ? stored.text : "";
      const chips = Array.isArray(stored?.chips) ? stored.chips.filter(isChip) : [];
      if (!text && !chips.length) continue;
      // `sending` is never rehydrated: the reload killed the request, and a
      // stored `true` would leave the composer disabled forever.
      out[threadId] = { text, chips, sending: false };
    }
    return out;
  } catch {
    return {};
  }
}

function persistDrafts(drafts: DraftMap): void {
  const store = session();
  if (!store) return;
  try {
    const keep = durable(drafts);
    if (!Object.keys(keep).length) store.removeItem(STORAGE_KEY);
    else store.setItem(STORAGE_KEY, JSON.stringify(keep));
  } catch {
    // Persistence is an enhancement; refused storage must not block typing.
  }
}

// The Chair/Floor switch can remount windows. Keep unsent work and an active
// submission in the current browser session, keyed to its Thread.
export const useThreadComposerDrafts = create<{ drafts: DraftMap }>(() => ({ drafts: loadDrafts() }));

useThreadComposerDrafts.subscribe((state) => persistDrafts(state.drafts));

export function clearThreadComposerDraft(threadId: string): void {
  useThreadComposerDrafts.setState((s) => {
    const drafts = { ...s.drafts };
    delete drafts[threadId];
    return { drafts };
  });
}

function updateField<K extends keyof ComposerDraft>(threadId: string, key: K, next: SetStateAction<ComposerDraft[K]>): void {
  useThreadComposerDrafts.setState((s) => {
    const current = s.drafts[threadId] ?? EMPTY_DRAFT;
    const value = typeof next === "function"
      ? (next as (value: ComposerDraft[K]) => ComposerDraft[K])(current[key])
      : next;
    const draft = { ...current, [key]: value };
    const drafts = { ...s.drafts };
    if (!draft.text && !draft.chips.length && !draft.sending) delete drafts[threadId];
    else drafts[threadId] = draft;
    return { drafts };
  });
}

export function useThreadComposerDraft(threadId: string) {
  const state = useThreadComposerDrafts((s) => s.drafts[threadId] ?? EMPTY_DRAFT);
  const setDraft = useCallback((value: SetStateAction<string>) => updateField(threadId, "text", value), [threadId]);
  const setChips = useCallback((value: SetStateAction<ComposerDraft["chips"]>) => updateField(threadId, "chips", value), [threadId]);
  const setSending = useCallback((value: SetStateAction<boolean>) => updateField(threadId, "sending", value), [threadId]);
  return { draft: state.text, chips: state.chips, sending: state.sending, setDraft, setChips, setSending };
}
