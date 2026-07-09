import { describe, it, expect } from "vitest";
import { currentStep, stepAnswered, verdictFor } from "./store.js";

function scenario() {
  return {
    id: "s1",
    pack: "smoke",
    steps: [
      { index: 0, surfaces: { web: { applicable: true }, ipad: { applicable: true }, iphone: { applicable: false, reason: "n/a" } } },
      { index: 1, surfaces: { web: { applicable: true }, ipad: { applicable: false, reason: "n/a" }, iphone: { applicable: false, reason: "n/a" } } },
    ],
  };
}

function sitting(verdicts) {
  return { verdicts };
}

describe("walkthrough resume math", () => {
  it("first step is current when nothing is answered", () => {
    const s = currentStep(sitting([]), scenario());
    expect(s.index).toBe(0);
  });

  it("advances only when every applicable surface of a step is answered", () => {
    // Answer web on step 0 but not ipad → still on step 0.
    let st = sitting([{ scenario_id: "s1", step_index: 0, surface: "web", verdict: "pass" }]);
    expect(currentStep(st, scenario()).index).toBe(0);

    // Answer ipad too → step 0 done (iphone is n/a, not required) → step 1.
    st = sitting([
      { scenario_id: "s1", step_index: 0, surface: "web", verdict: "pass" },
      { scenario_id: "s1", step_index: 0, surface: "ipad", verdict: "fail" },
    ]);
    expect(currentStep(st, scenario()).index).toBe(1);
  });

  it("scenario is complete when all applicable verdicts exist", () => {
    const st = sitting([
      { scenario_id: "s1", step_index: 0, surface: "web", verdict: "pass" },
      { scenario_id: "s1", step_index: 0, surface: "ipad", verdict: "pass" },
      { scenario_id: "s1", step_index: 1, surface: "web", verdict: "skip" },
    ]);
    expect(currentStep(st, scenario())).toBeNull();
  });

  it("stepAnswered ignores n/a surfaces", () => {
    const st = sitting([{ scenario_id: "s1", step_index: 1, surface: "web", verdict: "pass" }]);
    expect(stepAnswered(st, scenario(), scenario().steps[1])).toBe(true);
  });

  it("verdictFor finds the cast verdict", () => {
    const st = sitting([{ scenario_id: "s1", step_index: 0, surface: "web", verdict: "partial", note: "hm" }]);
    expect(verdictFor(st, "s1", 0, "web").note).toBe("hm");
    expect(verdictFor(st, "s1", 0, "ipad")).toBeUndefined();
  });
});
