// The detail's declared route binds the run even when the list never loaded it.
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { forgetExecutedReceipts } from "../../../meetings/summaryRoute";
import { MeetingRecord } from "../history/MeetingRecord";
import { meetingAction } from "../../../desk/__tests__/helpers/meetingReader";
import recorded from "../../../desk/__tests__/fixtures/meetings-hub/hs170.json";
import summaryWire from "../../../../../tests/fixtures/philo3_summary_wire.json";
vi.mock("../../../lib/api", async original => ({...(await original<typeof import("../../../lib/api")>()),apiFetch:vi.fn()}));
const subscribe = () => () => undefined;
vi.mock("../../../runtime/RuntimeBus", () => ({useRuntimeBus:()=>({state:"connected",lastFrame:null,subscribe}),useRuntimeFrame:()=>null}));
const detail=recorded["/api/meetings/m-off-words?include_parked=true"], answer=recorded["POST /api/meetings/m-off-words/intelligence/run"];
describe("a deep-linked summary", () => {
  beforeEach(()=>{vi.mocked(apiFetch).mockReset();forgetExecutedReceipts();});
  it("binds the detail route, accepts the queued answer and shows its finished summary without a reload", async () => {
    let current: Record<string,unknown>=detail;
    vi.mocked(apiFetch).mockImplementation(async (path,init)=>{
      if (path.endsWith("/intelligence/run") && init?.method === "POST") return answer as never;
      if (String(path).split("?")[0] === "/api/meetings/m-off-words") return current as never;
      if (String(path).startsWith("/api/meetings?")) return {meetings:[]} as never;
      return {} as never;
    });
    render(<MeetingRecord meetingId={detail.id} onClose={()=>undefined} />);
    expect(screen.getByRole("tab",{name:"Summary"})).toHaveAttribute("aria-selected","true");
    const verb=await meetingAction("Summarise",false); await waitFor(()=>expect(verb).toBeEnabled());
    expect(verb).toHaveAttribute("title","Summary runs on this device");
    fireEvent.click(verb);
    await waitFor(()=>expect(apiFetch).toHaveBeenCalledWith(`/api/meetings/${detail.id}/intelligence/run`,{method:"POST",json:{expected_selection_hash:detail.planned_route.selection_hash}}));
    expect(await screen.findByTestId("meeting-summary-state")).toHaveTextContent("Summary running");
    // Both bodies are recorded producer answers. Only meeting/job identity is
    // normalized to stage a delayed completion of this admitted 202 in one reader.
    const ready=summaryWire.cases.find(row=>row.state === "success")!.detail;
    const queued=summaryWire.cases.find(row=>row.state === "retry")!.detail;
    current={...queued,id:detail.id,run_receipt:{...queued.run_receipt,meeting_id:detail.id,job_id:answer.jobId}};
    act(()=>window.dispatchEvent(new Event("focus")));
    await waitFor(()=>expect(screen.getByTestId("meeting-summary-state")).toHaveTextContent("Summary queued"));
    current={...ready,id:detail.id};
    act(()=>window.dispatchEvent(new Event("focus")));
    await waitFor(()=>expect(screen.getByTestId("meeting-summary-state")).toHaveTextContent("Summary running"));
    expect(screen.queryByTestId("meeting-summary")).toBeNull();
    current={...ready,id:detail.id,run_receipt:{...ready.run_receipt,meeting_id:detail.id,job_id:answer.jobId}};
    act(()=>window.dispatchEvent(new Event("focus")));
    await waitFor(()=>expect(screen.getByTestId("meeting-summary")).toHaveTextContent(ready.intel!.summary));
    expect(screen.queryByTestId("meeting-summary-state")).toBeNull();
    expect(screen.getByRole("tab",{name:"Summary"})).toHaveAttribute("aria-selected","true");
  });
});
