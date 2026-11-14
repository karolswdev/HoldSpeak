/** Speak over recorded hub reads. The transport and capture seams are
 * doubles; the recent ledger is the actual journal answer, never a typed row. */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import JOURNAL from "../../test/wire/dictation-journal.wire.json";
import LOOP from "./fixtures/speak-hub/loop.json";
import DELIVERY from "./fixtures/speak-hub/delivery.json";
import { ApiError } from "../../lib/api";
import POLISH from "./fixtures/speak-hub/polish.json";
import { SYSTEM } from "../systemSprites";
import CUSTODY from "./fixtures/speak-hub/custody.json";
import { rereadHourCycle, wireClock, wireDayClock } from "../surface/format";
import { recordedGet } from "../../test/recordedHub";
const mocks = vi.hoisted(() => ({ apiFetch: vi.fn(), copy: vi.fn(), settings: vi.fn(), compact: false }));
vi.mock("../../lib/api", async (original) => ({ ...await original<typeof import("../../lib/api")>(), apiFetch: mocks.apiFetch }));
vi.mock("../useCompactViewport", () => ({ useCompactViewport: () => mocks.compact }));
vi.mock("../../runtime/RuntimeBus", () => ({ useRuntimeBus: () => ({ state: "connected", subscribe: () => () => undefined }), useOptionalRuntimeBus: () => null }));
vi.mock("../../lib/micSession", () => ({ subscribeMicPhase: () => () => undefined, micCaptureSupported: () => true, micCaptureReason: () => null }));
vi.mock("../../lib/openMic", () => ({ openMicDrop: vi.fn(), openMicListen: vi.fn() }));
vi.mock("../../lib/speakToFill", () => ({ speakToFillSupported: () => true, speakToFillUnsupportedReason: () => "", subscribeCaptureLevel: () => () => undefined }));
vi.mock("../shell", async (original) => ({ ...await original<typeof import("../shell")>(), openSurfaceOr: mocks.settings }));
import { DictationCore } from "../../pages/cores/DictationCore";
beforeEach(() => {
  localStorage.clear();
  mocks.compact = false;
  vi.clearAllMocks();
  mocks.copy.mockResolvedValue(undefined);
  Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: mocks.copy } });
  mocks.apiFetch.mockImplementation(async (path: string) => path.startsWith("/api/dictation/journal") ? JOURNAL.wire : recordedGet(LOOP.boot, path) ?? {});
});
it("selects recent words before a verb runs and opens them whole in the inspector", async () => {
  render(<DictationCore />);
  const recent = await screen.findByRole("grid", {name:"Recent dictations"});
  expect(recent).toHaveTextContent(JOURNAL.wire.items[0].final_text);
  expect(screen.getByRole("log", {name:"Dictated words"})).toBeInTheDocument();
  expect(screen.queryByText("Your voice")).toBeNull();
  expect(within(screen.getByRole("toolbar",{name:"Speak"})).getByRole("button", {name:"Copy"})).toBeDisabled();
  expect(screen.queryByRole("button", { name: "Journal" })).toBeNull();
  expect(screen.queryByRole("button", { name: /Speak Utterance/ })).toBeNull();
  const row = within(recent).getByText(JOURNAL.wire.items[0].final_text).closest("[data-object-id]")!;
  expect(row.querySelector("button")).toBeNull();
  fireEvent.click(row);
  fireEvent.click(screen.getByRole("button", {name:"Open"}));
  expect(screen.getByTestId("speak-inspector")).toHaveTextContent(JOURNAL.wire.items[0].final_text);
  expect(screen.getByTestId("speak-inspector").closest('[data-feedback-redact="true"]')).not.toBeNull();
  fireEvent.click(within(screen.getByRole("toolbar",{name:"Speak"})).getByRole("button", {name:"Copy"}));
  await waitFor(() => expect(screen.getByTestId("speak-footer")).toHaveTextContent("Copied"));
  expect(mocks.copy).toHaveBeenCalledWith(JOURNAL.wire.items[0].final_text);
});
it("a refused clipboard write keeps the words and offers Copy again", async () => {
  mocks.copy.mockRejectedValueOnce(new Error("Clipboard refused"));
  render(<DictationCore />);
  const recent = await screen.findByRole("grid", {name:"Recent dictations"});
  fireEvent.click(within(recent).getByText(JOURNAL.wire.items[0].final_text).closest("[data-object-id]")!);
  const copy = within(screen.getByRole("toolbar",{name:"Speak"})).getByRole("button", {name:"Copy"});
  fireEvent.click(copy);
  await waitFor(() => expect(screen.getByTestId("speak-footer")).toHaveTextContent("Not copied"));
  expect(recent).toHaveTextContent(JOURNAL.wire.items[0].final_text);
  fireEvent.click(copy);
  await waitFor(() => expect(screen.getByTestId("speak-footer")).toHaveTextContent("Copied"));
});
it("a failed recent read has Retry; its recorded answer lands after the press", async () => {
  const read = mocks.apiFetch.getMockImplementation()!;
  let fails = true;
  mocks.apiFetch.mockImplementation((path: string) => path.startsWith("/api/dictation/journal") && fails ? Promise.reject(new TypeError("Offline")) : read(path));
  render(<DictationCore />);
  const retry = await screen.findByRole("button", { name: "Try again" });
  expect(screen.getByTestId("speak-face")).toHaveTextContent("Hub unreachable · Nothing changed");
  expect(screen.getByTestId("speak-footer")).not.toHaveTextContent("Recent dictations not read");
  expect(screen.queryByText("No recent dictations")).toBeNull();
  fails = false;
  fireEvent.click(retry);
  await waitFor(()=>expect(screen.getByRole("grid", {name:"Recent dictations"})).toHaveTextContent(JOURNAL.wire.items[0].final_text));
});
it("the refused hold key has one door to Settings Speak", async () => {
  const read = mocks.apiFetch.getMockImplementation()!;
  mocks.apiFetch.mockImplementation((path: string) => path === "/api/dictation/readiness" ? Promise.resolve(CUSTODY.readiness.all_denied) : read(path));
  render(<DictationCore />);
  fireEvent.click(await screen.findByRole("button", { name: "Fix hold key" }));
  expect(screen.getByTestId("speak-hotkey")).toHaveTextContent("Microphone refused");
  expect(mocks.settings).toHaveBeenCalledWith("configure-settings", "/settings", "speak");
});

it("Type is live with no selection and keeps its words after a delivery refusal", async () => {
  const read = mocks.apiFetch.getMockImplementation()!;
  mocks.apiFetch.mockImplementation((path: string, init: unknown) => path === "/api/dictation/remote" ? Promise.reject(new TypeError("Offline")) : read(path,init));
  render(<DictationCore />);
  fireEvent.click(screen.getByRole("button",{name:"Actions"}));
  fireEvent.click(screen.getByRole("menuitem",{name:"Type"}));
  fireEvent.change(screen.getByLabelText("Dictation"),{target:{value:"Keep the rollback plan"}});
  fireEvent.click(screen.getByRole("button",{name:"Put words back"}));
  await screen.findByRole("button",{name:"Retry"});
  expect(screen.getByLabelText("Dictation")).toHaveValue("Keep the rollback plan");
  fireEvent.click(screen.getByRole("button",{name:"Copy words"}));
  await waitFor(()=>expect(mocks.copy).toHaveBeenCalledWith("Keep the rollback plan"));
});
it("the To choice changes the destination before the next act", async () => {
  render(<DictationCore />);
  fireEvent.change(screen.getByLabelText("To"), {target:{value:"agent"}});
  expect(screen.getByTestId("speak-types-into")).toHaveTextContent("To the agent");
  expect(localStorage.getItem("holdspeak.speakAim")).toBe("agent");
});

it("Put back uses the selected words and shows the recorded delivery result", async () => {
  const read = mocks.apiFetch.getMockImplementation()!;
  mocks.apiFetch.mockImplementation((path: string, init: unknown) => path === "/api/dictation/remote" ? Promise.resolve(DELIVERY.selected) : read(path,init));
  render(<DictationCore />);
  const recent = await screen.findByRole("grid",{name:"Recent dictations"});
  await waitFor(()=>expect(recent).toHaveTextContent(JOURNAL.wire.items[0].final_text));
  fireEvent.click(within(recent).getByText(JOURNAL.wire.items[0].final_text).closest("[data-object-id]")!);
  fireEvent.click(within(screen.getByRole("toolbar",{name:"Speak"})).getByRole("button",{name:"Put back"}));
  await waitFor(()=>expect(screen.getByRole("log",{name:"Dictated words"})).toHaveTextContent(DELIVERY.selected.final_text));
  const call = mocks.apiFetch.mock.calls.find(call=>call[0]==="/api/dictation/remote")!;
  expect(call[1].json.text).toBe(JOURNAL.wire.items[0].final_text);
  expect(call[1].json.target_mode).toBe("focused");
  expect(screen.getByTestId("speak-phase")).toHaveTextContent("Done");
});
it("a recorded delivery refusal retains input; Retry shows the acknowledged words", async () => {
  const read = mocks.apiFetch.getMockImplementation()!;
  let refused = true;
  mocks.apiFetch.mockImplementation((path: string, init: unknown) => path === "/api/dictation/remote" ? refused ? Promise.reject(new ApiError(422,"Refused",DELIVERY.refused)) : Promise.resolve(DELIVERY.landed) : read(path,init));
  render(<DictationCore />);
  fireEvent.click(screen.getByRole("button",{name:"Actions"}));
  fireEvent.click(screen.getByRole("menuitem",{name:"Type"}));
  fireEvent.change(screen.getByLabelText("Dictation"),{target:{value:"Keep the rollback plan"}});
  fireEvent.click(screen.getByRole("button",{name:"Put words back"}));
  const retry = await screen.findByRole("button",{name:"Retry"});
  expect(screen.getByLabelText("Dictation")).toHaveValue("Keep the rollback plan");
  refused = false;
  fireEvent.click(retry);
  await waitFor(()=>expect(screen.getByRole("log",{name:"Sent words"})).toHaveTextContent(DELIVERY.landed.final_text));
  fireEvent.click(screen.getByRole("button",{name:"Cancel"}));
  fireEvent.click(screen.getByRole("button",{name:"Actions"}));
  fireEvent.click(screen.getByRole("menuitem",{name:"Type"}));
  expect(screen.getByLabelText("Dictation")).toHaveValue("Keep the rollback plan");
});

it("Return opens the focused dictation before any selection", async () => {
  render(<DictationCore />);
  const recent = await screen.findByRole("grid",{name:"Recent dictations"});
  await waitFor(()=>expect(recent).toHaveTextContent(JOURNAL.wire.items[0].final_text));
  const row = within(recent).getByText(JOURNAL.wire.items[0].final_text).closest("[data-object-id]")!;
  fireEvent.keyDown(row,{key:"Enter"});
  expect(row).toHaveAttribute("aria-selected","true");
  expect(screen.getByTestId("speak-inspector")).toHaveTextContent(JOURNAL.wire.items[0].final_text);
  expect(screen.getByTestId("speak-inspector").closest('[data-feedback-redact="true"]')).not.toBeNull();
  expect(mocks.apiFetch.mock.calls.some(call=>call[0]==="/api/dictation/remote")).toBe(false);
});

it("keeps Talk live and selected-row verbs dead; Type and Settings are in Actions", async () => {
  render(<DictationCore />);
  await screen.findByRole("grid",{name:"Recent dictations"});
  const bar=within(screen.getByRole("toolbar",{name:"Speak"}));
  expect(bar.getByRole("button",{name:"Talk"})).toBeEnabled();
  for(const name of ["Open","Copy","Put back"]) expect(bar.getByRole("button",{name})).toBeDisabled();
  expect(bar.queryByRole("button",{name:"Type"})).toBeNull();
  expect(bar.queryByRole("button",{name:"Settings"})).toBeNull();
  expect(bar.getByText("To:")).toBeInTheDocument();
  fireEvent.click(bar.getByRole("button",{name:"Actions"}));
  expect(screen.getByRole("menuitem",{name:"Type"})).toBeEnabled();
  expect(screen.getByRole("menuitem",{name:"Settings"})).toBeEnabled();
});
it.each([
  ["all_denied","Microphone refused"],
  ["one_denied","Input Monitoring refused"],
  ["never_asked","Microphone not asked"],
  ["listener_failed","Hold key listener did not start"],
] as const)("names the missing hold-key step: %s",async (state,reason)=>{
  const read=mocks.apiFetch.getMockImplementation()!;
  mocks.apiFetch.mockImplementation((path:string)=>path==="/api/dictation/readiness"?Promise.resolve(CUSTODY.readiness[state]):read(path));
  render(<DictationCore />);
  const notice=await screen.findByTestId("speak-hotkey");
  expect(notice).toHaveTextContent(reason);
  expect(within(notice).getByRole("img",{name:reason})).toHaveAttribute("data-state","waiting");
  expect(within(notice).getByRole("button",{name:"Fix hold key"})).toBeEnabled();
});

it("Retry keeps the selected delivery words and leaves a different typed draft intact",async()=>{
  const read=mocks.apiFetch.getMockImplementation()!;
  let refused=true;
  mocks.apiFetch.mockImplementation((path:string,init:unknown)=>path==="/api/dictation/remote" ? refused ? Promise.reject(new ApiError(422,"Refused",DELIVERY.refused)) : Promise.resolve(DELIVERY.selected) : read(path,init));
  render(<DictationCore />);
  fireEvent.click(screen.getByRole("button",{name:"Actions"}));
  fireEvent.click(screen.getByRole("menuitem",{name:"Type"}));
  fireEvent.change(screen.getByLabelText("Dictation"),{target:{value:"Keep this different draft"}});
  fireEvent.click(screen.getByRole("button",{name:"Cancel"}));
  const grid=await screen.findByRole("grid",{name:"Recent dictations"});
  fireEvent.click(within(grid).getByText(JOURNAL.wire.items[0].final_text).closest("[data-object-id]")!);
  fireEvent.click(within(screen.getByRole("toolbar",{name:"Speak"})).getByRole("button",{name:"Put back"}));
  const retry=await screen.findByRole("button",{name:"Retry"});
  expect(screen.getByRole("log",{name:"Dictated words"})).toHaveTextContent(JOURNAL.wire.items[0].final_text);
  refused=false;
  fireEvent.click(retry);
  await waitFor(()=>expect(screen.getByTestId("speak-phase")).toHaveTextContent("Done"));
  const sends=mocks.apiFetch.mock.calls.filter(call=>call[0]==="/api/dictation/remote");
  expect(sends.map(call=>call[1].json.text)).toEqual([JOURNAL.wire.items[0].final_text,JOURNAL.wire.items[0].final_text]);
  fireEvent.click(screen.getByRole("button",{name:"Actions"}));
  fireEvent.click(screen.getByRole("menuitem",{name:"Type"}));
  expect(screen.getByLabelText("Dictation")).toHaveValue("Keep this different draft");
});

const RealDateTimeFormat = Intl.DateTimeFormat;
afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
  rereadHourCycle();
});
it.each(["en-US", "en-GB"])("recent and selected times use the system clock (%s)", async locale => {
  vi.spyOn(Intl, "DateTimeFormat").mockImplementation(function (asked, options) {
    return new RealDateTimeFormat(asked ?? locale, options);
  } as typeof Intl.DateTimeFormat);
  rereadHourCycle();
  vi.useFakeTimers({now: new Date(JOURNAL.wire.items[0].created_at), toFake: ["Date"]});
  render(<DictationCore />);
  const grid = await screen.findByRole("grid", {name:"Recent dictations"});
  const stored = JOURNAL.wire.items[0];
  const row = within(grid).getByText(stored.final_text).closest("[data-object-id]")!;
  const clock = wireClock(stored.created_at, true);
  expect(row.querySelector('[data-col="when"]')).toHaveTextContent(clock);
  fireEvent.doubleClick(row);
  expect(screen.getByTestId("speak-inspector")).toHaveTextContent(`Dictation · ${clock}`);
});

function polishRead() {
  const read = mocks.apiFetch.getMockImplementation()!;
  mocks.apiFetch.mockImplementation((path: string) => path.startsWith("/api/dictation/journal") ? Promise.resolve(POLISH.wire) : read(path));
  vi.useFakeTimers({now: new Date(POLISH.now), toFake: ["Date"]});
}
it("dictations keep the Speak object even when their words start with a path", async () => {
  polishRead();
  render(<DictationCore />);
  const grid = await screen.findByRole("grid", {name:"Recent dictations"});
  const row = within(grid).getByText(POLISH.wire.items[0].final_text).closest("[data-object-id]")!;
  expect(row.querySelector("img")).toBeNull();
  fireEvent.doubleClick(row);
  expect(screen.getByTestId("speak-inspector").querySelector(".surface-inspector-object img")).toHaveAttribute("src", SYSTEM.dockSpeak);
});
it("a compact selection gives the facts the capture well's unused space", async () => {
  polishRead();
  mocks.compact = true;
  render(<DictationCore />);
  const grid = await screen.findByRole("grid", {name:"Recent dictations"});
  fireEvent.click(within(grid).getByText(POLISH.wire.items[0].final_text).closest("[data-object-id]")!);
  expect(screen.getByTestId("speak-live")).toHaveAttribute("data-compact", "true");
  expect(screen.getByTestId("speak-live")).toHaveTextContent("Hold Talk, then speak");
  expect(screen.queryByTestId("live-level")).toBeNull();
  const inspector = screen.getByTestId("speak-inspector");
  for (const label of ["Words", "Length", "Speech now"]) expect(within(inspector).getByText(label, {exact:true})).toBeVisible();
  const read = mocks.apiFetch.getMockImplementation()!;
  let finish!: (value: unknown) => void;
  mocks.apiFetch.mockImplementation((path: string) => path === "/api/dictation/remote" ? new Promise(resolve => {finish = resolve;}) : read(path));
  fireEvent.click(screen.getByRole("button", {name:"Actions"}));
  fireEvent.click(screen.getByRole("menuitem", {name:"Type"}));
  fireEvent.change(screen.getByLabelText("Dictation"), {target:{value:"Keep the rollback plan"}});
  fireEvent.click(screen.getByRole("button", {name:"Put words back"}));
  expect(screen.getByTestId("speak-live")).toHaveAttribute("data-compact", "true");
  finish(DELIVERY.landed);
  await waitFor(() => expect(screen.getByTestId("speak-phase")).toHaveTextContent("Done"));
});
it("At uses minutes for a lone minute, seconds for a shared minute, and dates before today", async () => {
  polishRead();
  render(<DictationCore />);
  const grid = await screen.findByRole("grid", {name:"Recent dictations"});
  for (const [index, seconds] of [[0, true], [1, true], [2, false], [3, false]] as const) {
    const stored = POLISH.wire.items[index];
    const row = within(grid).getByText(stored.final_text).closest("[data-object-id]")!;
    const expected = index === 3 ? wireDayClock(stored.created_at).split(",")[0] : wireClock(stored.created_at, seconds);
    expect(row.querySelector('[data-col="when"]')?.textContent).toBe(expected);
  }
});
it("does not declare To when the journal has no known targets", async () => {
  polishRead();
  render(<DictationCore />);
  const grid = await screen.findByRole("grid", {name:"Recent dictations"});
  expect(within(grid).queryByRole("columnheader", {name:"To"})).toBeNull();
});
