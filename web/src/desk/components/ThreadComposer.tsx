/** HS-150-06 — Thread composer: textarea + MicButton + @-refs + / verbs.
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
  label: string;
  glyph: string;
}

/** The thread's / commands. These run the same handlers already wired
 * in ThreadPullout; the composer just provides the trigger. */
export const THREAD_SLASH_COMMANDS: SlashCommand[] = [
  { id: "keep", label: "Keep as note", glyph: "▤" },
  { id: "fork", label: "Fork from here", glyph: "◬" },
  { id: "stop", label: "Stop generation", glyph: "■" },
  { id: "new", label: "New thread", glyph: "◬" },
];

export function filterSlashCommands(query: string): SlashCommand[] {
  const lower = query.toLowerCase();
  return THREAD_SLASH_COMMANDS.filter(
    (c) => c.id.startsWith(lower) || c.label.toLowerCase().includes(lower),
  );
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

  // slash command state
  const [slashOpen, setSlashOpen] = useState(false);
  const [slashQuery, setSlashQuery] = useState("");
  const [slashMatches, setSlashMatches] = useState<SlashCommand[]>([]);
  const [slashIndex, setSlashIndex] = useState(0);

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
      // Check for slash command at start of field
      if (text.startsWith("/")) {
        const q = text.slice(1, cursor);
        const matches = filterSlashCommands(q);
        setSlashOpen(true);
        setSlashQuery(q);
        setSlashMatches(matches);
        setSlashIndex(0);
        setAcOpen(false);
        return;
      }
      setSlashOpen(false);

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
    [primitiveItems, acQuery, loadPeopleOnce],
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

  const runSlashCommand = useCallback(
    (cmd: SlashCommand) => {
      setDraft("");
      setSlashOpen(false);
      switch (cmd.id) {
        case "keep":
          if (lastAssistantId) onKeep(lastAssistantId, "note");
          break;
        case "fork":
          if (lastAssistantId) onFork(lastAssistantId);
          break;
        case "stop":
          onStop();
          break;
        case "new":
          onNewThread();
          break;
      }
    },
    [lastAssistantId, onKeep, onFork, onStop, onNewThread],
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
      if (slashOpen && slashMatches.length > 0) {
        if (e.key === "ArrowDown") {
          e.preventDefault();
          setSlashIndex((i) => Math.min(i + 1, slashMatches.length - 1));
          return;
        }
        if (e.key === "ArrowUp") {
          e.preventDefault();
          setSlashIndex((i) => Math.max(i - 1, 0));
          return;
        }
        if (e.key === "Enter") {
          e.preventDefault();
          runSlashCommand(slashMatches[slashIndex]);
          return;
        }
        if (e.key === "Tab" && !e.shiftKey) {
          e.preventDefault();
          runSlashCommand(slashMatches[slashIndex]);
          return;
        }
        if (e.key === "Escape") {
          e.preventDefault();
          setSlashOpen(false);
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
      slashMatches,
      slashIndex,
      acOpen,
      acMatches,
      acIndex,
      streaming,
      onStop,
      handleSend,
      selectAutocompleteItem,
      runSlashCommand,
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
        {slashOpen && slashMatches.length > 0 && (
          <div
            className="inlet-autocomplete thread-slash-palette"
            role="listbox"
            data-testid="slash-palette"
          >
            <SurfaceRows>
              {slashMatches.map((cmd, i) => (
                <SurfaceRow
                  key={cmd.id}
                  id={`thread-slash-${cmd.id}`}
                  role="option"
                  ariaSelected={i === slashIndex}
                  glyph={<span className="inlet-ac-kind-glyph">{cmd.glyph}</span>}
                  title={`/${cmd.id}`}
                  detail={cmd.label}
                  selected={i === slashIndex}
                  onOpen={() => runSlashCommand(cmd)}
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
