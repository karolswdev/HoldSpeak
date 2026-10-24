import { forgetDraft, keepDraft, keptDraft } from "../deskMemory";
import { useDesk } from "../store";
import type { DeskEditorHandle } from "../components/DeskEditor";

/** Thought-only persistence seam. A reference fixture can supply local memory. */
export interface ThoughtVoiceDraftIO {
  get(key: string): string | null;
  keep(key: string, text: string): void;
  forget(key: string): void;
  subscribe(listener: () => void): () => void;
}

export const deskThoughtVoiceDraft: ThoughtVoiceDraftIO = {
  get: keptDraft,
  keep: keepDraft,
  forget: forgetDraft,
  subscribe: (listener) => useDesk.subscribe(listener),
};

export function thoughtVoiceKey(noteId: string): string {
  return `thought/voice/${noteId}`;
}

/** Synchronous read-modify-write keeps results from separate captures. */
export function retainThoughtVoice(io: ThoughtVoiceDraftIO, noteId: string, text: string): void {
  const key = thoughtVoiceKey(noteId);
  const prior = io.get(key);
  io.keep(key, prior ? `${prior}\n\n${text}` : text);
}

/** Bind the active Thought's actual editor before focus or transcription can move. */
export function bindThoughtVoiceTarget(
  noteId: string | undefined,
  editor: DeskEditorHandle | null,
  isCurrent: () => boolean,
  io: ThoughtVoiceDraftIO,
): (text: string) => void {
  const target = editor?.captureVoiceTarget() ?? null;
  return (text) => {
    if (editor && target && isCurrent() && editor.insertAtCapturedTarget(target, text)) return;
    if (noteId) retainThoughtVoice(io, noteId, text);
  };
}
