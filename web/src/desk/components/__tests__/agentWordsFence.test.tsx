// Phase 16 fence — every surface that prints an agent's words draws them
// with AgentWords: no literal `**`, no literal backtick pair, no literal
// `1. ` marker when the input is markdown; HTML stays text; a link is no
// anchor; a compact line never ends inside a word.
// Canvas: docs/internal/philo/phase-16/02-canvas/agent-words.html.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("../MicButton", () => ({ MicButton: () => <span data-testid="mic" /> }));

import { AskWell } from "../../surface/objects/AskWell";
import { TimelineRail } from "../../surface/objects/Timeline";
import { NeedsRow } from "../../surface/objects/NeedsRow";
import { eventEntries } from "../../lane/laneWire";
import { sentHead } from "../../lane/LaneWindow";
import { agentWordsPlain, cutAtWord } from "../AgentWords";
import { BRIEF_HEAD, OWNER_TEXT, noLiteralMarks } from "./fixtures.agentWords";

const HOSTILE = 'Run **this** <img src=x onerror="alert(1)"> [here](https://evil.example/x)';

describe("the agent-words surfaces render markdown", () => {
  it("the ask well (lane, the owner's text)", () => {
    const { container } = render(
      <AskWell agent="pi" question={OWNER_TEXT} value="" onChange={() => {}} onAnswer={() => {}} data-testid="ask" />,
    );
    const q = container.querySelector(".ask-well-question") as HTMLElement;
    noLiteralMarks(q.textContent ?? "");
    expect(q.querySelector("ol")).not.toBeNull();
  });

  it("the ask well: HTML is text, a link is no anchor", () => {
    const { container } = render(
      <AskWell agent="pi" question={HOSTILE} value="" onChange={() => {}} onAnswer={() => {}} />,
    );
    const q = container.querySelector(".ask-well-question") as HTMLElement;
    expect(q.querySelector("img,a")).toBeNull();
    expect(q.textContent).toContain('<img src=x onerror="alert(1)">');
    expect(q.textContent).toContain("https://evil.example/x");
  });

  it("the rail: SAYS whole, ASKS one line", () => {
    const entries = eventEntries([
      { id: 1, ts: "2026-10-08T21:46:00Z", event: "UserPromptSubmit", text: "brief" },
      { id: 2, ts: "2026-10-08T21:51:00Z", event: "Stop", text: OWNER_TEXT },
    ] as never);
    const { container } = render(
      <TimelineRail
        label="Lane"
        entries={[
          ...entries.map(({ at: _at, kind: _kind, heads: _heads, gated: _gated, ...rest }) => rest),
          { word: "ASKS", words: OWNER_TEXT, wordsCompact: true },
          { word: "SAYS", words: HOSTILE },
        ]}
      />,
    );
    const rail = container.querySelector("ol.lane-rail") as HTMLElement;
    noLiteralMarks(rail.textContent ?? "");
    expect(rail.querySelector(".lane-rail-says ol")).not.toBeNull();
    expect(rail.querySelector(".lane-rail-words-line.is-compact")).not.toBeNull();
    expect(rail.querySelector("a,img")).toBeNull();
  });

  it("the Needs row (ASKS): compact, two lines", () => {
    const { container } = render(
      <ul>
        <NeedsRow id="coder:pi:1" kind="agent" name="pi: Write NOTES.md" fact={OWNER_TEXT} factWords kindWord="AGENT"
          lamp={{ label: "ASKS · 1 MIN", tone: "ask" }} />
      </ul>,
    );
    const fact = container.querySelector(".needs-row-words") as HTMLElement;
    expect(fact.classList.contains("is-compact")).toBe(true);
    expect(fact.getAttribute("data-lines")).toBe("2");
    noLiteralMarks(fact.textContent ?? "");
  });

  it("THE ASK leads every compact row: steps then a question -> the row starts with the question", () => {
    const steps = "Done so far:\n\n1. **Read** the plan\n2. Ran `pytest -q`\n\n**Shall I push `hs/x` now?**";
    const { container } = render(
      <>
        <ul>
          <NeedsRow id="coder:pi:2" kind="agent" name="pi" fact={steps} factWords lamp={{ label: "ASKS", tone: "ask" }} />
        </ul>
        <TimelineRail label="Lane" entries={[{ word: "ASKS", words: steps, wordsCompact: true }]} />
      </>,
    );
    for (const sel of [".needs-row-words", ".lane-rail-words-line"]) {
      const text = container.querySelector(sel)?.textContent ?? "";
      expect(text.startsWith("Shall I push hs/x now?"), `${sel}: ${text}`).toBe(true);
      noLiteralMarks(text);
    }
    // The tooltip (Mission Control) leads with the ask too.
    expect(agentWordsPlain(steps)).toBe("Shall I push hs/x now?");
    expect(agentWordsPlain(OWNER_TEXT).startsWith("May I open a pull request for branch hs/project_item-")).toBe(true);
  });

  it("the SENT line: a cut head ends at a whole word, never `. P`", () => {
    const head = sentHead(BRIEF_HEAD);
    expect(head.endsWith('line". …')).toBe(true);
    expect(head).not.toMatch(/\sP$/);
    // A head shorter than the hub's 120 characters is whole.
    expect(sentHead("Not yet.")).toBe("Not yet.");
  });

  // The PLAIN cut (a tooltip, `agentWordsPlain`). The RENDERED compact cut
  // is measured in a real browser at 393, one line and two lines:
  // tests/e2e/test_phase16_agent_words_glass.py::test_a_compact_line_at_393_keeps_its_ellipsis_in_the_box
  // (jsdom has no layout; Astra r1 on #1026).
  it("the plain cut (tooltip) never ends inside a word", () => {
    for (const max of [20, 37, 64, 101, 150]) {
      const out = cutAtWord(OWNER_TEXT, max);
      const kept = out.replace(/ …$/, "");
      const flat = OWNER_TEXT.replace(/\s+/g, " ");
      expect(flat.startsWith(kept)).toBe(true);
      expect([" ", undefined]).toContain(flat[kept.length]);
    }
  });
});

describe("the agent-words sites use AgentWords (source fence)", () => {
  const SRC = join(__dirname, "..", "..", "..");
  const SITES: Array<[string, RegExp]> = [
    ["desk/surface/objects/AskWell.tsx", /<AgentWords className="ask-well-question" text=\{question\}/],
    ["desk/surface/objects/Timeline.tsx", /<AgentWords className="lane-rail-says"/],
    ["desk/surface/objects/NeedsRow.tsx", /<AgentWords compact lines=\{2\}/],
    ["desk/lane/LaneWindow.tsx", /<AgentWords className="lw-ask-q"/],
    ["desk/lane/laneWire.ts", /kind: "says", word: "SAYS", words: event\.text/],
    ["desk/needs/needsFace.ts", /factWords: true/],
    ["desk/chair/ChairHome.tsx", /<AgentWords compact data-testid="arrival-coder-question"/],
    ["desk/pullouts/CoderPullout.tsx", /<AgentWords className="desk-coder-question"/],
    ["desk/components/SessionPullout.tsx", /<AgentWords className="desk-session-question"/],
    ["desk/components/MissionControlConveyor.tsx", /agentWordsPlain\(s\.lastAssistantText/],
    ["pages/cores/CompanionCore.tsx", /<AgentWords compact text=/],
  ];
  it.each(SITES)("%s draws the agent's words with AgentWords", (file, pattern) => {
    expect(readFileSync(join(SRC, file), "utf8")).toMatch(pattern);
  });

  it("AgentWords never injects HTML and never makes an anchor", () => {
    const src = readFileSync(join(SRC, "desk/components/AgentWords.tsx"), "utf8");
    expect(src).not.toMatch(/dangerouslySetInnerHTML|innerHTML|<a\b/);
  });
});
