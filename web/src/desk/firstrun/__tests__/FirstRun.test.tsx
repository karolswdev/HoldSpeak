/* First run C1 "Heard first" — the face states, with the hub faked.
 *
 * before -> running (First words opens only when the speech model is on
 * the device) -> name saved -> listening -> heard (his words, Play from the
 * browser's own capture) -> Keep as note (a real POST /api/notes). */
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { planSteps, speechReady, type LocalAiStatus } from "../localAi";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  refresh: vi.fn(),
  start: vi.fn(),
  retry: vi.fn(),
  closeMic: vi.fn(),
}));

vi.mock("../../../lib/api", async (importOriginal) => ({
  ApiError: (await importOriginal<typeof import("../../../lib/api")>()).ApiError,
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) => (error instanceof Error ? error.message : "Request failed"),
}));
vi.mock("../../store", () => ({
  useDesk: Object.assign(() => undefined, { getState: () => ({ refresh: mocks.refresh }) }),
}));
vi.mock("../../shell", () => ({ openSurfaceOr: vi.fn() }));
vi.mock("../../../lib/speakToFill", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/speakToFill")>()),
  retryPendingTranscription: mocks.retry,
}));
vi.mock("../../../lib/micSession", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/micSession")>()),
  closeMicSession: mocks.closeMic,
}));
vi.mock("../../../lib/micStreamSession", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/micStreamSession")>()),
  micStreamSupported: () => true,
  startStreamSession: mocks.start,
  subscribeCaptureLevel: () => () => undefined,
}));

import { FirstRun } from "../FirstRun";

const MB = 1_000_000;
function status(over: Partial<LocalAiStatus> & { landed?: boolean; all?: boolean } = {}): LocalAiStatus {
  // The shape of #856's GET /api/setup/local-ai (merged, main fd3272147).
  const { landed = false, all = false, ...rest } = over;
  const speech = landed || all;
  return {
    state: "not_started",
    files: [
      { key: "whisper", label: "whisper-base", size_bytes: 142 * MB, on_device: speech || all, url: "https://huggingface.co/a" },
      { key: "embed", label: "nomic-embed-text v1.5", size_bytes: 146 * MB, on_device: speech || all },
      { key: "starter", label: "Qwen3.5 4B", size_bytes: 2741 * MB, on_device: all },
    ],
    bytes_total: 0,
    bytes_done: 0,
    egress: { destination: "huggingface.co" },
    speech: { model: "base", backend: "mlx", state: speech ? "on_device" : "will_download" },
    local_engine: { ready: all },
    error: "",
    ...rest,
  };
}

let local: LocalAiStatus;
const calls: { path: string; method: string; json?: unknown }[] = [];

beforeEach(() => {
  vi.useRealTimers();
  calls.length = 0;
  local = status();
  mocks.refresh.mockReset().mockResolvedValue(undefined);
  mocks.retry.mockReset().mockResolvedValue(null);
  mocks.start.mockReset();
  mocks.closeMic.mockReset();
  mocks.apiFetch.mockReset().mockImplementation(async (path: string, init: { method?: string; json?: unknown } = {}) => {
    const method = init.method ?? "GET";
    calls.push({ path, method, json: init.json });
    if (path === "/api/setup/local-ai") {
      if (method === "POST") local = status({ state: "downloading", bytes_total: 3029 * MB, bytes_done: 40 * MB });
      return local;
    }
    if (path === "/api/settings" && method === "GET") return { owner: { name: "", aliases: [] } };
    if (path === "/api/settings") return { settings: { owner: init.json && (init.json as { owner: unknown }).owner } };
    if (path === "/api/notes") return { note: { id: "note_1" } };
    if (path === "/api/onboarding/calendar") return { macos: { state: "unavailable", can_request: false }, candidates: [], sources: 0 };
    if (path === "/api/onboarding/connections") return { candidates: [], tools: { gh: { installed: false }, acli: { installed: false } } };
    return {};
  });
});

describe("planSteps / speechReady", () => {
  it("lights speech only when every whisper file is on the device", () => {
    expect(speechReady(status())).toBe(false);
    expect(speechReady(status({ landed: true }))).toBe(true);
    expect(speechReady(null)).toBe(false);
    // The owner's own Whisper copy: no Whisper rows, speech is here.
    expect(speechReady({ ...status(), files: [], speech: { model: "small", backend: "mlx", state: "on_device_unpinned" } })).toBe(true);
    expect(speechReady({ ...status(), files: [], speech: { model: "large", backend: "mlx", state: "not_covered" } })).toBe(false);
  });

  it("puts the bytes of this run on the file in progress", () => {
    const steps = planSteps(
      status({ state: "downloading", landed: true, bytes_total: 3029 * MB, bytes_done: 288 * MB + 1100 * MB }),
      "46 MB/s",
    );
    expect(steps.map((s) => s.status)).toEqual(["done", "done", "running"]);
    expect(steps[2].rate).toBe("1.1 / 2.7 GB · 46 MB/s");
    expect(steps[2].progress).toBeCloseTo(1100 / 2741, 3);
  });
});

describe("FirstRun", () => {
  it("walks before -> running -> speech lands -> heard -> kept", async () => {
    const audio = new ArrayBuffer(44 + 32000 * 4);
    mocks.start.mockResolvedValue({
      stop: vi.fn().mockResolvedValue("Send the cutover plan to Priya before Friday."),
      cancel: vi.fn(),
      retained: vi.fn().mockResolvedValue(false),
      audio: () => audio,
    });
    render(<FirstRun />);

    // before: the one press with its size; First words waits for speech.
    const press = await screen.findByRole("button", { name: "Set up local AI · 3.0 GB" });
    expect(screen.getByText("HUGGINGFACE.CO")).toBeTruthy();
    expect(screen.getByRole("status", { name: "WAITS FOR SPEECH" })).toBeTruthy();
    expect((screen.getByRole("button", { name: "Dictate one sentence" }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByRole("heading", { name: "Get ready" }).className).toContain("surface-display");

    // running: speech not on the device yet -> still shut.
    fireEvent.click(press);
    await screen.findByRole("group", { name: "Local AI download" });
    expect(screen.queryByRole("button", { name: "◖ Dictate one sentence" })).toBeNull();

    // the speech model lands (the next poll).
    local = status({ state: "downloading", landed: true, bytes_total: 3029 * MB, bytes_done: 1400 * MB });
    const dictate = await screen.findByRole("button", { name: "◖ Dictate one sentence" }, { timeout: 3000 });
    expect(screen.getByTestId("firstrun-first-words").getAttribute("data-lit")).toBe("true");

    // You: the name is saved through the settings API.
    fireEvent.change(screen.getByRole("textbox", { name: "Your name" }), { target: { value: "Karol Sane" } });
    const alias = screen.getByRole("textbox", { name: "Also called" });
    fireEvent.change(alias, { target: { value: "Karol, KS" } });
    await waitFor(
      () => expect(calls.some((c) => c.path === "/api/settings" && c.method === "PUT")).toBe(true),
      { timeout: 2000 },
    );
    const put = calls.filter((c) => c.path === "/api/settings" && c.method === "PUT").pop();
    expect(put?.json).toEqual({ owner: { name: "Karol Sane", aliases: ["Karol", "KS"] } });
    await screen.findByRole("status", { name: "SET" });

    // listening -> heard.
    fireEvent.click(dictate);
    const stop = await screen.findByRole("button", { name: "Stop listening" });
    expect(screen.getByRole("status", { name: "LISTENING" })).toBeTruthy();
    await act(async () => {
      fireEvent.click(stop);
    });
    const quote = await screen.findByTestId("heard-quote");
    expect(quote.querySelector("blockquote")?.textContent).toBe(
      "“Send the cutover plan to Priya before Friday.”",
    );
    expect(quote.textContent).toContain("8 WORDS · 0:04");
    // One display element: the heading steps down once his words are back.
    expect(screen.getByRole("heading", { name: "Heard" }).className).not.toContain("surface-display");
    expect(screen.getByRole("button", { name: "▶ Play" })).toBeTruthy();

    // Keep as note: the note producer; option A keeps the one screen open
    // (Calendar and Connections are next), so no handoff yet.
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Keep as note" }));
    });
    const note = calls.find((c) => c.path === "/api/notes");
    expect(note?.method).toBe("POST");
    expect(note?.json).toMatchObject({ title: "First dictation", body_markdown: "Send the cutover plan to Priya before Friday." });
    await screen.findByRole("heading", { name: "Get ready" });
    // The card head and the quote both say HEARD (artboard onb-A-cal).
    expect(screen.getAllByRole("status", { name: "HEARD" })).toHaveLength(2);
    expect(screen.queryByRole("button", { name: "Keep as note" })).toBeNull();
    expect(calls.some((c) => c.path === "/api/setup/onboarding")).toBe(false);
    expect(mocks.refresh).not.toHaveBeenCalled();
  }, 15_000); // a long walk on real-timer polls: 2.5 s alone, more under the full suite

  it("withholds Play when the browser kept no audio of the take", async () => {
    local = status({ all: true, state: "ready" });
    mocks.start.mockResolvedValue({
      stop: vi.fn().mockResolvedValue("Hello there."),
      cancel: vi.fn(),
      retained: vi.fn().mockResolvedValue(false),
      audio: () => null,
    });
    render(<FirstRun />);
    fireEvent.click(await screen.findByRole("button", { name: "◖ Dictate one sentence" }));
    const stop = await screen.findByRole("button", { name: "Stop listening" });
    await act(async () => {
      fireEvent.click(stop);
    });
    await screen.findByTestId("heard-quote");
    expect(screen.queryByRole("button", { name: "▶ Play" })).toBeNull();
    expect(screen.getByRole("button", { name: "Again" })).toBeTruthy();
  });

  it("opens First words when the setup read fails (the dictation path names its own failure)", async () => {
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path === "/api/setup/local-ai") throw new Error("Not Found");
      return { owner: { name: "", aliases: [] } };
    });
    render(<FirstRun />);
    expect(await screen.findByRole("status", { name: "CAN'T CHECK" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "◖ Dictate one sentence" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Continue later" })).toBeTruthy();
  });

  it("names a speech model setup cannot get, with no dead Try again", async () => {
    local = {
      ...status({ state: "incomplete" }),
      files: status().files.filter((f) => f.key !== "whisper").map((f) => ({ ...f, on_device: true })),
      speech: { model: "large-v3", backend: "mlx", state: "not_covered" },
      error: "Set up local AI cannot get the selected Whisper model. Select the base model, or add the model yourself.",
    };
    render(<FirstRun />);
    expect(await screen.findByRole("status", { name: "NO SPEECH MODEL" })).toBeTruthy();
    expect(screen.getByText(/cannot get the selected Whisper model/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
    expect(screen.getByRole("status", { name: "WAITS FOR SPEECH" })).toBeTruthy();
  });

  it("stops a microphone grant that lands after Continue later (Astra #859 P1)", async () => {
    local = status({ all: true, state: "ready" });
    let grant: (session: unknown) => void = () => undefined;
    mocks.start.mockReturnValue(new Promise((resolve) => { grant = resolve; }));
    const cancel = vi.fn();
    render(<FirstRun />);
    fireEvent.click(await screen.findByRole("button", { name: "◖ Dictate one sentence" }));
    // Permission is pending (the acquisition has started): the owner leaves.
    await waitFor(() => expect(mocks.start).toHaveBeenCalled());
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Continue later" }));
    });
    await waitFor(() =>
      expect(calls.some((c) => c.path === "/api/setup/onboarding")).toBe(true),
    );
    // Then the grant lands.
    await act(async () => {
      grant({ stop: vi.fn(), cancel, retained: vi.fn().mockResolvedValue(false), audio: () => null });
    });
    expect(cancel).toHaveBeenCalledTimes(1);
    expect(mocks.closeMic).toHaveBeenCalled();
    expect(screen.queryByRole("button", { name: "Stop listening" })).toBeNull();
    expect(screen.queryByRole("status", { name: "LISTENING" })).toBeNull();
  });

  it("says a blocked mic as tokens with the verbs that work, no paragraph (Astra #859 P2)", async () => {
    local = status({ all: true, state: "ready" });
    mocks.start.mockRejectedValue(new DOMException("Permission denied", "NotAllowedError"));
    render(<FirstRun />);
    fireEvent.click(await screen.findByRole("button", { name: "◖ Dictate one sentence" }));
    const failure = await screen.findByTestId("firstrun-take-failure");
    expect(screen.getByRole("status", { name: "MIC BLOCKED" })).toBeTruthy();
    expect(failure.textContent).toContain("ALLOW IN BROWSER");
    expect(document.body.textContent).not.toMatch(/draft remains editable/i);
    expect(failure.querySelector(".firstrun-reason")).toBeNull();
    expect(screen.getByRole("button", { name: "Again" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Continue later" })).toBeTruthy();
  });
});

// PHILO-15 10 (B09): the Local AI card's second choice — the model server
// he runs on his network, with no chat download. It is the Concierge's own
// add-engine row. Astra r1 (finding 2): with no Whisper on this device the
// card keeps the speech download beside it, and the press also sets the
// Default for AI work.
describe("FirstRun — Use a server on my network", () => {
  function lanFakes(speechOnDevice: boolean) {
    local = status({ landed: speechOnDevice });
    const base = mocks.apiFetch.getMockImplementation()!;
    mocks.apiFetch.mockImplementation(async (path: string, init: { method?: string; json?: unknown } = {}) => {
      if (path === "/api/setup/discover-models") {
        calls.push({ path, method: "POST", json: init.json });
        return { ok: true, models: ["qwen3.8-27b"], detail: "Found 1 model.", tools: "yes" };
      }
      if (path === "/api/inference/model-library/define-endpoint") {
        return { provider: { profile_id: "engine-192-168-1-43-8080", profile_revision: 1 } };
      }
      if (path === "/api/concierge/summary-selection") {
        calls.push({ path, method: "POST", json: init.json });
        return { status: "succeeded", result: { state: "READY" }, summaryAssignment: null, defaultSet: true };
      }
      return base(path, init);
    });
  }

  async function useTheBox(opened = false) {
    if (!opened) fireEvent.click(screen.getByTestId("firstrun-lan-verb"));
    const address = await screen.findByLabelText("Server address");
    fireEvent.change(address, { target: { value: "http://192.168.1.43:8080/v1" } });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    expect((await screen.findByTestId("concierge-add-tools")).textContent).toBe("TOOLS");
    fireEvent.click(screen.getByTestId("concierge-add-submit"));
    return screen.findByTestId("firstrun-lan-receipt");
  }

  it("Whisper here: the box finishes the card, and sets the default", async () => {
    lanFakes(true);
    render(<FirstRun />);
    await screen.findByRole("button", { name: /^Set up local AI · / });
    const receipt = await useTheBox();
    expect(receipt.textContent).toContain("USING · QWEN3.8-27B · SUMMARIES · DEFAULT SET");
    expect(calls.find((c) => c.path === "/api/concierge/summary-selection")?.json).toMatchObject({ setDefault: true });
    expect(calls.find((c) => c.path === "/api/setup/discover-models")?.json).toMatchObject({ check_tools: true });
    await waitFor(() => expect(screen.getByRole("status", { name: "LAN · 192.168.1.43" })).toBeTruthy());
    expect(screen.queryByRole("button", { name: /^Set up local AI/ })).toBeNull();
    expect(screen.queryByTestId("firstrun-speech-verb")).toBeNull();
  });

  it("no Whisper here: the card keeps the speech download, named and sized", async () => {
    lanFakes(false);
    render(<FirstRun />);
    await screen.findByRole("button", { name: /^Set up local AI · / });
    fireEvent.click(screen.getByTestId("firstrun-lan-verb"));
    // Beside the server row: the speech model alone (142 MB in this fake).
    expect((await screen.findByTestId("firstrun-speech-verb")).textContent).toBe("Set up speech · 142 MB");
    await useTheBox(true);
    // The card is not done while speech is missing; the verb stays.
    const verb = await screen.findByTestId("firstrun-speech-verb");
    expect(screen.getByRole("status", { name: "WAITS FOR SPEECH" })).toBeTruthy();
    fireEvent.click(verb);
    await waitFor(() =>
      expect(calls.find((c) => c.path === "/api/setup/local-ai" && c.method === "POST")?.json).toEqual({ only: ["whisper"] }),
    );
  });
});
