// HS-135-11 -- capture hero tests:
// 1. tap -> record-start (mocked verb)
// 2. state render + dock-orb consistency (shared store fixture)
// 3. voice match set (transcription fixture; near-misses do NOT trigger)
// 4. Ask AI opens (mocked)
// 5. gradient-only-here style test (accent-gradient confined to hero + record-orb)

import { fireEvent, render, screen, act } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import fs from "node:fs";
import path from "node:path";
import { CaptureHero, matchesRecordCommand, VOICE_RECORD_COMMANDS } from "./CaptureHero";

// ---------------------------------------------------------------------------
// store mock: the minimal shared recording store the hero + dock orb read
// ---------------------------------------------------------------------------

const mockStartRecording = vi.fn().mockResolvedValue(undefined);
const mockStopRecording = vi.fn().mockResolvedValue(undefined);

let storeState = {
  recording: "idle" as "idle" | "busy" | "recording",
  recordingExternal: false,
  recordingStartedAt: null as number | null,
  startRecording: mockStartRecording,
  stopRecording: mockStopRecording,
};

vi.mock("../../store", () => {
  const useDesk = (selector: (s: typeof storeState) => unknown) =>
    selector(storeState);
  useDesk.getState = () => storeState;
  return { useDesk };
});

// ---------------------------------------------------------------------------
// sfx mock
// ---------------------------------------------------------------------------

vi.mock("../../../lib/sfx", () => ({
  play: vi.fn(),
}));

// ---------------------------------------------------------------------------
// MicButton mock: renders a button that calls onText when clicked
// ---------------------------------------------------------------------------

vi.mock("../../components/MicButton", () => ({
  MicButton: ({ onText, onState, label }: {
    onText: (text: string) => void;
    onState?: (state: string) => void;
    label?: string;
    variant?: string;
  }) => (
    <button
      data-testid="mock-mic-button"
      aria-label={label ?? "Speak"}
      onClick={() => {
        // Simulate: mic opens, transcription arrives, mic closes.
        onState?.("listening");
        onText("start meeting");
        onState?.("idle");
      }}
    >
      MIC
    </button>
  ),
  // Re-export the type
  type: { MicState: {} },
}));

// ---------------------------------------------------------------------------
// systemSprites mock
// ---------------------------------------------------------------------------

vi.mock("../../systemSprites", () => ({
  SYSTEM: {
    micGlyph: "/desk/sprites/mic.png",
    recordOrb: "/desk/sprites/record-orb.png",
  },
}));

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

function resetStore(overrides: Partial<typeof storeState> = {}) {
  storeState = {
    recording: "idle",
    recordingExternal: false,
    recordingStartedAt: null,
    startRecording: mockStartRecording,
    stopRecording: mockStopRecording,
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// tests
// ---------------------------------------------------------------------------

describe("CaptureHero", () => {
  beforeEach(() => {
    resetStore();
    vi.clearAllMocks();
  });

  // ---- 1. tap -> record-start (mocked verb) ----

  describe("tap starts recording", () => {
    it("calls startRecording on the shared store when the hero key is tapped", () => {
      const onAskAI = vi.fn();
      render(<CaptureHero onAskAI={onAskAI} />);
      const key = screen.getByTestId("capture-hero-key");
      fireEvent.click(key);
      expect(mockStartRecording).toHaveBeenCalledTimes(1);
    });

    it("does not call startRecording when recording is busy", () => {
      resetStore({ recording: "busy" });
      const onAskAI = vi.fn();
      render(<CaptureHero onAskAI={onAskAI} />);
      const key = screen.getByTestId("capture-hero-key");
      fireEvent.click(key);
      expect(mockStartRecording).not.toHaveBeenCalled();
    });

    it("calls stopRecording when tapped while recording", () => {
      resetStore({ recording: "recording", recordingStartedAt: Date.now() });
      const onAskAI = vi.fn();
      render(<CaptureHero onAskAI={onAskAI} />);
      const key = screen.getByTestId("capture-hero-key");
      fireEvent.click(key);
      expect(mockStopRecording).toHaveBeenCalledTimes(1);
    });

    it("hero key is disabled when state is busy", () => {
      resetStore({ recording: "busy" });
      const onAskAI = vi.fn();
      render(<CaptureHero onAskAI={onAskAI} />);
      const key = screen.getByTestId("capture-hero-key");
      expect(key).toBeDisabled();
    });

    it("hero key has honest label: 'Record a meeting' at idle", () => {
      const onAskAI = vi.fn();
      render(<CaptureHero onAskAI={onAskAI} />);
      const key = screen.getByTestId("capture-hero-key");
      expect(key).toHaveAttribute("aria-label", "Record a meeting");
    });

    it("hero key has honest label: 'Stop recording' when recording", () => {
      resetStore({ recording: "recording", recordingStartedAt: Date.now() });
      const onAskAI = vi.fn();
      render(<CaptureHero onAskAI={onAskAI} />);
      const key = screen.getByTestId("capture-hero-key");
      expect(key).toHaveAttribute("aria-label", "Stop recording");
    });
  });

  // ---- 2. state render + dock-orb consistency (shared store fixture) ----

  describe("recording state in hero (dock-orb consistency)", () => {
    it("renders elapsed time and stop verb when recording", () => {
      resetStore({ recording: "recording", recordingStartedAt: Date.now() });
      const onAskAI = vi.fn();
      render(<CaptureHero onAskAI={onAskAI} />);
      expect(screen.getByTestId("capture-hero-recording")).toBeInTheDocument();
      expect(screen.getByTestId("capture-hero-elapsed")).toBeInTheDocument();
      expect(screen.getByTestId("capture-hero-stop")).toBeInTheDocument();
    });

    it("does not render recording state when idle", () => {
      const onAskAI = vi.fn();
      render(<CaptureHero onAskAI={onAskAI} />);
      expect(screen.queryByTestId("capture-hero-recording")).not.toBeInTheDocument();
    });

    it("stop verb calls stopRecording on the same shared store", () => {
      resetStore({ recording: "recording", recordingStartedAt: Date.now() });
      const onAskAI = vi.fn();
      render(<CaptureHero onAskAI={onAskAI} />);
      const stop = screen.getByTestId("capture-hero-stop");
      fireEvent.click(stop);
      expect(mockStopRecording).toHaveBeenCalledTimes(1);
    });

    it("hero reads recording/startedAt from the same store the dock orb uses", () => {
      // The consistency guarantee: CaptureHero uses useDesk((s) => s.recording)
      // and useDesk((s) => s.recordingStartedAt), which are the SAME selectors
      // the RecordOrb uses. This test verifies that by checking the hero renders
      // the recording state set in the shared store fixture.
      const now = Date.now() - 65000; // 1:05 ago
      resetStore({ recording: "recording", recordingStartedAt: now });
      const onAskAI = vi.fn();
      render(<CaptureHero onAskAI={onAskAI} />);
      // The hero key should be in the active/recording state.
      const key = screen.getByTestId("capture-hero-key");
      expect(key).toHaveAttribute("data-active");
      // The recording section should exist.
      expect(screen.getByTestId("capture-hero-recording")).toBeInTheDocument();
    });
  });

  // ---- 3. voice match set (transcription fixture) ----

  describe("voice command matching", () => {
    it("VOICE_RECORD_COMMANDS contains the expected set", () => {
      expect(VOICE_RECORD_COMMANDS).toEqual([
        "start meeting",
        "start recording",
        "record meeting",
      ]);
    });

    it("matchesRecordCommand returns true for exact matches", () => {
      for (const cmd of VOICE_RECORD_COMMANDS) {
        expect(matchesRecordCommand(cmd)).toBe(true);
      }
    });

    it("matchesRecordCommand is case-insensitive", () => {
      expect(matchesRecordCommand("Start Meeting")).toBe(true);
      expect(matchesRecordCommand("START RECORDING")).toBe(true);
      expect(matchesRecordCommand("Record Meeting")).toBe(true);
    });

    it("matchesRecordCommand trims whitespace", () => {
      expect(matchesRecordCommand("  start meeting  ")).toBe(true);
      expect(matchesRecordCommand("\trecord meeting\n")).toBe(true);
    });

    it("near-misses do NOT trigger", () => {
      expect(matchesRecordCommand("start")).toBe(false);
      expect(matchesRecordCommand("meeting")).toBe(false);
      expect(matchesRecordCommand("start a meeting")).toBe(false);
      expect(matchesRecordCommand("begin meeting")).toBe(false);
      expect(matchesRecordCommand("stop meeting")).toBe(false);
      expect(matchesRecordCommand("start meetings")).toBe(false);
      expect(matchesRecordCommand("record")).toBe(false);
      expect(matchesRecordCommand("")).toBe(false);
      expect(matchesRecordCommand("start meeting please")).toBe(false);
      expect(matchesRecordCommand("can you start meeting")).toBe(false);
    });

    it("voice command triggers startRecording via mock MicButton", () => {
      const onAskAI = vi.fn();
      render(<CaptureHero onAskAI={onAskAI} />);
      // The mock MicButton fires onText("start meeting") on click.
      const mic = screen.getByTestId("mock-mic-button");
      fireEvent.click(mic);
      expect(mockStartRecording).toHaveBeenCalledTimes(1);
    });
  });

  // ---- 4. Ask AI opens (mocked) ----

  describe("Ask AI verb", () => {
    it("renders an Ask AI button", () => {
      const onAskAI = vi.fn();
      render(<CaptureHero onAskAI={onAskAI} />);
      expect(screen.getByTestId("capture-hero-ask")).toBeInTheDocument();
      expect(screen.getByTestId("capture-hero-ask")).toHaveTextContent("Ask AI");
    });

    it("calls onAskAI when the Ask AI button is clicked", () => {
      const onAskAI = vi.fn();
      render(<CaptureHero onAskAI={onAskAI} />);
      const ask = screen.getByTestId("capture-hero-ask");
      fireEvent.click(ask);
      expect(onAskAI).toHaveBeenCalledTimes(1);
    });
  });

  // ---- 5. gradient-only-here style test ----

  describe("accent-gradient boundary (counsel ruling E.4)", () => {
    it("hero.css uses --accent-gradient", () => {
      const cssPath = path.resolve(__dirname, "hero.css");
      const css = fs.readFileSync(cssPath, "utf-8");
      // Strip comments.
      const stripped = css.replace(/\/\*[\s\S]*?\*\//g, "");
      expect(stripped).toMatch(/--accent-gradient/);
    });

    it("accent-gradient appears ONLY in hero.css and record-orb.css within web/src/desk", () => {
      // Walk all CSS files under web/src/desk and check for --accent-gradient usage.
      const deskDir = path.resolve(__dirname, "../..");
      const cssFiles = findCssFiles(deskDir);
      const allowed = new Set([
        path.resolve(__dirname, "hero.css"),
        path.resolve(deskDir, "components/record-orb.css"),
      ]);

      const violators: string[] = [];
      for (const file of cssFiles) {
        if (allowed.has(file)) continue;
        const content = fs.readFileSync(file, "utf-8");
        // Strip comments so that documentary mentions don't false-positive.
        const stripped = content.replace(/\/\*[\s\S]*?\*\//g, "");
        if (stripped.match(/var\(\s*--accent-gradient\s*\)/)) {
          violators.push(path.relative(deskDir, file));
        }
      }
      expect(violators).toEqual([]);
    });
  });
});

// ---------------------------------------------------------------------------
// utility: find all .css files recursively
// ---------------------------------------------------------------------------

function findCssFiles(dir: string): string[] {
  const results: string[] = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...findCssFiles(full));
    } else if (entry.name.endsWith(".css")) {
      results.push(full);
    }
  }
  return results;
}
