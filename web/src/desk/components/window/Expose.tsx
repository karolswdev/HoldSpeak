// Exposé — every shown window as a live plate (PHILO-16 §5; HS-97-06 before).
//
// The plates are the windows themselves: the compositor draws each window's
// own element at its own size, scaled by `--k` into its grid cell (it
// scales, it never reflows), with its own title bar (§7). This overlay adds
// the veil and one pick target per plate: a press or Enter picks that
// window; Esc (the compositor) returns every window to its remembered rect.
//
// W7 (canvas 2026-10-28 (a), direction A "Captions on a slate veil"): the
// plate keeps its own title bar; at k ≈ 0.5 that text does not read, so a
// paper caption 8 px under each plate is the name you can read (its 20 px
// glyph, its name, a 3 px rule in its kind hue). The front window wears a
// 3 px vivid-blue ring and a blue caption, and the first focus lands on it.
import { cloneElement, isValidElement, useEffect, useRef, type CSSProperties, type ReactElement, type ReactNode } from "react";
import { useAllOpenWindows, useFrontWindowId } from "./windowRegistry";
import { windowIcons } from "./seatIcons";
import { glyphSprite } from "../../sprites";
import { Button } from "../../../components/signal/Signal";
import {
  exposePick,
  toggleExposeMode,
  usePresentation,
} from "../../compositor/useCompositor";
import { plateVisual } from "../../compositor/geometry";

/** The Overview verb, the Dock's button and ⌘⇧E (⌃↑) reach this one toggle. */
export function toggleExpose(force?: boolean) {
  toggleExposeMode(force);
}

/** The kind hue of a window's caption rule: its announced kind word, else
 * the Workbench blue (--kind-other) for an app or a window with no kind. */
export function captionHue(kind: string | undefined): string {
  const k = (kind ?? "").trim().toLowerCase();
  if (k.startsWith("decision")) return "var(--kind-decision)";
  if (k.startsWith("project")) return "var(--kind-project)";
  if (k.startsWith("note") || k.startsWith("thought")) return "var(--kind-note)";
  if (k.startsWith("meeting")) return "var(--kind-meeting)";
  if (k.startsWith("person") || k.startsWith("people")) return "var(--kind-person)";
  if (k.startsWith("agent") || k.startsWith("coder")) return "var(--kind-agent)";
  return "var(--kind-other)";
}

/** The caption's 20 px glyph: the window's title-bar icon drawn at 20, else
 * its registry glyph. */
function captionGlyph(id: string, glyph: string): ReactNode {
  const icon = windowIcons.get(id);
  if (isValidElement<{ src?: unknown }>(icon) && icon.type === "img" && typeof icon.props.src === "string") {
    return cloneElement(icon as ReactElement<Record<string, unknown>>, {
      src: glyphSprite(icon.props.src),
      width: 20,
      height: 20,
    });
  }
  return icon ?? <span className="desk-expose-caption-char">{glyph}</span>;
}

export function Expose() {
  const presentation = usePresentation();
  const windows = useAllOpenWindows();
  const front = useFrontWindowId();
  const firstBtnRef = useRef<HTMLButtonElement | null>(null);
  const active = presentation.mode === "expose";

  useEffect(() => {
    if (active) firstBtnRef.current?.focus({ preventScroll: true });
  }, [active]);

  if (!active) return null;
  const entries = windows.filter((w) => presentation.plates[w.id]);
  if (entries.length === 0) return null;
  // The first focus goes to the front plate; with no front, the first plate.
  const focusId = entries.some((en) => en.id === front) ? front : entries[0].id;
  return (
    <>
      <div className="desk-expose-scrim" aria-hidden="true" />
      <div
        className="desk-expose"
        // A region, not a dialog: the desk's no-modal law holds -- no
        // trap, Escape and the backdrop dismiss (Phase 73 lock).
        role="group"
        aria-label="Window overview"
        onClick={(e) => {
          if (e.target === e.currentTarget) toggleExpose(false);
        }}
      >
        {entries.map((en) => {
          const plate = presentation.plates[en.id];
          const v = plateVisual(plate.rect, plate.k ?? 1);
          const isFront = en.id === front;
          return (
            <Button
              variant="chrome"
              key={en.id}
              ref={en.id === focusId ? firstBtnRef : undefined}
              className="desk-expose-cell is-plate"
              data-front={isFront ? "" : undefined}
              style={{ top: v.y, left: v.x, width: v.w, height: v.h }}
              aria-label={`Focus ${en.label}`}
              title={en.label}
              onClick={() => exposePick(en.id)}
            >
              <span
                className="desk-expose-caption"
                data-testid="desk-expose-caption"
                aria-hidden="true"
                style={{ "--k": captionHue(en.kind) } as CSSProperties}
              >
                {captionGlyph(en.id, en.glyph)}
                <span className="desk-expose-caption-name">{en.label}</span>
              </span>
            </Button>
          );
        })}
      </div>
    </>
  );
}
