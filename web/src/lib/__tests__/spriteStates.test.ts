import { describe, expect, it } from "vitest";
import {
  isValidSpriteState,
  SPRITE_STATE_VOCAB,
  spriteStateCssClass,
  type SpriteStateEntry,
} from "../spriteStates";
import {
  spriteVariantKey,
  parseVariantKey,
  variantCssClass,
  deriveWorkbenchSpriteState,
  deriveArtifactSpriteState,
  deriveMeetingSpriteState,
} from "../spriteVariants";

function keys(entries: readonly SpriteStateEntry[]): string[] {
  return entries.map((e) => e.key);
}

describe("SPRITE_STATE_VOCAB", () => {
  it("declares states for workbench, meeting, artifact", () => {
    expect(keys(SPRITE_STATE_VOCAB.workbench)).toContain("idle");
    expect(keys(SPRITE_STATE_VOCAB.workbench)).toContain("pending");
    expect(keys(SPRITE_STATE_VOCAB.workbench)).toContain("running");
    expect(keys(SPRITE_STATE_VOCAB.workbench)).toContain("fresh");
    expect(keys(SPRITE_STATE_VOCAB.meeting)).toContain("idle");
    expect(keys(SPRITE_STATE_VOCAB.meeting)).toContain("recording");
    expect(keys(SPRITE_STATE_VOCAB.meeting)).toContain("paused");
    expect(keys(SPRITE_STATE_VOCAB.artifact)).toContain("draft");
    expect(keys(SPRITE_STATE_VOCAB.artifact)).toContain("final");
    expect(keys(SPRITE_STATE_VOCAB.artifact)).toContain("pending-review");
  });

  it("uses SpriteStateEntry format with key, label, and optional cssHint", () => {
    for (const entries of Object.values(SPRITE_STATE_VOCAB)) {
      for (const entry of entries) {
        expect(entry).toHaveProperty("key");
        expect(entry).toHaveProperty("label");
        expect(typeof entry.key).toBe("string");
        expect(typeof entry.label).toBe("string");
        if (entry.cssHint !== undefined) {
          expect(typeof entry.cssHint).toBe("string");
        }
      }
    }
  });

  it("uses workbench as the vocabulary kind, not recipe", () => {
    expect(SPRITE_STATE_VOCAB).toHaveProperty("workbench");
    expect(SPRITE_STATE_VOCAB).not.toHaveProperty("recipe");
  });
});

describe("isValidSpriteState", () => {
  it("accepts valid states", () => {
    expect(isValidSpriteState("workbench", "idle")).toBe(true);
    expect(isValidSpriteState("workbench", "running")).toBe(true);
    expect(isValidSpriteState("meeting", "recording")).toBe(true);
    expect(isValidSpriteState("artifact", "draft")).toBe(true);
  });
  it("rejects unknown states", () => {
    expect(isValidSpriteState("workbench", "exploding")).toBe(false);
    expect(isValidSpriteState("note", "idle")).toBe(false);
  });
  it("rejects null/undefined", () => {
    expect(isValidSpriteState("workbench", null)).toBe(false);
    expect(isValidSpriteState("workbench", undefined)).toBe(false);
  });
});

describe("spriteStateCssClass", () => {
  it("maps running to sprite-active", () => {
    expect(spriteStateCssClass("running")).toBe("sprite-active");
    expect(spriteStateCssClass("recording")).toBe("sprite-active");
  });
  it("maps fresh to sprite-fresh", () => {
    expect(spriteStateCssClass("fresh")).toBe("sprite-fresh");
  });
  it("maps pending states to sprite-pending", () => {
    expect(spriteStateCssClass("pending")).toBe("sprite-pending");
    expect(spriteStateCssClass("pending-review")).toBe("sprite-pending");
    expect(spriteStateCssClass("draft")).toBe("sprite-pending");
  });
  it("returns empty for null/unknown", () => {
    expect(spriteStateCssClass(null)).toBe("");
    expect(spriteStateCssClass(undefined)).toBe("");
    expect(spriteStateCssClass("idle")).toBe("");
    expect(spriteStateCssClass("final")).toBe("");
  });
});

describe("spriteVariantKey", () => {
  it("returns kind-state for valid states (hyphen separator)", () => {
    expect(spriteVariantKey("workbench", "running")).toBe("workbench-running");
    expect(spriteVariantKey("meeting", "recording")).toBe("meeting-recording");
    expect(spriteVariantKey("artifact", "draft")).toBe("artifact-draft");
  });
  it("returns bare kind for null/undefined/unknown", () => {
    expect(spriteVariantKey("workbench", null)).toBe("workbench");
    expect(spriteVariantKey("workbench", undefined)).toBe("workbench");
    expect(spriteVariantKey("workbench", "exploding")).toBe("workbench");
    expect(spriteVariantKey("note", "idle")).toBe("note");
  });
});

describe("parseVariantKey", () => {
  it("splits kind-state (hyphen)", () => {
    expect(parseVariantKey("workbench-running")).toEqual({
      kind: "workbench",
      state: "running",
    });
  });
  it("returns null state for bare kind", () => {
    expect(parseVariantKey("workbench")).toEqual({
      kind: "workbench",
      state: null,
    });
  });
  it("returns null state for unrecognized kind-state pairs", () => {
    // "note" has no registered states, so "note-idle" is a bare kind
    expect(parseVariantKey("note-idle")).toEqual({
      kind: "note-idle",
      state: null,
    });
  });
});

describe("variantCssClass", () => {
  it("returns the CSS class for a variant key with a mapped state", () => {
    expect(variantCssClass("workbench-running")).toBe("sprite-active");
  });
  it("returns empty for a bare kind", () => {
    expect(variantCssClass("workbench")).toBe("");
  });
});

describe("deriveWorkbenchSpriteState", () => {
  it("returns running when runtime is running", () => {
    expect(deriveWorkbenchSpriteState(3, "running")).toBe("running");
  });
  it("returns fresh when runtime is fresh", () => {
    expect(deriveWorkbenchSpriteState(0, "fresh")).toBe("fresh");
  });
  it("returns pending when count > 0", () => {
    expect(deriveWorkbenchSpriteState(5, null)).toBe("pending");
  });
  it("returns idle when nothing is happening", () => {
    expect(deriveWorkbenchSpriteState(0, null)).toBe("idle");
    expect(deriveWorkbenchSpriteState(0, undefined)).toBe("idle");
  });
  it("running wins over pending", () => {
    expect(deriveWorkbenchSpriteState(5, "running")).toBe("running");
  });
});

describe("deriveArtifactSpriteState", () => {
  it("returns final for final/complete/completed", () => {
    expect(deriveArtifactSpriteState("final")).toBe("final");
    expect(deriveArtifactSpriteState("complete")).toBe("final");
    expect(deriveArtifactSpriteState("Completed")).toBe("final");
  });
  it("returns pending-review for review variants", () => {
    expect(deriveArtifactSpriteState("pending-review")).toBe("pending-review");
    expect(deriveArtifactSpriteState("pending_review")).toBe("pending-review");
    expect(deriveArtifactSpriteState("review")).toBe("pending-review");
    expect(deriveArtifactSpriteState("reviewing")).toBe("pending-review");
  });
  it("returns draft for null/empty/unknown", () => {
    expect(deriveArtifactSpriteState(null)).toBe("draft");
    expect(deriveArtifactSpriteState(undefined)).toBe("draft");
    expect(deriveArtifactSpriteState("")).toBe("draft");
    expect(deriveArtifactSpriteState("something")).toBe("draft");
  });
});

describe("deriveMeetingSpriteState", () => {
  it("returns recording when recording", () => {
    expect(deriveMeetingSpriteState("recording")).toBe("recording");
  });
  it("returns paused when paused", () => {
    expect(deriveMeetingSpriteState("paused")).toBe("paused");
  });
  it("returns idle for null/undefined/unknown", () => {
    expect(deriveMeetingSpriteState(null)).toBe("idle");
    expect(deriveMeetingSpriteState(undefined)).toBe("idle");
    expect(deriveMeetingSpriteState("stopped")).toBe("idle");
  });
});
