import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { thoughtForNote, type Thought } from "../thoughts";
import { useDesk } from "../store";
import { Pullout } from "./Pullout";

vi.mock("./DeskWindow", () => ({ DeskWindowFrame: ({ children }: { children: React.ReactNode }) => <section aria-label="Legacy window">{children}</section> }));
vi.mock("../pullouts", () => ({ PULLOUT_CONTENT: { note: () => null } }));
vi.mock("../pullouts/NotePullout", () => ({ NotePullout: () => <div>Ordinary Note editor</div> }));
vi.mock("../thought-workspace/ThoughtWorkspaceWindow", () => ({ ThoughtWorkspaceWindow: ({ thought }: { thought: Thought }) => <section aria-label="Thought Workbench">{thought.working_note.title}</section> }));
vi.mock("../sprites", () => ({ spriteUrl: () => "note.png" }));
vi.mock("../thoughts", async (importOriginal) => ({ ...(await importOriginal<typeof import("../thoughts")>()), thoughtForNote: vi.fn() }));

const thought: Thought = {
  id: "thought-1", source: { kind: "typed" }, raw_captured_at: "now", state: "working",
  aggregate_revision: 1, lifecycle_revision: 1, working_revision: 1, attachment_revision: 0,
  working_note: { id: "note-1", title: "Owned Note", body_markdown: "Body", tags: [] }, filing_status: "filed",
};
const object = { kind: "note" as const, id: "note-1", title: "Owned Note", ref: { kind: "note", title: "Owned Note", bodyMarkdown: "Body" } } as never;

afterEach(() => { cleanup(); vi.clearAllMocks(); });

describe("Pullout Thought ownership routing", () => {
  it("routes a Thought-owned Note to exactly one dedicated Workbench", async () => {
    useDesk.setState({ profiles: [], closePullout: vi.fn() });
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought });
    render(<Pullout o={object} />);

    expect(await screen.findByRole("region", { name: "Thought Workbench" })).toHaveTextContent("Owned Note");
    expect(screen.getAllByRole("region", { name: "Thought Workbench" })).toHaveLength(1);
    expect(screen.queryByText("Ordinary Note editor")).not.toBeInTheDocument();
  });

  it("leaves an ordinary Note in the ordinary editor", async () => {
    useDesk.setState({ profiles: [], closePullout: vi.fn() });
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "ordinary", eligibility: "eligible", reason: null, note: { id: "note-1", title: "Owned Note", body_markdown: "Body", tags: [], revision: 1 } });
    render(<Pullout o={object} />);

    expect(await screen.findByText("Ordinary Note editor")).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Thought Workbench" })).not.toBeInTheDocument();
  });
});
