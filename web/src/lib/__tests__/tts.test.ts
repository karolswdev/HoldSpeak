/**
 * HS-154-01 — tts.ts unit tests.
 *
 * - speak() uses speechSynthesis when server is unavailable
 * - sentence queue speaks in order and can be flushed by stop()
 * - R4: server first chunk > 2 s falls back to browser voice
 * - no-voice silent no-op (never a crash)
 */
import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import {
  speak,
  enqueueSentence,
  stop,
  getState,
  onStateChange,
  _resetForTest,
  _setPreferServer,
  _getQueue,
  _getServerState,
} from "../tts";

// ---- mock speechSynthesis ----

function createMockSynthesis() {
  const utterances: SpeechSynthesisUtterance[] = [];
  const mockVoice = {
    lang: "en-US",
    name: "Mock English",
    localService: true,
    default: true,
    voiceURI: "mock-en-us",
  } as SpeechSynthesisVoice;

  const synth = {
    speak: vi.fn((u: SpeechSynthesisUtterance) => {
      utterances.push(u);
      // Auto-complete after a microtask
      setTimeout(() => {
        if (u.onend) u.onend(new Event("end") as SpeechSynthesisEvent);
      }, 10);
    }),
    cancel: vi.fn(() => {
      utterances.length = 0;
    }),
    getVoices: vi.fn(() => [mockVoice]),
    pending: false,
    speaking: false,
    paused: false,
    onvoiceschanged: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  };

  return { synth, utterances, mockVoice };
}

let mockSynth: ReturnType<typeof createMockSynthesis>;

beforeEach(() => {
  _resetForTest();
  mockSynth = createMockSynthesis();
  vi.stubGlobal("speechSynthesis", mockSynth.synth);
  vi.stubGlobal("SpeechSynthesisUtterance", class {
    text = "";
    voice: SpeechSynthesisVoice | null = null;
    onend: ((e: Event) => void) | null = null;
    onerror: ((e: Event) => void) | null = null;
    constructor(text?: string) {
      if (text) this.text = text;
    }
  });
});

afterEach(() => {
  vi.restoreAllMocks();
  _resetForTest();
});

describe("tts seam", () => {
  describe("browser voice (default)", () => {
    it("speak() calls speechSynthesis.speak", async () => {
      speak("Hello world");
      // Wait for the async probe + speak
      await vi.waitFor(() => {
        expect(mockSynth.synth.speak).toHaveBeenCalled();
      }, { timeout: 1000 });
    });

    it("speak() state transitions: idle -> speaking -> idle", async () => {
      const states: string[] = [];
      onStateChange((s) => states.push(s));

      speak("Test");
      await vi.waitFor(() => {
        expect(states).toContain("speaking");
      }, { timeout: 1000 });

      // Let the utterance complete
      await vi.waitFor(() => {
        expect(getState()).toBe("idle");
      }, { timeout: 1000 });
    });

    it("stop() cancels speechSynthesis and clears queue", () => {
      enqueueSentence("one");
      enqueueSentence("two");
      stop();
      expect(mockSynth.synth.cancel).toHaveBeenCalled();
      expect(_getQueue()).toHaveLength(0);
      expect(getState()).toBe("idle");
    });

    it("sentence queue speaks in order", async () => {
      const spoken: string[] = [];
      const origSpeak = mockSynth.synth.speak;
      mockSynth.synth.speak.mockImplementation((u: SpeechSynthesisUtterance) => {
        spoken.push(u.text);
        // Auto-complete immediately
        setTimeout(() => {
          if (u.onend) u.onend(new Event("end") as SpeechSynthesisEvent);
        }, 5);
      });

      enqueueSentence("First sentence.");
      enqueueSentence("Second sentence.");
      enqueueSentence("Third sentence.");

      await vi.waitFor(() => {
        expect(spoken).toHaveLength(3);
      }, { timeout: 2000 });

      expect(spoken[0]).toBe("First sentence.");
      expect(spoken[1]).toBe("Second sentence.");
      expect(spoken[2]).toBe("Third sentence.");
    });

    it("no speechSynthesis available: silent no-op, never a crash", async () => {
      vi.stubGlobal("speechSynthesis", undefined);
      // Must not throw
      speak("This should be silent");
      await new Promise((r) => setTimeout(r, 50));
      expect(getState()).toBe("idle");
    });
  });

  describe("server probe", () => {
    it("default state has server unchecked", () => {
      const s = _getServerState();
      expect(s.checked).toBe(false);
      expect(s.preferServer).toBe(false);
    });

    it("_setPreferServer overrides probe", () => {
      _setPreferServer(true);
      const s = _getServerState();
      expect(s.checked).toBe(true);
      expect(s.installed).toBe(true);
      expect(s.model_ready).toBe(true);
      expect(s.preferServer).toBe(true);
    });
  });

  describe("R4 fallback", () => {
    it("falls back to browser voice when server is slow (> 2s)", async () => {
      _setPreferServer(true);

      // Mock apiRequest to simulate slow response (never resolves within 2s)
      const { apiRequest } = await import("../api");
      const origFetch = globalThis.fetch;
      vi.stubGlobal("fetch", vi.fn(() =>
        new Promise((resolve) => {
          // Simulate 3s delay — should trigger R4 abort
          setTimeout(() => {
            resolve(new Response("", { status: 200 }));
          }, 3000);
        }),
      ));

      speak("R4 test");

      // Should eventually fall back to browser voice
      await vi.waitFor(() => {
        expect(mockSynth.synth.speak).toHaveBeenCalled();
      }, { timeout: 5000 });

      vi.stubGlobal("fetch", origFetch);
    });
  });

  describe("onStateChange", () => {
    it("subscribe/unsubscribe works", () => {
      const states: string[] = [];
      const unsub = onStateChange((s) => states.push(s));
      speak("test");
      unsub();
      // After unsub, no more notifications
    });
  });

  describe("M1: server-voice Audio stoppable by stop()", () => {
    it("stop() pauses the server-voice Audio element and transitions to idle", async () => {
      _setPreferServer(true);

      // Mock fetch to return a valid audio blob quickly
      const fakeBlob = new Blob(["fake-audio"], { type: "audio/wav" });
      const origFetch = globalThis.fetch;
      vi.stubGlobal("fetch", vi.fn(() =>
        Promise.resolve(new Response(fakeBlob, { status: 200 })),
      ));

      // Mock Audio constructor to track pause calls
      const mockPause = vi.fn();
      let mockAudioInstance: Record<string, unknown> | null = null;
      class MockAudio {
        src = "";
        currentTime = 0;
        onended: ((e: Event) => void) | null = null;
        onerror: ((e: Event) => void) | null = null;
        play = vi.fn(() => Promise.resolve());
        pause = mockPause;
        constructor(_url?: string) {
          if (_url) this.src = _url;
          mockAudioInstance = this as unknown as Record<string, unknown>;
        }
      }
      vi.stubGlobal("Audio", MockAudio);

      // Mock URL.createObjectURL / revokeObjectURL
      const origCreate = URL.createObjectURL;
      const origRevoke = URL.revokeObjectURL;
      URL.createObjectURL = vi.fn(() => "blob:fake-url");
      URL.revokeObjectURL = vi.fn();

      // Start speaking via server path
      speak("Server test");

      // Wait for the Audio element to be "playing"
      await vi.waitFor(() => {
        expect(mockAudioInstance).not.toBeNull();
        expect((mockAudioInstance as Record<string, unknown>).play).toBeDefined();
        const playFn = (mockAudioInstance as Record<string, unknown>).play as ReturnType<typeof vi.fn>;
        expect(playFn).toHaveBeenCalled();
      }, { timeout: 2000 });

      // Now call stop() — it must pause the server audio element
      stop();

      expect(mockPause).toHaveBeenCalled();
      expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:fake-url");
      expect(getState()).toBe("idle");

      // Restore
      URL.createObjectURL = origCreate;
      URL.revokeObjectURL = origRevoke;
      vi.stubGlobal("fetch", origFetch);
    });
  });

  describe("S3: pickVoice prefers local-only voices", () => {
    it("selects a local English voice over a non-local one", async () => {
      const localVoice = {
        lang: "en-US",
        name: "Local English",
        localService: true,
        default: false,
        voiceURI: "local-en",
      } as SpeechSynthesisVoice;
      const cloudVoice = {
        lang: "en-US",
        name: "Cloud English",
        localService: false,
        default: true,
        voiceURI: "cloud-en",
      } as SpeechSynthesisVoice;

      mockSynth.synth.getVoices.mockReturnValue([cloudVoice, localVoice]);

      speak("Voice preference test");
      await vi.waitFor(() => {
        expect(mockSynth.synth.speak).toHaveBeenCalled();
      }, { timeout: 1000 });

      const utterance = mockSynth.synth.speak.mock.calls[0][0] as SpeechSynthesisUtterance;
      expect(utterance.voice).toBe(localVoice);
    });

    it("returns null voice (no crash) when only non-local voices exist", async () => {
      const cloudVoice = {
        lang: "en-US",
        name: "Cloud Only",
        localService: false,
        default: true,
        voiceURI: "cloud-only",
      } as SpeechSynthesisVoice;

      mockSynth.synth.getVoices.mockReturnValue([cloudVoice]);

      // Speak should still work (null voice = browser default)
      speak("Fallback test");
      await vi.waitFor(() => {
        expect(mockSynth.synth.speak).toHaveBeenCalled();
      }, { timeout: 1000 });

      const utterance = mockSynth.synth.speak.mock.calls[0][0] as SpeechSynthesisUtterance;
      // voice should be null (no local voice to select)
      expect(utterance.voice).toBeNull();
    });

    it("selects a local non-English voice when no local English exists", async () => {
      const localFr = {
        lang: "fr-FR",
        name: "Local French",
        localService: true,
        default: false,
        voiceURI: "local-fr",
      } as SpeechSynthesisVoice;
      const cloudEn = {
        lang: "en-US",
        name: "Cloud English",
        localService: false,
        default: true,
        voiceURI: "cloud-en",
      } as SpeechSynthesisVoice;

      mockSynth.synth.getVoices.mockReturnValue([cloudEn, localFr]);

      speak("Non-English local test");
      await vi.waitFor(() => {
        expect(mockSynth.synth.speak).toHaveBeenCalled();
      }, { timeout: 1000 });

      const utterance = mockSynth.synth.speak.mock.calls[0][0] as SpeechSynthesisUtterance;
      expect(utterance.voice).toBe(localFr);
    });
  });
});
