/** HS-201-01 (counsel fix round, 2026-09-19) — inbound exposure is kept.
 *
 * Astra finding 4: the chip stopped saying that the hub binds off the
 * loopback with no token, and the Trust window never said it either, so
 * a desk reachable by every machine on the network read "This device."
 * The fact is INBOUND (who may reach this hub), not egress (where data
 * goes), so it is its own token on the chrome and its own line in the
 * Trust window, independent of the destination count.
 */
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("../../../lib/api", () => ({
  apiFetch: (...args: unknown[]) => apiFetch(...args),
}));

import { TrustWindow, useTrustWindow } from "../TrustWindow";

describe("Trust window states the inbound fact (HS-201-01)", () => {
  beforeEach(() => {
    apiFetch.mockReset();
    useTrustWindow.setState({ open: true });
  });

  it("says the hub is open to the network and that no token is set", async () => {
    apiFetch.mockResolvedValue({
      trust: {
        web_bind: "0.0.0.0",
        auth_token_set: false,
        transcript_egress: "none",
        destinations: [],
      },
    });
    render(<TrustWindow />);
    await waitFor(() =>
      expect(screen.getByText("Open to the network")).toBeTruthy(),
    );
    expect(screen.getByTestId("trust-inbound").textContent).toContain("yes");
    expect(screen.getByTestId("trust-inbound").textContent).toContain("Token: not set");
  });

  it("says no and names the token when the hub is on the loopback", async () => {
    apiFetch.mockResolvedValue({
      trust: {
        web_bind: "127.0.0.1",
        auth_token_set: true,
        transcript_egress: "none",
        destinations: [],
      },
    });
    render(<TrustWindow />);
    await waitFor(() =>
      expect(screen.getByTestId("trust-inbound").textContent).toContain("no"),
    );
    expect(screen.getByTestId("trust-inbound").textContent).toContain("Token: set");
  });
});
