import { describe, expect, it, vi } from "vitest";
import { runAsk } from "../ask";
import { editorVoiceGrammar } from "./grammars/editor";
import { routeVoiceIntent } from "./intentRouter";

vi.mock("../ask", () => ({ runAsk: vi.fn() }));

const route = (transcript: string, hasSelection = true) =>
  routeVoiceIntent({
    transcript,
    surfaceKind: "editor",
    selectionState: { hasSelection },
    grammar: editorVoiceGrammar,
  });

describe("voice intent router", () => {
  it("arms a local editor command without egress", async () => {
    const proposal = await route("bold this");
    expect(proposal).toMatchObject({
      intentId: "bold",
      verbId: "editor.bold",
      confidence: 0.9,
      requiresLLM: false,
    });
    expect(runAsk).not.toHaveBeenCalled();
  });

  it("uses Ask only for an LLM-backed candidate", async () => {
    vi.mocked(runAsk).mockResolvedValue({
      ok: true,
      output: '{"intentId":"rewrite","confidence":0.76}',
    } as Awaited<ReturnType<typeof runAsk>>);
    const proposal = await route("rewrite this shorter");
    expect(proposal).toMatchObject({
      intentId: "rewrite",
      confidence: 0.76,
      requiresLLM: true,
    });
    expect(runAsk).toHaveBeenCalledOnce();
  });

  it("falls through to dictation below the confidence threshold", async () => {
    vi.mocked(runAsk).mockResolvedValue({
      ok: true,
      output: '{"intentId":"rewrite","confidence":0.2}',
    } as Awaited<ReturnType<typeof runAsk>>);
    expect(await route("rewrite this shorter")).toMatchObject({
      intentId: "dictation",
      confidence: 0,
    });
  });

  it("does not classify unrelated editor dictation", async () => {
    expect(await route("remember to send the release notes")).toMatchObject({
      intentId: "dictation",
      confidence: 0,
    });
  });
});
