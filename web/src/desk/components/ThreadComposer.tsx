/** HS-151-06 / HS-153-02 — Thread composer: textarea + MicButton + @-refs + / verbs.
 *
 * HS-153-02: two-stage slash completion (command → argument), R3 rule
 * (/ only at line start), mode/prompt/tools/todo/compact/guardrail verbs,
 * each mapped to a registered verb id.
 *
 * Laws: Art. IV (voice arms, never fires), Art. VII (no modals),
 * mic on every text input, Signal Workbench material. */
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import { MicButton } from "./MicButton";
import {
  InletAutocomplete,
  filterItems,
  itemToRef,
  findAtTrigger,
  extractAtQuery,
  removeAtSpan,
  type AutocompleteItem,
} from "./InletAutocomplete";
import type { ResolvedRef } from "../../lib/drawerResolver";
import { useDesk } from "../store";
import { apiFetch } from "../../lib/api";
import { KIND_GLYPH } from "../tools";
import { SurfaceRows, SurfaceRow } from "../surface/Surface";

// ── ref chip (the attachment) ───────────────────────────────────────

export interface RefChip {
  ref: ResolvedRef;
}

function RefChipRow({
  chip,
  onRemove,
}: {
  chip: RefChip;
  onRemove: () => void;
}) {
  return (
    <span className="thread-ref-chip" data-testid={`ref-chip-${chip.ref.kind}`}>
      <span className="thread-ref-chip-kind">
        {KIND_GLYPH[chip.ref.kind] ?? chip.ref.kind}
      </span>
      <span className="thread-ref-chip-name">{chip.ref.name}</span>
      <button
        type="button"
        className="thread-ref-chip-remove"
        aria-label={`Remove ${chip.ref.name}`}
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          onRemove();
        }}
      >
        x
      </button>
    </span>
  );
}

// ── slash command palette ───────────────────────────────────────────

export interface SlashCommand {
  id: string;
  /** Registered verb id in verbRegistry.ts. */
  verbId: string;
  label: string;
  glyph: string;
  /** Whether this command takes an argument (enters second stage). */
  hasArg?: boolean;
}

/** The thread's / commands. Every entry maps to a registered verb id.
 * Commands with `hasArg` enter the second completion stage. */
export const THREAD_SLASH_COMMANDS: SlashCommand[] = [
  { id: "keep", verbId: "thread.keep", label: "Keep as note", glyph: "▤" },
  { id: "fork", verbId: "thread.fork", label: "Fork from here", glyph: "◬" },
  { id: "stop", verbId: "thread.stop", label: "Stop generation", glyph: "■" },
  { id: "new", verbId: "thread.new", label: "New thread", glyph: "◬" },
  { id: "mode", verbId: "thread.mode", label: "Switch mode", glyph: "◎", hasArg: true },
  { id: "prompt", verbId: "thread.prompt", label: "Insert prompt", glyph: "▤", hasArg: true },
  { id: "tools", verbId: "thread.tools", label: "Show tools", glyph: "⚙" },
  { id: "todo", verbId: "thread.todo", label: "Add todo", glyph: "◻", hasArg: true },
  { id: "compact", verbId: "thread.compact", label: "Compact thread", glyph: "⊟" },
  { id: "guardrail", verbId: "thread.guardrail", label: "Toggle guardrail", glyph: "⊘", hasArg: true },
];

export function filterSlashCommands(query: string): SlashCommand[] {
  const lower = query.toLowerCase();
  return THREAD_SLASH_COMMANDS.filter(
    (c) => c.id.startsWith(lower) || c.label.toLowerCase().includes(lower),
  );
}

// ── two-stage slash completion (pure, unit-testable) ────────────────

export interface SlashCompletionItem {
  id: string;
  label: string;
  detail?: string;
  glyph?: string;
}

export interface SlashCompletion {
  stage: "command" | "argument";
  /** The slash command being completed (only set for argument stage). */
  command?: SlashCommand;
  /** The argument query (only set for argument stage). */
  argQuery?: string;
  items: SlashCompletionItem[];
  /** The range in the input to replace when an item is picked. */
  replaceRange: { start: number; end: number };
}

export interface SlashCompletionContext {
  /** Available mode names (from fetchModes cache). */
  modes: Array<{ id: string; name: string }>;
  /** Available prompt note titles + bodies (from /api/notes?tag=prompt). */
  prompts: Array<{ id: string; title: string; body: string }>;
  /** Available guardrail note titles (from /api/notes?tag=guardrail). */
  guardrails: Array<{ id: string; title: string }>;
}

/** R3: / triggers only at column 0 of a line (start-of-text or after \n). */
export function isSlashAtLineStart(text: string, cursor: number): boolean {
  // Find the slash position: the last / before or at cursor on the current line
  const beforeCursor = text.slice(0, cursor);
  const lastNewline = beforeCursor.lastIndexOf("\n");
  const lineStart = lastNewline + 1;
  // The slash must be at lineStart
  return text[lineStart] === "/";
}

/** Pure function: given the full input text, cursor position, and context,
 * compute what the slash popover should show. Returns null when no slash
 * popover should be open. */
export function completeSlash(
  text: string,
  cursor: number,
  ctx: SlashCompletionContext,
): SlashCompletion | null {
  // Find the current line's start
  const beforeCursor = text.slice(0, cursor);
  const lastNewline = beforeCursor.lastIndexOf("\n");
  const lineStart = lastNewline + 1;

  // R3: / only at line start
  if (text[lineStart] !== "/") return null;

  const lineContent = text.slice(lineStart, cursor);
  // lineContent is "/<something>"

  // Check for a space — indicates possible second stage
  const spaceIdx = lineContent.indexOf(" ");

  if (spaceIdx === -1) {
    // First stage: filtering commands
    const query = lineContent.slice(1); // strip the /
    const matches = THREAD_SLASH_COMMANDS.filter(
      (c) => c.id.startsWith(query.toLowerCase()) || c.label.toLowerCase().includes(query.toLowerCase()),
    );
    return {
      stage: "command",
      items: matches.map((c) => ({
        id: c.id,
        label: `/${c.id}`,
        detail: c.label,
        glyph: c.glyph,
      })),
      replaceRange: { start: lineStart, end: cursor },
    };
  }

  // Second stage: the command name is before the space
  const cmdName = lineContent.slice(1, spaceIdx).toLowerCase();
  const cmd = THREAD_SLASH_COMMANDS.find((c) => c.id === cmdName);
  if (!cmd || !cmd.hasArg) return null;

  const argQuery = lineContent.slice(spaceIdx + 1).toLowerCase();
  let argItems: SlashCompletionItem[] = [];

  if (cmd.id === "mode") {
    argItems = ctx.modes
      .filter((m) => m.name.toLowerCase().includes(argQuery))
      .map((m) => ({ id: m.id, label: m.name }));
  } else if (cmd.id === "prompt") {
    argItems = ctx.prompts
      .filter((p) => p.title.toLowerCase().includes(argQuery))
      .map((p) => ({ id: p.id, label: p.title }));
  } else if (cmd.id === "guardrail") {
    // /guardrail on|off <name> — for now just show guardrail names
    argItems = ctx.guardrails
      .filter((g) => g.title.toLowerCase().includes(argQuery))
      .map((g) => ({ id: g.id, label: g.title }));
  }
  // /todo takes freeform text, no completions needed

  return {
    stage: "argument",
    command: cmd,
    argQuery: lineContent.slice(spaceIdx + 1),
    items: argItems,
    replaceRange: { start: lineStart, end: cursor },
  };
}

// ── notes loader (lazy, cached) ────────────────────────────────────

export interface PromptNote {
  id: string;
  title: string;
  body: string;
}

let _promptCache: PromptNote[] | null = null;
let _promptFetching = false;

export async function loadPromptNotes(): Promise<PromptNote[]> {
  if (_promptCache) return _promptCache;
  if (_promptFetching) return [];
  _promptFetching = true;
  try {
    const data = await apiFetch<{ notes?: Array<Record<string, unknown>> }>(
      "/api/notes?tag=prompt",
    );
    const notes = data.notes ?? [];
    _promptCache = notes
      .filter((n) => n.title && !n.deleted)
      .map((n) => ({
        id: String(n.id ?? ""),
        title: String(n.title ?? ""),
        body: String(n.body_markdown ?? ""),
      }));
    return _promptCache;
  } catch {
    return [];
  } finally {
    _promptFetching = false;
  }
}

export function resetPromptCache(): void {
  _promptCache = null;
}

let _guardrailCache: Array<{ id: string; title: string }> | null = null;
let _guardrailFetching = false;

export async function loadGuardrailNotes(): Promise<Array<{ id: string; title: string }>> {
  if (_guardrailCache) return _guardrailCache;
  if (_guardrailFetching) return [];
  _guardrailFetching = true;
  try {
    const data = await apiFetch<{ notes?: Array<Record<string, unknown>> }>(
      "/api/notes?tag=guardrail",
    );
    const notes = data.notes ?? [];
    _guardrailCache = notes
      .filter((n) => n.title && !n.deleted)
      .map((n) => ({
        id: String(n.id ?? ""),
        title: String(n.title ?? ""),
      }));
    return _guardrailCache;
  } catch {
    return [];
  } finally {
    _guardrailFetching = false;
  }
}

// ── people loader (lazy, cached) ────────────────────────────────────

interface PersonRow {
  id: string;
  display_name: string;
}

let _peopleCache: AutocompleteItem[] | null = null;
let _peopleFetching = false;

async function loadPeople(): Promise<AutocompleteItem[]> {
  if (_peopleCache) return _peopleCache;
  if (_peopleFetching) return [];
  _peopleFetching = true;
  try {
    const data = await apiFetch<{ relationships?: PersonRow[] }>(
      "/api/people/relationships",
    );
    const rels = data.relationships ?? [];
    _peopleCache = rels
      .filter((r) => r.display_name)
      .map((r) => ({
        id: r.id,
        kind: "person",
        name: r.display_name,
        nameNormalized: r.display_name.toLowerCase(),
      }));
    return _peopleCache;
  } catch {
    return [];
  } finally {
    _peopleFetching = false;
  }
}

// ── system-style row (in-flow status messages) ──────────────────────

export interface SystemRowProps {
  text: string;
}

function SystemRow({ text }: SystemRowProps) {
  return (
    <div className="thread-system-row" data-testid="thread-system-row">
      <span className="thread-system-row-text">{text}</span>
    </div>
  );
}

// ── composer ────────────────────────────────────────────────────────

export interface ThreadComposerProps {
  /** Send a turn with text + refs. */
  onSend: (text: string, refs: Array<{ ref_kind: string; ref_id: string }>) => void;
  /** Abort the running turn. */
  onStop: () => void;
  /** Keep the latest assistant message. */
  onKeep: (messageId: string, as: "note" | "artifact") => void;
  /** Fork from the latest assistant message. */
  onFork: (messageId: string) => void;
  /** Create a new thread (runs the desk.new-thread verb). */
  onNewThread: () => void;
  /** Set the thread's mode (calls setMode from threads.ts). */
  onModeSelect?: (recipeId: string) => void;
  /** The current thread's mode, used by /tools to show the palette. */
  currentMode?: { id: string; name: string } | null;
  /** Whether a turn is streaming. */
  streaming: boolean;
  /** The latest assistant message id (for keep/fork targets). */
  lastAssistantId: string | null;
  /** Whether focus should be restored (after turn_done). */
  restoreFocus?: boolean;
  /** Whether the composer is disabled. */
  disabled?: boolean;
}

export function ThreadComposer({
  onSend,
  onStop,
  onKeep,
  onFork,
  onNewThread,
  onModeSelect,
  currentMode,
  streaming,
  lastAssistantId,
  restoreFocus,
  disabled,
}: ThreadComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [draft, setDraft] = useState("");
  const [chips, setChips] = useState<RefChip[]>([]);
  const [sending, setSending] = useState(false);

  // autocomplete state
  const [acOpen, setAcOpen] = useState(false);
  const [acQuery, setAcQuery] = useState("");
  const [acMatches, setAcMatches] = useState<AutocompleteItem[]>([]);
  const [acIndex, setAcIndex] = useState(0);
  const [acAtPos, setAcAtPos] = useState(-1);

  // slash command state (two-stage)
  const [slashOpen, setSlashOpen] = useState(false);
  const [slashCompletion, setSlashCompletion] = useState<SlashCompletion | null>(null);
  const [slashIndex, setSlashIndex] = useState(0);

  // system message rows (in-flow feedback from slash commands)
  const [systemRows, setSystemRows] = useState<string[]>([]);

  // cached context for slash argument completion
  const [modes, setModes] = useState<Array<{ id: string; name: string }>>([]);
  const [prompts, setPrompts] = useState<PromptNote[]>([]);
  const [guardrails, setGuardrails] = useState<Array<{ id: string; title: string }>>([]);

  // people items (loaded lazily)
  const [people, setPeople] = useState<AutocompleteItem[]>([]);

  // source primitives from the desk store
  const items = useDesk((s) => s.items);

  const primitiveItems = useMemo((): AutocompleteItem[] => {
    const out: AutocompleteItem[] = [];
    const kinds: Array<{ key: "meeting" | "note" | "artifact" | "decision"; kind: string }> = [
      { key: "meeting", kind: "meeting" },
      { key: "note", kind: "note" },
      { key: "artifact", kind: "artifact" },
      { key: "decision", kind: "decision" },
    ];
    for (const { key, kind } of kinds) {
      for (const it of items[key] ?? []) {
        const prim = it as unknown as Record<string, unknown>;
        const name = String(prim.title ?? prim.name ?? prim.id ?? "");
        if (!name) continue;
        out.push({
          id: String(prim.id ?? ""),
          kind,
          name,
          nameNormalized: name.toLowerCase(),
        });
      }
    }
    return [...out, ...people];
  }, [items, people]);

  // Load people lazily on first @ trigger
  const loadPeopleOnce = useCallback(() => {
    if (people.length > 0 || _peopleCache) {
      if (_peopleCache && people.length === 0) setPeople(_peopleCache);
      return;
    }
    void loadPeople().then((p) => setPeople(p));
  }, [people]);

  // Load modes for /mode completion (reuse ModeTabs fetchModes cache)
  const loadModesOnce = useCallback(() => {
    if (modes.length > 0) return;
    // Dynamically import to reuse the ModeTabs cache
    import("./ModeTabs").then(({ default: _, ...mod }) => {
      // fetchModes is not exported, use the same API endpoint
      void apiFetch<{ recipes?: Array<Record<string, unknown>> }>(
        "/api/recipes?kind=mode",
      ).then((data) => {
        const recipes = data.recipes ?? [];
        const SEED_ORDER = [
          "hs-seed-mode-desk",
          "hs-seed-mode-chase",
          "hs-seed-mode-draft",
          "hs-seed-mode-plan",
        ];
        const rank = (id: string): number => {
          const i = SEED_ORDER.indexOf(id);
          return i === -1 ? SEED_ORDER.length : i;
        };
        const items = recipes
          .filter((r) => r.name && !r.deleted)
          .map((r) => ({
            id: String(r.id ?? ""),
            name: String(r.name ?? ""),
          }));
        items.sort((a, b) => rank(a.id) - rank(b.id) || a.name.localeCompare(b.name));
        setModes(items);
      });
    }).catch(() => {});
  }, [modes.length]);

  // Load prompts for /prompt completion
  const loadPromptsOnce = useCallback(() => {
    if (prompts.length > 0) return;
    void loadPromptNotes().then((p) => setPrompts(p));
  }, [prompts.length]);

  // Load guardrails for /guardrail completion
  const loadGuardrailsOnce = useCallback(() => {
    if (guardrails.length > 0) return;
    void loadGuardrailNotes().then((g) => setGuardrails(g));
  }, [guardrails.length]);

  // ── focus return after turn_done (double-rAF precedent) ──────────
  useEffect(() => {
    if (!restoreFocus) return;
    const id = requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        textareaRef.current?.focus();
      });
    });
    return () => cancelAnimationFrame(id);
  }, [restoreFocus]);

  // ── auto-resize textarea ─────────────────────────────────────────
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 120)}px`;
  }, [draft]);

  // ── update autocomplete on draft/cursor change ───────────────────
  const updateAutocomplete = useCallback(
    (text: string, cursor: number) => {
      // Two-stage slash completion (R3: / only at line start)
      const completion = completeSlash(text, cursor, { modes, prompts, guardrails });
      if (completion && completion.items.length > 0) {
        setSlashOpen(true);
        setSlashCompletion(completion);
        setSlashIndex(0);
        setAcOpen(false);

        // Lazy-load argument data when entering second stage
        if (completion.stage === "command") {
          // Pre-load for when the user picks a command with args
          loadModesOnce();
          loadPromptsOnce();
          loadGuardrailsOnce();
        }
        return;
      }
      setSlashOpen(false);
      setSlashCompletion(null);

      // Check for @ trigger
      const atPos = findAtTrigger(text, cursor);
      if (atPos >= 0) {
        loadPeopleOnce();
        const q = extractAtQuery(text, atPos, cursor);
        const matches = filterItems(q, primitiveItems);
        setAcOpen(true);
        setAcQuery(q);
        setAcMatches(matches);
        setAcAtPos(atPos);
        if (q !== acQuery) setAcIndex(0);
      } else {
        setAcOpen(false);
      }
    },
    [primitiveItems, acQuery, loadPeopleOnce, modes, prompts, guardrails, loadModesOnce, loadPromptsOnce, loadGuardrailsOnce],
  );

  // ── handlers ─────────────────────────────────────────────────────

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const text = e.target.value;
      setDraft(text);
      updateAutocomplete(text, e.target.selectionStart ?? text.length);
    },
    [updateAutocomplete],
  );

  const handleSelect = useCallback(() => {
    const ta = textareaRef.current;
    if (ta) updateAutocomplete(draft, ta.selectionStart);
  }, [draft, updateAutocomplete]);

  const addChip = useCallback(
    (ref: ResolvedRef) => {
      // Dedup by ref string
      if (chips.some((c) => c.ref.ref === ref.ref)) return;
      setChips((prev) => [...prev, { ref }]);
    },
    [chips],
  );

  const removeChip = useCallback((idx: number) => {
    setChips((prev) => prev.filter((_, i) => i !== idx));
  }, []);

  const selectAutocompleteItem = useCallback(
    (item: AutocompleteItem) => {
      addChip(itemToRef(item));
      // Remove the @query span
      if (acAtPos >= 0) {
        const ta = textareaRef.current;
        const cursor = ta?.selectionStart ?? draft.length;
        const result = removeAtSpan(draft, acAtPos, cursor);
        setDraft(result.text);
        setAcOpen(false);
        // Restore focus and cursor
        requestAnimationFrame(() => {
          if (ta) {
            ta.focus();
            ta.setSelectionRange(result.cursor, result.cursor);
          }
        });
      } else {
        setAcOpen(false);
      }
    },
    [acAtPos, addChip, draft],
  );

  const addSystemRow = useCallback((text: string) => {
    setSystemRows((prev) => [...prev, text]);
  }, []);

  const executeSlashCommand = useCallback(
    (cmdId: string, arg?: string) => {
      setSlashOpen(false);
      setSlashCompletion(null);

      switch (cmdId) {
        case "keep":
          setDraft("");
          if (lastAssistantId) onKeep(lastAssistantId, "note");
          break;
        case "fork":
          setDraft("");
          if (lastAssistantId) onFork(lastAssistantId);
          break;
        case "stop":
          setDraft("");
          onStop();
          break;
        case "new":
          setDraft("");
          onNewThread();
          break;
        case "mode":
          setDraft("");
          if (arg && onModeSelect) {
            // Find the mode by name
            const mode = modes.find((m) => m.name.toLowerCase() === arg.toLowerCase());
            if (mode) {
              onModeSelect(mode.id);
            }
          }
          break;
        case "prompt":
          if (arg) {
            const prompt = prompts.find((p) => p.title.toLowerCase() === arg.toLowerCase());
            if (prompt) {
              // Insert the prompt body at the caret (replace the slash command line)
              setDraft(prompt.body);
              // Focus and move cursor to end
              requestAnimationFrame(() => {
                const ta = textareaRef.current;
                if (ta) {
                  ta.focus();
                  ta.setSelectionRange(prompt.body.length, prompt.body.length);
                }
              });
            }
          }
          break;
        case "tools":
          setDraft("");
          if (currentMode) {
            addSystemRow(`Current palette: ${currentMode.name} mode tools`);
          } else {
            addSystemRow("Current palette: default (no mode bound)");
          }
          break;
        case "todo":
          // TODO(HS-153-05): wire to backend; for now show "not yet" in-flow
          setDraft("");
          addSystemRow("Todo: not yet available (coming in HS-153-05)");
          break;
        case "compact":
          // TODO(HS-153-05): wire to backend; for now show "not yet" in-flow
          setDraft("");
          addSystemRow("Compact: not yet available (coming in HS-153-05)");
          break;
        case "guardrail":
          // TODO(HS-153-03): wire to backend; for now show "not yet" in-flow
          setDraft("");
          addSystemRow("Guardrail: not yet available (coming in HS-153-03)");
          break;
      }
    },
    [lastAssistantId, onKeep, onFork, onStop, onNewThread, onModeSelect, modes, prompts, currentMode, addSystemRow],
  );

  const pickSlashItem = useCallback(
    (item: SlashCompletionItem) => {
      if (!slashCompletion) return;

      if (slashCompletion.stage === "command") {
        const cmd = THREAD_SLASH_COMMANDS.find((c) => c.id === item.id);
        if (!cmd) return;

        if (cmd.hasArg) {
          // Transition to second stage: replace the current text with "/cmd "
          const beforeSlash = draft.slice(0, slashCompletion.replaceRange.start);
          const afterCursor = draft.slice(slashCompletion.replaceRange.end);
          const newText = `${beforeSlash}/${cmd.id} ${afterCursor}`;
          const newCursor = beforeSlash.length + cmd.id.length + 2; // after "/cmd "
          setDraft(newText);

          // Lazy-load data for argument stage
          if (cmd.id === "mode") loadModesOnce();
          if (cmd.id === "prompt") loadPromptsOnce();
          if (cmd.id === "guardrail") loadGuardrailsOnce();

          // Update slash completion for the new text
          requestAnimationFrame(() => {
            const ta = textareaRef.current;
            if (ta) {
              ta.focus();
              ta.setSelectionRange(newCursor, newCursor);
            }
            // Re-run completion
            const nextCompletion = completeSlash(newText, newCursor, { modes, prompts, guardrails });
            if (nextCompletion) {
              setSlashCompletion(nextCompletion);
              setSlashIndex(0);
            }
          });
        } else {
          // No argument: execute immediately
          executeSlashCommand(cmd.id);
        }
      } else if (slashCompletion.stage === "argument" && slashCompletion.command) {
        // Argument picked: execute the command with the chosen arg
        executeSlashCommand(slashCompletion.command.id, item.label);
      }
    },
    [slashCompletion, draft, executeSlashCommand, modes, prompts, guardrails, loadModesOnce, loadPromptsOnce, loadGuardrailsOnce],
  );

  const handleSend = useCallback(async () => {
    if (!draft.trim() || sending) return;
    setSending(true);
    const text = draft.trim();
    const refs = chips.map((c) => ({
      ref_kind: c.ref.kind,
      ref_id: c.ref.id,
    }));
    setDraft("");
    setChips([]);
    onSend(text, refs);
    setSending(false);
  }, [draft, sending, chips, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      // Slash command palette navigation
      if (slashOpen && slashCompletion && slashCompletion.items.length > 0) {
        if (e.key === "ArrowDown") {
          e.preventDefault();
          setSlashIndex((i) => Math.min(i + 1, slashCompletion.items.length - 1));
          return;
        }
        if (e.key === "ArrowUp") {
          e.preventDefault();
          setSlashIndex((i) => Math.max(i - 1, 0));
          return;
        }
        if (e.key === "Enter") {
          e.preventDefault();
          pickSlashItem(slashCompletion.items[slashIndex]);
          return;
        }
        if (e.key === "Tab" && !e.shiftKey) {
          e.preventDefault();
          pickSlashItem(slashCompletion.items[slashIndex]);
          return;
        }
        if (e.key === "Escape") {
          e.preventDefault();
          setSlashOpen(false);
          setSlashCompletion(null);
          return;
        }
      }

      // Autocomplete navigation
      if (acOpen && acMatches.length > 0) {
        if (e.key === "ArrowDown") {
          e.preventDefault();
          setAcIndex((i) => Math.min(i + 1, acMatches.length - 1));
          return;
        }
        if (e.key === "ArrowUp") {
          e.preventDefault();
          setAcIndex((i) => Math.max(i - 1, 0));
          return;
        }
        if (e.key === "Enter") {
          e.preventDefault();
          selectAutocompleteItem(acMatches[acIndex]);
          return;
        }
        if (e.key === "Tab" && !e.shiftKey) {
          e.preventDefault();
          selectAutocompleteItem(acMatches[acIndex]);
          return;
        }
        if (e.key === "Escape") {
          e.preventDefault();
          setAcOpen(false);
          return;
        }
      }

      // Esc during streaming → stop
      if (e.key === "Escape" && streaming) {
        e.preventDefault();
        onStop();
        return;
      }

      // Enter → send (Shift+Enter → newline)
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (streaming) {
          onStop();
        } else {
          void handleSend();
        }
        return;
      }
    },
    [
      slashOpen,
      slashCompletion,
      slashIndex,
      acOpen,
      acMatches,
      acIndex,
      streaming,
      onStop,
      handleSend,
      selectAutocompleteItem,
      pickSlashItem,
    ],
  );

  const handleMicText = useCallback(
    (text: string) => {
      // Voice transcript lands in the field, never sends (Art. IV)
      setDraft((prev) => (prev ? prev + " " + text : text));
    },
    [],
  );

  return (
    <div className="thread-composer" data-testid="thread-composer">
      {/* System rows (in-flow feedback from slash commands) */}
      {systemRows.map((text, i) => (
        <SystemRow key={i} text={text} />
      ))}

      {/* Ref chips above the field */}
      {chips.length > 0 && (
        <div className="thread-composer-chips" data-testid="composer-chips">
          {chips.map((chip, i) => (
            <RefChipRow
              key={chip.ref.ref}
              chip={chip}
              onRemove={() => removeChip(i)}
            />
          ))}
        </div>
      )}

      {/* Autocomplete popover (above the field) */}
      <div className="thread-composer-ac-anchor">
        {acOpen && (
          <InletAutocomplete
            allMatches={acMatches}
            selectedIndex={acIndex}
            onSelectItem={selectAutocompleteItem}
            onSelectedIndexChange={setAcIndex}
            emptyLabel="No matches"
          />
        )}
        {slashOpen && slashCompletion && slashCompletion.items.length > 0 && (
          <div
            className="inlet-autocomplete thread-slash-palette"
            role="listbox"
            data-testid="slash-palette"
          >
            <SurfaceRows>
              {slashCompletion.items.map((item, i) => (
                <SurfaceRow
                  key={item.id}
                  id={`thread-slash-${item.id}`}
                  role="option"
                  ariaSelected={i === slashIndex}
                  glyph={item.glyph ? <span className="inlet-ac-kind-glyph">{item.glyph}</span> : undefined}
                  title={item.label}
                  detail={item.detail}
                  selected={i === slashIndex}
                  onOpen={() => pickSlashItem(item)}
                />
              ))}
            </SurfaceRows>
          </div>
        )}
      </div>

      {/* Input row: textarea + mic + send/stop */}
      <div className="thread-composer-row">
        <textarea
          ref={textareaRef}
          className="thread-composer-input"
          placeholder="Type a message..."
          value={draft}
          onChange={handleChange}
          onSelect={handleSelect}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={disabled || sending}
          data-testid="composer-input"
          aria-label="Thread message"
        />
        <MicButton
          onText={handleMicText}
          label="Speak"
        />
        {streaming ? (
          <button
            type="button"
            className="desk-chip"
            onClick={() => onStop()}
            data-testid="composer-stop"
          >
            Stop
          </button>
        ) : (
          <button
            type="button"
            className="desk-chip"
            onClick={() => void handleSend()}
            disabled={!draft.trim() || sending}
            data-testid="composer-send"
          >
            Send
          </button>
        )}
      </div>
    </div>
  );
}

// ── inline editor (edit-and-resend / fork-in-place) ─────────────────

export interface InlineEditorProps {
  /** Initial text to edit. */
  initialText: string;
  /** Called with the edited text when the user confirms (Enter). */
  onConfirm: (text: string) => void;
  /** Called when the user cancels (Escape). */
  onCancel: () => void;
  /** Placeholder text. */
  placeholder?: string;
}

/** An inline text editor that replaces a row in place (no modal). */
export function InlineEditor({
  initialText,
  onConfirm,
  onCancel,
  placeholder,
}: InlineEditorProps) {
  const [text, setText] = useState(initialText);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    // Double-rAF focus (real Chromium truth)
    const id = requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        inputRef.current?.focus();
        inputRef.current?.select();
      });
    });
    return () => cancelAnimationFrame(id);
  }, []);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (text.trim()) onConfirm(text.trim());
      }
      if (e.key === "Escape") {
        e.preventDefault();
        onCancel();
      }
    },
    [text, onConfirm, onCancel],
  );

  return (
    <div className="thread-inline-editor" data-testid="inline-editor">
      <textarea
        ref={inputRef}
        className="thread-inline-editor-input"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={onCancel}
        placeholder={placeholder}
        rows={1}
        data-testid="inline-editor-input"
      />
      <div className="thread-inline-editor-actions">
        <button
          type="button"
          className="desk-chip"
          onClick={() => text.trim() && onConfirm(text.trim())}
          disabled={!text.trim()}
        >
          Send
        </button>
        <button
          type="button"
          className="desk-chip quiet"
          onClick={onCancel}
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
