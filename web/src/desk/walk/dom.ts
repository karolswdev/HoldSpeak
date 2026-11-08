/** The walk's one DOM adapter (2026-11-07). The walk is an instrument over
 * the desk: its targets are selectors from the owner's walk script, so it
 * reads the desk's DOM where no React state of its own exists. Every lookup
 * of the walk is in this file, and only here (the null-read guard,
 * tests/unit/test_web_null_read_guard.py, names it). It reads; it never
 * writes the desk's DOM. */

/** A plain id is a `data-testid`; anything else is a CSS selector. */
export function selectorFor(target: string): string {
  return /^[A-Za-z][A-Za-z0-9_-]*$/.test(target) ? `[data-testid="${target}"]` : target;
}

function zOf(element: Element): number {
  const z = Number.parseInt(getComputedStyle(element).zIndex, 10);
  return Number.isFinite(z) ? z : 0;
}

/** Every desk window. */
function deskWindows(): HTMLElement[] {
  return Array.from(document.querySelectorAll<HTMLElement>("[data-layer='window']"));
}

/** The front window with this id (or `<id>:<scope>`), or null. */
export function frontWindow(id: string): HTMLElement | null {
  return deskWindows()
    .filter((element) => element.id === id || element.id.startsWith(`${id}:`))
    .sort((left, right) => zOf(right) - zOf(left))[0] ?? null;
}

/** True when the part is drawn: a part that is in the DOM but folded away
 * or hidden (a closed fold, `display: none`) is not there for the guide. The
 * walk asked about the Room's Programs fold at a zero rectangle instead of
 * saying "No Programs here yet" (owner, 2026-11-08). Where the page has a
 * layout (the browser), the part needs a box; where it has none (jsdom in a
 * test), the styles decide. */
export function isDrawn(element: HTMLElement): boolean {
  const laidOut = document.documentElement.getBoundingClientRect().width > 0;
  if (laidOut) {
    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }
  for (let node: HTMLElement | null = element; node; node = node.parentElement) {
    if (node.hidden) return false;
    const style = getComputedStyle(node);
    if (style.display === "none" || style.visibility === "hidden") return false;
  }
  return true;
}

/** True when this window is the front window of the desk: the highest
 * z-index among every desk window. On the phone the walk opened Needs you
 * behind the Programs window and asked about a window he could not see
 * (owner, 2026-11-08: "Doubt it is the right thing (right window opened…)"). */
export function isFrontWindow(element: HTMLElement): boolean {
  const z = zOf(element);
  return deskWindows().every((other) => other === element || zOf(other) <= z);
}

/** The first DRAWN match of a selector in a root, or null (a bad selector too). */
export function lookIn(root: ParentNode, selector: string): HTMLElement | null {
  try {
    const all = root.querySelectorAll<HTMLElement>(selector);
    for (const element of Array.from(all)) if (isDrawn(element)) return element;
    return null;
  } catch {
    return null;
  }
}

/** The first match on the desk outside the walk's own layer, or null. */
export function lookOnDesk(selector: string): HTMLElement | null {
  const anywhere = lookIn(document, selector);
  return anywhere && !anywhere.closest("[data-walk]") ? anywhere : null;
}

/** True while a part of the desk reads its first answer: the desk's own
 * `aria-busy` marker (the kit's loading face, the Surface state). */
export function walkLoading(root: ParentNode | null): boolean {
  return !!root?.querySelector("[aria-busy='true']");
}

// The compositor's flag "the hub's window list landed", loaded lazily: a
// static import makes a cycle through the window registry at module load
// (DeskApp → WalkRunner → walk → hubWindows → … → compositor/live).
let seeded: (() => boolean) | null = null;
/** Resolves when the compositor's flag is read; deskReady is false before. */
export const deskSignals: Promise<void> = import("../compositor/hubWindows").then(
  (module) => { seeded = module.hubSeeded; },
  () => undefined,
);

/** The desk's own drawn signals: the compositor restored its windows, the
 * desk's first read landed (`#desk-next` not busy), the Dock has a box, and
 * no window reads its first answer. */
export function deskReady(): boolean {
  if (typeof document === "undefined" || !seeded || !seeded()) return false;
  const desk = document.getElementById("desk-next");
  if (!desk || desk.getAttribute("aria-busy") === "true") return false;
  const dock = document.querySelector(".desk-dock");
  if (!dock || dock.getBoundingClientRect().height <= 0) return false;
  return !deskWindows().some(walkLoading);
}

/** The desk's dock height (the `--desk-dock-h` the dock sets), or 0. */
export function dockHeight(): number {
  if (typeof document === "undefined") return 0;
  return parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--desk-dock-h")) || 0;
}

/** The walk's two marks on a part: the halo (the part lifts and glows while
 * the guide asks about it) and the kit's pressed look for the guide's tap.
 * Each is taken off again by the same call with `on` false. */
export function markPart(element: HTMLElement, mark: "halo" | "pressed", on: boolean): void {
  if (mark === "halo") element.classList.toggle("walk-halo", on);
  else element.toggleAttribute("data-walk-pressed", on);
}
