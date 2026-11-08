// Settings > Speak: voice typing, wake word and spoken symbols. Moved out of SettingsCore.tsx.
import { useEffect, useState } from "react";
import type { SettingsResponse } from "../core-types";
import { Button } from "../../../components/signal/Signal";
import {
  CycleGadget,
  FoldGadget,
  GadgetGroup,
  GadgetTable,
  StringGadget,
} from "../../../desk/surface/gadgets";
import {
  countToken,
  ConfirmVerb,
  GadgetDivider,
  SurfaceColumns,
} from "../../../desk/surface";
import { HotkeyCapture } from "../settingsBespoke";
import { LANGUAGE_OPTIONS, WAKE_ACTION_OPTIONS } from "../settingsPrefs";
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
    const writesSymbols = ([path]: [string[], unknown]) =>
      path.length === 2 && path[0] === "dictation" && path[1] === "spoken_symbols";
    if (writer.hasPendingWrite(writesSymbols)) return;
    const confirmed = (writer.authoritativeBaseRef.current.dictation as { spoken_symbols?: SpokenSymbol[] } | undefined)?.spoken_symbols ?? [];
    if (
      confirmed.length === spokenSymbolsDraft.length &&
      confirmed.every((entry, index) =>
        entry.spoken === spokenSymbolsDraft[index].spoken?.trim() &&
        entry.symbol === spokenSymbolsDraft[index].symbol &&
        (entry.attach ?? "none") === (spokenSymbolsDraft[index].attach ?? "none").trim().toLowerCase(),
      )
    ) setSpokenSymbolsDraft(null);
  }, [data, spokenSymbolsDraft]);
  return { spokenSymbolsDraft, setSpokenSymbolsDraft };
}

export type SpokenSymbolsDraft = ReturnType<typeof useSpokenSymbolsDraft>;

export function SpeakSection({ b, symbolsDraft, onRefuse }: {
  b: SettingsBindings;
  symbolsDraft: SpokenSymbolsDraft;
  onRefuse: (refusal: string) => void;
}) {
  const { data, update, val, hl, check, str, num, cyc, prop, csv } = b;
  const { spokenSymbolsDraft, setSpokenSymbolsDraft } = symbolsDraft;
        const symbols = spokenSymbolsDraft ?? (val(["dictation", "spoken_symbols"]) ?? []) as SpokenSymbol[];
        const symbolsPath = ["dictation", "spoken_symbols"];
        const writeSymbols = (next: SpokenSymbol[]) => {
          setSpokenSymbolsDraft(next);
          if (next.every((entry) => entry.spoken?.trim() && (entry.symbol?.length ?? 0) > 0)) {
            update(symbolsPath, next);
          }
        };
        const patchSymbol = (index: number, patch: Record<string, string>) =>
          writeSymbols(
            symbols.map((entry, row) =>
              row === index ? { ...entry, ...patch } : entry,
            ),
          );
        const macroItems = (val(["dictation", "macros", "items"]) ??
          []) as unknown[];
        return (
          <>
            <SurfaceColumns
              variant="preferences"
              main={<>
                <GadgetGroup label="Voice typing" material="inset">
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
                  <GadgetDivider />
                  {check(["dictation", "preview_before_type"], "Preview before type")}
                  {check(
                    ["dictation", "macros", "enabled"],
                    "Voice commands",
                    countToken(macroItems.length, "command", "commands") ?? undefined,
                  )}
                </GadgetGroup>
                <GadgetGroup label="Wake word" material="inset">
                  {check(["wake_word", "enabled"], "Enabled")}
                  {cyc(
                    ["wake_word", "action"],
                    "Action",
                    WAKE_ACTION_OPTIONS,
                  )}
                </GadgetGroup>
              </>}
              side={
                <GadgetGroup
                  label="Spoken symbols"
                  material="inset"
                  actions={<>
                    <Button dense variant="secondary" onClick={() => setSpokenSymbolsDraft([...symbols, { spoken: "", symbol: "", attach: "none" }])}>Add symbol</Button>
                    {spokenSymbolsDraft !== null ? <span className="gadget-fact" role="status">Draft</span> : null}
                  </>}
                >
                  {symbols.length ? (
                    <GadgetTable
                      layout="fields"
                      head={["Spoken", "Symbol", "Attach"]}
                      verbs={(index) => <ConfirmVerb
                        label="Forget"
                        confirmLabel="Forget?"
                        ariaLabel={`Forget symbol ${index + 1}`}
                        onConfirm={() => writeSymbols(symbols.filter((_, row) => row !== index))}
                      />}
                      rows={symbols.map((entry, index) => [
                        <StringGadget
                          key="spoken"
                          label={`Spoken phrase ${index + 1}`}
                          value={entry.spoken ?? ""}
                          placeholder="arrow"
                          onChange={(next) => patchSymbol(index, { spoken: next })}
                        />,
                        <StringGadget
                          key="symbol"
                          label={`Symbol ${index + 1}`}
                          value={entry.symbol ?? ""}
                          placeholder="→"
                          mic={false}
                          onChange={(next) => patchSymbol(index, { symbol: next })}
                        />,
                        <CycleGadget
                          key="attach"
                          label={`Attachment ${index + 1}`}
                          value={entry.attach ?? "none"}
                          options={[
                            { value: "none" },
                            { value: "left" },
                            { value: "right" },
                            { value: "both" },
                          ]}
                          onChange={(next) => patchSymbol(index, { attach: next })}
                        />,
                      ])}
                    />
                  ) : <span className="gadget-fact">No spoken symbols</span>}
                </GadgetGroup>
              }
            />
            {/* HS-139-04/05: all voice RAW wells merged. */}
            <FoldGadget title="More">
              <GadgetGroup material="inset" label="Transcription">
                {num(
                  ["model", "transcribe_timeout_seconds"],
                  "Transcribe timeout",
                  {
                    unit: "s",
                    min: 5,
                    step: 5,
                  },
                )}
              </GadgetGroup>
              <GadgetGroup material="inset" label="Pipeline">
                {csv(["dictation", "pipeline", "stages"], "Stages")}
                {num(
                  ["dictation", "pipeline", "max_total_latency_ms"],
                  "Latency budget",
                  { unit: "ms", min: 0, step: 250 },
                )}
                {num(
                  ["dictation", "pipeline", "rewrite_passes"],
                  "Rewrite passes",
                  {
                    min: 0,
                    max: 5,
                  },
                )}
                {check(
                  ["dictation", "pipeline", "target_detect_llm_enabled"],
                  "LLM target detect",
                )}
                {prop(
                  ["dictation", "pipeline", "target_detect_llm_below"],
                  "Detect below",
                  { min: 0, max: 1, step: 0.05 },
                )}
              </GadgetGroup>
              <GadgetGroup material="inset" label="Wake word">
                {str(["wake_word", "model"], "Model", {
                  placeholder: "hey_jarvis",
                })}
                {prop(["wake_word", "threshold"], "Threshold", {
                  min: 0,
                  max: 1,
                  step: 0.05,
                })}
                {num(["wake_word", "armed_window_seconds"], "Armed window", {
                  unit: "s",
                  min: 1,
                  step: 1,
                })}
              </GadgetGroup>
            </FoldGadget>
          </>
        );
}
