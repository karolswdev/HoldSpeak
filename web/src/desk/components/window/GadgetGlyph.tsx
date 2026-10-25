// PHILO-13-11 (C1) — the Workbench 2.0 gadget glyphs. Window grammar
// (2026-10-24): 16 px glyphs with a real stroke weight (1.5 px ink), so the
// gadgets read at a glance on the tinted front title bar. The pen is
// currentColor (ink on paper bars, paper on the blue front bar); a white
// face is `--gadget-face` (the bar's own colour on the front bar). The shapes keep
// their Workbench meaning: close (a cross in the left gadget), iconify (the
// window falls to a block), zoom (a small rect in a big rect), depth (two
// overlapping rects, the front one white), size (two nested corners).
export type GadgetKind = "close" | "iconify" | "zoom" | "depth" | "size";

export function GadgetGlyph({ kind }: { kind: GadgetKind }) {
  const p = {
    width: 16,
    height: 16,
    viewBox: "0 0 16 16",
    "aria-hidden": true,
    focusable: false,
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.5,
    strokeLinecap: "round",
    strokeLinejoin: "round",
  } as const;
  switch (kind) {
    case "close":
      return (
        <svg {...p}>
          <path d="M4.5 4.5l7 7M11.5 4.5l-7 7" />
        </svg>
      );
    case "iconify":
      return (
        <svg {...p}>
          <rect x="2.25" y="2.75" width="11.5" height="10.5" rx="1.5" />
          <path d="M5 10.5h4" strokeWidth={2} />
        </svg>
      );
    case "zoom":
      return (
        <svg {...p}>
          <rect x="2.25" y="2.75" width="11.5" height="10.5" rx="1.5" />
          <rect x="4.25" y="4.75" width="4.5" height="3.5" rx="0.5" fill="currentColor" stroke="none" />
        </svg>
      );
    case "depth":
      return (
        <svg {...p}>
          <rect x="2.25" y="2.25" width="7.5" height="6.5" rx="1" />
          <rect x="6.25" y="7.25" width="7.5" height="6.5" rx="1" fill="var(--gadget-face, var(--wb-paper))" />
        </svg>
      );
    case "size":
      return (
        <svg {...p}>
          <rect x="6.25" y="6.25" width="7.5" height="7.5" rx="1" fill="var(--gadget-face, var(--wb-paper))" />
          <path d="M2.75 11V2.75H11" />
        </svg>
      );
  }
}
