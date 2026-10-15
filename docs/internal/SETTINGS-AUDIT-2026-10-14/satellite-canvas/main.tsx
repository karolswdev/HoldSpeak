import React from "react";
import { createRoot } from "react-dom/client";
import { Button } from "../../../../web/src/components/signal/Signal";
import { GadgetGroup, GadgetRow, StringGadget, StateChip, EgressChip, FilterTokens, SurfaceWell, SurfaceFooter } from "../../../../web/src/desk/surface";
import "../../../../web/src/styles/global.css";
import "../../../../web/src/styles/react-app.css";
import "../../../../web/src/desk/desk.css";
import "../../../../web/src/desk/components/window-interior.css";
import "../../../../web/src/desk/surface/surface.css";
import "../../../../web/src/pages/cores/settings.css";
import "../../../../web/src/pages/cores/connections/connections.css";
import "./canvas.css";
const noop = () => {};
function Canvas() {
  const pane = new URLSearchParams(location.search).get("pane") ?? "accounts";
  return <main className="desk-next canvas"><section className="desk-window desk-window-shell canvas-window"><header className="canvas-title">Settings</header><div className="canvas-body"><div className="prefs-module">
    <h2 className="gadget-pane-title">{pane === "people" ? "People" : pane === "guide" ? "Guide" : "Accounts"}</h2>
    {pane === "accounts" ? <>
      <GadgetGroup label="Accounts"><div className="connections-tool-row"><span className="connections-tool-identity"><span className="connections-tool-label">architecture-delivery.atlassian.net</span></span><span className="connections-tool-summary">karol@example.com</span><StateChip state="warning" label="Not signed in"/><div className="connections-tool-actions"><Button dense variant="secondary">Recheck</Button><EgressChip label="ARCHITECTURE-DELIVERY.ATLASSIAN.NET" scope="cloud"/></div><SurfaceWell><code>acli jira auth login --site architecture-delivery.atlassian.net --email karol@example.com --token</code></SurfaceWell></div><Button dense variant="ghost">Add account</Button></GadgetGroup>
      <GadgetGroup label="Add account"><GadgetRow label="Site"><StringGadget label="Site" value="architecture.atlassian.net" onChange={noop}/></GadgetRow><GadgetRow label="Email"><StringGadget label="Email" value="karol@example.com" onChange={noop}/></GadgetRow><div className="canvas-verbs"><Button dense variant="primary">Add</Button><StateChip state="failure" label="Account not added"/><Button dense variant="ghost">Retry</Button></div></GadgetGroup>
      <GadgetGroup label="Destination"><GadgetRow label="Account"><span className="canvas-verbs"><StateChip state="warning" label="No Jira account"/><Button dense variant="secondary">Set up account</Button></span></GadgetRow><GadgetRow label="Work item"><StringGadget label="Work item" value="PAY-118" onChange={noop}/></GadgetRow><Button dense disabled>Save</Button></GadgetGroup>
    </> : pane === "people" ? <><GadgetGroup label="You"><GadgetRow label="Your name"><StringGadget label="Your name" value="Karol" onChange={noop}/></GadgetRow><GadgetRow label="Also called"><StringGadget label="Also called" value="Carol" onChange={noop}/></GadgetRow></GadgetGroup><GadgetGroup label="Agents"><GadgetRow label="Agent access" wide><FilterTokens label="Agent access" value="write" options={[{value:"off",label:"Off"},{value:"read",label:"Read"},{value:"write",label:"Read and write"}]} onChange={noop}/></GadgetRow><GadgetRow label="Agents you start"><span>Read</span></GadgetRow><GadgetRow label="Receipt"><StateChip state="success" label="Saved · Read and write"/></GadgetRow></GadgetGroup></> : <><GadgetGroup label="Readiness"><GadgetRow label="Readiness not known" wide><span className="canvas-verbs"><StateChip state="failure" label="Could not check"/><Button dense variant="secondary">Retry</Button></span></GadgetRow><GadgetRow label="Speech model" wide><span>The speech model is not installed on this device</span><Button dense variant="primary">Download</Button></GadgetRow></GadgetGroup><GadgetGroup label="Speech"><GadgetRow label="Browser voice"><span>Available</span></GadgetRow><GadgetRow label="Server voice"><span className="canvas-verbs"><StateChip state="failure" label="Could not read"/><Button dense variant="secondary">Retry</Button></span></GadgetRow></GadgetGroup></>}
    </div></div><SurfaceFooter receipt={pane === "accounts" ? <span>Account not added</span> : undefined} verbs={<Button dense variant="secondary">Settings</Button>}/></section></main>;
}
createRoot(document.getElementById("root")!).render(<Canvas/>);
