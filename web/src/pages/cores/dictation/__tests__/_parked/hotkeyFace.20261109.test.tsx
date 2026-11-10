// Parked: the native Speak face sends hold-key repairs to Settings.
/* HS-200-05 — the physical hotkey's custody, as it is DRAWN.
 *
 * The defect: the runtime recorded whether the global hotkey listener
 * installed and nothing read it, so Right Option did nothing and the desk
 * never said why. These prove the face now names the permission, its state,
 * and the path to walk — in tokens, never a sentence — and that it says
 * nothing at all when there is nothing to say.
 */
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SpeakFace } from "../SpeakFace";
import { readHotkeyCustody } from "../hotkeyCustody";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn(), startStreamSession: vi.fn() }));

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
  conciergeDetect: () => Promise.resolve({ engines: [] }),
}));

/** One permission row as the server sends it. */
function perm(
  id: string,
  label: string,
  state: string,
  neededFor: string,
  pane: string,
) {
  return {
    id,
    label,
    state,
    source: "test",
    needed_for: neededFor,
    path: ["SYSTEM SETTINGS", "PRIVACY & SECURITY", pane],
    settings_url: `x-apple.systempreferences:com.apple.preference.security?Privacy_${pane}`,
    satisfied: state === "granted",
  };
}

const GRANTED = [
  perm("microphone", "MICROPHONE", "granted", "CAPTURE", "Microphone"),
  perm("input_monitoring", "INPUT MONITORING", "granted", "HOTKEY", "ListenEvent"),
  perm("accessibility", "ACCESSIBILITY", "granted", "TYPING", "Accessibility"),
];

function custodyWire(over: Record<string, unknown> = {}) {
  const permissions = (over.permissions as unknown[]) ?? GRANTED;
  const missing = (permissions as { id: string; satisfied: boolean }[])
    .filter((p) => !p.satisfied)
    .map((p) => p.id);
  return {
    platform: "darwin",
    supported: true,
    key: "alt_r",
    display: "⌥R",
    available: true,
    error: "",
    reason: "",
    permissions,
    missing,
    needs_attention: missing.length > 0 || over.available !== true,
    ...over,
  };
}

let hotkey: Record<string, unknown> | undefined;

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  hotkey = custodyWire();
  mocks.apiFetch.mockImplementation((url: string) => {
    const path = String(url);
    if (path.startsWith("/api/dictation/readiness"))
      return Promise.resolve({ config: {}, target: { label: "Editor" }, hotkey });
    if (path.startsWith("/api/dictation/blocks"))
      return Promise.resolve({ document: { blocks: [] } });
    if (path.startsWith("/api/dictation/corrections"))
      return Promise.resolve({ items: [] });
    return Promise.resolve({});
  });
});

/* ── the pure reading ── */

describe("the HOTKEY block on the Speak face", () => {
  it("is absent when the key works — no decorative all-clear row", async () => {
    render(<SpeakFace />);
    await screen.findByText("Types into"); // betterment C8 words
    expect(screen.queryByTestId("speak-hotkey")).toBeNull();
  });

  it("names a denied grant, its cost, its state and the pane to walk", async () => {
    hotkey = custodyWire({
      permissions: [
        GRANTED[0],
        perm("input_monitoring", "INPUT MONITORING", "denied", "HOTKEY", "ListenEvent"),
        GRANTED[2],
      ],
    });
    render(<SpeakFace />);
    const row = await screen.findByTestId("speak-permission-input_monitoring");
    expect(within(row).getByText("INPUT MONITORING")).toBeTruthy();
    expect(within(row).getByText("Hotkey")).toBeTruthy();
    expect(within(row).getByText("Denied")).toBeTruthy();
    // The walk, as tokens rather than a sentence.
    expect(within(row).getByText("System settings")).toBeTruthy();
    expect(within(row).getByText("Privacy & security")).toBeTruthy();
    // The two grants that ARE in hand stay silent.
    expect(screen.queryByTestId("speak-permission-microphone")).toBeNull();
    expect(screen.queryByTestId("speak-permission-accessibility")).toBeNull();
  });

  it("names a listener that never installed, by token and not by stack", async () => {
    hotkey = custodyWire({
      available: false,
      error: "RuntimeError: pynput is not available.",
      reason: "PYNPUT MISSING",
    });
    render(<SpeakFace />);
    const block = await screen.findByTestId("speak-hotkey");
    expect(within(block).getByText("Unavailable")).toBeTruthy();
    expect(within(block).getByTestId("speak-hotkey-reason").textContent).toBe(
      "pynput missing",
    );
    // The raw exception text never reaches the face.
    expect(block.textContent).not.toContain("pynput is not available");
  });

  it("says nothing when no grant could be read and no fault is known", async () => {
    hotkey = custodyWire({
      available: null,
      permissions: [
        perm("microphone", "MICROPHONE", "unknown", "CAPTURE", "Microphone"),
        perm("input_monitoring", "INPUT MONITORING", "unknown", "HOTKEY", "ListenEvent"),
        perm("accessibility", "ACCESSIBILITY", "unknown", "TYPING", "Accessibility"),
      ],
    });
    render(<SpeakFace />);
    await screen.findByText("Types into"); // betterment C8 words
    expect(screen.queryByTestId("speak-hotkey")).toBeNull();
  });

  it("an unread grant is silent while a denied one draws", () => {
    const read = readHotkeyCustody({
      hotkey: custodyWire({
        permissions: [
          perm("microphone", "MICROPHONE", "unknown", "CAPTURE", "Microphone"),
          perm("input_monitoring", "INPUT MONITORING", "denied", "HOTKEY", "ListenEvent"),
          GRANTED[2],
        ],
      }),
    });
    expect(read.show).toBe(true);
    expect(read.rows.map((row) => row.id)).toEqual(["input_monitoring"]);
  });

  it("offers ONE verb, and it re-reads the grant the owner just gave", async () => {
    hotkey = custodyWire({
      permissions: [
        GRANTED[0],
        perm("input_monitoring", "INPUT MONITORING", "denied", "HOTKEY", "ListenEvent"),
        GRANTED[2],
      ],
    });
    render(<SpeakFace />);
    const verb = await screen.findByTestId("speak-hotkey-recheck");
    expect(verb.tagName).toBe("BUTTON");
    // Canon A1: the library Button, never a raw <button>.
    expect(verb.className).toContain("btn--ghost");

    // He ticks the box in System Settings, comes back, presses Re-check.
    hotkey = custodyWire();
    await userEvent.click(verb);
    await waitFor(() =>
      expect(screen.queryByTestId("speak-hotkey")).toBeNull(),
    );
  });
});

