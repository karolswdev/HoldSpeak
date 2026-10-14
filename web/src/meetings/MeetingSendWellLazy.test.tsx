import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const chunk = vi.hoisted(() => {
  let resolve!: (module: unknown) => void;
  const promise = new Promise<unknown>((done) => { resolve = done; });
  return { promise, resolve };
});

vi.mock("./MeetingSendWell", () => chunk.promise);

import { MeetingSendWellLazy } from "./MeetingSendWellLazy";

describe("MeetingSendWellLazy", () => {
  it("holds a no-layout busy marker until the deferred well chunk arrives", async () => {
    render(<MeetingSendWellLazy meetingId="m-lazy" title="Vendor sync" />);
    expect(screen.getByTestId("meeting-send-well-reading")).toHaveAttribute("aria-busy", "true");

    chunk.resolve({
      MeetingSendWell: () => <div data-testid="deferred-meeting-send-well" />,
    });
    await waitFor(() => expect(screen.getByTestId("deferred-meeting-send-well")).toBeInTheDocument());
    expect(screen.queryByTestId("meeting-send-well-reading")).toBeNull();
  });
});
