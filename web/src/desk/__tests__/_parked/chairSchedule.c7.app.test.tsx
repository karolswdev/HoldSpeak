// Parked by Betterment capture C7 (One home for recording): Capture's
// Schedule is replaced by the next two Coming-up rows; the manual form moved
// under Meetings ▸ Record ▸ Another time…. The create window itself stays
// covered by web/src/desk/components/__tests__/scheduleCreate.test.tsx.
// Not run (vitest excludes _parked).
// From: web/src/desk/__tests__/chair.app.test.tsx

/*
// ── HS-144: the capture bar's Schedule opens the create window ────────────
// The hub's own answers (tests/integration/test_face_wire_fences.py
// `test_schedule_create_reads`): the create answer and the list after it.
import { ScheduleCreateWindow } from "../components/ScheduleCreateWindow";
import { useDesk } from "../store";
import SCHEDULE_CREATED from "../../test/wire/scheduled-recordings.create.wire.json";
import SCHEDULE_LIST from "../../test/wire/scheduled-recordings.list.wire.json";

describe("The capture bar: Schedule", () => {
  it("Cancel closes the window and posts nothing; Create posts the title, closes the window and loads the saved row", async () => {
    // replaces: tests/e2e/test_hs144_door_glass.py::test_upcoming_rail_schedule_create_round_trip_and_form_cancel
    let saved = false;
    const posts: Array<[string, any]> = [];
    hub(weekStripDoor(), (path, init) => {
      if (init?.method === "POST") posts.push([path, init]);
      if (path === "/api/scheduled-recordings" && init?.method === "POST") {
        saved = true;
        return structuredClone(SCHEDULE_CREATED.wire);
      }
      if (path === "/api/scheduled-recordings") {
        return saved ? structuredClone(SCHEDULE_LIST.wire) : { success: true, schedules: [] };
      }
      return undefined;
    });
    useDesk.setState({ scheduleCreateWindow: null } as never);
    render(<><ScheduleCreateWindow /><ChairHome /></>);

    const createWindow = () => document.getElementById("schedule:__create__");
    fireEvent.click(await screen.findByTestId("arrival-schedule"));
    await waitFor(() => expect(createWindow()).not.toBeNull());
    fireEvent.click(within(createWindow()!).getByRole("button", { name: "Cancel" }));
    await waitFor(() => expect(createWindow()).toBeNull());
    expect(posts).toEqual([]);

    fireEvent.click(screen.getByTestId("arrival-schedule"));
    await waitFor(() => expect(createWindow()).not.toBeNull());
    fireEvent.change(within(createWindow()!).getByRole("textbox", { name: "Title" }), {
      target: { value: "Rail form recording" },
    });
    fireEvent.click(within(createWindow()!).getByTestId("schedule-create-submit"));
    await waitFor(() => expect(createWindow()).toBeNull());
    expect(posts.map(([p]) => p)).toEqual(["/api/scheduled-recordings"]);
    expect(posts[0][1].json.title).toBe("Rail form recording");
    await waitFor(() =>
      expect(useDesk.getState().scheduledRecordings.map((r) => r.title)).toEqual(["Rail form recording"]));
  });
});

*/
