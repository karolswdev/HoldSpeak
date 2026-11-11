import { useEffect, useState } from "react";
import { spriteUrl } from "../../../desk/sprites";
import { Button } from "../../../components/signal/Signal";
import {
  CycleGadget,
  InspectorBody,
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
const pieces = [
  "Program deck",
  "Lamp",
  "Meter",
  "Step track",
  "Live well",
  "Elapsed",
  "Inspector figures",
  "Image well",
  "Inspector body",
  "Pane notice",
];

/** Local producer only. No engine, agent, screen read or hub write. */
export function LiveReference({ preset }: { preset: LivePreset }) {
  const [piece, setPiece] = useState(pieces[0]);
  return (
    <section
      className="reference-live"
      aria-label="Live pieces"
      data-testid="reference-live"
    >
      <div className="reference-live-picker">
        <CycleGadget
          label="Live piece"
          value={piece}
          options={pieces.map((value) => ({ value }))}
          onChange={setPiece}
        />
      </div>
      {piece === "Program deck" ? (
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
                ? {
                    id: "programs",
                    label: "Programs",
                    run: () => setOpen(false),
                  }
                : {
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
      {piece === "Step track" ? (
        <StepTrack
          label="Example steps"
          steps={Array.from({ length: 16 }, (_, i) => ({
            id: String(i),
            name: names[i % names.length],
            state:
              preset === "done" || i < 13
                ? "done"
                : i === 13
                  ? preset
                  : "planned",
          }))}
          current="13"
          selected={selected}
          onSelect={setSelected}
        />
      ) : null}
      {piece === "Live well" ? (
        <LiveWell
          lines={lines}
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
