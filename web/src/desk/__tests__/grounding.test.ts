// HS-83-01 — the context envelope's web mouth: refs-only wire, honest
// fetched-length gauge, receipts rows. The hub half is locked in pytest
// (test_web_routes_ask.py); this locks what the web SENDS and PRICES.
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  emptyGrounding, fetchGroundingMeeting, groundingIsEmpty, groundingLabel,
  groundingReceiptRows, groundingTokens, hubGrounding,
  type GroundingSelection,
} from "../grounding";
import { runAsk } from "../ask";

afterEach(() => vi.unstubAllGlobals());

const sel = (over: Partial<GroundingSelection> = {}): GroundingSelection => ({
  meetings: [
    {
      id: "m1", title: "Q3 kickoff", day: "2026-07-01",
      hasIntel: true, includeIntel: true,
      transcriptLines: 2, includeTranscript: false,
      intelChars: 400, transcriptChars: 8_000,
      artifacts: [
        { id: "a1", title: "Decisions", chars: 200, on: true },
        { id: "a2", title: "Actions", chars: 300, on: false },
      ],
    },
    {
      id: "m2", title: "Deep dive", day: "2026-07-02",
      hasIntel: false, includeIntel: false,
      transcriptLines: 40, includeTranscript: true,
      intelChars: 0, transcriptChars: 20_000,
      artifacts: [],
    },
  ],
  ...over,
});

describe("the wire half (refs only)", () => {
  it("ships ids, never bodies; any transcript toggle upgrades the expand", () => {
    expect(hubGrounding(sel())).toEqual({
      meeting_ids: ["m1", "m2"],
      artifact_ids: ["a1"],
      expand: "full",
    });
  });
  it("digest-only selections expand as summary", () => {
    const s = sel();
    s.meetings = [s.meetings[0]];
    expect(hubGrounding(s)?.expand).toBe("summary");
  });
  it("an empty selection ships nothing", () => {
    expect(hubGrounding(emptyGrounding())).toBeNull();
    expect(groundingIsEmpty(emptyGrounding())).toBe(true);
  });
});

describe("the honest gauge", () => {
  it("prices only what is toggled ON, from real lengths", () => {
    const s = sel();
    const priced = groundingTokens(s);
    // m1: intel 400 + artifact a1 200 (+ headers); m2: transcript 20k (+ header).
    // a2 (off) and m1's transcript (off) contribute NOTHING.
    expect(priced).toBeGreaterThan((400 + 200 + 20_000) / 4);
    expect(priced).toBeLessThan((400 + 200 + 20_000) / 4 + 100);
    s.meetings[1].includeTranscript = false;
    expect(groundingTokens(s)).toBeLessThan(priced - 4_000);
  });
  it("empty prices zero", () => {
    expect(groundingTokens(emptyGrounding())).toBe(0);
  });
});

describe("labels + receipts", () => {
  it("the chip label counts meetings and ON artifacts", () => {
    expect(groundingLabel(sel())).toBe("2 meetings · 1 artifact");
    expect(groundingLabel(emptyGrounding())).toBe("");
  });
  it("receipt rows name the meetings and the ON artifacts", () => {
    expect(groundingReceiptRows(sel())).toEqual([
      { id: "m1", title: "Q3 kickoff" },
      { id: "m2", title: "Deep dive" },
      { id: "a1", title: "Decisions" },
    ]);
  });
});

describe("the fetcher (real lengths, iPad defaults)", () => {
  it("prices segments/intel/artifacts from the hub's answers; digest defaults on", async () => {
    vi.stubGlobal("fetch", (url: string) => {
      if (url === "/api/meetings/m9") {
        return Promise.resolve(new Response(JSON.stringify({
          title: "Envelope proof", started_at: "2026-07-06T21:31:41",
          segments: [{ speaker: "Karol", text: "BLUE LANTERN is the codename." }],
          intel: { summary: "The codename exists.", action_items: [{ task: "Ship it" }] },
        })));
      }
      if (url === "/api/meetings/m9/artifacts") {
        return Promise.resolve(new Response(JSON.stringify({
          artifacts: [{ id: "a9", title: "Decisions", body_markdown: "- Ship the manifest." }],
        })));
      }
      return Promise.reject(new Error("unexpected " + url));
    });
    const m = await fetchGroundingMeeting("m9", "fallback");
    expect(m.title).toBe("Envelope proof");
    expect(m.day).toBe("2026-07-06");
    expect(m.hasIntel).toBe(true);
    expect(m.includeIntel).toBe(true);          // the iPad default
    expect(m.includeTranscript).toBe(false);    // transcript is opt-in
    expect(m.transcriptLines).toBe(1);
    expect(m.transcriptChars).toBeGreaterThan(30);
    expect(m.intelChars).toBeGreaterThan(20);
    expect(m.artifacts).toEqual([{ id: "a9", title: "Decisions", chars: 20, on: false }]);
  });
});

describe("runAsk carries the envelope", () => {
  it("ships grounding refs and returns the folded lineage", async () => {
    let sent: any = null;
    vi.stubGlobal("fetch", (_url: string, init: any) => {
      sent = JSON.parse(init.body);
      return Promise.resolve(new Response(JSON.stringify({
        output: "BLUE LANTERN",
        egress: { scope: "cloud", host: "192.168.1.43" },
        model: "Qwen",
        context_ids: ["m1"], context_titles: ["Q3 kickoff"],
        grounding: { meeting_ids: ["m1"], artifact_ids: [], expand: "full", titles: ["Q3 kickoff"] },
      })));
    });
    const r = await runAsk({
      prompt: "codename?", lens: "Ask", context: [],
      grounding: { meeting_ids: ["m1"], artifact_ids: [], expand: "full" },
    });
    expect(sent.grounding).toEqual({ meeting_ids: ["m1"], artifact_ids: [], expand: "full" });
    expect(r.ok).toBe(true);
    expect(r.contextIds).toEqual(["m1"]);
    expect(r.contextTitles).toEqual(["Q3 kickoff"]);
  });
  it("renders the hub's refusal verbatim, naming unknown ids", async () => {
    vi.stubGlobal("fetch", () => Promise.resolve(new Response(
      JSON.stringify({ error: "grounding ids not on this hub", unknown_ids: ["ghost"] }),
      { status: 400 },
    )));
    const r = await runAsk({
      prompt: "x", lens: "Ask", context: [],
      grounding: { meeting_ids: ["ghost"], artifact_ids: [], expand: "summary" },
    });
    expect(r.ok).toBe(false);
    expect(r.output).toBe("grounding ids not on this hub (ghost)");
  });
});
