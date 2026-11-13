import { useEffect } from "react";
import { within, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { wireDayClock } from "../../../desk/surface";
import { ApiError } from "../../../lib/api";
import { isSensitiveElement } from "../../../desk/feedback/capture";
import { UpdatePosture } from "../update/UpdatePosture";
import { useUpdateController } from "../update/useUpdateController";
import { decodeUpdate } from "../update/model";
import { PreparePosture } from "../prepare/PreparePosture";
import { usePrepareController } from "../prepare/usePrepareController";
import { StewardPosture } from "../steward/StewardPosture";
import { useStewardController } from "../steward/useStewardController";
import { ReviewPosture } from "../review/ReviewPosture";
import { useReviewController } from "../review/useReviewController";
import { clearEngineCache } from "../../../desk/hooks/useEngine";
import HANDOFF from "./room-wires/send-handoff.json";
import TAPE from "./room-wires/grammar10.json";
import STEWARD from "../steward/__tests__/fixtures/steward.recorded.json";
import REVIEW from "./room-wires/daily-review.json";
import CLAIMS from "./room-wires/claims200.json";

const io = vi.hoisted(() => ({ api: vi.fn() }));
vi.mock("../../../lib/api", async original => ({ ...await original<typeof import("../../../lib/api")>(), apiFetch: (...args: unknown[]) => io.api(...args) }));
let routes: Record<string, any>;
function route(url: string, init: { method?: string } = {}) {
  const key = `${init.method || "GET"} ${url.split("?")[0]}`;
  const value = routes[key];
  if (value) return typeof value === "function" ? value(init) : structuredClone(value);
  if (url.endsWith("/briefs/route")) return TAPE.PREP2_ROUTE;
  if (url.endsWith("/briefs/manifest")) return TAPE.PREP2_MANIFEST;
  if (url.includes("/briefs")) return TAPE.BRIEFS_KEPT;
  if (url.includes("/updates")) return TAPE.UPDATES_AFTER_SENDS;
  if (url.includes("/steward/policy")) return STEWARD.getPolicy;
  if (url.includes("/steward/runs")) return STEWARD.list;
  if (url.endsWith("/watches")) return STEWARD.watches;
  return {};
}
function press(name: string) { fireEvent.click(screen.getAllByRole("button", { name }).at(-1)!); }
function choose(label: string, value: string) { fireEvent.change(screen.getByRole("combobox", { name: label }), { target: { value } }); }
function Updates({ published = false }: { published?: boolean }) {
  const ctrl = useUpdateController(TAPE.DRAFT.update.project_id, () => {});
  useEffect(() => { ctrl.openUpdate(decodeUpdate(published ? TAPE.UPDATES_AFTER_SENDS.updates[0] : TAPE.DRAFT.update)); }, []);
  return <UpdatePosture ctrl={ctrl} />;
}
function Prepare() {
  const ctrl = usePrepareController(TAPE.PREP2_ROOM.project_id, () => {});
  useEffect(() => { void ctrl.enterPrepare("Prepare the review"); }, []);
  return <PreparePosture ctrl={ctrl} projectName="Project" onOpenRef={() => {}} onResultChange={() => {}} />;
}
function Steward() {
  const ctrl = useStewardController(STEWARD.projectId, () => {});
  useEffect(() => { void ctrl.enterSteward(); }, []);
  return <StewardPosture ctrl={ctrl} onOpenReview={reviewOpened} onOpenUpdate={async () => {}} />;
}
const reviewOpened = vi.fn();
function Review() {
  const ctrl = useReviewController(REVIEW.project_id, null, () => {});
  useEffect(() => { void ctrl.enterReview(); }, []);
  return <ReviewPosture ctrl={ctrl} />;
}
beforeEach(() => { routes = {}; io.api.mockReset(); io.api.mockImplementation(async (...args) => route(...args as [string])); clearEngineCache(); localStorage.clear(); sessionStorage.clear(); reviewOpened.mockReset(); });

describe("Update seats", () => {
  it("reads produced claims as words and names their sources without opaque references", async () => {
    function Produced() {
      const ctrl = useUpdateController(CLAIMS.real.pid, () => {});
      useEffect(() => { ctrl.openUpdate(decodeUpdate(CLAIMS.real.drafted)); }, []);
      return <UpdatePosture ctrl={ctrl} />;
    }
    render(<Produced />);
    choose("View", "claims");
    const grid = screen.getByRole("grid", { name: "Updates" });
    expect(grid).not.toHaveTextContent("[critical]");
    expect(grid).not.toHaveTextContent("-- open");
    expect(grid).toHaveTextContent("Critical");
    expect(grid.querySelector(".object-list-selection-title")).toHaveTextContent("Vendor lock-in · Open");
    expect(grid.querySelector(".object-list-detail")).toHaveTextContent("Risk · Critical");
    fireEvent.click(grid.querySelector(".object-list-row")!);
    const facts = document.querySelector(".surface-inspector-facts")!;
    expect(facts).not.toHaveTextContent("item:pitem_");
    expect(facts).toHaveTextContent("Item");
  });
  it("reads a draft before opening its retained editor", async () => {
    render(<Updates />);
    await screen.findByRole("grid", { name: "Updates" });
    expect(document.querySelector(".surface-object-reader")).not.toBeNull();
    expect(screen.queryByRole("textbox", { name: "Update body" })).toBeNull();
    press("Edit");
    const editor = await screen.findByRole("textbox", { name: "Update body" });
    expect(isSensitiveElement(editor)).toBe(true);
    fireEvent.change(editor, { target: { value: "Keep these words while I read" } }); press("Cancel");
    expect(screen.getByText("Keep these words while I read")).toBeVisible();
    expect(screen.getByText("Not saved")).toBeVisible(); press("Edit");
    expect(screen.getByRole("textbox", { name: "Update body" })).toHaveValue("Keep these words while I read");
  });
  it("names an update by its date, reads markdown first and opens editing explicitly", async () => {
    const projectId = HANDOFF.room.project_id;
    routes[`GET /api/projects/${projectId}/updates`] = HANDOFF.updates;
    function Saved() {
      const ctrl = useUpdateController(projectId, () => {});
      useEffect(() => { void ctrl.openLatest(); }, []);
      return <UpdatePosture ctrl={ctrl} />;
    }
    render(<Saved />);
    await waitFor(() => expect(document.querySelector(".surface-object-reader .reading-document, .surface-object-reader .reading-document-body, .surface-object-reader p")).not.toBeNull());
    const grid = screen.getByRole("grid", { name: "Updates" });
    const selected = HANDOFF.updates.updates[0];
    expect(grid.querySelector(`[data-object-id="${selected.id}"] .object-list-selection-title`)).toHaveTextContent(wireDayClock(selected.published_at || selected.updated_at));
    expect(grid.querySelector('[data-col="to"]')).toBeNull();
    expect(screen.queryByRole("textbox", { name: "Update body" })).toBeNull();
  });

  it("keeps a failed save in the editor and retries with the newer words", async () => {
    render(<Updates />); press("Edit"); const field = await screen.findByRole("textbox", { name: "Update body" });
    fireEvent.change(field, { target: { value: "First edit" } });
    routes[`PUT /api/updates/${TAPE.DRAFT.update.id}`] = () => { throw new ApiError(503, "offline", {}); };
    press("Save"); await screen.findByText("Could not save the update · Your words stay here");
    fireEvent.change(field, { target: { value: "First edit and newer words" } });
    routes[`PUT /api/updates/${TAPE.DRAFT.update.id}`] = TAPE.PUT;
    press("Try again");
    await waitFor(() => expect(io.api.mock.calls.filter(([,init]) => init?.method === "PUT").at(-1)?.[1].json.body_md).toContain("First edit and newer words"));
  });
  it("reads a published body and opens the shared Send seat", async () => {
    render(<Updates published />);
    await screen.findByRole("grid", { name: "Updates" });
    expect(screen.queryByRole("textbox", { name: "Update body" })).toBeNull();
    press("Send"); expect(await screen.findByTestId("send-sheet")).toBeInTheDocument();
    expect(screen.getByTestId("send-sheet").closest(".surface-live-reading")).toBeNull();
  });
  it("keeps Mark delivered and To in this update's inspector", async () => {
    render(<Updates published />); await screen.findByRole("grid", { name: "Updates" }); press("Mark delivered");
    const to = screen.getByRole("textbox", { name: "Delivered to" }); fireEvent.change(to, { target: { value: "Steering group" } });
    expect(screen.getAllByRole("button", { name: "Mark delivered" }).at(-1)).toBeEnabled();
    press("Mark delivered");
    await waitFor(() => expect(io.api.mock.calls.some(([url,init]) => url.endsWith("/delivered") && init?.json?.delivered_to === "Steering group")).toBe(true));
  });
  it("keeps the update list and says a lost delivery result once while holding its retry", async () => {
    const projectId = HANDOFF.room.project_id;
    routes[`GET /api/projects/${projectId}/updates`] = HANDOFF.updates;
    const id = HANDOFF.updates.latest_published_update_id!;
    routes[`POST /api/updates/${id}/delivered`] = () => { throw new TypeError("Lost delivery answer"); };
    function SavedUpdates() {
      const ctrl = useUpdateController(projectId, () => {});
      useEffect(() => { void ctrl.openLatest(); }, []);
      return <UpdatePosture ctrl={ctrl} />;
    }
    render(<SavedUpdates />);
    await waitFor(() => expect(screen.getAllByRole("button", { name: "Mark delivered" }).at(-1)).toBeEnabled());
    press("Mark delivered");
    fireEvent.change(screen.getByRole("textbox", { name: "Delivered to" }), { target: { value: "Steering group" } });
    press("Mark delivered");
    await screen.findByText("Result unknown");
    expect(screen.queryByText("No delivery result")).toBeNull();
    expect(screen.getAllByText("Result unknown", { exact: true })).toHaveLength(1);
    const grid = screen.getByRole("grid", { name: "Updates" });
    for (const update of HANDOFF.updates.updates) expect(grid.querySelector(`[data-object-id="${update.id}"]`)).not.toBeNull();
    press("Try again");
    await waitFor(() => expect(io.api.mock.calls.filter(([url]) => url.endsWith("/delivered"))).toHaveLength(2));
    const calls = io.api.mock.calls.filter(([url]) => url.endsWith("/delivered"));
    expect(calls[1][1].json).toEqual(calls[0][1].json);
  });
  it("puts claims into one selection list and reviews only the selected claim", async () => {
    render(<Updates />); await screen.findByRole("grid", { name: "Updates" }); choose("View", "claims");
    const claim = TAPE.DRAFT.update.claims_json;
    const rows = screen.getByRole("grid", { name: "Updates" }).querySelectorAll(".object-list-row");
    expect(rows.length).toBeGreaterThan(0); fireEvent.click(rows[0]);
    press("Accept claim");
    await waitFor(() => expect(io.api.mock.calls.some(([url]) => url.includes("/claims/") && url.endsWith("/review"))).toBe(true));
  });
});
describe("Preparation seats", () => {
  it("reads the producer's brief headings in sentence case", async () => {
    routes[`POST /api/projects/${TAPE.PREP2_ROOM.project_id}/briefs/prepare`] = TAPE.PREPARE_OK;
    render(<Prepare />); await screen.findByRole("textbox", { name: "Purpose" }); press("Prepare");
    expect(await screen.findByRole("heading", { name: "Decide today" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Ask them" })).toBeVisible();
  });
  it("prepares from the retained purpose and reads the result in the same pane", async () => {
    routes[`POST /api/projects/${TAPE.PREP2_ROOM.project_id}/briefs/prepare`] = TAPE.PREPARE_OK;
    render(<Prepare />); const purpose = await screen.findByRole("textbox", { name: "Purpose" });
    fireEvent.change(purpose, { target: { value: "Review the cutover" } }); press("Prepare");
    await waitFor(() => expect(screen.queryByRole("textbox", { name: "Purpose" })).toBeNull());
    expect(document.querySelector(".surface-object-reader[aria-label=Brief]")).toBeInTheDocument();
    expect(io.api.mock.calls.find(([url,init]) => url.endsWith("/prepare") && init?.method === "POST")?.[1].json.purpose).toBe("Review the cutover");
  });
  it("keeps and copies the prepared brief; discard asks first", async () => {
    routes[`POST /api/projects/${TAPE.PREP2_ROOM.project_id}/briefs/prepare`] = TAPE.PREPARE_OK;
    render(<Prepare />); await screen.findByRole("textbox", { name: "Purpose" }); press("Prepare"); await waitFor(() => expect(document.querySelector(".surface-object-reader[aria-label=Brief]")).not.toBeNull());
    press("Discard"); expect(screen.getByRole("button", { name: "Cancel" })).toHaveFocus();
    expect(io.api.mock.calls.some(([url]) => url.endsWith("/discard"))).toBe(false);
    press("Cancel"); routes[`POST /api/briefs/${TAPE.PREPARE_OK.brief.id}/keep`] = TAPE.KEEP;
    press("Keep"); await waitFor(() => expect(io.api.mock.calls.some(([url]) => url.endsWith("/keep"))).toBe(true));
  });
  it("keeps sources, carried decisions, omitted records, claims and kept briefs as records", async () => {
    render(<Prepare />); await screen.findByRole("textbox", { name: "Purpose" });
    for (const value of ["sources", "carried", "kept"]) { choose("View", value); expect(screen.getByRole("grid", { name: "Prepare" })).toBeInTheDocument(); }
  });
});
describe("Steward and review seats", () => {
  it("opens a run as steps and offers its recorded review", async () => {
    const run = STEWARD.completed.detail.run;
    routes[`GET /api/steward/runs/${run.id}`] = STEWARD.completed.detail;
    render(<Steward />); const grid = await screen.findByRole("grid", { name: "Steward" });
    await waitFor(() => expect(grid.querySelectorAll(".object-list-row").length).toBeGreaterThan(0));
    fireEvent.doubleClick(grid.querySelector(".object-list-row")!);
    await waitFor(() => expect(screen.getByRole("combobox", { name: "Steward records" })).toHaveValue("steps"));
    press("Open review"); expect(reviewOpened).toHaveBeenCalledWith(run.summary.phase_results.compare.review_id);
  });
  it("keeps every saved policy field and the approval boundary in the settings form", async () => {
    render(<Steward />); await screen.findByRole("grid", { name: "Steward" }); press("Watch settings");
    expect(await screen.findByRole("checkbox", { name: "Unattended" })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Nudge text" })).toBeInTheDocument();
    expect(screen.getByRole("spinbutton", { name: "Actions per run" })).toHaveValue(STEWARD.getPolicy.policy.max_actions_per_run);
  });
  it("edits human fields with the same labels as the facts and preserves the wire patch", async () => {
    routes[`POST /api/projects/${REVIEW.project_id}/reviews`] = REVIEW;
    render(<Review />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Edit and accept" })).toBeEnabled());
    press("Edit and accept");
    expect(screen.getByRole("textbox", { name: "Text" })).toHaveValue("Send the dry-run report");
    expect(isSensitiveElement(screen.getByRole("textbox", { name: "Text" }))).toBe(true);
    expect(screen.queryByRole("textbox", { name: "card id" })).toBeNull();
    fireEvent.change(screen.getByRole("textbox", { name: "Text" }), { target: { value: "Read the saved rollback plan" } });
    press("Save and accept");
    await waitFor(() => expect(io.api.mock.calls.some(([, init]) => init?.json?.patch?.text === "Read the saved rollback plan")).toBe(true));
    const sent = io.api.mock.calls.find(([, init]) => init?.json?.patch?.text === "Read the saved rollback plan")![1].json.patch;
    expect(sent.card_id).toBe("philo13-b4-owned-action");
  });
  it("reads proposals into one list and keeps edit, defer and dismissal in the inspector", async () => {
    routes[`POST /api/projects/${REVIEW.project_id}/reviews`] = REVIEW;
    render(<Review />); await screen.findByRole("grid", { name: "Review" });
    await waitFor(() => expect(screen.getByRole("grid", { name: "Review" }).querySelectorAll(".object-list-row").length).toBeGreaterThan(0));
    expect(screen.getByRole("grid", { name: "Review" }).querySelector(".object-list-row [data-col=state]")).toHaveTextContent("Open"); press("Defer");
    expect(screen.getByRole("textbox", { name: "Until" })).toBeInTheDocument(); press("Cancel"); press("Dismiss");
    expect(screen.getByRole("button", { name: "Cancel" })).toHaveFocus();
  });
});
