/* The Note's diagrams (owner 2026-10-27: "there doesn't seem to be a mermaid
   renderer"). Every ```mermaid fence in the note shows as its drawn diagram
   while the caret is outside it; when the caret enters the fence, the source
   shows again (the live-preview way). mermaid loads lazily, once, on the first
   fence seen, so a note without a diagram never pays for it. */
import { type EditorState, type Extension, type Range, StateField } from "@codemirror/state";
import { Decoration, type DecorationSet, EditorView, WidgetType } from "@codemirror/view";

type MermaidApi = {
  initialize: (config: Record<string, unknown>) => void;
  render: (id: string, text: string) => Promise<{ svg: string }>;
};

type Rendered = { svg: string } | { error: string };

let loading: Promise<MermaidApi> | null = null;
let renderSeq = 0;
const cache = new Map<string, Rendered>();
const pending = new Map<string, Promise<Rendered>>();
const heights = new Map<string, number>();

/** A desk token as a colour mermaid can read (a hex or an rgb value). */
function token(name: string, fallback: string): string {
  if (typeof document === "undefined") return fallback;
  const raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  if (!raw) return fallback;
  if (/^#[0-9a-f]{3,8}$/i.test(raw) || /^rgba?\(/i.test(raw)) return raw;
  try {
    const ctx = document.createElement("canvas").getContext("2d");
    if (!ctx) return fallback;
    ctx.fillStyle = fallback;
    ctx.fillStyle = raw;
    return ctx.fillStyle;
  } catch {
    return fallback;
  }
}

function loadMermaid(): Promise<MermaidApi> {
  if (!loading) {
    loading = import("mermaid").then((module) => {
      const mermaid = (module.default ?? module) as unknown as MermaidApi;
      const ink = token("--wb-ink", "#253449");
      const paper = token("--wb-paper", "#fafbfc");
      const sel = token("--wb-sel", "#3b5d93");
      const rule = token("--wb-rule", "#c5cfdd");
      const font = typeof document === "undefined"
        ? "Inter, system-ui, sans-serif"
        : getComputedStyle(document.documentElement).getPropertyValue("--font-ui").trim() || "Inter, system-ui, sans-serif";
      mermaid.initialize({
        startOnLoad: false,
        securityLevel: "strict",
        suppressErrorRendering: true,
        logLevel: 5,
        theme: "base",
        fontFamily: font,
        themeVariables: {
          background: paper,
          mainBkg: paper,
          primaryColor: paper,
          primaryBorderColor: sel,
          primaryTextColor: ink,
          secondaryColor: paper,
          tertiaryColor: paper,
          lineColor: sel,
          textColor: ink,
          nodeBorder: sel,
          clusterBkg: paper,
          clusterBorder: rule,
          edgeLabelBackground: paper,
          fontFamily: font,
          fontSize: "14px",
        },
      });
      return mermaid;
    });
    loading.catch(() => { loading = null; });
  }
  return loading;
}

function firstLine(error: unknown): string {
  const text = error instanceof Error ? error.message : String(error ?? "");
  return text.split("\n").map((line) => line.trim()).find(Boolean) ?? "unknown error";
}

function renderDiagram(source: string): Promise<Rendered> {
  const done = cache.get(source);
  if (done) return Promise.resolve(done);
  const running = pending.get(source);
  if (running) return running;
  const job = loadMermaid()
    .then((mermaid) => mermaid.render(`hs-mermaid-${++renderSeq}`, source))
    .then(({ svg }) => ({ svg }) as Rendered, (error: unknown) => ({ error: firstLine(error) }) as Rendered)
    .then((result) => {
      cache.set(source, result);
      pending.delete(source);
      return result;
    });
  pending.set(source, job);
  return job;
}

class MermaidWidget extends WidgetType {
  constructor(readonly source: string, readonly sourceFrom: number) {
    super();
  }

  eq(other: MermaidWidget) {
    return other.source === this.source;
  }

  get estimatedHeight() {
    return heights.get(this.source) ?? 120;
  }

  toDOM(view: EditorView) {
    const box = document.createElement("div");
    box.className = "cm-mermaid";
    box.setAttribute("data-testid", "note-mermaid");
    box.setAttribute("data-state", "rendering");
    box.style.minHeight = `${heights.get(this.source) ?? 120}px`;
    // A press on the diagram puts the caret in its source (the fence opens).
    box.addEventListener("mousedown", (event) => {
      if (event.button !== 0) return;
      event.preventDefault();
      const at = Math.min(this.sourceFrom, view.state.doc.length);
      view.dispatch({ selection: { anchor: at } });
      view.focus();
    });
    const paint = (result: Rendered) => {
      if ("svg" in result) {
        box.setAttribute("data-state", "drawn");
        box.innerHTML = result.svg;
      } else {
        box.setAttribute("data-state", "failed");
        const code = document.createElement("pre");
        code.className = "cm-mermaid-source";
        code.textContent = this.source;
        const line = document.createElement("p");
        line.className = "cm-mermaid-error";
        line.textContent = `Diagram did not render: ${result.error}`;
        box.replaceChildren(code, line);
      }
      box.style.minHeight = "";
      requestAnimationFrame(() => {
        const h = box.getBoundingClientRect().height;
        if (h > 0) heights.set(this.source, h);
        view.requestMeasure();
      });
    };
    const ready = cache.get(this.source);
    if (ready) paint(ready);
    else void renderDiagram(this.source).then(paint);
    return box;
  }

  ignoreEvent() {
    return false;
  }
}

/** The ```mermaid fences of a document: the whole fence and its source. */
export function mermaidFences(state: EditorState): { from: number; to: number; sourceFrom: number; source: string }[] {
  const out: { from: number; to: number; sourceFrom: number; source: string }[] = [];
  const doc = state.doc;
  for (let n = 1; n <= doc.lines; n++) {
    const open = doc.line(n);
    if (!/^\s{0,3}```\s*mermaid\s*$/i.test(open.text)) continue;
    for (let m = n + 1; m <= doc.lines; m++) {
      const close = doc.line(m);
      if (!/^\s{0,3}```\s*$/.test(close.text)) continue;
      const body = m > n + 1 ? doc.sliceString(doc.line(n + 1).from, doc.line(m - 1).to) : "";
      if (body.trim()) out.push({ from: open.from, to: close.to, sourceFrom: m > n + 1 ? doc.line(n + 1).from : open.to, source: body });
      n = m;
      break;
    }
  }
  return out;
}

function build(state: EditorState): DecorationSet {
  const fences = mermaidFences(state);
  if (!fences.length) return Decoration.none;
  const ranges = state.selection.ranges;
  const marks: Range<Decoration>[] = [];
  for (const fence of fences) {
    const inside = ranges.some((range) => range.to >= fence.from && range.from <= fence.to);
    if (inside) continue;
    marks.push(Decoration.replace({ widget: new MermaidWidget(fence.source, fence.sourceFrom), block: true }).range(fence.from, fence.to));
  }
  return Decoration.set(marks);
}

const mermaidField = StateField.define<DecorationSet>({
  create: build,
  update(value, tr) {
    return tr.docChanged || tr.selection ? build(tr.state) : value;
  },
  provide: (field) => EditorView.decorations.from(field),
});

/** The live-preview extension for the Note's editor. */
export function mermaidPreview(): Extension {
  return mermaidField;
}

/** Test seam: forget drawn diagrams. */
export function resetMermaidPreview() {
  cache.clear();
  pending.clear();
  heights.clear();
  loading = null;
}
