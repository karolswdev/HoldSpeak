/* The retired row verbs now act on selection. These properties keep the
 * owner, source, write and stale-read fences of meetingKit.phase16. */
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { MeetingOutcomes } from "../MeetingDetail";
import { useMeetingData } from "../useMeetingData";
import { apiFetch } from "../../../../lib/api";
import { MEETING_OPEN_EVENT } from "../../../../desk/objectWindows";
import { useDesk } from "../../../../desk/store";
vi.mock("../../../../lib/api", async original => ({ ...await original<typeof import("../../../../lib/api")>(), apiFetch: vi.fn() }));
vi.mock("../../../../runtime/RuntimeBus", () => ({ useRuntimeBus: () => ({ subscribe: () => () => undefined }) }));
const meeting = { id: "m1", title: "Cutover", segments: [{ text: "Jordan owns the runbook" }] };
const row = (id = "p1", overrides = {}) => ({ id, meeting_id: "m1", kind: "action", text: `Task ${id}`, owner: "Jordan", due: "2026-11-05", support: "source_linked", state: "proposed", created_at: "", ...overrides });
const data = (proposals = [row()], overrides = {}) => ({ ftProposals: proposals, openActions: [], settledActions: [], segments: meeting.segments, busy: false, firstRead: true, prepared: [],
  confirmProposal: vi.fn(), dismissProposal: vi.fn(), deferProposal: vi.fn(), completeAction: vi.fn(), retryOutcomeReview: vi.fn(), ...overrides });
const select = async (text: string) => { const cell = await screen.findByText(text); fireEvent.click(cell.closest('[role="row"]')!); };
const verb = (name: string) => screen.getByRole("button", { name });
beforeEach(() => { vi.mocked(apiFetch).mockReset(); vi.mocked(apiFetch).mockResolvedValue({} as never); });

it("a task with gaps opens one inspector; confirmation sends the owner name and date", async () => {
  const model = data([row("gap", { owner: null, due: null })]);
  render(<MeetingOutcomes data={model as never} meeting={meeting} mode="commitments" />);
  await select("Task gap"); fireEvent.click(verb("Edit"));
  expect(screen.queryByRole("grid")).toBeNull();
  fireEvent.change(screen.getByLabelText("Task"), { target: { value: "Ship the runbook" } });
  fireEvent.change(screen.getByLabelText("Owner"), { target: { value: "Jordan" } });
  fireEvent.change(screen.getByLabelText("Due"), { target: { value: "2026-11-12" } });
  fireEvent.click(within(screen.getByRole("region", { name: "Edit proposal" })).getByRole("button", { name: "Confirm" }));
  expect(model.confirmProposal).toHaveBeenCalledWith("gap", expect.objectContaining({ text: "Ship the runbook", owner: "Jordan", due: "2026-11-12" }));
  expect(vi.mocked(apiFetch).mock.calls.some(([path]) => path.includes("owner-aliases"))).toBe(false);
});
it("Confirm keeps the decision; Dismiss removes only its selected row", async () => {
  let proposals = [row("one", { kind: "decision" }), row("two", { kind: "decision" })];
  vi.mocked(apiFetch).mockImplementation(async (path, init) => {
    if (init?.method === "POST") { proposals = path.endsWith("confirm") ? proposals.map(p => p.id === "one" ? { ...p, state: "confirmed" } : p) : proposals.filter(p => p.id !== "two"); return {} as never; }
    if (path.endsWith("/follow-through-proposals") || path.endsWith("/outcome-review")) return { proposals } as never;
    if (path === "/api/meetings/m1") return meeting as never;
    return {} as never;
  });
  function Harness() { const model = useMeetingData(meeting, () => undefined); return <MeetingOutcomes data={model} meeting={meeting} />; }
  render(<Harness />); await select("Task one"); fireEvent.click(verb("Confirm"));
  await waitFor(() => expect(verb("Confirm")).toBeDisabled());
  expect(screen.getByRole("grid")).toHaveTextContent("Task one");
  await select("Task two"); fireEvent.click(verb("Dismiss"));
  await waitFor(() => expect(screen.queryByText("Task two")).toBeNull());
  expect(screen.getByRole("grid")).toHaveTextContent("Task one");
});
it.each([null, undefined, -1, 1, 0.5, "0", 0])("only a stored in-range numeric segment opens its exact source (%s)", async segment => {
  const opened = vi.fn(); window.addEventListener(MEETING_OPEN_EVENT, opened);
  render(<MeetingOutcomes data={data([row("source", { kind: "decision", segment_index: segment })]) as never} meeting={meeting} />);
  await select("Task source"); if (segment !== 0) expect(verb("Show in transcript")).toBeDisabled();
  if (segment === 0) { expect(verb("Show in transcript")).toBeEnabled(); fireEvent.click(verb("Show in transcript")); expect(opened).toHaveBeenCalledWith(expect.objectContaining({ detail: expect.objectContaining({ meetingId: "m1", segment: 0 }) })); }
  window.removeEventListener(MEETING_OPEN_EVENT, opened);
});
it("a failed authoritative person read retries without a write; names alone never enable People", async () => {
  let reads = 0;
  vi.mocked(apiFetch).mockImplementation(async path => { if (path === "/api/door") { if (++reads === 1) throw new Error("offline"); return { board: { now: [{ id: "a1", source: "action_item", person_relationship_id: "rel-jordan" }] } } as never; } return {} as never; });
  const model = data([row("person", { state: "confirmed", action_item_id: "a1" })]);
  render(<MeetingOutcomes data={model as never} meeting={meeting} mode="commitments" />);
  await select("Task person"); await screen.findByRole("alert"); expect(verb("People")).toBeDisabled();
  fireEvent.click(verb("Check person")); await waitFor(() => expect(verb("People")).toBeEnabled());
  expect(reads).toBe(2); expect(model.confirmProposal).not.toHaveBeenCalled(); expect(model.completeAction).not.toHaveBeenCalled();
  expect(vi.mocked(apiFetch).mock.calls.every(([,init]) => !init?.method)).toBe(true);
});
it("an ambiguous person join never enables People", async () => {
  vi.mocked(apiFetch).mockResolvedValue({ board: { now: [{ id: "a1", source: "action_item", person_relationship_id: "one" }, { id: "a1", source: "action_item", person_relationship_id: "two" }] } } as never);
  render(<MeetingOutcomes data={data([row("person", { state: "confirmed", action_item_id: "a1" })]) as never} meeting={meeting} mode="commitments" />);
  await select("Task person"); await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/door")); expect(verb("People")).toBeDisabled();
});
it("a late person answer cannot attach the old row's relationship to a new selection", async () => {
  const answers: Array<(body: unknown) => void> = [];
  vi.mocked(apiFetch).mockImplementation(() => new Promise(resolve => answers.push(resolve)) as never);
  render(<MeetingOutcomes data={data([row("a", { state: "confirmed", action_item_id: "a" }), row("b", { state: "confirmed", action_item_id: "b" })]) as never} meeting={meeting} mode="commitments" />);
  await select("Task a"); await waitFor(() => expect(answers).toHaveLength(1));
  await select("Task b"); await waitFor(() => expect(answers).toHaveLength(2));
  await act(async () => answers[1]({ board: { now: [] } }));
  await act(async () => answers[0]({ board: { now: [{ id: "b", source: "action_item", person_relationship_id: "stale" }] } }));
  expect(verb("People")).toBeDisabled(); expect(verb("Check person")).toBeEnabled();
});
it("recorded decisions open their object; an unlinked decision starts Decide", async () => {
  const openSurfaceWindow = vi.fn(), onDecide = vi.fn(); useDesk.setState({ openSurfaceWindow } as never);
  const model = data([row("unlinked", { kind: "decision", state: "confirmed" })], { meetingDecisions: [{ id: "d1", text: "Recorded decision", record_id: "rec1", lifecycle: "active" }] });
  render(<MeetingOutcomes data={model as never} meeting={meeting} onDecide={onDecide} />);
  await select("Recorded decision"); fireEvent.click(verb("Open")); expect(openSurfaceWindow).toHaveBeenCalledWith("open-decisions", "record:rec1");
  await select("Task unlinked"); fireEvent.click(verb("Open")); expect(onDecide).toHaveBeenCalledOnce();
});
