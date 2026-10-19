import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS, fromWireDirectory } from "../api";
import { useDesk } from "../store";
import { DeskFilingStrip } from "./DeskFilingStrip";
import { apiRequest } from "../../lib/api";

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
