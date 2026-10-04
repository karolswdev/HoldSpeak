// Review of #778: the Thread pullout printed `2026-10-04T03:06` for a
// meeting at 21:06 on Oct 3 in Denver (wrong clock and wrong day).
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MeetingResultView } from "../ThreadPullout";

const previous = process.env.TZ;
beforeAll(() => {
  process.env.TZ = "America/Denver";
});
afterAll(() => {
  if (previous === undefined) delete process.env.TZ;
  else process.env.TZ = previous;
});

describe("Thread pullout meeting rows", () => {
  it("shows the meeting's local day and clock", () => {
    render(
      <MeetingResultView
        data={{ meetings: [{ id: "m1", title: "Ledger cutover sync", started_at: "2026-10-04T03:06:00+00:00" }] }}
      />,
    );
    expect(screen.getByText("Oct 3, 21:06")).toBeInTheDocument();
    expect(document.body.textContent ?? "").not.toMatch(/2026-10-04T03:06/);
  });
});
