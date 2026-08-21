import { describe, expect, it } from "vitest";
import { mergeSettingsChanges } from "../SettingsCore";

describe("SettingsCore atomic settings writer", () => {
  it("creates a newly introduced settings section in an older payload", () => {
    const legacy = {
      meeting: { intel_provider: "local" },
      dictation: { runtime: { backend: "auto" } },
    } as never;

    const merged = mergeSettingsChanges(legacy, [
      [["thoughts", "inference_target_id"], "preset_openrouter_qwen3_8b"],
    ]);

    expect(merged).toMatchObject({
      meeting: { intel_provider: "local" },
      dictation: { runtime: { backend: "auto" } },
      thoughts: { inference_target_id: "preset_openrouter_qwen3_8b" },
    });
    expect(legacy).not.toHaveProperty("thoughts");
  });

  it("creates every missing intermediate object for a coupled local choice", () => {
    const merged = mergeSettingsChanges({} as never, [
      [["meeting", "intel_realtime_model"], "/Models/qwen.gguf"],
      [["thoughts", "inference_target_id"], null],
      [["dictation", "runtime", "backend"], "llama_cpp"],
    ]);

    expect(merged).toMatchObject({
      meeting: { intel_realtime_model: "/Models/qwen.gguf" },
      thoughts: { inference_target_id: null },
      dictation: { runtime: { backend: "llama_cpp" } },
    });
  });
});
