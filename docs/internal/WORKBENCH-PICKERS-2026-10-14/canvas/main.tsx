// Direction only. Real library controls with sample choice data.
import { createRoot } from "react-dom/client";
import { useState } from "react";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import { Button } from "@w/components/signal/Signal";
import { CycleGadget, type CycleOption } from "@w/desk/surface/gadgets";
import { DeskWindowFrame } from "@w/desk/components/DeskWindow";
import { RuntimeBusProvider } from "@w/runtime/RuntimeBus";
import "./canvas.css";

window.fetch = async () => new Response("{}", {status:200,headers:{"content-type":"application/json"}});

function Proposal({ label, initial, choices, active, disabled = false }: {
  label: string; initial: string; choices: CycleOption[]; active?: string; disabled?: boolean;
}) {
  const [value, setValue] = useState(initial);
  const known = choices.some((choice) => choice.value === value);
  const rows = known ? choices : [{ value, label: value }, ...choices];
  return <section className="canvas-case">
    <h2>{label}</h2>
    <CycleGadget label={label} value={value} options={choices} disabled={disabled} onChange={setValue}/>
    {disabled ? null : <div className="canvas-picker" role="listbox" aria-label={`${label} choices`}>
      {rows.map((choice) => <Button key={choice.value} variant="chrome" role="option" tabIndex={-1}
        aria-selected={choice.value === value} disabled={choice.disabled} className="canvas-picker-row"
        data-active={choice.value === (active ?? value) || undefined} onClick={() => setValue(choice.value)}>
        <span className="canvas-check" aria-hidden="true">{choice.value === value ? "✓" : ""}</span>
        <span>{choice.label ?? choice.value}</span>
      </Button>)}
    </div>}
  </section>;
}
const languages = ["English", "Deutsch", "Español", "Français", "Italiano", "Nederlands", "Polski", "Português", "Svenska", "Türkçe", "Українська", "日本語"].map((value) => ({value}));
createRoot(document.getElementById("root")!).render(<RuntimeBusProvider><main className="desk-next canvas-desk">
  <header className="canvas-head">Workbench pickers · library direction</header>
  <DeskWindowFrame id="workbench-picker-canvas" title="Workbench pickers" label="Workbench pickers" minW={320} defaultW={1000} defaultH={660} open entrance={false} onClose={() => undefined} className="desk-surface-window">
  <div className="desk-surface-body canvas-window">
    <h1>Pick a choice</h1>
    <div className="canvas-cases">
      <Proposal label="Provider" initial="On this Mac" active="OpenAI" choices={[
        {value:"On this Mac"}, {value:"OpenAI"}, {value:"Anthropic"}, {value:"Remote engine",disabled:true},
      ]}/>
      <Proposal label="Language" initial="English" active="Polski" choices={languages}/>
      <Proposal label="Destination" initial="Project archive" choices={[
        {value:"Notes"}, {value:"Senior architecture review — platform modernization and delivery"}, {value:"External notes",disabled:true},
      ]}/>
      <Proposal label="Held" initial="OpenAI" disabled choices={[{value:"OpenAI"},{value:"On this Mac"}]}/>
    </div>
  </div>
  </DeskWindowFrame>
</main></RuntimeBusProvider>);
