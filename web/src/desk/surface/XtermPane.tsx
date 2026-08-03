// HS-111-11 — the xterm interior of the PaneWell (lazy chunk).
//
// A VIEWER, never an input: `disableStdin` is set, no `onData` handler
// exists anywhere in this file, and nothing here imports a send path —
// typing reaches a pane only through the armed steer composer
// (Article XI / Phase 87 law). The chunk lazy-loads with the pullout so
// the desk's first paint never pays for a terminal emulator.
//
// Material: Signal Workbench, not stock xterm — the screen is the
// OPAQUE terminal-screen token (set on the container BEFORE open(), so
// there is no white flash), mono from the house token, a steady block
// cursor (no blink, no glow), selection in the accent tint.
import { useEffect, useMemo, useRef } from "react";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { SearchAddon } from "@xterm/addon-search";
import "@xterm/xterm/css/xterm.css";

/** Pane geometry + cursor riding a raw peek (HS-111-11 wire). */
export interface PaneGeometry {
  width: number;
  height: number;
  cursorX: number;
  cursorY: number;
}

/** A search order from the well head: `query` re-finds incrementally,
 * bumping `seq` advances to the next match (Enter in the gadget). */
export interface SearchOrder {
  query: string;
  seq: number;
}

function tokenValue(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  return value || fallback;
}

/** The Signal Workbench terminal theme, read from the live tokens.
 * ANSI slots with a semantic house counterpart use it (ok/warn/danger/
 * accent-cool); the rest are curated to sit on the same dark screen. */
export function workbenchTerminalTheme() {
  const screen = tokenValue("--desk-terminal-screen", "#0f1115");
  const text = tokenValue("--text", "#f2f3f5");
  return {
    background: screen,
    foreground: text,
    cursor: text,
    cursorAccent: screen,
    selectionBackground: tokenValue("--accent-tint", "rgba(168, 110, 74, 0.12)"),
    selectionForeground: undefined as string | undefined,
    black: tokenValue("--surface-1", "#15171d"),
    red: tokenValue("--danger-signal", "#f87171"),
    green: tokenValue("--ok", "#34d399"),
    yellow: tokenValue("--warn-signal", "#fbbf24"),
    blue: tokenValue("--accent-cool", "#5b8def"),
    magenta: "#c084fc",
    cyan: "#67e8f9",
    white: "#d6d9e0",
    brightBlack: tokenValue("--text-muted", "#9ba2b0"),
    brightRed: "#fca5a5",
    brightGreen: tokenValue("--ok-strong", "#10b981"),
    brightYellow: tokenValue("--warn-strong", "#f59e0b"),
    brightMagenta: "#d8b4fe",
    brightCyan: "#a5f3fc",
    brightBlue: "#93b4f5",
    brightWhite: text,
  };
}

const CLEAR = "[3J[2J[H"; // scrollback + screen + home
const SEARCH_DECORATIONS = {
  matchOverviewRuler: "#fbbf24",
  activeMatchColorOverviewRuler: "#a86e4a",
  matchBackground: "#3f3520",
  activeMatchBackground: "#7a3a1d",
};

export default function XtermPane({
  raw,
  pane,
  search,
}: {
  /** The full raw ANSI snapshot; every change is one clear+write
   * repaint (the story's honest first step — no streaming). */
  raw: string;
  /** tmux geometry when the wire names it: the terminal sizes itself
   * to the PANE so wrapped layout stays faithful, and the block cursor
   * parks where the pane's cursor sits. Absent: fit to the well. */
  pane?: PaneGeometry | null;
  search?: SearchOrder;
}) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const termRef = useRef<Terminal | null>(null);
  const fitRef = useRef<FitAddon | null>(null);
  const searchRef = useRef<SearchAddon | null>(null);
  const theme = useMemo(() => workbenchTerminalTheme(), []);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const term = new Terminal({
      disableStdin: true, // a viewer — keystrokes never become pane input
      allowProposedApi: true, // search decorations
      convertEol: true,
      cursorBlink: false,
      cursorStyle: "block",
      scrollback: 4000,
      fontFamily: tokenValue("--font-mono", "JetBrains Mono, monospace"),
      fontSize: 11,
      lineHeight: 1.2,
      theme,
    });
    const fit = new FitAddon();
    const finder = new SearchAddon();
    term.loadAddon(fit);
    term.loadAddon(finder);
    term.open(host);
    // Copy-on-select: the operator's utility, still read-only.
    term.onSelectionChange(() => {
      const selected = term.getSelection();
      if (selected) void navigator.clipboard?.writeText(selected).catch(() => {});
    });
    termRef.current = term;
    fitRef.current = fit;
    searchRef.current = finder;
    return () => {
      searchRef.current = null;
      fitRef.current = null;
      termRef.current = null;
      term.dispose();
    };
    // The theme is token-derived and stable for the mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Full repaint on poll: clear + snapshot + cursor park in ONE write —
  // xterm coalesces it into a single frame, so there is no flicker.
  useEffect(() => {
    const term = termRef.current;
    if (!term) return;
    if (pane && pane.width > 0 && pane.height > 0) {
      if (term.cols !== pane.width || term.rows !== pane.height) {
        term.resize(pane.width, pane.height);
      }
    } else if (fitRef.current) {
      try {
        fitRef.current.fit();
      } catch {
        /* a zero-size host mid-layout — the next repaint fits */
      }
    }
    const park = pane
      ? `[${pane.cursorY + 1};${pane.cursorX + 1}H`
      : "";
    term.write(CLEAR + raw + park, () => term.scrollToBottom());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [raw, pane?.width, pane?.height, pane?.cursorX, pane?.cursorY]);

  // The well-head search gadget drives the addon: typing refines the
  // current match in place (incremental), Enter (a seq bump) advances
  // to the next one.
  useEffect(() => {
    const finder = searchRef.current;
    if (!finder) return;
    if (!search || !search.query) {
      finder.clearDecorations();
      return;
    }
    finder.findNext(search.query, {
      incremental: true,
      decorations: SEARCH_DECORATIONS,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search?.query]);
  useEffect(() => {
    const finder = searchRef.current;
    if (!finder || !search || !search.query || !search.seq) return;
    finder.findNext(search.query, {
      incremental: false,
      decorations: SEARCH_DECORATIONS,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search?.seq]);

  return <div ref={hostRef} className="terminal-well-screen" />;
}
