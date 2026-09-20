import { StrictMode, useLayoutEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import artboardManifest from "../artboards.json";
import { Button } from "@production/components/signal/Signal";
import { DeskWindowFrame } from "@production/desk/components/DeskWindow";
import { useDesk } from "@production/desk/store";
import {
  ActionNotice,
  CheckGadget,
  EgressChip,
  GadgetGroup,
  GadgetRow,
  ProgressPlan,
  Receipt,
  StateChip,
  SurfaceFooter,
  SurfaceIdentity,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceRows,
  SurfaceRow,
  SurfaceSection,
  SurfaceVerbs,
  SurfaceWell,
} from "@production/desk/surface";
import "@production/styles/global.css";
import "@production/styles/react-app.css";
import "@production/desk/desk.css";
import "@production/desk/components/pullout.css";
import "@production/desk/components/window-chrome.css";
import "@production/desk/components/dock.css";
import "@production/desk/surface/gadgets.css";
import "@production/desk/surface/surface.css";
import "./gallery.css";

type ArtboardId =
  | "desk-spatial"
  | "desk-list"
  | "desk-context"
  | "desk-drawer"
  | "windows-two"
  | "windows-expose"
  | "speak-ready"
  | "speak-progress"
  | "meeting-review"
  | "thread"
  | "agents"
  | "settings"
  | "info"
  | "drop-valid"
  | "drop-refusal"
  | "command"
  | "shade"
  | "high-contrast"
  | "pseudo";

type Tone = "current" | "proposed";

type Artboard = {
  id: ArtboardId;
  label: string;
  group: string;
  tone: Tone;
  requirement: string;
  primary?: boolean;
};

const ARTBOARDS = artboardManifest as Artboard[];

const PRIMARY = ARTBOARDS.filter((artboard) => artboard.primary).map((artboard) => artboard.id);

function seedDesk(ids: string[]) {
  const rects = Object.fromEntries(
    ids.map((id, index) => [id, { x: 96 + index * 28, y: 84 + index * 24, w: 640, h: 580 }]),
  );
  useDesk.setState({ panelOrder: ids, panelRects: rects, panelSaved: ids, panelMin: [], panelMax: [] });
}

function getArtboardFromUrl(): ArtboardId {
  const value = new URLSearchParams(window.location.search).get("artboard");
  return ARTBOARDS.some((artboard) => artboard.id === value) ? (value as ArtboardId) : "desk-spatial";
}

function ArtboardBadge({ artboard }: { artboard: Artboard }) {
  return (
    <div className="fixture-artboard-badge" data-tone={artboard.tone}>
      <span className="fixture-artboard-badge-main">{artboard.tone === "current" ? "AUTHORED · SOURCE-BACKED" : "AUTHORED · PROPOSED"}</span>
      <span>{artboard.requirement}</span>
      <span>{artboard.tone === "current" ? "current behavior reference" : "future variant · implementation debt"}</span>
    </div>
  );
}

function FixtureFrame({
  id,
  title,
  glyph,
  children,
  className = "",
  defaultW = 650,
  defaultH = 500,
  actions,
}: {
  id: string;
  title: string;
  glyph: string;
  children: React.ReactNode;
  className?: string;
  defaultW?: number;
  defaultH?: number;
  actions?: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(true);
  if (!isOpen) {
    return <div className="fixture-closed"><span>{title} · PARKED</span><Button variant="ghost" dense onClick={() => setIsOpen(true)}>REOPEN</Button></div>;
  }
  return (
    <DeskWindowFrame
      id={id}
      label={title}
      title={title}
      glyph={glyph}
      actions={actions}
      open={isOpen}
      entrance={false}
      defaultW={defaultW}
      defaultH={defaultH}
      minW={320}
      minH={260}
      className={`desk-surface-window fixture-window ${className}`}
      onClose={() => setIsOpen(false)}
    >
      {children}
    </DeskWindowFrame>
  );
}

function SurfaceBody({ children }: { children: React.ReactNode }) {
  return <div className="desk-surface-body">{children}</div>;
}

function Footer({ label = "LOCAL RECEIPT" }: { label?: string }) {
  return (
    <SurfaceFooter
      egress={<EgressChip label="⌂ THIS DEVICE" />}
      receipt={<Receipt status="ok" label={label} timestamp="NOW" />}
      verbs={<Button variant="ghost" dense>OPEN RECORD</Button>}
    />
  );
}

function FixtureWorld({ selected = false }: { selected?: boolean }) {
  const objects = [
    ["note11_sel.png", "RuntimeBus boundary", 13, 15, true],
    ["tome9.png", "Desk object contract", 35, 20, false],
    ["cassette11.png", "Architecture review", 61, 14, false],
    ["automaton3.png", "Local model target", 20, 55, false],
    ["paper.png", "Host ADR", 47, 62, false],
    ["people-ledger.png", "Reports", 74, 54, false],
  ] as const;
  return (
    <div className="fixture-world" aria-label="Spatial Desk fixture">
      <div className="fixture-world-caption"><span>CHAIR</span><span>SPATIAL · 6 OBJECTS</span></div>
      {objects.map(([src, label, left, top, objectSelected]) => (
        <div key={label} className={`fixture-world-object${objectSelected && selected ? " is-selected" : ""}`} style={{ left: `${left}%`, top: `${top}%` }}>
          <img src={`/desk/sprites/${src}`} alt="" />
          <span>{label}</span>
        </div>
      ))}
      <div className="fixture-world-dock"><span className="fixture-dock-sprite">◈</span><span>DESK</span><span>ASK</span><span>MEETINGS</span><span>AGENTS</span></div>
    </div>
  );
}

function DeskListFrame({ selected = false }: { selected?: boolean }) {
  return (
    <FixtureFrame id="desk-list-window" title="DESK / WORK" glyph="▦" defaultW={700} defaultH={560}>
      <SurfaceBody>
        <SurfaceVerbs status={<StateChip state="active" label="6 OBJECTS" />}>
          <Button variant="primary" dense>NEW NOTE</Button>
          <Button variant="ghost" dense>LIST</Button>
          <Button variant="ghost" dense>SPATIAL</Button>
        </SurfaceVerbs>
        <SurfaceIdentity name="Work" chips={<><span className="surface-token">6 OBJECTS</span><span className="surface-token">LOCAL</span></>} outcome="Objects remain in the Desk until you open one." />
        <SurfaceSection label="RECENT">
          <SurfaceRows>
            <SurfaceRow glyph="▣" title="RuntimeBus boundary" detail="Note · changed 2m ago" meta="NEW" selected={selected} verbs={<Button variant="ghost" dense>INFO</Button>} />
            <SurfaceRow glyph="▤" title="Architecture review" detail="Meeting · 4 segments" meta="READY" verbs={<Button variant="ghost" dense>OPEN</Button>} />
            <SurfaceRow glyph="◈" title="Host ADR" detail="Decision · local record" meta="LOCAL" verbs={<Button variant="ghost" dense>OPEN</Button>} />
            <SurfaceRow glyph="▦" title="Desk object contract" detail="Knowledge · 12 sources" meta="INDEXED" verbs={<Button variant="ghost" dense>OPEN</Button>} />
          </SurfaceRows>
        </SurfaceSection>
        <Footer label="DESK VIEW READY" />
      </SurfaceBody>
    </FixtureFrame>
  );
}

function DeskScene({ variant }: { variant: "spatial" | "list" | "context" | "drawer" }) {
  useLayoutEffect(() => {
    seedDesk(variant === "spatial" ? [] : variant === "drawer" ? ["desk-drawer-window"] : ["desk-list-window"]);
  }, [variant]);
  return (
    <div className="fixture-desk-stage desk-next">
      <FixtureWorld selected={variant === "context"} />
      {variant === "list" ? <DeskListFrame /> : null}
      {variant === "context" ? (
        <>
          <DeskListFrame selected />
          <div className="fixture-context-menu" role="menu" aria-label="RuntimeBus boundary commands">
            <span className="fixture-context-title">RUNTIMEBUS BOUNDARY</span>
            <Button variant="ghost" dense>OPEN</Button>
            <Button variant="ghost" dense>INFO</Button>
            <Button variant="ghost" dense>ASK ABOUT THIS</Button>
            <Button variant="ghost" dense>F2 RENAME</Button>
          </div>
        </>
      ) : null}
      {variant === "drawer" ? (
        <FixtureFrame id="desk-drawer-window" title="PROJECT / KERNEL" glyph="▤" defaultW={620} defaultH={430}>
          <SurfaceBody>
            <SurfaceVerbs status={<StateChip state="active" label="LOCAL RECORD" />}>
              <Button variant="primary" dense>OPEN</Button>
              <Button variant="ghost" dense>INFO</Button>
            </SurfaceVerbs>
            <SurfaceIdentity name="Kernel" chips={<><span className="surface-token">12 SOURCES</span><span className="surface-token">LOCAL</span></>} outcome="Admission and execution remain one bounded path." />
            <SurfaceSection label="OBJECTS">
              <SurfaceRows>
                <SurfaceRow glyph="▣" title="RuntimeBus boundary" detail="The Desk reads typed frames." meta="NOTE" />
                <SurfaceRow glyph="▤" title="Host seam" detail="Opaque file references only." meta="DECISION" />
                <SurfaceRow glyph="◈" title="Placement receipt" detail="The run names its destination." meta="KNOWLEDGE" />
              </SurfaceRows>
            </SurfaceSection>
            <Footer label="DRAWER OPEN" />
          </SurfaceBody>
        </FixtureFrame>
      ) : null}
    </div>
  );
}

function WindowsScene({ expose = false }: { expose?: boolean }) {
  useLayoutEffect(() => seedDesk(["meeting-window", "thread-window"]), []);
  return (
    <div className="fixture-desk-stage desk-next">
      <FixtureWorld />
      <FixtureFrame id="meeting-window" title="MEETING / ARCHITECTURE REVIEW" glyph="◉" defaultW={660} defaultH={460} className="fixture-window-back">
        <SurfaceBody><SurfaceIdentity name="Architecture review" chips={<span className="surface-token">4 SEGMENTS</span>} /><SurfaceWell head="TRANSCRIPT · LOCAL">RuntimeBus owns one product /ws. The Desk keeps state in one store.</SurfaceWell></SurfaceBody>
      </FixtureFrame>
      <FixtureFrame id="thread-window" title="THREAD / HOST BOUNDARY" glyph="◌" defaultW={570} defaultH={380}>
        <SurfaceBody><SurfaceVerbs><Button variant="primary" dense>REPLY</Button><Button variant="ghost" dense>PIN</Button></SurfaceVerbs><SurfaceIdentity name="Host boundary" chips={<span className="surface-token">2 SOURCES</span>} /><SurfaceWell head="THREAD · 3 TURNS"><strong>Architect</strong> — Keep the web bundle as the application specification.</SurfaceWell></SurfaceBody>
      </FixtureFrame>
      {expose ? <div className="fixture-expose" aria-label="Exposé overview"><span className="fixture-expose-label">EXPOSÉ · 2 WINDOWS</span><div className="fixture-expose-cards"><div><span>MEETING</span><strong>Architecture review</strong></div><div><span>THREAD</span><strong>Host boundary</strong></div></div><Button variant="primary" dense>RETURN TO FRONT</Button></div> : null}
    </div>
  );
}

function SpeakScene({ progress = false }: { progress?: boolean }) {
  useLayoutEffect(() => seedDesk(["speak-window"]), []);
  return (
    <div className="fixture-desk-stage desk-next">
      <FixtureWorld />
      <FixtureFrame id="speak-window" title="SPEAK" glyph="◉" defaultW={600} defaultH={480}>
        <SurfaceBody>
          <SurfaceVerbs status={<StateChip state={progress ? "working" : "idle"} label={progress ? "CAPTURING" : "READY"} />}>
            <Button variant="primary">{progress ? "STOP" : "START"}</Button>
            <Button variant="ghost" dense>SETTINGS</Button>
          </SurfaceVerbs>
          <SurfaceIdentity name="Focused input" chips={<><StateChip state={progress ? "working" : "idle"} label={progress ? "CAPTURING" : "READY"} /><EgressChip label="⌂ THIS DEVICE" /></>} outcome="One admitted speech run. One final delivery." />
          {progress ? (
            <ProgressPlan ariaLabel="Speech run" steps={[
              { id: "capture", label: "CAPTURE", status: "done", detail: "Local microphone stream" },
              { id: "transcribe", label: "TRANSCRIBE", status: "running", progress: 0.68, rate: "68%", detail: "Whisper stays on the selected target" },
              { id: "deliver", label: "DELIVER", status: "queued", detail: "Focused input waits for the final text" },
            ]} />
          ) : (
            <SurfaceSection label="PREVIEW">
              <SurfaceWell head="TEXT · PREVIEW">The runtime keeps one operation boundary from speech capture to focused input delivery.</SurfaceWell>
              <div className="fixture-control-row"><Button variant="ghost" dense>DISCARD</Button><Button variant="primary" dense>DELIVER</Button></div>
            </SurfaceSection>
          )}
          <SurfaceSection label="RECEIPT"><ActionNotice tone="info" icon="i">FIXTURE STATE · no microphone or backend call is made</ActionNotice></SurfaceSection>
          <Footer label={progress ? "RUN OPEN" : "READY"} />
        </SurfaceBody>
      </FixtureFrame>
    </div>
  );
}

function MeetingScene() {
  useLayoutEffect(() => seedDesk(["meeting-review-window"]), []);
  return (
    <div className="fixture-desk-stage desk-next">
      <FixtureWorld />
      <FixtureFrame id="meeting-review-window" title="MEETING / ARCHITECTURE REVIEW" glyph="◉" defaultW={720} defaultH={590}>
        <SurfaceBody>
          <SurfaceVerbs status={<StateChip state="success" label="RETAINED" />}><Button variant="primary" dense>OPEN THREAD</Button><Button variant="ghost" dense>INFO</Button></SurfaceVerbs>
          <SurfaceIdentity name="Architecture review" chips={<><StateChip state="success" label="RETAINED" /><span className="surface-token">4 SEGMENTS</span><EgressChip label="⌂ THIS DEVICE" /></>} outcome="Make the web Desk the application specification." />
          <SurfaceSection label="TRANSCRIPT">
            <SurfaceWell head="TRANSCRIPT · 4 SEG">
              <div className="fixture-transcript"><p><time>09:14</time><strong>Architect</strong><span>Keep one HTTP client and one RuntimeBus owner.</span></p><p><time>09:18</time><strong>Architect</strong><span>A host may return opaque file references. It does not own records.</span></p><p><time>09:22</time><strong>Architect</strong><span>Measure the seam before choosing Tauri or Electron.</span></p><p><time>09:27</time><strong>HoldSpeak</strong><span>Decision candidate: web fallback remains the reference build.</span></p></div>
            </SurfaceWell>
          </SurfaceSection>
          <SurfaceSection label="REVIEW">
            <SurfaceRows><SurfaceRow glyph="✓" title="Keep the web bundle as the application specification" meta="DECISION" verbs={<Button variant="ghost" dense>OPEN</Button>} /><SurfaceRow glyph="→" title="Measure the host seam before packaging" meta="ACTION" verbs={<Button variant="ghost" dense>OPEN</Button>} /><SurfaceRow glyph="⌂" title="Show egress at the connector boundary" meta="RULE" verbs={<Button variant="ghost" dense>INFO</Button>} /></SurfaceRows>
          </SurfaceSection>
          <Footer label="MEETING RETAINED" />
        </SurfaceBody>
      </FixtureFrame>
    </div>
  );
}

function ThreadScene() {
  useLayoutEffect(() => seedDesk(["thread-review-window"]), []);
  return (
    <div className="fixture-desk-stage desk-next">
      <FixtureWorld />
      <FixtureFrame id="thread-review-window" title="THREAD / HOST BOUNDARY" glyph="◌" defaultW={660} defaultH={540}>
        <SurfaceBody>
          <SurfaceVerbs status={<StateChip state="active" label="OPEN" />}><Button variant="primary" dense>REPLY</Button><Button variant="ghost" dense>PIN</Button><Button variant="ghost" dense>INFO</Button></SurfaceVerbs>
          <SurfaceIdentity name="Host boundary" chips={<><StateChip state="active" label="OPEN" /><span className="surface-token">2 SOURCES</span></>} outcome="One retained discussion with frozen sources." />
          <SurfaceSection label="TURNS">
            <SurfaceLedger count="3 TURNS · 2 SOURCES" cols="auto 1fr auto">
              <SurfaceLedgerRow time="09:18" primary="Keep the web bundle as the application specification." cells={<span className="surface-token">ARCHITECT</span>} />
              <SurfaceLedgerRow time="09:22" primary="The host returns opaque file references only." cells={<span className="surface-token">HOLDSPEAK</span>} />
              <SurfaceLedgerRow time="09:27" primary="Measure permission denial and recovery in the same walk." cells={<span className="surface-token">ARCHITECT</span>} />
            </SurfaceLedger>
          </SurfaceSection>
          <SurfaceWell head="SOURCES · FROZEN">Architecture guide · Desktop host ADR</SurfaceWell>
          <div className="fixture-control-row"><Button variant="ghost" dense>ATTACH SOURCE</Button><Button variant="primary" dense>SEND</Button></div>
          <Footer label="THREAD OPEN" />
        </SurfaceBody>
      </FixtureFrame>
    </div>
  );
}

function AgentsScene() {
  useLayoutEffect(() => seedDesk(["agents-window"]), []);
  return (
    <div className="fixture-desk-stage desk-next">
      <FixtureWorld />
      <FixtureFrame id="agents-window" title="AGENTS" glyph="♙" defaultW={680} defaultH={520}>
        <SurfaceBody>
          <SurfaceVerbs status={<StateChip state="active" label="WORKBENCH" />}><Button variant="primary" dense>NEW WORKBENCH</Button><Button variant="ghost" dense>FILTER</Button></SurfaceVerbs>
          <SurfaceIdentity name="Agent workbenches" chips={<><span className="surface-token">2 RECORDS</span><span className="surface-token">LOCAL</span></>} outcome="A workbench is a retained record. A live process is not a record." />
          <SurfaceSection label="WORKBENCHES">
            <SurfaceRows><SurfaceRow glyph="♙" title="Muad'Dib · documentation check" detail="Claude session · HoldSpeak Philo" meta="READY" verbs={<Button variant="ghost" dense>OPEN</Button>} /><SurfaceRow glyph="♙" title="Astra · visual gallery" detail="Codex session · Desk lane" meta="OPEN" verbs={<Button variant="ghost" dense>OPEN</Button>} /></SurfaceRows>
          </SurfaceSection>
          <SurfaceSection label="AUTHORITY"><ActionNotice tone="info" icon="i">FIXTURE RECORD · process state is not inferred</ActionNotice></SurfaceSection>
          <Footer label="AGENTS READY" />
        </SurfaceBody>
      </FixtureFrame>
    </div>
  );
}

function SettingsScene({ pseudo = false }: { pseudo?: boolean }) {
  useLayoutEffect(() => seedDesk(["settings-window"]), []);
  return (
    <div className="fixture-desk-stage desk-next">
      <FixtureWorld />
      <FixtureFrame id="settings-window" title={pseudo ? "SETTINGS · PSEUDO-LOCALE" : "SETTINGS"} glyph="⚙" defaultW={620} defaultH={540} className={pseudo ? "fixture-pseudo" : ""}>
        <SurfaceBody>
          <SurfaceVerbs status={<StateChip state="active" label={pseudo ? "PSEUDO-LOCALE" : "SYSTEM"} />}><Button variant="primary" dense>SAVE</Button><Button variant="ghost" dense>RESET</Button></SurfaceVerbs>
          <SurfaceIdentity name={pseudo ? "Locale and theme expansion for retained Desk records" : "Desk settings"} chips={<><span className="surface-token">LOCAL</span><span className="surface-token">SOURCE-OF-TRUTH</span></>} outcome={pseudo ? "Stable command and object identifiers stay unchanged while translated labels expand." : "Themes change tokens. Commands and state meaning stay fixed."} />
          <GadgetGroup label="DISPLAY">
            <GadgetRow label={pseudo ? "Pseudo-locale preview with expanded labels" : "Reduced motion"} fact="PROPOSED"><CheckGadget label={pseudo ? "ENABLED FOR REVIEW" : "ON"} checked={pseudo} onChange={() => undefined} variant="token" /></GadgetRow>
            <GadgetRow label="High contrast" fact="NFR-THEME-002"><CheckGadget label="ON" checked={false} onChange={() => undefined} variant="token" /></GadgetRow>
            <GadgetRow label="Density" fact="NORMAL"><Button variant="ghost" dense>COMPACT</Button></GadgetRow>
          </GadgetGroup>
          <SurfaceSection label="BOUNDARIES"><SurfaceRows><SurfaceRow glyph="⌂" title="Provider secrets" detail="Remain outside Web state and storage." meta="RULE" /><SurfaceRow glyph="◈" title="Host files" detail="Arrive as opaque references." meta="PROPOSED" /></SurfaceRows></SurfaceSection>
          <Footer label={pseudo ? "VARIANT ONLY" : "SETTINGS READY"} />
        </SurfaceBody>
      </FixtureFrame>
    </div>
  );
}

function InfoScene() {
  useLayoutEffect(() => seedDesk(["info-window"]), []);
  return (
    <div className="fixture-desk-stage desk-next">
      <FixtureWorld selected />
      <FixtureFrame id="info-window" title="INFO / RUNTIMEBUS BOUNDARY" glyph="ⓘ" defaultW={560} defaultH={430}>
        <SurfaceBody>
          <SurfaceVerbs><Button variant="primary" dense>OPEN</Button><Button variant="ghost" dense>RENAME</Button></SurfaceVerbs>
          <SurfaceIdentity name="RuntimeBus boundary" chips={<><span className="surface-token">NOTE</span><StateChip state="active" label="RETAINED" /></>} />
          <SurfaceSection label="PROPERTIES"><GadgetGroup><GadgetRow label="Kind" fact="DESK OBJECT"><span className="fixture-value">NOTE</span></GadgetRow><GadgetRow label="Source" fact="LOCAL"><span className="fixture-value">ARCHITECTURE_GUIDE</span></GadgetRow><GadgetRow label="Updated" fact="2M AGO"><span className="fixture-value">09:27</span></GadgetRow></GadgetGroup></SurfaceSection>
          <SurfaceWell head="CONTENT · LOCAL">The product has one WebSocket owner. The Desk receives typed frames and projects them into windows.</SurfaceWell>
          <Footer label="INFO READY" />
        </SurfaceBody>
      </FixtureFrame>
    </div>
  );
}

function DropScene({ refusal = false }: { refusal?: boolean }) {
  useLayoutEffect(() => seedDesk(["drop-window"]), []);
  return (
    <div className="fixture-desk-stage desk-next">
      <FixtureWorld />
      <FixtureFrame id="drop-window" title="DESK / DROP" glyph="⇣" defaultW={620} defaultH={440}>
        <SurfaceBody>
          <SurfaceVerbs status={<StateChip state={refusal ? "failure" : "active"} label={refusal ? "REFUSED" : "DROP READY"} />}><Button variant="ghost" dense>ESCAPE</Button></SurfaceVerbs>
          <SurfaceIdentity name={refusal ? "Drop refused" : "Release operation"} chips={<StateChip state={refusal ? "failure" : "active"} label={refusal ? "REFUSED" : "READY"} />} outcome={refusal ? "The target does not accept this object kind." : "Choose the named operation before the write."} />
          <SurfaceSection label="TARGETS">
            <SurfaceRows>
              <SurfaceRow glyph={refusal ? "✗" : "✓"} title="Knowledge" detail={refusal ? "Recipe → Knowledge is not in the current matrix." : "Note → Knowledge · add membership"} meta={refusal ? "INERT" : "VALID"} verbs={<Button variant={refusal ? "ghost" : "primary"} dense disabled={refusal}>{refusal ? "UNAVAILABLE" : "FILE INTO KNOWLEDGE"}</Button>} />
              <SurfaceRow glyph="→" title="Recipe" detail="Note → Recipe · hold beside a run verb" meta={refusal ? "INERT" : "VALID"} verbs={<Button variant="ghost" dense disabled={refusal}>GROUND INTO RECIPE</Button>} />
            </SurfaceRows>
          </SurfaceSection>
          {refusal ? <ActionNotice tone="danger" icon="✗">CAN'T DROP · Recipe → Knowledge is not a supported pair</ActionNotice> : <ActionNotice tone="ok" icon="✓">RELEASE · FILE INTO KNOWLEDGE</ActionNotice>}
          <Footer label={refusal ? "NO WRITE" : "DROP READY"} />
        </SurfaceBody>
      </FixtureFrame>
    </div>
  );
}

function CommandScene({ shade = false }: { shade?: boolean }) {
  useLayoutEffect(() => seedDesk(shade ? [] : ["command-window"]), [shade]);
  return (
    <div className={`fixture-desk-stage desk-next${shade ? " is-shaded" : ""}`}>
      <FixtureWorld />
      {!shade ? <FixtureFrame id="command-window" title="COMMAND DECK" glyph="⌘" defaultW={580} defaultH={460}>
        <SurfaceBody>
          <SurfaceVerbs><Button variant="ghost" dense>ESCAPE</Button></SurfaceVerbs>
          <SurfaceIdentity name="Command deck" chips={<span className="surface-token">⌘K</span>} outcome="The registry is the vocabulary for menus, palette and keymap." />
          <SurfaceRows><SurfaceRow glyph="＋" title="Create Note" meta="⌘N" verbs={<Button variant="primary" dense>RUN</Button>} /><SurfaceRow glyph="⌕" title="Open Ask" meta="⌘I" verbs={<Button variant="ghost" dense>RUN</Button>} /><SurfaceRow glyph="▦" title="Open Desk list" meta="⌘L" verbs={<Button variant="ghost" dense>RUN</Button>} /><SurfaceRow glyph="⌘" title="Shortcut sheet" meta="⌘/" verbs={<Button variant="ghost" dense>RUN</Button>} /></SurfaceRows>
          <Footer label="COMMAND READY" />
        </SurfaceBody>
      </FixtureFrame> : <div className="fixture-shade"><span className="fixture-shade-mark">HOLDSPEAK</span><strong>SYSTEM SHADE</strong><span>ESCAPE TO RETURN</span><Button variant="primary">RETURN</Button></div>}
    </div>
  );
}

function Scene({ artboard }: { artboard: ArtboardId }) {
  switch (artboard) {
    case "desk-spatial": return <DeskScene variant="spatial" />;
    case "desk-list": return <DeskScene variant="list" />;
    case "desk-context": return <DeskScene variant="context" />;
    case "desk-drawer": return <DeskScene variant="drawer" />;
    case "windows-two": return <WindowsScene />;
    case "windows-expose": return <WindowsScene expose />;
    case "speak-ready": return <SpeakScene />;
    case "speak-progress": return <SpeakScene progress />;
    case "meeting-review": return <MeetingScene />;
    case "thread": return <ThreadScene />;
    case "agents": return <AgentsScene />;
    case "settings": return <SettingsScene />;
    case "info": return <InfoScene />;
    case "drop-valid": return <DropScene />;
    case "drop-refusal": return <DropScene refusal />;
    case "command": return <CommandScene />;
    case "shade": return <CommandScene shade />;
    case "high-contrast": return <MeetingScene />;
    case "pseudo": return <SettingsScene pseudo />;
  }
}

function Gallery() {
  const [current, setCurrent] = useState<ArtboardId>(getArtboardFromUrl);
  const artboard = useMemo(() => ARTBOARDS.find((item) => item.id === current) ?? ARTBOARDS[0], [current]);
  const bare = new URLSearchParams(window.location.search).get("bare") === "1";

  const select = (id: ArtboardId) => {
    setCurrent(id);
    const url = new URL(window.location.href);
    url.searchParams.set("artboard", id);
    window.history.replaceState({}, "", url);
  };

  return (
    <div className={`fixture-gallery${bare ? " is-bare" : ""}${current === "high-contrast" ? " is-high-contrast" : ""}`}>
      {!bare ? <header className="fixture-gallery-head">
        <div><span className="fixture-kicker">PHILO · DESK VISUAL SPECIFICATION</span><h1>HoldSpeak Desk artboard gallery</h1><p>Authored compositions for source-backed current states and clearly marked future variants.</p></div>
        <div className="fixture-head-note"><span>ANCHOR</span><strong>675401a857b8</strong><span>FIXTURE · NO LIVE API</span></div>
      </header> : null}
      {!bare ? <nav className="fixture-gallery-nav" aria-label="Artboard selector">
        {ARTBOARDS.map((item) => <Button key={item.id} variant={item.id === current ? "primary" : "ghost"} dense onClick={() => select(item.id)} aria-current={item.id === current ? "page" : undefined}>{item.label}</Button>)}
      </nav> : null}
      <main className="fixture-gallery-main">
        <div className="fixture-gallery-meta"><span>{artboard.group} · {artboard.label}</span><span>{PRIMARY.includes(artboard.id) ? "PRIMARY FACE · 1440 + 393" : "WIDE REFERENCE · 1440"}</span></div>
        <ArtboardBadge artboard={artboard} />
        <Scene artboard={artboard.id} />
        <div className="fixture-focus-order"><strong>FOCUS ORDER</strong><span>window shell → head verbs → surface verbs → records → footer egress</span><span>Keyboard: Tab through library Button controls · Escape closes the authored window</span></div>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<StrictMode><Gallery /></StrictMode>);
