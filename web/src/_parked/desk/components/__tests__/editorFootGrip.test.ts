// The editor footer must reserve the window resize-grip corner —
// Save may never occlude the resize affordance (owner finding,
// 2026-08-17; same occlusion class as the Collapse bug).
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("inline editor foot clears the resize grip", () => {
  it("reserves the grip corner with right padding", () => {
    const css = readFileSync(
      resolve(__dirname, "../inline-editor.css"),
      "utf8",
    );
    const foot = css.split(".desk-inline-editor-foot")[1]?.split("}")[0] ?? "";
    expect(foot).toContain("padding-right");
    expect(foot).toContain("--size-icon-sm");
  });
});
