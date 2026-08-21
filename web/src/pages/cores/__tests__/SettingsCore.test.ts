import { describe, expect, it } from "vitest";
import {
  mergeSettingsChanges,
  projectPendingSettingsChanges,
} from "../SettingsCore";

describe("SettingsCore atomic settings writer", () => {
  it("creates a newly introduced settings section in an older payload", () => {
    const legacy = {
      meeting: { intel_provider: "local" },
      dictation: { runtime: { backend: "auto" } },
    };
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

  it("rebases exact C/D/E patches without allowing old responses or conflicts to erase newer edits", () => {
    const initial = {
      _revision: "r1",
      thoughts: { inference_target_id: null },
      dictation: { runtime: { warm_on_start: false } },
      rails_observer: { tail: 20 },
    };
    const c = [[["thoughts", "inference_target_id"], "preset-deep"]] as Array<
      [string[], unknown]
    >;
    const d = [[["dictation", "runtime", "warm_on_start"], true]] as Array<
      [string[], unknown]
    >;
    const e = [[["rails_observer", "tail"], 40]] as Array<[string[], unknown]>;

    const cResponse = {
      ...mergeSettingsChanges(initial as never, c),
      _revision: "r2",
    } as never;
    const afterC = projectPendingSettingsChanges(cResponse, [d]);
    const put2 = mergeSettingsChanges(cResponse, d);
    expect(afterC).toEqual(put2);

    const dResponse = { ...put2, _revision: "r3" } as never;
    const afterD = projectPendingSettingsChanges(dResponse, [e]);
    const put3 = mergeSettingsChanges(dResponse, e);
    expect(afterD).toEqual(put3);
    expect(put3).toMatchObject({
      _revision: "r3",
      thoughts: { inference_target_id: "preset-deep" },
      dictation: { runtime: { warm_on_start: true } },
      rails_observer: { tail: 40 },
    });

    const external = {
      ...initial,
      _revision: "external-r2",
      meeting: { intel_provider: "cloud" },
    } as never;
    const conflictRebase = projectPendingSettingsChanges(external as never, [d]);
    expect(conflictRebase).toMatchObject({
      _revision: "external-r2",
      thoughts: { inference_target_id: null },
      dictation: { runtime: { warm_on_start: true } },
      meeting: { intel_provider: "cloud" },
    });
  });
});
