import { useState } from "react";
import { createRoot } from "react-dom/client";
import { Button } from "../../../../web/src/components/signal/Signal";
import { DeskWindowFrame } from "../../../../web/src/desk/components/DeskWindow";
import { useDesk } from "../../../../web/src/desk/store";
import { SurfaceWings } from "../../../../web/src/desk/surface/wings";
import { FootSlotContext } from "../../../../web/src/desk/surface/foot";
import { CheckGadget, CycleGadget, EgressChip, FoldGadget, GadgetGroup, GadgetRow, PadGadget, StateChip, StringGadget, SurfaceFooter, SurfaceLedger, SurfaceLedgerRow, SurfaceSection, SurfaceWell } from "../../../../web/src/desk/surface";
import "../../../../web/src/styles/global.css";
import "../../../../web/src/styles/react-app.css";
import "../../../../web/src/desk/desk.css";
import "../../../../web/src/desk/components/window-interior.css";
import "../../../../web/src/desk/surface/surface.css";
import "./canvas.css";

const HOST = "architecture-research-and-platform-delivery.atlassian.net";
const ACCOUNT = "senior.architect.with.reports@example.com";
const noop = () => {};
const windowId = "settings-satellite-visual-direction-2";
useDesk.setState({ panelOrder: [windowId], panelMax: [windowId], panelMin: [] });
const wings = [{ id: "settings", label: "Settings" }, { id: "engines", label: "Engines" }, { id: "accounts", label: "Accounts" }, { id: "guide", label: "Guide" }];

function Canvas() {
  const [foot, setFoot] = useState<HTMLDivElement | null>(null);
  const query = new URLSearchParams(location.search);
  const state = query.get("state") ?? "populated";
  const [well, setWell] = useState(state === "refused" || state === "add" ? "jira:add" : state === "signin" ? "github:signin" : "");
  const [site, setSite] = useState(state === "refused" ? "another-architecture-team.atlassian.net" : "");
  const [email, setEmail] = useState(state === "refused" ? "architect@example.com" : "");
  const [copied, setCopied] = useState(false);
  const [folder, setFolder] = useState("/Users/karol/Documents/Architecture/reports");
  const [destinationName, setDestinationName] = useState("Architecture reports");
  const [synced, setSynced] = useState(false);
  const editingDestination = state.startsWith("destination");
  const refused = state === "refused";
  const active = Boolean(well) || editingDestination;
  const providers = [{ id: "github", name: "GitHub", account: "", state: "Not signed in" }, { id: "jira", name: "Jira", account: ACCOUNT, state: "Not checked" }, { id: "confluence", name: "Confluence", account: ACCOUNT, state: "Not checked" }];
  const title = "Accounts";

  const signIn = (provider: string) => <SurfaceWell><div className="v2-well-head"><strong>Sign in to {provider === "github" ? "GitHub" : provider === "jira" ? "Jira" : "Confluence"}</strong><Button dense variant="ghost" onClick={() => setWell("")}>Close</Button></div><div className="v2-command"><code>{provider === "github" ? "gh auth login" : `acli ${provider} auth login --site ${HOST} --email ${ACCOUNT} --token`}</code><Button dense variant="secondary" onClick={() => setCopied(true)}>{copied ? "Copied" : "Copy command"}</Button></div><div className="v2-actions"><EgressChip label={provider === "github" ? "GITHUB.COM" : HOST} scope="cloud"/><Button dense variant="primary">Check sign-in</Button></div></SurfaceWell>;

  return <main className="desk-next v2"><DeskWindowFrame id={windowId} title="Settings" open onClose={noop} onBack={noop} className="desk-surface-window v2-window" entrance={false} wings={<SurfaceWings wings={wings} active="accounts" onChange={noop}/> }><FootSlotContext.Provider value={foot}><div className="desk-surface-body v2-body"><div className="v2-content"><h2>{title}</h2>
    {<>
      <div className="v2-account-column"><SurfaceSection label="Services"><SurfaceLedger count="" cols="room"><ul className="surface-ledger-rows v2-services">
        {providers.map((provider) => <SurfaceLedgerRow key={provider.id} wrap expands={false} open={well.startsWith(provider.id)} lead={<span className="v2-initial">{provider.name === "GitHub" ? "GH" : provider.name[0]}</span>} primary={<span className="v2-identity"><strong>{provider.name}</strong>{provider.account ? <span className="v2-account">{provider.account.split("@")[0]}@<wbr/>{provider.account.split("@")[1]}</span> : null}</span>} cells={<span className="surface-ledger-cells v2-state"><StateChip state={provider.id === "github" ? "warning" : "idle"} label={provider.state}/></span>} trailing={<span className="v2-actions"><Button dense variant={provider.id === "github" && !active ? "primary" : "secondary"} onClick={() => { setCopied(false); setWell(well === `${provider.id}:signin` ? "" : `${provider.id}:signin`); }}>Sign-in details</Button></span>}>
          {well === `${provider.id}:signin` ? signIn(provider.id) : <SurfaceWell><div className="v2-well-head"><strong>Add {provider.name} account</strong></div><GadgetGroup><GadgetRow label="Site"><StringGadget label="Site" value={site} onChange={setSite} placeholder="site.atlassian.net"/></GadgetRow><GadgetRow label="Email"><StringGadget label="Email" value={email} onChange={setEmail} placeholder="you@example.com"/></GadgetRow></GadgetGroup>{refused ? <div className="v2-outcome" role="alert"><StateChip state="failure" label="Account not added"/></div> : null}<div className="v2-actions"><Button dense variant="primary">{refused ? "Retry" : "Add account"}</Button><Button dense variant="ghost" onClick={() => setWell("")}>Cancel</Button></div><FoldGadget title="Sign-in command"><div className="v2-command"><code>{`acli ${provider.id} auth login --site ${site || "<site>"} --email ${email || "<email>"} --token`}</code><Button dense variant="secondary" onClick={() => setCopied(true)}>{copied ? "Copied" : "Copy command"}</Button></div></FoldGadget></SurfaceWell>}
        </SurfaceLedgerRow>)}
      </ul></SurfaceLedger><div className="v2-actions v2-section-actions"><Button dense variant="ghost" onClick={() => setWell("jira:add")}>Add Jira account</Button><Button dense variant="ghost" onClick={() => setWell("confluence:add")}>Add Confluence account</Button></div></SurfaceSection>
      <SurfaceSection label="Calendar"><SurfaceLedger count="" cols="room"><ul className="surface-ledger-rows"><SurfaceLedgerRow wrap expands={false} lead={<span className="v2-initial">▦</span>} primary={<span className="v2-identity"><strong>Calendar</strong><span className="v2-account">Work · Mac calendar</span></span>} cells={<span className="surface-ledger-cells"><StateChip state="success" label="Connected"/></span>} trailing={<Button dense variant="secondary">Choose calendar</Button>}/></ul></SurfaceLedger></SurfaceSection>
      </div><div className="v2-destination-column"><SurfaceSection label="Send to"><SurfaceLedger count="" cols="room"><ul className="surface-ledger-rows"><SurfaceLedgerRow wrap expands={false} lead={<span className="v2-initial">▸</span>} primary={<span className="v2-identity"><strong>HoldSpeak folder</strong><span className="v2-account">Documents / HoldSpeak / Sent</span></span>} cells={<span className="surface-ledger-cells v2-kind">Folder</span>} trailing={<Button dense variant="ghost">Edit</Button>}/></ul></SurfaceLedger>
        {editingDestination ? <SurfaceWell><div className="v2-well-head"><strong>Add destination</strong></div><GadgetGroup><GadgetRow label="Send to"><CycleGadget label="Channel" value="file" options={[{value:"file",label:"Folder"},{value:"email",label:"Email"}]} onChange={noop}/></GadgetRow><GadgetRow label="Name"><StringGadget label="Name" value={destinationName} onChange={setDestinationName}/></GadgetRow><GadgetRow label="Folder"><PadGadget label="Folder" value={folder} onChange={setFolder} rows={2}/></GadgetRow><GadgetRow label="Synced folder"><CheckGadget label="Synced folder" checked={synced} onChange={setSynced}/></GadgetRow></GadgetGroup>{state === "destination-refused" ? <div className="v2-outcome"><StateChip state="failure" label="Not saved · Folder not found"/></div> : null}<div className="v2-actions"><Button dense variant="primary">{state === "destination-refused" ? "Retry" : "Save"}</Button><Button dense variant="ghost">Cancel</Button></div></SurfaceWell> : <div className="v2-actions v2-section-actions"><Button dense variant="ghost">Add destination</Button></div>}
      </SurfaceSection><FoldGadget title="Credentials"/><FoldGadget title="Advanced"/></div>
    </>}
    </div></div><SurfaceFooter receipt={refused ? <span>Account not added</span> : undefined} verbs={<Button dense variant="ghost">Settings</Button>}/><div ref={setFoot} className="surface-footer"/></FootSlotContext.Provider></DeskWindowFrame><div className="v2-canvas-note">Design direction 2 · Synthetic accounts · Production window and controls</div></main>;
}
createRoot(document.getElementById("root")!).render(<Canvas/>);
