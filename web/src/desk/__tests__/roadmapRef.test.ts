// B0-F4 / STATUS: "The Roadmap window shows the wrong name". A Roadmap item's
// id is `roadmap:<slug>`; the palette and the Floor qualify it again
// (`roadmap:roadmap:<slug>`). The window must open on the slug itself.
import { beforeEach, describe, expect, it } from "vitest";
import { qualifiedRef } from "../api";
import { useDesk } from "../store";

beforeEach(() => {
  useDesk.setState({ roadmapWindows: [], workbenchWindows: [] });
});

describe("a twice-qualified Roadmap ref", () => {
  it("opens the Roadmap window on its slug", () => {
    useDesk.getState().openPullout(qualifiedRef("roadmap", "roadmap:holdspeak"));
    expect(useDesk.getState().roadmapWindows.map((w) => w.slug)).toEqual(["holdspeak"]);
  });

  it("opens the same window from a once-qualified ref", () => {
    useDesk.getState().openPullout("roadmap:holdspeak");
    expect(useDesk.getState().roadmapWindows.map((w) => w.slug)).toEqual(["holdspeak"]);
  });
});

describe("only the Roadmap's ref is normalised (Astra, #869 P1)", () => {
  it("opens the Workbench whose id is `workbench:weekly`, not the one named `weekly`", () => {
    // Two workbenches: `weekly` and `workbench:weekly` ("Weekly delivery").
    // The palette qualifies the second one's id: `workbench:workbench:weekly`.
    useDesk.getState().openPullout(qualifiedRef("workbench", "workbench:weekly"));
    expect(useDesk.getState().workbenchWindows.map((w) => w.id)).toEqual(["workbench:weekly"]);
    useDesk.getState().openPullout(qualifiedRef("workbench", "weekly"));
    expect(useDesk.getState().workbenchWindows.map((w) => w.id)).toEqual(["workbench:weekly", "weekly"]);
  });
});
