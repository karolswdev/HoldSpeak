import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PeopleCore, RelationshipPane } from "../PeopleCore";
import { useDesk } from "../../../desk/store";
import RECORDED_RELATIONSHIP from "../../../desk/__tests__/fixtures/people-wire/relationship-before.json";
import RECORDED_PREP from "../../../desk/__tests__/fixtures/people-wire/brief.json";
import RECORDED_OWED from "../../../desk/__tests__/fixtures/people-wire/owed-created.json";
import RECORDED_SESSIONS from "../../../desk/__tests__/fixtures/people-agenda-wire/one-on-ones.json";

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

function stub(handlers: Record<string, (input: string, opts?: { method?: string; body?: string }) => Response | Promise<Response>>) {
  vi.stubGlobal("fetch", vi.fn(async (input: string, opts?: { method?: string; body?: string }) => {
    // PHILO-17 REFIT: Prep leads, so a person's open reads the 1:1 brief;
    // a test that does not name it gets an empty brief.
    // The roster read carries `?counts=1` (PHILO-17); a stub names the path.
    const handler = handlers[String(input).replace("?counts=1", "")] ?? (String(input).endsWith("/brief") ? () => json({ brief: { open_commitments: [], agenda_items: [] } }) : undefined);
    if (!handler) throw new Error(`Unexpected request: ${String(input)}`);
    return handler(input, opts);
  }));
}

afterEach(() => vi.unstubAllGlobals());

describe("Prep owns each obligation and pending Add draft", () => {
  beforeEach(() => useDesk.setState({ drafts: {}, places: {} }));
  afterEach(() => useDesk.setState({ drafts: {}, places: {} }));
  const person = RECORDED_RELATIONSHIP.relationship;
  const leader = person.commitments[0];
  const report = RECORDED_OWED.commitment;
  const session = RECORDED_SESSIONS.one_on_ones[0];
  const scenarios = [
    { label: "Add to the agenda", section: "people-next-plate", button: "Add to agenda", path: `/api/people/one-on-ones/${session.id}/agenda` },
    { label: "I owe Priya", section: "people-you-owe", button: "Add", path: `/api/people/requests/${person.requests[0].id}/accept` },
    { label: "Priya owes me", section: "people-they-owe", button: "Add", path: `/api/people/relationships/${person.id}/owed` },
  ];
  function mount(id = person.id, refresh = vi.fn(), failure = vi.fn()) {
    const relationship = { ...person, id, sessions: [session], owed_to_you: [report] };
    // The recorded transport contains nullable fields (for example
    // project_refs). Preserve that genuine wire instead of inventing values
    // to satisfy the narrower component annotation.
    return render(<RelationshipPane relationship={relationship as unknown as Parameters<typeof RelationshipPane>[0]["relationship"]} initialLens="prep" onRefresh={refresh} onProtectedFailure={failure} onArchived={vi.fn()} />);
  }
  function readers(write: (path: string, opts?: { method?: string; body?: string }) => Response | Promise<Response> = () => json({ commitment: report }, 201)) {
    vi.stubGlobal("fetch", vi.fn(async (input: string, opts?: { method?: string; body?: string }) => {
      const path = String(input);
      if (opts?.method === "POST") {
        if (path.endsWith("/requests")) return json({ request: person.requests[0] }, 201);
        return write(path, opts);
      }
      if (path.endsWith("/brief")) return json(RECORDED_PREP);
      if (path === "/api/door") return json({ upcoming: [] });
      if (path === "/api/workbenches") return json({ workbenches: [] });
      if (path.endsWith("/execution")) return json({ items: [] });
      if (path === "/api/projects") return json({ projects: [] });
      throw new Error(`Unexpected request: ${path}`);
    }));
  }

  it("opens either exact commitment in its owning section and Close returns to that row", async () => {
    readers();
    mount();
    await screen.findByTestId("people-prep-lens");
    for (const [sectionId, item] of [["people-you-owe", leader], ["people-they-owe", report]] as const) {
      const section = screen.getByTestId(sectionId);
      const title = within(section).getByRole("button", { name: item.body });
      title.focus();
      fireEvent.click(title);
      expect(within(section).getByRole("button", { name: "Send to automation" })).toBeTruthy();
      expect(section.querySelector(".people-commitment-body")).toHaveTextContent(item.body);
      await waitFor(() => expect(vi.mocked(fetch).mock.calls.some(([url]) => String(url) === `/api/people/commitments/${item.id}/execution`)).toBe(true));
      expect(document.querySelectorAll(".people-commitment-inspector")).toHaveLength(1);
      fireEvent.click(within(section).getByRole("button", { name: "Close" }));
      expect(section.querySelector(".people-commitment-inspector")).toBeNull();
      expect(within(section).getByRole("button", { name: item.body })).toBeTruthy();
      expect(title).toHaveFocus();
    }
  });

  it.each(scenarios)("$label starts closed and clears only its accepted submitted draft", async ({ label, section, button }) => {
    const refresh = vi.fn();
    readers();
    mount(person.id, refresh);
    const area = await screen.findByTestId(section);
    expect(screen.queryByLabelText(label)).toBeNull();
    fireEvent.click(within(area).getByRole("button", { name: button }));
    fireEvent.change(screen.getByLabelText(label), { target: { value: "  Send the platform plan  " } });
    fireEvent.click(within(area).getByRole("button", { name: button }));
    await waitFor(() => expect(refresh).toHaveBeenCalledOnce());
    expect(screen.queryByLabelText(label)).toBeNull();
    fireEvent.click(within(area).getByRole("button", { name: button }));
    expect(screen.getByLabelText(label)).toHaveValue("");
  });

  it.each(scenarios)("$label stays open and focused when its text is cleared for editing", async ({ label, section, button }) => {
    readers();
    mount();
    const area = await screen.findByTestId(section);
    fireEvent.click(within(area).getByRole("button", { name: button }));
    const input = screen.getByLabelText(label) as HTMLInputElement;
    input.focus();
    fireEvent.change(input, { target: { value: "Replace these words" } });
    input.setSelectionRange(0, input.value.length);
    fireEvent.change(input, { target: { value: "" } });
    expect(screen.getByLabelText(label)).toBe(input);
    expect(input).toHaveFocus();
    expect(input).toHaveValue("");
    expect(within(area).getByRole("button", { name: button })).toBeDisabled();
    fireEvent.change(input, { target: { value: "Replacement words" } });
    expect(input).toHaveFocus();
    expect(input).toHaveValue("Replacement words");
    expect(vi.mocked(fetch).mock.calls.some(([, options]) => options?.method === "POST")).toBe(false);
    fireEvent.click(within(area).getByRole("button", { name: "Hide" }));
    expect(screen.queryByLabelText(label)).toBeNull();
  });

  it.each(scenarios.flatMap((scenario) => [true, false].map((accepted) => ({ ...scenario, accepted }))))("$label keeps newer text after accepted=$accepted and through person/tab/remount return", async ({ label, section, button, path, accepted }) => {
    let finish!: (response: Response) => void;
    const submitted: Array<{ path: string; body: unknown }> = [];
    readers((url, opts) => {
      submitted.push({ path: url, body: opts?.body ? JSON.parse(opts.body) : null });
      return new Promise<Response>((resolve) => { finish = resolve; });
    });
    const refresh = vi.fn();
    const failure = vi.fn();
    let view = mount(person.id, refresh, failure);
    const area = await screen.findByTestId(section);
    fireEvent.click(within(area).getByRole("button", { name: button }));
    const input = screen.getByLabelText(label);
    fireEvent.change(input, { target: { value: "Original task for this report" } });
    fireEvent.click(within(area).getByRole("button", { name: button }));
    await waitFor(() => expect(submitted).toHaveLength(1));
    expect(submitted[0].path).toBe(path);
    expect(within(area).getByRole("button", { name: button })).toBeDisabled();
    expect(input).not.toBeDisabled();
    fireEvent.change(input, { target: { value: "Newer task for the next Add" } });
    await act(async () => finish(accepted ? json({ commitment: report }, 201) : json({ error: "Writer refused" }, 409)));
    await waitFor(() => expect(accepted ? refresh : failure).toHaveBeenCalledOnce());
    expect(screen.getByLabelText(label)).toHaveValue("Newer task for the next Add");
    fireEvent.click(screen.getByRole("button", { name: "History" }));
    // Betterment D7: the prep stays on the page; the folds sit under it.
    expect(await screen.findByLabelText(label)).toHaveValue("Newer task for the next Add");
    view.unmount();
    view = mount("another-report");
    const other = await screen.findByTestId(section);
    expect(screen.queryByLabelText(label)).toBeNull();
    fireEvent.click(within(other).getByRole("button", { name: button }));
    expect(screen.getByLabelText(label)).toHaveValue("");
    view.unmount();
    mount();
    expect(await screen.findByLabelText(label)).toHaveValue("Newer task for the next Add");
    expect(submitted).toHaveLength(1);
  });
});

describe("Context keeps the report's working note", () => {
  beforeEach(() => useDesk.setState({ drafts: {}, places: {} }));
  afterEach(() => useDesk.setState({ drafts: {}, places: {} }));
  const relationship = { id: "context-r1", display_name: "Priya", notes: [{ id: "saved", topic: "Career plan", body: "Lead the ledger cutover next month.", visibility: "leader_private" as const }] };
  function mount(id = relationship.id, onRefresh = vi.fn()) {
    return render(<RelationshipPane relationship={{ ...relationship, id }} initialLens="context" onRefresh={onRefresh} onProtectedFailure={vi.fn()} onArchived={vi.fn()} />);
  }
  function readers(post?: (opts?: { method?: string; body?: string }) => Response | Promise<Response>) {
    stub({
      "/api/projects": () => json({ projects: [] }),
      "/api/door": () => json({ upcoming: [] }),
      "/api/people/relationships/context-r1/notes": (_url, opts) => post?.(opts) ?? json({}, 201),
    });
  }
  function typeNote() {
    fireEvent.click(screen.getByRole("button", { name: "Add note" }));
    fireEvent.change(screen.getByLabelText("Topic"), { target: { value: "Release feedback" } });
    fireEvent.change(screen.getByLabelText("Note"), { target: { value: "Priya can lead the release after the rollback review." } });
    fireEvent.change(screen.getByLabelText("Visibility"), { target: { value: "shared_intent" } });
  }

  it("leads with saved context and keeps a closed draft through tab return, remount and another person", async () => {
    readers();
    let view = mount();
    expect(screen.getByText("Lead the ledger cutover next month.")).toBeTruthy();
    expect(screen.queryByLabelText("Note")).toBeNull();
    expect(screen.queryByTestId("people-link-event")).toBeNull();
    typeNote();
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(screen.queryByLabelText("Note")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "History" }));
    fireEvent.click(screen.getByRole("button", { name: "Context" }));
    expect(screen.getByLabelText("Note")).toHaveValue("Priya can lead the release after the rollback review.");
    expect(screen.getByLabelText("Visibility")).toHaveValue("shared_intent");
    view.unmount();
    view = mount("context-r2");
    fireEvent.click(screen.getByRole("button", { name: "Add note" }));
    expect(screen.getByLabelText("Note")).toHaveValue("");
    expect(screen.getByLabelText("Visibility")).toHaveValue("leader_private");
    view.unmount();
    mount();
    expect(screen.getByLabelText("Topic")).toHaveValue("Release feedback");
    expect(screen.getByLabelText("Note")).toHaveValue("Priya can lead the release after the rollback review.");
    expect(screen.getByLabelText("Visibility")).toHaveValue("shared_intent");
  });

  it("keeps a refused draft and clears it only after a successful retry with the same private/shared authority", async () => {
    let attempts = 0;
    const submitted: unknown[] = [];
    readers((opts) => {
      submitted.push(JSON.parse(String(opts?.body)));
      return ++attempts === 1 ? json({ error: "revision_conflict" }, 409) : json({}, 201);
    });
    const refresh = vi.fn();
    mount(relationship.id, refresh);
    typeNote();
    fireEvent.click(screen.getByRole("button", { name: "Add note" }));
    await waitFor(() => expect(attempts).toBe(1));
    await waitFor(() => expect(screen.getByRole("button", { name: "Add note" })).not.toBeDisabled());
    expect(screen.getByLabelText("Note")).toHaveValue("Priya can lead the release after the rollback review.");
    expect(refresh).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Add note" }));
    await waitFor(() => expect(refresh).toHaveBeenCalledOnce());
    expect(submitted[1]).toEqual(submitted[0]);
    expect(submitted[1]).toMatchObject({ visibility: "shared_intent" });
    fireEvent.click(screen.getByRole("button", { name: "Add note" }));
    expect(screen.getByLabelText("Topic")).toHaveValue("");
    expect(screen.getByLabelText("Note")).toHaveValue("");
    expect(screen.getByLabelText("Visibility")).toHaveValue("leader_private");
  });

  it("does not clear a newer note typed while the submitted snapshot is pending", async () => {
    let accept: (response: Response) => void = () => {};
    readers(() => new Promise<Response>((resolve) => { accept = resolve; }));
    const refresh = vi.fn();
    mount(relationship.id, refresh);
    typeNote();
    fireEvent.click(screen.getByRole("button", { name: "Add note" }));
    fireEvent.change(screen.getByLabelText("Note"), { target: { value: "Next note: discuss the rollout owners." } });
    await act(async () => { accept(json({}, 201)); });
    expect(refresh).toHaveBeenCalledOnce();
    expect(screen.getByLabelText("Note")).toHaveValue("Next note: discuss the rollout owners.");
    expect(screen.getByLabelText("Topic")).toHaveValue("Release feedback");
    expect(screen.getByLabelText("Visibility")).toHaveValue("shared_intent");
  });
});

describe("PeopleCore encrypted local plane", () => {
  it("an unconfigured store is an empty roster: no Set up step, one line (Betterment D6)", async () => {
    stub({ "/api/people/readiness": () => json({ readiness: "unconfigured" }), "/api/people/suggestions": () => json({ suggestions: [] }) });
    render(<PeopleCore />);
    expect((await screen.findByTestId("people-empty-roster")).textContent).toBe("People you meet appear here.");
    expect(screen.queryByText("Set up People")).toBeNull();
    expect(screen.queryByTestId("people-joy-state")).toBeNull();
  });

  it("clears roster data when a relationship read becomes locked", async () => {
    stub({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted", sync: "local_only", capture: "notes_only" }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Avery", relationship_kind: "direct_report" }] }),
      "/api/people/relationships/r1": () => json({ detail: "key locked" }, 423),
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
    });
    // Window grammar: a roster press selects; a person read is the scoped
    // open (`people:<id>`), here or in the person's own window.
    render(<PeopleCore scope="people:r1" />);
    // Betterment D6: a People read that failed is one line in place.
    expect(await screen.findByTestId("people-read-failed")).toBeTruthy();
    expect(screen.queryByText("Avery")).toBeNull();
    expect(screen.queryByLabelText("Add person")).toBeNull();
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
    // Window grammar: the storage facts are Encrypted in the roster's
    // status bar; the words ride its title.
    const roster = render(<PeopleCore />);
    const lock = await screen.findByTestId("people-lock");
    expect(lock.textContent).toContain("Encrypted");
    expect(lock.getAttribute("title")).toBe("Encrypted · Local storage · Notes only");
    roster.unmount();
    render(<PeopleCore scope="people:r1" />);
    await screen.findByTestId("people-prep-lens");
    // One status bar per window: with a person open, the Prep's bar stands alone.
    await waitFor(() => expect(screen.queryByTestId("people-lock")).toBeNull());
    expect(document.querySelectorAll(".kit-statusbar").length).toBe(1);
    expect(screen.getByTestId("person-lock").textContent).toBe("Encrypted");
    fireEvent.click(screen.getByRole("button", { name: "Context" }));
    expect(await screen.findByRole("button", { name: /Platform/ })).toBeTruthy();
    expect(screen.getByText("Prefers written context")).toBeTruthy();
    expect(screen.queryByLabelText("Note")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Add note" }));
    expect(screen.getByLabelText("Note")).toBeTruthy();
    // HS-176-04 — the voice law (Article IV.1): People's wells carry the
    // mic like every other text input.  This assertion used to require the
    // opposite; the seven mic={false} opt-outs it guarded are gone.
    expect(screen.getAllByRole("button", { name: /^Speak / }).length).toBeGreaterThan(0);
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
    expect(await screen.findByRole("button", { name: "Send to automation" })).toBeTruthy();
    expect(screen.queryByTitle("Workbench model")).toBeNull();
    expect(screen.queryByText("Workbench model")).toBeNull();
    expect(screen.getByRole("button", { name: "Mark satisfied" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "History" }));
    expect(screen.getByText("Accepted")).toBeTruthy();
    // Betterment D7: the prep stays above the History fold, so the item shows in both.
    expect(screen.getAllByText("Discuss the next architecture step").length).toBeGreaterThanOrEqual(2);
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
    await waitFor(() => expect(screen.getByRole("button", { name: "Context" })).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Context" }));
    fireEvent.click(screen.getByRole("button", { name: "Links" }));
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
      const handler = handlers[String(input).replace("?counts=1", "")];
      if (!handler) throw new Error(`Unexpected request: ${String(input)}`);
      return handler();
    });
    vi.stubGlobal("fetch", fetchSpy);
    render(<PeopleCore scope="people:r1" />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Context" })).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Context" }));
    fireEvent.click(screen.getByRole("button", { name: "Links" }));
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
      const handler = handlers[String(input).replace("?counts=1", "")];
      if (!handler) throw new Error(`Unexpected request: ${String(input)}`);
      return handler();
    });
    vi.stubGlobal("fetch", fetchSpy);
    render(<PeopleCore scope="people:r1" />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Context" })).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Context" }));
    fireEvent.click(screen.getByRole("button", { name: "Links" }));
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
      const handler = handlers[String(input).replace("?counts=1", "")];
      if (!handler) throw new Error(`Unexpected request: ${String(input)}`);
      return handler();
    });
    vi.stubGlobal("fetch", fetchSpy);
    render(<PeopleCore scope="people:r1" />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Context" })).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Context" }));
    fireEvent.click(screen.getByRole("button", { name: "Links" }));
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
      // The hub's brief names the linked series' next event.
      "/api/people/relationships/r1/brief": () => json({ brief: { open_commitments: [], agenda_items: [], next_one_on_one: { id: "e1", uid: "uid-ewa", title: "1:1 w/ Ewa", starts_at: "2099-09-01T10:00:00Z", ends_at: "2099-09-01T10:30:00Z", source_id: "cal-1", source_label: "Work" } } }),
      "/api/door": () => json({ upcoming: [
        { id: "e1", uid: "uid-ewa", source: "calendar_event", title: "1:1 w/ Ewa", starts_at: "2099-09-01T10:00:00Z", ends_at: "2099-09-01T10:30:00Z", source_id: "cal-1" },
      ] }),
    });
    render(<PeopleCore scope="people:r1" />);
    const header = await screen.findByTestId("people-next-1on1");
    expect(header.textContent).toContain("Next 1:1");
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
    await screen.findByTestId("people-next-plate");
    expect(screen.queryByTestId("people-next-1on1")).toBeNull();
  });

  it("an empty roster is one line (Betterment D6)", async () => {
    stub({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
      "/api/people/relationships": () => json({ relationships: [] }),
    });
    render(<PeopleCore />);
    expect(await screen.findByTestId("people-empty-roster")).toBeTruthy();
    expect(screen.getByText("People you meet appear here.")).toBeTruthy();
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
    await waitFor(() => expect(screen.getByRole("button", { name: "Context" })).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Context" }));
    fireEvent.click(screen.getByRole("button", { name: "Links" }));
    fireEvent.click(await screen.findByTestId("people-link-event"));
    // "1:1 w/ EWA" should be SUGGESTED even though name is lowercase "ewa"
    expect(screen.getByText("SUGGESTED")).toBeTruthy();
  });
});

describe("PeopleCore HS-149-04 Prep lens", () => {
  it("renders the Prep tab with display step and agenda", async () => {
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
        last_meeting: { meeting_id: "m1", title: "Last 1:1", item_count: 2, open_count: 1 },
      } }),
      "/api/door": () => json({ upcoming: [] }),
    });
    render(<PeopleCore scope="people:r1" />);
    await screen.findByTestId("people-prep-lens");
    // Betterment D7: the prep stays on the page; the folds sit under it.
    // HS-172-05: display step + summary rows + agenda
    expect(await screen.findByTestId("people-prep-lens")).toBeTruthy();
    expect(screen.getByTestId("prep-display-name")).toHaveTextContent("Ewa");
    expect(screen.getByText("Discuss roadmap")).toBeTruthy();
    // LAST MEETING summary row
    expect(screen.getByTestId("prep-meeting-row")).toBeTruthy();
    // Footer
    expect(screen.queryByText("THIS DEVICE")).toBeNull();
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
      const handler = handlers[String(input).replace("?counts=1", "")];
      if (!handler) throw new Error(`Unexpected request: ${String(input)}`);
      return handler();
    });
    vi.stubGlobal("fetch", fetchSpy);
    render(<PeopleCore scope="people:r1" />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Context" })).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Context" }));
    fireEvent.click(screen.getByRole("button", { name: "Links" }));
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
    // Betterment D7: the prep is the page; every fold under it starts closed.
    for (const fold of ["Context", "History", "Info"]) {
      // Folds appear after Prep completes its first asynchronous read.
      expect((await screen.findByRole("button", { name: fold })).getAttribute("aria-expanded")).toBe("false");
    }
  });
});

// HS-200-14 (AC4): `people:project:<id>` scopes the roster to the Project's
// people; the window's close hands focus back to the Room verb it came from.
import { rememberTaskFocus, taskFocusPending } from "../../../desk/returnToTask";

describe("PeopleCore scoped to a Project (HS-200-14)", () => {
  const ready = () => json({ readiness: "ready", store: "encrypted", sync: "local_only", capture: "notes_only" });

  it("lists only the people linked to the Project, names the rest as a way out, and never a zero", async () => {
    stub({
      "/api/people/readiness": ready,
      "/api/people/relationships": () => json({ relationships: [
        { id: "r1", display_name: "Marek Kubiak", relationship_kind: "direct_report", project_refs: ["p1"] },
        { id: "r2", display_name: "Priya Sharma", relationship_kind: "peer", project_refs: [] },
        { id: "r3", display_name: "Anil Kumar", relationship_kind: "peer" },
      ] }),
    });
    render(<PeopleCore scope="people:project:p1" />);
    expect((await screen.findByTestId("people-count")).textContent).toBe("1 on this project");
    expect(screen.getByRole("button", { name: /Marek Kubiak/ })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Priya Sharma/ })).toBeNull();
    const everyone = screen.getByTestId("people-roster-everyone");
    expect(everyone).toHaveTextContent("2 more · Everyone");
    fireEvent.click(everyone);
    expect(await screen.findByRole("button", { name: /Priya Sharma/ })).toBeTruthy();
    expect(screen.getByTestId("people-count").textContent).toBe("3 people");
    expect(screen.queryByTestId("people-roster-everyone")).toBeNull();
  });

  it("says NO ONE LINKED YET as a token, not a sentence, when the Project links nobody", async () => {
    stub({
      "/api/people/readiness": ready,
      "/api/people/relationships": () => json({ relationships: [
        { id: "r2", display_name: "Priya Sharma", relationship_kind: "peer", project_refs: [] },
      ] }),
    });
    render(<PeopleCore scope="people:project:p1" />);
    expect(await screen.findByTestId("people-roster-none-linked")).toHaveTextContent("No one linked yet");
    expect(screen.getByTestId("people-roster-everyone")).toHaveTextContent("1 more · Everyone");
  });

  it("hands focus back to the Room verb when the window closes with a return owed", async () => {
    stub({ "/api/people/readiness": ready, "/api/people/relationships": () => json({ relationships: [] }) });
    const verb = document.createElement("button");
    verb.textContent = "People";
    document.body.appendChild(verb);
    verb.focus();
    rememberTaskFocus(verb);
    expect(taskFocusPending()).toBe(true);
    const view = render(<PeopleCore scope="people:project:p1" />);
    await screen.findByTestId("people-roster-none-linked");
    verb.blur();
    view.unmount();
    await waitFor(() => expect(document.activeElement).toBe(verb));
    expect(taskFocusPending()).toBe(false);
    verb.remove();
  });

  it("owes nothing when it was not opened from a task", async () => {
    stub({ "/api/people/readiness": ready, "/api/people/relationships": () => json({ relationships: [] }) });
    const listener = vi.fn();
    window.addEventListener("holdspeak:settings-updated", listener);
    const view = render(<PeopleCore />);
    await screen.findByText("People you meet appear here.");
    view.unmount();
    expect(listener).not.toHaveBeenCalled();
    window.removeEventListener("holdspeak:settings-updated", listener);
  });
});

describe("PeopleCore PHILO-17 the 1:1 runs both ways", () => {
  function spy(handlers: Record<string, (opts?: { method?: string; body?: string }) => Response>) {
    const fetchSpy = vi.fn(async (input: string, opts?: { method?: string; body?: string }) => {
      const url = String(input).replace("?counts=1", "");
      const key = `${opts?.method ?? "GET"} ${url}`;
      const handler = handlers[key] ?? handlers[url];
      if (!handler) throw new Error(`Unexpected request: ${key}`);
      return handler(opts);
    });
    vi.stubGlobal("fetch", fetchSpy);
    return fetchSpy;
  }
  const posts = (fetchSpy: ReturnType<typeof spy>, path: string) =>
    fetchSpy.mock.calls.filter(([url, opts]) => String(url) === path && (opts as { method?: string } | undefined)?.method === "POST");

  it("Prep records what they owe you, marks it done, and names requests 'Asked of you'", async () => {
    // The person's read carries the added item once the Add has saved it.
    const added: { id: string; body: string; state: string; direction: string }[] = [];
    const fetchSpy = spy({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Maya Chen", relationship_kind: "direct_report" }] }),
      "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Maya Chen", commitments: [], requests: [{ id: "q1", body: "Review my doc", state: "requested" }], owed_to_you: [{ id: "o1", body: "Send the rollout plan", state: "open", direction: "report_owes" }, { id: "o2", body: "Old item", state: "done", direction: "report_owes" }, ...added] } }),
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
      "/api/people/relationships/r1/brief": () => json({ brief: { relationship_id: "r1", open_commitments: [], agenda_items: [] } }),
      "/api/door": () => json({ upcoming: [] }),
      "POST /api/people/relationships/r1/owed": (opts) => {
        added.push({ id: "o3", body: JSON.parse(String(opts?.body)).body, state: "open", direction: "report_owes" });
        return json({ commitment: { id: "o3" } }, 201);
      },
      "POST /api/people/commitments/o1/transition": () => json({ transition: { verb: "done" } }),
    });
    render(<PeopleCore scope="people:r1" />);
    const owed = await screen.findByTestId("people-they-owe");
    expect(within(owed).getByRole("heading").textContent).toBe("Maya owes me1");
    expect(within(owed).getByText("Send the rollout plan")).toBeTruthy();
    expect(within(owed).queryByText("Old item")).toBeNull();
    expect(screen.getByText("Asked of you")).toBeTruthy();
    expect(screen.queryByText(/Open requests/i)).toBeNull();
    fireEvent.click(within(owed).getByRole("button", { name: "Add" }));
    fireEvent.change(within(owed).getByLabelText("Maya owes me"), { target: { value: "Send me the API migration estimate" } });
    fireEvent.click(within(owed).getByRole("button", { name: "Add" }));
    await waitFor(() => expect(posts(fetchSpy, "/api/people/relationships/r1/owed")).toHaveLength(1));
    expect(JSON.parse(String(posts(fetchSpy, "/api/people/relationships/r1/owed")[0][1]?.body)).body).toBe("Send me the API migration estimate");
    expect(posts(fetchSpy, "/api/people/relationships/r1/requests")).toHaveLength(0);
    // The Add refreshes the person: while the second read is out the pane
    // draws the roster row (no "They owe you" items, no Done), then the read
    // lands. Wait for the read that carries the added item, then press Done.
    // A press in that gap found no Done: the -n 8 flake (test diet 2026-10-11).
    await within(owed).findByText("Send me the API migration estimate");
    const rollout = within(owed).getByText("Send the rollout plan").closest(".people-plate-row") as HTMLElement;
    fireEvent.click(within(rollout).getByRole("button", { name: "Done" }));
    await waitFor(() => expect(posts(fetchSpy, "/api/people/commitments/o1/transition")).toHaveLength(1));
    expect(JSON.parse(String(posts(fetchSpy, "/api/people/commitments/o1/transition")[0][1]?.body)).verb).toBe("done");
  });

  it("Add person stays on the list, warns once on a name already here, then adds it", async () => {
    let roster = [{ id: "r1", display_name: "Maya Chen", relationship_kind: "direct_report" }];
    const fetchSpy = spy({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
      "/api/people/relationships": (opts) => {
        if (opts?.method === "POST") {
          const name = JSON.parse(String(opts.body)).display_name;
          roster = [...roster, { id: `r${roster.length + 1}`, display_name: name, relationship_kind: "direct_report" }];
          return json({ relationship: roster[roster.length - 1] }, 201);
        }
        return json({ relationships: roster });
      },
    });
    render(<PeopleCore />);
    // PHILO-17 ALIVE: one way to add. Add person opens the add row.
    expect(screen.queryByTestId("people-add-row")).toBeNull();
    fireEvent.click(await screen.findByRole("button", { name: "Add person" }));
    // Window grammar: Add person stays on the toolbar; the add row opens under it.
    expect(screen.getByTestId("people-add-row")).toBeTruthy();
    const name = screen.getByLabelText("Add person");
    fireEvent.change(name, { target: { value: "Sam Ortiz" } });
    fireEvent.click(screen.getByRole("button", { name: "Add" }));
    await screen.findByRole("button", { name: /Sam Ortiz/ });
    expect(screen.queryByRole("tablist")).toBeNull();
    expect((screen.getByLabelText("Add person") as HTMLInputElement).value).toBe("");
    expect(document.activeElement).toBe(screen.getByLabelText("Add person"));
    fireEvent.change(screen.getByLabelText("Add person"), { target: { value: " maya chen " } });
    fireEvent.click(screen.getByRole("button", { name: "Add" }));
    expect(await screen.findByTestId("people-duplicate")).toHaveTextContent("Maya Chen · Already here");
    expect(posts(fetchSpy, "/api/people/relationships")).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Add again" }));
    await waitFor(() => expect(posts(fetchSpy, "/api/people/relationships")).toHaveLength(2));
    await waitFor(() => expect(screen.queryByTestId("people-duplicate")).toBeNull());
  });

  it("History shows no zero counters and Info hides fields that are not set", async () => {
    spy({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Maya Chen", relationship_kind: "direct_report" }] }),
      "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Maya Chen", relationship_kind: "direct_report", commitments: [] } }),
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
      "/api/people/relationships/r1/brief": () => json({ brief: { relationship_id: "r1", open_commitments: [], agenda_items: [] } }),
      "/api/door": () => json({ upcoming: [] }),
    });
    render(<PeopleCore scope="people:r1" />);
    fireEvent.click(await screen.findByRole("button", { name: "History" }));
    expect(screen.queryByTestId("people-history-facts")).toBeNull();
    expect(document.body.textContent).not.toContain("—");
    expect(screen.queryByRole("button", { name: "Add person" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Info" }));
    expect(screen.queryByText("Role context")).toBeNull();
    expect(screen.queryByText("Not set")).toBeNull();
  });

  it("PHILO-17 ALIVE: a roster row says the next 1:1, owed both ways, and Plan for a report with none", async () => {
    const soon = new Date(Date.now() + 2 * 86_400_000).toISOString();
    // The counts ride the roster read (`?counts=1`); the next 1:1 is the
    // Door's calendar row that carries the person. No per-person read.
    const fetchSpy = spy({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
      "/api/people/relationships": () => json({ relationships: [
        { id: "r1", display_name: "Maya Chen", relationship_kind: "direct_report", you_owe_count: 1, owes_you_count: 1 },
        { id: "r2", display_name: "Sam Ortiz", relationship_kind: "direct_report", you_owe_count: 0, owes_you_count: 0 },
      ] }),
      "/api/door": () => json({ upcoming: [{ id: "e1", source: "calendar_event", title: "1:1 Maya / Karol", starts_at: soon, ends_at: soon, person_relationship_id: "r1", person_label: "Maya Chen" }] }),
    });
    render(<PeopleCore />);
    // Window grammar: a dense list row (Name · Role · Next 1:1 · You owe).
    const cell = (row: Element, col: string) => row.querySelector(`[data-col="${col}"]`)?.textContent ?? "";
    const maya = (await screen.findByRole("button", { name: /Maya Chen/ })).closest("[role=row]")!;
    await waitFor(() => expect(cell(maya, "next")).toMatch(/^1:1 /));
    expect(cell(maya, "owe")).toBe("1");
    expect(cell(maya, "role")).toBe("Direct report");
    const sam = screen.getByRole("button", { name: /Sam Ortiz/ }).closest("[role=row]")!;
    await waitFor(() => expect(cell(sam, "next")).toBe("None"));
    expect(cell(sam, "owe")).toBe("");
    // Plan is the selected row's verb, in the status bar.
    expect(screen.queryByRole("button", { name: "Plan" })).toBeNull();
    fireEvent.click(within(sam as HTMLElement).getByRole("button", { name: /Sam Ortiz/ }));
    expect(within(screen.getByTestId("people-status")).getByRole("button", { name: "Plan" })).toBeTruthy();
    expect(fetchSpy.mock.calls.some(([url]) => /\/api\/people\/relationships\/r\d$/.test(String(url)))).toBe(false);
    // The soonest 1:1 this week is the status bar's warm words; Open prep
    // joins them only within a day (this one is two days out).
    expect(screen.getByTestId("people-roster-next").textContent).toMatch(/^1:1 with Maya /);
    expect(screen.queryByTestId("people-open-prep")).toBeNull();
  });
});


describe("Calendar reads keep their actual state", () => {
  it("shows loading, keeps the note through failure, retries, then shows a true empty", async () => {
    let settle: (response: Response) => void = () => {};
    let reads = 0;
    stub({
      "/api/projects": () => json({ projects: [] }),
      "/api/door": () => ++reads === 1
        ? new Promise<Response>((resolve) => { settle = resolve; })
        : json({ upcoming: [] }),
    });
    render(<RelationshipPane relationship={{ id: "calendar-state", display_name: "Priya" }} initialLens="context" onRefresh={vi.fn()} onProtectedFailure={vi.fn()} onArchived={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "Add note" }));
    fireEvent.change(screen.getByLabelText("Note"), { target: { value: "Keep the rollout draft" } });
    fireEvent.click(screen.getByRole("button", { name: "Links" }));
    fireEvent.click(screen.getByTestId("people-link-event"));
    const picker = screen.getByTestId("people-event-picker");
    expect(picker.querySelector('[data-kind="loading"]')).toBeTruthy();
    expect(screen.queryByText("No upcoming events")).toBeNull();
    await act(async () => { settle(json({ error: "unavailable" }, 503)); });
    expect(within(picker).getByRole("alert")).toHaveTextContent("CALENDAR DID NOT LOAD");
    expect(screen.getByLabelText("Note")).toHaveValue("Keep the rollout draft");
    fireEvent.click(within(picker).getByRole("button", { name: "Try again" }));
    expect(await within(picker).findByText("No upcoming events")).toBeTruthy();
    expect(reads).toBe(2);
    expect(screen.getByLabelText("Note")).toHaveValue("Keep the rollout draft");
  });
});
