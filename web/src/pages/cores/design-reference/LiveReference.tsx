import { useEffect, useState } from "react";
import { SendFace, ProofCell } from "../../../desk/surface/send/SendWell";
import { spriteUrl } from "../../../desk/sprites";
import { Button } from "../../../components/signal/Signal";
import {
  ActionNotice,
  ObjectReader,
  ReadingDocument,
  CycleGadget,
  SegmentedTabs,
  InspectorBody,
  InspectorFacts,
  PaneNotice,
  Elapsed,
  ImageWell,
  InspectorQuestion,
  LivePane,
  ListPane,
  PreferencePane,
  FootSlotContext,
  InspectorFigures,
  InspectorForm,
  Lamp,
  ListView,
  LiveWell,
  Meter,
  PaneActions,
  PaneInspector,
  StatusBar,
  StepTrack,
  type LampState,
  type LiveLine,
  type ObjectListRow,
  type TrackStep,
} from "../../../desk/surface";

export type LivePreset = "waiting" | "working" | "done";
const names = [
  "Store the stall reason",
  "Show the reason on the step",
  "Retry a stalled step one time",
  "Write the morning recap",
];
const groups = [
  { id: 0, label: "Needs you" },
  { id: 1, label: "Running" },
  { id: 2, label: "Tonight, from 23:00" },
  { id: 3, label: "Earlier" },
];
const seedLines: LiveLine[] = [
  { id: "hand", text: "hub    handed step 2 to Claude Code" },
  { id: "read", text: "read   holdspeak/programs/steps.py" },
];
const nextLines = [
  "edit   web/src/desk/programs/StepRow.tsx  +14 −2",
  "test   step-row.app.test.tsx",
  "       12 passed in 3.1 s",
  "read   web/src/desk/walks/programs.walk.json",
  "check  step 2",
];
export const LIVE_PIECES = [
  "Program deck",
  "Send",
  "Send receipt",
  "Object reader",
  "Object working",
  "Object failed",
  "Lamp",
  "Meter",
  "Step track",
  "Track with 6 steps",
  "Track with 12 steps",
  "Whole tabs",
  "Stop verb",
  "Live well",
  "Elapsed",
  "Inspector figures",
  "Image well",
  "Inspector body",
  "Selected facts",
  "Pane notice",
  "Notice",
  "Form fit",
];

/** Local producer only. No engine, agent, screen read or hub write. */
export function LiveReference({ preset, piece: chosen, onPiece }: { preset: LivePreset; piece?: string; onPiece?(piece: string): void }) {
  const [localPiece, setLocalPiece] = useState(LIVE_PIECES[0]);
  const piece = chosen ?? localPiece, setPiece = onPiece ?? setLocalPiece;
  const [added, setAdded] = useState(false);
  return (
    <section
      className="reference-live"
      aria-label="Live pieces"
      data-testid="reference-live"
    >
      {!chosen ? <div className="reference-live-picker">
        <CycleGadget
          label="Live piece"
          value={piece}
          options={LIVE_PIECES.map((value) => ({ value }))}
          onChange={setPiece}
        />
      </div> : null}
      {piece === "Send" ? <div className="reference-live-alone"><SendFace onAddDestination={() => setAdded(true)} destination={{id:added ? "weekly" : "folder",name:added ? "Weekly reports" : "Reports folder",channel:"file" as const,target:{},account:{}}}
        destinations={[{id:"folder",name:"Reports folder",channel:"file" as const,target:{},account:{}},...(added ? [{id:"weekly",name:"Weekly reports",channel:"file" as const,target:{},account:{}}] : [])]} onDestination={id => setAdded(id === "weekly")}
        preview={{fields:[{label:"Name",value:"Weekly report.md"}],body_kind:"markdown",body:"The weekly report is ready."}}
        completion={{cancel:() => setPiece("Program deck"),primary:{label:"Send",run:() => setPiece("Send receipt")}}} /><StatusBar items={[{text:"New"}]} /></div>
      : piece === "Send receipt" ? <InspectorFacts name="Receipt" rows={[{label:"When",value:"2026-10-15"},{label:"Result",value:<ProofCell channel="file" proof={{path:"/Users/owner/Reports/Architecture/Weekly report.md"}} /> }]} />
      : piece === "Notice" ? <PreferencePane label="Failed save"><ActionNotice tone="danger" role="alert" keeps="Your edits stay here." action={{label:"Try again",onClick:()=>setPiece("Object reader")}}>No answer from the engine</ActionNotice><StatusBar items={[{text:"12 results"},{text:"Last update Nov 9, 21:24"},{text:"No answer from the engine",notice:"Failed",lamp:"fail"},{text:"Needs you",lamp:"ask"}]} /></PreferencePane>
      : piece === "Stop verb" ? <ListView label="Live calls" rows={[{id:"live",kind:"call",name:"Review the platform plan"}]} selectedId="live" columns={[{key:"name",word:"Call"}]} verbs={[{id:"hang-up",label:"Hang up",variant:"stop",enabled:()=>true,run:()=>setPiece("Elapsed")},{id:"call",label:"Call me",enabled:()=>false,run:()=>{}}]} />
      : piece === "Form fit" ? <PreferencePane label="Form fit"><ListPane label="New person" list={<ListView label="People" headerless rows={Array.from({length:12},(_,i)=>({id:String(i),name:"Person "+(i+1),kind:"person"}))} columns={[{key:"name",word:"Name"}]} />}>
        <PaneInspector label="New person"><InspectorForm fit="rows" rows={[{label:"Name",control:<CycleGadget roster label="Name" value="Priya" options={[{value:"Priya"}]} onChange={()=>{}} />},{label:"Relationship",control:<CycleGadget label="Relationship" value="peer" options={[{value:"peer",label:"Peer"},{value:"report",label:"Direct report"}]} onChange={()=>{}} />}]}
        completion={{cancel:()=>setPiece("Notice"),primary:{label:"Add",run:()=>setPiece("Object reader")}}} /></PaneInspector></ListPane></PreferencePane>
      : piece.startsWith("Object ") ? <ObjectReader label="Result" facts={[{label:"Engine",value:"Codex"},{label:"Time",value:"37 s"}]}
        running={piece === "Object working" ? {start:Date.now()-37000} : undefined} lines={[{id:"read",text:"Read the saved step reason"}]}
        failure={piece === "Object failed" ? "The engine did not answer" : undefined} retry={piece === "Object failed" ? {label:"Try again",run:() => setPiece("Object working")} : undefined}>
        {piece === "Object reader" ? <ReadingDocument>The reason stays with the step.</ReadingDocument> : null}
      </ObjectReader> : piece === "Program deck" ? (
        <ProgramDeck key={preset} preset={preset} />
      ) : (
        <LiveSpecimen
          key={`${piece}-${preset}`}
          piece={piece}
          preset={preset}
        />
      )}
    </section>
  );
}
function useScreen(working: boolean) {
  const [lines, setLines] = useState(seedLines);
  useEffect(() => {
    if (!working) return;
    let at = 0;
    const timer = window.setInterval(() => {
      if (document.hidden) return;
      const index = at++;
      if (index < nextLines.length)
        setLines((before) => [
          ...before,
          { id: `line-${index}`, text: nextLines[index] },
        ]);
      else window.clearInterval(timer);
    }, 2000);
    return () => window.clearInterval(timer);
  }, [working]);
  return lines;
}
function lampOf(state: string): LampState {
  return state === "working"
    ? "working"
    : state === "waiting"
      ? "waiting"
      : state === "done"
        ? "done"
        : "off";
}
function ProgramDeck({ preset }: { preset: LivePreset }) {
  const [state, setState] = useState<string>(
      preset === "done" ? "working" : preset,
    ),
    [picked, setPicked] = useState(preset === "done" ? "people" : "night");
  const [open, setOpen] = useState(false),
    [step, setStep] = useState(preset === "waiting" ? 0 : 1),
    [selected, setSelected] = useState<string | null>(null);
  const [parkedIds, setParkedIds] = useState(new Set<string>());
  const park = () => {
    setParkedIds((before) => new Set([...before, picked]));
    if (picked === "night") setState("parked");
  };
  const [since, setSince] = useState(() => Date.now() - 7000);
  const done = picked === "people" || picked === "replies",
    night = picked === "triage",
    parked =
      parkedIds.has(picked) ||
      picked === "wizard" ||
      (picked === "night" && state === "parked");
  const working =
    !done && !night && !parked && (picked === "calls" || state === "working");
  const lines = useScreen(working);
  const waiting = !done && !night && !parked && !working;
  const current = picked === "calls" ? 2 : step;
  const stepNames =
    picked === "calls"
      ? [
          "Read the call log",
          "Name the caller",
          "Draft the call note",
          "File the note in the project",
          "Ask before a call back",
          "Write the recap",
        ]
      : names;
  const steps: TrackStep[] = stepNames.map((name, i) => ({
    id: `s${i}`,
    name,
    state:
      i < current
        ? "done"
        : i === current
          ? working
            ? "working"
            : waiting
              ? "waiting"
              : "parked"
          : "planned",
  }));
  const makeRow = (
    id: string,
    name: string,
    group: number,
    detail: string,
    lamp: LampState,
    at: number,
    total: number,
    rowState: string,
  ): ObjectListRow => ({
    id,
    name,
    kind: "program",
    group,
    detail,
    leadingLamp: { state: lamp, label: rowState },
    meter: { current: at, total, state: rowState },
  });
  const rows = [
    makeRow(
      "night",
      "Overnight on the home box",
      state === "waiting" ? 0 : state === "parked" ? 3 : 1,
      `Step ${step + 1} of 4 · ${state === "waiting" ? "Waits on you" : state === "parked" ? "Parked" : "Claude Code works"}`,
      lampOf(state),
      step,
      4,
      state,
    ),
    makeRow(
      "calls",
      "Calls on the home box",
      parkedIds.has("calls") ? 3 : 1,
      parkedIds.has("calls") ? "Parked at step 3" : "Step 3 of 6 · Codex works",
      parkedIds.has("calls") ? "off" : "working",
      2,
      6,
      parkedIds.has("calls") ? "parked" : "working",
    ),
    makeRow(
      "triage",
      "Triage the inbox",
      2,
      "Tonight · 5 steps · Claude Code",
      "tonight",
      -1,
      5,
      "planned",
    ),
    makeRow(
      "wizard",
      "Ship the wizard",
      3,
      "Parked at step 2 · Fri",
      "off",
      1,
      7,
      "parked",
    ),
    makeRow(
      "people",
      "Move the People routes",
      3,
      "Finished · Today 06:12",
      "done",
      8,
      8,
      "done",
    ),
    makeRow(
      "replies",
      "Draft replies",
      3,
      "Finished · Sun 23:40",
      "done",
      5,
      5,
      "done",
    ),
  ];
  const row = rows.find((row) => row.id === picked)!;
  const advance = () => {
    setState("working");
    setStep(Math.min(step + 1, names.length - 1));
    setSince(Date.now());
  };
  return (
    <PreferencePane label="Program deck" testId="program-deck">
      <ListPane
        deck
        open={open}
        hostBack
        label="Selected example program"
        list={
          <ListView
            label="Example programs"
            headerless
            ordered
            groups={groups}
            columns={[{ key: "name", word: "Program" }]}
            rows={rows}
            selectedId={picked}
            onSelect={(id) => {
              setPicked(id);
              setSelected(null);
            }}
            onOpen={() => setOpen(true)}
            toolbar={{}}
            verbs={[
              open
                ? { enabled: () => true,
                    id: "programs",
                    label: "Programs",
                    run: () => setOpen(false),
                  }
                : { enabled: () => true,
                    id: "open",
                    label: "Open",
                    key: "Enter",
                    run: () => setOpen(true),
                  },
              {
                id: "park",
                label: "Park",
                enabled: () => !done && !night,
                run: park,
              },
            ]}
          />
        }
      >
        {!done && !night ? (
          <StepTrack
            steps={steps}
            current={`s${current}`}
            selected={selected}
            onSelect={setSelected}
            label="Program steps"
          />
        ) : null}
        <LivePane
          label={
            done
              ? row.name
              : night
                ? "Starts tonight at 23:00"
                : `Step ${current + 1} · ${stepNames[current]}`
          }
          trailing={
            <>
              <Lamp
                state={
                  done
                    ? "done"
                    : night
                      ? "tonight"
                      : working
                        ? "working"
                        : waiting
                          ? "waiting"
                          : "off"
                }
                label={row.name}
              />
              <span>
                {working
                  ? "Claude Code works"
                  : waiting
                    ? "Waits on you"
                    : done
                      ? "Finished"
                      : night
                        ? "Tonight"
                        : "Parked"}
              </span>
              {working ? <Elapsed start={since} /> : null}
            </>
          }
          well={
            working ? (
              <LiveWell
                label="Agent screen"
                lines={lines}
                show={5}
                working
                data-feedback-redact="true"
              />
            ) : undefined
          }
          figures={
            done ? (
              <InspectorFigures
                label="Program recap"
                figures={[
                  { value: 8, label: "steps done" },
                  { value: 0, label: "questions to you" },
                  { value: "1 h 52 min", label: "from start to end" },
                ]}
              />
            ) : undefined
          }
          facts={
            done
              ? [
                  { label: "Agent", value: "Codex, hands-off" },
                  {
                    label: "Result",
                    value: "Each check passed. The recap is in the project.",
                  },
                ]
              : night
                ? [
                    { label: "Agent", value: "Claude Code, hands-off" },
                    {
                      label: "Asks you",
                      value: "For a question about the brief",
                    },
                    { label: "In the morning", value: "A recap in Needs you" },
                  ]
                : [
                    {
                      label: "What it must prove",
                      value: "The focused test passes.",
                    },
                    { label: "Then", value: "Write the morning recap" },
                    ...(waiting
                      ? [
                          {
                            label: "What the agent did",
                            value:
                              "Added the reason to the step record. Added one test.",
                          },
                          { label: "Check", value: "Passed at 19:42" },
                        ]
                      : []),
                  ]
          }
          question={
            waiting ? (
              <InspectorQuestion
                actionId="program-go-on"
                targetId={`${picked}:${step}`}
                question="The check passed. Keep the changes and go on?"
                cancelLabel="Park"
                cancel={park}
                onDisarm={() => {}}
                variant="brass"
                verb={{ label: "Go on", run: advance }}
              />
            ) : undefined
          }
        />
      </ListPane>
      <FootSlotContext.Provider value={null}>
        <StatusBar
          items={[
            { key: "count", text: "6 programs" },
            waiting
              ? { key: "ask", text: "1 waits on you", lamp: "ask" }
              : null,
            { key: "working", text: "1 running" },
          ]}
        />
      </FootSlotContext.Provider>
    </PreferencePane>
  );
}
function LiveSpecimen({
  piece,
  preset,
}: {
  piece: string;
  preset: LivePreset;
}) {
  const [selected, setSelected] = useState<string | null>(null),
    [since] = useState(() => Date.now() - 7000);
  const lines = useScreen(preset === "working");
  if (piece === "Whole tabs") return <InspectorBody><SegmentedTabs label="Example record views" value={selected || "step"} onChange={setSelected} tabs={["Step","Requirements","Gate","Rounds","Report","Handoffs","Race","Agents"].map(label=>({id:label.toLowerCase(),label}))}><InspectorFacts header={false} name="Selected view" rows={[{label:"View",value:selected || "Step"}]} /></SegmentedTabs></InspectorBody>;
  if (piece === "Selected facts") return <InspectorFacts header={false} name="Selected step" rows={[{label:"Brief",value:"Keep the transcript."},{label:"Owns",value:"transcript.ts"},{label:"Check",value:"Green"},{label:"Agent",value:"Claude Code"},{label:"State",value:"Working"},{label:"Requirement",value:"The saved text stays."}]}/>;
  if (piece === "Pane notice")
    return <PaneNotice>This question changed. Read it again.</PaneNotice>;
  if (piece === "Inspector body")
    return (
      <PaneInspector label="Step result">
        <InspectorBody>
          <InspectorFigures
            label="Result"
            figures={[{ value: 3, label: "steps done" },{value:"4 min",label:"time"}]}
          />
          <PaneNotice>The three steps finished.</PaneNotice>
        </InspectorBody>
      </PaneInspector>
    );
  return (
    <div className="reference-live-alone">
      {piece === "Image well" ? (
        <ImageWell
          src={spriteUrl("program", "example")}
          alt="Evidence image example"
        />
      ) : null}
      {piece === "Lamp"
        ? (["working", "waiting", "done", "tonight", "off"] as const).map(
            (state) => (
              <span key={state}>
                <Lamp state={state} label={state} />{" "}
                {state === "working"
                  ? "In work"
                  : state === "waiting"
                    ? "Waits on you"
                    : state === "done"
                      ? "Done"
                      : state === "tonight"
                        ? "Tonight"
                        : "Off"}
              </span>
            ),
          )
        : null}
      {piece === "Meter" ? (
        <>
          <Meter current={2} total={6} state={preset} />
          <Meter current={13} total={20} state={preset} />
        </>
      ) : null}
      {["Step track", "Track with 6 steps", "Track with 12 steps"].includes(piece) ? (
        <StepTrack
          label="Example steps"
          steps={Array.from({ length: piece === "Track with 6 steps" ? 6 : 12 }, (_, i) => ({
            id: String(i),
            name: names[i % names.length],
            state:
              preset === "done" || i < 3
                ? "done"
                : i === 3
                  ? preset
                  : "planned",
          }))}
          current="3"
          selected={selected}
          onSelect={setSelected}
        />
      ) : null}
      {piece === "Live well" ? (
        <LiveWell
          lines={preset === "waiting" ? lines.slice(0,1) : lines}
          show={7}
          label="Example screen"
          working={preset === "working"}
          data-feedback-redact="true"
        />
      ) : null}
      {piece === "Elapsed" ? (
        <Elapsed
          start={since}
          running={preset === "working"}
          end={preset === "done" ? since + 112000 : undefined}
        />
      ) : null}
      {piece === "Inspector figures" ? (
        <InspectorFigures
          label="Example recap"
          figures={[
            { value: 8, label: "steps done" },
            { value: 0, label: "questions to you" },
            { value: "1 h 52 min", label: "from start to end" },
          ]}
        />
      ) : null}
    </div>
  );
}
