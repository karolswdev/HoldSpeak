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
import {
  announceTaskReturn,
  forgetTaskFocus,
  onReturnToTask,
  rememberTaskFocus,
  returnToTask,
  taskFocusPending,
} from "../../../../desk/returnToTask";

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

/* ── HS-200-41 — the FOCUS half ──────────────────────────────────────────
 *
 * Story 04 shipped the state half above: readiness re-reads without a
 * reload. What it left MISSING (design D3) was the other half of the same
 * ratified sentence — *"on its `Apply` the window closes, the ask well
 * refreshes readiness WITHOUT a reload, and focus returns to `Prepare`."*
 * These tests are that half, on the one shared helper rather than four
 * ad-hoc lines. */

describe("the focus half of return-to-task (HS-200-41)", () => {
  beforeEach(() => {
    forgetTaskFocus();
    document.body.replaceChildren();
  });

  function verb(id: string): HTMLButtonElement {
    const button = document.createElement("button");
    button.id = id;
    button.textContent = id;
    document.body.appendChild(button);
    return button;
  }

  it("puts focus back on the verb the owner left", () => {
    const prepare = verb("prepare");
    prepare.focus();
    rememberTaskFocus();
    // The setup surface takes focus, then unmounts, leaving it on the body.
    (document.activeElement as HTMLElement)?.blur();
    expect(returnToTask()).toBe(true);
    expect(document.activeElement).toBe(prepare);
  });

  it("returns to the verb even while the setup control still holds focus", () => {
    // The Concierge's own Apply is where the hand still is when the set
    // lands. That is not the owner choosing somewhere else, so the return
    // stands — `from` is what tells the two apart.
    const prepare = verb("prepare");
    const apply = verb("apply");
    prepare.focus();
    rememberTaskFocus();
    apply.focus();
    expect(returnToTask(apply)).toBe(true);
    expect(document.activeElement).toBe(prepare);
  });

  it("does NOT steal focus when the owner has moved somewhere else", () => {
    const prepare = verb("prepare");
    const apply = verb("apply");
    const elsewhere = verb("elsewhere");
    prepare.focus();
    rememberTaskFocus();
    // He did not wait: he went and put his hand somewhere else.
    elsewhere.focus();
    expect(returnToTask(apply)).toBe(false);
    expect(document.activeElement).toBe(elsewhere);
  });

  it("does not chase a verb that unmounted while he was away", () => {
    const prepare = verb("prepare");
    prepare.focus();
    rememberTaskFocus();
    prepare.remove();
    expect(returnToTask()).toBe(false);
  });

  it("does not send him back to a verb that is now refused", () => {
    const prepare = verb("prepare");
    prepare.focus();
    rememberTaskFocus();
    prepare.disabled = true;
    (document.activeElement as HTMLElement)?.blur();
    expect(returnToTask()).toBe(false);
  });

  it("is consumed once — a second return moves nothing", () => {
    const prepare = verb("prepare");
    const other = verb("other");
    prepare.focus();
    rememberTaskFocus();
    (document.activeElement as HTMLElement)?.blur();
    expect(returnToTask()).toBe(true);
    other.focus();
    expect(returnToTask()).toBe(false);
    expect(document.activeElement).toBe(other);
  });

  it("remembers nothing when nothing was focused", () => {
    rememberTaskFocus();
    expect(taskFocusPending()).toBe(false);
    expect(returnToTask()).toBe(false);
  });

  it("announceTaskReturn fires the readiness signal AND hands focus back", async () => {
    const prepare = verb("prepare");
    const apply = verb("apply");
    const heard = vi.fn();
    const off = onReturnToTask(heard);
    prepare.focus();
    rememberTaskFocus();
    apply.focus();

    announceTaskReturn(apply);
    // The announcement is synchronous — every subscriber re-reads at once.
    expect(heard).toHaveBeenCalledTimes(1);
    // The focus return waits a frame, so the faces that re-render on the
    // event (and the setup surface that closes on it) settle first.
    await waitFor(() => expect(document.activeElement).toBe(prepare));
    off();
  });
});

describe("SpeakFace hands focus back to the verb it left (HS-200-41)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    forgetTaskFocus();
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

  it("Choose → apply → focus is back on Choose, with the utterance intact", async () => {
    render(<SpeakFace />);
    const well = await screen.findByLabelText("Utterance");
    await userEvent.click(well);
    await userEvent.paste(UTTERANCE);
    const choose = await screen.findByRole("button", { name: "Choose" });
    await userEvent.click(choose);
    // The engine row's handoff remembered the verb it was leaving.
    expect(taskFocusPending()).toBe(true);
    const before = readinessCalls();

    // The setup surface applies and announces, exactly as the Concierge does.
    announceTaskReturn(choose);

    await waitFor(() => expect(readinessCalls()).toBeGreaterThan(before));
    await waitFor(() => expect(document.activeElement).toBe(choose));
    expect(await screen.findByLabelText("Utterance")).toHaveValue(UTTERANCE);
  });
});
