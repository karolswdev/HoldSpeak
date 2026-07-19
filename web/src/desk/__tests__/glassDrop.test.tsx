// HS-101 B7 — through the glass: the drop contract. Files decide by
// the hub's own suffix table and refuse BY NAME; a desk object
// dropped on a marked well lands in the composer's grounding.
import { fireEvent, render, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  AUDIO_SUFFIXES,
  TRANSCRIPT_SUFFIXES,
  glassFileKind,
  glassFileRefusal,
} from "../glassDrop";
import { GroundingSection } from "../components/GroundingSection";

vi.mock("../store", () => ({
  useDesk: (selector: (s: unknown) => unknown) =>
    selector({ draggingId: null }),
}));

vi.mock("../grounding", () => ({
  emptyGrounding: () => ({ meetings: [] }),
  groundingIsEmpty: () => true,
  groundingLabel: () => "Ground this ask",
  groundingTokens: () => 0,
  fetchGroundingMeeting: vi.fn().mockResolvedValue({
    id: "m1",
    title: "Release sync",
    include: { digest: true },
    tokens: 10,
  }),
  fetchGroundingResource: vi
    .fn()
    .mockResolvedValue({ ref: "note:n1", kind: "Note", title: "Q3", tokens: 5 }),
}));

describe("the file-drop decision (canon §6.4)", () => {
  it("every hub-supported suffix imports; junk refuses by name", () => {
    for (const suffix of [...TRANSCRIPT_SUFFIXES]) {
      expect(glassFileKind(`meeting${suffix}`)).toBe("transcript");
    }
    for (const suffix of [...AUDIO_SUFFIXES]) {
      expect(glassFileKind(`call${suffix}`)).toBe("audio");
    }
    expect(glassFileKind("archive.zip")).toBeNull();
    expect(glassFileKind("noext")).toBeNull();
    expect(glassFileKind("UPPER.VTT")).toBe("transcript");
    expect(glassFileRefusal("archive.zip")).toContain(".zip");
    expect(glassFileRefusal("archive.zip")).toContain("transcript");
  });
});

describe("the desk-object drop well (canon rule 4)", () => {
  it("a desk:glass-drop event adds the object to the grounding", async () => {
    const onChange = vi.fn();
    const { container } = render(
      <GroundingSection
        meetings={[]}
        resources={[{ ref: "note:n1", kind: "Note", id: "n1", title: "Q3" }]}
        selection={{ meetings: [] }}
        onChange={onChange}
        limitTokens={1000}
      />,
    );
    const well = container.querySelector("[data-glass-accept~='desk-object']");
    expect(well).toBeTruthy();
    fireEvent(
      well as Element,
      new CustomEvent("desk:glass-drop", {
        detail: { id: "n1", kind: "note" },
      }),
    );
    await waitFor(() => expect(onChange).toHaveBeenCalled());
    const next = onChange.mock.calls.at(-1)?.[0];
    expect(next.resources?.[0]?.ref).toBe("note:n1");
  });
});
