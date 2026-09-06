/* HS-200-05 (AC2) — the Speak face says WHO owns the microphone.

   Browser capture is only honest if the face can answer "is it listening,
   and if not, who has it?". Two shipped tokens answer that, and they are
   pinned here rather than assumed:

   * the `Mic` lamp names the session's own phase, one word
     (`MIC_PHASE_FACT` in shared.ts — CLOSED / SUSPENDED / OPEN /
     SEGMENTING / HELD);
   * a floor refusal names its OWNER (`FloorHeldError.refusal` ->
     `floor_held_meeting` -> `FLOOR HELD MEETING` through `refusalLabel`),
     so "another source has the mic" is never a silent dead button.

   Library species only: a LampGadget and a token. No prose. */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { FloorHeldError } from "../../../../lib/audioFloor";
import { SpeakFace } from "../SpeakFace";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  openMicListen: vi.fn(),
  phaseListener: null as null | ((phase: string) => void),
}));

vi.mock("../../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (e: unknown) => (e instanceof Error ? e.message : "failed"),
  ApiError: class ApiError extends Error {},
}));
vi.mock("../../../../lib/micSession", () => ({
  subscribeMicPhase: (listener: (phase: string) => void) => {
    mocks.phaseListener = listener;
    listener("closed");
    return () => {
      mocks.phaseListener = null;
    };
  },
  micCaptureSupported: () => true,
  micCaptureReason: () => null,
}));
vi.mock("../../../../lib/openMic", () => ({
  openMicDrop: vi.fn(),
  openMicListen: mocks.openMicListen,
}));
vi.mock("../../../../lib/speakToFill", () => ({
  speakToFillSupported: () => true,
  speakToFillUnsupportedReason: () => "",
  retryPendingTranscription: vi.fn(),
  subscribeCaptureLevel: () => () => undefined,
}));
vi.mock("../../assignmentExperience", () => ({
  getAssignmentEditor: () => Promise.resolve(null),
}));
vi.mock("../../../../features/concierge/api", () => ({
  conciergeDetect: () => Promise.resolve({ engines: [] }),
}));

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  mocks.phaseListener = null;
  mocks.apiFetch.mockImplementation(() => Promise.resolve({}));
  mocks.openMicListen.mockImplementation(() => Promise.resolve(undefined));
});

async function openDetails(): Promise<void> {
  const details = await screen.findByRole("button", { name: /Details/ });
  fireEvent.click(details);
}

describe("microphone ownership on the Speak face", () => {
  it("names the mic's own phase, one word", async () => {
    render(<SpeakFace />);
    await openDetails();

    expect(await screen.findByText("CLOSED")).toBeTruthy();

    mocks.phaseListener?.("open");
    await waitFor(() => expect(screen.getByText("OPEN")).toBeTruthy());
  });

  it("names the OWNER when another source holds the floor", async () => {
    mocks.openMicListen.mockRejectedValue(new FloorHeldError("meeting"));
    render(<SpeakFace />);

    fireEvent.click(await screen.findByRole("button", { name: /Open mic/ }));
    await openDetails();

    await waitFor(() =>
      expect(screen.getByText("FLOOR HELD MEETING")).toBeTruthy(),
    );
  });
});
