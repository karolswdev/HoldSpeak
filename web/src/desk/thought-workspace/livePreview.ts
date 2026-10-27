/* The Note's live preview (owner 2026-10-27: "a powerful, delighting and also
   useful experience"). The note stays one CodeMirror document; every line the
   caret is NOT on shows as written text, the way Obsidian's live preview does:
   heading marks, emphasis marks, list marks, link urls, quote marks, fence
   marks and rules hide; a task is a real checkbox; a table is a real table.
   The line the caret is on shows its source again, at the same size, so
   nothing under the caret moves. Everything is Decorations (mark, replace,
   line, widget) over the Markdown syntax tree; the document text is the only
   copy. The mermaid fences are mermaidPreview.ts (same mechanism).

   Note canvas A, step 4: the objects the text names (a person, a Project, a
   decision, a meeting, a pull request, a Jira key) draw as a glyph and ink
   on the lines the caret is not on; a press opens the object's window; the
   pointer that rests on one for 400 ms shows its peek card (CSS only). Typing
   @ or # offers the people and the Projects; the choice is written as a
   plain Markdown link (`[@Priya](person:<id>)`). noteObjects.ts says what
   the desk knows about each one. */
import { autocompletion, type CompletionContext, type CompletionResult } from "@codemirror/autocomplete";
import { syntaxTree } from "@codemirror/language";
import { type EditorState, type Extension, type Range, StateEffect, StateField } from "@codemirror/state";
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
import {
  deskObjects,
  objectGlyph,
  pullRequestOf,
  refKind,
  type NoteObjectPeek,
  type NoteObjects,
  type NoteObjectToken,
} from "./noteObjects";

export interface LivePreviewOptions {
  /** Opens a desk object ref (`project:…`, `decision:…`). Return false when
   *  the ref is not one the desk opens. Default: openObject's refOpener. */
  openRef?: (ref: string) => boolean;
  /** Opens an external url. Default: a new browser tab. */
  openUrl?: (url: string) => void;
  /** W1-DOORS (atlas 2026-10-27): every line shows as written text until the
   *  editor first takes focus, so a note that opens with its caret on a task
   *  line does not open on that line's source. After the first focus the
   *  caret's lines show their source as before. */
  renderUntilFocus?: boolean;
  /** What the desk knows about the objects the text names, and the people
   *  and Projects that @ and # offer. Default: the desk store
   *  (noteObjects.ts). */
  objects?: NoteObjects;
}

type Context = {
  objects: NoteObjects;
  openRef: (ref: string) => boolean;
  openUrl: (url: string) => void;
};

/* ── the caret's lines ───────────────────────────────────────────────── */

/** The editor took focus once (only with `renderUntilFocus`). */
const firstFocus = StateEffect.define<null>();
const focusedOnce = StateField.define<boolean>({
  create: () => false,
  update: (value, tr) => value || tr.effects.some((effect) => effect.is(firstFocus)),
});
const untilFocus: Extension = [
  focusedOnce,
  EditorView.focusChangeEffect.of((state, focusing) =>
    focusing && !state.field(focusedOnce) ? firstFocus.of(null) : null),
];

/** True when any selection range touches [from, to]. Before the first focus
 *  of a `renderUntilFocus` editor, no line is touched. */
function touched(state: EditorState, from: number, to: number): boolean {
  if (state.field(focusedOnce, false) === false) return false;
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

/** An object the text names: a glyph and the words in their kind's ink,
 *  with the peek card inside it (shown by CSS after 400 ms of hover). A
 *  press opens the object when the desk can open it. */
class ObjectTokenWidget extends WidgetType {
  constructor(readonly token: NoteObjectToken, readonly peek: NoteObjectPeek, readonly open: (() => void) | null) {
    super();
  }

  eq(other: ObjectTokenWidget) {
    return other.token.kind === this.token.kind && other.token.label === this.token.label &&
      other.token.href === this.token.href && JSON.stringify(other.peek) === JSON.stringify(this.peek) &&
      Boolean(other.open) === Boolean(this.open);
  }

  toDOM() {
    const token = document.createElement("span");
    token.className = "cm-lp-obj";
    token.setAttribute("data-kind", this.token.kind);
    token.setAttribute("data-testid", "note-object");
    if (this.token.href) token.setAttribute("data-href", this.token.href);
    if (this.open) {
      token.setAttribute("data-opens", "");
      token.setAttribute("role", "link");
      token.setAttribute("aria-label", `Open ${this.peek.kind.toLowerCase()}: ${this.peek.name}`);
    }
    const glyph = document.createElement("img");
    glyph.className = "cm-lp-obj-glyph";
    glyph.src = objectGlyph(this.token.kind);
    glyph.alt = "";
    glyph.width = 14;
    glyph.height = 14;
    glyph.draggable = false;
    const words = document.createElement("span");
    words.className = "cm-lp-obj-text";
    words.textContent = this.token.label;
    token.append(glyph, words, this.peekCard());
    token.addEventListener("mousedown", (event) => {
      if (event.button !== 0) return;
      // The press opens the object; the caret stays where it is.
      event.preventDefault();
      this.open?.();
    });
    return token;
  }

  private peekCard() {
    const card = document.createElement("span");
    card.className = "cm-lp-peek";
    card.setAttribute("data-testid", "note-object-peek");
    card.setAttribute("aria-hidden", "true");
    const head = document.createElement("span");
    head.className = "cm-lp-peek-head";
    const glyph = document.createElement("img");
    glyph.src = objectGlyph(this.token.kind);
    glyph.alt = "";
    glyph.width = 20;
    glyph.height = 20;
    const name = document.createElement("span");
    name.className = "cm-lp-peek-name";
    name.textContent = this.peek.name;
    head.append(glyph, name);
    const line = document.createElement("span");
    line.className = "cm-lp-peek-line";
    line.textContent = [this.peek.kind, this.peek.fact].filter(Boolean).join(" · ");
    card.append(head, line);
    return card;
  }

  ignoreEvent() {
    return true;
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
    if (tr.docChanged || tr.selection || syntaxTree(tr.state) !== syntaxTree(tr.startState) ||
        tr.effects.some((effect) => effect.is(firstFocus))) return buildTables(tr.state);
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

/** The opener of an object token: a desk ref through the one open grammar,
 *  a pull request url in a new tab; null when nothing opens. */
function tokenOpener(token: NoteObjectToken, ctx: Context): (() => void) | null {
  const href = token.href;
  if (!href) return null;
  if (/^https?:\/\//i.test(href)) return () => ctx.openUrl(href);
  return refOpener(href) ? () => { ctx.openRef(href); } : null;
}

/* A pull request number (`#1482`, `PR #1482`) and a Jira key (`PAY-311`) in
   the words. Words that only look like a key are left alone. */
const PLAIN_OBJECT = /(^|[\s(\[])((?:PR\s+)?#(\d{1,7})(?![\w-])|([A-Z][A-Z0-9]{1,9}-\d{1,7})(?![\w-]))/g;
const NOT_JIRA = new Set(["UTF", "ISO", "SHA", "RFC", "TLS", "SSL", "MP", "COVID", "GPT"]);
/** Nodes whose words are never object tokens (code, links, raw html). */
const NO_TOKENS = new Set(["InlineCode", "FencedCode", "CodeBlock", "Link", "Autolink", "URL", "HTMLTag", "HTMLBlock", "Image", "Table", "LinkReference"]);

function buildInline(view: EditorView, ctx: Context): DecorationSet {
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
  /** Ranges the plain-word scan for PR numbers and Jira keys skips. */
  const busy: Array<[number, number]> = [];
  /** A number's pull request url, when the note holds one. */
  const prUrls = new Map<string, string>();
  for (const match of doc.toString().matchAll(/https?:\/\/(?:www\.)?github\.com\/[\w.-]+\/[\w.-]+\/pull\/(\d+)/gi))
    if (!prUrls.has(match[1])) prUrls.set(match[1], match[0]);
  const token = (kind: NoteObjectToken["kind"], label: string, href: string | null, at: number, end: number) => {
    const shown: NoteObjectToken = { kind, label, href };
    if (lineTouched(state, at)) {
      out.push(mark(`cm-lp-obj-ink${href ? " cm-lp-link" : ""}`, { "data-kind": kind, ...(href ? { "data-lp-href": href, title: href } : {}) }).range(at, end));
      return;
    }
    out.push(Decoration.replace({ widget: new ObjectTokenWidget(shown, ctx.objects.peek(shown), tokenOpener(shown, ctx)) }).range(at, end));
  };

  syntaxTree(state).iterate({
    from,
    to,
    enter(ref) {
      const name = ref.name;
      const node = ref.node;
      if (NO_TOKENS.has(name) && name !== "Link" && name !== "Autolink" && name !== "URL") busy.push([ref.from, ref.to]);

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
        busy.push([ref.from, ref.to]);
        const kind = refKind(href) ?? (pullRequestOf(href) ? "pr" : null);
        if (kind && textTo > textFrom) {
          token(kind, doc.sliceString(textFrom, textTo), href, ref.from, ref.to);
          return false;
        }
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
        busy.push([ref.from, ref.to]);
        const pr = pullRequestOf(href);
        if (pr) {
          token("pr", `PR #${pr.number}`, href, ref.from, ref.to);
          return false;
        }
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
        busy.push([ref.from, ref.to]);
        const pr = pullRequestOf(href);
        if (pr) {
          token("pr", `PR #${pr.number}`, href, ref.from, ref.to);
          return;
        }
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

  for (const range of view.visibleRanges) {
    const text = doc.sliceString(range.from, range.to);
    for (const match of text.matchAll(PLAIN_OBJECT)) {
      const at = range.from + (match.index ?? 0) + match[1].length;
      const end = at + match[2].length;
      if (busy.some(([a, b]) => at < b && end > a)) continue;
      if (match[3]) token("pr", match[2].replace(/\s+/, " "), prUrls.get(match[3]) ?? null, at, end);
      else if (match[4] && !NOT_JIRA.has(match[4].split("-")[0])) token("jira", match[4], null, at, end);
    }
  }

  for (const [at, classes] of lines) out.push(line(classes.join(" ")).range(at));
  return Decoration.set(out, true);
}

/** The People roster (or another slow read of the objects) came in. */
const objectsReady = StateEffect.define<null>();

const inlinePlugin = (ctx: Context) => ViewPlugin.fromClass(
  class {
    decorations: DecorationSet;

    constructor(view: EditorView) {
      this.decorations = buildInline(view, ctx);
      void ctx.objects.ready?.().then(() => {
        if (view.dom.isConnected) view.dispatch({ effects: objectsReady.of(null) });
      }, () => undefined);
    }

    update(update: ViewUpdate) {
      if (update.docChanged || update.selectionSet || update.viewportChanged ||
          syntaxTree(update.state) !== syntaxTree(update.startState) ||
          update.state.field(focusedOnce, false) !== update.startState.field(focusedOnce, false) ||
          update.transactions.some((tr) => tr.effects.some((effect) => effect.is(objectsReady))))
        this.decorations = buildInline(update.view, ctx);
    }
  },
  { decorations: (plugin) => plugin.decorations },
);

/* ── @ and # : the people and the Projects ───────────────────────────── */

const TRIGGER = /[@#][\p{L}\p{N}_.'-]*/u;
const NO_COMPLETION = new Set(["InlineCode", "FencedCode", "CodeBlock", "CodeText", "Link", "URL", "Autolink"]);

function markdownText(name: string): string {
  return name.replace(/([\\[\]])/g, "\\$1");
}

/** The completion source: @ offers the people, # the Projects. The choice
 *  is written as a plain Markdown link. */
export function objectCompletions(objects: NoteObjects) {
  return async (context: CompletionContext): Promise<CompletionResult | null> => {
    const match = context.matchBefore(TRIGGER);
    if (!match) return null;
    const before = match.from > 0 ? context.state.sliceDoc(match.from - 1, match.from) : "";
    if (before && !/[\s([]/.test(before)) return null;
    const trigger = match.text[0] as "@" | "#";
    const query = match.text.slice(1);
    if (trigger === "#" && /^\d/.test(query)) return null; // a pull request number
    // `#` then a space at the start of a line is a heading.
    if (trigger === "#" && !query && context.state.doc.lineAt(match.from).from === match.from) return null;
    for (let node: SyntaxNode | null = syntaxTree(context.state).resolveInner(match.from, 1); node; node = node.parent)
      if (NO_COMPLETION.has(node.name)) return null;
    const choices = trigger === "@" ? await objects.people() : objects.projects();
    if (context.aborted || !choices.length) return null;
    const scheme = trigger === "@" ? "person" : "project";
    return {
      from: match.from + 1,
      validFor: /^[\p{L}\p{N}_.'-]*$/u,
      options: choices.map((choice) => ({
        label: choice.name,
        detail: choice.detail,
        type: scheme,
        apply: (view: EditorView, _completion: unknown, from: number, to: number) => {
          const insert = `[${trigger}${markdownText(choice.name)}](${scheme}:${choice.id})`;
          view.dispatch({
            changes: { from: from - 1, to, insert },
            selection: { anchor: from - 1 + insert.length },
            userEvent: "input.complete",
          });
        },
      })),
    };
  };
}

function objectCompletion(objects: NoteObjects): Extension {
  return autocompletion({
    override: [objectCompletions(objects)],
    icons: false,
    tooltipClass: () => "cm-lp-complete",
    optionClass: () => "cm-lp-complete-option",
    addToOptions: [{
      position: 20,
      render: (completion) => {
        const glyph = document.createElement("img");
        glyph.className = "cm-lp-complete-glyph";
        glyph.src = objectGlyph(completion.type === "person" ? "person" : "project");
        glyph.alt = "";
        glyph.width = 16;
        glyph.height = 16;
        return glyph;
      },
    }],
  });
}

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

function linkClicks(ctx: Context): Extension {
  const { openRef, openUrl } = ctx;
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
  const ctx: Context = {
    objects: options.objects ?? deskObjects,
    openRef: options.openRef ?? defaultOpenRef,
    openUrl: options.openUrl ?? defaultOpenUrl,
  };
  return [...(options.renderUntilFocus ? [untilFocus] : []), inlinePlugin(ctx), tableField, linkClicks(ctx), objectCompletion(ctx.objects)];
}
