// PG-DIRECTION DIR2 (T2): the briefing page, from the hub's recorded answers
// (web/src/briefing/__fixtures__/reach.page.json, recorded by
// tests/integration/test_desk_reach.py; HOLDSPEAK_WIRE_WRITE=1 rewrites it).
//
// A press on Go on renders the settled outcome and no verbs; Later ▾ at 13:00
// renders "Later · back at …" and keeps the choices; the expired face has no
// data; an evidence fold loads its pane when it opens. The guard: nothing
// under web/src/briefing reaches the desk's auth client (src/lib/auth.ts) or
// src/lib/api.ts, by the transitive import walk.
import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import recorded from "../__fixtures__/reach.page.json";
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
      body = url.endsWith("/brief") ? recorded.brief : url.endsWith("/log") ? recorded.log : recorded.text;
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

describe("the briefing page (direction A, the brief)", () => {
  it("reads its token from the path only", () => {
    expect(tokenFromPath(`/b/${TOKEN}`)).toBe(TOKEN);
    expect(tokenFromPath(`/b/${TOKEN}/x`)).toBe("");
    expect(tokenFromPath("/b/short")).toBe("");
  });

  it("shows the question first, each choice with what it does, and Later last", async () => {
    hub({ open: recorded.open });
    render(<BriefingApp token={TOKEN} />);
    const well = await screen.findByTestId("briefing-well");
    expect(screen.getByTestId("briefing-head").textContent).toBe(recorded.open.package.head);
    expect(within(well).getByTestId("briefing-question").textContent).toBe(recorded.open.items[0].question);
    const choices = within(well).getByTestId("briefing-choices");
    const verbs = within(choices).getAllByRole("button").map((button) => button.textContent?.trim());
    expect(verbs).toEqual(["Go on", "Park", "Later"]);
    for (const choice of recorded.open.items[0].choices) expect(choices.textContent).toContain(choice.consequence);
    expect(screen.getByTestId("briefing-status").textContent).toContain(recorded.open.package.expires_words);
    expect(screen.getByTestId("briefing-status").textContent).toContain(`from HoldSpeak on ${recorded.open.package.hub}`);
    // Every verb is the library Button.
    for (const button of screen.getAllByRole("button")) expect(button.className).toMatch(/\bbtn\b/);
  });

  it("a press on Go on settles the well: the outcome, and nothing to press", async () => {
    const calls = hub({ open: recorded.open, post: recorded.decided });
    render(<BriefingApp token={TOKEN} />);
    fireEvent.click(await screen.findByTestId("briefing-choice-go_on"));
    const outcome = await screen.findByTestId("briefing-outcome");
    expect(outcome.textContent).toBe(recorded.decided.item.outcome.words);
    expect(outcome.textContent).toMatch(/^Go on · decided here · \d\d:\d\d$/);
    expect(screen.queryByTestId("briefing-choices")).toBeNull();
    expect(within(screen.getByTestId("briefing-well")).queryAllByRole("button")).toHaveLength(0);
    const post = calls.find((call) => call.method === "POST");
    expect(post?.url).toBe(`/api/b/${TOKEN}/answer`);
    expect(post?.body).toEqual({ ref: recorded.open.items[0].ref, choice: "go_on" });
  });

  it("Later ▾ at 13:00 says when it comes back and keeps the choices", async () => {
    const calls = hub({ open: recorded.open, post: recorded.later });
    render(<BriefingApp token={TOKEN} />);
    fireEvent.click(await screen.findByTestId("briefing-later"));
    fireEvent.click(await screen.findByRole("menuitem", { name: /At 13:00/ }));
    const outcome = await screen.findByTestId("briefing-outcome");
    expect(outcome.textContent).toBe(recorded.later.item.outcome.words);
    expect(outcome.textContent).toMatch(/^Later · back at \d\d:\d\d$/);
    expect(screen.getByTestId("briefing-choices")).toBeTruthy();
    expect(calls.find((call) => call.method === "POST")?.body).toEqual({
      ref: recorded.open.items[0].ref, choice: "later", later: "at_13",
    });
  });

  it("a second answer hears answered already and reads the page again", async () => {
    hub({ open: recorded.open, post: recorded.again, postStatus: 409 });
    render(<BriefingApp token={TOKEN} />);
    fireEvent.click(await screen.findByTestId("briefing-choice-park"));
    expect((await screen.findByTestId("briefing-failure")).textContent).toBe(recorded.again.detail);
  });

  it("the expired face has no data", async () => {
    hub({ open: recorded.expired, status: 404 });
    render(<BriefingApp token={TOKEN} />);
    const face = await screen.findByTestId("briefing-expired");
    expect(face.textContent).toContain("This page has expired.");
    expect(face.textContent).toContain("Open the item on your desk.");
    expect(document.body.textContent).not.toContain(recorded.open.items[0].question);
    expect(document.body.textContent).not.toContain(recorded.open.package.head);
    expect(screen.queryAllByRole("button")).toHaveLength(0);
  });

  it("an evidence fold loads its pane when it opens, read only", async () => {
    const calls = hub({ open: recorded.open });
    render(<BriefingApp token={TOKEN} />);
    await screen.findByTestId("briefing-evidence");
    expect(calls.filter((call) => call.url.includes("/evidence/"))).toHaveLength(0);
    const fold = screen.getByText("Brief").closest("details") as HTMLDetailsElement;
    fold.open = true;
    fireEvent(fold, new Event("toggle"));
    const pane = await screen.findByTestId("briefing-pane-brief");
    await waitFor(() => expect(pane.textContent).toContain(recorded.brief.text.split("\n")[0]));
    expect(calls.some((call) => call.url === `/api/b/${TOKEN}/evidence/${encodeURIComponent(recorded.open.items[0].ref)}/brief`)).toBe(true);
    expect(within(pane).queryAllByRole("textbox")).toHaveLength(0);
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
