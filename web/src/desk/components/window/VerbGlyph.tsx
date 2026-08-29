// VerbGlyph — the window verb SVG path map.
// Extracted from DeskWindow.tsx (HS-117-04).

/** HS-99-02 — the window verb glyphs: crisp inline SVG strokes that
 * inherit currentColor (text glyphs read as characters, not chrome). */
export function VerbGlyph({ kind }: { kind: string }) {
  const paths: Record<string, string> = {
    minimize: "M3 7h8",
    maximize: "M3.5 3.5h7v7h-7Z",
    restore: "M3 5.2h5.8V11H3Z M5.2 5.2V3H11v5.8H8.8",
    close: "M3.5 3.5l7 7M10.5 3.5l-7 7",
    "light-close": "M3.6 3.6l6.8 6.8M10.4 3.6l-6.8 6.8",
    "light-min": "M3 7h8",
    "light-max": "M7 3v8M3 7h8",
    "light-restore": "M4 7h6M7 4l-3 3 3 3M7 4l3 3-3 3",
    // HS-111-09 — the dock verbs join the one SVG glyph language (the
    // dingbats were kit-law leaks): overview = the 2x2 window
    // grid, reset = the return loop.
    overview: "M3 3.5h3.2v3.2H3Z M7.8 3.5H11v3.2H7.8Z M3 8.3h3.2v3.2H3Z M7.8 8.3H11v3.2H7.8Z",
    reset: "M11 7a4 4 0 1 1-1.55-3.16 M9.2 2.2l.55 1.9-1.9.55",
    // HS-148-01 — checkable lane marks (the Amiga toggle grammar):
    // square-check for boolean toggles, circle-dot for mutual-exclude.
    check: "M3 3h8v8H3Z M5.2 7l1.6 1.6 2.4-3.2",
  };
  // HS-148-01: circle-dot needs a filled inner dot — special-cased.
  if (kind === "dot") {
    return (
      <svg
        viewBox="0 0 14 14"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <circle cx="7" cy="7" r="4" />
        <circle cx="7" cy="7" r="2" fill="currentColor" stroke="none" />
      </svg>
    );
  }
  return (
    <svg
      viewBox="0 0 14 14"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.3"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[kind]} />
    </svg>
  );
}
