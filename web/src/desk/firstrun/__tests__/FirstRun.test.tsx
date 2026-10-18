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

// These behavior tests enter the optional setup and chat wells explicitly.
function renderExpandedFirstRun() {
 const view = render(<FirstRun />);
 view.container.querySelectorAll<HTMLDetailsElement>(".firstrun-chat, .firstrun-optional").forEach((fold) => { fold.open = true; });
 return view;
}

import { inventedFields, recorded } from "../../../test/wireShape";
import LOCAL_AI_WIRE from "../../../test/wire/setup-local-ai.wire.json";
import SETTINGS_WIRE from "../../../test/wire/settings.owner.wire.json";
import SETTINGS_PUT_WIRE from "../../../test/wire/settings.put.wire.json";
import NOTE_WIRE from "../../../test/wire/notes-create.wire.json";
import CALENDAR_WIRE from "../../../test/wire/onboarding-calendar.wire.json";
import CONNECTIONS_WIRE from "../../../test/wire/onboarding-connections.wire.json";
import DISCOVER_WIRE from "../../../test/wire/discover-models.wire.json";
import DEFINE_WIRE from "../../../test/wire/define-endpoint.wire.json";
import SELECTION_WIRE from "../../../test/wire/summary-selection.wire.json";
import { ApiError } from "../../../lib/api";

const MB = 1_000_000;
/** The hub's own GET /api/setup/local-ai (the recorder pins an Apple-silicon
 *  Mac with mlx-whisper: tests/integration/test_face_wire_fences.py), with
 *  this test's files on the device. */
function status(over: Partial<LocalAiStatus> & { landed?: boolean; all?: boolean } = {}): LocalAiStatus {
  const { landed = false, all = false, ...rest } = over;
  const speech = landed || all;
  const hub = recorded<LocalAiStatus & Record<string, any>>(LOCAL_AI_WIRE);
  return {
    ...hub,
    files: hub.files.map((f) => ({ ...f, on_device: f.key === "starter" ? all : speech })),
    speech: { ...hub.speech, state: speech ? "on_device" : "will_download", ready: speech } as LocalAiStatus["speech"],
    local_engine: { ...hub.local_engine, ready: all },
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
    if (path === "/api/notes") return { note: { ...recorded<Record<string, any>>(NOTE_WIRE).note, id: "note_1" } };
    if (path === "/api/onboarding/calendar") {
      return { ...recorded<Record<string, unknown>>(CALENDAR_WIRE), macos: { state: "unavailable", can_request: false }, candidates: [], sources: 0 };
    }
    if (path === "/api/onboarding/connections") {
      const hub = recorded<Record<string, any>>(CONNECTIONS_WIRE);
      return { ...hub, candidates: [], tools: { gh: { ...hub.tools.gh, installed: false }, acli: { ...hub.tools.acli, installed: false } } };
    }
    return {};
  });
});

describe("the typed hub bodies carry only the hub's fields (the SCAR LAW)", () => {
  // The hub's own answers: tests/integration/test_face_wire_fences.py::test_first_run_reads.
  it("local AI, settings, a kept note, the calendar and the connections", async () => {
    const hubLocal = recorded<{ files: unknown[] }>(LOCAL_AI_WIRE);
    for (const typed of [status(), status({ landed: true }), status({ all: true })]) {
      const { files, ...rest } = typed;
      expect(inventedFields(rest, hubLocal)).toEqual([]);
      for (const file of files) expect(inventedFields(file, hubLocal.files[0])).toEqual([]);
    }
    expect(inventedFields(await mocks.apiFetch("/api/settings"), recorded(SETTINGS_WIRE))).toEqual([]);
    expect(inventedFields(await mocks.apiFetch("/api/settings", { method: "PUT", json: { owner: { name: "K", aliases: [] } } }),
      recorded(SETTINGS_PUT_WIRE))).toEqual([]);
    expect(inventedFields(await mocks.apiFetch("/api/notes", { method: "POST" }), recorded(NOTE_WIRE))).toEqual([]);
    expect(inventedFields(await mocks.apiFetch("/api/onboarding/calendar"), recorded(CALENDAR_WIRE))).toEqual([]);
    expect(inventedFields(await mocks.apiFetch("/api/onboarding/connections"), recorded(CONNECTIONS_WIRE))).toEqual([]);
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
  it("starts with speech alone and folds the optional decisions", async () => {
    const view = render(<FirstRun />);
    const speech = await screen.findByTestId("firstrun-speech-verb");
    expect(speech.className).toContain("btn--primary");
    expect(speech.textContent).toBe("Set up speech · 144 MB");
    expect(view.container.querySelector<HTMLDetailsElement>(".firstrun-chat")?.open).toBe(false);
    expect(view.container.querySelector<HTMLDetailsElement>(".firstrun-optional")?.open).toBe(false);
    expect(screen.getByRole("textbox", { name: "Your name" }).closest("details")?.open).toBe(false);
    expect(screen.getByRole("button", { name: "Continue later" })).toBeTruthy();
    fireEvent.click(speech);
    await waitFor(() => expect(calls.find((call) => call.path === "/api/setup/local-ai" && call.method === "POST")?.json).toEqual({ only: ["whisper"] }));
  });

  it("walks before -> running -> speech lands -> heard -> kept", async () => {
    const audio = new ArrayBuffer(44 + 32000 * 4);
    mocks.start.mockResolvedValue({
      stop: vi.fn().mockResolvedValue("Send the cutover plan to Priya before Friday."),
      cancel: vi.fn(),
      retained: vi.fn().mockResolvedValue(false),
      audio: () => audio,
    });
    renderExpandedFirstRun();

    // before: the one press with its size; First words waits for speech.
    const press = await screen.findByRole("button", { name: "Set up local AI · 3.0 GB" });
    expect(screen.getAllByText("HUGGINGFACE.CO").length).toBeGreaterThan(0);
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
    expect(note?.json).toMatchObject({ title: "Send the cutover plan to Priya", body_markdown: "Send the cutover plan to Priya before Friday." });
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
    renderExpandedFirstRun();
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
    renderExpandedFirstRun();
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
    renderExpandedFirstRun();
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
    renderExpandedFirstRun();
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
    renderExpandedFirstRun();
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

describe("PHILO-17: First words' missing speech model is fixed in place", () => {
  it("never opens New Project: the hub says no speech model -> the shared Set up speech verb, its host, a speech-only download", async () => {
    local = status({ landed: true, state: "not_started" });
    mocks.start.mockImplementation(async () => {
      local = status(); // the hub's read now: the Whisper files are not here
      throw new ApiError(503, "transcription unavailable", null);
    });
    renderExpandedFirstRun();
    fireEvent.click(await screen.findByRole("button", { name: "◖ Dictate one sentence" }));
    const verb = await screen.findByTestId("firstrun-words-speech-verb");
    expect(verb.textContent).toBe("Set up speech · 144 MB");
    const words = screen.getByTestId("firstrun-first-words");
    expect(words.textContent).toContain("HUGGINGFACE.CO");
    expect(screen.queryByRole("button", { name: "Setup" })).toBeNull();
    await act(async () => {
      fireEvent.click(verb);
    });
    const post = calls.find((c) => c.path === "/api/setup/local-ai" && c.method === "POST");
    expect(post?.json).toEqual({ only: ["whisper"] });
    const shell = await import("../../shell");
    expect(vi.mocked(shell.openSurfaceOr)).not.toHaveBeenCalledWith("project-setup", "/");
  });

  it("speech on this device by the hub's read: the door is Engines, not New Project", async () => {
    local = status({ all: true, state: "ready" });
    mocks.start.mockRejectedValue(new ApiError(503, "transcription unavailable", null));
    renderExpandedFirstRun();
    fireEvent.click(await screen.findByRole("button", { name: "◖ Dictate one sentence" }));
    await screen.findByTestId("firstrun-take-failure");
    const shell = await import("../../shell");
    fireEvent.click(await screen.findByRole("button", { name: "Engines" }));
    expect(vi.mocked(shell.openSurfaceOr)).toHaveBeenCalledWith("configure-runs-on", "/profiles");
    expect(vi.mocked(shell.openSurfaceOr)).not.toHaveBeenCalledWith("project-setup", "/");
  });
});

// PHILO-15 10 (B09): the Local AI card's second choice — the model server
// he runs on his network, with no chat download. It is the Concierge's own
// add-engine row. Astra r1 (finding 2): with no Whisper on this device the
// card keeps the speech download beside it, and the press also sets the
// Default for AI work.
describe("FirstRun — Use a server", () => {
  function lanFakes(speechOnDevice: boolean, models: string[] = ["qwen3.8-27b"]) {
    local = status({ landed: speechOnDevice });
    const base = mocks.apiFetch.getMockImplementation()!;
    mocks.apiFetch.mockImplementation(async (path: string, init: { method?: string; json?: unknown } = {}) => {
      // The hub's own answers to the three presses (a fake OpenAI server on
      // the loopback: tests/integration/test_face_wire_fences.py), with this
      // test's server, model and a server that takes tool calls.
      if (path === "/api/setup/discover-models") {
        calls.push({ path, method: "POST", json: init.json });
        return { ...recorded<Record<string, unknown>>(DISCOVER_WIRE), models, tools: "yes" };
      }
      if (path === "/api/inference/model-library/define-endpoint") {
        calls.push({ path, method: "POST", json: init.json });
        const hub = recorded<Record<string, any>>(DEFINE_WIRE);
        return { ...hub, provider: { ...hub.provider, profile_id: "engine-192-168-1-43-8080", profile_revision: 1 } };
      }
      if (path === "/api/concierge/summary-selection") {
        calls.push({ path, method: "POST", json: init.json });
        return recorded(SELECTION_WIRE);
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
    renderExpandedFirstRun();
    await screen.findByRole("button", { name: /^Set up local AI · / });
    const receipt = await useTheBox();
    expect(receipt.textContent).toContain("USING · QWEN3.8-27B · SUMMARIES · NOW THE DEFAULT");
    expect(calls.find((c) => c.path === "/api/concierge/summary-selection")?.json).toMatchObject({ setDefault: true });
    expect(calls.find((c) => c.path === "/api/setup/discover-models")?.json).toMatchObject({ check_tools: true });
    await waitFor(() => expect(screen.getByRole("status", { name: "LAN · 192.168.1.43" })).toBeTruthy());
    expect(screen.queryByRole("button", { name: /^Set up local AI/ })).toBeNull();
    expect(screen.queryByTestId("firstrun-speech-verb")).toBeNull();
  });

  it("a server with two models: nothing is picked for him; Use saves the one he picks", async () => {
    lanFakes(true, ["alpha-7b", "qwen3.8-27b"]);
    renderExpandedFirstRun();
    await screen.findByRole("button", { name: /^Set up local AI · / });
    fireEvent.click(screen.getByTestId("firstrun-lan-verb"));
    fireEvent.change(await screen.findByLabelText("Server address"), { target: { value: "http://192.168.1.43:8080/v1" } });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    const picks = await screen.findAllByTestId("concierge-add-pick-model");
    expect(picks.map((b) => b.textContent)).toEqual(["alpha-7b", "qwen3.8-27b"]);
    expect(picks.every((b) => b.getAttribute("aria-pressed") === "false")).toBe(true);
    expect(screen.queryByTestId("concierge-add-model")).toBeNull();
    expect(screen.getByTestId("concierge-add-submit")).toBeDisabled();
    fireEvent.click(picks[1]);
    expect(screen.getByTestId("concierge-add-model").textContent).toBe("qwen3.8-27b");
    fireEvent.click(screen.getByTestId("concierge-add-submit"));
    await screen.findByTestId("firstrun-lan-receipt");
    const define = calls.find((c) => c.path === "/api/inference/model-library/define-endpoint")?.json as { draft: Record<string, unknown> };
    expect(define.draft).toMatchObject({ model: "qwen3.8-27b" });
  });

  it("no Whisper here: the card keeps the speech download, named and sized", async () => {
    lanFakes(false);
    renderExpandedFirstRun();
    await screen.findByRole("button", { name: /^Set up local AI · / });
    fireEvent.click(screen.getByTestId("firstrun-lan-verb"));
    // Beside the server row: the speech model alone (the recorded two Whisper files, 144 MB).
    expect((await screen.findByTestId("firstrun-speech-verb")).textContent).toBe("Set up speech · 144 MB");
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
