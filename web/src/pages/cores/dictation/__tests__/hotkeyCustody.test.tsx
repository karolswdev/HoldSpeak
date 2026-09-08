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

describe("readHotkeyCustody", () => {
  it("says nothing when the key is proven up and every grant is in hand", () => {
    const read = readHotkeyCustody({ hotkey: custodyWire() });
    expect(read.show).toBe(false);
    expect(read.rows).toEqual([]);
  });

  it("never claims the listener works when the wire could not know", () => {
    const read = readHotkeyCustody({ hotkey: custodyWire({ available: null }) });
    expect(read.available).toBeNull();
    expect(read.token).toBe("UNKNOWN");
    expect(read.kind).toBe("warning");
    expect(read.show).toBe(true);
  });

  it("carries a wire with no hotkey block silently rather than guessing", () => {
    const read = readHotkeyCustody({ config: {} });
    expect(read.show).toBe(false);
    expect(read.available).toBeNull();
  });

  it.each([
    ["denied", "DENIED", "failure"],
    ["not_determined", "NOT ASKED", "warning"],
    ["unknown", "UNKNOWN", "warning"],
  ])("draws %s as %s", (state, token, kind) => {
    const read = readHotkeyCustody({
      hotkey: custodyWire({
        permissions: [
          perm("input_monitoring", "INPUT MONITORING", state, "HOTKEY", "ListenEvent"),
          ...GRANTED.filter((p) => p.id !== "input_monitoring"),
        ],
      }),
    });
    expect(read.rows).toHaveLength(1);
    expect(read.rows[0].token).toBe(token);
    expect(read.rows[0].kind).toBe(kind);
  });

  it("off macOS reads no grant and speaks only when the listener failed", () => {
    const quiet = readHotkeyCustody({
      hotkey: custodyWire({ supported: false, available: null, permissions: [] }),
    });
    expect(quiet.show).toBe(false);
    const loud = readHotkeyCustody({
      hotkey: custodyWire({ supported: false, available: false, permissions: [] }),
    });
    expect(loud.show).toBe(true);
    expect(loud.rows).toEqual([]);
  });
});

/* ── the face ── */

describe("the HOTKEY block on the Speak face", () => {
  it("is absent when the key works — no decorative all-clear row", async () => {
    render(<SpeakFace />);
    await screen.findByText("LANDS IN");
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
    expect(within(row).getByText("HOTKEY")).toBeTruthy();
    expect(within(row).getByText("DENIED")).toBeTruthy();
    // The walk, as tokens rather than a sentence.
    expect(within(row).getByText("SYSTEM SETTINGS")).toBeTruthy();
    expect(within(row).getByText("PRIVACY & SECURITY")).toBeTruthy();
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
    expect(within(block).getByText("UNAVAILABLE")).toBeTruthy();
    expect(within(block).getByTestId("speak-hotkey-reason").textContent).toBe(
      "PYNPUT MISSING",
    );
    // The raw exception text never reaches the face.
    expect(block.textContent).not.toContain("pynput is not available");
  });

  it("says UNKNOWN rather than working when nothing could be read", async () => {
    hotkey = custodyWire({
      available: null,
      permissions: [
        perm("microphone", "MICROPHONE", "unknown", "CAPTURE", "Microphone"),
        perm("input_monitoring", "INPUT MONITORING", "unknown", "HOTKEY", "ListenEvent"),
        perm("accessibility", "ACCESSIBILITY", "unknown", "TYPING", "Accessibility"),
      ],
    });
    render(<SpeakFace />);
    const block = await screen.findByTestId("speak-hotkey");
    expect(within(block).getAllByText("UNKNOWN")).toHaveLength(4); // the key + three grants
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

describe("the head chip never contradicts the rows beneath it", () => {
  it("says BLOCKED, not ACTIVE, when the listener is up but a grant is not", () => {
    /* The macOS trap this story exists for: `Listener.start()` succeeds and
       the key still hears nothing, because Input Monitoring is refused. A
       green ACTIVE beside a red DENIED reads as "it works, but". */
    const read = readHotkeyCustody({
      hotkey: custodyWire({
        available: true,
        permissions: [
          GRANTED[0],
          perm("input_monitoring", "INPUT MONITORING", "denied", "HOTKEY", "ListenEvent"),
          GRANTED[2],
        ],
      }),
    });
    expect(read.token).toBe("BLOCKED");
    expect(read.kind).toBe("warning");
  });

  it("says ACTIVE only when the listener is up AND every grant is held", () => {
    const read = readHotkeyCustody({ hotkey: custodyWire({ available: true }) });
    expect(read.token).toBe("ACTIVE");
    expect(read.show).toBe(false);
  });
});
