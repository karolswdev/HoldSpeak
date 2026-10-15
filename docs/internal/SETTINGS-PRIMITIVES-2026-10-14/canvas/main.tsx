// DRAFT canvas only. These local wrappers prototype opt-in library props.
// The Desk frame, wings, inputs, key capture, table and verbs are production species.
import { useState, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import "/web/src/styles/global.css";
import "/web/src/styles/react-app.css";
import "/web/src/desk/desk.css";
import "/web/src/desk/surface/surface.css";
import { DeskWindowFrame } from "/web/src/desk/components/DeskWindow";
import { useDesk } from "/web/src/desk/store";
import { SurfaceWings } from "/web/src/desk/surface/wings";
import { FootSlotContext } from "/web/src/desk/surface/foot";
import { SurfaceFooter } from "/web/src/desk/surface/SurfaceFooter";
import { Button } from "/web/src/components/signal/Signal";
import { ConfirmVerb } from "/web/src/desk/surface/Surface";
import {
  GadgetGroup,
  GadgetRow,
  GadgetTable,
  CycleGadget,
  CheckGadget,
  StringGadget,
  FoldGadget,
  StepperGadget,
} from "/web/src/desk/surface/gadgets";
import { HotkeyCapture } from "/web/src/pages/cores/settingsBespoke";
import "./main.css";

const windowId = "settings-primitives-canvas";
useDesk.setState({ panelOrder: [windowId], panelMax: [windowId], panelMin: [] });
const noop = () => {};
const wings = [
  { id: "settings", label: "Settings" },
  { id: "engines", label: "Engines" },
  { id: "accounts", label: "Accounts" },
  { id: "guide", label: "Guide" },
];

/** Prototype: GadgetGroup material="inset" and actions={...}.
 * The wrapper is only a canvas adapter for the unchanged production group. */
function InsetGroup({ label, actions, children }: {
  label: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return <div className="prototype-gadget-group" data-material="inset">
    <GadgetGroup label={label}>
      {children}
      {actions ? <div className="prototype-gadget-actions">{actions}</div> : null}
    </GadgetGroup>
  </div>;
}

/** Prototype: CheckGadget variant="state". The real native checkbox
 * owns the full target; the visible word is a noninteractive overlay. */
function StateCheck({ label, checked, onChange }: {
  label: string;
  checked: boolean;
  onChange(next: boolean): void;
}) {
  return <span className="prototype-check-state" data-on={checked || undefined}>
    <CheckGadget label={label} checked={checked} onChange={onChange}/>
    <span className="prototype-check-word" aria-hidden="true">{checked ? "On" : "Off"}</span>
  </span>;
}

/** Prototype: GadgetTable layout="fields". At narrow width the library
 * repeats each head beside its own cell; input accessible names stay native. */
function NamedCell({ label, children }: { label: string; children: ReactNode }) {
  return <span className="prototype-field-cell">
    <span className="prototype-field-label" aria-hidden="true">{label}</span>
    {children}
  </span>;
}

type SymbolEntry = { id: number; spoken: string; symbol: string; attach: string };
const populatedSymbols: SymbolEntry[] = [
  { id: 1, spoken: "right arrow", symbol: "→", attach: "none" },
  { id: 2, spoken: "open bracket", symbol: "(", attach: "right" },
];
const languages = [
  { value: "auto", label: "Detect" },
  { value: "en", label: "English" },
  { value: "pl", label: "Polish" },
  { value: "de", label: "German" },
];
const attachments = [
  { value: "none", label: "None" },
  { value: "left", label: "Left" },
  { value: "right", label: "Right" },
  { value: "both", label: "Both" },
];

function Canvas() {
  const [foot, setFoot] = useState<HTMLDivElement | null>(null);
  const [key, setKey] = useState({ key: "alt_r", display: "⌥R" });
  const [language, setLanguage] = useState("en");
  const [preview, setPreview] = useState(true);
  const [commands, setCommands] = useState(false);
  const [wake, setWake] = useState(false);
  const [wakeAction, setWakeAction] = useState("draft");
  const [refusal, setRefusal] = useState("");
  const [symbols, setSymbols] = useState<SymbolEntry[]>(
    new URLSearchParams(location.search).get("symbols") === "empty" ? [] : populatedSymbols,
  );
  const patchSymbol = (id: number, patch: Partial<SymbolEntry>) => {
    setSymbols((current) => current.map((entry) => entry.id === id ? { ...entry, ...patch } : entry));
  };
  const addSymbol = () => setSymbols((current) => [
    ...current,
    { id: Date.now(), spoken: "", symbol: "", attach: "none" },
  ]);

  return <div className="desk-next primitives-canvas">
    <DeskWindowFrame
      id={windowId}
      title="Settings"
      open
      onClose={noop}
      onBack={noop}
      className="desk-surface-window primitives-window"
      entrance={false}
      wings={<SurfaceWings wings={wings} active="settings" onChange={noop}/>}
    >
      <FootSlotContext.Provider value={foot}>
        <div className="desk-surface-body primitives-body">
          <div className="primitives-voice" data-settings-module="voice">
            <div className="primitives-module-head">
              <img className="primitives-module-sprite" alt="" src="/web/public/desk/sprites/settings/voice.png"/>
              <h2>Voice</h2>
            </div>

            <div className="prototype-gadget-columns">
              <div className="prototype-gadget-column">
                <InsetGroup label="Voice typing">
                  <HotkeyCapture value={key} onCommit={setKey} onRefuse={setRefusal}/>
                  <GadgetRow label="Language">
                    <CycleGadget label="Language" value={language} options={languages} onChange={setLanguage}/>
                  </GadgetRow>
                  <div className="prototype-gadget-rule"/>
                  <GadgetRow label="Preview before type">
                    <StateCheck label="Preview before type" checked={preview} onChange={setPreview}/>
                  </GadgetRow>
                  <GadgetRow label="Voice commands">
                    <StateCheck label="Voice commands" checked={commands} onChange={setCommands}/>
                  </GadgetRow>
                </InsetGroup>

                <InsetGroup label="Wake word">
                  <GadgetRow label="Enabled">
                    <StateCheck label="Wake word enabled" checked={wake} onChange={setWake}/>
                  </GadgetRow>
                  <GadgetRow label="Action">
                    <CycleGadget label="Wake word action" value={wakeAction} options={[
                      { value: "draft", label: "Draft" },
                      { value: "type", label: "Type" },
                    ]} onChange={setWakeAction}/>
                  </GadgetRow>
                </InsetGroup>
              </div>

              <div className="prototype-gadget-column">
                <InsetGroup
                  label="Spoken symbols"
                  actions={<Button dense variant="secondary" onClick={addSymbol}>Add symbol</Button>}
                >
                  {symbols.length ? <div className="prototype-gadget-table" data-layout="fields">
                    <GadgetTable
                      head={["Spoken", "Symbol", "Attach"]}
                      rowKey={(index) => String(symbols[index].id)}
                      verbs={(index) => <ConfirmVerb
                        label="Forget"
                        confirmLabel="Forget?"
                        ariaLabel={`Forget symbol ${symbols[index].spoken || index + 1}`}
                        onConfirm={() => setSymbols((current) => current.filter((entry) => entry.id !== symbols[index].id))}
                      />}
                      rows={symbols.map((entry, index) => [
                        <NamedCell key="spoken" label="Spoken">
                          <StringGadget label={`Spoken phrase ${index + 1}`} value={entry.spoken} placeholder="right arrow" onChange={(spoken) => patchSymbol(entry.id, { spoken })}/>
                        </NamedCell>,
                        <NamedCell key="symbol" label="Symbol">
                          <StringGadget label={`Symbol ${index + 1}`} value={entry.symbol} placeholder="→" onChange={(symbol) => patchSymbol(entry.id, { symbol })}/>
                        </NamedCell>,
                        <NamedCell key="attach" label="Attach">
                          <CycleGadget label={`Attachment ${index + 1}`} value={entry.attach} options={attachments} onChange={(attach) => patchSymbol(entry.id, { attach })}/>
                        </NamedCell>,
                      ])}
                    />
                  </div> : <div className="prototype-gadget-empty">No spoken symbols</div>}
                </InsetGroup>
              </div>
            </div>

            <FoldGadget title="Advanced" className="primitives-advanced">
              <div className="prototype-gadget-columns">
                <InsetGroup label="Transcription">
                  <GadgetRow label="Timeout" fact="seconds">
                    <StepperGadget label="Transcribe timeout" value={30} min={5} step={5} unit="s" onChange={noop}/>
                  </GadgetRow>
                </InsetGroup>
                <InsetGroup label="Pipeline">
                  <GadgetRow label="Latency budget">
                    <StepperGadget label="Latency budget" value={2500} min={0} step={250} unit="ms" onChange={noop}/>
                  </GadgetRow>
                </InsetGroup>
              </div>
            </FoldGadget>
          </div>
        </div>
        <SurfaceFooter receipt={<span>{refusal || "Saved 14:25"}</span>}/>
        <div ref={setFoot} className="surface-footer"/>
      </FootSlotContext.Provider>
    </DeskWindowFrame>
  </div>;
}

createRoot(document.getElementById("root")!).render(<Canvas/>);
