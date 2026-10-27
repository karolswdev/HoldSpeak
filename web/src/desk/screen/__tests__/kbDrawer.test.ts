/** Betterment Q10 "Knowledge becomes drawers": a knowledge collection is a
 * drawer on the desk and in About, and nothing offers "Knowledge". The hub
 * half (a collection reads with its live members) is tests/unit/test_desk_drawers.py. */
import { describe, expect, it } from "vitest";
import { EMPTY_ITEMS, fromWireKb } from "../../api";
import { composeScreen } from "../compose";
import { aboutCandidates } from "../../components/about/AboutPicker";
import { menuVerbs, verbById } from "../../verbRegistry";
import { kindWord } from "../../windowName";

const kb = fromWireKb({ id: "kb_ref", name: "Reference", member_ids: ["note:n1"], created_at: "", last_modified: "" })!;
const items = { ...EMPTY_ITEMS, kb: [kb], note: [{ kind: "note", id: "n1", title: "Cutover plan", bodyMarkdown: "x", tags: [], createdAt: "" }] } as never;

describe("a knowledge collection is a drawer", () => {
  it("is drawn as a drawer of its name, and its members stay on the desk", () => {
    const objects = composeScreen({
      items, projectCounts: {}, needsCount: 0, needsRefs: new Set(), heldCalls: 0, sessions: [], flights: [],
      filed: new Set(), persons: [], membersLoaded: true,
    });
    const drawer = objects.find((o) => o.key === "knowledge:kb_ref");
    // W2-BUILDER: the floor caption says Knowledge (atlas 2026-10-27).
    expect(drawer).toMatchObject({ role: "drawer", kindWord: "KNOWLEDGE", name: "Reference", target: { type: "ref", ref: "knowledge:kb_ref" } });
    // A collection is many-to-many: unlike a real drawer it files nothing away.
    expect(objects.some((o) => o.key === "note:n1" && o.role === "loose")).toBe(true);
  });

  it("is an About chip, found by its name, as a drawer", () => {
    const found = aboutCandidates(items).find((c) => c.ref === "knowledge:kb_ref");
    expect(found).toMatchObject({ kind: "zone", label: "Reference" });
  });

  it("nothing offers Knowledge: no New Knowledge, and its window kind is Drawer", () => {
    expect(verbById("desk.new-knowledge")).toBeUndefined();
    expect(menuVerbs("desk").map((v) => v.label)).not.toContain("New Knowledge");
    expect(kindWord("kb")).toBe("Drawer");
  });
});
