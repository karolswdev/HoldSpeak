import { useState } from "react";
import { createRoot } from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/surface/surface.css";
import "@w/pages/cores/people.css";
import "@w/features/project-room/project-room.css";
import { Button } from "@w/components/signal/Signal";
import { SurfaceSection, SurfaceRows, SurfaceRow } from "@w/desk/surface/Surface";
import { CycleGadget, StringGadget } from "@w/desk/surface/gadgets";
import { StateChip } from "@w/desk/surface/patterns/StateChip";
import { AppHead, StatusStrip } from "@w/desk/surface/kit";
import "./canvas.css";

const params = new URLSearchParams(location.search);
const pose = params.get("pose") || "detail";
const noop = () => {};
const commitments = {
  you: { id: "declared-leader-commitment", text: "Send the platform migration options to Priya Narayanan before the architecture review", due: "Due Friday" },
  they: { id: "declared-report-commitment", text: "Prepare the API compatibility plan and service rollout checklist for the platform migration", due: "Due Tuesday" },
};

function AddWell({ label, placeholder, initial = "", pending = false, submitted }: { label: string; placeholder: string; initial?: string; pending?: boolean; submitted?: string }) {
  const [text, setText] = useState(initial);
  const [open, setOpen] = useState(Boolean(initial));
  return <div className="daily-add">
    {!open ? <Button dense variant="ghost" aria-expanded={false} onClick={() => setOpen(true)}>Add</Button> : <div className="daily-add-well">
      <StringGadget label={label} value={text} onChange={setText} placeholder={placeholder}/>
      {pending && submitted ? <div className="daily-pending"><StateChip state="working" label="Adding"/><span>{submitted}</span></div> : null}
      <div className="daily-verbs"><Button dense variant="secondary" loading={pending} disabled={!text.trim()}>{pending ? "Adding" : "Add"}</Button><Button dense variant="ghost" disabled={pending} aria-expanded={true} onClick={() => setOpen(false)}>Hide</Button></div>
    </div>}
  </div>;
}

function CommitmentDetail({ direction, onClose }: { direction: keyof typeof commitments; onClose: () => void }) {
  const [workbench, setWorkbench] = useState("platform");
  const [note, setNote] = useState("");
  const item = commitments[direction];
  return <div className="people-commitment-inspector" data-ref={`commitment:${item.id}`}>
    <div className="people-inspector-head"><strong>Commitment</strong><Button dense variant="ghost" onClick={onClose}>Close</Button></div>
    <div className="people-commitment-body">{item.text}</div>
    <div className="people-delegate"><CycleGadget label="Workbench" value={workbench} onChange={setWorkbench} options={[{ value: "platform", label: "Platform migration and API compatibility" }, { value: "delivery", label: "Delivery review" }]}/><Button dense variant="secondary">Send to Workbench</Button></div>
    <div className="people-satisfy"><StringGadget label="Satisfaction note" value={note} onChange={setNote} placeholder="What fulfilled the commitment?"/><Button dense variant="secondary">Mark satisfied</Button></div>
  </div>;
}

function ObligationSection({ direction, selected, onSelect }: { direction: keyof typeof commitments; selected: keyof typeof commitments | null; onSelect: (value: keyof typeof commitments | null) => void }) {
  const item = commitments[direction];
  return <section className="people-plate">
    <h3 className="people-cap">{direction === "you" ? "YOU OWE" : "THEY OWE YOU"}<b>1</b></h3>
    <ul className="people-plate-rows"><li className="people-plate-row"><span className="people-plate-text"><Button variant="chrome" className="people-plate-title" onClick={() => onSelect(direction)} aria-expanded={selected === direction}>{item.text}</Button><span className="people-plate-meta">{item.due}</span></span><Button dense variant="ghost">Done</Button></li></ul>
    {selected === direction ? <CommitmentDetail direction={direction} onClose={() => onSelect(null)}/> : null}
    <AddWell label={direction === "you" ? "You owe" : "They owe you"} placeholder={direction === "you" ? "What you owe" : "What they owe you"}/>
  </section>;
}

function PeoplePrep() {
  const [selected, setSelected] = useState<keyof typeof commitments | null>(pose === "detail" ? "they" : null);
  return <div className="person-page daily-face">
    <AppHead fact="Priya Narayanan"><StatusStrip items={[{ text: "Direct report" }, { text: "Prep" }]}/></AppHead>
    <section className="people-next" aria-label="Next 1:1">
      <header className="people-next-bar"><span className="people-next-label">NEXT 1:1</span><span className="people-next-when">Today 14:30 · in 50 min</span></header>
      <div className="people-next-body">
        <div className="people-next-event"><span className="people-next-text"><span className="people-next-title">Platform architecture and delivery review with Priya Narayanan</span><span className="people-plate-meta">Work calendar · 14:30–15:15</span></span><Button dense>Record meeting</Button></div>
        <span className="people-plate-meta"><Button variant="chrome" className="people-pill people-pill-link" data-tone="info">Platform migration and API compatibility</Button></span>
        <div className="people-raise"><span className="people-cap">TO RAISE<b>2</b></span><ol className="people-raise-list"><li className="people-raise-row"><span className="people-raise-n">1</span><span className="people-raise-words">Agree the service rollout order and the compatibility checks.</span><Button dense variant="ghost">Remove</Button></li><li className="people-raise-row"><span className="people-raise-n">2</span><span className="people-raise-words">Review the open dependencies with the delivery team.</span><Button dense variant="ghost">Remove</Button></li></ol></div>
        <AddWell label="Add to the agenda" placeholder="What to raise" initial={pose === "pending" ? "Ask about the next service rollout owner" : ""} pending={pose === "pending"} submitted="Confirm the API compatibility test scope"/>
      </div>
    </section>
    <div className="people-owe-grid"><ObligationSection direction="you" selected={selected} onSelect={setSelected}/><ObligationSection direction="they" selected={selected} onSelect={setSelected}/></div>
    <SurfaceSection label="Last time"><SurfaceRows><SurfaceRow title="Platform architecture review" detail="Stage the migration by service; keep the old API available through the transition." meta="Oct 15 · Meeting" onOpen={noop}/></SurfaceRows></SurfaceSection>
    <SurfaceSection label="Open work"><SurfaceRows><SurfaceRow title="API compatibility plan" detail="Ania Kowalska · Due Tuesday" onOpen={noop}/></SurfaceRows></SurfaceSection>
  </div>;
}

function Project() {
  const [sourceOpen, setSourceOpen] = useState(pose === "source");
  const [source, setSource] = useState("Platform architecture review");
  const pending = params.get("pending") !== "none";
  const secondary = sourceOpen ? "secondary" : "primary";
  return <div className="daily-face room-body">
    <div className="room-head"><div className="room-head-line"><span className="surface-display room-headline">{pending ? "3 open here" : "1 open here"}</span><span className="room-head-strip">Target Oct 27 · Read 09:12</span><span className="room-head-trailing daily-verbs">{pending ? <Button dense variant={secondary}>Review 2</Button> : null}<Button dense variant={pending ? "secondary" : secondary}>Draft update</Button></span></div><p className="room-head-outcome">Release each service with API compatibility checks.</p></div>
    <SurfaceSection label="Sources" actions={!sourceOpen ? <Button dense variant="ghost" onClick={() => setSourceOpen(true)}>Add source</Button> : undefined}>
      {sourceOpen ? <div className="daily-add-well"><StringGadget label="Source" value={source} onChange={setSource} placeholder="Find a source"/><div className="daily-verbs"><Button>Add source</Button><Button variant="ghost" dense onClick={() => setSourceOpen(false)}>Hide</Button></div></div> : <StatusStrip items={[{ text: "Platform architecture review · Oct 15" }, { text: "API compatibility plan" }]}/>}
    </SurfaceSection>
    <SurfaceSection label="Open here"><SurfaceRows>{pending ? <><SurfaceRow title="Stage the platform migration by service" detail="Awaiting review · Platform architecture review" onOpen={noop}/><SurfaceRow title="Confirm API compatibility test coverage" detail="Awaiting review · Delivery risks and dependency review" onOpen={noop}/></> : null}<SurfaceRow title="Resolve the rollout owner for the reporting service" detail="Due Tuesday · Priya Narayanan" onOpen={noop}/></SurfaceRows></SurfaceSection>
    <div className="daily-support"><SurfaceSection label="Plan"><SurfaceRows><SurfaceRow title="API compatibility checks" detail="Ania Kowalska · Due Tuesday"/><SurfaceRow title="First service rollout" detail="Priya Narayanan · Target Oct 27"/></SurfaceRows></SurfaceSection><SurfaceSection label="Signals"><SurfaceRows><SurfaceRow title="Service rollout dependency" detail="Delivery team · Updated Oct 15"/></SurfaceRows></SurfaceSection></div>
  </div>;
}

const face = params.get("surface") || "people";
const Content = face === "project" ? Project : PeoplePrep;
const title = face === "project" ? "Platform migration and API compatibility" : "People · Prep";
createRoot(document.getElementById("root")!).render(<main className="desk-next daily-ground"><section className="daily-window"><header className="daily-window-title">{title}</header><div className="desk-surface-body daily-body"><Content/></div></section></main>);
