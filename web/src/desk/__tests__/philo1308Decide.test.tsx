/** PHILO-13-08 (B3) — decide where the meeting is.
 *
 * - `New Decision` (⌘K, ⌘⇧N, the floor menu) writes nothing until the
 *   decision has a title; the palette asks it inline; an abandoned try
 *   writes nothing (grounding F9: each try left a `New decision` record).
 * - The meeting record's `Decide` asks the title inline and creates ONE
 *   decision carrying the meeting and the meeting's project; the meeting
 *   then lists it, and the row opens its own window.
 * Real store slice, real palette and well; the hub transport is the double. */
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const hub = vi.hoisted(() => ({
  decisions: [] as Array<Record<string, unknown>>,
  posts: [] as Array<Record<string, unknown>>,
  resourcePuts: [] as string[],
  projects: [{ project_id: "proj-1", project_name: "Checkout" }] as Array<Record<string, unknown>>,
}));

function decisionWire(body: Record<string, unknown>, n: number) {
  return {
    id: `decision_${n}`, title: body.title, status: body.status ?? "proposed", deciders: [],
    decided_at: null, context_markdown: body.context_markdown ?? "", decision_markdown: "",
    alternatives: [], consequences_markdown: "", tags: body.tags ?? [],
    created_at: `2026-10-02T00:00:0${n}Z`, updated_at: "2026-10-02T00:00:00Z", deleted: false,
  };
}

vi.mock("../../lib/api", async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>();
  const post = (raw: unknown) => {
    const body = JSON.parse(String(raw ?? "{}")) as Record<string, unknown>;
    hub.posts.push(body);
    const decision = decisionWire(body, hub.posts.length);
    hub.decisions = [...hub.decisions, decision];
    return decision;
  };
  return {
    ...real,
    apiRequest: vi.fn((url: string, init?: RequestInit) => {
      if (url === "/api/decisions" && init?.method === "POST") {
        const decision = post(init.body);
        return Promise.resolve({ ok: true, status: 201, json: () => Promise.resolve({ decision }) });
      }
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) });
    }),
    apiFetch: vi.fn((url: string, init?: RequestInit & { json?: unknown }) => {
      if (url === "/api/decisions" && init?.method === "POST")
        return Promise.resolve({ decision: post(init.body) });
      if (url === "/api/decisions") return Promise.resolve({ decisions: hub.decisions });
      if (/^\/api\/meetings\/[^/]+\/projects$/.test(url))
        return Promise.resolve({ projects: hub.projects });
      if (url.startsWith("/api/projects/") && init?.method === "PUT") {
        hub.resourcePuts.push(decodeURIComponent(url));
        return Promise.resolve({ resource: {} });
      }
      return Promise.resolve({});
    }),
  };
});
vi.mock("../setup", () => ({ loadSetup: vi.fn(() => Promise.resolve(null)) }));

import { useDesk } from "../store";
import { useNamePrompt, usePalette } from "../chromeState";
import { DeskToolShelf } from "../components/DeskToolShelf";
import { MeetingDecideWell } from "../../meetings/MeetingDecideWell";
import { VERBS } from "../verbRegistry";

beforeEach(() => {
  hub.decisions = [];
  hub.posts = [];
  hub.resourcePuts = [];
  hub.projects = [{ project_id: "proj-1", project_name: "Checkout" }];
  useNamePrompt.getState().clear();
  usePalette.getState().setOpen(false);
  useDesk.setState({ pullouts: [], editingId: null, newIds: [] });
});

const newDecision = () => VERBS.find((v) => v.id === "desk.new-decision")!;

describe("PHILO-13-08 New Decision writes nothing before it is named", () => {
  it("the verb asks the title in the palette and posts nothing", async () => {
    await act(async () => { newDecision().run({ selectedRef: null }); });
    expect(hub.posts).toEqual([]);
    expect(useNamePrompt.getState().prompt?.label).toBe("Decision title");
    expect(usePalette.getState().open).toBe(true);
  });

  it("an abandoned try (the palette closes) leaves no record", async () => {
    render(<DeskToolShelf />);
    await act(async () => { newDecision().run({ selectedRef: null }); });
    const well = screen.getByRole("textbox", { name: "Decision title" });
    fireEvent.change(well, { target: { value: "Half a thought" } });
    await act(async () => { usePalette.getState().setOpen(false); });
    expect(useNamePrompt.getState().prompt).toBeNull();
    expect(hub.posts).toEqual([]);
    expect(hub.decisions.filter((d) => d.title === "New decision")).toEqual([]);
  });

  it("type + Enter creates one decision with that title and opens it", async () => {
    render(<DeskToolShelf />);
    await act(async () => { newDecision().run({ selectedRef: null }); });
    const well = screen.getByRole("textbox", { name: "Decision title" });
    fireEvent.change(well, { target: { value: "Adopt feature flags" } });
    await act(async () => { fireEvent.keyDown(well, { key: "Enter" }); });
    await waitFor(() => expect(hub.posts).toHaveLength(1));
    expect(hub.posts[0].title).toBe("Adopt feature flags");
    await waitFor(() => expect(useDesk.getState().pullouts.map((p) => p.id)).toContain("decision_1"));
    expect(usePalette.getState().open).toBe(false);
  });

  it("Enter with no title writes nothing", async () => {
    render(<DeskToolShelf />);
    await act(async () => { newDecision().run({ selectedRef: null }); });
    const well = screen.getByRole("textbox", { name: "Decision title" });
    await act(async () => { fireEvent.keyDown(well, { key: "Enter" }); });
    expect(hub.posts).toEqual([]);
    expect(useNamePrompt.getState().prompt).not.toBeNull();
  });
});

describe("PHILO-13-08 Decide in the meeting record", () => {
  const well = () =>
    render(
      <MeetingDecideWell meetingId="m-42" title="Checkout latency review"
        startedAt="2026-10-01T09:00:00" summary="p99 doubled after the cache change." />,
    );

  it("Decide, type + Enter: one decision with the meeting and its project", async () => {
    well();
    fireEvent.click(screen.getByRole("button", { name: "Decide" }));
    const title = screen.getByRole("textbox", { name: "Decision title" });
    fireEvent.change(title, { target: { value: "Roll back the cache change" } });
    await act(async () => { fireEvent.keyDown(title, { key: "Enter" }); });
    await waitFor(() => expect(hub.posts).toHaveLength(1));
    const body = hub.posts[0];
    expect(body.title).toBe("Roll back the cache change");
    expect(body.tags).toEqual(["meeting:m-42", "project:proj-1"]);
    expect(String(body.context_markdown)).toContain("Meeting: Checkout latency review · 2026-10-01");
    expect(String(body.context_markdown)).toContain("p99 doubled");
    await waitFor(() => expect(hub.resourcePuts).toEqual(["/api/projects/proj-1/resources/decision:decision_1"]));
    // the receipt is where the click happened: the meeting lists it
    await waitFor(() => expect(screen.getByTestId("decide-receipt").textContent).toMatch(/^✓ DECIDED \d\d:\d\d$/));
    expect(screen.getByText("Roll back the cache change")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Decide" })).toBeTruthy();
  });

  it("a meeting with no project still decides; no project tag, no edge", async () => {
    hub.projects = [];
    well();
    fireEvent.click(screen.getByRole("button", { name: "Decide" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Decision title" }), { target: { value: "Ship it" } });
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Save" })); });
    await waitFor(() => expect(hub.posts).toHaveLength(1));
    expect(hub.posts[0].tags).toEqual(["meeting:m-42"]);
    expect(hub.resourcePuts).toEqual([]);
  });

  it("Cancel abandons: nothing is written", async () => {
    well();
    fireEvent.click(screen.getByRole("button", { name: "Decide" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Decision title" }), { target: { value: "Maybe" } });
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(hub.posts).toEqual([]);
    expect(screen.queryByRole("textbox", { name: "Decision title" })).toBeNull();
  });

  it("Save stays off until the title has words", () => {
    well();
    fireEvent.click(screen.getByRole("button", { name: "Decide" }));
    expect((screen.getByRole("button", { name: "Save" }) as HTMLButtonElement).disabled).toBe(true);
  });
});
