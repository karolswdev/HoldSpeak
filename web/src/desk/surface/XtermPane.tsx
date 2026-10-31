// HS-111-11 — the xterm interior of the PaneWell (lazy chunk).
//
// A shared terminal interior: read-only by default, with an opt-in input
// callback for a controller that already owns the target, grant and focus.
// The renderer never discovers or selects a session. The chunk lazy-loads with
// the pullout so the desk's first paint never pays for a terminal emulator.
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
  // The desk's ordinary `--text` is dark Workbench ink for pale wells. The
  // terminal screen is intentionally dark, so use the existing light-on-deep
  // token instead of making terminal output disappear in the browser.
  const text = tokenValue("--text-on-accent", "#f7f9fc");
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

const CLEAR = "[2J[H"; // screen + home; keep scrollback for scrolled viewers
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
  onData,
  focusSignal,
  copyOnSelect = true,
  inputEnabled = Boolean(onData),
  onFocus,
}: {
  /** The full raw ANSI snapshot; every change is one clear+write
   * repaint (the story's honest first step — no streaming). */
  raw: string;
  /** tmux geometry when the wire names it: the terminal sizes itself
   * to the PANE so wrapped layout stays faithful, and the block cursor
   * parks where the pane's cursor sits. Absent: fit to the well. */
  pane?: PaneGeometry | null;
  search?: SearchOrder;
  /** Optional owner input seam. Omitted for the ordinary read-only panes. */
  onData?: (data: string) => void;
  /** Increment to focus the xterm without remounting its emulator. */
  focusSignal?: number | string;
  /** Copy selected text to the system clipboard. Defaults to true. */
  copyOnSelect?: boolean;
  /** Enables stdin only when the owning controller has granted posture. */
  inputEnabled?: boolean;
  /** Called when the terminal's own textarea receives focus. */
  onFocus?: () => void;
}) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const termRef = useRef<Terminal | null>(null);
  const fitRef = useRef<FitAddon | null>(null);
  const searchRef = useRef<SearchAddon | null>(null);
  const onDataRef = useRef(onData);
  const copyRef = useRef(copyOnSelect);
  const inputRef = useRef(inputEnabled);
  const focusCallbackRef = useRef(onFocus);
  const lastFrameRef = useRef<string | null>(null);
  const hasGeometry = Boolean(pane && pane.width > 0 && pane.height > 0);
  onDataRef.current = onData;
  copyRef.current = copyOnSelect;
  inputRef.current = inputEnabled;
  focusCallbackRef.current = onFocus;
  const theme = useMemo(() => workbenchTerminalTheme(), []);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const term = new Terminal({
      disableStdin: !inputEnabled,
      allowProposedApi: true, // search decorations
      convertEol: true,
      cursorBlink: false,
      cursorStyle: "block",
      scrollback: 4000,
      fontFamily: tokenValue("--font-mono", "\"JetBrains Mono\", \"JetBrains Mono Fallback\", monospace"),
      fontSize: 12,
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
      if (!copyRef.current) return;
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

  // Attach/detach stdin independently of the callback identity. This keeps a
  // controller rerender from destroying xterm's scrollback and selection.
  useEffect(() => {
    const term = termRef.current;
    if (!term) return;
    // xterm reads this option at event time. Keep the emulator mounted while
    // posture changes, but make the read-only boundary explicit on the live
    // instance as well as in the constructor options.
    term.options.disableStdin = !inputEnabled;
    if (!inputEnabled) return;
    const input = term.onData((data) => onDataRef.current?.(data));
    return () => {
      input.dispose();
      if (termRef.current === term) term.options.disableStdin = true;
    };
  }, [inputEnabled]);

  useEffect(() => {
    if (focusSignal === undefined || focusSignal === 0) return;
    termRef.current?.focus();
  }, [focusSignal]);

  // A no-geometry consumer (including a resized normal Desk frame) uses the
  // host's own dimensions rather than a one-time fit at mount.
  useEffect(() => {
    if (hasGeometry || !hostRef.current || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => {
      try {
        fitRef.current?.fit();
      } catch {
        /* zero-size host during a frame transition; next resize will fit */
      }
    });
    observer.observe(hostRef.current);
    return () => observer.disconnect();
  }, [hasGeometry]);

  // Full repaint on poll: clear + snapshot + cursor park in ONE write —
  // xterm coalesces it into a single frame, so there is no flicker. Keep the
  // prior viewport when the owner was reading above the tail.
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
    const frame = CLEAR + raw + park;
    if (lastFrameRef.current === frame) return;
    const active = term.buffer?.active;
    const viewportY = active?.viewportY ?? 0;
    const followTail = !active || viewportY >= active.baseY;
    lastFrameRef.current = frame;
    term.write(frame, () => {
      // The view can close while the write is pending; a disposed terminal
      // has no render service, so a scroll then throws (TERMINAL-REDS).
      if (termRef.current !== term) return;
      if (followTail) term.scrollToBottom();
      else if (typeof term.scrollToLine === "function") term.scrollToLine(viewportY);
    });
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

  return (
    <div
      ref={hostRef}
      className="terminal-well-screen"
      onFocus={() => focusCallbackRef.current?.()}
      onKeyDown={(event) => {
        // Escape belongs to the focused TUI when input is enabled. Letting it
        // bubble to DeskWindow would close the window instead.
        if (inputRef.current) event.stopPropagation();
      }}
    />
  );
}
