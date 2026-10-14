import { useState } from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { emptyGrounding, type GroundingResource, type GroundingSelection } from "../../grounding";
import { GroundingSection } from "../GroundingSection";

const mocks = vi.hoisted(() => ({ resource: vi.fn() }));
vi.mock("../../grounding", async (importOriginal) => ({
  ...await importOriginal<typeof import("../../grounding")>(),
  fetchGroundingResource: mocks.resource,
}));

const resources = ["Alpha", "Beta"].map((title) => ({ ref: `note:${title}`, kind: "Note", id: title, title }));
function Harness() {
  const [selection, setSelection] = useState<GroundingSelection>(emptyGrounding);
  return <><GroundingSection meetings={[]} resources={resources} selection={selection} onChange={setSelection} limitTokens={16384} />
    <output data-testid="chosen">{JSON.stringify(selection.resources?.map((row) => row.ref) ?? [])}</output></>;
}

describe("grounding choices retain the owner's selection", () => {
  beforeEach(() => { mocks.resource.mockReset(); });

  it("keeps both choices when their async reads resolve in reverse order", async () => {
    const readers = new Map<string, (value: GroundingResource) => void>();
    mocks.resource.mockImplementation((ref: string) => new Promise((resolve) => readers.set(ref, resolve)));
    render(<Harness />);
    fireEvent.click(screen.getByText("Ground this ask"));
    fireEvent.click(await screen.findByRole("checkbox", { name: "Alpha" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Beta" }));
    expect(mocks.resource).toHaveBeenCalledTimes(2);
    await act(async () => readers.get("note:Beta")!({ ...resources[1], chars: 40 }));
    await act(async () => readers.get("note:Alpha")!({ ...resources[0], chars: 40 }));
    await waitFor(() => expect(JSON.parse(screen.getByTestId("chosen").textContent!)).toEqual(["note:Beta", "note:Alpha"]));
    expect(screen.getByRole("checkbox", { name: "Alpha" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Beta" })).toBeChecked();
  });

  it("offers one keyboard control per choice without nesting an input inside a button", async () => {
    render(<Harness />);
    fireEvent.click(screen.getByText("Ground this ask"));
    await screen.findByRole("checkbox", { name: "Alpha" });
    for (const checkbox of screen.getAllByRole("checkbox")) expect(checkbox.closest("button")).toBeNull();
  });
});
