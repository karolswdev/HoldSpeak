import { useCallback, type SetStateAction } from "react";
import { create } from "zustand";
import type { ResolvedRef } from "../lib/drawerResolver";

interface ComposerDraft {
  text: string;
  chips: Array<{ ref: ResolvedRef }>;
  sending: boolean;
}

const EMPTY_DRAFT: ComposerDraft = { text: "", chips: [], sending: false };

// The Chair/Floor switch can remount windows. Keep unsent work and an active
// submission in the current browser session, keyed to its Thread.
export const useThreadComposerDrafts = create<{ drafts: Record<string, ComposerDraft> }>(() => ({ drafts: {} }));

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
