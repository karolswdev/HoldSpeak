import { useState } from "react";
import { createRoot } from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/surface/surface.css";
import "@w/desk/surface/patterns/conversation.css";
import "@w/desk/pullouts/thread-pullout.css";
import "@w/desk/components/ask-panel.css";
import "@w/desk/components/mission-control.css";
import "@w/pages/cores/settings.css";
import "@w/pages/cores/settingsSurfaceRepair.css";
import { Button } from "@w/components/signal/Signal";
import { SurfaceSection, SurfaceRows, SurfaceRow, SurfaceTraffic, SurfaceTrafficTurn, SurfaceWell } from "@w/desk/surface/Surface";
import { PadGadget, CheckGadget, CycleGadget, GadgetGroup, GadgetRow } from "@w/desk/surface/gadgets";
import { StateChip } from "@w/desk/surface/patterns/StateChip";
import { ActionNotice } from "@w/desk/surface/patterns/ActionNotice";
import { Material } from "@w/desk/surface/Material";
import { AppHead, StatusStrip } from "@w/desk/surface/kit";
import "./canvas.css";

const params = new URLSearchParams(location.search);
const pose = params.get("pose") || "pending";
const noop = () => {};
const submitted = "/todo Send the platform migration options to Priya Narayanan before the architecture review";

function ThreadCommand() {
  const pending = pose === "pending";
  const unknown = pose === "unknown";
  const [draft, setDraft] = useState(pending ? "/todo Confirm the service rollout owner with Ania Kowalska" : submitted);
  return <div className="recovery-face">
    <AppHead fact="Platform architecture review"><StatusStrip items={[{ text: "Thread" }, { text: "Priya Narayanan · Ania Kowalska" }]}/></AppHead>
    <div className="conversation-reading"><SurfaceTraffic>
      <SurfaceTrafficTurn prefix="YOU"><Material>{"Prepare the platform migration options for the architecture review. Keep the API compatibility checks attached to each rollout stage."}</Material></SurfaceTrafficTurn>
      <SurfaceTrafficTurn prefix="ASSISTANT"><Material>{"## Next work\n\n- Compare the service rollout options.\n- Confirm the API compatibility checks.\n- Send the options to Priya Narayanan."}</Material></SurfaceTrafficTurn>
    </SurfaceTraffic></div>
    <SurfaceSection label="Task command">
      <div className="recovery-command"><StateChip state={pending ? "working" : "warning"} label={pending ? "Adding task" : unknown ? "Result unknown" : "Task not added"}/><span className="recovery-submitted">{submitted}</span></div>
      {!pending && !unknown ? <ActionNotice tone="warn">Task writer unavailable</ActionNotice> : null}
    </SurfaceSection>
    <div className="conversation-composer"><PadGadget label="Thread message" value={draft} onChange={setDraft} rows={3} placeholder="Continue this conversation"/><div className="recovery-verbs"><Button disabled={pending}>Send</Button></div></div>
  </div>;
}

function AskContext() {
  const known = params.get("known") !== "none";
  const [prompt, setPrompt] = useState("Compare the migration options using the platform plan and the latest architecture review.");
  const [projectPicked, setProjectPicked] = useState(true);
  const [notePicked, setNotePicked] = useState(true);
  return <div className="recovery-face">
    <AppHead fact="Ask about your work"><StatusStrip items={[{ text: "Selected note · API compatibility plan" }]}/></AppHead>
    <SurfaceSection label="Selected text"><div className="recovery-paper"><Material>{"Keep the old API available until each service passes its compatibility checks."}</Material></div></SurfaceSection>
    <div className="conversation-composer"><PadGadget label="Question" value={prompt} onChange={setPrompt} rows={3}/></div>
    <SurfaceSection label="Add notes"><div className="recovery-choices"><div className="desk-ground-line"><CheckGadget label="API compatibility plan" checked={notePicked} onChange={setNotePicked}/><span className="desk-ground-name">API compatibility plan</span></div></div></SurfaceSection>
    <SurfaceSection label="Projects">
      <ActionNotice tone="warn" action={{ label: "Retry", onClick: noop }}>Could not read Projects</ActionNotice>
      {known ? <div className="recovery-choices"><span className="surface-token">Last read · 09:12</span><div className="desk-ground-line"><CheckGadget label="Platform migration and API compatibility" checked={projectPicked} onChange={setProjectPicked}/><span className="desk-ground-name">Platform migration and API compatibility</span></div></div> : null}
    </SurfaceSection>
    <div className="recovery-verbs"><Button>Ask</Button><Button dense variant="ghost">Back to note</Button></div>
  </div>;
}

function ProposalNotice() {
  const pending = pose === "pending";
  const approved = params.get("decision") !== "decline";
  const action = approved ? "Approve" : "Decline";
  return <div className="recovery-face">
    <ActionNotice tone="warn">Dormant design sample · Excluded from product work</ActionNotice>
    <AppHead fact="Needs your decision"/>
    <aside className="ambient-qlippy recovery-notice" aria-label="Qlippy">
      <header className="ambient-notice-head"><span className="ambient-source">Platform architecture review · Oct 16</span><strong>Stage the platform migration by service with API compatibility checks</strong></header>
      <SurfaceWell><Material>{"Release one service at a time. Keep the old API available until its compatibility checks pass."}</Material></SurfaceWell>
      <StatusStrip items={[{ text: "Proposal" }, { text: "Original meeting · Platform architecture review" }]}/>
      <div className="recovery-command"><StateChip state={pending ? "working" : "failure"} label={pending ? `${action} pending` : `Could not ${action.toLowerCase()}`}/><span className="recovery-submitted">Stage the platform migration by service with API compatibility checks</span></div>
      {!pending ? <ActionNotice tone="warn" action={{ label: "Retry", onClick: noop }}>{`${action} · Decision not saved`}</ActionNotice> : null}
      <div className="ambient-verbs"><Button dense loading={pending && approved} disabled={pending}>Approve</Button><Button dense variant="ghost" loading={pending && !approved} disabled={pending}>Decline</Button><Button dense variant="ghost" disabled={pending}>Dismiss</Button></div>
    </aside>
    <SurfaceSection label="Next notice"><SurfaceRows><SurfaceRow title="Delivery risks and dependency review" detail="Waiting · Separate proposal"/></SurfaceRows></SurfaceSection>
  </div>;
}

function RemoteRecovery() {
  const [enabled, setEnabled] = useState("OFF");
  return <div className="recovery-face">
    <AppHead fact="Remote access"><StatusStrip items={[{ text: "Last read · 09:12" }]}/></AppHead>
    <GadgetGroup label="Remote access" material="inset"><GadgetRow label="Access"><CycleGadget label="Remote access" value={enabled} onChange={setEnabled} options={[{value:"OFF",label:"Off"},{value:"ON",label:"On"}]}/></GadgetRow></GadgetGroup>
    {pose === "read-failed" ? <ActionNotice tone="warn" action={{ label: "Retry", onClick: noop }}>Could not read Remote access</ActionNotice> : <ActionNotice tone="warn" action={{ label: "Reload current state", onClick: noop }}>Change not confirmed · Turn remote access on</ActionNotice>}
    <SurfaceSection label="Credentials"><SurfaceRows><SurfaceRow title="Platform assistant" detail="Last read · Active" meta="Project · Platform migration and API compatibility"/></SurfaceRows>
      <GadgetRow label="Platform migration review" wide controlWidth="full">
        <span className="prefs-project-line"><span className="surface-token" data-chip>RUN AND PUBLISH ALLOWED</span><Button dense variant="ghost" onClick={noop}>Stop run and publish</Button></span>
      </GadgetRow>
    </SurfaceSection>
  </div>;
}

const surface = params.get("surface") || "thread";
const faces = { thread: ThreadCommand, ask: AskContext, notice: ProposalNotice, remote: RemoteRecovery };
const Face = faces[surface as keyof typeof faces] || ThreadCommand;
const names = { thread: "Thread", ask: "Ask", notice: "Notice", remote: "Settings" };
createRoot(document.getElementById("root")!).render(<main className="desk-next recovery-ground"><section className="recovery-window"><header className="recovery-window-title">{names[surface as keyof typeof names] || "Thread"}</header><div className="desk-surface-body recovery-body"><Face/></div></section></main>);
