import { HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { EditorView } from "@codemirror/view";
import { tags } from "@lezer/highlight";

export const deskEditorTheme = EditorView.theme(
  {
    "&": {
      backgroundColor: "var(--surface-2)",
      color: "var(--text)",
      border: "1px solid var(--border)",
      borderRadius: "var(--radius-sm)",
      boxShadow: "var(--desk-window-etch)",
      fontFamily: "var(--font-mono)",
      fontSize: "var(--font-size-sm)",
      lineHeight: "1.6",
    },
    "&.cm-focused": {
      borderColor: "var(--field-focus-border)",
      boxShadow: "var(--desk-window-etch), 0 0 0 2px var(--accent-tint)",
    },
    ".cm-scroller": {
      fontFamily: "inherit",
      overflow: "auto",
    },
    ".cm-content": {
      minHeight: "var(--desk-editor-min-height, 120px)",
      padding: "8px 12px",
      caretColor: "var(--accent)",
    },
    ".cm-line": {
      padding: "0",
    },
    // PHILO-9-04 round two (Codex Astra r1 finding 1): the editor takes the
    // desk-wide selection pair, ground AND ink. The tint ground under the
    // global page ink read 1.33:1; the accent ground with the page ink is
    // 4.56:1 for the selected text.
    ".cm-selectionBackground, ::selection": {
      backgroundColor: "var(--selection-bg) !important",
    },
    "::selection": {
      color: "var(--selection-ink)",
    },
    ".cm-cursor, .cm-dropCursor": {
      borderLeftColor: "var(--accent)",
    },
    ".cm-placeholder": {
      color: "var(--text-faint)",
      fontStyle: "italic",
    },
    ".cm-gutters": {
      display: "none",
    },
  },
  { dark: true },
);

export const deskMarkdownHighlighting = syntaxHighlighting(
  HighlightStyle.define([
    { tag: tags.heading, color: "var(--text)", fontWeight: "700" },
    { tag: tags.strong, fontWeight: "700" },
    { tag: tags.emphasis, fontStyle: "italic" },
    {
      tag: tags.monospace,
      color: "var(--info)",
      backgroundColor: "var(--desk-window-well)",
    },
    { tag: [tags.link, tags.url], color: "var(--accent)" },
    { tag: tags.list, color: "var(--text-faint)" },
  ]),
);
