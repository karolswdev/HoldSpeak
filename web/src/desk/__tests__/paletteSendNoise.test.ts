// STATUS: "the palette shows noise rows for 'send'". The scattered-letter
// match ran across the words of a label, so `send` found "Close window"
// (s-e in close, n-d in window), "Overview · No window open" and more.
// It stays inside one word now (`mgs` still finds Meetings).
import { describe, expect, it } from "vitest";
import { fuzzyScore, rankRow } from "../components/DeskToolShelf";

describe("the palette's loose match stays inside one word", () => {
  it("does not match letters spread over several words", () => {
    expect(fuzzyScore("send", "Close window")).toBe(0);
    expect(fuzzyScore("send", "Search relevance")).toBe(0);
    expect(rankRow({ label: "Close window", terms: "window close" }, "send", false)).toBe(0);
  });

  it("keeps the in-word abbreviation and every word match", () => {
    expect(fuzzyScore("mgs", "Meetings")).toBe(30);
    expect(fuzzyScore("send", "Send to Team folder")).toBe(80);
    expect(fuzzyScore("send", "Brief send")).toBe(60);
    expect(fuzzyScore("send", "Resend")).toBe(30);
  });
});

describe("a query of several words still matches word by word", () => {
  it("finds a label whose words start with the query's words", () => {
    expect(fuzzyScore("payments cutover", "Payments ledger cutover")).toBe(55);
    expect(fuzzyScore("holdspeak roadmap", "HoldSpeak — Roadmap")).toBe(55);
    expect(fuzzyScore("pay cut", "Payments ledger cutover")).toBe(55);
  });
});
