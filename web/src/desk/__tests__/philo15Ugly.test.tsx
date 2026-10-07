// PHILO-15 lane 12: the UGLY bounces of rehearsal 1A
// (docs/internal/philo/phase-15/rehearsal-1a/BOUNCES.md), fenced where a
// rule can be measured without a browser. The glass half (bounding boxes at
// 1440 and 393) is tests/e2e/test_philo15_12_ugly_glass.py; the Dock sprite
// fence is web/src/desk/systemSprites.test.ts.
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Material } from "../surface/Material";
import { previewOf, targetName, targetToken } from "../../features/channels/channels";
import { roomHealthWord, roomIsEmpty, type RoomSnapshot } from "../../features/project-room/model";
import { receiptLabel } from "../surface/egress";
import { nameBreaks } from "../surface/objects/DeskIcon";
import { fitName } from "../surface/objects/fitName";
import { PULLOUT_SIZE } from "../pullouts/size";

describe("B23: the Send well's folder and preview", () => {
  const target = { builtin: "documents", folder: "/private/var/folders/q7/x/T/hs-day1/Documents/HoldSpeak/Sent", display: "~/Documents/HoldSpeak/Sent" };

  it("a folder reads by its name, never a path", () => {
    expect(targetName("file", target)).toBe("HoldSpeak/Sent");
    expect(targetName("file", { folder: "/Volumes/Team/Reports" })).toBe("Team/Reports");
    // The ~ token stays for hover and for Settings ▸ Destinations.
    expect(targetToken("file", target)).toBe("~/Documents/HoldSpeak/Sent");
    // Other channels read their own token.
    expect(targetName("jira", { key: "PAY-12" })).toBe("PAY-12");
  });

  it("the preview's Folder field is the name, not the raw /private/var path", () => {
    const preview = previewOf("file", target, {}, { text: "# x" });
    const folder = preview.fields.find((f) => f.label === "Folder");
    expect(folder?.value).toBe("HoldSpeak/Sent");
    expect(JSON.stringify(preview.fields)).not.toContain("/private/var");
  });

  it("a filename's underscores are never italics", () => {
    const { container } = render(<Material>{"philo3_architect_meeting\n\nDate: 2026-10-07"}</Material>);
    expect(container.querySelector("em")).toBeNull();
    expect(container.textContent).toContain("philo3_architect_meeting");
  });

  it("an _emphasis_ between spaces still reads as emphasis", () => {
    const { container } = render(<Material>{"this is _the_ point"}</Material>);
    expect(container.querySelector("em")?.textContent).toBe("the");
  });
});

function room(overrides: Partial<Record<keyof RoomSnapshot, unknown>> = {}): RoomSnapshot {
  const ok = <T,>(data: T) => ({ state: "ok" as const, ...data });
  return {
    projectId: "p1", revision: 1, observedAt: "2026-10-07T11:06:00Z", nextCheckAt: null,
    project: { id: "p1", name: "Payments ledger cutover" },
    items: ok({ focus: [], totalsByType: {}, total: 0 }),
    meetings: ok({ count: 0, latest: null }),
    resources: ok({ count: 0, latest: null }),
    changes: { state: "absent", reason: "x" },
    review: { state: "absent", reason: "x" },
    needsYou: ok({ items: [], count: 0 }),
    sources: ok({ items: [], count: 0, nextCheckAt: null }),
    health: ok({ assessment: "on_track", reason: null, inputs: { overdue: 0, overdueMilestones: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false } }),
    sinceRead: { state: "absent", reason: "x" },
    decisions: ok({ items: [] }),
    commitments: ok({ items: [] }),
    target: ok({ targetAt: null, daysLeft: null, passed: false }),
    updates: { state: "absent", reason: "x" },
    steward: { state: "absent", reason: "x" },
    receipts: { state: "absent", reason: "x" },
    ...overrides,
  } as unknown as RoomSnapshot;
}

describe("B25: an empty Project reads NEW", () => {
  it("nothing to judge: NEW, never ON TRACK", () => {
    expect(roomIsEmpty(room())).toBe(true);
    expect(roomHealthWord(room())?.word).toBe("NEW");
  });

  it("one source, one meeting or one open item: ON TRACK", () => {
    expect(roomHealthWord(room({ sources: { state: "ok", items: [{}], count: 1, nextCheckAt: null } }))?.word).toBe("ON TRACK");
    expect(roomHealthWord(room({ meetings: { state: "ok", count: 1, latest: null } }))?.word).toBe("ON TRACK");
    expect(roomHealthWord(room({ needsYou: { state: "ok", items: [], count: 2 } }))?.word).toBe("ON TRACK");
  });

  it("AT RISK wins; an unread section is not empty; no health read, no word", () => {
    const risk = room({ health: { state: "ok", assessment: "at_risk", reason: "overdue", inputs: {} } });
    expect(roomHealthWord(risk)?.word).toBe("AT RISK");
    expect(roomIsEmpty(room({ sources: { state: "degraded", error_code: "x" } }))).toBe(false);
    expect(roomHealthWord(room({ health: { state: "degraded", error_code: "x" } }))).toBeNull();
  });

  it("the Door's create receipt reads CREATE", () => {
    expect(receiptLabel({ op: "create_from_setup" })).toBe("CREATE");
  });
});

describe("B24: the Intelligence window opens at a size that shows its first items", () => {
  it("is wide enough for its tabs on one row (they stack at a 420 px body)", () => {
    const size = PULLOUT_SIZE.intelligence;
    expect(size).toBeTruthy();
    expect(size!.w).toBeGreaterThanOrEqual(600);
    expect(size!.h).toBeGreaterThanOrEqual(560);
  });
});

describe("B30: a desk label breaks between words, and keeps its end", () => {
  // The desk label at 393 holds about 11 monospaced characters a line, two lines.
  it("breaks at spaces first; joins only inside a word that cannot fit", () => {
    expect(fitName("Use SQLite for the meeting ledger", 11, 9)).toEqual(["Use SQLite", "for the", "meeting", "ledger"]);
    // A space wins over the join inside a word that fits a line.
    expect(fitName("ledger_v2 cutover", 11, 2)).toEqual(["ledger_v2", "cutover"]);
    // A word wider than the line breaks after its joins, not inside letters.
    expect(fitName("philo3_architect_meeting", 12, 3)).toEqual(["philo3_", "architect_", "meeting"]);
  });

  it("an underscore join is where a two-line label breaks", () => {
    const set = fitName("philo3_architect_meeting", 11, 2);
    expect(set).toHaveLength(2);
    expect(set[0]).toBe("philo3_");
    expect(set[1].endsWith("meeting")).toBe(true);
    expect(set.join("")).toContain("…");
  });

  it("names that differ only at the end stay different (a middle cut)", () => {
    const v2 = fitName("Payments ledger cutover v2", 11, 2);
    const v3 = fitName("Payments ledger cutover v3", 11, 2);
    expect(v2.length).toBeLessThanOrEqual(2);
    expect(v2.join(" ")).toMatch(/…\s*v2$/);
    expect(v3.join(" ")).toMatch(/…\s*v3$/);
    expect(v2[0]).toBe("Payments");
    for (const line of [...v2, ...v3]) expect(line.length).toBeLessThanOrEqual(11);
  });

  it("an unbroken overlong word is cut with an ellipsis, never split", () => {
    const set = fitName("Supercalifragilisticexpialidocious", 11, 2);
    expect(set).toHaveLength(1);
    expect(set[0]).toContain("…");
    expect(set[0].length).toBeLessThanOrEqual(11);
    expect(set[0].startsWith("Super")).toBe(true);
    expect(set[0].endsWith("ous")).toBe(true);
  });

  it("a name that fits is untouched", () => {
    expect(fitName("Weekly update", 11, 2)).toEqual(["Weekly", "update"]);
    expect(fitName("1:1 prep", 11, 2)).toEqual(["1:1 prep"]);
  });

  it("the CSS form: one block per word, a <wbr> only after a join", () => {
    const { container } = render(<span>{nameBreaks("philo3_architect_meeting v2")}</span>);
    const words = container.querySelectorAll(".name-word");
    expect(words).toHaveLength(2);
    expect(words[0].querySelectorAll("wbr")).toHaveLength(2);
    expect(words[1].querySelectorAll("wbr")).toHaveLength(0);
    expect(container.textContent).toBe("philo3_architect_meeting v2");
  });
});
