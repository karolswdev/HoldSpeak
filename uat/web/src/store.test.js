import { describe, it, expect } from "vitest";
import { currentStep, stepAnswered, verdictFor } from "./store.js";

function scenario() {
  return {
    id: "s1",
    pack: "smoke",
    steps: [
      { index: 0, execution_slots: [
        { id: "react-desktop", target: "web_react", form_factor: "desktop_browser" },
        { id: "swift-ipad", target: "ios_flagship_swift", form_factor: "ipad" },
      ] },
      { index: 1, execution_slots: [
        { id: "react-desktop", target: "web_react", form_factor: "desktop_browser" },
      ] },
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

  it("advances only when every execution slot of a step is answered", () => {
    let st = sitting([{ scenario_id: "s1", step_index: 0, slot_id: "react-desktop", verdict: "pass" }]);
    expect(currentStep(st, scenario()).index).toBe(0);

    st = sitting([
      { scenario_id: "s1", step_index: 0, slot_id: "react-desktop", verdict: "pass" },
      { scenario_id: "s1", step_index: 0, slot_id: "swift-ipad", verdict: "fail" },
    ]);
    expect(currentStep(st, scenario()).index).toBe(1);
  });

  it("scenario is complete when all slot verdicts exist", () => {
    const st = sitting([
      { scenario_id: "s1", step_index: 0, slot_id: "react-desktop", verdict: "pass" },
      { scenario_id: "s1", step_index: 0, slot_id: "swift-ipad", verdict: "pass" },
      { scenario_id: "s1", step_index: 1, slot_id: "react-desktop", verdict: "skip" },
    ]);
    expect(currentStep(st, scenario())).toBeNull();
  });

  it("stepAnswered uses explicit slots", () => {
    const st = sitting([{ scenario_id: "s1", step_index: 1, slot_id: "react-desktop", verdict: "pass" }]);
    expect(stepAnswered(st, scenario(), scenario().steps[1])).toBe(true);
  });

  it("verdictFor finds the cast verdict", () => {
    const st = sitting([{ scenario_id: "s1", step_index: 0, slot_id: "react-desktop", verdict: "partial", note: "hm" }]);
    expect(verdictFor(st, "s1", 0, "react-desktop").note).toBe("hm");
    expect(verdictFor(st, "s1", 0, "swift-ipad")).toBeUndefined();
  });

  it("does not silently complete a malformed step with no slots", () => {
    const malformed = { ...scenario(), steps: [{ index: 0, execution_slots: [] }] };
    expect(currentStep(sitting([]), malformed).index).toBe(0);
    expect(stepAnswered(sitting([]), malformed, malformed.steps[0])).toBe(false);
  });
});
