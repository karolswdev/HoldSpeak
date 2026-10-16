import { describe, expect, it } from "vitest";
import { EMPTY_ITEMS, type Items } from "../api";
import { lineage, resolveRef } from "../lineage";

const items = {
  ...EMPTY_ITEMS,
  meeting: [{ kind: "meeting", id: "shared", title: "Meeting" }],
  note: [{ kind: "note", id: "shared", title: "Note" }, { kind: "note", id: "legacy-note", title: "Legacy note" }, { kind: "note", id: "project:shared", title: "Qualified-looking bare ID" }, { kind: "note", id: "knowledge:missing", title: "Wrong-kind qualified-looking ID" }],
  kb: [{ kind: "kb", id: "shared", name: "Knowledge" }],
  project: [{ kind: "project", id: "shared", name: "Project" }],
  directory: [{ kind: "directory", id: "shared", name: "Zone" }],
  recipe: [{ kind: "recipe", id: "shared", name: "Agent" }],
  chain: [{ kind: "chain", id: "shared", name: "Sequence" }],
} as unknown as Items;

describe("lineage resolves the Desk's canonical identities", () => {
  it.each([
    ["note:shared", "note", "Note"],
    ["knowledge:shared", "kb", "Knowledge"],
    ["project:shared", "project", "Project"],
  ])("resolves existing %s by kind even when another kind has the same ID", (ref, kind, label) => {
    expect(resolveRef(items, ref)).toEqual({ kind, label, resolved: true, actionRef: ref });
  });

  it.each([
    ["kb:shared", "knowledge:shared", "kb", "Knowledge"],
    ["directory:shared", "zone:shared", "directory", "Zone"],
    ["zone:shared", "zone:shared", "directory", "Zone"],
    ["recipe:shared", "persona:shared", "recipe", "Agent"],
    ["persona:shared", "persona:shared", "recipe", "Agent"],
    ["chain:shared", "sequence:shared", "chain", "Sequence"],
    ["sequence:shared", "sequence:shared", "chain", "Sequence"],
  ])("resolves %s through the shared canonical alias", (ref, actionRef, kind, label) => {
    expect(resolveRef(items, ref)).toEqual({ kind, label, resolved: true, actionRef });
  });

  it.each(["note:missing", "knowledge:missing", "unknown:shared", ""])('keeps missing "%s" unresolved', (ref) => {
    expect(resolveRef(items, ref)).toEqual({ kind: "", label: ref, resolved: false });
  });

  it("keeps a legacy bare source and supplies its canonical action identity", () => {
    const result = lineage(items, [{ source_type: "note", source_ref: "legacy-note" }]);
    expect(result.from).toEqual([{ type: "note", ref: "legacy-note", kind: "note", label: "Legacy note", resolved: true, actionRef: "note:legacy-note" }]);
  });

  it("keeps legacy via wire identity while resolving a qualified alias", () => {
    const result = lineage(items, [{ source_type: "agent", source_ref: "recipe:shared" }, { source_type: "note", source_ref: "note:shared" }]);
    expect(result.via).toMatchObject({ type: "agent", ref: "recipe:shared", kind: "recipe", label: "Agent", actionRef: "persona:shared" });
    expect(result.from[0]).toMatchObject({ ref: "note:shared", kind: "note", actionRef: "note:shared" });
  });
});
