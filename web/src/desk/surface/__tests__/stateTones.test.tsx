// The language, 2026-11-08: one table of state words and their meaning
// colours. A face that passes another tone for a state word gets the table's.
import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { DotWord, stateTone } from "..";

describe("STATE_TONES", () => {
  it.each([
    ["At risk", "fail"],
    ["At risk: the API is late", "fail"],
    ["Blocked", "fail"],
    ["Late", "fail"],
    ["Overdue 3 Nov", "fail"],
    ["Done", "ok"],
    ["Done · checked by you", "ok"],
    ["On track", "ok"],
    ["Parked", "parked"],
    ["Parked 2 at 10:00", "parked"],
    ["Waits on you", "ask"],
    ["Your turn", "ask"],
    // The language in every window (2026-11-08): the quiet states are graphite (warn), never brass.
    ["To review", "warn"],
    ["To decide", "warn"],
    ["Unassigned", "warn"],
    ["No engine for answers", "warn"],
    ["Not set", "warn"],
    ["Your name is not set", "warn"],
    ["Stale", "warn"],
    ["Offline", "warn"],
  ])("%s → %s", (word, tone) => {
    expect(stateTone(word)).toBe(tone);
  });

  it("does not read a longer word as a state word", () => {
    expect(stateTone("Later")).toBeUndefined();
    expect(stateTone("Doneness")).toBeUndefined();
    expect(stateTone("Unassignedness")).toBeUndefined();
  });

  it("DotWord draws a state word in the table's tone, whatever the face passed", () => {
    const { container } = render(
      <>
        <DotWord tone="warn">At risk</DotWord>
        <DotWord tone="info">Done</DotWord>
        <DotWord tone="ask">Parked</DotWord>
        <DotWord tone="warn">Offline</DotWord>
      </>,
    );
    const tones = [...container.querySelectorAll(".kit-dotword")].map((el) => el.getAttribute("data-tone"));
    expect(tones).toEqual(["fail", "ok", "parked", "warn"]);
  });
});
