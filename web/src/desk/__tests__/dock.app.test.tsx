// The Dock app (test diet, 2026-10-11): the outage, moved off the browser.
//
// replaces: tests/e2e/test_philo13_13_dock_glass.py::TestLiveDock::test_the_dock_shows_his_day_live_and_stays_through_an_outage (the outage receipt leg)
//
// The hub stops and his "Refresh from hub" runs: the real store's refresh
// reads every collection, the fetch fails as a stopped hub fails (a
// TypeError: no answer came), and the real screen bar names the failed read
// with Retry and OK. Only `fetch` is stubbed.
//
// The other legs of that walk have their successors beside the Dock:
//  - READY 1, cleared by the read frame: components/window/Dock.test.tsx:237-282
//  - SENT hh:mm in the ok tone: Dock.test.tsx:296-306
//  - REC only on the hub's confirmation, REC hh:mm in the rec tone; OFFLINE ·
//    AS OF with no tag and no count: Dock.test.tsx:331-379
//  - the Desk is never replaced by the error face: web/src/desk/DeskApp.test.tsx:213-224
//  - opening the meeting POSTs /ready/read: web/src/pages/cores/__tests__/meetingRefresh202.test.tsx:305-312
//  - the producers: tests/unit/test_philo13_c3_ready.py:131-171 (aftercare_ready
//    on the bus), tests/unit/test_philo13_c3_dock.py (a settled send's
//    durable row and its frame)
import { act, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useDesk } from "../store";
import { clearWriteFailure } from "../hooks/useWriteReceipt";
import { DeskChrome } from "../components/DeskChrome";

vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "offline", lastFrame: null, subscribe: () => () => undefined }),
  useOptionalRuntimeBus: () => ({ state: "offline", subscribe: () => () => undefined }),
}));

describe("Dock app: the hub goes away", () => {
  beforeEach(() => {
    localStorage.clear();
    clearWriteFailure();
    // A stopped hub: no request gets an answer.
    vi.stubGlobal("fetch", vi.fn(async () => {
      throw new TypeError("Failed to fetch");
    }));
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    clearWriteFailure();
  });

  it("Refresh from hub names READ MEETINGS FAILED · HUB UNREACHABLE on the screen bar, with Retry and OK", async () => {
    render(<MemoryRouter><DeskChrome /></MemoryRouter>);
    await act(async () => {
      await useDesk.getState().refresh();
    });
    const receipt = await waitFor(() => {
      const node = document.querySelector(".desk-menubar .desk-chrome-receipt .write-receipt");
      expect(node, "the receipt sits in the screen bar").toBeTruthy();
      return node as HTMLElement;
    });
    expect(receipt.querySelector(".write-receipt-label")?.textContent).toBe("READ MEETINGS FAILED · HUB UNREACHABLE");
    expect(within(receipt).getByRole("button", { name: "Retry" })).toBeTruthy();
    expect(within(receipt).getByRole("button", { name: "OK" })).toBeTruthy();
    expect(screen.queryByLabelText("Preparing HoldSpeak")).toBeNull();
  });
});
