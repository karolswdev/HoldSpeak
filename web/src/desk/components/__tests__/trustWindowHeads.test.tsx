/** HS-201-06 (counsel fix round, 2026-09-19) — the Trust window row heads.
 *
 * Constitution tenet 4 (ASD-STE100): every head is short, common, and
 * means one thing. The head over `revoke_action` says "How to stop
 * sending", not "How to stop it": the row stops the transfer out of this
 * device, never the work itself (Astra finding 5). This fence holds that
 * word and the rest of the head set.
 */
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("../../../lib/api", () => ({
  apiFetch: (...args: unknown[]) => apiFetch(...args),
}));

import { TrustWindow, useTrustWindow } from "../TrustWindow";

const DESTINATION = {
  id: "meeting_intel",
  name: "Meeting intelligence",
  operation: "Analyze meeting transcript",
  enabled: true,
  destination: "Configured runtime",
  boundary: "Configured runtime destination",
  data_class: "Transcript text",
  authority_basis: "Explicit provider and Runs on selection",
  background_ability: "Deferred jobs may retry while HoldSpeak runs",
  revoke_action:
    "Use a model on this device for summaries, or stop summaries. " +
    "Then no transcript goes out.",
  last_receipt: null,
};

describe("Trust window heads (HS-201-06)", () => {
  beforeEach(() => {
    apiFetch.mockReset();
    apiFetch.mockResolvedValue({
      trust: { transcript_egress: "configured", destinations: [DESTINATION] },
    });
    useTrustWindow.setState({ open: true });
  });

  it("names stopping the sending, and keeps the plain head set", async () => {
    render(<TrustWindow />);

    await waitFor(() =>
      expect(screen.getByText("How to stop sending")).toBeInTheDocument(),
    );
    for (const head of [
      "Where it goes",
      "Allowed by",
      "Runs without you",
      "How to stop sending",
    ]) {
      expect(screen.getByText(head)).toBeInTheDocument();
    }
    // The retired heads never come back.
    for (const dead of [
      "How to stop it",
      "Boundary",
      "Authority",
      "Background",
      "Revoke",
    ]) {
      expect(screen.queryByText(dead)).toBeNull();
    }
  });

  it("shows the plain-words stop text under that head", async () => {
    render(<TrustWindow />);

    await waitFor(() =>
      expect(screen.getByText("How to stop sending")).toBeInTheDocument(),
    );
    // The text says what stops: the transfer off this device.
    expect(
      screen.getByText(
        "Use a model on this device for summaries, or stop summaries. " +
          "Then no transcript goes out.",
      ),
    ).toBeInTheDocument();
  });
});
