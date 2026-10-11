// The Trust app (test diet, 2026-10-11): a cloud summary route is named on
// the face, moved off the browser.
//
// replaces: tests/e2e/test_hs201_summary_trust_glass.py::test_summary_cloud_route_is_visible_in_trust_glass (the face half)
// The hub half (the selection, the planned route, the trust read, nothing
// executed) is tests/unit/test_desk_trust.py.
//
// TRUST is the hub's own answer: `/api/setup/status` `trust`, recorded from
// the hub in tests/unit/test_desk_trust.py's seed (a cloud summary
// assignment, live analysis off, actuators off). Two of its eight destination
// rows are kept (the enabled summary row and the saved folder); the other six
// are disabled rows of the same shape. Only `fetch` is stubbed; the real
// screen bar, egress badge and Trust window render it.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useDesk } from "../store";
import { DeskChrome } from "../components/DeskChrome";
import { TrustWindow, useTrustWindow } from "../components/TrustWindow";

vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useOptionalRuntimeBus: () => ({ state: "connected", subscribe: () => () => undefined }),
}));

const TRUST = {
  web_bind: "127.0.0.1",
  auth_token_set: false,
  transcript_egress: "configured",
  egress_detail: "Live analysis is off for Record. Dictation and manual summary can use a remote route.",
  configured_endpoints: ["api.openai.com"],
  actuators_enabled: false,
  webhook_allowed_hosts: ["*"],
  destinations: [
    {
      id: "meeting_intel", background_ability: "Only runs for an explicit summary request",
      revoke_action: "Change the summary assignment", authority_basis: "Assigned summary route",
      data_class: "Meeting transcript", boundary: "cloud", name: "Meeting summary",
      operation: "Generate meeting summary", enabled: true, destination: "api.openai.com", last_receipt: null,
    },
    {
      id: "channel:holdspeak-folder", name: "HoldSpeak folder", operation: "Send a document",
      boundary: "This device", data_class: "The document you send", authority_basis: "You press Send",
      background_ability: "No. Each send needs your press", revoke_action: "Nothing leaves this device",
      enabled: false, saved: true, destination: "~/Documents/HoldSpeak/Sent", last_receipt: null,
    },
  ],
  last_egress: null,
  summary: "1 external destination enabled.",
};

describe("Trust app: a cloud summary route", () => {
  beforeEach(() => {
    localStorage.clear();
    useTrustWindow.setState({ open: false });
    useDesk.setState({ setup: { trust: TRUST } as never, error: "" });
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const body = String(input).includes("/api/setup/status") ? { trust: TRUST } : {};
      return new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } });
    }));
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("the badge names api.openai.com; Trust opens from it and names the host and the external scope", async () => {
    render(<MemoryRouter><DeskChrome /><TrustWindow /></MemoryRouter>);
    const badge = screen.getByRole("button", { name: /Privacy and trust/ });
    expect(badge.getAttribute("aria-label")).toContain("api.openai.com");
    expect(badge.textContent?.toLowerCase()).toContain("api.openai.com");

    fireEvent.click(badge);
    const win = await waitFor(() => {
      const node = document.querySelector(".desk-trust-window");
      expect(node).toBeTruthy();
      return node as HTMLElement;
    });
    await waitFor(() => expect(within(win).getByText("api.openai.com")).toBeTruthy());
    expect(within(win).getByText("this device + external")).toBeTruthy();
    expect(within(win).getByText("Only runs for an explicit summary request")).toBeTruthy();
  });
});
