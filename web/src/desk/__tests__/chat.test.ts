// HS-83-02 — the web persona conversation's data layer: device-local threads
// (the iPad AppStorage posture), the turn wire (history tail + grounding
// refs), harvest. The hub half is locked in pytest
// (test_web_routes_recipe_chat.py); this locks what the web SENDS and KEEPS.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  clearThread,
  keepReply,
  loadChatGrounding,
  loadThread,
  runChatTurn,
  saveChatGrounding,
  saveThread,
  type ChatTurn,
} from "../chat";
import { emptyGrounding, type GroundingSelection } from "../grounding";

const store = new Map<string, string>();
beforeEach(() => {
  store.clear();
  vi.stubGlobal("localStorage", {
    getItem: (k: string) => store.get(k) ?? null,
    setItem: (k: string, v: string) => void store.set(k, v),
    removeItem: (k: string) => void store.delete(k),
  });
});
afterEach(() => vi.unstubAllGlobals());

const turn = (role: "you" | "agent", text: string): ChatTurn => ({
  id: text,
  role,
  text,
});

describe("device-local threads", () => {
  it("round-trips per persona and clears cleanly", () => {
    saveThread("scout", [turn("you", "hi"), turn("agent", "hello")]);
    saveThread("sage", [turn("you", "plan?")]);
    expect(loadThread("scout")).toHaveLength(2);
    expect(loadThread("sage")).toHaveLength(1);
    clearThread("scout");
    expect(loadThread("scout")).toEqual([]);
    expect(loadThread("sage")).toHaveLength(1);
  });
  it("per-conversation grounding persists and empties away", () => {
    const sel: GroundingSelection = {
      meetings: [
        {
          id: "m1",
          title: "Kickoff",
          day: "",
          hasIntel: true,
          includeIntel: true,
          transcriptLines: 0,
          includeTranscript: false,
          intelChars: 10,
          transcriptChars: 0,
          artifacts: [],
        },
      ],
    };
    saveChatGrounding("scout", sel);
    expect(loadChatGrounding("scout").meetings[0].id).toBe("m1");
    saveChatGrounding("scout", emptyGrounding());
    expect(loadChatGrounding("scout")).toEqual({ meetings: [] });
  });
});

describe("the turn wire", () => {
  it("posts question + the 12-turn tail + grounding refs; returns the honest egress", async () => {
    let sent: any = null;
    vi.stubGlobal("fetch", (url: string, init: any) => {
      expect(url).toBe("/api/recipes/scout/chat");
      sent = JSON.parse(init.body);
      return Promise.resolve(
        new Response(
          JSON.stringify({
            output: "BLUE LANTERN",
            egress: { scope: "cloud", host: "192.168.1.43" },
            model: "Qwen",
          }),
        ),
      );
    });
    const history = Array.from({ length: 15 }, (_, i) => turn("you", `t${i}`));
    const r = await runChatTurn("scout", "codename?", history, {
      meetings: [
        {
          id: "m1",
          title: "Kickoff",
          day: "",
          hasIntel: true,
          includeIntel: true,
          transcriptLines: 2,
          includeTranscript: true,
          intelChars: 10,
          transcriptChars: 100,
          artifacts: [],
        },
      ],
    });
    expect(sent.question).toBe("codename?");
    expect(sent.history).toHaveLength(12);
    expect(sent.history[0]).toEqual({ role: "you", text: "t3" });
    expect(sent.grounding).toEqual({
      meeting_ids: ["m1"],
      artifact_ids: [],
      expand: "full",
    });
    expect(r).toEqual({
      ok: true,
      output: "BLUE LANTERN",
      egress: { scope: "cloud", host: "192.168.1.43" },
      model: "Qwen",
    });
  });
  it("omits grounding when nothing is selected and names refusals verbatim", async () => {
    let sent: any = null;
    vi.stubGlobal("fetch", (_u: string, init: any) => {
      sent = JSON.parse(init.body);
      return Promise.resolve(
        new Response(
          JSON.stringify({
            error: "grounding ids not on this hub",
            unknown_ids: ["ghost"],
          }),
          { status: 400 },
        ),
      );
    });
    const r = await runChatTurn("scout", "hi", [], emptyGrounding());
    expect("grounding" in sent).toBe(false);
    expect(r.ok).toBe(false);
    expect(r.output).toBe("grounding ids not on this hub (ghost)");
  });
});

describe("model chats (HS-83-03)", () => {
  it("ids discriminate and round-trip the model name", async () => {
    const { isModelChat, modelChatId, modelChatName } = await import("../chat");
    expect(modelChatId("Qwen3.5-9B")).toBe("modelchat:hub:Qwen3.5-9B");
    expect(isModelChat("modelchat:hub:Qwen3.5-9B")).toBe(true);
    expect(isModelChat("recipe_scout")).toBe(false);
    expect(modelChatName("modelchat:hub:Qwen3.5-9B")).toBe("Qwen3.5-9B");
  });
  it("packs the conversation client-side (no role/context — a model persona has none)", async () => {
    const { packModelTurn } = await import("../chat");
    expect(packModelTurn("Qwen", "codename?", [])).toBe("[USER]\ncodename?");
    const packed = packModelTurn("Qwen", "and now?", [
      turn("you", "hi"),
      turn("agent", "hello"),
    ]);
    expect(packed).toBe(
      "[CONVERSATION SO FAR]\nUser: hi\nQwen: hello\n\n[USER]\nand now?",
    );
  });
  it("a model turn rides /api/ask pinned to THAT model, grounding refs along", async () => {
    const { runModelChatTurn } = await import("../chat");
    let sent: any = null;
    vi.stubGlobal("fetch", (url: string, init: any) => {
      expect(url).toBe("/api/ask");
      sent = JSON.parse(init.body);
      return Promise.resolve(
        new Response(
          JSON.stringify({
            output: "OK",
            egress: { scope: "cloud", host: "192.168.1.43" },
            model: "Qwen3.5-9B",
          }),
        ),
      );
    });
    const r = await runModelChatTurn(
      "Qwen3.5-9B",
      "codename?",
      [turn("you", "hi")],
      {
        meetings: [
          {
            id: "m1",
            title: "Kickoff",
            day: "",
            hasIntel: true,
            includeIntel: true,
            transcriptLines: 0,
            includeTranscript: false,
            intelChars: 10,
            transcriptChars: 0,
            artifacts: [],
          },
        ],
      },
    );
    expect(sent.model).toBe("Qwen3.5-9B");
    expect(sent.lens).toBe("Chat");
    expect(sent.prompt).toContain("[CONVERSATION SO FAR]\nUser: hi");
    expect(sent.grounding).toEqual({
      meeting_ids: ["m1"],
      artifact_ids: [],
      expand: "summary",
    });
    expect(r.ok).toBe(true);
    expect(r.model).toBe("Qwen3.5-9B");
  });
});

describe("harvest", () => {
  it("keepReply posts question + output and returns the artifact id", async () => {
    let sent: any = null;
    vi.stubGlobal("fetch", (url: string, init: any) => {
      expect(url).toBe("/api/recipes/scout/keep");
      sent = JSON.parse(init.body);
      return Promise.resolve(
        new Response(JSON.stringify({ artifact_id: "artifact_9" }), {
          status: 201,
        }),
      );
    });
    expect(await keepReply("scout", "codename?", "BLUE LANTERN.")).toBe(
      "artifact_9",
    );
    expect(sent).toEqual({ question: "codename?", output: "BLUE LANTERN." });
  });
});
