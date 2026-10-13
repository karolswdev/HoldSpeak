/** HS-130-09 — grammar ↔ handler parity.
 *
 * No voice intent may be advertised without a live handler. Every intent the
 * Workbench grammar advertises must have a matching `case "<id>"` in
 * WorkbenchWindow.handleVoiceProposal — the actual switch, read from source,
 * so drift in either direction fails the build.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, it, expect } from "vitest";

import { workbenchVoiceGrammar } from "../workbench";

// vitest runs with cwd = web/ (see vite.config.ts). Read the real handler
// source so grammar↔handler parity is checked against the actual switch.
const windowSource = readFileSync(
  resolve(process.cwd(), "src/desk/components/WorkbenchWindow.tsx"),
  "utf8",
);

describe("workbench voice grammar parity", () => {
  const intentIds = workbenchVoiceGrammar.intents.map((i) => i.id);

  it("advertises the expected intents", () => {
    expect(new Set(intentIds)).toEqual(
      new Set([
        "add-item",
        "run",
        "dismiss",
        "set-agent",
        "set-schedule",
        "clear-done",
      ]),
    );
  });

  it.each(workbenchVoiceGrammar.intents.map((i) => i.id))(
    "intent %s has a live handler case",
    (id) => {
      expect(windowSource).toContain(`case "${id}":`);
    },
  );

  it("the once-dead intents are now wired", () => {
    // set-agent and dismiss previously fell through to setVoiceProposal(null).
    expect(windowSource).toContain(`case "set-agent":`);
    expect(windowSource).toContain(`case "dismiss":`);
  });
});
