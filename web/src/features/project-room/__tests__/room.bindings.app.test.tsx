import { useEffect } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import { recordedGet } from "../../../test/recordedHub";
import { ProjectRoomCore } from "../ProjectRoomCore";
import { PreparePosture } from "../prepare/PreparePosture";
import { usePrepareController } from "../prepare/usePrepareController";
import { decodeBrief } from "../prepare/model";
import { ReviewPosture } from "../review/ReviewPosture";
import { useReviewController } from "../review/useReviewController";
import { useDesk } from "../../../desk/store";
import { EMPTY_ITEMS } from "../../../desk/api";
import { clearEngineCache } from "../../../desk/hooks/useEngine";
import CONFIRM from "./room-wires/binding-confirm.json";
import DISMISS from "./room-wires/binding-dismiss.json";
import RETIRE from "./room-wires/binding-retire.json";
import ACCEPT from "./room-wires/binding-accept.json";
import ANSWER from "./room-wires/binding-answer.json";
import DISCARD from "./room-wires/binding-discard.json";

const io = vi.hoisted(() => ({ api: vi.fn() }));
vi.mock("../../../lib/api", async original => ({ ...await original<typeof import("../../../lib/api")>(), apiFetch: (...args: unknown[]) => io.api(...args) }));
const press = (word: string) => fireEvent.click(screen.getAllByRole("button", { name: word }).at(-1)!);
const refusal = "This item changed or its saved version is missing. Nothing changed. Read again.";
type Tape = { project_id: string; path: string; request: unknown; read: any; gets: Record<string, unknown>; stale: any };
function replay(tape: Tape) {
  io.api.mockImplementation(async (path: string, init: { method?: string } = {}) => {
    if (path === tape.path && init.method === "POST") throw new ApiError(409, tape.stale.error || tape.stale.message, tape.stale);
    return recordedGet(tape.gets, path) ?? {};
  });
}
function Brief({ tape }: { tape: Tape }) {
  const ctrl = usePrepareController(tape.project_id, () => {});
  useEffect(() => { void ctrl.openBrief(decodeBrief(tape.read)); }, []);
  return <PreparePosture ctrl={ctrl} projectName="Bindings" onOpenRef={() => {}} onResultChange={() => {}} />;
}
function Review({ tape }: { tape: Tape }) {
  const ctrl = useReviewController(tape.project_id, null, () => {});
  useEffect(() => { void ctrl.enterReview("binding-review"); }, []);
  return <ReviewPosture ctrl={ctrl} />;
}
beforeEach(() => {
  io.api.mockReset(); localStorage.clear(); sessionStorage.clear(); clearEngineCache();
  useDesk.setState({ windowsById: {}, items: { ...EMPTY_ITEMS }, projects: [], inferenceTargets: [] });
});
async function assertRefused(tape: Tape) {
  await screen.findAllByText(new RegExp("Nothing changed\\. Read again\\."));
  expect(io.api).toHaveBeenCalledWith(tape.path, expect.objectContaining({ method: "POST", json: expect.objectContaining({ binding: tape.read.binding }) }));
  expect(screen.getByRole("button", { name: "Read again" })).toBeEnabled();
  press("Read again");
  await waitFor(() => expect(screen.queryByText(refusal, { exact: true })).toBeNull());
}
describe("Room answers carry their saved bindings", () => {
  it.each([["Confirm", CONFIRM], ["Dismiss", DISMISS]] as const)("binds proposal %s and renders the hub refusal", async (verb, raw) => {
    const tape = raw as Tape; replay(tape);
    render(<ProjectRoomCore scope={`project:${tape.project_id}`} scopeLabel="Bindings" />);
    const grid = await screen.findByRole("grid", { name: "Open" });
    await waitFor(() => expect(grid.querySelectorAll(".object-list-row").length).toBeGreaterThan(0));
    fireEvent.click(screen.getByRole("row", { name: new RegExp(tape.read.text) }));
    press(verb); if (verb === "Dismiss") press(verb);
    await assertRefused(tape);
  });
  it("binds watch removal and offers a new read instead of repeating it", async () => {
    const tape = RETIRE as Tape; replay(tape);
    render(<ProjectRoomCore scope={`project:${tape.project_id}`} scopeLabel="Bindings" />);
    fireEvent.click(await screen.findByRole("tab", { name: "Sources" }));
    fireEvent.click(await screen.findByRole("row", { name: /acme\/app/ }));
    press("Remove"); press("Remove");
    await assertRefused(tape);
    expect(io.api.mock.calls.filter(([path]) => path === tape.path)).toHaveLength(1);
  });
  it.each([["Accept", ANSWER], ["Finish review", ACCEPT]] as const)("binds review %s and renders the hub refusal", async (verb, raw) => {
    const tape = raw as Tape; replay(tape); render(<Review tape={tape} />);
    await screen.findByRole("grid", { name: "Review" });
    await waitFor(() => expect(screen.getByRole("button", { name: verb })).toBeEnabled());
    expect(screen.getByRole("button", { name: "Open" })).toBeDisabled();
    press(verb); await assertRefused(tape);
  });
  it("binds brief discard, keeps the brief on refusal, and can read it again", async () => {
    const tape = DISCARD as Tape; replay(tape); render(<Brief tape={tape} />);
    await screen.findByRole("grid", { name: "Prepare" });
    await waitFor(() => expect(screen.getByRole("button", { name: "Discard" })).toBeEnabled());
    press("Discard"); press("Discard");
    await assertRefused(tape);
  });
});
