/** HS-151-06 / HS-153-02 — Thread composer: PadGadget + @-refs + / verbs.
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
import { PadGadget } from "../surface/gadgets";
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
import { ApiError, apiFetch, readableError } from "../../lib/api";
import { KIND_GLYPH } from "../tools";
import { ScrollHint, SurfaceRows, SurfaceRow } from "../surface/Surface";
import { Button } from "../../components/signal/Signal";
import { beginThreadTodo, settleThreadTodo, useThreadComposerDraft } from "../threadComposerDrafts";
import { noteName } from "../windowName";
import { ActionNotice, StateChip, StringGadget } from "../surface";
import { useOnDeskChanged } from "../useDeskChangedRefresh";

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
      <Button
        variant="ghost"
        dense
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
      </Button>
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
  { id: "tools", verbId: "thread.tools", label: "Show tools", glyph: String.fromCodePoint(0x2699) },
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
  return cursor > lineStart && text[lineStart] === "/";
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
  if (cursor <= lineStart || text[lineStart] !== "/") return null;

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
    // S2: strip "on " or "off " prefix from the arg query before matching.
    let grQuery = argQuery;
    if (grQuery.startsWith("on ")) grQuery = grQuery.slice(3);
    else if (grQuery.startsWith("off ")) grQuery = grQuery.slice(4);
    argItems = ctx.guardrails
      .filter((g) => g.title.toLowerCase().includes(grQuery))
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
let _promptFetching: Promise<PromptNote[]> | null = null;

export async function loadPromptNotes(refresh = false): Promise<PromptNote[]> {
  if (!refresh && _promptCache) return _promptCache;
  if (_promptFetching) return _promptFetching;
  _promptFetching = (async () => {
    const data = await apiFetch<{ notes?: Array<Record<string, unknown>> }>(
      "/api/notes?tag=prompt",
    );
    const notes = data.notes ?? [];
    _promptCache = notes
      .filter((n) => !n.deleted)
      .map((n) => ({
        id: String(n.id ?? ""),
        // PHILO-17: an untitled note is named by its first words.
        title: noteName(n),
        body: String(n.body_markdown ?? ""),
      }));
    return _promptCache;
  })();
  try { return await _promptFetching; } finally { _promptFetching = null; }
}

export function resetPromptCache(): void {
  _promptCache = null;
}

let _guardrailCache: Array<{ id: string; title: string }> | null = null;
let _guardrailFetching: Promise<Array<{ id: string; title: string }>> | null = null;

export async function loadGuardrailNotes(refresh = false): Promise<Array<{ id: string; title: string }>> {
  if (!refresh && _guardrailCache) return _guardrailCache;
  if (_guardrailFetching) return _guardrailFetching;
  _guardrailFetching = (async () => {
    const data = await apiFetch<{ notes?: Array<Record<string, unknown>> }>(
      "/api/notes?tag=guardrail",
    );
    const notes = data.notes ?? [];
    _guardrailCache = notes
      .filter((n) => !n.deleted)
      .map((n) => ({
        id: String(n.id ?? ""),
        title: noteName(n),
      }));
    return _guardrailCache;
  })();
  try { return await _guardrailFetching; } finally { _guardrailFetching = null; }
}

// ── people loader (lazy, cached) ────────────────────────────────────

interface PersonRow {
  id: string;
  display_name: string;
}

let _peopleCache: AutocompleteItem[] | null = null;
let _peopleFetching: Promise<AutocompleteItem[]> | null = null;

async function loadPeople(refresh = false): Promise<AutocompleteItem[]> {
  if (!refresh && _peopleCache) return _peopleCache;
  if (_peopleFetching) return _peopleFetching;
  _peopleFetching = (async () => {
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
  })();
  try { return await _peopleFetching; } finally { _peopleFetching = null; }
}

/** Test seam; the production cache remains shared by the existing pickers. */
export function resetThreadChoiceCaches(): void {
  _promptCache = null;
  _guardrailCache = null;
  _peopleCache = null;
}

type ChoiceKind = "modes" | "prompts" | "guardrails" | "people";
type ChoiceRead = { status: "loading" | "ready" | "failed"; error?: string; known?: boolean };
const CHOICE_LABELS: Record<ChoiceKind, string> = { modes: "Modes", prompts: "Prompts", guardrails: "Guardrails", people: "People" };

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
  /** The thread id — needed by /compact and /todo verbs (HS-153-05). */
  threadId: string;
  /** Send a turn with text + refs. */
  onSend: (text: string, refs: Array<{ ref_kind: string; ref_id: string }>) => void | boolean | Promise<void | boolean>;
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
  /** HS-153-03: Toggle a guardrail on/off for the thread's mode. */
  onToggleGuardrail?: (guardrailId: string, enable: boolean) => void;
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
  threadId,
  onSend,
  onStop,
  onKeep,
  onFork,
  onNewThread,
  onModeSelect,
  onToggleGuardrail,
  currentMode,
  streaming,
  lastAssistantId,
  restoreFocus,
  disabled,
}: ThreadComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { draft, setDraft, chips, setChips, sending, setSending, todo } = useThreadComposerDraft(threadId);
  const [choiceReads, setChoiceReads] = useState<Partial<Record<ChoiceKind, ChoiceRead>>>({});
  const choiceReadsRef = useRef(choiceReads);
  const live = useRef(true);
  useEffect(() => { live.current = true; return () => { live.current = false; }; }, []);

  // Explicit pickers keep their query separate from the unsent message.
  const [picker, setPicker] = useState<"sources" | "commands" | null>(null);
  const [sourceQuery, setSourceQuery] = useState("");
  const [commandQuery, setCommandQuery] = useState("");
  const [pickerIndex, setPickerIndex] = useState(0);
  const [command, setCommand] = useState<SlashCommand | null>(null);
  const [commandArgument, setCommandArgument] = useState("");

  const pickerRef = useRef<HTMLDivElement>(null);
  const pickerResultsRef = useRef<HTMLDivElement>(null);
  const closePicker = useCallback(() => {
    setPicker(null);
    requestAnimationFrame(() => textareaRef.current?.focus());
  }, []);
  useEffect(() => {
    if (!picker) return;
    const frame = requestAnimationFrame(() => {
      pickerRef.current?.querySelector<HTMLElement>(
        "input",
      )?.focus();
    });
    return () => cancelAnimationFrame(frame);
  }, [picker, command]);

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
        // PHILO-17: an untitled note is named by its first words, not skipped.
        const name = kind === "note" ? noteName(prim) : String(prim.title ?? prim.name ?? prim.id ?? "");
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

  const readChoices = useCallback(async (kind: ChoiceKind, refresh = false) => {
    const prior = choiceReadsRef.current[kind];
    if (prior?.status === "loading" || (!refresh && prior)) return;
    const publish = (read: ChoiceRead) => {
      if (!live.current) return;
      choiceReadsRef.current = { ...choiceReadsRef.current, [kind]: read };
      setChoiceReads(choiceReadsRef.current);
    };
    publish({ status: "loading", known: prior?.known });
    try {
      if (kind === "people") setPeople(await loadPeople(refresh));
      else if (kind === "prompts") setPrompts(await loadPromptNotes(refresh));
      else if (kind === "guardrails") setGuardrails(await loadGuardrailNotes(refresh));
      else {
        const data = await apiFetch<{ recipes?: Array<Record<string, unknown>> }>("/api/recipes?kind=mode");
        const order = ["hs-seed-mode-desk", "hs-seed-mode-chase", "hs-seed-mode-draft", "hs-seed-mode-plan"];
        const rank = (id: string) => order.includes(id) ? order.indexOf(id) : order.length;
        const next = (data.recipes ?? []).filter((row) => row.name && !row.deleted)
          .map((row) => ({ id: String(row.id ?? ""), name: String(row.name ?? "") }))
          .sort((a, b) => rank(a.id) - rank(b.id) || a.name.localeCompare(b.name));
        if (live.current) setModes(next);
      }
      publish({ status: "ready", known: true });
    } catch (error) {
      publish({ status: "failed", error: readableError(error), known: prior?.known });
    }
  }, []);
  const loadPeopleOnce = useCallback(() => { void readChoices("people"); }, [readChoices]);
  const loadModesOnce = useCallback(() => { void readChoices("modes"); }, [readChoices]);
  const loadPromptsOnce = useCallback(() => { void readChoices("prompts"); }, [readChoices]);
  const loadGuardrailsOnce = useCallback(() => { void readChoices("guardrails"); }, [readChoices]);
  useOnDeskChanged(() => {
    for (const kind of Object.keys(choiceReadsRef.current) as ChoiceKind[]) void readChoices(kind, true);
  }, ["mode", "note", "person", "recipe", "relationship", "thought"]);

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

  // ── update autocomplete on draft/cursor change ───────────────────
  const updateAutocomplete = useCallback(
    (text: string, cursor: number) => {
      if (picker) { setAcOpen(false); setSlashOpen(false); return; }
      // Two-stage slash completion (R3: / only at line start)
      const completion = completeSlash(text, cursor, { modes, prompts, guardrails });
      if (completion?.stage === "argument") {
        if (completion.command?.id === "mode") loadModesOnce();
        if (completion.command?.id === "prompt") loadPromptsOnce();
        if (completion.command?.id === "guardrail") loadGuardrailsOnce();
      }
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
    [picker, primitiveItems, acQuery, loadPeopleOnce, modes, prompts, guardrails, loadModesOnce, loadPromptsOnce, loadGuardrailsOnce],
  );

  // ── handlers ─────────────────────────────────────────────────────

  const handleChange = useCallback(
    (text: string) => {
      setDraft(text);
      updateAutocomplete(text, textareaRef.current?.selectionStart ?? text.length);
    },
    [updateAutocomplete],
  );

  const handleSelect = useCallback(() => {
    const ta = textareaRef.current;
    if (ta) updateAutocomplete(draft, ta.selectionStart);
  }, [draft, updateAutocomplete]);

  // A completed choice read updates the open picker without another keystroke.
  useEffect(() => {
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
    setSystemRows((prev) => [...prev.slice(-1), text]);
  }, []);

  const executeSlashCommand = useCallback(
    (cmdId: string, arg?: string, preserveDraft = false) => {
      const clearCommand = () => { if (!preserveDraft) setDraft(""); };
      setSlashOpen(false);
      setSlashCompletion(null);

      switch (cmdId) {
        case "keep":
          clearCommand();
          if (lastAssistantId) onKeep(lastAssistantId, "note");
          break;
        case "fork":
          clearCommand();
          if (lastAssistantId) onFork(lastAssistantId);
          break;
        case "stop":
          clearCommand();
          onStop();
          break;
        case "new":
          clearCommand();
          onNewThread();
          break;
        case "mode":
          clearCommand();
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
              const nextDraft = preserveDraft && draft ? `${draft}\n${prompt.body}` : prompt.body;
              setDraft(nextDraft);
              // Focus and move cursor to end
              requestAnimationFrame(() => {
                const ta = textareaRef.current;
                if (ta) {
                  ta.focus();
                  ta.setSelectionRange(nextDraft.length, nextDraft.length);
                }
              });
            }
          }
          break;
        case "tools":
          clearCommand();
          if (currentMode) {
            addSystemRow(`Current palette: ${currentMode.name} mode tools`);
          } else {
            addSystemRow("Current palette: default (no mode bound)");
          }
          break;
        case "todo":
          if (!arg) {
            addSystemRow("Usage: /todo <text>");
          } else if (beginThreadTodo(threadId, preserveDraft ? `/todo ${arg}` : draft)) {
            const command = preserveDraft ? `/todo ${arg}` : draft;
            void (async () => {
              try {
                const result = await apiFetch<{ status: string; error?: string }>(
                  `/api/threads/${encodeURIComponent(threadId)}/todo`,
                  { method: "POST", json: { text: arg } },
                );
                if (result.status === "ok") settleThreadTodo(threadId, command, "accepted");
                // These two replies return before the tool is dispatched.
                else if (["denied", "timeout"].includes(result.status))
                  settleThreadTodo(threadId, command, "refused", result.error || result.status);
                else settleThreadTodo(threadId, command, "unknown", result.error);
              } catch (error) {
                // A transport/server failure does not establish whether this
                // non-idempotent task writer ran. Never replay it implicitly.
                const refused = error instanceof ApiError && error.status >= 400 && error.status < 500;
                settleThreadTodo(threadId, command, refused ? "refused" : "unknown", readableError(error));
              }
            })();
          }
          break;
        case "compact":
          clearCommand();
          void (async () => {
            try {
              addSystemRow("Compacting thread...");
              const result = await apiFetch<{ status: string; error?: string }>(
                `/api/threads/${threadId}/compact`,
                { method: "POST" },
              );
              if (result.status === "failed") {
                addSystemRow(`Compact failed: ${result.error || "unknown error"}`);
              }
            } catch (err) {
              addSystemRow(`Compact failed: ${err instanceof Error ? err.message : "unknown error"}`);
            }
          })();
          break;
        case "guardrail":
          clearCommand();
          if (!currentMode) {
            addSystemRow("Bind a mode first (use /mode)");
          } else if (arg && onToggleGuardrail) {
            // S2: parse "on|off <name>" prefix
            let enable = true;
            let guardrailName = arg;
            const lower = arg.toLowerCase();
            if (lower.startsWith("on ")) {
              enable = true;
              guardrailName = arg.slice(3).trim();
            } else if (lower.startsWith("off ")) {
              enable = false;
              guardrailName = arg.slice(4).trim();
            }
            const guardrail = guardrails.find(
              (g) => g.title.toLowerCase() === guardrailName.toLowerCase(),
            );
            if (guardrail) {
              onToggleGuardrail(guardrail.id, enable);
              addSystemRow(`Guardrail ${enable ? "enabled" : "disabled"}: ${guardrail.title}`);
            } else {
              addSystemRow(`Unknown guardrail: ${guardrailName}`);
            }
          } else {
            addSystemRow("Usage: /guardrail on|off <name>");
          }
          break;
      }
    },
    [threadId, draft, lastAssistantId, onKeep, onFork, onStop, onNewThread, onModeSelect, onToggleGuardrail, modes, prompts, guardrails, currentMode, addSystemRow],
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
    if (!draft.trim() || sending || todo?.status === "pending") return;
    const text = draft.trim();
    // HS-153-05: intercept freeform-arg slash commands (e.g. /todo, /compact)
    // that never enter the palette's argument stage because they have no completions.
    const slashMatch = /^\/(\w+)(?:\s+(.*))?$/.exec(text);
    if (slashMatch) {
      const cmdName = slashMatch[1].toLowerCase();
      const cmd = THREAD_SLASH_COMMANDS.find((c) => c.id === cmdName);
      if (cmd) {
        executeSlashCommand(cmdName, slashMatch[2]?.trim());
        return;
      }
    }
    setSending(true);
    const refs = chips.map((c) => ({
      ref_kind: c.ref.kind,
      ref_id: c.ref.id,
    }));
    try {
      const accepted = await onSend(text, refs);
      if (accepted !== false) {
        setDraft("");
        setChips([]);
      }
    } catch {
      // Keep the owner's words available after an unconfirmed send.
    } finally {
      setSending(false);
      textareaRef.current?.focus();
    }
  }, [draft, sending, todo, chips, onSend, executeSlashCommand]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.nativeEvent.isComposing || e.keyCode === 229) return;
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

      // Draft editing continues while a reply runs. Stop is explicit.
      if (e.key === "Enter" && !e.shiftKey && !streaming) {
        e.preventDefault();
        void handleSend();
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

  const sourceMatches = filterItems(sourceQuery, primitiveItems);
  const sourceCapped = primitiveItems.filter((item) => item.nameNormalized.startsWith(sourceQuery.toLowerCase())).length > sourceMatches.length;
  const commandMatches = filterSlashCommands(commandQuery).filter((item) => item.id === "stop" ? streaming
    : ["keep", "fork"].includes(item.id) ? Boolean(lastAssistantId) : true);
  const argumentQuery = command?.id === "guardrail" ? commandArgument.replace(/^(?:on|off)\s+/i, "") : commandArgument;
  const argumentChoices = command?.id === "mode" ? modes.map((item) => ({ id: item.id, label: item.name }))
    : command?.id === "prompt" ? prompts.map((item) => ({ id: item.id, label: item.title }))
      : command?.id === "guardrail" ? guardrails.map((item) => ({ id: item.id, label: item.title })) : [];
  const argumentMatches = argumentChoices.filter((item) => item.label.toLowerCase().includes(argumentQuery.toLowerCase()));
  const validArgument = Boolean(commandArgument.trim()) && (command?.id === "todo"
    || argumentChoices.some((item) => item.label.toLowerCase() === argumentQuery.trim().toLowerCase()));
  const pickerCount = picker === "sources" ? sourceMatches.length : command ? argumentMatches.length : commandMatches.length;
  const selectedPickerIndex = Math.min(picker === "sources" ? acIndex : pickerIndex, Math.max(0, pickerCount - 1));

  useEffect(() => {
    if (!picker) return;
    if (picker === "sources") setAcIndex(selectedPickerIndex);
    else setPickerIndex(selectedPickerIndex);
    pickerResultsRef.current?.querySelector<HTMLElement>("[data-selected]")?.scrollIntoView?.({ block: "nearest" });
  }, [picker, command, pickerIndex, acIndex, commandQuery, commandArgument, sourceQuery, pickerCount, selectedPickerIndex]);

  const chooseCommand = (item: SlashCommand) => {
    if (item.hasArg) {
      setCommand(item); setCommandArgument(""); setPickerIndex(0);
      if (item.id === "mode") loadModesOnce();
      if (item.id === "prompt") loadPromptsOnce();
      if (item.id === "guardrail") loadGuardrailsOnce();
    } else { closePicker(); executeSlashCommand(item.id, undefined, true); }
  };
  const chooseArgument = (label: string) => {
    if (!command) return;
    const prefix = command.id === "guardrail" ? commandArgument.match(/^(on|off)\s+/i)?.[1] : undefined;
    closePicker(); executeSlashCommand(command.id, prefix ? `${prefix} ${label}` : label, true);
  };
  const pickerListId = picker === "sources" ? "wb-inlet-listbox" : `thread-${threadId}-picker-results`;
  const activePickerId = !pickerCount ? undefined : picker === "sources"
    ? `wb-inlet-option-${sourceMatches[selectedPickerIndex].kind}-${sourceMatches[selectedPickerIndex].id}`
    : command ? `thread-command-argument-${argumentMatches[selectedPickerIndex].id}` : `thread-command-${commandMatches[selectedPickerIndex].id}`;
  const pickerInputProps = command?.id === "todo" && picker === "commands" ? {} : { role: "combobox", "aria-expanded": true, "aria-autocomplete": "list" as const,
    "aria-controls": pickerListId, "aria-activedescendant": activePickerId };
  const handlePickerKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.nativeEvent.isComposing || event.keyCode === 229) return;
    if (["ArrowDown", "ArrowUp"].includes(event.key)) {
      event.preventDefault();
      const next = Math.max(0, Math.min(selectedPickerIndex + (event.key === "ArrowDown" ? 1 : -1), pickerCount - 1));
      if (picker === "sources") setAcIndex(next); else setPickerIndex(next);
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (picker === "sources") {
        if (sourceMatches[selectedPickerIndex]) { addChip(itemToRef(sourceMatches[selectedPickerIndex])); closePicker(); }
        return;
      }
      if (picker === "commands" && !command && commandMatches[selectedPickerIndex]) {
        chooseCommand(commandMatches[selectedPickerIndex]);
      } else if (command && argumentMatches[selectedPickerIndex]) {
        chooseArgument(argumentMatches[selectedPickerIndex].label);
      } else if (command && validArgument) {
        closePicker(); executeSlashCommand(command.id, commandArgument.trim(), true);
      }
    }
  };

  const handleMicText = useCallback((text: string) => {
    // Append to the latest draft, including edits made during capture.
    setDraft((current) => current ? `${current} ${text}` : text);
  }, []);

  return (
    <div className="thread-composer conversation-composer" data-testid="thread-composer"
      onKeyDownCapture={(event) => {
        if (event.key === "Escape" && picker && !event.nativeEvent.isComposing && event.keyCode !== 229) {
          event.preventDefault();
          event.stopPropagation();
          closePicker();
        }
      }}>
      {picker && <div ref={pickerRef} className="thread-composer-picker" data-testid="composer-picker">
        <div className="thread-picker-head">
          <span>{picker === "sources" ? "Sources" : command?.label || "Commands"}</span>
          <Button variant="ghost" dense aria-label="Close picker" onClick={() => { closePicker(); }}>Close</Button>
        </div>
        {picker === "sources" ? <>
          <StringGadget label="Find source" placeholder="Find source" value={sourceQuery} onChange={(value) => { setSourceQuery(value); setAcIndex(0); }} autoFocus
            inputProps={pickerInputProps} onKeyDown={handlePickerKeyDown} />
          <ScrollHint axis="y" scrollRef={pickerResultsRef} className="thread-picker-hint">
            <div ref={pickerResultsRef} className="thread-picker-results">
              <InletAutocomplete allMatches={sourceMatches} selectedIndex={selectedPickerIndex}
                onSelectedIndexChange={setAcIndex} emptyLabel="No matches"
                onSelectItem={(item) => { addChip(itemToRef(item)); closePicker(); }} />
            </div>
          </ScrollHint>
          {sourceCapped && <span className="thread-picker-feedback">Type to filter</span>}
        </> : !command ? <>
          <StringGadget label="Find command" placeholder="Find command" value={commandQuery} onChange={(value) => { setCommandQuery(value); setPickerIndex(0); }} autoFocus
            inputProps={pickerInputProps} onKeyDown={handlePickerKeyDown} />
          <ScrollHint axis="y" scrollRef={pickerResultsRef} className="thread-picker-hint">
            <div ref={pickerResultsRef} className="thread-picker-results" id={pickerListId} role="listbox" aria-label="Commands">
              <SurfaceRows>
                {commandMatches.map((item, index) => (
                  <SurfaceRow
                    key={item.id} id={`thread-command-${item.id}`}
                    role="option" ariaSelected={index === selectedPickerIndex} selected={index === selectedPickerIndex}
                    title={item.label} meta={`/${item.id}`} onOpen={() => chooseCommand(item)} />
                ))}
              </SurfaceRows>
              {!commandMatches.length && <span className="thread-picker-feedback" role="status">No matches</span>}
            </div>
          </ScrollHint>
        </> : <>
          <StringGadget label={command.label} value={commandArgument} onChange={(value) => { setCommandArgument(value); setPickerIndex(0); }} autoFocus
            inputProps={pickerInputProps} onKeyDown={handlePickerKeyDown} />
          {command.id !== "todo" && <ScrollHint axis="y" scrollRef={pickerResultsRef} className="thread-picker-hint">
            <div ref={pickerResultsRef} className="thread-picker-results" id={pickerListId} role="listbox" aria-label={command.label}>
              <SurfaceRows>
                {argumentMatches.map((item, index) => (
                  <SurfaceRow
                    key={item.id} id={`thread-command-argument-${item.id}`}
                    role="option" ariaSelected={index === selectedPickerIndex} selected={index === selectedPickerIndex}
                    title={item.label} onOpen={() => chooseArgument(item.label)} />
                ))}
              </SurfaceRows>
              {argumentChoices.length > 0 && !argumentMatches.length && <span className="thread-picker-feedback" role="status">No matches</span>}
            </div>
          </ScrollHint>}
          <div className="thread-picker-actions">
            <Button variant="ghost" dense onClick={() => { setCommand(null); setPickerIndex(0); }}>Back</Button>
            <Button variant="primary" dense disabled={!validArgument} onClick={() => {
              closePicker(); executeSlashCommand(command.id, commandArgument.trim(), true);
            }}>{command.label}</Button>
          </div>
        </>}
      </div>}

      {todo ? <ActionNotice role={todo.status === "refused" || todo.status === "unknown" ? "alert" : "status"} tone={todo.status === "accepted" ? "ok" : "warn"}>
        <StateChip state={todo.status === "pending" ? "working" : todo.status === "accepted" ? "success" : "warning"}
          label={todo.status === "pending" ? "Adding task" : todo.status === "accepted" ? "Task added" : todo.status === "refused" ? "Task not added" : "Result unknown"} />
        {" · "}<span>{todo.command}</span>
        {todo.message ? <>{" · "}<span>{todo.message}</span></> : null}
      </ActionNotice> : null}
      {(Object.keys(choiceReads) as ChoiceKind[]).map((kind) => {
        const read = choiceReads[kind]!;
        const count = kind === "modes" ? modes.length : kind === "prompts" ? prompts.length : kind === "guardrails" ? guardrails.length : people.length;
        return read.status === "failed" ? <ActionNotice key={kind} role="alert" tone="warn" action={{ label: `Retry ${CHOICE_LABELS[kind]}`, onClick: () => void readChoices(kind, true) }}>
          <StateChip state="unreachable" label={`${CHOICE_LABELS[kind]} unavailable`} />
          {read.known ? <>{" · "}<StateChip state="warning" label="Last read" /></> : null}
          {" · "}<span>{read.error}</span>
        </ActionNotice> : read.status === "loading" ? <StateChip key={kind} state="working" label={`Reading ${CHOICE_LABELS[kind]}`} />
          : !count ? <StateChip key={kind} state="idle" label={`No ${CHOICE_LABELS[kind].toLowerCase()}`} /> : null;
      })}
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

      <div className="thread-composer-row">
        <PadGadget
          inputRef={textareaRef}
          label="Thread message"
          placeholder="Continue this conversation"
          value={draft}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          rows={2}
          autoGrow
          mic={false}
          disabled={disabled || sending}
          inputProps={{
            className: "thread-composer-input",
            onSelect: handleSelect,
            "data-testid": "composer-input",
          } as React.ComponentPropsWithoutRef<"textarea">}
        />
        <div className="thread-composer-actions">
          <div className="thread-composer-tools">
            <Button variant="ghost" dense aria-expanded={picker === "sources"} onClick={() => {
              if (picker === "sources") closePicker(); else setPicker("sources"); setSourceQuery(""); setAcIndex(0);
              setAcOpen(false); setSlashOpen(false); loadPeopleOnce();
            }}>Sources</Button>
            <Button variant="ghost" dense aria-expanded={picker === "commands"} onClick={() => {
              if (picker === "commands") closePicker(); else setPicker("commands"); setCommand(null); setCommandQuery(""); setPickerIndex(0);
              setAcOpen(false); setSlashOpen(false);
            }}>Commands</Button>
          </div>
          <div className="thread-composer-capture"><MicButton onText={handleMicText} label="Speak" /></div>
        {streaming ? (
          <Button
            variant="secondary"
            type="button"
            onClick={() => onStop()}
            data-testid="composer-stop"
          >
            Stop
          </Button>
        ) : (
          <Button
            variant="primary"
            type="button"
            onClick={() => void handleSend()}
            disabled={disabled || !draft.trim() || sending || todo?.status === "pending"}
            data-testid="composer-send"
          >
            Send
          </Button>
        )}
        </div>
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
      if (e.nativeEvent.isComposing || e.keyCode === 229) return;
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
    <div
      className="thread-inline-editor conversation-composer"
      data-testid="inline-editor"
      onBlur={(event) => {
        if (event.relatedTarget instanceof Node && event.currentTarget.contains(event.relatedTarget)) return;
        onCancel();
      }}
    >
      <PadGadget
        inputRef={inputRef}
        label={placeholder ?? "Edit message"}
        value={text}
        onChange={setText}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={3}
        autoGrow
        mic={false}
        inputProps={{
          className: "thread-inline-editor-input",
          "data-testid": "inline-editor-input",
        } as React.ComponentPropsWithoutRef<"textarea">}
      />
      <div className="thread-inline-editor-actions">
        <div className="thread-composer-capture">
          <MicButton label="Speak message" onText={(spoken) => setText((current) =>
            current && !/\s$/.test(current) ? `${current} ${spoken}` : current + spoken,
          )} />
        </div>
        <Button
          variant="primary"
          type="button"
          onClick={() => text.trim() && onConfirm(text.trim())}
          disabled={!text.trim()}
        >
          Send
        </Button>
        <Button
          variant="ghost"
          type="button"
          onClick={onCancel}
        >
          Cancel
        </Button>
      </div>
    </div>
  );
}
