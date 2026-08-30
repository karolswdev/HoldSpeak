import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PeopleCore } from "../PeopleCore";

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

function stub(handlers: Record<string, (input: string, opts?: { method?: string; body?: string }) => Response | Promise<Response>>) {
  vi.stubGlobal("fetch", vi.fn(async (input: string, opts?: { method?: string; body?: string }) => {
    const handler = handlers[String(input)];
    if (!handler) throw new Error(`Unexpected request: ${String(input)}`);
    return handler(input, opts);
  }));
}

afterEach(() => vi.unstubAllGlobals());

describe("PeopleCore encrypted local plane", () => {
  it("names an unconfigured store with the joy pattern leading with the act", async () => {
    stub({ "/api/people/readiness": () => json({ readiness: "unconfigured" }) });
    render(<PeopleCore />);
    expect(await screen.findByTestId("people-joy-state")).toBeTruthy();
    expect(screen.getByTestId("people-joy-action")).toHaveTextContent("Set up People");
    expect(screen.getByText("Encrypted, local-only relationship context")).toBeTruthy();
    expect(screen.queryByLabelText("New relationship")).toBeNull();
  });

  it("clears roster data when a relationship read becomes locked", async () => {
    stub({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted", sync: "local_only", capture: "notes_only" }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Avery", relationship_kind: "direct_report" }] }),
      "/api/people/relationships/r1": () => json({ detail: "key locked" }, 423),
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
    });
    render(<PeopleCore />);
    fireEvent.click(await screen.findByRole("button", { name: /Avery/ }));
    expect(await screen.findByTestId("people-joy-state")).toBeTruthy();
    expect(screen.queryByText("Avery")).toBeNull();
    expect(screen.queryByLabelText("New relationship")).toBeNull();
  });

  it("renders local trust facts and a manual relationship", async () => {
    stub({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted", sync: "local_only", capture: "notes_only" }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Avery", relationship_kind: "direct_report", manager_commitment_count: 1 }] }),
      "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Avery", relationship_kind: "peer", project_refs: ["p1"], commitments: [], notes: [{ id: "n1", topic: "Collaboration", body: "Prefers written context", visibility: "shared_intent" }] } }),
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
      "/api/projects": () => json({ projects: [{ id: "p1", name: "Platform", description: "Platform work" }] }),
      "/api/door": () => json({ upcoming: [] }),
    });
    render(<PeopleCore scope="people:r1" />);
    await screen.findByText("Local storage");
    expect(screen.getByText("Encrypted")).toBeTruthy();
    expect(screen.getByText("Notes only")).toBeTruthy();
    await waitFor(() => expect(screen.getByRole("tab", { name: "1:1s" })).toBeTruthy());
    fireEvent.click(screen.getByRole("tab", { name: "Context" }));
    expect(await screen.findByRole("button", { name: /Platform/ })).toBeTruthy();
    expect(screen.getByText("Prefers written context")).toBeTruthy();
    expect(screen.getByLabelText("Grounding note")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /^Speak / })).toBeNull();
  });

  it("opens a commitment execution inspector and relationship history", async () => {
    stub({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Avery", relationship_kind: "peer" }] }),
      "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Avery", relationship_kind: "peer", commitments: [{ id: "c1", body: "Discuss the next architecture step", state: "open", history: [{ event: "accepted", state: "open", at: "2026-08-17T03:00:00Z", source: "people" }] }] } }),
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
      "/api/workbenches": () => json({ workbenches: [{ id: "wb1", name: "Architecture" }] }),
      "/api/people/commitments/c1/execution": () => json({ items: [] }),
      "/api/door": () => json({ upcoming: [] }),
    });
    render(<PeopleCore scope="people:r1" />);
    fireEvent.click(await screen.findByRole("button", { name: /Discuss the next architecture step/ }));
    expect(await screen.findByRole("button", { name: "Send to Workbench" })).toBeTruthy();
    expect(screen.getByText("Workbench model")).toBeTruthy();
    expect(screen.getByTitle("Workbench model")).toHaveClass("egress-badge", "is-cloud");
    expect(screen.getByRole("button", { name: "Mark satisfied" })).toBeTruthy();
    fireEvent.click(screen.getByRole("tab", { name: "History" }));
    expect(screen.getByText("Accepted")).toBeTruthy();
    expect(screen.getByText("Discuss the next architecture step")).toBeTruthy();
  });
});

describe("PeopleCore HS-149-03 gesture", () => {
  it("picker renders upcoming events with suggestion ordering", async () => {
    stub({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Ewa", relationship_kind: "direct_report" }] }),
      "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Ewa", relationship_kind: "direct_report", calendar_links: [] } }),
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
      "/api/projects": () => json({ projects: [] }),
      "/api/door": () => json({ upcoming: [
        { id: "e1", uid: "uid-team", source: "calendar_event", title: "Team standup", starts_at: "2099-09-01T09:00:00Z", ends_at: "2099-09-01T09:30:00Z", source_id: "cal-1", source_label: "Work" },
        { id: "e2", uid: "uid-ewa", source: "calendar_event", title: "1:1 w/ Ewa", starts_at: "2099-09-01T10:00:00Z", ends_at: "2099-09-01T10:30:00Z", source_id: "cal-1", source_label: "Work" },
        { id: "e3", uid: "uid-ewa-review", source: "calendar_event", title: "Ewa performance review", starts_at: "2099-09-02T14:00:00Z", ends_at: "2099-09-02T15:00:00Z", source_id: "cal-1", source_label: "Work" },
      ] }),
    });
    render(<PeopleCore scope="people:r1" />);
    await waitFor(() => expect(screen.getByRole("tab", { name: "Context" })).toBeTruthy());
    fireEvent.click(screen.getByRole("tab", { name: "Context" }));
    // Open picker
    fireEvent.click(await screen.findByTestId("people-link-event"));
    expect(screen.getByTestId("people-event-picker")).toBeTruthy();
    // Suggested rows come first (case-insensitive match on "Ewa")
    const rows = screen.getAllByRole("button").filter((btn) => btn.closest(".surface-row"));
    const titles = rows.map((btn) => btn.textContent).filter(Boolean);
    // "1:1 w/ Ewa" and "Ewa performance review" should be before "Team standup"
    const ewaIdx1 = titles.findIndex((t) => t?.includes("1:1 w/ Ewa"));
    const ewaIdx2 = titles.findIndex((t) => t?.includes("Ewa performance review"));
    const teamIdx = titles.findIndex((t) => t?.includes("Team standup"));
    // At least one Ewa event is before the team standup
    expect(ewaIdx1 < teamIdx || ewaIdx2 < teamIdx).toBe(true);
    // Suggested rows show SUGGESTED meta
    expect(screen.getAllByText("SUGGESTED").length).toBeGreaterThanOrEqual(1);
  });

  it("zero-auto-link pin: no link POST without a click", async () => {
    const fetchSpy = vi.fn(async (input: string) => {
      const handlers: Record<string, () => Response> = {
        "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
        "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Ewa", relationship_kind: "direct_report" }] }),
        "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Ewa", calendar_links: [] } }),
        "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
        "/api/projects": () => json({ projects: [] }),
        "/api/door": () => json({ upcoming: [
          { id: "e1", uid: "uid-ewa", source: "calendar_event", title: "1:1 w/ Ewa", starts_at: "2099-09-01T10:00:00Z", ends_at: "2099-09-01T10:30:00Z", source_id: "cal-1" },
        ] }),
      };
      const handler = handlers[String(input)];
      if (!handler) throw new Error(`Unexpected request: ${String(input)}`);
      return handler();
    });
    vi.stubGlobal("fetch", fetchSpy);
    render(<PeopleCore scope="people:r1" />);
    await waitFor(() => expect(screen.getByRole("tab", { name: "Context" })).toBeTruthy());
    fireEvent.click(screen.getByRole("tab", { name: "Context" }));
    await screen.findByTestId("people-link-event");
    // Pin: no link POST was made without clicking a picker row
    const linkCalls = fetchSpy.mock.calls.filter(([url]: [string]) => String(url).includes("calendar-links"));
    expect(linkCalls).toHaveLength(0);
  });

  it("link POST on picker row click", async () => {
    const fetchSpy = vi.fn(async (input: string, opts?: { method?: string; body?: string }) => {
      const handlers: Record<string, () => Response> = {
        "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
        "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Ewa", relationship_kind: "direct_report" }] }),
        "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Ewa", calendar_links: [] } }),
        "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
        "/api/projects": () => json({ projects: [] }),
        "/api/door": () => json({ upcoming: [
          { id: "e1", uid: "uid-ewa", source: "calendar_event", title: "1:1 w/ Ewa", starts_at: "2099-09-01T10:00:00Z", ends_at: "2099-09-01T10:30:00Z", source_id: "cal-1", source_label: "Work" },
        ] }),
      };
      if (String(input).includes("calendar-links") && opts?.method === "POST") {
        return json({ relationship: { id: "r1", display_name: "Ewa", calendar_links: [{ uid: "uid-ewa", source_id: "cal-1", label: "1:1 w/ Ewa" }] } });
      }
      const handler = handlers[String(input)];
      if (!handler) throw new Error(`Unexpected request: ${String(input)}`);
      return handler();
    });
    vi.stubGlobal("fetch", fetchSpy);
    render(<PeopleCore scope="people:r1" />);
    await waitFor(() => expect(screen.getByRole("tab", { name: "Context" })).toBeTruthy());
    fireEvent.click(screen.getByRole("tab", { name: "Context" }));
    fireEvent.click(await screen.findByTestId("people-link-event"));
    // Click the event row to link
    fireEvent.click(screen.getByRole("button", { name: /1:1 w\/ Ewa/ }));
    await waitFor(() => {
      const linkCalls = fetchSpy.mock.calls.filter(([url, opts]: [string, { method?: string }?]) => String(url).includes("calendar-links") && opts?.method === "POST");
      expect(linkCalls).toHaveLength(1);
      const body = JSON.parse(linkCalls[0][1]?.body as string);
      expect(body.uid).toBe("uid-ewa");
      expect(body.source_id).toBe("cal-1");
      expect(body.label).toBe("1:1 w/ Ewa");
    });
  });

  it("unlink two-beat: first tap shows confirm, second fires DELETE", async () => {
    const fetchSpy = vi.fn(async (input: string, opts?: { method?: string }) => {
      const handlers: Record<string, () => Response> = {
        "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
        "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Ewa", relationship_kind: "direct_report" }] }),
        "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Ewa", calendar_links: [{ uid: "uid-ewa", source_id: "cal-1", label: "1:1 w/ Ewa", linked_at: "2026-08-28T00:00:00Z" }] } }),
        "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
        "/api/projects": () => json({ projects: [] }),
        "/api/door": () => json({ upcoming: [] }),
      };
      if (String(input).includes("calendar-links") && opts?.method === "DELETE") {
        return json({ relationship: { id: "r1", display_name: "Ewa", calendar_links: [] } });
      }
      const handler = handlers[String(input)];
      if (!handler) throw new Error(`Unexpected request: ${String(input)}`);
      return handler();
    });
    vi.stubGlobal("fetch", fetchSpy);
    render(<PeopleCore scope="people:r1" />);
    await waitFor(() => expect(screen.getByRole("tab", { name: "Context" })).toBeTruthy());
    fireEvent.click(screen.getByRole("tab", { name: "Context" }));
    // Beat 1: "Unlink" button
    const unlinkBtn = await screen.findByRole("button", { name: "Unlink" });
    fireEvent.click(unlinkBtn);
    // Beat 2: confirm "Unlink?" appears
    const confirmBtn = await screen.findByRole("button", { name: "Unlink?" });
    fireEvent.click(confirmBtn);
    await waitFor(() => {
      const unlinkCalls = fetchSpy.mock.calls.filter(([url, opts]: [string, { method?: string }?]) => String(url).includes("calendar-links") && opts?.method === "DELETE");
      expect(unlinkCalls).toHaveLength(1);
    });
  });

  it("NEXT 1:1 header renders when a linked series has an upcoming event", async () => {
    stub({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Ewa", relationship_kind: "direct_report" }] }),
      "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Ewa", calendar_links: [{ uid: "uid-ewa", source_id: "cal-1", label: "1:1 w/ Ewa" }] } }),
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
      "/api/door": () => json({ upcoming: [
        { id: "e1", uid: "uid-ewa", source: "calendar_event", title: "1:1 w/ Ewa", starts_at: "2099-09-01T10:00:00Z", ends_at: "2099-09-01T10:30:00Z", source_id: "cal-1" },
      ] }),
    });
    render(<PeopleCore scope="people:r1" />);
    const header = await screen.findByTestId("people-next-1on1");
    expect(header.textContent).toContain("NEXT 1:1");
  });

  it("NEXT 1:1 header absent when no linked series has upcoming events", async () => {
    stub({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Ewa", relationship_kind: "direct_report" }] }),
      "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Ewa", calendar_links: [] } }),
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
      "/api/door": () => json({ upcoming: [] }),
    });
    render(<PeopleCore scope="people:r1" />);
    await waitFor(() => expect(screen.getByRole("tab", { name: "Now" })).toBeTruthy());
    expect(screen.queryByTestId("people-next-1on1")).toBeNull();
  });

  it("empty roster leads with the create act", async () => {
    stub({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
      "/api/people/relationships": () => json({ relationships: [] }),
    });
    render(<PeopleCore />);
    expect(await screen.findByTestId("people-empty-roster")).toBeTruthy();
    expect(screen.getByText("Add a relationship to start")).toBeTruthy();
  });

  it("suggestion ordering is case-insensitive", async () => {
    stub({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "ewa", relationship_kind: "direct_report" }] }),
      "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "ewa", calendar_links: [] } }),
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
      "/api/projects": () => json({ projects: [] }),
      "/api/door": () => json({ upcoming: [
        { id: "e1", uid: "uid-team", source: "calendar_event", title: "Team standup", starts_at: "2099-09-01T09:00:00Z", ends_at: "2099-09-01T09:30:00Z", source_id: "cal-1" },
        { id: "e2", uid: "uid-ewa", source: "calendar_event", title: "1:1 w/ EWA", starts_at: "2099-09-01T10:00:00Z", ends_at: "2099-09-01T10:30:00Z", source_id: "cal-1" },
      ] }),
    });
    render(<PeopleCore scope="people:r1" />);
    await waitFor(() => expect(screen.getByRole("tab", { name: "Context" })).toBeTruthy());
    fireEvent.click(screen.getByRole("tab", { name: "Context" }));
    fireEvent.click(await screen.findByTestId("people-link-event"));
    // "1:1 w/ EWA" should be SUGGESTED even though name is lowercase "ewa"
    expect(screen.getByText("SUGGESTED")).toBeTruthy();
  });
});

describe("PeopleCore HS-149-04 Prep lens", () => {
  it("renders the Prep tab and brief sections", async () => {
    stub({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Ewa", relationship_kind: "direct_report" }] }),
      "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Ewa", calendar_links: [] } }),
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
      "/api/people/relationships/r1/brief": () => json({ brief: {
        relationship_id: "r1", display_name: "Ewa",
        open_commitments: [{ id: "c1", body: "Ship the feature", visibility: "shared_intent" }],
        agenda_items: [{ id: "a1", body: "Discuss roadmap", visibility: "shared_intent", state: "open" }],
        grounding_note_count: 2,
        linked_meetings: [
          { meeting_id: "m1", title: "Last 1:1", started_at: "2026-08-01T10:00:00", open_action_items: [{ id: "ai1", task: "Review docs", owner: "Ewa", due: null }], decisions: [{ id: "d1", decision_text: "Approved RFC", rationale: null, lifecycle: "active" }] },
        ],
        unlinked_meeting_count: 3,
      } }),
      "/api/door": () => json({ upcoming: [] }),
    });
    render(<PeopleCore scope="people:r1" />);
    await waitFor(() => expect(screen.getByRole("tab", { name: "Prep" })).toBeTruthy());
    fireEvent.click(screen.getByRole("tab", { name: "Prep" }));
    // Sections render
    expect(await screen.findByTestId("people-prep-lens")).toBeTruthy();
    expect(screen.getByText("Ship the feature")).toBeTruthy();
    expect(screen.getByText("Discuss roadmap")).toBeTruthy();
    expect(screen.getByTestId("prep-grounding-count")).toHaveTextContent("2 grounding notes");
    expect(screen.getByText("Last 1:1")).toBeTruthy();
    expect(screen.getByText("Review docs (Ewa)")).toBeTruthy();
    expect(screen.getByText("Approved RFC")).toBeTruthy();
    expect(screen.getByTestId("prep-unlinked-count")).toHaveTextContent("3 unlinked meetings in this window");
  });

  it("renders Owner aliases section on the Context lens with add and two-beat remove", async () => {
    const fetchSpy = vi.fn(async (input: string, opts?: { method?: string; body?: string }) => {
      const handlers: Record<string, () => Response> = {
        "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
        "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Ewa", relationship_kind: "direct_report" }] }),
        "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Ewa", calendar_links: [], owner_aliases: ["Ewa S.", "ES"] } }),
        "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
        "/api/projects": () => json({ projects: [] }),
        "/api/door": () => json({ upcoming: [] }),
      };
      if (String(input).includes("owner-aliases") && opts?.method === "POST") {
        return json({ relationship: { id: "r1", display_name: "Ewa", owner_aliases: ["Ewa S.", "ES", "E."] } });
      }
      if (String(input).includes("owner-aliases") && opts?.method === "DELETE") {
        return json({ relationship: { id: "r1", display_name: "Ewa", owner_aliases: ["ES"] } });
      }
      const handler = handlers[String(input)];
      if (!handler) throw new Error(`Unexpected request: ${String(input)}`);
      return handler();
    });
    vi.stubGlobal("fetch", fetchSpy);
    render(<PeopleCore scope="people:r1" />);
    await waitFor(() => expect(screen.getByRole("tab", { name: "Context" })).toBeTruthy());
    fireEvent.click(screen.getByRole("tab", { name: "Context" }));
    // Section renders with existing aliases
    const section = await screen.findByTestId("people-owner-aliases");
    expect(section).toBeTruthy();
    expect(within(section).getByText("Ewa S.")).toBeTruthy();
    expect(within(section).getByText("ES")).toBeTruthy();
    // Add flow: type + click Add (scoped to the alias section)
    const addArea = within(section).getByTestId("people-alias-add");
    const addInput = addArea.querySelector("input")!;
    fireEvent.change(addInput, { target: { value: "E." } });
    fireEvent.click(within(addArea).getByRole("button", { name: "Add" }));
    await waitFor(() => {
      const postCalls = fetchSpy.mock.calls.filter(([url, opts]: [string, { method?: string }?]) =>
        String(url).includes("owner-aliases") && opts?.method === "POST"
      );
      expect(postCalls).toHaveLength(1);
      const body = JSON.parse(postCalls[0][1]?.body as string);
      expect(body.alias).toBe("E.");
    });
    // Remove flow: two-beat (scoped to the alias section)
    const removeBtn = within(section).getAllByRole("button", { name: "Remove" })[0];
    fireEvent.click(removeBtn);
    const confirmBtn = await within(section).findByRole("button", { name: "Remove?" });
    fireEvent.click(confirmBtn);
    await waitFor(() => {
      const deleteCalls = fetchSpy.mock.calls.filter(([url, opts]: [string, { method?: string }?]) =>
        String(url).includes("owner-aliases") && opts?.method === "DELETE"
      );
      expect(deleteCalls).toHaveLength(1);
    });
  });

  it("opens Prep lens directly via scope focus", async () => {
    stub({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Ewa", relationship_kind: "direct_report" }] }),
      "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Ewa", calendar_links: [] } }),
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
      "/api/people/relationships/r1/brief": () => json({ brief: {
        relationship_id: "r1", display_name: "Ewa",
        open_commitments: [], agenda_items: [], grounding_note_count: 0,
        linked_meetings: [], unlinked_meeting_count: 0,
      } }),
      "/api/door": () => json({ upcoming: [] }),
    });
    render(<PeopleCore scope="people:r1:prep" />);
    // Prep tab should be active on load
    expect(await screen.findByTestId("people-prep-lens")).toBeTruthy();
    // Verify the Prep tab is selected
    const prepTab = screen.getByRole("tab", { name: "Prep" });
    expect(prepTab.getAttribute("aria-selected")).toBe("true");
  });
});
