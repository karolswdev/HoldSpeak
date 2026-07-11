// HSM-16-04 — the Ask AI atom's web data layer: the wire payloads match the
// hub routes and the lineage line keeps the iPad grammar.
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ASK_LENSES,
  askContexts,
  askLineageLine,
  keepAsk,
  runAsk,
} from "../ask";
import type { Items } from "../api";

const items = {
  meeting: [{ kind: "meeting", id: "m1", title: "Q3 kickoff" }],
  note: [{ kind: "note", id: "n1", title: "Mesh sync owner" }],
  artifact: [{ kind: "artifact", id: "a1", title: "Q3 summary" }],
  kb: [],
  recipe: [],
  chain: [],
  workflow: [],
  directory: [],
  coder: [],
} as unknown as Items;

afterEach(() => vi.unstubAllGlobals());

describe("ask contexts", () => {
  it("resolves selected ids to id+kind+title, dropping unknowns", () => {
    expect(askContexts(items, ["n1", "m1", "ghost"])).toEqual([
      { id: "n1", kind: "note", ref: "note:n1", title: "Mesh sync owner" },
      { id: "m1", kind: "meeting", ref: "meeting:m1", title: "Q3 kickoff" },
    ]);
  });
});

describe("the lineage line (iPad grammar)", () => {
  const ctx = askContexts(items, ["m1", "n1", "a1"]);
  it("bundles read as 'N items → lens'", () => {
    expect(askLineageLine(ctx, "Distill")).toBe("3 items → Distill");
  });
  it("a single card is named", () => {
    expect(askLineageLine(ctx.slice(0, 1), "Summarize")).toBe(
      "Q3 kickoff → Summarize",
    );
  });
});

describe("the run/keep wire", () => {
  it("runAsk posts the /api/ask payload and returns the honest egress", async () => {
    let sent: any = null;
    vi.stubGlobal("fetch", (url: string, init: any) => {
      expect(url).toBe("/api/ask");
      sent = JSON.parse(init.body);
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            output: "PRINTED",
            egress: { scope: "cloud", host: "192.168.1.43" },
            model: "Qwen3.5-9B-Q6_K",
            profile_id: "p1",
          }),
      });
    });
    const r = await runAsk({
      prompt: "Go",
      lens: "Distill",
      context: askContexts(items, ["m1", "n1"]),
      profileId: "p1",
    });
    expect(sent).toEqual({
      prompt: "Go",
      lens: "Distill",
      context: [
        { id: "m1", kind: "meeting", ref: "meeting:m1", title: "Q3 kickoff" },
        { id: "n1", kind: "note", ref: "note:n1", title: "Mesh sync owner" },
      ],
      profile_id: "p1",
    });
    expect(r).toEqual({
      ok: true,
      output: "PRINTED",
      egress: { scope: "cloud", host: "192.168.1.43" },
      model: "Qwen3.5-9B-Q6_K",
      profileId: "p1",
      inferenceTarget: null,
      actualPlacement: null,
      // HS-83-01: the hub's folded lineage rides the result (empty when the
      // response omits it — an ungrounded ask against an older shape).
      contextIds: [],
      contextTitles: [],
    });
  });

  it("keepAsk posts the /api/ask/keep payload (id+title per card) and returns the artifact id", async () => {
    let sent: any = null;
    vi.stubGlobal("fetch", (url: string, init: any) => {
      expect(url).toBe("/api/ask/keep");
      sent = JSON.parse(init.body);
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ artifact_id: "artifact_x" }),
      });
    });
    const id = await keepAsk({
      lens: "Distill",
      prompt: "Go",
      output: "PRINTED",
      context: askContexts(items, ["m1"]),
    });
    expect(sent).toEqual({
      lens: "Distill",
      prompt: "Go",
      output: "PRINTED",
      context: [{ id: "m1", kind: "meeting", ref: "meeting:m1", title: "Q3 kickoff" }],
    });
    expect(id).toBe("artifact_x");
  });

  it("a hub error surfaces, never throws", async () => {
    vi.stubGlobal("fetch", () =>
      Promise.resolve({
        ok: false,
        status: 502,
        json: () => Promise.resolve({ error: "no model" }),
      }),
    );
    const r = await runAsk({ prompt: "Go", lens: "Ask", context: [] });
    expect(r.ok).toBe(false);
    expect(r.output).toBe("no model");
  });
});

describe("the lens presets", () => {
  it("mirror the iPad RouteLenses (five, Summarize first)", () => {
    expect(ASK_LENSES.map((l) => l.name)).toEqual([
      "Summarize",
      "Action items",
      "Risks",
      "Decisions",
      "Draft email",
    ]);
  });
});
