import { useEffect, useRef, useState } from "react";
import { DeskEditor, type DeskEditorHandle } from "../components/DeskEditor";
import type { ThoughtDraft } from "../pullouts/editors/useThoughtNoteWriter";
import { originalThought, sourceLabel, type Thought } from "../thoughts";

export function ThoughtDocumentPane({
  draft,
  thoughtId,
  onEdit,
  disabled,
  message,
  onRetry,
  revealRange,
}: {
  draft: ThoughtDraft;
  thoughtId: string;
  onEdit: (patch: Partial<ThoughtDraft>) => void;
  disabled: boolean;
  message: string;
  onRetry: () => void;
  revealRange?: { start: number; end: number; focus?: boolean } | null;
}) {
  const bodyRef = useRef<DeskEditorHandle | null>(null);
  const [tagsOpen, setTagsOpen] = useState(false);
  const [original, setOriginal] = useState<Thought | null>(null);
  const [originalBusy, setOriginalBusy] = useState(false);
  const [originalError, setOriginalError] = useState("");
  const infoRef = useRef<HTMLButtonElement | null>(null);
  const originalRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!revealRange || !bodyRef.current) return;
    bodyRef.current.revealRange(revealRange.start, revealRange.end, { focus: revealRange.focus });
  }, [revealRange]);

  useEffect(() => {
    if (!original) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault(); event.stopPropagation();
      setOriginal(null);
      requestAnimationFrame(() => infoRef.current?.focus());
    };
    window.addEventListener("keydown", closeOnEscape, true);
    return () => window.removeEventListener("keydown", closeOnEscape, true);
  }, [original]);

  const showOriginal = async () => {
    if (originalBusy) return;
    if (original) { originalRef.current?.focus(); return; }
    setOriginalBusy(true); setOriginalError("");
    try {
      setOriginal(await originalThought(thoughtId));
      requestAnimationFrame(() => originalRef.current?.focus());
    } catch {
      setOriginalError("Could not open the original on this hub. The Note is unchanged.");
    } finally { setOriginalBusy(false); }
  };

  const tags = draft.tags.split(",").map((tag) => tag.trim()).filter(Boolean);
  return <section className="thought-document" aria-label="Note">
    <input
      className="thought-document-title"
      aria-label="Title"
      value={draft.title}
      disabled={disabled}
      onChange={(event) => onEdit({ title: event.target.value })}
    />
    <DeskEditor
      ref={bodyRef}
      className="thought-document-body"
      ariaLabel="Note body"
      value={draft.body}
      editable={!disabled}
      autoFocus
      placeholder="Start with what you know…"
      showToolbar
      lineWrapping
      onChange={(body) => onEdit({ body })}
    />
    <div className="thought-document-meta">
      <div className="thought-document-tags" aria-label="Tags">
        {tags.map((tag) => <button key={tag} type="button" className="thought-tag" disabled={disabled} onClick={() => onEdit({ tags: tags.filter((item) => item !== tag).join(", ") })} aria-label={`Remove ${tag} tag`}>{tag}<span aria-hidden="true"> ×</span></button>)}
        <button type="button" className="thought-tag-add" aria-expanded={tagsOpen} onClick={() => setTagsOpen((value) => !value)}>Add tag</button>
        {tagsOpen ? <input aria-label="Tag names" value={draft.tags} disabled={disabled} onChange={(event) => onEdit({ tags: event.target.value })} onBlur={() => setTagsOpen(false)} autoFocus /> : null}
        <button ref={infoRef} type="button" className="thought-tag-add" disabled={originalBusy} onClick={() => void showOriginal()}>Info</button>
      </div>
      {message ? <span className="thought-save-truth" role="status">{message}</span> : null}
    </div>
    {original ? <section ref={originalRef} className="thought-document-original surface-aerogel" aria-label="Original kept" tabIndex={-1}><strong>Original kept · {sourceLabel(original.source.kind)}</strong><pre className="thought-original-raw">{original.raw_text}</pre><button type="button" className="desk-chip quiet" onClick={() => { setOriginal(null); requestAnimationFrame(() => infoRef.current?.focus()); }}>Close original</button></section> : null}
    {originalError ? <p className="thought-document-original-error" role="alert">{originalError} <button type="button" className="desk-chip quiet" onClick={() => void showOriginal()}>Try again</button></p> : null}
    {message.includes("Retry save") ? <button type="button" className="desk-chip quiet thought-save-retry" onClick={onRetry}>Retry save</button> : null}
  </section>;
}
