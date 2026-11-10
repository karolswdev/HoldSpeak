// Settings > Speak: voice typing, wake word and spoken symbols. Moved out of SettingsCore.tsx.
import { useEffect, useState } from "react";
import type { SettingsResponse } from "../core-types";
import { Button } from "../../../components/signal/Signal";
import {
  CycleGadget,
  GadgetGroup,
  GadgetRow,
  StringGadget,
  countToken,
  PreferencePane,
  ListPane,
  SegmentedTabs,
  PaneGroup,
  PaneInspector,
  InspectorForm,
  ListView,
  type ListVerb,
} from "../../../desk/surface";
import { LANGUAGE_OPTIONS, WAKE_ACTION_OPTIONS } from "./prefs";
import type { SettingsBindings } from "./bindings";
import type { SettingsWriter } from "./writer";

type SpokenSymbol = { spoken?: string; symbol?: string; attach?: string };

/** An unfinished dictionary row stays on this face, outside the settings
 *  document, until its required fields can pass the producer's validation.
 *  The face holds the draft, so it outlives a remount of the section. */
export function useSpokenSymbolsDraft(data: SettingsResponse, writer: SettingsWriter) {
  const [spokenSymbolsDraft, setSpokenSymbolsDraft] = useState<SpokenSymbol[] | null>(null);
  useEffect(() => {
    if (spokenSymbolsDraft === null) return;
    const writesSymbols = ([path]: [string[], unknown]) => path.length === 2 && path[0] === "dictation" && path[1] === "spoken_symbols";
    if (writer.hasPendingWrite(writesSymbols)) return;
    const confirmed = (writer.authoritativeBaseRef.current.dictation as { spoken_symbols?: SpokenSymbol[] } | undefined)?.spoken_symbols ?? [];
    if (
      confirmed.length === spokenSymbolsDraft.length &&
      confirmed.every(
        (entry, index) =>
          entry.spoken === spokenSymbolsDraft[index].spoken?.trim() &&
          entry.symbol === spokenSymbolsDraft[index].symbol &&
          (entry.attach ?? "none") === (spokenSymbolsDraft[index].attach ?? "none").trim().toLowerCase(),
      )
    )
      setSpokenSymbolsDraft(null);
  }, [data, spokenSymbolsDraft]);
  return { spokenSymbolsDraft, setSpokenSymbolsDraft };
}

export type SpokenSymbolsDraft = ReturnType<typeof useSpokenSymbolsDraft>;

export function SpeakSection({ b, symbolsDraft, onRefuse }: { b: SettingsBindings; symbolsDraft: SpokenSymbolsDraft; onRefuse: (refusal: string) => void }) {
  const { data, update, val, hl, check, str, cyc } = b;
  const { spokenSymbolsDraft, setSpokenSymbolsDraft } = symbolsDraft;
  const symbols = spokenSymbolsDraft ?? ((val(["dictation", "spoken_symbols"]) ?? []) as SpokenSymbol[]);
  const symbolsPath = ["dictation", "spoken_symbols"];
  const writeSymbols = (next: SpokenSymbol[]) => {
    setSpokenSymbolsDraft(next);
    if (next.every((entry) => entry.spoken?.trim() && (entry.symbol?.length ?? 0) > 0)) {
      update(symbolsPath, next);
    }
  };
  const patchSymbol = (index: number, patch: Record<string, string>) => writeSymbols(symbols.map((entry, row) => (row === index ? { ...entry, ...patch } : entry)));
  const macroItems = (val(["dictation", "macros", "items"]) ?? []) as unknown[];
  const [tab, setTab] = useState("typing");
  const [picked, pick] = useState<string | null>(null);
  const [editing, edit] = useState<number | null>(null);
  const entry = editing === null ? null : symbols[editing];
  const verbs: ListVerb[] = [
    {
      id: "add",
      label: "Add symbol",
      symbol: "+",
      run: () => {
        setSpokenSymbolsDraft([...symbols, { spoken: "", symbol: "", attach: "none" }]);
        edit(symbols.length);
      },
    },
    {
      id: "remove",
      label: "Forget",
      symbol: "−",
      key: "Delete",
      enabled: (row) => Boolean(row),
      run: (row) => {
        writeSymbols(symbols.filter((_, i) => String(i) !== row?.id));
        pick(null);
      },
    },
    {
      id: "edit",
      label: "Edit…",
      key: "Enter",
      enabled: (row) => Boolean(row),
      run: (row) => edit(Number(row!.id)),
    },
  ];
  return (
    <PreferencePane label="Speak">
      <SegmentedTabs
        label="Speak"
        value={tab}
        onChange={setTab}
        tabs={[
          { id: "typing", label: "Typing" },
          { id: "wake", label: "Wake word" },
          { id: "symbols", label: "Symbols" },
        ]}
      >
        {tab === "typing" ? (
          <GadgetGroup label="Voice typing">
            <HotkeyCapture
              grouped={false}
              value={(data.hotkey ?? {}) as Record<string, unknown>}
              highlight={hl(["hotkey"])}
              onCommit={(next) =>
                update(["hotkey"], {
                  ...(data.hotkey as Record<string, unknown>),
                  ...next,
                })
              }
              onRefuse={onRefuse}
            />
            {cyc(["model", "language"], "Language", LANGUAGE_OPTIONS)}
            {check(["dictation", "preview_before_type"], "Preview before type")}
            {check(["dictation", "macros", "enabled"], "Voice commands", countToken(macroItems.length, "command", "commands") ?? undefined)}
            {/* Review 7b F1: this tick permits a model call that carries the spoken text. It stays on the face. */}
            {check(["dictation", "pipeline", "target_detect_llm_enabled"], "Model finds the target")}
          </GadgetGroup>
        ) : null}
        {tab === "wake" ? (
          <GadgetGroup label="Wake word">
            {check(["wake_word", "enabled"], "Enabled")}
            {cyc(["wake_word", "action"], "Action", WAKE_ACTION_OPTIONS)}
            {str(["wake_word", "model"], "Model", {
              placeholder: "hey_jarvis",
            })}
          </GadgetGroup>
        ) : null}
        {tab === "symbols" ? (
          <ListPane
            label="Symbol inspector"
            list={
              <PaneGroup label="Spoken symbols">
                <ListView
                  label="Spoken symbols"
                  ordered
                  rows={symbols.map((symbol, i) => ({
                    id: String(i),
                    kind: "symbol",
                    name: symbol.spoken || "New symbol",
                    cells: { symbol: symbol.symbol, attach: symbol.attach },
                  }))}
                  columns={[
                    { key: "name", word: "Spoken", priority: 100 },
                    { key: "symbol", word: "Symbol", priority: 30 },
                    { key: "attach", word: "Attach", priority: 10 },
                  ]}
                  selectedId={picked}
                  onSelect={pick}
                  verbs={verbs}
                  defaultVerb="edit"
                />
              </PaneGroup>
            }
          >
            {entry ? (
              <PaneInspector label="Spoken symbol" onClose={() => edit(null)}>
                <InspectorForm>
                  <GadgetRow label="Spoken">
                    <StringGadget
                      label={`Spoken phrase ${editing! + 1}`}
                      value={entry.spoken ?? ""}
                      onChange={(next) => patchSymbol(editing!, { spoken: next })}
                    />
                  </GadgetRow>
                  <GadgetRow label="Symbol">
                    <StringGadget
                      label={`Symbol ${editing! + 1}`}
                      value={entry.symbol ?? ""}
                      mic={false}
                      onChange={(next) => patchSymbol(editing!, { symbol: next })}
                    />
                  </GadgetRow>
                  <GadgetRow label="Attach">
                    <CycleGadget
                      label={`Attachment ${editing! + 1}`}
                      value={entry.attach ?? "none"}
                      options={[{ value: "none" }, { value: "left" }, { value: "right" }, { value: "both" }]}
                      onChange={(next) => patchSymbol(editing!, { attach: next })}
                    />
                  </GadgetRow>
                </InspectorForm>
              </PaneInspector>
            ) : null}
          </ListPane>
        ) : null}
      </SegmentedTabs>
    </PreferencePane>
  );
}

// HS-101 round 5 / HS-111-01 — bespoke configuration components. A
// complex idea gets a component shaped like the idea, on the gadget kit:
//  - HotkeyCapture: a key is pressed, not typed — mapped to exactly the
//    key names the hub accepts (holdspeak/hotkey.py). Listening is
//    inverted video with a block cursor; a refusal lands in the Prefs
//    status bar (never row prose).
// HS-112-01 — RuntimeDestination died: endpoint/model identity lives in
// the Prefs `models` module (`settings/Models.tsx`), the one dial.

/* ── the hotkey: pressed, not typed ────────────────────────────── */

// The hub's accepted set (holdspeak/hotkey.py _key_name_map) — the
// capture can only ever write a name the listener understands.
const CODE_TO_NAME: Record<string, string> = {
  AltRight: "alt_r",
  AltLeft: "alt_l",
  ControlRight: "ctrl_r",
  ControlLeft: "ctrl_l",
  MetaRight: "cmd_r",
  MetaLeft: "cmd_l",
  ShiftRight: "shift_r",
  ShiftLeft: "shift_l",
  CapsLock: "caps_lock",
};
for (let n = 1; n <= 12; n += 1) CODE_TO_NAME[`F${n}`] = `f${n}`;

const NAME_TO_DISPLAY: Record<string, string> = {
  alt_r: "⌥R",
  alt_l: "⌥L",
  ctrl_r: "⌃R",
  ctrl_l: "⌃L",
  cmd_r: "⌘R",
  cmd_l: "⌘L",
  shift_r: "⇧R",
  shift_l: "⇧L",
  caps_lock: "⇪",
};
for (let n = 1; n <= 12; n += 1) NAME_TO_DISPLAY[`f${n}`] = `F${n}`;

export function HotkeyCapture({
  value,
  onCommit,
  onRefuse,
  grouped = true,
  highlight = false,
}: {
  value: Record<string, unknown>;
  onCommit: (next: { key: string; display: string }) => void;
  /** The refusal (names the accepted set) — lands in the status bar. */
  onRefuse?: (refusal: string) => void;
  /** Compose the existing row into a containing preference sheet. */
  grouped?: boolean;
  /** Highlight the row when a Settings palette entry lands here. */
  highlight?: boolean;
}) {
  const [listening, setListening] = useState(false);
  useEffect(() => {
    if (!listening) return;
    const onKey = (event: KeyboardEvent) => {
      event.preventDefault();
      event.stopPropagation();
      if (event.key === "Escape") {
        setListening(false);
        return;
      }
      const name = CODE_TO_NAME[event.code];
      if (!name) {
        onRefuse?.(`${event.code} can't be a hold key: use a modifier (⌥ ⌃ ⌘ ⇧, left or right), ⇪, or F1–F12`);
        return;
      }
      setListening(false);
      onCommit({ key: name, display: NAME_TO_DISPLAY[name] ?? name });
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [listening, onCommit, onRefuse]);
  const current = String(value.display || value.key || "unset");
  const row = (
    <GadgetRow label="Push-to-talk key" fact="hold · release types" highlight={highlight} controlWidth={grouped ? undefined : "short"}>
      <Button
        variant="chrome"
        className={"gadget-keycap" + (listening ? " is-listening" : "")}
        aria-label={listening ? "Listening for the hold key. Esc cancels." : `Push-to-talk key: ${current}. Press to change.`}
        onClick={() => {
          onRefuse?.("");
          setListening((v) => !v);
        }}
      >
        {listening ? "" : current}
      </Button>
    </GadgetRow>
  );
  return grouped ? <GadgetGroup>{row}</GadgetGroup> : row;
}
