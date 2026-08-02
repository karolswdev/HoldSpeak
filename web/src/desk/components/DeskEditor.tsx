import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
} from "react";
import { defaultKeymap, history, historyKeymap, indentWithTab } from "@codemirror/commands";
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
    },
    forwardedRef,
  ) {
    const host = useRef<HTMLDivElement | null>(null);
    const viewRef = useRef<EditorView | null>(null);
    const onChangeRef = useRef(onChange);
    const onEscapeRef = useRef(onEscape);
    const onModEnterRef = useRef(onModEnter);

    onChangeRef.current = onChange;
    onEscapeRef.current = onEscape;
    onModEnterRef.current = onModEnter;

    useImperativeHandle(forwardedRef, () => ({
      insertAtCursor(text) {
        const view = viewRef.current;
        if (!view) return;
        const { from, to } = view.state.selection.main;
        view.dispatch({ changes: { from, to, insert: text } });
        view.focus();
      },
    }), []);

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
              {
                key: "Mod-Enter",
                run() {
                  if (!onModEnterRef.current) return false;
                  onModEnterRef.current();
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
              if (update.docChanged) onChangeRef.current(update.state.doc.toString());
            }),
            ...(ariaLabel ? [EditorView.contentAttributes.of({ "aria-label": ariaLabel })] : []),
            ...(placeholderText ? [placeholder(placeholderText)] : []),
          ],
        }),
        parent: host.current,
      });
      viewRef.current = view;
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

    return (
      <div
        ref={host}
        className={["desk-code-editor", className].filter(Boolean).join(" ")}
        style={{ "--desk-editor-min-height": minHeight } as React.CSSProperties}
      />
    );
  },
);
