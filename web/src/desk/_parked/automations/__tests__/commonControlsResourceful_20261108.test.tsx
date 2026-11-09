// PARKED 20261108: the two WorkbenchResourceful tests, split from
// src/desk/components/__tests__/commonControls.test.tsx when the queue view was
// parked. Not collected (vitest excludes _parked). Restore with git revert.
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
