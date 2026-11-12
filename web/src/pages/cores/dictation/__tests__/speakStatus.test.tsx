// Speak reads the speech engine’s supplied name. The kit tests Elapsed.
import { describe, expect, it } from "vitest";
import { speechEngineName } from "../SpeakFace";

describe("Speak status words", () => {
  it("names the speech engine from the hub's speech read", () => {
    expect(speechEngineName({ status: { speech: { model: "base", backend: "mlx", state: "on_device" } } as never })).toBe("whisper-base-mlx");
    expect(speechEngineName({ status: { speech: { model: "small", backend: "auto", state: "on_device" } } as never })).toBe("whisper-small");
    expect(speechEngineName({ status: null })).toBeNull();
  });
});
