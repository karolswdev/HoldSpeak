import { createRoot } from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "@w/desk/components/window-interior.css";
import "@w/desk/surface/surface.css";
import { Button } from "@w/components/signal/Signal";
import { GadgetGroup, GadgetRow, CycleGadget, FoldGadget, StringGadget, CheckGadget } from "@w/desk/surface/gadgets";
import { SurfaceSection, SurfaceLedgerRow } from "@w/desk/surface/Surface";
import { SurfaceFooter } from "@w/desk/surface/SurfaceFooter";
import "./main.css";
const noop = () => {};
function Canvas() {
 return <div className="desk-next canvas">
  <div className="canvas-label">Settings direction · synthetic values · production components</div>
  <main className="desk-window desk-window-shell canvas-window">
   <header className="canvas-title">Settings</header>
   <nav className="canvas-wings">Settings <span>Engines</span><span>Accounts</span><span>Guide</span></nav>
   <div className="canvas-body">
    <div className="prefs-module">
     <h2>Meetings</h2>
     <GadgetGroup label="Summary"><GadgetRow label="Make summary"><CycleGadget label="Summary timing" value="every" options={[{value:"off",label:"Manual"},{value:"room_linked",label:"After room meetings"},{value:"every",label:"After every meeting"}]} onChange={noop} /></GadgetRow><GadgetRow label="Engine"><span>Qwen 27B · LAN</span><Button dense variant="ghost">Change engine</Button></GadgetRow></GadgetGroup>
     <GadgetGroup label="Recording"><GadgetRow label="Microphone"><span className="gadget-fact">System default</span></GadgetRow><GadgetRow label="System audio"><span className="gadget-fact">Auto</span></GadgetRow><GadgetRow label="Auto-record"><CycleGadget label="Auto-record mode" value="off" options={[{value:"off",label:"Off"},{value:"room_linked",label:"Room meetings"},{value:"all_calendar",label:"All calendar meetings"}]} onChange={noop} /></GadgetRow><FoldGadget title="Audio devices"><GadgetRow label="Microphone name"><StringGadget label="Microphone name" value="" placeholder="System default" onChange={noop}/></GadgetRow><GadgetRow label="System audio name"><StringGadget label="System audio name" value="" placeholder="Auto" onChange={noop}/></GadgetRow></FoldGadget></GadgetGroup>
     <SurfaceSection label="Calendar"><ul className="surface-rows"><SurfaceLedgerRow wrap primary="Work" cells={<span className="gadget-fact">Mac calendar</span>} trailing={<Button dense variant="ghost">Edit</Button>} /><SurfaceLedgerRow wrap primary="Team schedule" cells={<span className="gadget-fact">Calendar feed</span>} trailing={<Button dense variant="ghost">Edit</Button>} /></ul><div className="canvas-actions"><Button dense>Add calendar</Button><Button dense variant="ghost">Add feed</Button><Button dense variant="ghost">Import image</Button></div></SurfaceSection>
     <GadgetGroup label="Export"><GadgetRow label="Auto export"><CheckGadget label="Auto export" checked={false} onChange={noop}/></GadgetRow></GadgetGroup>
     <FoldGadget title="Advanced"><GadgetRow label="Separate speakers"><CheckGadget label="Separate speakers" checked={true} onChange={noop}/></GadgetRow></FoldGadget>
    </div>
   </div>
   <SurfaceFooter receipt={<span>Saved 14:25</span>} verbs={<Button dense variant="ghost">Settings</Button>}/>
  </main>
 </div>;
}
createRoot(document.getElementById("root")!).render(<Canvas/>);
