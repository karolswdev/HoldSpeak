import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";
import { InfoWindow } from "../InfoWindow";
import { CapabilitySection, openCapabilityEngines } from "../../pullouts/shared/CapabilitySection";
import { openSurfaceOr } from "../../shell";
import { readDurableDraft } from "../../../lib/durableDraft";

const { micCallbacks } = vi.hoisted(() => ({ micCallbacks: new Map<string, (text: string) => void>() }));
vi.mock("../MicButton", () => ({
  MicButton: ({ onText, label = "Speak", draftScope = "" }: { onText: (text: string) => void; label?: string; draftScope?: string }) => {
    micCallbacks.set(draftScope, onText);
    return <button type="button" aria-label={label} data-testid="field-mic" data-draft-scope={draftScope}/>;
  },
}));

const realOpenPullout = useDesk.getState().openPullout;

vi.mock("../DeskWindow", () => ({ DeskWindowFrame: ({ children }: { children: ReactNode }) => <div>{children}</div> }));
vi.mock("../../shell", async () => ({
  ...await vi.importActual<typeof import("../../shell")>("../../shell"),
  openSurfaceOr: vi.fn(),
}));

beforeEach(() => {
  vi.clearAllMocks();
  micCallbacks.clear();
  localStorage.clear();
  vi.stubGlobal("fetch", vi.fn(async () => new Response("{}", { headers: { "content-type": "application/json" } })));
  useDesk.setState({ items: { ...EMPTY_ITEMS }, selectedIds: [], drafts: {}, places: {}, zoneViewPrefs: {}, openPullout: vi.fn() });
});
afterEach(() => vi.unstubAllGlobals());

describe("common controls keep their actions", () => {
  it("opens resolved Info lineage and leaves unresolved lineage disabled", () => {
    useDesk.setState({ items: {
      ...EMPTY_ITEMS,
      note: [{ id: "note-1", title: "Plan", sources: ["meeting-1", "missing-source"] }],
      meeting: [{ id: "meeting-1", title: "Cutover review" }],
    } as never });
    render(<InfoWindow refId="note:note-1" />);
    const resolved = screen.getByRole("button", { name: "Cutover review" });
    expect(resolved).toHaveClass("btn");
    fireEvent.click(resolved);
    expect(useDesk.getState().openPullout).toHaveBeenCalledWith("meeting:meeting-1");
    const missing = screen.getByRole("button", { name: "missing-source" });
    expect(missing).toBeDisabled();
    fireEvent.click(missing);
    expect(useDesk.getState().openPullout).toHaveBeenCalledTimes(1);
  });

  it("opens the existing canonical Note from Info without choosing a same-ID meeting", () => {
    useDesk.setState({
      items: {
        ...EMPTY_ITEMS,
        meeting: [{ kind: "meeting", id: "shared", title: "Meeting collision" }],
        note: [{ kind: "note", id: "shared", title: "Source note" }],
        kb: [{ kind: "kb", id: "shared", name: "Source knowledge" }],
        project: [{ kind: "project", id: "shared", name: "Source project" }],
        artifact: [{ kind: "artifact", id: "result", title: "Kept result", sources: [
          { source_type: "note", source_ref: "note:shared" },
          { source_type: "knowledge", source_ref: "knowledge:shared" },
          { source_type: "project", source_ref: "project:shared" },
          { source_type: "note", source_ref: "note:missing" },
        ] }],
      } as never,
      openPullout: realOpenPullout,
      pullouts: [], windowsById: {}, panelMin: [], panelMax: [], panelOrder: [], panelRects: {},
    });
    render(<InfoWindow refId="artifact:result" />);
    expect(screen.getByRole("button", { name: "Source knowledge" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Source project" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "note:missing" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Source note" }));
    expect(useDesk.getState().pullouts.map((pullout) => pullout.id)).toEqual(["note:shared"]);
  });
});
