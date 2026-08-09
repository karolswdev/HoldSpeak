/** HS-130-09 — the "Runs on" display token equals the stored token.
 *
 * An unset target stores null (inherit); the display must NOT fabricate a
 * "this_machine" string that was never stored. The sentinel round-trips back
 * to null so stored and displayed carry the same inherit meaning.
 */
import { describe, it, expect } from "vitest";

import {
  INHERIT_TARGET,
  displayTargetToken,
  storedTargetToken,
  isInheritedTarget,
} from "../workbenchTarget";

describe("workbench runs-on token", () => {
  it("never fabricates 'this_machine' for an unset target", () => {
    expect(displayTargetToken(null)).not.toBe("this_machine");
    expect(displayTargetToken(undefined)).not.toBe("this_machine");
    expect(displayTargetToken("")).not.toBe("this_machine");
    expect(displayTargetToken(null)).toBe(INHERIT_TARGET);
  });

  it("round-trips: unset display sentinel stores back as null (inherit)", () => {
    expect(storedTargetToken(displayTargetToken(null))).toBeNull();
    expect(storedTargetToken(INHERIT_TARGET)).toBeNull();
    expect(storedTargetToken("")).toBeNull();
  });

  it("preserves a concrete target token in both directions", () => {
    expect(displayTargetToken("laptop-a")).toBe("laptop-a");
    expect(storedTargetToken("laptop-a")).toBe("laptop-a");
  });

  it("isInheritedTarget is true exactly when unset", () => {
    expect(isInheritedTarget(null)).toBe(true);
    expect(isInheritedTarget(undefined)).toBe(true);
    expect(isInheritedTarget("")).toBe(true);
    expect(isInheritedTarget("laptop-a")).toBe(false);
  });
});
