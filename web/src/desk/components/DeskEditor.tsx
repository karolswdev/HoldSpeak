import "./inline-editor.css";
import { Button } from "../../components/signal/Signal";
import { forwardRef, useEffect, useImperativeHandle, useLayoutEffect, useRef } from "react";
import {
  defaultKeymap,
  history,
  historyKeymap,
  indentWithTab,
  isolateHistory,
} from "@codemirror/commands";
import { markdown, markdownKeymap } from "@codemirror/lang-markdown";
import { Annotation, Compartment, EditorState, StateEffect, StateField, type Extension } from "@codemirror/state";
import { Decoration, EditorView, keymap, placeholder } from "@codemirror/view";
import { deskEditorTheme, deskMarkdownHighlighting } from "./deskEditorTheme";

export interface DeskEditorHandle {
  insertAtCursor(text: string): void;
  captureVoiceTarget(): DeskEditorVoiceTarget | null;
  insertAtCapturedTarget(target: DeskEditorVoiceTarget, text: string, options?: { focus?: boolean }): boolean;
  getSelection(): DeskEditorSelection;
  getScrollTop(): number | null;
  restoreSelection(from: number, to: number, options?: { scrollTop?: number | null; focus?: boolean }): boolean;
  revealRange(from: number, to: number, options?: { focus?: boolean }): boolean;
  clearReveal(): void;
}

/** Opaque to consumers: a range in one editor and one document generation. */
export interface DeskEditorVoiceTarget {
  readonly view: EditorView;
  readonly generation: number;
  readonly from: number;
  readonly to: number;
}

export interface DeskEditorSelection {
  from: number;
  to: number;
  text: string;
}

const setReveal = StateEffect.define<{ from: number; to: number } | null>();
const authoritativeSync = Annotation.define<boolean>();
const revealField = StateField.define({
  create: () => Decoration.none,
  update(value, transaction) {
    value = value.map(transaction.changes);
    for (const effect of transaction.effects) {
      if (!effect.is(setReveal)) continue;
      value = effect.value
        ? Decoration.set([Decoration.mark({ class: "cm-thought-answer-reveal" }).range(effect.value.from, effect.value.to)])
        : Decoration.none;
    }
    return value;
  },
  provide: (field) => EditorView.decorations.from(field),
});

interface DeskEditorProps {
  value: string;
  onChange: (value: string) => void;
  autoFocus?: boolean;
  onEscape?: () => void;
  placeholder?: string;
  className?: string;
  minHeight?: string;
  ariaLabel?: string;
  onModEnter?: () => void;
  onViewChange?: (view: EditorView) => void;
  onSelectionChange?: (selection: DeskEditorSelection) => void;
  onAIBarToggle?: () => void;
  /** The formatting rail is on by default; compact embeds may opt out. */
  showToolbar?: boolean;
  editable?: boolean;
  /** PHILO-13-18: long lines wrap by default at every width (the Update
   * draft cut owners and due dates at 393, Astra's B5 check #739). A code
   * embed that needs one line per line passes `lineWrapping={false}`. */
  lineWrapping?: boolean;
  /** Extra CodeMirror extensions, read once at mount (the Note's diagram
   *  preview, mermaidPreview.ts). */
  extensions?: Extension;
}

function toggleInlineWrap(view: EditorView, marker: string, closingMarker = marker): boolean {
  const { from, to } = view.state.selection.main;
  const doc = view.state.doc;
  const selected = doc.sliceString(from, to);

  if (
    selected.length >= marker.length + closingMarker.length &&
    selected.startsWith(marker) &&
    selected.endsWith(closingMarker)
  ) {
    const text = selected.slice(marker.length, -closingMarker.length);
    view.dispatch({
      changes: { from, to, insert: text },
      selection: { anchor: from, head: from + text.length },
    });
  } else if (
    from >= marker.length &&
    doc.sliceString(from - marker.length, from) === marker &&
    doc.sliceString(to, to + closingMarker.length) === closingMarker
  ) {
    view.dispatch({
      changes: {
        from: from - marker.length,
        to: to + closingMarker.length,
        insert: selected,
      },
      selection: { anchor: from - marker.length, head: to - marker.length },
    });
  } else if (from === to) {
    view.dispatch({
      changes: { from, insert: `${marker}${closingMarker}` },
      selection: { anchor: from + marker.length },
    });
  } else {
    view.dispatch({
      changes: { from, to, insert: `${marker}${selected}${closingMarker}` },
      selection: { anchor: from + marker.length, head: to + marker.length },
    });
  }
  view.focus();
  return true;
}

function transformSelectedLines(
  view: EditorView,
  transform: (line: string) => string,
): void {
  const { from, to } = view.state.selection.main;
  const doc = view.state.doc;
  const first = doc.lineAt(from).number;
  const last = doc.lineAt(to > from ? to - 1 : to).number;
  const changes = [];

  for (let number = first; number <= last; number += 1) {
    const line = doc.line(number);
    const next = transform(line.text);
    if (next !== line.text)
      changes.push({ from: line.from, to: line.to, insert: next });
  }
  if (changes.length) view.dispatch({ changes });
  view.focus();
}

function setHeading(view: EditorView, level: 1 | 2 | 3): void {
  const prefix = `${"#".repeat(level)} `;
  transformSelectedLines(view, (line) => {
    const bare = line.replace(/^#{1,6}\s+/, "");
    return line.startsWith(prefix) ? bare : `${prefix}${bare}`;
  });
}

function togglePrefix(view: EditorView, pattern: RegExp, prefix: string): void {
  transformSelectedLines(view, (line) =>
    pattern.test(line) ? line.replace(pattern, "") : `${prefix}${line}`,
  );
}

function toggleCode(view: EditorView): void {
  const { from, to } = view.state.selection.main;
  const selected = view.state.doc.sliceString(from, to);
  if (!selected.includes("\n")) {
    toggleInlineWrap(view, "`");
    return;
  }
  const fenced = selected.startsWith("```\n") && selected.endsWith("\n```");
  const text = fenced ? selected.slice(4, -4) : `\`\`\`\n${selected}\n\`\`\``;
  view.dispatch({
    changes: { from, to, insert: text },
    selection: {
      anchor: fenced ? from : from + 4,
      head: fenced ? from + text.length : from + 4 + selected.length,
    },
  });
  view.focus();
}

function insertLink(view: EditorView): void {
  const { from, to } = view.state.selection.main;
  const selected = view.state.doc.sliceString(from, to) || "text";
  view.dispatch({
    changes: { from, to, insert: `[${selected}](url)` },
    selection: { anchor: from + 1, head: from + 1 + selected.length },
  });
  view.focus();
}

export const DeskEditor = forwardRef<DeskEditorHandle, DeskEditorProps>(
  function DeskEditor(
    {
      value,
      onChange,
      autoFocus = false,
      onEscape,
      placeholder: placeholderText,
      className,
      minHeight = "120px",
      ariaLabel,
      onModEnter,
      onViewChange,
      onSelectionChange,
      onAIBarToggle,
      showToolbar = true,
      editable = true,
      lineWrapping = true,
      extensions: extraExtensions,
    },
    forwardedRef,
  ) {
    const host = useRef<HTMLDivElement | null>(null);
    const viewRef = useRef<EditorView | null>(null);
    const documentGenerationRef = useRef(0);
    const composingRef = useRef(false);
    const onChangeRef = useRef(onChange);
    const onEscapeRef = useRef(onEscape);
    const onModEnterRef = useRef(onModEnter);
    const onAIBarToggleRef = useRef(onAIBarToggle);
    const onSelectionChangeRef = useRef(onSelectionChange);
    const editableCompartment = useRef(new Compartment());

    onChangeRef.current = onChange;
    onEscapeRef.current = onEscape;
    onModEnterRef.current = onModEnter;
    onAIBarToggleRef.current = onAIBarToggle;
    onSelectionChangeRef.current = onSelectionChange;

    useImperativeHandle(
      forwardedRef,
      () => ({
        insertAtCursor(text) {
          const view = viewRef.current;
          if (!view) return;
          const { from, to } = view.state.selection.main;
          // The cursor goes after the inserted text, so the next words
          // (typed or spoken) continue it.
          view.dispatch({ changes: { from, to, insert: text }, selection: { anchor: from + text.length } });
          view.focus();
        },
        captureVoiceTarget() {
          const view = viewRef.current;
          if (!view || !view.state.facet(EditorView.editable) || view.composing || composingRef.current) return null;
          const { from, to } = view.state.selection.main;
          return { view, generation: documentGenerationRef.current, from, to };
        },
        insertAtCapturedTarget(target, text, options) {
          const view = viewRef.current;
          if (!view || view !== target.view || view.composing || composingRef.current ||
              !view.state.facet(EditorView.editable) ||
              target.generation !== documentGenerationRef.current ||
              target.from < 0 || target.to < target.from || target.to > view.state.doc.length) return false;
          view.dispatch({
            changes: { from: target.from, to: target.to, insert: text },
            selection: { anchor: target.from + text.length },
            annotations: isolateHistory.of("full"),
          });
          if (options?.focus) view.focus();
          return true;
        },
        getSelection() {
          const view = viewRef.current;
          if (!view) return { from: 0, to: 0, text: "" };
          const { from, to } = view.state.selection.main;
          return { from, to, text: view.state.doc.sliceString(from, to) };
        },
        getScrollTop() {
          return viewRef.current?.scrollDOM.scrollTop ?? null;
        },
        restoreSelection(from, to, options) {
          const view = viewRef.current;
          if (!view || from < 0 || to < from || to > view.state.doc.length) return false;
          view.dispatch({
            selection: { anchor: from, head: to },
            effects: options?.scrollTop == null ? [EditorView.scrollIntoView(from, { y: "center" })] : [],
          });
          if (options?.focus !== false) view.focus();
          if (options?.scrollTop != null) view.scrollDOM.scrollTop = options.scrollTop;
          return true;
        },
        revealRange(from, to, options) {
          const view = viewRef.current;
          if (!view || from < 0 || to < from || to > view.state.doc.length) return false;
          view.dispatch({
            selection: { anchor: to },
            effects: [setReveal.of({ from, to }), EditorView.scrollIntoView(from, { y: "center" })],
          });
          if (options?.focus !== false) view.focus();
          return true;
        },
        clearReveal() {
          viewRef.current?.dispatch({ effects: setReveal.of(null) });
        },
      }),
      [],
    );

    useEffect(() => {
      if (!host.current) return;
      const view = new EditorView({
        state: EditorState.create({
          doc: value,
          extensions: [
            history(),
            markdown(),
            deskEditorTheme,
            deskMarkdownHighlighting,
            revealField,
            editableCompartment.current.of(EditorView.editable.of(editable)),
            ...(lineWrapping ? [EditorView.lineWrapping] : []),
            ...(extraExtensions ? [extraExtensions] : []),
            keymap.of([
              {
                key: "Escape",
                run(editor) {
                  const selection = editor.state.selection.main;
                  if (!selection.empty) {
                    editor.dispatch({ selection: { anchor: selection.head } });
                  } else {
                    onEscapeRef.current?.();
                  }
                  return true;
                },
              },
              { key: "Mod-b", run: (editor) => toggleInlineWrap(editor, "**") },
              { key: "Mod-i", run: (editor) => toggleInlineWrap(editor, "*") },
              {
                key: "Mod-Enter",
                run() {
                  if (!onModEnterRef.current) return false;
                  onModEnterRef.current();
                  return true;
                },
              },
              {
                key: "Mod-j",
                run() {
                  onAIBarToggleRef.current?.();
                  return true;
                },
              },
              indentWithTab,
              ...defaultKeymap,
              ...historyKeymap,
              ...markdownKeymap,
            ]),
            EditorView.domEventHandlers({
              compositionstart() {
                composingRef.current = true;
                return false;
              },
              compositionend() {
                composingRef.current = false;
                return false;
              },
              keydown(event) {
                if (event.key !== "Escape") return false;
                event.preventDefault();
                event.stopPropagation();
                return false;
              },
            }),
            EditorView.updateListener.of((update) => {
              if (update.docChanged) documentGenerationRef.current += 1;
              if (update.docChanged && !update.transactions.some((transaction) => transaction.annotation(authoritativeSync)))
                onChangeRef.current(update.state.doc.toString());
              if (update.docChanged || update.selectionSet) {
                const { from, to } = update.state.selection.main;
                onSelectionChangeRef.current?.({ from, to, text: update.state.doc.sliceString(from, to) });
              }
            }),
            ...(ariaLabel
              ? [EditorView.contentAttributes.of({ "aria-label": ariaLabel })]
              : []),
            ...(placeholderText ? [placeholder(placeholderText)] : []),
          ],
        }),
        parent: host.current,
      });
      viewRef.current = view;
      onViewChange?.(view);
      const { from, to } = view.state.selection.main;
      onSelectionChangeRef.current?.({ from, to, text: view.state.doc.sliceString(from, to) });
      if (autoFocus) view.focus();

      return () => {
        composingRef.current = false;
        view.destroy();
        viewRef.current = null;
      };
      // This editor deliberately initializes once. Prop synchronization lives below.
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
      const view = viewRef.current;
      if (!view || value === view.state.doc.toString()) return;
      const { from, to } = view.state.selection.main;
      const nextCursor = Math.min(value.length, Math.max(0, from));
      view.dispatch({
        changes: { from: 0, to: view.state.doc.length, insert: value },
        selection: { anchor: nextCursor, head: Math.min(value.length, to) },
        annotations: authoritativeSync.of(true),
      });
    }, [value]);

    useLayoutEffect(() => {
      viewRef.current?.dispatch({ effects: editableCompartment.current.reconfigure(EditorView.editable.of(editable)) });
    }, [editable]);

    const useView = (format: (view: EditorView) => void) => () => {
      const view = viewRef.current;
      if (view) format(view);
    };

    return (
      <div className="desk-editor">
        {showToolbar ? (
          <div
            className="desk-editor-toolbar"
            role="toolbar"
            aria-label="Markdown formatting"
          >
            <Button
              variant="chrome"
              className="desk-chip quiet"
              aria-label="Bold"
              title="Bold (⌘B)"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView((view) => toggleInlineWrap(view, "**"))}
            >
              <strong>B</strong>
            </Button>
            <Button
              variant="chrome"
              className="desk-chip quiet"
              aria-label="Italic"
              title="Italic (⌘I)"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView((view) => toggleInlineWrap(view, "*"))}
            >
              <em>I</em>
            </Button>
            <Button
              variant="chrome"
              className="desk-chip quiet"
              aria-label="Underline"
              title="Underline"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView((view) => toggleInlineWrap(view, "<u>", "</u>"))}
            >
              <u>U</u>
            </Button>
            <Button
              variant="chrome"
              className="desk-chip quiet"
              title="Heading 1"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView((view) => setHeading(view, 1))}
            >
              H1
            </Button>
            <Button
              variant="chrome"
              className="desk-chip quiet"
              title="Heading 2"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView((view) => setHeading(view, 2))}
            >
              H2
            </Button>
            <Button
              variant="chrome"
              className="desk-chip quiet"
              title="Heading 3"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView((view) => setHeading(view, 3))}
            >
              H3
            </Button>
            <Button
              variant="chrome"
              className="desk-chip quiet"
              title="Bulleted list"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView((view) => togglePrefix(view, /^-\s/, "- "))}
            >
              List
            </Button>
            <Button
              variant="chrome"
              className="desk-chip quiet"
              title="Numbered list"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView((view) => togglePrefix(view, /^\d+\.\s/, "1. "))}
            >
              1.
            </Button>
            <Button
              variant="chrome"
              className="desk-chip quiet"
              title="Code"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView(toggleCode)}
            >
              &lt;/&gt;
            </Button>
            <Button
              variant="chrome"
              className="desk-chip quiet"
              title="Link"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView(insertLink)}
            >
              Link
            </Button>
            <Button
              variant="chrome"
              className="desk-chip quiet"
              title="Quote"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView((view) => togglePrefix(view, /^>\s/, "> "))}
            >
              Quote
            </Button>
          </div>
        ) : null}
        <div
          ref={host}
          className={["desk-code-editor", className].filter(Boolean).join(" ")}
          style={
            { "--desk-editor-min-height": minHeight } as React.CSSProperties
          }
        />
      </div>
    );
  },
);
