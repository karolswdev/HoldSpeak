/* PHILO-17 speech — one speech-readiness truth on Speak, Record, Runs on and
 * Setup, and a meeting with no transcript that says why.
 *
 * The hub is faked: GET /api/setup/local-ai answers `speech` (the
 * whisper_models.speech_readiness truth); a press of "Set up speech" is the
 * first-run page's own speech-only POST. Nothing is downloaded. */
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { LocalAiStatus } from "../localAi";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("../../../lib/api", async (importOriginal) => ({
  ApiError: (await importOriginal<typeof import("../../../lib/api")>()).ApiError,
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) => (error instanceof Error ? error.message : "Request failed"),
}));

import { SPEECH_SETUP_EVENT, SpeechSetup, useSpeechSetup } from "../SpeechSetup";
import { NO_TRANSCRIPT_SPEECH, speechWasMissing } from "../speechTruth";
import { meetingsHeadline } from "../../../pages/cores/history/helpers";
import { meetingStripItems } from "../../../pages/cores/history/MeetingHeader";

const MB = 1_000_000;
function status(landed: boolean, over: Partial<LocalAiStatus> = {}): LocalAiStatus {
  return {
    state: "not_started",
    files: [
      { key: "whisper", label: "whisper-base-mlx", size_bytes: 144 * MB, on_device: landed, url: "https://huggingface.co/a" },
      { key: "embed", label: "nomic-embed-text v1.5", size_bytes: 146 * MB, on_device: false },
    ],
    bytes_total: 0,
    bytes_done: 0,
    egress: { destination: "huggingface.co" },
    speech: {
      model: "base", backend: "mlx", state: landed ? "on_device" : "will_download",
      ready: landed, bytes: landed ? 0 : 144 * MB,
    },
    error: "",
    ...over,
  };
}

let local: LocalAiStatus;
const calls: { path: string; method: string; json?: unknown }[] = [];

beforeEach(() => {
  calls.length = 0;
  local = status(false);
  mocks.apiFetch.mockReset().mockImplementation(async (path: string, init: { method?: string; json?: unknown } = {}) => {
    const method = init.method ?? "GET";
    calls.push({ path, method, json: init.json });
    if (path === "/api/setup/local-ai" && method === "POST") {
      local = status(true);
      return local;
    }
    if (path === "/api/setup/local-ai") return local;
    throw new Error(`unexpected ${method} ${path}`);
  });
});

function Host({ bare, onReady }: { bare?: boolean; onReady?: () => void }) {
  const setup = useSpeechSetup();
  return <SpeechSetup setup={setup} bare={bare} onReady={onReady} testId="row" />;
}

describe("SpeechSetup — the one row", () => {
  it("speech model missing: the line, the host it comes from, and ONE sized verb", async () => {
    render(<Host />);
    expect((await screen.findByTestId("row-line")).textContent).toBe("Speech is not set up");
    expect(screen.getByTestId("row-verb").textContent).toBe("Set up speech · 144 MB");
    expect(screen.getByText("HUGGINGFACE.CO")).toBeTruthy();
    expect(screen.getAllByRole("button")).toHaveLength(1);
  });

  it("the verb runs the first-run page's speech-only download, then the row goes", async () => {
    const onReady = vi.fn();
    render(<Host onReady={onReady} />);
    fireEvent.click(await screen.findByTestId("row-verb"));
    await waitFor(() =>
      expect(calls.find((c) => c.path === "/api/setup/local-ai" && c.method === "POST")?.json).toEqual({
        only: ["whisper"],
      }),
    );
    await waitFor(() => expect(screen.queryByTestId("row")).toBeNull());
    expect(onReady).toHaveBeenCalledTimes(1);
  });

  it("speech ready: no row at all", async () => {
    local = status(true);
    render(<Host />);
    await waitFor(() => expect(calls.length).toBeGreaterThan(0));
    expect(screen.queryByTestId("row")).toBeNull();
  });

  it("a read with no speech fact draws nothing (never a guess)", async () => {
    local = { ...status(false), speech: undefined };
    render(<Host />);
    await waitFor(() => expect(calls.length).toBeGreaterThan(0));
    expect(screen.queryByTestId("row")).toBeNull();
  });

  it("a model setup cannot get: the line, and no verb that does nothing", async () => {
    local = status(false, { speech: { model: "small", backend: "mlx", state: "not_covered", ready: false, bytes: 0 } });
    render(<Host />);
    expect((await screen.findByTestId("row-line")).textContent).toBe("Speech is not set up");
    expect(screen.queryByTestId("row-verb")).toBeNull();
  });

  it("the speech library cannot run here: named, and no download verb", async () => {
    local = status(false, {
      speech: { model: "base", backend: "mlx", state: "backend_unavailable", ready: false, bytes: 0 },
    });
    render(<Host />);
    expect((await screen.findByTestId("row-line")).textContent).toBe("Speech is not set up");
    expect(screen.getByText("SPEECH LIBRARY MISSING")).toBeTruthy();
    expect(screen.queryByTestId("row-verb")).toBeNull();
  });

  it("setup done elsewhere reaches this face (the setup event, and focus)", async () => {
    render(<Host />);
    await screen.findByTestId("row-verb");
    local = status(true);
    act(() => {
      window.dispatchEvent(new Event(SPEECH_SETUP_EVENT));
    });
    await waitFor(() => expect(screen.queryByTestId("row")).toBeNull());

    local = status(false);
    act(() => {
      window.dispatchEvent(new Event("focus"));
    });
    expect(await screen.findByTestId("row-verb")).toBeTruthy();
  });

  it("bare: the verb only, for a row that already says it", async () => {
    render(<Host bare />);
    expect((await screen.findByTestId("row-verb")).textContent).toBe("Set up speech · 144 MB");
    expect(screen.queryByTestId("row-line")).toBeNull();
  });
});

describe("a meeting saved with no transcript because speech was missing", () => {
  const lost = {
    id: "m1",
    intel_status: "disabled",
    transcriptWords: null,
    transcription_status: "record_only",
    transcription_status_detail: { reason_code: "speech_not_set_up", repair: "set_up_speech" },
  };
  const fine = { id: "m2", intel_status: "complete", has_summary: true, transcriptWords: 120 };

  it("reads the record's reason", () => {
    expect(speechWasMissing(lost)).toBe(true);
    expect(speechWasMissing(fine)).toBe(false);
    expect(NO_TRANSCRIPT_SPEECH).toBe("No transcript: speech is not set up");
  });

  it("the list headline never says All summaries done over it", () => {
    expect(meetingsHeadline([fine], false)).toEqual({ text: "All summaries done", accent: false });
    expect(meetingsHeadline([fine, lost], false)).toEqual({ text: "1 meeting has no transcript", accent: true });
  });

  it("the record's strip names it", () => {
    const items = meetingStripItems(lost, { detail: null, startedAt: "", durationS: 6, segments: [] });
    expect(items.find((item) => item.key === "speech")?.text).toBe("NO TRANSCRIPT · SPEECH NOT SET UP");
  });
});
