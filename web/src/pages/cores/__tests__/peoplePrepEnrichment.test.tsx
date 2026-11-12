/** People brief records keep every source selectable, without zero counters or pronoun labels. */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { personView } from "./peopleView";
import { PersonWindowBody } from "../PeopleCore";

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

function stub(handlers: Record<string, (input: string, opts?: { method?: string; body?: string }) => Response | Promise<Response>>) {
  vi.stubGlobal("fetch", vi.fn(async (input: string, opts?: { method?: string; body?: string }) => {
    const url = String(input);
    // Match the most specific handler first.
    for (const [pattern, handler] of Object.entries(handlers)) {
      if (url === pattern || url.startsWith(pattern)) {
        return handler(input, opts);
      }
    }
    throw new Error(`Unexpected request: ${url}`);
  }));
}

afterEach(() => vi.unstubAllGlobals());

// ── Pure unit tests for helper functions ──

// ── Integration tests for the Prep lens ──

const WATCH_SUMMARY = {
  prs_waiting: [
    { title: "Fix migration", repo: "karolswdev/holdspeak", pr_number: 612, days_waiting: 5, url: "https://github.com/pr/612", room_id: "p1", room_name: "Platform" },
    { title: "Update types", repo: "karolswdev/holdspeak", pr_number: 618, days_waiting: 2, url: "https://github.com/pr/618", room_id: "p1", room_name: "Platform" },
  ],
  oldest_waiting_days: 5,
  open_assignments: [
    { summary: "PostgreSQL migration", key: "GOV-412", status: "In Progress", url: "https://jira/GOV-412", overdue: true, room_id: "p1", room_name: "Platform" },
  ],
};

const LAST_MEETING = {
  meeting_id: "m1",
  title: "Sprint Review",
  item_count: 5,
  open_count: 2,
};

function makeBrief(overrides: Record<string, unknown> = {}) {
  return {
    relationship_id: "r1",
    display_name: "Ania",
    open_commitments: [
      { id: "c1", body: "API spec", visibility: "shared_intent", state: "open", due: "2020-01-01" },
    ],
    agenda_items: [
      { id: "a1", body: "Discuss API contract timeline", visibility: "shared_intent", state: "open" },
      { id: "a2", body: "Review #612 priority", visibility: "shared_intent", state: "open" },
    ],
    grounding_note_count: 0,
    linked_meetings: [],
    unlinked_meeting_count: 0,
    watch_summary: WATCH_SUMMARY,
    last_meeting: LAST_MEETING,
    ...overrides,
  };
}

function stubWithBrief(briefOverrides: Record<string, unknown> = {}) {
  stub({
    "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
    "/api/people/relationships/r1/brief": () => json({ brief: makeBrief(briefOverrides) }),
    "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
    "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Ania", relationship_kind: "direct_report", calendar_links: [] } }),
    "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Ania", relationship_kind: "direct_report" }] }),
    "/api/door": () => json({ upcoming: [] }),
  });
}

describe("People 1:1 brief uses the selection grammar", () => {
  async function brief(overrides:Record<string,unknown>={}) {
    stubWithBrief(overrides); render(<PersonWindowBody relationshipId="r1"/>);
    await screen.findByTestId("people-prep-lens");await personView("1:1 brief");
    return screen.getByRole("grid",{name:"1:1 brief"});
  }
  it("keeps the person's name, PRs, issues, overdue promise and meeting facts", async()=>{
    const list=await brief();
    expect(screen.getByTestId("prep-display-name")).toHaveTextContent("Ania");
    expect(within(list).getByRole("row",{name:/#612 · Fix migration/})).toHaveTextContent("5 days");
    expect(within(list).getByRole("row",{name:/#618 · Update types/})).toHaveTextContent("2 days");
    expect(within(list).getByRole("row",{name:/GOV-412/})).toHaveTextContent("In progress");
    expect(within(list).getByRole("row",{name:/API spec/})).toHaveTextContent("Overdue");
    expect(within(list).getByRole("row",{name:/Sprint Review/})).toHaveTextContent("5 items · 2 open");
    expect(screen.getByTestId("prep-receipt")).toHaveTextContent(/^Prepared \d{2}:\d{2}$/);
  });
  it("omits absent records and zero counters",async()=>{
    const list=await brief({watch_summary:{prs_waiting:[],open_assignments:[]},last_meeting:null,open_commitments:[]});
    expect(within(list).queryAllByRole("row")).toHaveLength(0);
    expect(list).not.toHaveTextContent(/\b0\s+(PRs|assignments|commitments|items)\b/i);
  });
  it("keeps every PR as a selectable row instead of hiding the fourth and later numbers",async()=>{
    const prs=Array.from({length:5},(_,i)=>({...WATCH_SUMMARY.prs_waiting[0],pr_number:i+1,title:`Change ${i+1}`}));
    const list=await brief({watch_summary:{prs_waiting:prs,open_assignments:[]}});
    for(const pr of prs)expect(within(list).getByRole("row",{name:new RegExp(`#${pr.pr_number} · ${pr.title}`)})).toBeInTheDocument();
  });
  it("keeps pronoun-free metadata",async()=>{
    const list=await brief();expect(list.textContent).not.toMatch(/\b(her|him|she|he)\b/i);
  });
  it("marks PRs waiting three days or longer",async()=>{
    const list=await brief();expect(within(list).getByRole("row",{name:/#612/})).toHaveTextContent("Waiting for review");
    expect(within(list).getByRole("row",{name:/#618/})).not.toHaveTextContent("Waiting for review");
  });
  it("keeps younger PRs quiet",async()=>{
    const list=await brief({watch_summary:{prs_waiting:[{...WATCH_SUMMARY.prs_waiting[0],days_waiting:1}],open_assignments:[]}});
    expect(within(list).getByRole("row",{name:/#612/})).not.toHaveTextContent("Waiting for review");
  });
  it("opens each selected PR through the one declared Open PR verb",async()=>{
    const open=vi.spyOn(window,"open").mockImplementation(()=>null);const list=await brief();
    for(const pr of WATCH_SUMMARY.prs_waiting){const row=within(list).getByRole("row",{name:new RegExp(`#${pr.pr_number}`)});expect(row.querySelector("button")).toBeNull();fireEvent.click(row);fireEvent.click(screen.getByRole("button",{name:"Open PR"}));expect(open).toHaveBeenLastCalledWith(pr.url,"_blank","noopener");}open.mockRestore();
  });
  it("opens the selected assignment",async()=>{
    const open=vi.spyOn(window,"open").mockImplementation(()=>null);const list=await brief();
    fireEvent.click(within(list).getByRole("row",{name:/GOV-412/}));fireEvent.click(screen.getByRole("button",{name:"Open issue"}));expect(open).toHaveBeenCalledWith(WATCH_SUMMARY.open_assignments[0].url,"_blank","noopener");open.mockRestore();
  });
  it("keeps agenda items in their own View",async()=>{
    await brief();await personView("Agenda");const list=screen.getByRole("grid",{name:"Agenda"});
    expect(within(list).getByRole("row",{name:/Discuss API contract timeline/})).toBeInTheDocument();expect(within(list).getByRole("row",{name:/Review #612 priority/})).toBeInTheDocument();
  });
  it("keeps an empty Agenda free of invented items",async()=>{
    await brief({agenda_items:[]});await personView("Agenda");expect(within(screen.getByRole("grid",{name:"Agenda"})).queryAllByRole("row")).toHaveLength(0);
  });
  it("opens the selected last meeting with its own verb",async()=>{
    const list=await brief();fireEvent.click(within(list).getByRole("row",{name:/Sprint Review/}));expect(screen.getByRole("button",{name:"Open meeting"})).toBeEnabled();
  });
});
