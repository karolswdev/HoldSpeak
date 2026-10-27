// The Note margin as a drawer (a window under 720 px, thought-workspace.css):
// the drawer lies over the foot of the page, so the last lines of a short
// note sat under it with no room to scroll them up. A caret put back there
// (Back to Thought from Ask, the changed-source return) was painted under
// the drawer's verbs: a press on that line hit "Add to note".
//
// This extension gives the editor room under its last line as tall as the
// part of the drawer that covers the editor, and tells CodeMirror's
// scroll-into-view about it (scrollMargins), so a caret is always brought
// above the drawer. With no drawer (a wide window, an empty margin) it
// adds nothing.
import { EditorView, ViewPlugin, type ViewUpdate } from "@codemirror/view";

function drawerOverlap(view: EditorView): number {
  const doc = view.dom.closest(".thought-note-document");
  const drawer = doc?.querySelector<HTMLElement>(":scope > .note-margin");
  if (!drawer || getComputedStyle(drawer).position !== "absolute") return 0;
  const scroller = view.scrollDOM.getBoundingClientRect();
  const box = drawer.getBoundingClientRect();
  return Math.max(0, Math.round(scroller.bottom - Math.max(box.top, scroller.top)));
}

const room = ViewPlugin.fromClass(class {
  overlap = 0;
  private observer: MutationObserver | null = null;
  private sizes: ResizeObserver | null = null;
  constructor(private view: EditorView) {
    const doc = view.dom.closest(".thought-note-document");
    if (doc && typeof MutationObserver !== "undefined") {
      this.observer = new MutationObserver(() => this.watch());
      this.observer.observe(doc, { childList: true });
    }
    this.watch();
  }
  /** Follow the drawer's size while it is there. */
  watch() {
    this.sizes?.disconnect();
    this.sizes = null;
    const drawer = this.view.dom.closest(".thought-note-document")?.querySelector<HTMLElement>(":scope > .note-margin");
    if (drawer && typeof ResizeObserver !== "undefined") {
      this.sizes = new ResizeObserver(() => this.measure());
      this.sizes.observe(drawer);
    }
    this.measure();
  }
  measure() {
    const next = drawerOverlap(this.view);
    if (next === this.overlap) return;
    this.overlap = next;
    this.view.contentDOM.style.paddingBottom = next ? `${next}px` : "";
    this.view.requestMeasure();
  }
  update(update: ViewUpdate) {
    if (update.geometryChanged) this.measure();
  }
  destroy() {
    this.observer?.disconnect();
    this.sizes?.disconnect();
    this.view.contentDOM.style.paddingBottom = "";
  }
});

export function marginDrawerRoom() {
  return [
    room,
    EditorView.scrollMargins.of((view) => {
      const overlap = view.plugin(room)?.overlap ?? 0;
      return overlap ? { bottom: overlap } : null;
    }),
  ];
}
