import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS, fromWireDirectory } from "../api";
import { useDesk } from "../store";
import { DeskFilingStrip } from "./DeskFilingStrip";
import { apiRequest } from "../../lib/api";
import { play as sfx } from "../../lib/sfx";

vi.mock("../../lib/sfx", () => ({ play: vi.fn() }));

vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  apiRequest: vi.fn(async (path: string) => new Response(JSON.stringify(
    path === "/api/kbs" ? { kbs: [] } : path === "/api/projects" ? { projects: [] } : { knowledge: [], projects: [] },
  ), { status: 200, headers: { "Content-Type": "application/json" } })),
}));
const parent = fromWireDirectory({ id: "parent", name: "Platform", parent_id: null, member_ids: ["note:note-1"] })!;
const child = fromWireDirectory({ id: "child", name: "Architecture", parent_id: "parent", member_ids: [] })!;

beforeEach(() => {
  useDesk.setState({ items: { ...EMPTY_ITEMS, directory: [parent, child] } });
});

describe("Directory filing location", () => {
  it("names the real parent of a child drawer without requiring a second membership edge", async () => {
    render(<DeskFilingStrip objectKind="directory" objectId="child" objectRef="zone:child" />);
    expect(await screen.findByText("Filed · Platform")).toBeInTheDocument();
    expect(screen.queryByText("Filed · Desk root")).toBeNull();
  });
  it("keeps a root drawer at Desk root", async () => {
    render(<DeskFilingStrip objectKind="directory" objectId="parent" objectRef="zone:parent" />);
    expect(await screen.findByText("Filed · Desk root")).toBeInTheDocument();
  });
  it("retains the existing membership location for a Note", async () => {
    render(<DeskFilingStrip objectKind="note" objectId="note-1" objectRef="note:note-1" />);
    expect(await screen.findByText("Filed · Platform")).toBeInTheDocument();
  });

  it("names both drawer memberships together without a Knowledge group or count", async () => {
    vi.mocked(apiRequest).mockImplementationOnce(async () => new Response(JSON.stringify({
      knowledge: [{ knowledge_id: "reference" }], projects: [],
    }))).mockImplementationOnce(async () => new Response(JSON.stringify({
      kbs: [{ id: "reference", name: "Reference", deleted: false }],
    }))).mockImplementationOnce(async () => new Response(JSON.stringify({ projects: [] })));
    render(<DeskFilingStrip objectKind="note" objectId="note-1" objectRef="note:note-1" />);
    expect(await screen.findByText("Filed · Platform · Reference")).toBeInTheDocument();
    const groups = document.querySelectorAll(".desk-pullout-filed-axis");
    expect(groups).toHaveLength(1);
    expect(groups[0].querySelector(".surface-eyebrow")).toHaveTextContent("Drawers");
    expect(groups[0]).toHaveTextContent("Platform");
    expect(groups[0]).toHaveTextContent("Reference");
    expect(screen.queryByText("Knowledge")).toBeNull();
  });
});

/* HS-S42: a decision's Projects axis acts on its canonical record; its
 * drawers stay on the source decision. */
describe("canonical project axis", () => {
  const SOURCE = "desk_decision:d1";
  const RECORD = "decision_record:rec_1";
  const writes: string[] = [];
  let canonicalRows: Array<Record<string, unknown>> = [];
  let sourceRows: Array<Record<string, unknown>> = [];
  let putStatus = 200;
  const reply = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

  beforeEach(() => {
    writes.length = 0;
    canonicalRows = [];
    sourceRows = [];
    putStatus = 200;
    vi.mocked(sfx).mockReset();
    useDesk.setState({ items: { ...EMPTY_ITEMS, directory: [] } });
    vi.mocked(apiRequest).mockImplementation(async (path: string, init?: RequestInit) => {
      const method = init?.method ?? "GET";
      const url = decodeURIComponent(path);
      if (method !== "GET") {
        writes.push(`${method} ${url}`);
        if (method === "PUT" && url.includes(RECORD)) {
          if (putStatus !== 200) return reply({ error: "refused" }, putStatus);
          canonicalRows = [{ project_id: url.split("/")[3], relationship: "member" }];
        }
        if (method === "DELETE" && url.includes(RECORD)) canonicalRows = [];
        return reply({ success: true, removed: true });
      }
      if (url === "/api/kbs") return reply({ kbs: [{ id: "drawer", name: "Reference" }] });
      if (url === "/api/projects") return reply({ projects: [{ id: "atlas", name: "Atlas" }, { id: "ledger", name: "Ledger" }] });
      if (url === `/api/desk/relationships/${RECORD}`) return reply({ resource_ref: RECORD, projects: canonicalRows, knowledge: [] });
      if (url === `/api/desk/relationships/${SOURCE}`) return reply({ resource_ref: SOURCE, projects: sourceRows, knowledge: [] });
      return reply({});
    });
  });
  const strip = (projectRef: string | null | undefined) =>
    render(<DeskFilingStrip objectKind="decision" objectId="d1" objectRef={SOURCE} projectRef={projectRef} projectNote="Decision record not read" bare />);

  it("Assign writes the record's member edge; a drawer still writes the source ref", async () => {
    strip(RECORD);
    fireEvent.click(await screen.findByRole("button", { name: "Assign to Ledger Project" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Remove from Ledger Project" })).toHaveAttribute("aria-pressed", "true"));
    fireEvent.click(screen.getByRole("button", { name: "Remove from Ledger Project" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Assign to Ledger Project" })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /Reference/ }));
    await waitFor(() => expect(writes).toHaveLength(3));
    expect(writes).toEqual([
      `PUT /api/projects/ledger/resources/${RECORD}`,
      `DELETE /api/projects/ledger/resources/${RECORD}`,
      `PUT /api/kbs/drawer/members/${SOURCE}`,
    ]);
  });

  it("a row of another kind shows its kind and is never toggled", async () => {
    canonicalRows = [{ project_id: "atlas", relationship: "source" }];
    strip(RECORD);
    const chip = await screen.findByRole("button", { name: "Atlas Project links it as source" });
    expect(chip).toBeDisabled();
    expect(screen.queryByRole("button", { name: /Remove from Atlas/ })).toBeNull();
    expect(writes).toEqual([]);
  });

  it("the source's own project rows show read-only, apart from the record's", async () => {
    sourceRows = [{ project_id: "atlas", relationship: "member" }];
    strip(RECORD);
    const source = await screen.findByTestId("filing-source-projects");
    expect(source).toHaveTextContent("Atlas");
    expect(within(source).queryByRole("button")).toBeNull();
    expect(screen.getByRole("button", { name: "Assign to Atlas Project" })).toHaveAttribute("aria-pressed", "false");
  });

  it("a refused PUT plays no filing sound and says it failed", async () => {
    putStatus = 409;
    strip(RECORD);
    fireEvent.click(await screen.findByRole("button", { name: "Assign to Atlas Project" }));
    await waitFor(() => expect(screen.getByText("Filing unavailable")).toBeInTheDocument());
    expect(sfx).not.toHaveBeenCalledWith("file");
    expect(sfx).toHaveBeenCalledWith("error");
    expect(screen.getByRole("button", { name: "Assign to Atlas Project" })).toHaveAttribute("aria-pressed", "false");
  });

  it("an unknown record identity closes the Projects axis and leaves drawers working", async () => {
    sourceRows = [{ project_id: "atlas", relationship: "member" }];
    strip(null);
    expect(await screen.findByTestId("filing-projects-closed")).toHaveTextContent("Decision record not read");
    expect(screen.queryByRole("button", { name: /Atlas Project/ })).toBeNull();
    expect(screen.getByRole("button", { name: /Reference/ })).toBeEnabled();
  });

  it("left out, projectRef keeps the source ref for Projects (every other consumer)", async () => {
    strip(undefined);
    fireEvent.click(await screen.findByRole("button", { name: "Assign to Atlas Project" }));
    await waitFor(() => expect(writes).toEqual([`PUT /api/projects/atlas/resources/${SOURCE}`]));
  });
});
