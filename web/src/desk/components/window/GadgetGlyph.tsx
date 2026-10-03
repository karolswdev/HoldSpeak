// PHILO-13-11 (C1) — the Workbench 2.0 gadget glyphs, drawn crisp at 1x and
// 2x (the ratified canvas, `assets/story-11-canvas/harness/p13.tsx`). Pen 1
// (--wb-ink) draws every line; pen 2 (--wb-paper) fills the white parts.
export type GadgetKind = "close" | "iconify" | "zoom" | "depth" | "size";

export function GadgetGlyph({ kind }: { kind: GadgetKind }) {
  const p = {
    width: 14,
    height: 12,
    viewBox: "0 0 14 12",
    "aria-hidden": true,
    focusable: false,
    shapeRendering: "crispEdges",
  } as const;
  switch (kind) {
    case "close": // 2.0: a small square in the middle of the gadget
      return (
        <svg {...p}>
          <rect x="4.5" y="3.5" width="5" height="5" fill="var(--wb-paper)" stroke="var(--wb-ink)" />
        </svg>
      );
    case "iconify": // 3.9: the window falls to a small block, bottom left
      return (
        <svg {...p}>
          <rect x="1.5" y="1.5" width="11" height="9" fill="none" stroke="var(--wb-ink)" />
          <rect x="2" y="7" width="5" height="3" fill="var(--wb-ink)" />
        </svg>
      );
    case "zoom": // 2.0: a small rect at the top left of a big rect
      return (
        <svg {...p}>
          <rect x="1.5" y="1.5" width="11" height="9" fill="var(--wb-paper)" stroke="var(--wb-ink)" />
          <rect x="2" y="2" width="5" height="4" fill="var(--wb-ink)" />
        </svg>
      );
    case "depth": // 2.0: two overlapping rects; the front one white
      return (
        <svg {...p}>
          <rect x="1.5" y="1.5" width="7" height="6" fill="none" stroke="var(--wb-ink)" />
          <rect x="5.5" y="4.5" width="7" height="6" fill="var(--wb-paper)" stroke="var(--wb-ink)" />
        </svg>
      );
    case "size": // 2.0: the sizing gadget, two nested corners
      return (
        <svg {...p}>
          <rect x="5.5" y="4.5" width="7" height="6" fill="var(--wb-paper)" stroke="var(--wb-ink)" />
          <path d="M2.5 9.5V1.5h8" fill="none" stroke="var(--wb-ink)" />
        </svg>
      );
  }
}
