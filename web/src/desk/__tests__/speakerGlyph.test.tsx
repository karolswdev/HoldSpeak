// HS-154-04 — SpeakerGlyph renders, replays, and shows speaking state.
//
// - The glyph renders on finished assistant messages
// - Clicking replays the message text via speak()
// - Active/speaking visual state when this message is being spoken
// - Click while speaking stops
// - Keyboard reachable (Enter/Space toggles)
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, act } from "@testing-library/react";

// ---- mock autoSpeak ----

const mockReplayMessage = vi.fn();
const mockStopReplay = vi.fn();
let mockActiveSpeakerId: string | null = null;

vi.mock("../autoSpeak", () => ({
  replayMessage: (...args: unknown[]) => mockReplayMessage(...args),
  stopReplay: (...args: unknown[]) => mockStopReplay(...args),
  getActiveSpeakerId: () => mockActiveSpeakerId,
}));

// ---- mock TTS ----

let ttsStateCallback: ((s: string) => void) | null = null;
vi.mock("../../lib/tts", () => ({
  onStateChange: (cb: (s: string) => void) => {
    ttsStateCallback = cb;
    return () => { ttsStateCallback = null; };
  },
}));

import { SpeakerGlyph } from "../components/SpeakerGlyph";

// ---- suite ----

describe("SpeakerGlyph", () => {
  beforeEach(() => {
    mockReplayMessage.mockClear();
    mockStopReplay.mockClear();
    mockActiveSpeakerId = null;
    ttsStateCallback = null;
  });

  afterEach(() => {
    cleanup();
  });

  it("renders with play symbol when not speaking", () => {
    render(<SpeakerGlyph messageId="msg-1" text="Hello world" />);
    const glyph = screen.getByTestId("speaker-glyph");
    expect(glyph.textContent).toContain("▶"); // ▶
    expect(glyph.getAttribute("data-speaking")).toBe("false");
  });

  it("does not render when text is empty", () => {
    render(<SpeakerGlyph messageId="msg-1" text="" />);
    expect(screen.queryByTestId("speaker-glyph")).toBeNull();
  });

  it("does not render when text is whitespace only", () => {
    render(<SpeakerGlyph messageId="msg-1" text="   " />);
    expect(screen.queryByTestId("speaker-glyph")).toBeNull();
  });

  it("click calls replayMessage with message text", () => {
    render(<SpeakerGlyph messageId="msg-1" text="Test text" />);
    const glyph = screen.getByTestId("speaker-glyph");
    fireEvent.click(glyph);
    expect(mockReplayMessage).toHaveBeenCalledWith("msg-1", "Test text");
  });

  it("shows active state when this message is speaking", () => {
    mockActiveSpeakerId = "msg-1";
    render(<SpeakerGlyph messageId="msg-1" text="Test text" />);

    // Simulate TTS speaking
    act(() => {
      ttsStateCallback?.("speaking");
    });

    const glyph = screen.getByTestId("speaker-glyph");
    expect(glyph.getAttribute("data-speaking")).toBe("true");
    expect(glyph.textContent).toContain("■"); // ■ (stop symbol)
    expect(glyph.classList.contains("thread-speaker-glyph--active")).toBe(true);
  });

  it("does NOT show active state when a different message is speaking", () => {
    mockActiveSpeakerId = "msg-OTHER";
    render(<SpeakerGlyph messageId="msg-1" text="Test text" />);

    act(() => {
      ttsStateCallback?.("speaking");
    });

    const glyph = screen.getByTestId("speaker-glyph");
    expect(glyph.getAttribute("data-speaking")).toBe("false");
  });

  it("click while speaking calls stopReplay", () => {
    mockActiveSpeakerId = "msg-1";
    render(<SpeakerGlyph messageId="msg-1" text="Test text" />);

    // Set to speaking state
    act(() => {
      ttsStateCallback?.("speaking");
    });

    const glyph = screen.getByTestId("speaker-glyph");
    fireEvent.click(glyph);
    expect(mockStopReplay).toHaveBeenCalled();
    expect(mockReplayMessage).not.toHaveBeenCalled();
  });

  it("is keyboard reachable with Enter", () => {
    render(<SpeakerGlyph messageId="msg-1" text="Test" />);
    const glyph = screen.getByTestId("speaker-glyph");
    expect(glyph.getAttribute("tabindex")).toBe("0");
    fireEvent.keyDown(glyph, { key: "Enter" });
    expect(mockReplayMessage).toHaveBeenCalledWith("msg-1", "Test");
  });

  it("is keyboard reachable with Space", () => {
    render(<SpeakerGlyph messageId="msg-1" text="Test" />);
    const glyph = screen.getByTestId("speaker-glyph");
    fireEvent.keyDown(glyph, { key: " " });
    expect(mockReplayMessage).toHaveBeenCalledWith("msg-1", "Test");
  });

  it("has correct aria-label for play state", () => {
    render(<SpeakerGlyph messageId="msg-1" text="Test" />);
    const glyph = screen.getByTestId("speaker-glyph");
    expect(glyph.getAttribute("aria-label")).toBe("Speak message");
  });

  it("has correct aria-label for stop state", () => {
    mockActiveSpeakerId = "msg-1";
    render(<SpeakerGlyph messageId="msg-1" text="Test" />);

    act(() => {
      ttsStateCallback?.("speaking");
    });

    const glyph = screen.getByTestId("speaker-glyph");
    expect(glyph.getAttribute("aria-label")).toBe("Stop speaking");
  });
});
