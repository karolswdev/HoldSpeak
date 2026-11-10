/** Native Speak over recorded hub reads. The transport and capture seams are
 * doubles; the recent ledger is the actual journal answer, never a typed row. */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import JOURNAL from "../../test/wire/dictation-journal.wire.json";
import LOOP from "./fixtures/speak-hub/loop.json";
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
it("has one voice plate, a meaning spine and recent rows; Copy keeps a visible receipt", async () => {
  render(<DictationCore />);
  const recent = await screen.findByTestId("speak-recent");
  expect(recent).toHaveTextContent(JOURNAL.wire.items[0].final_text);
  expect(screen.getByTestId("speak-spine")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Journal" })).toBeNull();
  expect(screen.queryByRole("button", { name: /Speak Utterance/ })).toBeNull();
  fireEvent.click(within(recent).getAllByRole("button", { name: "Copy" })[0]);
  await waitFor(() => expect(screen.getByTestId("speak-footer")).toHaveTextContent("Copied"));
  expect(mocks.copy).toHaveBeenCalledWith(JOURNAL.wire.items[0].final_text);
});
it("a refused clipboard write keeps the words and offers Copy again", async () => {
  mocks.copy.mockRejectedValueOnce(new Error("Clipboard refused"));
  render(<DictationCore />);
  const recent = await screen.findByTestId("speak-recent");
  const copy = within(recent).getAllByRole("button", { name: "Copy" })[0];
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
  fails = false;
  fireEvent.click(retry);
  expect(await screen.findByTestId("speak-recent")).toHaveTextContent(JOURNAL.wire.items[0].final_text);
});
it("the refused hold key has one door to Settings Speak", async () => {
  const read = mocks.apiFetch.getMockImplementation()!;
  mocks.apiFetch.mockImplementation((path: string) => path === "/api/dictation/readiness" ? Promise.resolve(CUSTODY.readiness.all_denied) : read(path));
  render(<DictationCore />);
  fireEvent.click(await screen.findByRole("button", { name: "Fix hold key" }));
  expect(mocks.settings).toHaveBeenCalledWith("configure-settings", "/settings", "speak");
});
