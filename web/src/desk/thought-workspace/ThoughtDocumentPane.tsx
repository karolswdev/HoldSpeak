import { firstWords, NEW_THOUGHT_TITLE } from "../thoughtTitle";
import { useEffect, useRef, useSyncExternalStore, type ReactNode, type RefObject } from "react";
import { EditInPlace, ReadingObjectLinks, StateChip, SurfaceWell, Toolbar } from "../surface";
import { Button } from "../../components/signal/Signal";
import { MicButton } from "../components/MicButton";
import { DeskEditor, type DeskEditorHandle, type DeskEditorSelection } from "../components/DeskEditor";
import { refOpener } from "../openObject";
import type { ThoughtDraft } from "../pullouts/editors/useThoughtNoteWriter";
import { claimThoughtKeys } from "../thoughtKeys";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { livePreview } from "./livePreview";
import { mermaidPreview } from "./mermaidPreview";
import { bindThoughtVoiceTarget, deskThoughtVoiceDraft, thoughtVoiceKey, type ThoughtVoiceDraftIO } from "./thoughtVoiceDraft";

/* HS-201-12 — bands 1 and 2 of the one clean note (the owner's first-use
   verdict of 2026-09-20).  The title wraps and is edited in place; the note
   is the text, full width, no formatting rail.  The tag row, the Info verb,
   the orphan mic and the Filed/Saved foot left THIS window: tags and the
   original capture stay in the Note pullout (`desk/pullouts/NotePullout`),
   the kept state moved to the window foot.  The mic is the note field's own
   (it writes at the cursor), never a button beside the field. */
/** A title of his own: not the untitled name, and not the first words of the
 *  note (the name the save rule gives an untitled note). */
/** The note in live preview: every line the caret is not on shows as
 *  written text (livePreview.ts); the diagrams draw in place
 *  (mermaidPreview.ts). */
const NOTE_EDITOR_EXTENSIONS = [livePreview(), mermaidPreview()];

export function ownTitle(title: string, body: string): boolean {
  const clean = title.trim();
  return Boolean(clean) && clean !== NEW_THOUGHT_TITLE && clean !== firstWords(body);
}

/** The same recovery view serves the live Thought and an isolated Components fixture. */
export function ThoughtVoiceRecovery({ text, disabled, onInsert }: {
  text: string;
  disabled: boolean;
  onInsert: () => void;
}) {
  return <ThoughtVoiceRecoveryContent key={text} text={text} disabled={disabled} onInsert={onInsert} />;
}

function ThoughtVoiceRecoveryContent({ text, disabled, onInsert }: {
  text: string;
  disabled: boolean;
  onInsert: () => void;
}) {
  const { copy, state: copyState } = useCopyReceipt();
  return <SurfaceWell head="Voice">
    <div className="thought-voice-recovery" data-testid="thought-voice-recovery">
      <StateChip state="warning" label="NOT INSERTED" />
      <div className="thought-voice-text">{text}</div>
      <div className="thought-voice-actions">
        <Button dense variant="primary" disabled={disabled} onClick={onInsert}>Insert at caret</Button>
        <Button dense variant="ghost" onClick={() => void copy(text)}>
          {copyState === "copied" ? "Copied" : copyState === "failed" ? "Copy failed" : "Copy"}
        </Button>
      </div>
    </div>
  </SurfaceWell>;
}

export function ThoughtDocumentPane({
  noteId,
  draft,
  onEdit,
  disabled,
  lockedReason,
  revealRange,
  returnRange,
  editorRef,
  onSelectionChange,
  onOpenLink,
  voiceDraftIO = deskThoughtVoiceDraft,
  mic = true,
  voiceInput,
  verbs,
  margin,
}: {
  /** The thought's note. With it, the field takes the keys typed between
   *  `Write a thought` and this window (thoughtKeys.ts). */
  noteId?: string;
  draft: ThoughtDraft;
  onEdit: (patch: Partial<ThoughtDraft>) => void;
  disabled: boolean;
  /** Why the note cannot be edited right now (a finished Thought). Never a
   *  dead field without a reason — the EditInPlace contract. */
  lockedReason?: string;
  revealRange?: { start: number; end: number; focus?: boolean } | null;
  /** A validated Ask return. The original editor owns the CM selection. */
  returnRange?: { from: number; to: number; scrollTop: number | null; nonce: number } | null;
  editorRef?: RefObject<DeskEditorHandle | null>;
  onSelectionChange?: (selection: DeskEditorSelection) => void;
  /** Components supplies a local receipt; production uses the Desk opener. */
  onOpenLink?: (ref: string) => void;
  /** Fixture seam for the same Thought recovery view, without workspace writes. */
  voiceDraftIO?: ThoughtVoiceDraftIO;
  mic?: boolean;
  /** Alternate input control for the same document composition and binder. */
  voiceInput?: (bindText: () => (text: string) => void, disabled: boolean) => ReactNode;
  /** Window grammar (2026-10-24): the window's verbs. They sit on the
   *  toolbar under the title bar, left; the field's voice control sits at
   *  its right end. */
  verbs?: ReactNode;
  /** Direction A (2026-10-27): the margin beside the text (NoteMargin). The
   *  editor keeps its place; the margin takes the right column. */
  margin?: ReactNode;
}) {
  const ownBodyRef = useRef<DeskEditorHandle | null>(null);
  const bodyRef = editorRef ?? ownBodyRef;
  const activeNoteIdRef = useRef(noteId);
  activeNoteIdRef.current = noteId;
  const voiceKey = noteId ? thoughtVoiceKey(noteId) : null;
  const retained = useSyncExternalStore(
    voiceDraftIO.subscribe,
    () => voiceKey ? voiceDraftIO.get(voiceKey) : null,
    () => null,
  );
  const bindText = () => bindThoughtVoiceTarget(
    noteId, bodyRef.current, () => activeNoteIdRef.current === noteId, voiceDraftIO,
  );

  /* HS-201-12 — the reveal is re-applied when the authoritative body
     lands: the append arrives as a whole-document sync, which maps the
     decoration away.  The window clears `revealRange` on the first real
     edit, so this never re-scrolls under the owner's cursor. */
  useEffect(() => {
    if (!revealRange || !bodyRef.current) return;
    bodyRef.current.revealRange(revealRange.start, revealRange.end, { focus: revealRange.focus });
  }, [revealRange, draft.body]);

  useEffect(() => {
    if (!returnRange || !bodyRef.current) return;
    bodyRef.current.restoreSelection(returnRange.from, returnRange.to, { scrollTop: returnRange.scrollTop });
  }, [returnRange, draft.body]);

  useEffect(() => {
    if (!noteId) return;
    return claimThoughtKeys(noteId, (text) => bodyRef.current?.insertAtCursor(text));
  }, [noteId]);

  const voice = mic ? <MicButton label="Speak the note" disabled={disabled}
    onText={(text) => bodyRef.current?.insertAtCursor(text)}
    bindText={bindText} /> : voiceInput?.(bindText, disabled) ?? null;

  return <section className={margin ? "thought-note-document has-margin" : "thought-note-document"} aria-label="Note">
    {/* Window grammar (2026-10-24): a native editor window. The verbs are
        on the kit Toolbar under the title bar; the field's own voice control is
        at the toolbar's right end and still writes at the field's captured
        target (#1443). The editor fills the window below it. */}
    <Toolbar
      label="Note actions"
      className="thought-note-toolbar"
      data-testid="thought-note-toolbar"
      trailingStays
      trailing={voice ? <span className="thought-note-field-mic thought-note-toolbar-voice">{voice}</span> : null}
    >
      {verbs}
    </Toolbar>
    <div className="thought-note-field">
      {/* Betterment Q8 (one note): the title shows once, in the title bar. A
          heading that only repeats the note's first line (an untitled note,
          named by its first words, thoughtTitle.ts) left the window. A title
          of his own, which the first line does not say, stays editable here
          as the page's first line at the body step, never a display
          headline (Object ▸ Rename opens this window). Owner 2026-10-27:
          it is one line, a document's name line (17 px, ellipsis when
          long, the whole name while it is edited), never a three-line H1. */}
      {ownTitle(draft.title, draft.body) ? <EditInPlace
        className="thought-note-title"
        label="Title"
        value={draft.title}
        disabledReason={lockedReason}
        onCommit={(next) => onEdit({ title: next })}
      /> : null}
      <DeskEditor
        ref={bodyRef}
        className="thought-note-body"
        ariaLabel="Note body"
        value={draft.body}
        editable={!disabled}
        autoFocus
        placeholder="Start with what you know…"
        showToolbar={false}
        lineWrapping
        extensions={NOTE_EDITOR_EXTENSIONS}
        onChange={(body) => onEdit({ body })}
        onSelectionChange={onSelectionChange}
      />
    </div>
    {margin}
    {retained && voiceKey ? <ThoughtVoiceRecovery text={retained} disabled={disabled} onInsert={() => {
      const editor = bodyRef.current;
      const target = editor?.captureVoiceTarget();
      if (editor && target && editor.insertAtCapturedTarget(target, retained, { focus: true }))
        voiceDraftIO.forget(voiceKey);
    }} /> : null}
    <ReadingObjectLinks source={draft.body} onOpen={onOpenLink ?? ((ref) => refOpener(ref)?.())} />
  </section>;
}
