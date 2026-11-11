import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
const mocks = vi.hoisted(() => ({
  api: vi.fn(),
  picture: vi.fn(),
  stop: vi.fn(),
  speak: vi.fn(),
}));
vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: mocks.api,
}));
vi.mock("../../../lib/tts", () => ({
  speak: mocks.speak,
  stop: mocks.stop,
  onStateChange: () => () => {},
  enqueueSentence: vi.fn(),
}));
vi.mock("../../feedback/capture", async (original) => ({
  ...(await original<typeof import("../../feedback/capture")>()),
  captureViewportPng: mocks.picture,
}));
vi.mock("../walk", async (original) => ({
  ...(await original<typeof import("../walk")>()),
  waitForDeskReady: vi.fn().mockResolvedValue(true),
  READY_BEAT_MS: 0,
}));
import { WindowIdContext } from "../../components/window/windowIdContext";
import { ListView, SegmentedTabs } from "../../surface";
import { WalkRunner, canGuidePress } from "../WalkRunner";
import { runLocalWalk, type WalkStep } from "../walk";
import {
  bindUiFeedbackLauncher,
  hydrateUiFeedback,
  resetUiFeedbackRuntimeForTests,
} from "../../feedback/runtime";
const steps: WalkStep[] = [
  {
    press: { target: '[data-testid="rows"] .object-list-row' },
    highlight: {
      target: '[data-testid="rows"] .object-list-row',
      words: "Select a decision. Its text shows below.",
    },
  },
  {
    press: { target: '[data-tab="other"]' },
    highlight: { target: '[data-tab="other"]', words: "Choose another tab." },
  },
  {
    highlight: {
      target: "new",
      words: "New decision opens a form in this window.",
    },
  },
];
function Face({ empty = false }: { empty?: boolean }) {
  const [picked, setPicked] = useState<string | null>(null);
  const [tab, setTab] = useState("first");
  return (
    <WindowIdContext.Provider value="surface-decisions">
      <div id="surface-decisions" data-layer="window">
        <SegmentedTabs
          label="Views"
          value={tab}
          onChange={setTab}
          tabs={[
            { id: "first", label: "First" },
            { id: "other", label: "Other" },
          ]}
        >
          <div data-testid="rows">
            <ListView
              label="Decisions"
              rows={
                empty
                  ? []
                  : [{ id: "one", kind: "decision", name: "Adopt tracing" }]
              }
              selectedId={picked}
              onSelect={setPicked}
              onClearSelection={() => setPicked(null)}
            />
          </div>
        </SegmentedTabs>
        <p data-testid="detail">
          {picked ? "Adopt tracing for every service" : "Select a decision"}
        </p>
        <button data-testid="new">New decision</button>
      </div>
      <WalkRunner />
    </WindowIdContext.Provider>
  );
}
const start = (script = steps) =>
  act(() =>
    runLocalWalk({ title: "Decisions", steps: script }, "surface-decisions"),
  );
beforeEach(() => {
  window.history.replaceState({}, "", "/");
  localStorage.setItem("hs:walk-voice", "off");
  mocks.api.mockReset();
  mocks.picture.mockResolvedValue("png");
  resetUiFeedbackRuntimeForTests();
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
describe("Local guide", () => {
  it("selects a real list row, fills its pane, and restores selection and tab on Stop", async () => {
    render(<Face />);
    start();
    await screen.findByText("Select a decision. Its text shows below.");
    expect(screen.getByTestId("detail")).toHaveTextContent(
      "Adopt tracing for every service",
    );
    fireEvent.click(screen.getByTestId("walk-next"));
    await waitFor(() =>
      expect(screen.getByRole("tab", { name: "Other" })).toHaveAttribute(
        "aria-selected",
        "true",
      ),
    );
    await waitFor(() =>
      expect(screen.getByTestId("walk-stop")).not.toBeDisabled(),
    );
    fireEvent.click(screen.getByTestId("walk-stop"));
    expect(screen.queryByTestId("guide-note")).toBeNull();
    expect(screen.getByTestId("detail")).toHaveTextContent("Select a decision");
    expect(screen.getByRole("tab", { name: "First" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(mocks.api).not.toHaveBeenCalled();
  });
  it.each(["Escape", "Done", "owner"])("restores on %s", async (ending) => {
    render(<Face />);
    start([steps[0]]);
    await screen.findByTestId("guide-note");
    await waitFor(() =>
      expect(screen.getByTestId("walk-next")).not.toBeDisabled(),
    );
    if (ending === "Escape") fireEvent.keyDown(document, { key: "Escape" });
    else if (ending === "owner")
      fireEvent.pointerDown(screen.getByTestId("detail"));
    else fireEvent.click(screen.getByRole("button", { name: "Done" }));
    expect(screen.getByTestId("detail")).toHaveTextContent("Select a decision");
    expect(screen.queryByTestId("guide-note")).toBeNull();
  });
  it("refuses to press a verb button", async () => {
    render(<Face />);
    const press = vi.fn();
    screen.getByTestId("new").addEventListener("click", press);
    start([
      {
        press: { target: "new" },
        highlight: { target: "new", words: "A write" },
      },
    ]);
    await screen.findByText("Show me cannot press this control.");
    expect(press).not.toHaveBeenCalled();
    expect(canGuidePress(screen.getByTestId("new"))).toBe(false);
  });
  it("skips an empty list to its first new verb", async () => {
    render(<Face empty />);
    start();
    await screen.findByText("New decision opens a form in this window.");
    expect(
      screen.queryByText("Select a decision. Its text shows below."),
    ).toBeNull();
    expect(mocks.api).not.toHaveBeenCalled();
  });
  it("gives feedback the guide context and stays on that step after Save or Cancel", async () => {
    mocks.api.mockResolvedValue({ enabled: true });
    await hydrateUiFeedback();
    const launch = vi.fn();
    const unbind = bindUiFeedbackLauncher(launch);
    render(<Face />);
    start();
    await screen.findByText("Select a decision. Its text shows below.");
    fireEvent.click(screen.getByRole("button", { name: "Say what is off" }));
    const [target, request] = launch.mock.calls[0];
    expect(target).toHaveAttribute("data-object-id", "one");
    expect(request.guide).toEqual({
      app: "Decisions",
      step: 1,
      of: 3,
      target: '[data-testid="rows"] .object-list-row',
      words: "Select a decision. Its text shows below.",
    });
    expect(screen.queryByTestId("walk-next")).toBeNull();
    act(() => request.onFinish(false));
    expect(screen.getByTestId("walk-count")).toHaveTextContent("1 of 3");
    fireEvent.click(screen.getByRole("button", { name: "Say what is off" }));
    act(() => launch.mock.calls[1][1].onFinish(true));
    expect(screen.getByTestId("walk-count")).toHaveTextContent("Saved.");
    expect(screen.getByTestId("walk-caption")).toHaveTextContent(
      "Select a decision.",
    );
    unbind();
  });
  it("hides feedback when the runtime flag is off", async () => {
    render(<Face />);
    start();
    await screen.findByTestId("guide-note");
    expect(screen.queryByText("Say what is off")).toBeNull();
  });
});
it("a link Walk still posts its answer to the token route", async () => {
  const token = "a".repeat(43);
  window.history.replaceState({}, "", `/?walk=${token}`);
  mocks.api
    .mockResolvedValueOnce({
      title: "Review",
      answers: {},
      steps: [
        {
          highlight: {
            target: "new",
            window: "surface-decisions",
            words: "Review this part.",
          },
          ask: {
            ref: "review",
            question: "Keep this?",
            choices: ["Keep", "Redo"],
          },
        },
      ],
    })
    .mockResolvedValueOnce({ ref: "review", choice: "Keep" });
  render(<Face />);
  await screen.findByRole("button", { name: "Keep" });
  fireEvent.click(screen.getByRole("button", { name: "Keep" }));
  await waitFor(() =>
    expect(mocks.api).toHaveBeenCalledWith(
      `/api/w/${token}/answer`,
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining('"choice":"Keep"'),
      }),
    ),
  );
});

it("restores the host rail posture after its row callback", async () => {
  const { borrowGuideView, useGuideView } = await import("../viewState");
  let returnView!: () => void;
  function RailHost() {
    const [pane, setPane] = useState(false),
      [picked, setPicked] = useState("one");
    useGuideView(
      () => ({ pane, picked }),
      (saved) => {
        setPane(saved.pane);
        setPicked(saved.picked);
      },
      () => setPane(false),
      1,
    );
    return (
      <>
        <span data-testid="posture">{`${picked}:${pane}`}</span>
        <button
          onClick={() => {
            returnView = borrowGuideView("surface-test");
          }}
        >
          Borrow
        </button>
        <RailChild
          picked={picked}
          pick={(id) => {
            setPicked(id);
            setPane(true);
          }}
        />
      </>
    );
  }
  function RailChild({
    picked,
    pick,
  }: {
    picked: string;
    pick(id: string): void;
  }) {
    useGuideView(
      () => picked,
      (saved) => pick(saved),
    );
    return <button onClick={() => pick("two")}>Pick two</button>;
  }
  render(
    <WindowIdContext.Provider value="surface-test">
      <RailHost />
    </WindowIdContext.Provider>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Borrow" }));
  fireEvent.click(screen.getByRole("button", { name: "Pick two" }));
  act(() => returnView());
  expect(screen.getByTestId("posture")).toHaveTextContent("one:false");
});

it("speaks local help through the one speech seam without a server voice", async () => {
  localStorage.setItem("hs:walk-voice", "on");
  render(<Face />);
  start();
  await waitFor(() => expect(mocks.speak).toHaveBeenCalledWith(
    "Select a decision. Its text shows below.", { localOnly: true },
  ));
  expect(mocks.api).not.toHaveBeenCalled();
});

it.each(["Stop", "Escape", "Done"])("discloses folded verbs without pressing an item, and closes on %s", async (end) => {
  const { WorkMenu } = await import("../../components/DeskMenu");
  const write = vi.fn();
  function FoldedFace() {
    const [open, setOpen] = useState(false);
    const [anchor, setAnchor] = useState<HTMLButtonElement | null>(null);
    return <WindowIdContext.Provider value="surface-decisions">
      <div id="surface-decisions" data-layer="window">
        <div data-testid="folded-toolbar" className="object-list-toolbar">
          <span className="object-list-toolbar-strip"><button ref={setAnchor} aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen(!open)}>Actions</button></span>
          {open ? <WorkMenu label="Decision actions" x={0} y={50} opener={anchor} onClose={() => setOpen(false)} entries={[
            {type:"item", id:"decide", label:"Decide", onSelect:write},
            {type:"item", id:"new", label:"New decision", onSelect:write},
          ]} /> : null}
        </div>
      </div><WalkRunner />
    </WindowIdContext.Provider>;
  }
  render(<FoldedFace />);
  start([
    {highlight:{target:'[data-testid="folded-toolbar"] button[aria-label="Decide"]', words:"Decide records the answer."}},
    {highlight:{target:'[data-testid="folded-toolbar"] button[aria-label="New decision"]', words:"New decision opens a form."}},
  ]);
  const item=await screen.findByRole("menuitem", {name:"Decide"});
  expect(item.closest('[data-layer="window"]')).toHaveAttribute("id","surface-decisions");
  expect(canGuidePress(item)).toBe(false);
  expect(canGuidePress(screen.getByRole("button",{name:"Actions"}))).toBe(true);
  await screen.findByTestId("guide-note");
  await waitFor(() => expect(screen.getByTestId("walk-next")).not.toBeDisabled());
  fireEvent.click(screen.getByTestId("walk-next"));
  await screen.findByText("New decision opens a form.");
  await waitFor(() => expect(screen.getByTestId("walk-next")).not.toBeDisabled());
  if(end==="Escape")fireEvent.keyDown(document,{key:"Escape"});
  else fireEvent.click(screen.getByRole("button",{name:end}));
  expect(screen.queryByRole("menu")).toBeNull();
  expect(write).not.toHaveBeenCalled();
});

it.each(["href", "submit"])("refuses a nominally safe disclosure carrying %s", (kind) => {
  const button=document.createElement("button");
  button.className="surface-strip-menu";
  button.setAttribute("aria-haspopup","menu");
  button.setAttribute(kind === "href" ? "href" : "type", kind === "href" ? "/write" : "submit");
  expect(canGuidePress(button)).toBe(false);
});
it("a linked desk.new-drawer step dispatches nothing and keeps its words", async () => {
  const token="b".repeat(43);
  window.history.replaceState({},"",`/?walk=${token}`);
  mocks.api.mockResolvedValueOnce({title:"Review",answers:{},steps:[{
    verb:{verb:"desk.new-drawer"},highlight:{window:"surface-decisions",target:"new",words:"Read this part."},
  }]});
  const registry=await import("../../verbRegistry");
  const verb=registry.verbById("desk.new-drawer")!;
  const run=vi.spyOn(verb,"run").mockImplementation(()=>undefined);
  render(<Face />);
  await screen.findByText("Read this part.");
  await waitFor(()=>expect(screen.getByTestId("walk-next")).not.toBeDisabled());
  expect(run).not.toHaveBeenCalled();
  expect(screen.getByRole("alert")).toHaveTextContent("cannot run that verb");
  run.mockRestore();
});
it.each(["Stop", "replace"])("aborts a guide's feedback capture on %s", async (end) => {
  mocks.api.mockResolvedValue({enabled:true});
  await hydrateUiFeedback();
  let signal:AbortSignal|undefined;
  const off=bindUiFeedbackLauncher((_target,request)=>{signal=request?.signal;});
  render(<Face />);start();
  fireEvent.click(await screen.findByRole("button",{name:"Say what is off"}));
  expect(signal?.aborted).toBe(false);
  if(end === "replace") start();
  else cleanup();
  await waitFor(()=>expect(signal?.aborted).toBe(true));
  off();
});

it("a linked app opener still runs through the existing registry verb", async () => {
  const token="c".repeat(43);
  window.history.replaceState({},"",`/?walk=${token}`);
  mocks.api.mockResolvedValueOnce({title:"Review",answers:{},steps:[{
    verb:{verb:"go.configure-settings"},highlight:{window:"surface-decisions",target:"new",words:"Read this part."},
  }]});
  const registry=await import("../../verbRegistry");
  const run=vi.spyOn(registry.verbById("go.configure-settings")!,"run").mockImplementation(()=>undefined);
  render(<Face />);
  await screen.findByText("Read this part.");
  await waitFor(()=>expect(screen.getByTestId("walk-next")).not.toBeDisabled());
  expect(run).toHaveBeenCalledOnce();
  run.mockRestore();
});
