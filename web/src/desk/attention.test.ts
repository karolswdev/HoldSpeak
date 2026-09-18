// HS-200-15 — the browser's ranking, dedup and reason token mirror
// `holdspeak/services/attention_ranking.py`: the same five classes, the
// same within-class orders, the same tie-break, the same dedup key.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  ATTENTION_CAP,
  RANK_CLASSES,
  ageToken,
  attentionCaption,
  classify,
  dedupAttention,
  normalizeTitle,
  observedAtToken,
  projectionRef,
  rankAndDedup,
  rankAttention,
  reasonToken,
  type RankableItem,
} from "./attention";

const NOW = new Date(2026, 8, 7, 9, 12, 0); // Mon 2026-09-07 09:12 local

function item(id: string, extra: Partial<RankableItem> = {}): RankableItem {
  return {
    id,
    projectId: "p1",
    title: id,
    why: "",
    severity: "info",
    source: "github",
    ...extra,
  };
}

describe("ranking (AC2)", () => {
  it("has the five classes in the ratified order and a cap of five", () => {
    expect(RANK_CLASSES).toEqual(["overdue", "due_today", "not_run", "no_due_date", "waiting"]);
    expect(ATTENTION_CAP).toBe(5);
  });

  it("ranks overdue, due today, not run, no due date, waiting — severity never reorders", () => {
    const ranked = rankAttention([
      item("w", { why: "WAITING ON YOUR REVIEW · 3d", since: "2026-09-04T09:00:00", severity: "danger" }),
      item("n", { why: "CI RED", since: "2026-09-07T08:32:00", severity: "danger" }),
      item("r", { why: "NOT RUN", since: "2026-09-05T09:00:00" }),
      item("t", { why: "DUE TODAY", dueAt: "2026-09-07T17:00:00" }),
      item("o", { why: "OVERDUE", dueAt: "2026-09-05", severity: "info" }),
    ], NOW);
    expect(ranked.map((r) => r.id)).toEqual(["o", "t", "r", "n", "w"]);
    expect(ranked.map((r) => r.rankClass)).toEqual(RANK_CLASSES);
  });

  it("orders within each class by the ratified observable time", () => {
    const ids = (rows: RankableItem[]) => rankAttention(rows, NOW).map((r) => r.id);
    expect(ids([item("a", { dueAt: "2026-09-06" }), item("b", { dueAt: "2026-09-03" })])).toEqual(["b", "a"]);
    expect(ids([item("a", { dueAt: "2026-09-07T16:00" }), item("b", { dueAt: "2026-09-07T10:00" })])).toEqual(["b", "a"]);
    expect(ids([item("a", { why: "NOT RUN", since: "2026-09-06T09:00" }), item("b", { why: "NOT RUN", since: "2026-09-02T09:00" })])).toEqual(["b", "a"]);
    expect(ids([item("a", { why: "CI RED", since: "2026-09-06T09:00" }), item("b", { why: "CI RED", since: "2026-09-07T08:32" })])).toEqual(["b", "a"]);
    expect(ids([item("a", { why: "WAITING", since: "2026-09-06T09:00" }), item("b", { why: "WAITING", since: "2026-09-04T09:00" })])).toEqual(["b", "a"]);
  });

  it("tie-breaks on the stable id, deterministically", () => {
    const rows = ["c", "a", "b"].map((id) => item(id, { why: "CI RED", since: "2026-09-07T08:00" }));
    expect(rankAttention(rows, NOW).map((r) => r.id)).toEqual(["a", "b", "c"]);
    expect(rankAttention([...rows].reverse(), NOW).map((r) => r.id)).toEqual(["a", "b", "c"]);
  });

  it("trusts the wire's class when lawful and reads the facts otherwise", () => {
    expect(classify(item("x", { why: "WAITING", dueAt: "2026-09-06" }), NOW)).toBe("overdue");
    expect(rankAttention([item("x", { rankClass: "not_run", why: "CI RED" })], NOW)[0].rankClass).toBe("not_run");
    expect(rankAttention([item("x", { rankClass: "bogus", why: "CI RED" })], NOW)[0].rankClass).toBe("no_due_date");
  });

  it("sorts an unknown time last in its class", () => {
    const ranked = rankAttention([
      item("unknown", { why: "WAITING" }),
      item("known", { why: "WAITING", since: "2026-09-01T09:00" }),
    ], NOW);
    expect(ranked.map((r) => r.id)).toEqual(["known", "unknown"]);
  });
});

describe("dedup (AC3)", () => {
  it("collapses three projections of one obligation into one traceable row", () => {
    const rows = dedupAttention([
      item("proposal:abc", { title: "Payments cut-over runbook", why: "PROPOSED · Standup", source: "proposal", since: "2026-09-06T11:31" }),
      item("p1:cmt", { title: "payments  cut-over runbook", why: "WAITING ON PRIYA", source: "commitment", since: "2026-09-04T09:00" }),
      item("p1:jira:KAN-7", { title: "KAN-7 Payments cut-over runbook", why: "OVERDUE · 2 DAYS", dueAt: "2026-09-05", source: "jira", severity: "danger" }),
    ], NOW);
    expect(rows).toHaveLength(1);
    expect(rows[0].id).toBe("p1:jira:KAN-7");
    expect(rows[0].dedupCount).toBe(3);
    expect(rows[0].sources?.map((s) => s.source)).toEqual(["jira", "proposal", "commitment"]);
    expect(rows[0].severity).toBe("danger");
  });

  it("keeps the same title in two Projects as two obligations", () => {
    expect(dedupAttention([
      item("a", { title: "CI failing on main", projectId: "p1" }),
      item("b", { title: "CI failing on main", projectId: "p2" }),
    ], NOW)).toHaveLength(2);
  });

  it("joins a Door card to the one Project that names the same thing", () => {
    const rows = dedupAttention([
      item("door:1", { title: "Priya confirms the freeze window", projectId: "", why: "OVERDUE · 1D", source: "action_item" }),
      item("p1:cmt", { title: "Priya confirms the freeze window", why: "DUE TODAY", dueAt: "2026-09-07", source: "commitment" }),
    ], NOW);
    expect(rows).toHaveLength(1);
    expect(rows[0].dedupCount).toBe(2);
  });

  it("counsel probe 1: distinct obligations with one title and one source never merge", () => {
    const rows = dedupAttention([
      item("p1:jira:KAN-7", { title: "KAN-7 Rotate the staging credentials", why: "OVERDUE · 2 DAYS", dueAt: "2026-09-05", source: "jira", severity: "danger" }),
      item("p1:jira:KAN-12", { title: "KAN-12 Rotate the staging credentials", why: "OVERDUE · 1 DAYS", dueAt: "2026-09-06", source: "jira", severity: "danger" }),
      item("p1:github:612", { title: "#612 Fix flaky test", why: "WAITING ON YOUR REVIEW · 3d", since: "2026-09-04T09:00", source: "github" }),
      item("p1:github:640", { title: "#640 Fix flaky test", why: "WAITING ON YOUR REVIEW · 1d", since: "2026-09-06T09:00", source: "github" }),
    ], NOW);
    expect(rows.map((r) => r.id)).toEqual(["p1:jira:KAN-7", "p1:jira:KAN-12", "p1:github:612", "p1:github:640"]);
    expect(rows.every((r) => r.dedupCount === 1)).toBe(true);
  });

  it("the true cross-source case is one row whose sources each keep their title and way in", () => {
    const rows = dedupAttention([
      item("p1:jira:KAN-7", { title: "KAN-7 Rotate the staging credentials", why: "OVERDUE · 2 DAYS", dueAt: "2026-09-05", source: "jira", severity: "danger", verbHref: "https://jira/KAN-7" } as never),
      item("p1:jira:KAN-12", { title: "KAN-12 Rotate the staging credentials", why: "OVERDUE · 1 DAYS", dueAt: "2026-09-06", source: "jira", severity: "danger" }),
      item("proposal:1", { title: "Rotate the staging credentials", why: "PROPOSED · STANDUP", since: "2026-09-06T11:40", source: "proposal" }),
    ], NOW);
    expect(rows.map((r) => r.id)).toEqual(["p1:jira:KAN-7", "p1:jira:KAN-12"]);
    expect(rows[0].sources?.map((s) => [s.source, s.title, s.verbHref])).toEqual([
      ["jira", "KAN-7 Rotate the staging credentials", "https://jira/KAN-7"],
      ["proposal", "Rotate the staging credentials", null],
    ]);
    expect(projectionRef(item("x", { title: "KAN-7 Runbook" }))).toBe("KAN-7");
    expect(projectionRef(item("x", { title: "Runbook" }))).toBe("");
  });

  it("the shared fixture ranks and groups exactly as the Python side does", () => {
    const fx = JSON.parse(readFileSync(resolve(__dirname, "../../../tests/fixtures/attention_ranking.json"), "utf8"));
    const now = new Date(fx.now);
    const rows = rankAndDedup(fx.items as RankableItem[], now);
    expect(rows.map((r) => r.id)).toEqual(fx.expected_order);
    const groups = Object.fromEntries(rows.map((r) => [r.id, r.sources?.map((s) => s.id)]));
    expect(groups).toEqual(fx.expected_groups);
    for (const [raw, expected] of Object.entries(fx.normalize as Record<string, string>)) {
      expect(normalizeTitle(raw)).toBe(expected);
    }
  });

  it("keeps the wire's own sources when merging a row that arrived merged", () => {
    const merged = item("p1:jira:K", {
      title: "KAN-7 Runbook",
      sources: [
        { id: "p1:jira:K", source: "jira", why: "OVERDUE" },
        { id: "proposal:1", source: "proposal", why: "PROPOSED" },
      ],
      dedupCount: 2,
    });
    const door = item("door:9", { title: "Runbook", projectId: "", source: "action_item" });
    const [row] = dedupAttention([merged, door], NOW);
    expect(row.dedupCount).toBe(3);
  });

  it("normalises a leading ref, case and spacing", () => {
    expect(normalizeTitle("KAN-7 Payments cut-over runbook")).toBe("payments cut-over runbook");
    expect(normalizeTitle("#612 Rig  settles")).toBe("rig settles");
  });
});

describe("the tokens the face draws", () => {
  it("reason token: the class, the source's detail, the observable age", () => {
    expect(reasonToken(item("o", { why: "OVERDUE · 2 DAYS", dueAt: "2026-09-05" }), NOW)).toBe("OVERDUE · 2 DAYS");
    expect(reasonToken(item("t", { why: "DUE TODAY", dueAt: "2026-09-07" }), NOW)).toBe("DUE TODAY");
    expect(reasonToken(item("r", { why: "NOT RUN", since: "2026-09-05T09:00" }), NOW)).toBe("NOT RUN · 2 DAYS");
    expect(reasonToken(item("n", { why: "CI RED", since: "2026-09-07T08:32" }), NOW)).toBe("NO DUE DATE · CI RED · CHANGED 40 MIN AGO");
    expect(reasonToken(item("w", { why: "WAITING ON YOUR REVIEW · 3d", since: "2026-09-04T09:00" }), NOW)).toBe("WAITING ON YOUR REVIEW · 3 DAYS");
    expect(reasonToken(item("w2", { why: "WAITING", since: "2026-09-04T09:00" }), NOW)).toBe("WAITING · 3 DAYS");
    expect(reasonToken(item("p", { why: "PROPOSED · Standup", since: "2026-09-07T09:00" }), NOW)).toBe("NO DUE DATE · PROPOSED · STANDUP · CHANGED 12 MIN AGO");
  });

  it("ages and observation stamps", () => {
    expect(ageToken("2026-09-07T08:32", NOW)).toBe("40 MIN");
    expect(ageToken("2026-09-07T06:00", NOW)).toBe("3 H");
    expect(ageToken("2026-09-06T09:00", NOW)).toBe("1 DAY");
    expect(ageToken("2026-09-04T09:00", NOW)).toBe("3 DAYS");
    expect(ageToken("", NOW)).toBe("");
    expect(observedAtToken("2026-09-07T08:41", NOW)).toBe("OBSERVED 08:41");
    expect(observedAtToken("2026-09-06T08:41", NOW)).toBe("OBSERVED 09-06 08:41");
    expect(observedAtToken(null, NOW)).toBe("NEVER OBSERVED");
  });

  it("caption: the cap in the caption, never a zero", () => {
    expect(attentionCaption(5, 17)).toBe("NEEDS YOU 5 OF 17");
    expect(attentionCaption(3, 3)).toBe("NEEDS YOU 3");
    expect(attentionCaption(0, 0)).toBe("NEEDS YOU");
    expect(attentionCaption(2, 2, "MUTED")).toBe("MUTED 2");
  });
});
