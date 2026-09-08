// HSM-16-04 — the Ask AI atom's web data layer: the wire payloads match the
// hub routes and the lineage line keeps the iPad grammar.
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ASK_LENSES,
  askContexts,
  askLineageLine,
  keepAsk,
  runAsk,
  stopAskTask,
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
    });
    expect(sent).toEqual({
      prompt: "Go",
      lens: "Distill",
      context: [
        { id: "m1", kind: "meeting", ref: "meeting:m1", title: "Q3 kickoff" },
        { id: "n1", kind: "note", ref: "note:n1", title: "Mesh sync owner" },
      ],
    });
    expect(sent).not.toHaveProperty("profile_id");
    expect(sent).not.toHaveProperty("inference_target_id");
    expect(r).toEqual({
      ok: true,
      output: "PRINTED",
      // HS-200-41: the identity the run was journaled under. Empty when the
      // response omits it (an older shape) — the hub stamps it today.
      invocationId: "",
      // HS-200-41: the hub's bounded refusal token. A run that SUCCEEDED
      // carries none — there is nothing to record as a stop.
      refusalCode: "",
      egress: { scope: "cloud", host: "192.168.1.43" },
      model: "Qwen3.5-9B-Q6_K",
      profileId: "p1",
      inferenceTarget: null,
      actualPlacement: null,
      // HS-83-01: the hub's folded lineage rides the result (empty when the
      // response omits it — an ungrounded ask against an older shape).
      contextIds: [],
      contextTitles: [],
      // HS-103-03: empty when the response carries no per-claim signal
      // (an ungrounded ask, or an older response shape).
      groundingClaims: [],
      groundingReceipt: null,
    });
  });

  // HS-200-41 (ruling B3): a saved ask pins its invocation identity BEFORE
  // anything is dispatched, so an answer that lands after the tab is gone can
  // be CLAIMED out of the hub's ask_results instead of paid for twice. The
  // client had no way to send that id, and never read the one it got back.
  it("runAsk runs under a pinned invocation id and reads the one it is given", async () => {
    let sent: Record<string, unknown> = {};
    vi.stubGlobal("fetch", (_url: string, init: RequestInit) => {
      sent = JSON.parse(String(init.body));
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({ output: "PRINTED", invocation_id: "ask_pinned1" }),
      });
    });
    const r = await runAsk({
      prompt: "Go",
      lens: "Project",
      context: [],
      invocationId: "ask_pinned1",
    });
    expect(sent.invocation_id).toBe("ask_pinned1");
    expect(r.invocationId).toBe("ask_pinned1");
  });

  it("runAsk omits the invocation id entirely when none is pinned", async () => {
    let sent: Record<string, unknown> = {};
    vi.stubGlobal("fetch", (_url: string, init: RequestInit) => {
      sent = JSON.parse(String(init.body));
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ output: "PRINTED" }),
      });
    });
    const r = await runAsk({ prompt: "Go", lens: "Project", context: [] });
    expect(sent).not.toHaveProperty("invocation_id");
    expect(r.invocationId).toBe("");
  });

  it("runAsk parses grounding_claims into the quiet per-claim flag shape", async () => {
    vi.stubGlobal("fetch", () =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            output: "- a\n- b",
            grounding_claims: [
              { text: "a", score: 1, label: "entailed", flagged: false },
              { text: "b", score: 0.1, label: "unsupported", flagged: true },
            ],
          }),
      }),
    );
    const r = await runAsk({ prompt: "Go", lens: "Distill", context: [] });
    expect(r.groundingClaims).toEqual([
      { text: "a", score: 1, label: "entailed", flagged: false },
      { text: "b", score: 0.1, label: "unsupported", flagged: true },
    ]);
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
      context: [
        { id: "m1", kind: "meeting", ref: "meeting:m1", title: "Q3 kickoff" },
      ],
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

/* HS-200-41 — the refusal CODE, kept apart from the refusal sentence.
 *
 * `save_ask` writes the row before dispatch (ruling B3), so the ordinary
 * failure — an engine that is not ready — used to leave the row `saved` with
 * nothing to say about why. The way back in is
 * `POST /api/ask-tasks/{id}/stopped` with the hub's own bounded token, and
 * `runAsk` never read it: it folded `data.error` into the failure string and
 * dropped `data.code` on the floor. */
describe("the refusal code (HS-200-41)", () => {
  it("surfaces the hub's bounded code beside its sentence on a refusal", async () => {
    vi.stubGlobal("fetch", () =>
      Promise.resolve({
        ok: false,
        status: 409,
        json: () =>
          Promise.resolve({
            error: "model file not found: qwen3-35b.gguf",
            code: "inference_target_unavailable",
            inference_target: { id: "t1" },
          }),
      }),
    );
    const r = await runAsk({ prompt: "Go", lens: "Project", context: [] });
    expect(r.ok).toBe(false);
    // The sentence is for the owner's eye — kept verbatim, as it always was.
    expect(r.output).toBe("model file not found: qwen3-35b.gguf");
    // The TOKEN is the only thing that may travel back to the store (B5).
    expect(r.refusalCode).toBe("inference_target_unavailable");
  });

  it("carries no code when the hub sent none, so nothing is invented", async () => {
    vi.stubGlobal("fetch", () =>
      Promise.resolve({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ error: "boom" }),
      }),
    );
    expect((await runAsk({ prompt: "Go", lens: "Project", context: [] })).refusalCode).toBe("");
  });

  it("carries no code when the transport itself failed", async () => {
    vi.stubGlobal("fetch", () => Promise.reject(new TypeError("failed to fetch")));
    const r = await runAsk({ prompt: "Go", lens: "Project", context: [] });
    expect(r.ok).toBe(false);
    expect(r.refusalCode).toBe("");
  });
});

/* The stop wire itself: a token goes up, and NOTHING else. */
describe("stopAskTask (HS-200-41)", () => {
  it("posts the code alone — no reason, no prose, nothing to be helpful with", async () => {
    let url = "";
    let sent: Record<string, unknown> = {};
    vi.stubGlobal("fetch", (target: string, init: RequestInit) => {
      url = target;
      sent = JSON.parse(String(init.body));
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            task: { id: "asktask_1", invocationId: "ask_1", state: "failed" },
            changed: true,
          }),
      });
    });
    const out = await stopAskTask("asktask_1", "inference_target_unavailable");
    expect(url).toBe("/api/ask-tasks/asktask_1/stopped");
    // The server ignores any reason a caller sends; the client does not send
    // one at all, so there is nothing to ignore (ruling B5).
    expect(sent).toEqual({ code: "inference_target_unavailable" });
    expect(out.ok).toBe(true);
    expect(out.changed).toBe(true);
    expect(out.task?.state).toBe("failed");
  });

  it("a repeat on an already-failed row is a no-op, NOT a failure", async () => {
    vi.stubGlobal("fetch", () =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            task: { id: "asktask_1", invocationId: "ask_1", state: "failed" },
            changed: false,
          }),
      }),
    );
    const out = await stopAskTask("asktask_1", "inference_target_unavailable");
    expect(out.ok).toBe(true);
    expect(out.changed).toBe(false);
  });

  it("sends nothing at all when there is no code to send", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    expect(await stopAskTask("asktask_1", "")).toEqual({
      ok: false, task: null, changed: false,
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
