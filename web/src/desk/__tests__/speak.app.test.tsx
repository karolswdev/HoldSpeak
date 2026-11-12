/** Speak over recorded hub reads. The transport and capture seams are
 * doubles; the recent ledger is the actual journal answer, never a typed row. */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import JOURNAL from "../../test/wire/dictation-journal.wire.json";
import LOOP from "./fixtures/speak-hub/loop.json";
import DELIVERY from "./fixtures/speak-hub/delivery.json";
import { ApiError } from "../../lib/api";
import CUSTODY from "./fixtures/speak-hub/custody.json";
import { recordedGet } from "../../test/recordedHub";
const mocks = vi.hoisted(() => ({ apiFetch: vi.fn(), copy: vi.fn(), settings: vi.fn() }));
vi.mock("../../lib/api", async (original) => ({ ...await original<typeof import("../../lib/api")>(), apiFetch: mocks.apiFetch }));
vi.mock("../../runtime/RuntimeBus", () => ({ useRuntimeBus: () => ({ state: "connected", subscribe: () => () => undefined }), useOptionalRuntimeBus: () => null }));
vi.mock("../../lib/micSession", () => ({ subscribeMicPhase: () => () => undefined, micCaptureSupported: () => true, micCaptureReason: () => null }));
vi.mock("../../lib/openMic", () => ({ openMicDrop: vi.fn(), openMicListen: vi.fn() }));
vi.mock("../../lib/speakToFill", () => ({ speakToFillSupported: () => true, speakToFillUnsupportedReason: () => "", subscribeCaptureLevel: () => () => undefined }));
vi.mock("../shell", async (original) => ({ ...await original<typeof import("../shell")>(), openSurfaceOr: mocks.settings }));
import { DictationCore } from "../../pages/cores/DictationCore";
beforeEach(() => {
  localStorage.clear();
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
  const retry = await screen.findByRole("button", { name: "Retry" });
  expect(screen.getByTestId("speak-footer")).toHaveTextContent("Recent words not read");
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
  expect(within(screen.getByTestId("speak-hotkey")).getByRole("img",{name:"Permission refused"})).toHaveAttribute("data-state","waiting");
  expect(mocks.settings).toHaveBeenCalledWith("configure-settings", "/settings", "speak");
});

it("Type is live with no selection and keeps its words after a delivery refusal", async () => {
  const read = mocks.apiFetch.getMockImplementation()!;
  mocks.apiFetch.mockImplementation((path: string, init: unknown) => path === "/api/dictation/remote" ? Promise.reject(new TypeError("Offline")) : read(path,init));
  render(<DictationCore />);
  fireEvent.click(screen.getByRole("button",{name:"Type"}));
  fireEvent.change(screen.getByLabelText("Utterance"),{target:{value:"Keep the rollback plan"}});
  fireEvent.click(screen.getByRole("button",{name:"Put words back"}));
  await screen.findByRole("button",{name:"Retry"});
  expect(screen.getByLabelText("Utterance")).toHaveValue("Keep the rollback plan");
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
  fireEvent.click(screen.getByRole("button",{name:"Type"}));
  fireEvent.change(screen.getByLabelText("Utterance"),{target:{value:"Keep the rollback plan"}});
  fireEvent.click(screen.getByRole("button",{name:"Put words back"}));
  const retry = await screen.findByRole("button",{name:"Retry"});
  expect(screen.getByLabelText("Utterance")).toHaveValue("Keep the rollback plan");
  refused = false;
  fireEvent.click(retry);
  await waitFor(()=>expect(screen.getByRole("log",{name:"Sent words"})).toHaveTextContent(DELIVERY.landed.final_text));
  fireEvent.click(screen.getByRole("button",{name:"Cancel"}));
  fireEvent.click(screen.getByRole("button",{name:"Type"}));
  expect(screen.getByLabelText("Utterance")).toHaveValue("Keep the rollback plan");
});

it("Return opens the focused dictation before any selection", async () => {
  render(<DictationCore />);
  const recent = await screen.findByRole("grid",{name:"Recent dictations"});
  await waitFor(()=>expect(recent).toHaveTextContent(JOURNAL.wire.items[0].final_text));
  const row = within(recent).getByText(JOURNAL.wire.items[0].final_text).closest("[data-object-id]")!;
  fireEvent.keyDown(row,{key:"Enter"});
  expect(row).toHaveAttribute("aria-selected","true");
  expect(screen.getByTestId("speak-inspector")).toHaveTextContent(JOURNAL.wire.items[0].final_text);
  expect(mocks.apiFetch.mock.calls.some(call=>call[0]==="/api/dictation/remote")).toBe(false);
});
