import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

function source(path: string) {
  return readFileSync(new URL(path, import.meta.url), "utf8");
}

const companion = source("../../pages/cores/CompanionCore.tsx");
const attention = source("../components/AttentionDrawer.tsx");
const capability = source("../pullouts/shared/CapabilitySection.tsx");
const workbench = source("../components/WorkbenchWindow.tsx");
const repo = source("../components/RepoWindow.tsx");
const coder = source("../pullouts/CoderPullout.tsx");
const deliveryTerminal = source("../components/DeliveryTerminalWindow.tsx");
const runtimeDocs = source("../../pages/cores/RuntimeDocsCore.tsx");
const inspector = source("../components/DeskToolInspector.tsx");

describe("HS-129-09 one state grammar", () => {
  it("routes the named loading, empty, and error legs through SurfaceState", () => {
    expect(companion).toMatch(/<SurfaceState\s+loading=\{recipes\.loading\}\s+empty=\{!recipes\.loading\}/s);
    expect(companion).toMatch(/<SurfaceState\s+empty\s+emptyLabel="No sessions"/s);
    expect(companion).toMatch(/<SurfaceState\s+error=\{recipes\.error\}/s);
    expect(attention).toMatch(/store\.loading \?\s*\(\s*<SurfaceState loading/s);
    expect(capability).toMatch(/<SurfaceState error=\{readiness\.detail \|\| "Unavailable"\}/);
    expect(workbench).toMatch(/\{running \? <SurfaceState loading\s*\/> : null\}/);
    expect(workbench).toMatch(/\{resolving \? <SurfaceState loading\s*\/> : null\}/);
    expect(workbench).toMatch(/<SurfaceState\s+error=\{/s);
    expect(repo).toMatch(/<SurfaceState error=\{error\} onRetry=\{retry/s);
    expect(repo).toContain('emptyLabel="ISSUES UNAVAILABLE"');
  });

  it("removes the audited dialect literals", () => {
    expect(companion).not.toMatch(/"READING"|"NO AGENTS"/);
    expect(attention).not.toContain('"Loading…"');
    expect(workbench).not.toContain("Drop to add");
    expect(repo).not.toContain("coming soon");
    expect(repo).not.toContain("Commit failed.");
    expect(coder).not.toContain("Delivery failed. Your reply remains editable.");
  });

  it("keeps raw material behind RAW folds and reference material as rows", () => {
    expect(inspector).toMatch(/<FoldGadget title="RAW · SOURCE">\s*<pre>/s);
    expect(companion).toMatch(/<FoldGadget title="RAW · QUESTION">\s*<pre/s);
    expect(coder).toMatch(/<FoldGadget title="RAW · SELECTED TEXT">\s*<SurfaceWell/s);
    expect(runtimeDocs).not.toContain("SurfaceCode");
    expect(runtimeDocs).toMatch(/<SurfaceRow title="INSTALL"/);
    expect(runtimeDocs).toContain('title="KEY ENV"');
  });
});
