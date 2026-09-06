/* HS-176-05 (ruling R13) — ONE mic authority on the Speak face.
   `Talk` is the transport; the utterance well takes `mic={false}`. The
   built well's default-true mic (gadgets.tsx) was a 170 drift that drew a
   THIRD mic beside `Talk` and `Open mic`; the boards draw it mic-less
   (Constitution Article IV.3, design D2(a) closing paragraph). */
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SpeakFace } from "../SpeakFace";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));

vi.mock("../../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (e: unknown) => (e instanceof Error ? e.message : "failed"),
  ApiError: class ApiError extends Error {},
}));
vi.mock("../../../../lib/micSession", () => ({
  subscribeMicPhase: () => () => undefined,
  micCaptureSupported: () => true,
  micCaptureReason: () => null,
}));
vi.mock("../../../../lib/openMic", () => ({
  openMicDrop: vi.fn(),
  openMicListen: vi.fn(),
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
  mocks.apiFetch.mockImplementation(() => Promise.resolve({}));
});

describe("the Speak face's mic authority", () => {
  it("the utterance well carries NO mic of its own", async () => {
    render(<SpeakFace />);
    const well = await screen.findByLabelText("Utterance");
    expect(well.tagName).toBe("TEXTAREA");
    // The gadget's own mic would announce itself as "Speak Utterance".
    expect(screen.queryByRole("button", { name: /Speak Utterance/ })).toBeNull();
  });

  it("`Talk` is still the face's one transport mic", async () => {
    render(<SpeakFace />);
    expect(await screen.findByRole("button", { name: /Talk/ })).toBeTruthy();
  });
});
