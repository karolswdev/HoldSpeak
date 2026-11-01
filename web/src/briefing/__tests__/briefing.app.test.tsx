// PG-DIRECTION DIR2 (T2): the briefing page, from the hub's recorded answers
// (web/src/briefing/__fixtures__/reach.page.json, recorded by
// tests/integration/test_desk_reach.py; HOLDSPEAK_WIRE_WRITE=1 rewrites it).
//
// The recorded case is the owner's first real page (2026-10-31): a step
// parked because the repository has no remote. The brief reads in his terms
// in the rule's order; a press on Resume settles the page to one line; Later
// at 13:00 settles the same way; the expired face has no data; an evidence
// word opens its pane in place, loaded when it opens. The guard: nothing
// under web/src/briefing reaches the desk's auth client (src/lib/auth.ts) or
// src/lib/api.ts, by the transitive import walk.
import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import recorded from "../__fixtures__/reach.page.json";
// DIR9: one page for three held items, and the same page after two answers
// (tests/integration/test_desk_reach_digest.py, HOLDSPEAK_WIRE_WRITE=1).
import digest from "../__fixtures__/reach.digest.json";
import digestAnswered from "../__fixtures__/reach.digest.answered.json";
import { BriefingApp } from "../BriefingApp";
import { tokenFromPath } from "../api";

const TOKEN = recorded.made.token;

type Call = { url: string; method: string; body: unknown };

function hub(answers: { open?: unknown; status?: number; post?: unknown; postStatus?: number }) {
  const calls: Call[] = [];
  vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
    const method = init?.method ?? "GET";
    calls.push({ url, method, body: init?.body ? JSON.parse(String(init.body)) : null });
    expect(init?.credentials).toBe("omit");
    expect(url).not.toContain("?token=");
    let status = 200;
    let body: unknown = null;
    if (method === "POST") {
      status = answers.postStatus ?? 200;
      body = answers.post;
    } else if (url.includes("/evidence/")) {
      body = url.endsWith("/brief") ? recorded.brief : url.endsWith("/log") ? recorded.log
        : url.endsWith("/error") ? recorded.error : url.endsWith("/report") ? recorded.report : recorded.text;
    } else {
      status = answers.status ?? 200;
      body = answers.open;
    }
    return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
  }));
  return calls;
}

afterEach(() => {
  vi.unstubAllGlobals();
  document.body.innerHTML = "";
});

describe("the briefing page (the owner's BRIEF RULE, direction A)", () => {
  const shown = recorded.open.items[0];

  it("reads its token from the path only", () => {
    expect(tokenFromPath(`/b/${TOKEN}`)).toBe(TOKEN);
    expect(tokenFromPath(`/b/${TOKEN}/x`)).toBe("");
    expect(tokenFromPath("/b/short")).toBe("");
  });

  it("reads like a note: the goal, where we are, the step, what happened, then the question", async () => {
    hub({ open: recorded.open });
    render(<BriefingApp token={TOKEN} />);
    await screen.findByTestId("briefing-question");
    const text = document.body.textContent ?? "";
    const order = [shown.kind_words, recorded.open.package.head, shown.goal, shown.place, shown.doing, shown.happened,
      shown.question, shown.blocked_words].map((line) => text.indexOf(line));
    expect(order.every((at) => at >= 0)).toBe(true);
    expect(order).toEqual([...order].sort((x, y) => x - y));
    expect(screen.getByTestId("briefing-happened").textContent).toBe(
      "The step could not push its branch: this repository has no remote.");
    expect(screen.getByTestId("briefing-question").textContent).toBe("Start the step again, or stop it?");
    expect(screen.getByTestId("briefing-question").tagName).toBe("H2");
    // No raw text on the face: the git error is only in its fold.
    expect(text).not.toMatch(/fatal:|error:|\/tmp\/|sh -c/);
  });

  it("draws the step line with this step lit and the steps that wait on it marked", async () => {
    hub({ open: recorded.open });
    render(<BriefingApp token={TOKEN} />);
    const track = await screen.findByTestId("briefing-track");
    const stations = Array.from(track.querySelectorAll("li"));
    expect(stations.map((li) => li.getAttribute("data-state"))).toEqual(["current", "ahead", "ahead"]);
    expect(stations.map((li) => li.getAttribute("data-mark"))).toEqual([null, "blocked", "blocked"]);
    expect(stations[0].querySelector(".pg-station-dot")?.hasAttribute("data-live")).toBe(true);
    expect(track.getAttribute("aria-label")).toBe("Step 1 of 3, here; steps 2, 3 wait on it");
    expect(screen.getByTestId("briefing-blocked").textContent).toBe("2 steps wait on this: 2 Link the README, 3 Announce it.");
  });

  it("each choice says what it does in his terms, and Later opens its times in place", async () => {
    hub({ open: recorded.open });
    render(<BriefingApp token={TOKEN} />);
    const tray = await screen.findByTestId("briefing-choices");
    expect(within(tray).getAllByRole("button").map((button) => button.textContent?.trim())).toEqual(["Resume", "Skip", "Later"]);
    expect(tray.textContent).toContain("Try the step again. It will fail the same way until the repository has a remote.");
    expect(tray.textContent).toContain("Stop this step. The 2 steps that wait on it wait too.");
    fireEvent.click(screen.getByTestId("briefing-later"));
    const times = screen.getByTestId("briefing-times");
    expect(within(times).getAllByRole("button")).toHaveLength(4);
    expect(screen.queryByRole("menu")).toBeNull();
    // No disclosure marker anywhere.
    expect(document.body.textContent).not.toMatch(/[▸▾]/);
    for (const button of screen.getAllByRole("button")) expect(button.className).toMatch(/\bbtn\b/);
    expect(screen.getByTestId("briefing-status").textContent).toContain(recorded.open.package.expires_words);
  });

  it("a press on Resume settles the page to one line and Open on the desk", async () => {
    const calls = hub({ open: recorded.open, post: recorded.decided });
    render(<BriefingApp token={TOKEN} />);
    fireEvent.click(await screen.findByTestId("briefing-choice-resume"));
    const outcome = await screen.findByTestId("briefing-outcome");
    expect(outcome.textContent).toBe(recorded.decided.item.outcome.words);
    expect(outcome.textContent).toMatch(/^Resume · \d\d:\d\d\. The step starts again\. Nothing else waits on you\.$/);
    for (const gone of ["briefing-choices", "briefing-evidence", "briefing-changed", "briefing-question", "briefing-track"]) {
      expect(screen.queryByTestId(gone)).toBeNull();
    }
    expect(screen.getAllByRole("button").map((button) => button.textContent)).toEqual(["Open on the desk"]);
    const post = calls.find((call) => call.method === "POST");
    expect(post?.url).toBe(`/api/b/${TOKEN}/answer`);
    expect(post?.body).toEqual({ ref: shown.ref, choice: "resume" });
  });

  it("Later at 13:00 settles the same way, to its one line", async () => {
    const calls = hub({ open: recorded.open, post: recorded.later });
    render(<BriefingApp token={TOKEN} />);
    fireEvent.click(await screen.findByTestId("briefing-later"));
    fireEvent.click(screen.getByTestId("briefing-later-at_13"));
    const outcome = await screen.findByTestId("briefing-outcome");
    expect(outcome.textContent).toBe("Later · back at 13:00.");
    expect(screen.queryByTestId("briefing-choices")).toBeNull();
    expect(calls.find((call) => call.method === "POST")?.body).toEqual({ ref: shown.ref, choice: "later", later: "at_13" });
  });

  it("a second answer hears answered already and reads the page again", async () => {
    hub({ open: recorded.open, post: recorded.again, postStatus: 409 });
    render(<BriefingApp token={TOKEN} />);
    fireEvent.click(await screen.findByTestId("briefing-choice-skip"));
    expect((await screen.findByTestId("briefing-failure")).textContent).toBe(recorded.again.detail);
  });

  it("the expired face has no data", async () => {
    hub({ open: recorded.expired, status: 404 });
    render(<BriefingApp token={TOKEN} />);
    const face = await screen.findByTestId("briefing-expired");
    expect(face.textContent).toContain("This page has expired.");
    expect(face.textContent).toContain("Open the item on your desk.");
    expect(document.body.textContent).not.toContain(shown.question);
    expect(document.body.textContent).not.toContain(recorded.open.package.head);
    expect(screen.queryAllByRole("button")).toHaveLength(0);
  });

  it("the evidence is one line of words; a pane opens in place with Close", async () => {
    const calls = hub({ open: recorded.open });
    render(<BriefingApp token={TOKEN} />);
    const evidence = await screen.findByTestId("briefing-evidence");
    expect(within(evidence).getAllByRole("button").map((button) => button.textContent)).toEqual(
      ["The error", "Check log", "Brief", "Report", "Program text"]);
    expect(calls.filter((call) => call.url.includes("/evidence/"))).toHaveLength(0);
    fireEvent.click(screen.getByTestId("briefing-open-error"));
    const pane = await screen.findByTestId("briefing-pane-error");
    await waitFor(() => expect(pane.textContent).toContain("does not appear to be a git repository"));
    expect(calls.some((call) => call.url === `/api/b/${TOKEN}/evidence/${encodeURIComponent(shown.ref)}/error`)).toBe(true);
    expect(within(pane).queryAllByRole("textbox")).toHaveLength(0);
    fireEvent.click(screen.getByTestId("briefing-pane-close"));
    expect(screen.queryByTestId("briefing-pane-error")).toBeNull();
    // PG-IMPORT IMP1: Report opens the step's registers as rows, read only.
    fireEvent.click(screen.getByTestId("briefing-open-report"));
    const report = await screen.findByTestId("briefing-pane-report");
    await waitFor(() => expect(report.textContent).toContain("Checked:"));
    expect(report.textContent).toContain("Files:");
    expect(within(report).queryAllByRole("textbox")).toHaveLength(0);
  });
});

describe("the guard: the page never reaches the desk's auth client", () => {
  const web = resolve(__dirname, "../../..");
  const exts = ["", ".ts", ".tsx", "/index.ts", "/index.tsx"];
  function resolveSpec(from: string, spec: string): string | null {
    if (!spec.startsWith(".")) return null;
    const base = resolve(dirname(from), spec);
    for (const ext of exts) {
      const file = base + ext;
      if (existsSync(file) && statSync(file).isFile()) return file;
    }
    return null;
  }
  function walk(file: string, seen: Map<string, string | null>, parent: string | null) {
    if (seen.has(file)) return;
    seen.set(file, parent);
    const source = readFileSync(file, "utf8");
    const pattern = /(?:import|export)\s[^'"]*?from\s*['"]([^'"]+)['"]|import\s*\(\s*['"]([^'"]+)['"]\s*\)|import\s+['"]([^'"]+)['"]/g;
    for (let found = pattern.exec(source); found; found = pattern.exec(source)) {
      const next = resolveSpec(file, found[1] || found[2] || found[3]);
      if (next && /\.tsx?$/.test(next)) walk(next, seen, file);
    }
  }

  it("walks every import under web/src/briefing and finds neither src/lib/auth.ts nor src/lib/api.ts", () => {
    const dir = join(web, "src", "briefing");
    const roots = readdirSync(dir).filter((name) => /\.tsx?$/.test(name)).map((name) => join(dir, name));
    expect(roots.length).toBeGreaterThan(2);
    const seen = new Map<string, string | null>();
    for (const root of roots) walk(root, seen, null);
    const banned = [join(web, "src", "lib", "auth.ts"), join(web, "src", "lib", "api.ts")];
    for (const file of banned) {
      const chain: string[] = [];
      for (let at: string | null | undefined = file; at && seen.has(at); at = seen.get(at)) chain.push(at.slice(web.length + 1));
      expect(chain, `the page reaches ${file}`).toEqual([]);
    }
    expect(seen.size).toBeGreaterThan(5);
  });
});

describe("DIR9, the page half: several held items on one page", () => {
  type Item = { ref: string; state: string; outcome?: { words: string } };
  const answered = (ref: string) => (digestAnswered.items as Item[]).find((item) => item.ref === ref)!;

  it("each item is its own brief in order; a press settles that item alone", async () => {
    const decision = answered("decision:dec-1");
    const calls = hub({ open: digest, post: { item: decision } });
    render(<BriefingApp token={TOKEN} />);
    const items = await screen.findAllByTestId("briefing-item");
    expect(items.map((node) => node.getAttribute("data-ref"))).toEqual((digest.items as Item[]).map((item) => item.ref));
    expect(screen.getByTestId("briefing-open-words").textContent).toBe("3 wait on you.");
    // Each item has its own question and its own tray.
    expect(items.map((node) => within(node).getByTestId("briefing-question").textContent))
      .toEqual(digest.items.map((item) => item.question));
    const target = items.find((node) => node.getAttribute("data-ref") === "decision:dec-1")!;
    const confirm = within(target).getAllByRole("button").find((button) => button.textContent === "Confirm")!;
    fireEvent.click(confirm);
    await waitFor(() => expect(within(target).getByTestId("briefing-outcome").textContent).toBe(decision.outcome!.words));
    const posted = calls.find((call) => call.method === "POST");
    expect((posted!.body as { ref: string }).ref).toBe("decision:dec-1");
    // The others stay as they were, each with its tray; the head counts what waits.
    const others = screen.getAllByTestId("briefing-item").filter((node) => node.getAttribute("data-ref") !== "decision:dec-1");
    for (const node of others) expect(within(node).getByTestId("briefing-choices")).toBeTruthy();
    expect(screen.getByTestId("briefing-open-words").textContent).toBe("2 wait on you.");
  });

  it("a page read after two answers shows them settled and one open", async () => {
    hub({ open: digestAnswered });
    render(<BriefingApp token={TOKEN} />);
    const items = await screen.findAllByTestId("briefing-item");
    expect(items.map((node) => node.getAttribute("data-state"))).toEqual((digestAnswered.items as Item[]).map((item) => item.state));
    expect(screen.getByTestId("briefing-open-words").textContent).toBe("1 waits on you.");
    expect(screen.getAllByTestId("briefing-choices")).toHaveLength(1);
  });
});

// PG-LANG JRN9 to JRN11: an audit's File the findings, its Make, and a lesson
// on the page (tests/integration/test_reach_audit_rows.py, HOLDSPEAK_WIRE_WRITE=1).
import audit from "../__fixtures__/reach.audit.json";
import lesson from "../__fixtures__/reach.lesson.json";

describe("the audit and lesson rows on the page (JRN9 to JRN11)", () => {
  it("File the findings: the question, its two choices in his terms; File settles the page to one line", async () => {
    const calls = hub({ open: audit.open, post: audit.filed });
    render(<BriefingApp token={audit.made.token} />);
    expect((await screen.findByTestId("briefing-question")).textContent).toBe("File the findings as Door tasks?");
    const tray = screen.getByTestId("briefing-choices");
    expect(within(tray).getAllByRole("button").map((button) => button.textContent?.trim())).toEqual(["File", "Skip", "Later"]);
    expect(tray.textContent).toContain("Each finding becomes a Door task.");
    expect(document.body.textContent).toContain("Audit findings");
    fireEvent.click(screen.getByTestId("briefing-choice-file"));
    const outcome = await screen.findByTestId("briefing-outcome");
    expect(outcome.textContent).toBe(audit.filed.item.outcome.words);
    expect(screen.queryByTestId("briefing-choices")).toBeNull();
    const post = calls.find((call) => call.method === "POST");
    expect(post?.body).toEqual({ ref: audit.open.items[0].ref, choice: "file" });
  });

  it("a lesson: Keep for this program · Keep for HoldSpeak · Skip; the press settles in place", async () => {
    const calls = hub({ open: lesson.open, post: lesson.kept });
    render(<BriefingApp token={lesson.made.token} />);
    expect((await screen.findByTestId("briefing-question")).textContent).toBe("Keep this lesson, and where?");
    const tray = screen.getByTestId("briefing-choices");
    expect(within(tray).getAllByRole("button").map((button) => button.textContent?.trim()))
      .toEqual(["Keep for this program", "Keep for HoldSpeak", "Skip", "Later"]);
    fireEvent.click(screen.getByTestId("briefing-choice-keep_program"));
    expect((await screen.findByTestId("briefing-outcome")).textContent).toBe(lesson.kept.item.outcome.words);
    expect(calls.find((call) => call.method === "POST")?.body).toEqual({ ref: lesson.open.items[0].ref, choice: "keep_program" });
  });
});
