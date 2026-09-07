/* HS-200-04 — return to the task.
 *
 * The owner is mid-utterance, sees the engine is not set, opens Models, picks
 * one, and comes back. The utterance must still be in the well, and readiness
 * must be re-read — without a reload and without configuring anything twice. */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SpeakFace } from "../SpeakFace";
import {
  DESK_APPLICATION_ALIASES,
  SURFACE_APPLICATIONS,
} from "../../../../desk/applications";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  startStreamSession: vi.fn(),
  detect: vi.fn(),
  openSurface: vi.fn(),
}));

vi.mock("../../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  newDeliveryId: () => "speak:test-delivery-id",
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
  retryPendingTranscription: vi.fn(async () => null),
  subscribeCaptureLevel: () => () => undefined,
}));
vi.mock("../../../../lib/micStreamSession", () => ({
  micStreamSupported: () => true,
  startStreamSession: mocks.startStreamSession,
  subscribeCaptureLevel: () => () => undefined,
}));
vi.mock("../../assignmentExperience", () => ({
  getAssignmentEditor: () => Promise.resolve(null),
}));
vi.mock("../../../../features/concierge/api", () => ({
  conciergeDetect: mocks.detect,
}));
vi.mock("../../../../desk/shell", () => ({
  openSurface: mocks.openSurface,
  openSurfaceOr: vi.fn(),
}));

const UTTERANCE = "the postgres migration lands on friday";

function readinessCalls(): number {
  return mocks.apiFetch.mock.calls.filter(([url]) =>
    String(url).startsWith("/api/dictation/readiness"),
  ).length;
}

describe("return to the task after configuring a model (HS-200-04)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    localStorage.setItem("holdspeak.speakAim", "field");
    mocks.detect.mockResolvedValue({ engines: [], repairs: [] });
    mocks.apiFetch.mockImplementation((url: string) => {
      const path = String(url);
      if (path.startsWith("/api/dictation/readiness"))
        return Promise.resolve({ config: {}, target: { label: "Editor", overrides: [] } });
      return Promise.resolve({});
    });
  });

  it("the Models handoff has a hosted surface, so it opens in world", () => {
    // Before this story `configure-runs-on` had no hosted surface, so every
    // "Set up AI" handoff fell back to navigate("/settings") and unmounted the
    // task that asked for it.
    const alias = DESK_APPLICATION_ALIASES["configure-runs-on"];
    expect(alias).toBeDefined();
    expect(alias.target).toBe("open-concierge");
    expect(
      SURFACE_APPLICATIONS.some((app) => app.action === alias.target),
    ).toBe(true);
  });

  it("keeps the utterance and re-reads readiness when a model is applied", async () => {
    render(<SpeakFace />);
    const well = await screen.findByLabelText("Utterance");
    await userEvent.click(well);
    await userEvent.paste(UTTERANCE);
    await waitFor(() => expect(readinessCalls()).toBeGreaterThan(0));
    const before = readinessCalls();
    const detects = mocks.detect.mock.calls.length;

    // The Concierge announces the applied set on the one existing signal.
    window.dispatchEvent(new Event("holdspeak:settings-updated"));

    await waitFor(() => expect(readinessCalls()).toBeGreaterThan(before));
    expect(mocks.detect.mock.calls.length).toBeGreaterThan(detects);
    // The task itself is untouched: same words, same well, no reload.
    expect(await screen.findByLabelText("Utterance")).toHaveValue(UTTERANCE);
  });

  it("does not re-read readiness when nothing was applied", async () => {
    render(<SpeakFace />);
    await screen.findByLabelText("Utterance");
    await waitFor(() => expect(readinessCalls()).toBeGreaterThan(0));
    const before = readinessCalls();
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(readinessCalls()).toBe(before);
  });
});
