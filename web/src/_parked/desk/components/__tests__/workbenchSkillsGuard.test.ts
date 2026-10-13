// HS-134-06 — Skills belong to the Agent.
//
// WorkbenchWindow displays inherited skills read-only. All skill mutation
// (bind, detach, approve, dismiss) belongs to the Agent editor. This guard
// FAILS when anyone re-introduces a skill mutation path into
// WorkbenchWindow.tsx.
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const COMPONENTS = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const SOURCE = readFileSync(resolve(COMPONENTS, "WorkbenchWindow.tsx"), "utf8");

/** The four mutation identifiers that Issue #450 ruled out of WorkbenchWindow.
 * Any occurrence — import, declaration, call, prop — is a violation. */
const FORBIDDEN = [
  "updateSkill",
  "attachSkill",
  "detachSkill",
  "approveSkill",
];

describe("HS-134-06 skill-mutation guard", () => {
  for (const id of FORBIDDEN) {
    it(`WorkbenchWindow does not contain "${id}"`, () => {
      const regex = new RegExp(`\\b${id}\\b`);
      expect(regex.test(SOURCE)).toBe(false);
    });
  }

  it("no skill picker UI remains", () => {
    expect(SOURCE).not.toContain("wb-skill-picker");
    expect(SOURCE).not.toContain("ATTACH SKILL");
    expect(SOURCE).not.toContain("showSkillPicker");
  });

  it("inherited display and hand-off verb are present", () => {
    expect(SOURCE).toContain("INHERITED");
    expect(SOURCE).toContain("Edit in Agent");
  });

  it("honest empty state names the reason", () => {
    expect(SOURCE).toContain("Agent has no skills yet");
    expect(SOURCE).toContain("Skills appear when an agent is bound");
  });
});
