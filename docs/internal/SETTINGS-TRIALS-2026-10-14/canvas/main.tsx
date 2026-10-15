// Direction only: production library species, canvas data, no product API.
import { createRoot } from "react-dom/client";
import { useState, useRef } from "react";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "@w/features/runson/runson.css";
import { Button } from "@w/components/signal/Signal";
import { DeskWindowFrame } from "@w/desk/components/DeskWindow";
import { SurfaceSwitchboard, EgressChip, FoldGadget, useSwitchboardLayout } from "@w/desk/surface";
import { RuntimeBusProvider } from "@w/runtime/RuntimeBus";
import "./canvas.css";

window.fetch = async () => new Response("{}", { status: 200, headers: { "content-type": "application/json" } });
const definitions = [
  ["speech_recognition", "Speech to text", "Whisper small · on this Mac"],
  ["writing_dictation", "Dictation clean-up", "Qwen3.8 27B · on 192.168.1.43"],
  ["thoughts_notes", "Answers and notes", "Qwen3.8 27B · on 192.168.1.43"],
  ["meetings", "Meeting summaries", "Qwen3.8 27B · on 192.168.1.43"],
  ["agents_tools", "Custom tasks", "Qwen3.8 27B · on 192.168.1.43"],
  ["background", "Background work", "Qwen3.8 27B · on 192.168.1.43"],
  ["default", "Default engine", "Qwen3.8 27B · on 192.168.1.43"],
];

function Canvas() {
  const ref = useRef<HTMLDivElement>(null);
  const layout = useSwitchboardLayout(ref);
  const [selected, setSelected] = useState("thoughts_notes");
  const [state, setState] = useState(new URLSearchParams(location.search).get("state") || "idle");
  const busy = state === "busy";
  const jobs = definitions.map(([id, name, route]) => {
    const active = id === selected;
    const action = id === "default" ? null : <span className="canvas-trial-action">
      {id !== "speech_recognition" ? <EgressChip label="192.168.1.43" scope="local" /> : null}
      <Button dense variant="secondary" loading={active && busy} onClick={() => { setSelected(id); setState("busy"); }} data-testid={`canvas-try-${id}`}>Try it</Button>
    </span>;
    const result = active && state !== "idle" ? <span className="canvas-trial-result" role="status">
      <span>{busy ? "Trying" : state === "done" ? "Tried · Qwen3.8 27B · 412 ms" : "Not tried · Engine busy"}</span>
      {state === "done" ? <span className="canvas-output">The meeting is on Tuesday.</span> : null}
    </span> : null;
    return { id, name, lead: `${name} → ${route}`, tasks: "", state: "ready" as const, runsOn: route, current: id === "speech_recognition" ? "whisper" : "qwen", verb: layout === "board" ? action : undefined, result: <>
      {layout === "list" ? action : null}{result}
      {active ? <FoldGadget title="Details"><span className="canvas-details">Questions · Notes · Chat</span></FoldGadget> : null}
    </> };
  });
  return <RuntimeBusProvider><div className="desk-next canvas-desk">
    <div className="canvas-label">Direction · library components · sample data</div>
    <DeskWindowFrame id="surface-settings" title="Settings" label="Settings" minW={320} defaultW={900} defaultH={730} open entrance={false} onClose={() => undefined} className="desk-surface-window">
      <div className="desk-surface-body">
        <div className="runson-root" ref={ref}>
          <h1 className="surface-display runson-fact">2 engines</h1>
          <SurfaceSwitchboard layout={layout} jobs={jobs} engines={[
            { id: "qwen", emblem: "LAN", name: "Qwen3.8 27B", tokens: ["192.168.1.43"], lamp: "ok" },
            { id: "whisper", emblem: "MAC", name: "Whisper small", tokens: [], lamp: "ok" },
          ]} wires={definitions.map(([id]) => ({ job: id, engine: id === "speech_recognition" ? "whisper" : "qwen", order: 0 }))} selected={selected} onSelect={setSelected} captions={{ jobs: "What HoldSpeak does", engines: "What you have" }} />
        </div>
      </div>
    </DeskWindowFrame>
  </div></RuntimeBusProvider>;
}
createRoot(document.getElementById("root")!).render(<Canvas />);
