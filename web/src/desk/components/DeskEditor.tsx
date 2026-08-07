import "./inline-editor.css";
import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import {
  defaultKeymap,
  history,
  historyKeymap,
  indentWithTab,
} from "@codemirror/commands";
import { markdown, markdownKeymap } from "@codemirror/lang-markdown";
import { EditorState } from "@codemirror/state";
import { EditorView, keymap, placeholder } from "@codemirror/view";
import { deskEditorTheme, deskMarkdownHighlighting } from "./deskEditorTheme";

export interface DeskEditorHandle {
  insertAtCursor(text: string): void;
}

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
  onAIBarToggle?: () => void;
  /** The formatting rail is on by default; compact embeds may opt out. */
  showToolbar?: boolean;
}

function toggleInlineWrap(view: EditorView, marker: string): boolean {
  const { from, to } = view.state.selection.main;
  const doc = view.state.doc;
  const selected = doc.sliceString(from, to);

  if (
    selected.length >= marker.length * 2 &&
    selected.startsWith(marker) &&
    selected.endsWith(marker)
  ) {
    const text = selected.slice(marker.length, -marker.length);
    view.dispatch({
      changes: { from, to, insert: text },
      selection: { anchor: from, head: from + text.length },
    });
  } else if (
    from >= marker.length &&
    doc.sliceString(from - marker.length, from) === marker &&
    doc.sliceString(to, to + marker.length) === marker
  ) {
    view.dispatch({
      changes: {
        from: from - marker.length,
        to: to + marker.length,
        insert: selected,
      },
      selection: { anchor: from - marker.length, head: to - marker.length },
    });
  } else if (from === to) {
    view.dispatch({
      changes: { from, insert: `${marker}${marker}` },
      selection: { anchor: from + marker.length },
    });
  } else {
    view.dispatch({
      changes: { from, to, insert: `${marker}${selected}${marker}` },
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
      onAIBarToggle,
      showToolbar = true,
    },
    forwardedRef,
  ) {
    const host = useRef<HTMLDivElement | null>(null);
    const viewRef = useRef<EditorView | null>(null);
    const onChangeRef = useRef(onChange);
    const onEscapeRef = useRef(onEscape);
    const onModEnterRef = useRef(onModEnter);
    const onAIBarToggleRef = useRef(onAIBarToggle);

    onChangeRef.current = onChange;
    onEscapeRef.current = onEscape;
    onModEnterRef.current = onModEnter;
    onAIBarToggleRef.current = onAIBarToggle;

    useImperativeHandle(
      forwardedRef,
      () => ({
        insertAtCursor(text) {
          const view = viewRef.current;
          if (!view) return;
          const { from, to } = view.state.selection.main;
          view.dispatch({ changes: { from, to, insert: text } });
          view.focus();
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
              keydown(event) {
                if (event.key !== "Escape") return false;
                event.preventDefault();
                event.stopPropagation();
                return false;
              },
            }),
            EditorView.updateListener.of((update) => {
              if (update.docChanged)
                onChangeRef.current(update.state.doc.toString());
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
      if (autoFocus) view.focus();

      return () => {
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
      });
    }, [value]);

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
            <button
              type="button"
              className="desk-chip quiet"
              aria-label="Bold"
              title="Bold (⌘B)"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView((view) => toggleInlineWrap(view, "**"))}
            >
              <strong>B</strong>
            </button>
            <button
              type="button"
              className="desk-chip quiet"
              aria-label="Italic"
              title="Italic (⌘I)"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView((view) => toggleInlineWrap(view, "*"))}
            >
              <em>I</em>
            </button>
            <button
              type="button"
              className="desk-chip quiet"
              title="Heading 1"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView((view) => setHeading(view, 1))}
            >
              H1
            </button>
            <button
              type="button"
              className="desk-chip quiet"
              title="Heading 2"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView((view) => setHeading(view, 2))}
            >
              H2
            </button>
            <button
              type="button"
              className="desk-chip quiet"
              title="Heading 3"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView((view) => setHeading(view, 3))}
            >
              H3
            </button>
            <button
              type="button"
              className="desk-chip quiet"
              title="Bulleted list"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView((view) => togglePrefix(view, /^-\s/, "- "))}
            >
              List
            </button>
            <button
              type="button"
              className="desk-chip quiet"
              title="Numbered list"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView((view) => togglePrefix(view, /^\d+\.\s/, "1. "))}
            >
              1.
            </button>
            <button
              type="button"
              className="desk-chip quiet"
              title="Code"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView(toggleCode)}
            >
              &lt;/&gt;
            </button>
            <button
              type="button"
              className="desk-chip quiet"
              title="Link"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView(insertLink)}
            >
              Link
            </button>
            <button
              type="button"
              className="desk-chip quiet"
              title="Quote"
              onMouseDown={(event) => event.preventDefault()}
              onClick={useView((view) => togglePrefix(view, /^>\s/, "> "))}
            >
              Quote
            </button>
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
