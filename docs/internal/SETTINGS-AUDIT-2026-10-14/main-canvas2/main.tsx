import { useState } from "react";
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
import { CONTROL_MODES, controlModeLabel } from "/web/src/lib/productLanguage";
import { GadgetGroup, GadgetRow, CycleGadget, CheckGadget, StringGadget, FoldGadget } from "/web/src/desk/surface/gadgets";
import { SurfaceSection, SurfaceLedger, SurfaceLedgerRow } from "/web/src/desk/surface/Surface";
import "./main.css";

const windowId = "settings-visual-direction-2";
useDesk.setState({ panelOrder: [windowId], panelMax: [windowId], panelMin: [] });
const noop = () => {};
const icon = (name: string) => <img className="settings2-icon" alt="" src={`/web/public/desk/sprites/settings/${name}.png`} />;
const wings = [{id:"settings",label:"Settings"},{id:"engines",label:"Engines"},{id:"accounts",label:"Accounts"},{id:"guide",label:"Guide"}];

function Canvas() {
  const [pane, setPane] = useState(new URLSearchParams(location.search).get("pane") === "meetings" ? "meetings" : "home");
  const [foot, setFoot] = useState<HTMLDivElement | null>(null);
  const [summary, setSummary] = useState("every");
  const [record, setRecord] = useState("off");
  const [exportOn, setExportOn] = useState(false);
  const [editCalendar, setEditCalendar] = useState(false);
  const [name, setName] = useState("Work");
  const modules = [
    {name:"Voice",sprite:"voice",fact:"Push to talk"},
    {name:"Meetings",sprite:"meetings",fact:"Summary after each meeting"},
    {name:"Rhythm",sprite:"rhythm",fact:"Morning brief at 6"},
    {name:"Engines",sprite:"models",fact:"Qwen 27B"},
    {name:"Accounts",sprite:"integrations",fact:"None connected"},
    {name:"Sounds & Presence",sprite:"sounds",fact:"Desk sounds on"},
    {name:"Wallpaper",sprite:"wallpaper",fact:"Quiet Desk"},
    {name:"People",sprite:"system",fact:"Read and write"},
    {name:"System",sprite:"system",fact:"Other devices off"},
  ];
  const directory = (entries: typeof modules) => <SurfaceLedger count={null} cols="kit" label="Preferences">
    {entries.map((entry) => <SurfaceLedgerRow
      key={entry.name}
      lead={icon(entry.sprite)}
      primary={<span className="settings2-directory-name">{entry.name}<span className="settings2-directory-fact">{entry.fact}</span></span>}
      trailing={<Button dense variant="secondary" onClick={() => { if (entry.name === "Meetings") setPane("meetings"); }}>Open</Button>}
      expands={false}
    />)}
  </SurfaceLedger>;

  return <div className="desk-next settings2-canvas">
    <DeskWindowFrame
      id={windowId} title="Settings" open onClose={noop} onBack={() => setPane("home")}
      className="desk-surface-window settings2-window" entrance={false}
      wings={<SurfaceWings wings={wings} active="settings" onChange={() => setPane("home")} />}
    >
      <FootSlotContext.Provider value={foot}>
        <div className="desk-surface-body settings2-body">
          {pane === "home" ? <div className="settings2 settings2-home" data-pane="home">
            <div className="settings2-directory-grid">
              <SurfaceSection label="Work">{directory(modules.slice(0,5))}</SurfaceSection>
              <SurfaceSection label="Desk">{directory(modules.slice(5))}</SurfaceSection>
            </div>
            <div className="settings2-control-mode"><GadgetRow label="Control mode"><CycleGadget label="Control mode" value="neutral" options={CONTROL_MODES.map(value => ({value,label:controlModeLabel(value)}))} onChange={noop}/></GadgetRow></div>
          </div> : <div className="settings2" data-pane="meetings">
            <h2 className="settings2-module-title">Meetings</h2>
            <div className="settings2-groups">
              <div className="settings2-column">
                <GadgetGroup label="Summary">
                  <GadgetRow label="Make summary"><CycleGadget label="Auto-run the summary" value={summary} options={[{value:"off",label:"Manual"},{value:"room_linked",label:"After room meetings"},{value:"every",label:"After every meeting"}]} onChange={setSummary}/></GadgetRow>
                  <GadgetRow label="Engine"><span className="settings2-value">Qwen 27B</span><Button dense variant="secondary">Change</Button></GadgetRow>
                </GadgetGroup>
                <GadgetGroup label="Recording">
                  <GadgetRow label="Microphone"><span className="settings2-value">System default</span></GadgetRow>
                  <GadgetRow label="System audio"><span className="settings2-value">Auto</span></GadgetRow>
                  <GadgetRow label="Auto-record"><CycleGadget label="Auto-record mode" value={record} options={[{value:"off",label:"Off"},{value:"room_linked",label:"Room meetings"},{value:"all_calendar",label:"All calendar meetings"}]} onChange={setRecord}/></GadgetRow>
                  <FoldGadget title="Audio devices"><GadgetRow wide label="Microphone name"><StringGadget label="Microphone name" value="" placeholder="System default" onChange={noop}/></GadgetRow><GadgetRow wide label="System audio name"><StringGadget label="System audio name" value="" placeholder="Auto" onChange={noop}/></GadgetRow></FoldGadget>
                </GadgetGroup>
              </div>
              <div className="settings2-column">
                <SurfaceSection label="Calendar" className="settings2-calendar">
                  <SurfaceLedger count={null} cols="kit">
                    <SurfaceLedgerRow lead={icon("meetings")} primary={<span className="settings2-directory-name">{name}<span className="settings2-directory-fact">Mac calendar</span></span>} trailing={<Button dense variant="secondary" onClick={() => setEditCalendar(!editCalendar)}>Edit</Button>} expands={false} open={editCalendar}>
                      {editCalendar ? <div className="settings2-calendar-edit"><GadgetRow wide label="Name"><StringGadget label="Calendar name" value={name} onChange={setName}/></GadgetRow><Button dense variant="secondary" onClick={() => setEditCalendar(false)}>Done</Button></div> : null}
                    </SurfaceLedgerRow>
                    <SurfaceLedgerRow lead={icon("meetings")} primary={<span className="settings2-directory-name">Personal<span className="settings2-directory-fact">Calendar feed · Disabled</span></span>} trailing={<Button dense variant="secondary">Edit</Button>} expands={false}/>
                  </SurfaceLedger>
                  <div className="settings2-calendar-actions"><Button dense variant="primary">Add calendar</Button><Button dense variant="secondary">Add feed</Button><Button dense variant="secondary">Import image</Button></div>
                </SurfaceSection>
                <GadgetGroup label="Export">
                  <GadgetRow label="Auto export"><CheckGadget label="Auto export" checked={exportOn} onChange={setExportOn}/></GadgetRow>
                  {exportOn ? <GadgetRow label="Format"><CycleGadget label="Export format" value="markdown" options={[{value:"markdown",label:"MD"},{value:"txt",label:"TXT"}]} onChange={noop}/></GadgetRow> : null}
                </GadgetGroup>
              </div>
            </div>
            <FoldGadget title="Advanced"><span className="settings2-meta">Capture · Summary · Routing</span></FoldGadget>
          </div>}
        </div>
        <SurfaceFooter receipt={<span>Saved 14:25</span>} verbs={pane === "meetings" ? <Button dense variant="secondary" onClick={() => setPane("home")}>Settings</Button> : undefined}/>
        <div ref={setFoot} className="surface-footer"/>
      </FootSlotContext.Provider>
    </DeskWindowFrame>
    <div className="settings2-canvas-note">Design direction 2 · Synthetic values · Production window and controls</div>
  </div>;
}
createRoot(document.getElementById("root")!).render(<Canvas/>);
