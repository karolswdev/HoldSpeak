import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ArtifactPullout } from "./ArtifactPullout";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import type { Artifact } from "../../lib/primitives";

vi.mock("../surface/SurfaceFooter", () => ({ SurfaceFooter: ({ verbs }: { verbs: React.ReactNode }) => <footer>{verbs}</footer> }));
vi.mock("../components/DeskFilingStrip", () => ({ DeskFilingStrip: () => <div data-testid="filing-strip" /> }));
vi.mock("../documentSendsLazy", () => ({ ArtifactSendWells: () => <div data-testid="send-wells" /> }));

// Same stored-fixture boundary as test_web_routes_sync.py's exact-read case.
// No successful PR review or agent completion is asserted by this fixture.
const artifact: Artifact = { kind: "artifact", id: "art-held", artifactType: "run_output", title: "PR context needed",
  status: "pending-review", bodyMarkdown: "PR context was absent. No review was completed.",
  sources: [{ source_type: "workbench", source_ref: "wb-source" }] };
const object = (ref = artifact) => ({ kind: "artifact" as const, id: ref.id, title: ref.title, ref });
const refresh = vi.fn(async () => {});
beforeEach(() => { vi.clearAllMocks(); useDesk.setState({ items: { ...EMPTY_ITEMS }, refresh }); });

describe("Artifact source inspection", () => {
  it.each([["pending-review", "Awaiting review"], ["rejected", "Rejected"]])("names the stored %s state and reads its actual words", (status, label) => {
    render(<ArtifactPullout object={object({ ...artifact, status })} onClose={vi.fn()} />);
    expect(screen.getByLabelText(label)).toBeInTheDocument();
    expect(screen.getByText(artifact.bodyMarkdown)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /accept|approve|publish/i })).toBeNull();
    expect(refresh).not.toHaveBeenCalled();
  });

  it("an unavailable source shell exposes read Retry without blank material actions", () => {
    const missing = { ...artifact, bodyMarkdown: "", status: "", sourceRead: { state: "unavailable" as const, message: "Unknown artifact: art-held", hasMaterial: false } };
    render(<ArtifactPullout object={object(missing)} onClose={vi.fn()} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Source unavailable");
    expect(screen.queryByLabelText("Awaiting review")).toBeNull();
    expect(screen.queryByTestId("send-wells")).toBeNull();
    expect(screen.queryByTestId("filing-strip")).toBeNull();
    expect(screen.queryByRole("button", { name: "Copy" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Dictate about this" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Retry read" }));
    expect(refresh).toHaveBeenCalledTimes(1);
  });

  it("a later failed read keeps known material and marks its last-read status", () => {
    render(<ArtifactPullout object={object({ ...artifact, sourceRead: { state: "failed", message: "Connection refused", hasMaterial: true } })} onClose={vi.fn()} />);
    expect(screen.getByText(artifact.bodyMarkdown)).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Read failed");
    expect(screen.getByLabelText("Last read")).toBeInTheDocument();
    expect(screen.getByLabelText("Awaiting review")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy" })).toBeInTheDocument();
  });
});
