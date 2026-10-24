import { useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { ThoughtDocumentPane } from "../../../desk/thought-workspace/ThoughtDocumentPane";
import { thoughtVoiceKey, type ThoughtVoiceDraftIO } from "../../../desk/thought-workspace/thoughtVoiceDraft";
import type { ThoughtDraft } from "../../../desk/pullouts/editors/useThoughtNoteWriter";
import { StateChip } from "../../../desk/surface";
import "../../../desk/thought-workspace/thought-workspace.css";

export type EditingPreset = "ordinary" | "retained" | "newer" | "read-only" | "linked";

const NOTE_ID = "components-editing-specimen";
const SAMPLE_WORDS = "Confirm the boundary before rollout.";
const BASE_BODY = "Review the source before rollout.";

function localVoiceDraftIO(initialWords: string | null): ThoughtVoiceDraftIO {
  const values = new Map<string, string>();
  if (initialWords) values.set(thoughtVoiceKey(NOTE_ID), initialWords);
  const listeners = new Set<() => void>();
  const changed = () => listeners.forEach((listener) => listener());
  return {
    get: (key) => values.get(key) ?? null,
    keep: (key, text) => { values.set(key, text); changed(); },
    forget: (key) => { values.delete(key); changed(); },
    subscribe: (listener) => { listeners.add(listener); return () => { listeners.delete(listener); }; },
  };
}

/** Components uses the live Thought document and voice binder with window-local data. */
export function EditingReference({ preset }: { preset: EditingPreset }) {
  const readOnly = preset === "read-only";
  const [draft, setDraft] = useState<ThoughtDraft>(() => ({
    title: "Release review",
    body: preset === "newer" ? `${BASE_BODY}\nNewer local edit.` : preset === "linked"
      ? `${BASE_BODY}\n\nLooked at: [API boundary](note:sample-source)\n\nFrom: [Ask thread](thread:sample-ask)` : BASE_BODY,
    tags: "",
  }));
  const [voiceDraftIO] = useState(() => localVoiceDraftIO(
    preset === "retained" || preset === "newer" || readOnly ? SAMPLE_WORDS : null,
  ));
  const delivery = useRef<((text: string) => void) | null>(null);
  const [captured, setCaptured] = useState(false);
  const [openedLink, setOpenedLink] = useState<string | null>(null);

  return <section className="reference-example reference-editing" data-testid="reference-editing" aria-label="Editing pattern">
    <div className="reference-example-head">
      <div><h2>Thought note</h2></div>
      <StateChip state={readOnly ? "idle" : "active"} label={readOnly ? "READ ONLY" : "LOCAL SPECIMEN"} />
    </div>
    <div className="reference-editing-document">
      <ThoughtDocumentPane
        noteId={NOTE_ID}
        draft={draft}
        onEdit={(patch) => setDraft((current) => ({ ...current, ...patch }))}
        disabled={readOnly}
        lockedReason={readOnly ? "Read only" : undefined}
        voiceDraftIO={voiceDraftIO}
        onOpenLink={setOpenedLink}
        mic={false}
        voiceInput={(bindText, disabled) => <Button dense variant="ghost" disabled={disabled}
          onClick={() => { delivery.current = bindText(); setCaptured(true); }}>Capture target</Button>}
      />
    </div>
    {openedLink ? <div role="status" className="reference-actions">Opened locally: {openedLink}</div> : null}
    {captured ? <div className="reference-actions">
      <Button dense variant="primary" onClick={() => {
        const deliver = delivery.current;
        delivery.current = null;
        setCaptured(false);
        deliver?.(SAMPLE_WORDS);
      }}>Deliver local text</Button>
    </div> : null}
  </section>;
}
