import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";
import type { ResourcefulPolicy } from "../../detail-types";
import { InfoWindow } from "../InfoWindow";
import { WorkbenchResourceful } from "../WorkbenchResourceful";
import { CapabilitySection, openCapabilityEngines } from "../../pullouts/shared/CapabilitySection";
import { openSurfaceOr } from "../../shell";
import { useWriteReceipt } from "../../hooks/useWriteReceipt";
import { readDurableDraft } from "../../../lib/durableDraft";

const { micCallbacks } = vi.hoisted(() => ({ micCallbacks: new Map<string, (text: string) => void>() }));
vi.mock("../MicButton", () => ({
  MicButton: ({ onText, label = "Speak", draftScope = "" }: { onText: (text: string) => void; label?: string; draftScope?: string }) => {
    micCallbacks.set(draftScope, onText);
    return <button type="button" aria-label={label} data-testid="field-mic" data-draft-scope={draftScope}/>;
  },
}));

const realOpenPullout = useDesk.getState().openPullout;

const updatePolicy = vi.fn();
vi.mock("../../api", async () => ({
  ...await vi.importActual<typeof import("../../api")>("../../api"),
  updateResourcefulPolicy: (...args: unknown[]) => updatePolicy(...args),
}));
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

  it("keeps one resourceful policy write pending and releases its library actions", async () => {
    let accept: () => void = () => {};
    updatePolicy.mockImplementation(() => new Promise<void>((resolve) => { accept = resolve; }));
    const policy: ResourcefulPolicy = {
      workbench_id: "wb-1", enabled: true, idle_after_minutes: 15, cooldown_hours: 2,
      nightly_target: 1, night_only: true, night_start_hour: 22, night_end_hour: 6,
      routines: ["loose_ideas"], nightly_count: 0,
    };
    const write = vi.fn(async (_verb: string, run: () => Promise<void>) => { await run(); return { ok: true, value: undefined }; });
    const changed = vi.fn();
    render(<WorkbenchResourceful workbenchId="wb-1" policy={policy} write={write as never} onChanged={changed} />);
    const save = screen.getByRole("button", { name: "Save policy" });
    expect(save).toHaveClass("btn");
    fireEvent.click(save);
    fireEvent.click(save);
    expect(save).toHaveAttribute("aria-busy", "true");
    expect(screen.getByRole("button", { name: "Pause" })).toBeDisabled();
    expect(updatePolicy).toHaveBeenCalledTimes(1);
    await act(async () => { accept(); });
    expect(changed).toHaveBeenCalledOnce();
    expect(save).not.toBeDisabled();
    expect(updatePolicy).toHaveBeenCalledWith("wb-1", expect.objectContaining({ enabled: true, routines: ["loose_ideas"] }));
  });

  it("keeps receipt Enable Retry guarded and blocks Pause until that replay settles", async () => {
    let finish: () => void = () => {};
    updatePolicy.mockRejectedValueOnce(new TypeError("offline"))
      .mockImplementationOnce(() => new Promise<void>((resolve) => { finish = resolve; }))
      .mockResolvedValueOnce({});
    const policy: ResourcefulPolicy = {
      workbench_id: "wb-retry", enabled: false, idle_after_minutes: 15, cooldown_hours: 2,
      nightly_target: 1, night_only: false, night_start_hour: 22, night_end_hour: 6,
      routines: ["loose_ideas"], nightly_count: 0,
    };
    function Harness({ enabled }: { enabled: boolean }) {
      const { attempt, receipt } = useWriteReceipt();
      return <>{receipt}<WorkbenchResourceful workbenchId="wb-retry" policy={{ ...policy, enabled }} write={attempt} onChanged={vi.fn()} /></>;
    }
    const view = render(<Harness enabled={false} />);
    fireEvent.click(screen.getByRole("button", { name: "Enable resourcefulness" }));
    fireEvent.click(screen.getByRole("button", { name: "RUN AS OWNER?" }));
    expect(await screen.findByText("Could not turn on resourcefulness")).toBeTruthy();
    // An authoritative policy read now exposes Pause while the refused Enable
    // receipt remains. Its Retry still replays the original write callback.
    view.rerender(<Harness enabled />);
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    const pause = screen.getByRole("button", { name: "Pause" });
    expect(pause).toBeDisabled();
    expect(pause).toHaveAttribute("aria-busy", "true");
    fireEvent.click(pause);
    expect(updatePolicy).toHaveBeenCalledTimes(2);
    await act(async () => { finish(); });
    expect(pause).toBeEnabled();
    fireEvent.click(pause);
    await waitFor(() => expect(updatePolicy).toHaveBeenCalledTimes(3));
    expect(updatePolicy.mock.calls.map(([, update]) => update.enabled)).toEqual([true, true, false]);
    expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
  });


});
