/* The Note's live preview (owner 2026-10-27: "a powerful, delighting and also
   useful experience"). The note stays one CodeMirror document; every line the
   caret is NOT on shows as written text, the way Obsidian's live preview does:
   heading marks, emphasis marks, list marks, link urls, quote marks, fence
   marks and rules hide; a task is a real checkbox; a table is a real table.
   The line the caret is on shows its source again, at the same size, so
   nothing under the caret moves. Everything is Decorations (mark, replace,
   line, widget) over the Markdown syntax tree; the document text is the only
   copy. The mermaid fences are mermaidPreview.ts (same mechanism). */
import { syntaxTree } from "@codemirror/language";
import { type EditorState, type Extension, type Range, StateField } from "@codemirror/state";
import {
  Decoration,
  type DecorationSet,
  EditorView,
  ViewPlugin,
  type ViewUpdate,
  WidgetType,
} from "@codemirror/view";
import type { SyntaxNode } from "@lezer/common";
import { refOpener } from "../openObject";

export interface LivePreviewOptions {
  /** Opens a desk object ref (`project:…`, `decision:…`). Return false when
   *  the ref is not one the desk opens. Default: openObject's refOpener. */
  openRef?: (ref: string) => boolean;
  /** Opens an external url. Default: a new browser tab. */
  openUrl?: (url: string) => void;
}

/* ── the caret's lines ───────────────────────────────────────────────── */

/** True when any selection range touches [from, to]. */
function touched(state: EditorState, from: number, to: number): boolean {
  return state.selection.ranges.some((range) => range.from <= to && range.to >= from);
}

function lineTouched(state: EditorState, pos: number): boolean {
  const line = state.doc.lineAt(pos);
  return touched(state, line.from, line.to);
}

/* ── widgets ─────────────────────────────────────────────────────────── */

class BulletWidget extends WidgetType {
  constructor(readonly text: string, readonly ordered: boolean) {
    super();
  }

  eq(other: BulletWidget) {
    return other.text === this.text && other.ordered === this.ordered;
  }

  toDOM() {
    const mark = document.createElement("span");
    mark.className = this.ordered ? "cm-lp-number" : "cm-lp-bullet";
    mark.setAttribute("aria-hidden", "true");
    mark.textContent = this.ordered ? this.text : "•";
    return mark;
  }
}

class CheckboxWidget extends WidgetType {
  constructor(readonly checked: boolean) {
    super();
  }

  eq(other: CheckboxWidget) {
    return other.checked === this.checked;
  }

  toDOM(view: EditorView) {
    const wrap = document.createElement("span");
    wrap.className = "cm-lp-task";
    const box = document.createElement("input");
    box.type = "checkbox";
    box.className = "cm-lp-checkbox";
    box.checked = this.checked;
    box.tabIndex = -1;
    box.setAttribute("data-testid", "note-task-box");
    box.setAttribute("aria-label", "Done");
    // The press keeps the caret where it is (the line stays rendered).
    box.addEventListener("mousedown", (event) => event.preventDefault());
    box.addEventListener("click", (event) => {
      event.preventDefault();
      if (!view.state.facet(EditorView.editable)) return;
      toggleTaskAt(view, view.posAtDOM(wrap));
    });
    wrap.appendChild(box);
    return wrap;
  }

  ignoreEvent() {
    return true;
  }
}

/** Toggles the `[ ]` / `[x]` of the task item that starts at `pos`. */
export function toggleTaskAt(view: EditorView, pos: number): boolean {
  const line = view.state.doc.lineAt(pos);
  const rest = line.text.slice(pos - line.from);
  const match = /^\s*(?:[-*+]|\d+[.)])\s+\[( |x|X)\]/.exec(rest);
  if (!match) return false;
  const at = pos + match[0].length - 2;
  view.dispatch({ changes: { from: at, to: at + 1, insert: match[1] === " " ? "x" : " " } });
  return true;
}

class FenceLabelWidget extends WidgetType {
  constructor(readonly language: string) {
    super();
  }

  eq(other: FenceLabelWidget) {
    return other.language === this.language;
  }

  toDOM() {
    const label = document.createElement("span");
    label.className = "cm-lp-fence-label";
    label.textContent = this.language;
    return label;
  }
}

type Align = "left" | "center" | "right";
type TableShape = { head: string[]; rows: string[][]; align: Align[] };

function cells(text: string): string[] {
  let body = text.trim();
  if (body.startsWith("|")) body = body.slice(1);
  if (body.endsWith("|") && !body.endsWith("\\|")) body = body.slice(0, -1);
  return body.split(/(?<!\\)\|/).map((cell) => cell.trim().replace(/\\\|/g, "|"));
}

/** Cell words without their inline marks (the table is a reading view). */
function plainCell(text: string): string {
  return text
    .replace(/!?\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/(\*\*|__|~~)(.+?)\1/g, "$2")
    .replace(/(\*|_)(.+?)\1/g, "$2")
    .replace(/`([^`]*)`/g, "$1");
}

class TableWidget extends WidgetType {
  constructor(readonly shape: TableShape, readonly sourceFrom: number) {
    super();
  }

  eq(other: TableWidget) {
    return JSON.stringify(other.shape) === JSON.stringify(this.shape);
  }

  toDOM(view: EditorView) {
    const box = document.createElement("div");
    box.className = "cm-lp-table";
    box.setAttribute("data-testid", "note-table");
    const table = document.createElement("table");
    const head = table.createTHead().insertRow();
    this.shape.head.forEach((text, i) => {
      const th = document.createElement("th");
      th.textContent = plainCell(text);
      th.style.textAlign = this.shape.align[i] ?? "left";
      head.appendChild(th);
    });
    const body = table.createTBody();
    for (const row of this.shape.rows) {
      const tr = body.insertRow();
      this.shape.head.forEach((_, i) => {
        const td = tr.insertCell();
        td.textContent = plainCell(row[i] ?? "");
        td.style.textAlign = this.shape.align[i] ?? "left";
      });
    }
    box.appendChild(table);
    // A press on the table puts the caret in its source (the table opens).
    box.addEventListener("mousedown", (event) => {
      if (event.button !== 0) return;
      event.preventDefault();
      view.dispatch({ selection: { anchor: Math.min(this.sourceFrom, view.state.doc.length) } });
      view.focus();
    });
    return box;
  }

  ignoreEvent() {
    return false;
  }
}

/* ── tables: block widgets (a state field; plugins cannot replace lines) ── */

function tableShape(state: EditorState, node: SyntaxNode): TableShape | null {
  const doc = state.doc;
  const first = doc.lineAt(node.from).number;
  const last = doc.lineAt(node.to).number;
  if (last - first < 1) return null;
  const head = cells(doc.line(first).text);
  const align = cells(doc.line(first + 1).text).map((spec): Align => {
    const left = spec.startsWith(":");
    const right = spec.endsWith(":");
    return left && right ? "center" : right ? "right" : "left";
  });
  const rows: string[][] = [];
  for (let n = first + 2; n <= last; n++) rows.push(cells(doc.line(n).text));
  return { head, rows, align };
}

function buildTables(state: EditorState): DecorationSet {
  const out: Range<Decoration>[] = [];
  syntaxTree(state).iterate({
    enter(ref) {
      if (ref.name !== "Table") return;
      const from = state.doc.lineAt(ref.from).from;
      const to = state.doc.lineAt(ref.to).to;
      if (!touched(state, from, to)) {
        const shape = tableShape(state, ref.node);
        if (shape) out.push(Decoration.replace({ widget: new TableWidget(shape, ref.from), block: true }).range(from, to));
      }
      return false;
    },
  });
  return Decoration.set(out);
}

const tableField = StateField.define<DecorationSet>({
  create: buildTables,
  update(value, tr) {
    if (tr.docChanged || tr.selection || syntaxTree(tr.state) !== syntaxTree(tr.startState)) return buildTables(tr.state);
    return value;
  },
  provide: (field) => EditorView.decorations.from(field),
});

/* ── inline and line decorations over the visible ranges ─────────────── */

const hide = Decoration.replace({});
const line = (cls: string) => Decoration.line({ class: cls });
const mark = (cls: string, attributes?: Record<string, string>) => Decoration.mark({ class: cls, attributes });
const INLINE_MARK_PARENTS = new Set(["StrongEmphasis", "Emphasis", "Strikethrough", "InlineCode"]);
const STYLE: Record<string, string> = {
  StrongEmphasis: "cm-lp-strong",
  Emphasis: "cm-lp-em",
  Strikethrough: "cm-lp-strike",
  InlineCode: "cm-lp-icode",
};

function isMermaid(state: EditorState, node: SyntaxNode): boolean {
  const info = node.getChild("CodeInfo");
  return Boolean(info && /^mermaid$/i.test(state.doc.sliceString(info.from, info.to).trim()));
}

function linkHref(url: string): string {
  return /^www\./i.test(url) ? `https://${url}` : url;
}

function buildInline(view: EditorView): DecorationSet {
  const { state } = view;
  const doc = state.doc;
  const out: Range<Decoration>[] = [];
  const lines = new Map<number, string[]>();
  const addLine = (pos: number, cls: string) => {
    const at = doc.lineAt(pos).from;
    lines.set(at, [...(lines.get(at) ?? []), cls]);
  };
  /** Hides [from, to) and, when asked, the one space that follows it. */
  const hideMark = (from: number, to: number, withSpace = false) => {
    const end = withSpace && doc.sliceString(to, to + 1) === " " ? to + 1 : to;
    if (end > from) out.push(hide.range(from, end));
  };
  if (!view.visibleRanges.length) return Decoration.none;
  const from = view.visibleRanges[0].from;
  const to = view.visibleRanges[view.visibleRanges.length - 1].to;

  syntaxTree(state).iterate({
    from,
    to,
    enter(ref) {
      const name = ref.name;
      const node = ref.node;

      const heading = /^ATXHeading([1-6])$/.exec(name);
      if (heading) {
        addLine(ref.from, `cm-lp-h cm-lp-h${Math.min(3, Number(heading[1]))}`);
        if (!lineTouched(state, ref.from)) {
          let first = true;
          for (let child = node.firstChild; child; child = child.nextSibling) {
            if (child.name !== "HeaderMark") continue;
            if (first) hideMark(child.from, child.to, true);
            else hideMark(doc.sliceString(child.from - 1, child.from) === " " ? child.from - 1 : child.from, child.to);
            first = false;
          }
        }
        return;
      }

      if (INLINE_MARK_PARENTS.has(name)) {
        out.push(mark(STYLE[name]).range(ref.from, ref.to));
        if (!lineTouched(state, ref.from)) {
          for (let child = node.firstChild; child; child = child.nextSibling)
            if (child.name === "EmphasisMark" || child.name === "StrikethroughMark" || child.name === "CodeMark")
              hideMark(child.from, child.to);
        }
        return name === "InlineCode" ? false : undefined;
      }

      if (name === "ListItem") {
        const listMark = node.getChild("ListMark");
        if (!listMark) return;
        addLine(ref.from, "cm-lp-li");
        const task = node.getChild("Task");
        const marker = task?.getChild("TaskMarker");
        const markerText = marker ? doc.sliceString(marker.from, marker.to) : "";
        const checked = /\[[xX]\]/.test(markerText);
        if (task && marker) {
          addLine(ref.from, checked ? "cm-lp-task-line cm-lp-task-done" : "cm-lp-task-line");
          if (checked && task.to > marker.to) out.push(mark("cm-lp-done").range(marker.to, task.to));
        }
        if (lineTouched(state, ref.from)) return;
        if (task && marker) {
          const end = doc.sliceString(marker.to, marker.to + 1) === " " ? marker.to + 1 : marker.to;
          out.push(Decoration.replace({ widget: new CheckboxWidget(checked) }).range(listMark.from, end));
        } else {
          const ordered = node.parent?.name === "OrderedList";
          const end = doc.sliceString(listMark.to, listMark.to + 1) === " " ? listMark.to + 1 : listMark.to;
          out.push(Decoration.replace({ widget: new BulletWidget(doc.sliceString(listMark.from, listMark.to), ordered) })
            .range(listMark.from, end));
        }
        return;
      }

      if (name === "Link") {
        const url = node.getChild("URL");
        const marks = node.getChildren("LinkMark");
        if (!url || marks.length < 2) return;
        const href = doc.sliceString(url.from, url.to);
        const textFrom = marks[0].to;
        const textTo = marks[1].from;
        if (textTo > textFrom)
          out.push(mark("cm-lp-link", { title: href, "data-lp-href": linkHref(href) }).range(textFrom, textTo));
        if (!lineTouched(state, ref.from)) {
          hideMark(ref.from, textFrom);
          hideMark(textTo, ref.to);
        }
        return false;
      }

      if (name === "Autolink") {
        const url = node.getChild("URL");
        if (!url) return false;
        const href = doc.sliceString(url.from, url.to);
        out.push(mark("cm-lp-link", { title: href, "data-lp-href": linkHref(href) }).range(url.from, url.to));
        if (!lineTouched(state, ref.from)) {
          hideMark(ref.from, url.from);
          hideMark(url.to, ref.to);
        }
        return false;
      }

      if (name === "URL") {
        // A bare url in the text (GFM autolink). Urls inside links and
        // images are handled by their parents.
        const parent = node.parent?.name;
        if (parent === "Link" || parent === "Image" || parent === "Autolink" || parent === "LinkReference") return;
        const href = doc.sliceString(ref.from, ref.to);
        out.push(mark("cm-lp-link", { title: href, "data-lp-href": linkHref(href) }).range(ref.from, ref.to));
        return;
      }

      if (name === "FencedCode") {
        const active = touched(state, doc.lineAt(ref.from).from, doc.lineAt(ref.to).to);
        if (!active && isMermaid(state, node)) return false; // mermaidPreview draws it
        const first = doc.lineAt(ref.from);
        const last = doc.lineAt(ref.to);
        const marks = node.getChildren("CodeMark");
        const closed = marks.length > 1 && last.number > first.number;
        for (let n = first.number; n <= last.number; n++) {
          const cls = ["cm-lp-code"];
          if (n === first.number) cls.push("cm-lp-code-open");
          if (n === last.number && closed) cls.push("cm-lp-code-close");
          addLine(doc.line(n).from, cls.join(" "));
        }
        if (!active) {
          const info = node.getChild("CodeInfo");
          const language = info ? doc.sliceString(info.from, info.to).trim() : "";
          if (first.to > first.from)
            out.push(Decoration.replace({ widget: new FenceLabelWidget(language) }).range(first.from, first.to));
          if (closed && last.to > last.from) out.push(hide.range(last.from, last.to));
        }
        return false;
      }

      if (name === "Blockquote") {
        const first = doc.lineAt(ref.from).number;
        const last = doc.lineAt(ref.to).number;
        for (let n = first; n <= last; n++) addLine(doc.line(n).from, "cm-lp-quote");
        return;
      }

      if (name === "QuoteMark") {
        if (!lineTouched(state, ref.from)) hideMark(ref.from, ref.to, true);
        return;
      }

      if (name === "HorizontalRule") {
        if (!lineTouched(state, ref.from)) {
          addLine(ref.from, "cm-lp-hr");
          hideMark(ref.from, ref.to);
        }
        return;
      }

      if (name === "Table") return false; // tableField draws it
      return undefined;
    },
  });

  for (const [at, classes] of lines) out.push(line(classes.join(" ")).range(at));
  return Decoration.set(out, true);
}

const inlinePlugin = ViewPlugin.fromClass(
  class {
    decorations: DecorationSet;

    constructor(view: EditorView) {
      this.decorations = buildInline(view);
    }

    update(update: ViewUpdate) {
      if (update.docChanged || update.selectionSet || update.viewportChanged ||
          syntaxTree(update.state) !== syntaxTree(update.startState))
        this.decorations = buildInline(update.view);
    }
  },
  { decorations: (plugin) => plugin.decorations },
);

/* ── ⌘-click on a link ───────────────────────────────────────────────── */

function defaultOpenRef(ref: string): boolean {
  const open = refOpener(ref);
  if (!open) return false;
  open();
  return true;
}

function defaultOpenUrl(url: string) {
  window.open(url, "_blank", "noopener,noreferrer");
}

function linkClicks(options: LivePreviewOptions): Extension {
  const openRef = options.openRef ?? defaultOpenRef;
  const openUrl = options.openUrl ?? defaultOpenUrl;
  return EditorView.domEventHandlers({
    mousedown(event) {
      if (!(event.metaKey || event.ctrlKey) || event.button !== 0) return false;
      const target = (event.target as HTMLElement | null)?.closest?.("[data-lp-href]");
      const href = target?.getAttribute("data-lp-href");
      if (!href) return false;
      event.preventDefault();
      if (/^https?:\/\//i.test(href)) openUrl(href);
      else if (/^[a-z][a-z_]*:\S+$/i.test(href)) openRef(href);
      return true;
    },
  });
}

/** The live-preview extension for the Note's editor. */
export function livePreview(options: LivePreviewOptions = {}): Extension {
  return [inlinePlugin, tableField, linkClicks(options)];
}
