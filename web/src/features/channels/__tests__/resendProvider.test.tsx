// PHILO-10-07: Resend, the second email provider, on the face. The provider
// comes from the one table (EMAIL_PROVIDERS): the SENT word, the egress chip,
// the far side, the Destination form's Provider cycle, its key row and the
// key's keychain name. The glass fence for SendGrid stays
// tests/e2e/test_philo10_04_send_face_glass.py.

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../../pages/cores/connections/api", async () => {
  const actual = await vi.importActual<typeof import("../../../pages/cores/connections/api")>("../../../pages/cores/connections/api");
  return { ...actual, fetchConnections: () => Promise.resolve({ tools: [] }) };
});

import { egressOf, farSide, sentWord } from "../channels";
import { Destinations, keyRef } from "../../../pages/cores/connections/Destinations";

describe("the provider words", () => {
  it("names the provider that accepted the email", () => {
    expect(sentWord("email", { provider: "resend", message_id: "4ef9" })).toBe("ACCEPTED BY RESEND");
    expect(sentWord("email", { provider: "sendgrid", message_id: "sg-1" })).toBe("ACCEPTED BY SENDGRID");
    expect(sentWord("email", null, { provider: "resend" })).toBe("ACCEPTED BY RESEND");
    expect(sentWord("email")).toBe("ACCEPTED BY SENDGRID");
    expect(sentWord("github")).toBe("POSTED");
  });

  it("shows the provider's host as the egress and its activity page as the far side", () => {
    expect(egressOf({ channel: "email", account: { provider: "resend" } })).toEqual(
      { label: "API.RESEND.COM", scope: "cloud", title: "api.resend.com" });
    expect(egressOf({ channel: "email", account: { provider: "sendgrid" } }).label).toBe("API.SENDGRID.COM");
    expect(farSide("email", {}, { provider: "resend" })).toBe("https://resend.com/emails");
    expect(farSide("email", {}, { provider: "sendgrid" })).toBe("https://app.sendgrid.com/email_activity");
  });

  it("keeps each provider's key under its own name", () => {
    expect(keyRef("Karol@Example.com", "resend")).toBe("resend-karol@example.com");
    expect(keyRef("Karol@Example.com", "sendgrid")).toBe("sendgrid-karol@example.com");
    // PHILO-15 04 (gap 13): Resend is the default provider.
    expect(keyRef("Karol@Example.com")).toBe("resend-karol@example.com");
  });
});

describe("the Destination form", () => {
  const calls: { method: string; path: string; json?: Record<string, unknown> }[] = [];
  beforeEach(() => {
    calls.length = 0;
    apiFetch.mockReset();
    apiFetch.mockImplementation((path: string, init: RequestInit & { json?: Record<string, unknown> } = {}) => {
      const method = init.method ?? "GET";
      calls.push({ method, path, json: init.json });
      if (method === "GET" && path.startsWith("/api/channels/destinations")) return Promise.resolve({ destinations: [] });
      if (method === "PUT") return Promise.resolve({ key_ref: decodeURIComponent(path.split("/").pop() ?? ""), saved: true });
      if (method === "POST" && path === "/api/channels/destinations") {
        return Promise.resolve({ destination: { id: "chd_r", name: "x", channel: "email", account: {}, target: {},
          synced: false, state: "active", created_at: "", parked_at: null } });
      }
      return Promise.reject(new Error(`unrouted ${method} ${path}`));
    });
  });

  it("picks Resend: its key row, its key save, its egress, its save body", async () => {
    render(<Destinations />);
    const form = await screen.findByTestId("dest-form");
    fireEvent.change(within(form).getByLabelText("Channel"), { target: { value: "email" } });
    const provider = within(screen.getByTestId("dest-form")).getByLabelText("Provider") as HTMLSelectElement;
    // PHILO-15 04 (gap 13): Resend first and picked; SendGrid one change away.
    expect([...provider.options].map((o) => o.textContent)).toEqual(["Resend", "SendGrid"]);
    expect(provider.value).toBe("resend");
    fireEvent.change(provider, { target: { value: "sendgrid" } });
    expect(provider.value).toBe("sendgrid");
    expect(screen.getByTestId("dest-key-row").textContent).toContain("SendGrid key");
    fireEvent.change(provider, { target: { value: "resend" } });
    fireEvent.change(screen.getByTestId("dest-from"), { target: { value: "karol@example.com" } });
    fireEvent.change(screen.getByTestId("dest-to"), { target: { value: "priya@example.com" } });

    const keyRow = screen.getByTestId("dest-key-row");
    expect(keyRow.textContent).toContain("Resend key");
    expect(keyRow.textContent).not.toContain("SendGrid");
    expect(screen.getByTestId("dest-form-verbs").textContent).toContain("API.RESEND.COM");

    fireEvent.click(within(keyRow).getByRole("button", { name: "Replace" }));
    const secret = within(keyRow).getByLabelText("Replacement Resend key");
    fireEvent.change(secret, { target: { value: "re_synthetic_key" } });
    fireEvent.keyDown(secret, { key: "Enter" });
    await waitFor(() => expect(calls.some((c) => c.method === "PUT")).toBe(true));
    const put = calls.find((c) => c.method === "PUT")!;
    expect(put.path).toBe("/api/channels/email-keys/resend-karol%40example.com");
    expect(put.json).toMatchObject({ api_key: "re_synthetic_key", provider: "resend" });
    await waitFor(() => expect(within(screen.getByTestId("dest-key-row")).getByText("SET")).toBeTruthy());

    fireEvent.click(screen.getByTestId("dest-save"));
    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    const saved = calls.find((c) => c.method === "POST")!.json!;
    expect(saved).toMatchObject({ channel: "email", provider: "resend", from_email: "karol@example.com",
      key_ref: "resend-karol@example.com", to: ["priya@example.com"] });
  });
});
