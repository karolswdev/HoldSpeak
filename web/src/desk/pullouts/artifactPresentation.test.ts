import { describe, expect, it } from "vitest";
import { EMPTY_ITEMS } from "../api";
import { presentArtifact, withoutDuplicateHeading, withoutSynthesisFraming } from "./artifactPresentation";

describe("artifact reading presentation", () => {
  it("strips only an exact synthesis footer owned by source metadata", () => {
    const body = "# ADR DRAFTER\n\nKeep the boundary.\n\n- Source windows: win-1\n- Source plugin runs: run-2\n";
    const sources = [
      { source_type: "intent_window", source_ref: "win-1" },
      { source_type: "plugin_run", source_ref: "run-2" },
    ];
    expect(withoutSynthesisFraming(body, sources)).toBe("# ADR DRAFTER\n\nKeep the boundary.");
    expect(withoutSynthesisFraming(body.replace("run-2", "run-other"), sources)).toBe(body.replace("run-2", "run-other"));
  });

  it("removes one duplicate title heading and keeps a plain first line", () => {
    expect(withoutDuplicateHeading("# Keep the data\n\nBody", "Keep the data")).toBe("Body");
    expect(withoutDuplicateHeading("Keep the data\n\nBody", "Keep the data")).toBe("Keep the data\n\nBody");
    expect(withoutDuplicateHeading("Keep the data in the cache", "Keep the data")).toBe("Keep the data in the cache");
  });

  it("recognizes the exact empty ADR result without inventing document material", () => {
    const result = presentArtifact({
      title: "ADR Drafter",
      artifactType: "adr",
      bodyMarkdown: "# ADR Drafter\n\nadr_drafter: no architectural decisions found.\n",
      sources: [{ source_type: "workbench", source_ref: "wb-1" }],
      items: { ...EMPTY_ITEMS },
    });
    expect(result.isEmptyResult).toBe(true);
    expect(result.emptyLabel).toBe("No architecture decisions found");
    expect(result.body).toBe("");
    expect(result.sources[0]).toMatchObject({ ref: "wb-1", resolved: false });
  });
});
