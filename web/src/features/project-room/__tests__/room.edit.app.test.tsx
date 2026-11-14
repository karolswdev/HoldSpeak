import { useEffect } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import { UpdatePosture } from "../update/UpdatePosture";
import { useUpdateController } from "../update/useUpdateController";
import { useReviewController } from "../review/useReviewController";
import { ReviewPosture } from "../review/ReviewPosture";
import { decodeUpdate } from "../update/model";
import { useDesk } from "../../../desk/store";
import { clearEngineCache } from "../../../desk/hooks/useEngine";
import WIRE from "./room-wires/edit14.json";

const io = vi.hoisted(() => ({ api: vi.fn(), fail: false }));
vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: (...args: unknown[]) => io.api(...args),
}));
function Editor() {
  const ctrl = useUpdateController(WIRE.pid, () => {});
  useEffect(() => {
    ctrl.openUpdate(decodeUpdate(WIRE.update));
  }, []);
  return <UpdatePosture ctrl={ctrl} />;
}
function ItemReview() {
  const ctrl = useReviewController(WIRE.pid, null, () => {});
  useEffect(() => { void ctrl.enterReview("room-edit-review"); }, []);
  return <ReviewPosture ctrl={ctrl} />;
}
beforeEach(() => {
  useDesk.setState({drafts:{}});
  clearEngineCache();
  localStorage.clear();
  sessionStorage.clear();
  io.fail = false;
  io.api.mockReset();
  io.api.mockImplementation(async (url: string, init?: { method?: string }) => {
    if (init?.method === "PUT") {
      if (io.fail)
        throw new ApiError(
          WIRE.stale.status,
          WIRE.stale.answer.body.message,
          WIRE.stale.answer.body,
        );
      return structuredClone(WIRE.saved);
    }
    return {};
  });
});
it("edits the selected claim's subject and declared choices and reads the saved result", async () => {
  render(<Editor />);
  fireEvent.click(screen.getByRole("button", { name: "Edit" }));
  const field = screen.getByRole("textbox", { name: "Subject" });
  expect(field).not.toHaveValue(expect.stringContaining("[critical]"));
  expect(field).not.toHaveValue(expect.stringContaining("-- open"));
  expect(
    screen
      .getByRole("grid", { name: "Updates" })
      .querySelectorAll(".object-list-row").length,
  ).toBeGreaterThan(1);
  expect(screen.getByRole("combobox", { name: "Kind" })).toHaveValue("risk");
  fireEvent.change(field, { target: { value: WIRE.edit.values.subject } });
  fireEvent.change(screen.getByRole("combobox", { name: "State" }), {
    target: { value: WIRE.edit.values.state },
  });
  fireEvent.click(screen.getAllByRole("button", { name: "Save" }).at(-1)!);
  await waitFor(() =>
    expect(document.querySelector(".surface-object-reading")).toHaveTextContent(
      "Read the saved rollback plan",
    ),
  );
  const saved = io.api.mock.calls.find(([, init]) => init?.method === "PUT")![1]
    .json;
  expect(saved.claim_edits).toEqual([WIRE.edit]);
  expect(saved.body_md).toBeUndefined();
});
it("keeps the edited subject and choices when the hub refuses the save", async () => {
  io.fail = true;
  render(<Editor />);
  fireEvent.click(screen.getByRole("button", { name: "Edit" }));
  const field = screen.getByRole("textbox", { name: "Subject" });
  fireEvent.change(field, { target: { value: WIRE.edit.values.subject } });
  fireEvent.click(screen.getAllByRole("button", { name: "Save" }).at(-1)!);
  expect(await screen.findByText(/Could not save the update/)).toBeVisible();
  expect(screen.getByRole("textbox", { name: "Subject" })).toHaveValue(
    WIRE.edit.values.subject,
  );
  expect(screen.getByRole("combobox", { name: "State" })).toHaveValue("open");
});


it("keeps each claim draft when selection changes and when the form closes", () => {
  render(<Editor />);
  fireEvent.click(screen.getByRole("button", {name:"Edit"}));
  fireEvent.change(screen.getByRole("textbox", {name:"Subject"}), {target:{value:"Keep these words across selection"}});
  const rows=screen.getByRole("grid", {name:"Updates"}).querySelectorAll(".object-list-row");
  fireEvent.click(rows[1]);
  expect(screen.getByText("This claim has no separate kind or state.")).toBeVisible();
  fireEvent.click(rows[0]);
  expect(screen.getByRole("textbox", {name:"Subject"})).toHaveValue("Keep these words across selection");
  fireEvent.click(screen.getByRole("button", {name:"Cancel"}));
  expect(screen.getByText("Not saved")).toBeVisible();
  expect(screen.getByRole("button", {name:"Edit full text"})).toBeDisabled();
  fireEvent.click(screen.getByRole("button", {name:"Edit"}));
  expect(screen.getByRole("textbox", {name:"Subject"})).toHaveValue("Keep these words across selection");
  expect(io.api.mock.calls.some(([,init])=>init?.method === "PUT")).toBe(false);
});

it("keeps a full-text draft until it is saved before claim editing", () => {
  render(<Editor />);
  fireEvent.click(screen.getByRole("button", {name:"Edit full text"}));
  fireEvent.change(screen.getByRole("textbox", {name:"Update body"}), {target:{value:"These full-text words stay"}});
  fireEvent.click(screen.getByRole("button", {name:"Cancel"}));
  expect(screen.getByRole("button", {name:"Edit"})).toBeDisabled();
  expect(screen.getByRole("button", {name:"Publish"})).toBeDisabled();
  expect(screen.getByText("These full-text words stay")).toBeVisible();
});


it("uses the hub's state vocabulary when the item kind changes", () => {
  render(<Editor />);
  fireEvent.click(screen.getByRole("button", {name:"Edit"}));
  fireEvent.change(screen.getByRole("combobox", {name:"Kind"}), {target:{value:"dependency"}});
  expect(screen.getByRole("combobox", {name:"Kind"})).toHaveValue("dependency");
  expect(screen.getByRole("combobox", {name:"State"})).toHaveValue("healthy");
});

it("changes a review item's type and lifecycle from the same hub vocabulary, then accepts it", async () => {
  let accepted = false;
  io.api.mockImplementation(async (_url: string, init?: {method?: string}) => {
    if (init?.method === "POST") { accepted = true; return structuredClone(WIRE.item_saved); }
    return structuredClone(accepted ? WIRE.item_review_saved : WIRE.item_review);
  });
  render(<ItemReview />);
  fireEvent.click(await screen.findByRole("button", {name:"Edit and accept"}));
  fireEvent.change(screen.getByRole("combobox", {name:"Item type"}), {target:{value:"dependency"}});
  expect(screen.getByRole("combobox", {name:"Lifecycle"})).toHaveValue("healthy");
  fireEvent.click(screen.getByRole("button", {name:"Save and accept"}));
  await waitFor(() => expect(screen.queryByRole("combobox", {name:"Lifecycle"})).not.toBeInTheDocument());
  const body = io.api.mock.calls.find(([,init])=>init?.method === "POST")![1].json;
  expect(body.patch).toMatchObject({item_type:"dependency",lifecycle:"healthy"});
  expect(accepted).toBe(true);
});
