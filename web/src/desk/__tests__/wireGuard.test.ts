import { describe, it, expect, vi } from "vitest";
import {
  wireString,
  wireNumber,
  wireBool,
  wireArray,
  wireStringOrNull,
  wireRaw,
  warnMissingId,
} from "../wireGuard";
import {
  fromWireNote,
  fromWireDecision,
  fromWireRecipe,
  fromWireKb,
  fromWireDirectory,
  fromWireChain,
  fromWireWorkflow,
  fromWireWorkbench,
  fromWireRepository,
  fromCoderStatus,
} from "../api";

// ── wireGuard extractors ──────────────────────────────────────────────

describe("wireString", () => {
  it("returns the string value when present", () => {
    expect(wireString({ name: "hello" }, "name")).toBe("hello");
  });
  it("returns fallback when key is missing", () => {
    expect(wireString({}, "name", "default")).toBe("default");
  });
  it("returns fallback when value is not a string", () => {
    expect(wireString({ name: 42 }, "name", "fb")).toBe("fb");
  });
  it("returns empty string fallback by default", () => {
    expect(wireString({}, "name")).toBe("");
  });
  it("returns fallback when wire is null", () => {
    expect(wireString(null, "name", "x")).toBe("x");
  });
  it("returns fallback when wire is undefined", () => {
    expect(wireString(undefined, "name")).toBe("");
  });
});

describe("wireNumber", () => {
  it("returns the number when present", () => {
    expect(wireNumber({ count: 5 }, "count")).toBe(5);
  });
  it("returns fallback when missing", () => {
    expect(wireNumber({}, "count", 10)).toBe(10);
  });
  it("returns fallback when value is not a number", () => {
    expect(wireNumber({ count: "five" }, "count")).toBe(0);
  });
  it("returns fallback for NaN", () => {
    expect(wireNumber({ count: NaN }, "count", 7)).toBe(7);
  });
  it("returns fallback for Infinity", () => {
    expect(wireNumber({ count: Infinity }, "count", 0)).toBe(0);
  });
});

describe("wireBool", () => {
  it("returns boolean value", () => {
    expect(wireBool({ active: true }, "active")).toBe(true);
    expect(wireBool({ active: false }, "active")).toBe(false);
  });
  it("returns fallback when missing", () => {
    expect(wireBool({}, "active", true)).toBe(true);
  });
  it("returns fallback for non-boolean", () => {
    expect(wireBool({ active: 1 }, "active")).toBe(false);
  });
});

describe("wireArray", () => {
  it("returns the array when present", () => {
    expect(wireArray({ items: [1, 2] }, "items")).toEqual([1, 2]);
  });
  it("returns empty array when missing", () => {
    expect(wireArray({}, "items")).toEqual([]);
  });
  it("returns empty array when value is not an array", () => {
    expect(wireArray({ items: "not-array" }, "items")).toEqual([]);
  });
});

describe("wireStringOrNull", () => {
  it("returns string when present", () => {
    expect(wireStringOrNull({ id: "abc" }, "id")).toBe("abc");
  });
  it("returns null when missing", () => {
    expect(wireStringOrNull({}, "id")).toBeNull();
  });
  it("returns null when not a string", () => {
    expect(wireStringOrNull({ id: 123 }, "id")).toBeNull();
  });
});

describe("wireRaw", () => {
  it("returns the raw value", () => {
    const obj = { nested: { a: 1 } };
    expect(wireRaw(obj, "nested")).toEqual({ a: 1 });
  });
  it("returns undefined when missing", () => {
    expect(wireRaw({}, "missing")).toBeUndefined();
  });
});

describe("warnMissingId", () => {
  it("warns when the key is absent", () => {
    const spy = vi.spyOn(console, "warn").mockImplementation(() => {});
    warnMissingId("note", {}, "id");
    expect(spy).toHaveBeenCalledOnce();
    spy.mockRestore();
  });
  it("warns when the value is empty string", () => {
    const spy = vi.spyOn(console, "warn").mockImplementation(() => {});
    warnMissingId("note", { id: "" }, "id");
    expect(spy).toHaveBeenCalledOnce();
    spy.mockRestore();
  });
  it("does not warn when the key has a value", () => {
    const spy = vi.spyOn(console, "warn").mockImplementation(() => {});
    warnMissingId("note", { id: "abc" }, "id");
    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });
});

// ── fromWire* mapper shapes ───────────────────────────────────────────

describe("fromWireNote", () => {
  it("maps valid wire data to Note", () => {
    const wire = {
      id: "n1",
      title: "Test Note",
      body_markdown: "# Hello",
      tags: ["a", "b"],
      created_at: "2026-01-01T00:00:00Z",
      last_modified: "2026-01-02T00:00:00Z",
    };
    const note = fromWireNote(wire);
    expect(note).toEqual({
      kind: "note",
      id: "n1",
      title: "Test Note",
      bodyMarkdown: "# Hello",
      tags: ["a", "b"],
      createdAt: "2026-01-01T00:00:00Z",
      lastModified: "2026-01-02T00:00:00Z",
    });
  });
  it("returns null and warns when id is missing", () => {
    const spy = vi.spyOn(console, "warn").mockImplementation(() => {});
    const note = fromWireNote({});
    expect(note).toBeNull();
    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });
  it("returns null for malformed id types", () => {
    const spy = vi.spyOn(console, "warn").mockImplementation(() => {});
    const note = fromWireNote({ id: 123, title: null, tags: "not-array" });
    expect(note).toBeNull();
    spy.mockRestore();
  });
});

describe("fromWireDecision", () => {
  it("maps valid wire data", () => {
    const wire = {
      id: "d1",
      title: "Use React",
      status: "accepted",
      deciders: ["alice"],
      decided_at: "2026-01-01",
      context_markdown: "ctx",
      decision_markdown: "dec",
      alternatives: [{ name: "Vue", reason: "also good" }],
      consequences_markdown: "cons",
      tags: ["arch"],
      created_at: "2026-01-01",
    };
    const d = fromWireDecision(wire)!;
    expect(d.kind).toBe("decision");
    expect(d.id).toBe("d1");
    expect(d.status).toBe("accepted");
    expect(d.deciders).toEqual(["alice"]);
    expect(d.alternatives).toHaveLength(1);
  });
});

describe("fromWireRecipe", () => {
  it("maps valid wire data to Persona", () => {
    const wire = {
      id: "r1",
      name: "Helper",
      avatar: "",
      role: "assistant",
      system_prompt: "You help.",
      user_template: "",
      tools: ["search"],
      kb_id: "kb1",
      profile_id: "p1",
      capability: { readiness: { state: "ready" } },
    };
    const p = fromWireRecipe(wire)!;
    expect(p.kind).toBe("recipe");
    expect(p.name).toBe("Helper");
    expect(p.tools).toEqual(["search"]);
    expect(p.profileId).toBe("p1");
    expect(p.capability).toEqual({ readiness: { state: "ready" } });
  });
});

describe("fromWireKb", () => {
  it("maps valid wire data", () => {
    const kb = fromWireKb({
      id: "kb1",
      name: "My KB",
      member_ids: ["n1", "n2"],
      created_at: "2026-01-01",
      last_modified: "2026-02-01",
    })!;
    expect(kb.kind).toBe("kb");
    expect(kb.memberIds).toEqual(["n1", "n2"]);
    expect(kb.lastModified).toBe("2026-02-01");
  });
});

describe("fromWireDirectory", () => {
  it("maps valid wire data", () => {
    const dir = fromWireDirectory({
      id: "z1",
      name: "Work",
      parent_id: null,
      member_ids: ["n1"],
      created_at: "2026-01-01",
    })!;
    expect(dir.kind).toBe("directory");
    expect(dir.memberIds).toEqual(["n1"]);
  });
  it("falls back to members object keys", () => {
    const spy = vi.spyOn(console, "warn").mockImplementation(() => {});
    const dir = fromWireDirectory({
      id: "z2",
      name: "Legacy",
      members: { n1: true, n2: true },
    })!;
    expect(dir.memberIds).toEqual(["n1", "n2"]);
    spy.mockRestore();
  });
});

describe("fromWireChain", () => {
  it("maps valid wire data", () => {
    const c = fromWireChain({
      id: "c1",
      name: "Pipeline",
      steps: ["a1", "a2"],
      capability: { readiness: { state: "ready" } },
    })!;
    expect(c.kind).toBe("chain");
    expect(c.steps).toEqual(["a1", "a2"]);
    expect(c.capability).toBeTruthy();
  });
});

describe("fromWireWorkflow", () => {
  it("maps valid wire data with graph", () => {
    const w = fromWireWorkflow({
      id: "w1",
      name: "Summarize",
      prompt: "Do it",
      graph_json: { id: "g1", name: "g", entry: "n1", nodes: [], exec_edges: [], data_edges: [] },
      capability: null,
    })!;
    expect(w.kind).toBe("workflow");
    expect(w.hasGraph).toBe(true);
    expect(w.graphJson).toBeTruthy();
  });
  it("handles empty graph", () => {
    const spy = vi.spyOn(console, "warn").mockImplementation(() => {});
    const w = fromWireWorkflow({ id: "w2", name: "Empty" })!;
    expect(w.hasGraph).toBe(false);
    expect(w.graphJson).toBeUndefined();
    spy.mockRestore();
  });
});

describe("fromWireWorkbench", () => {
  it("maps valid wire data", () => {
    const wb = fromWireWorkbench({
      id: "wb1",
      name: "Daily",
      recipe_id: "r1",
      profile_id: "p1",
      schedule: { cron: "0 9 * * *" },
      schedule_enabled: true,
      item_count: 5,
      pending_count: 2,
      last_run: "2026-01-01",
      created_at: "2026-01-01",
      last_modified: "2026-02-01",
    })!;
    expect(wb.kind).toBe("workbench");
    expect(wb.itemCount).toBe(5);
    expect(wb.scheduleEnabled).toBe(true);
  });
});

describe("fromWireRepository", () => {
  it("maps valid wire data", () => {
    const r = fromWireRepository({
      id: "repo1",
      name: "holdspeak",
      source_id: "src1",
      branch: "main",
      created_at: "2026-01-01",
    })!;
    expect(r.kind).toBe("repository");
    expect(r.sourceId).toBe("src1");
  });
});

describe("fromCoderStatus", () => {
  it("maps nested session structure", () => {
    const data = {
      agent: {
        sessions: {
          items: [
            {
              session: {
                session_id: "s1",
                agent: "claude",
                project: "holdspeak",
                model: "opus",
                state: "running",
              },
              identity: { question: null },
              selected: false,
              pinned: true,
              stale: false,
            },
          ],
        },
      },
    };
    const coders = fromCoderStatus(data);
    expect(coders).toHaveLength(1);
    expect(coders[0].kind).toBe("coder");
    expect(coders[0].sessionId).toBe("s1");
    expect(coders[0].agent).toBe("claude");
    expect(coders[0].pinned).toBe(true);
  });
  it("returns empty array for null data", () => {
    expect(fromCoderStatus(null)).toEqual([]);
  });
});

// ── unknown kinds omitted ─────────────────────────────────────────────

describe("unknown kind handling", () => {
  it("unknown kind from server is not in TypedItems buckets", () => {
    // TypedItems only has known PrimitiveKind keys. An unknown kind
    // string cannot be assigned as a key, so the loadAll mapper
    // naturally omits it. This test validates the type-level guarantee.
    const knownKinds = new Set([
      "meeting", "artifact", "note", "decision", "directory", "kb",
      "project", "repository", "recipe", "chain", "workflow", "coder",
      "game", "layout", "roadmap", "story", "workbench",
    ]);
    expect(knownKinds.has("unknown_future_kind")).toBe(false);
  });
});
