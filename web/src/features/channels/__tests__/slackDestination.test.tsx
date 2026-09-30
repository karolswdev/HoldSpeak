// PHILO-11-05: Slack in the Destinations form (canvas D1-D4, design section 5).
// The webhook is a SecretRow saved through the HTTP-only
// `channel.save_slack_webhook` (POST /api/channels/slack-webhooks); the hub
// mints the key_ref and the URL is never shown again. The channel name is his
// label; the name fills from it and stays editable. Check reports what is
// known without a post. The glass fence is
// tests/e2e/test_philo11_05b_meeting_faces_glass.py.
//
// The answers below have the shapes the real hub returns
// (tests/integration/test_philo11_slack_operations.py asserts them:
// `{key_ref, saved}`, account `{key_ref}`, target `{channel_label}`,
// check state `ready`, the refusal `slack_webhook_invalid`).

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";

const apiFetch = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../../pages/cores/connections/api", async () => {
  const actual = await vi.importActual<typeof import("../../../pages/cores/connections/api")>("../../../pages/cores/connections/api");
  return { ...actual, fetchConnections: () => Promise.resolve({ tools: [] }) };
});

import { autoName, Destinations } from "../../../pages/cores/connections/Destinations";

const URL = "https://hooks.slack.com/services/T000/B000/synthetic-secret";
const KEY_REF = "slack_0123456789abcdef01234567";
type Call = { method: string; path: string; json?: Record<string, unknown> };
const calls: Call[] = [];
let rows: Record<string, unknown>[] = [];
let checkState = "ready";

const slackRow = (id: string, ref = KEY_REF) => ({
  id, name: "Slack #leads", channel: "slack", account: { key_ref: ref }, target: { channel_label: "#leads" },
  synced: false, state: "active", badge: "cloud", created_at: "2026-09-30T09:00:00Z", parked_at: null, connection: null,
});

beforeEach(() => {
  calls.length = 0;
  rows = [];
  checkState = "ready";
  apiFetch.mockReset();
  apiFetch.mockImplementation((path: string, init: RequestInit & { json?: Record<string, unknown> } = {}) => {
    const method = init.method ?? "GET";
    calls.push({ method, path, json: init.json });
    if (method === "GET" && path.startsWith("/api/channels/destinations")) return Promise.resolve({ destinations: rows });
    if (method === "POST" && path === "/api/channels/slack-webhooks") {
      if (!String(init.json?.webhook_url ?? "").startsWith("https://hooks.slack.com/services/")) {
        return Promise.reject(new ApiError(400, "refused", { code: "slack_webhook_invalid", error_code: "slack_webhook_invalid" }));
      }
      return Promise.resolve({ key_ref: KEY_REF, saved: true });
    }
    if (method === "POST" && path === "/api/channels/destinations") {
      rows = [slackRow("chd_slack", String(init.json?.key_ref))];
      return Promise.resolve({ destination: rows[0] });
    }
    if (method === "POST" && path.endsWith("/check")) {
      return Promise.resolve({ destination: rows[0], check: { state: checkState, resolved: null } });
    }
    return Promise.reject(new Error(`unrouted ${method} ${path}`));
  });
});

async function slackForm() {
  render(<Destinations />);
  const form = await screen.findByTestId("dest-form");
  const channel = within(form).getByLabelText("Channel") as HTMLSelectElement;
  expect([...channel.options].map((o) => o.textContent)).toContain("Slack");
  fireEvent.change(channel, { target: { value: "slack" } });
  return screen.getByTestId("dest-form");
}

function typeWebhook(url: string) {
  const keyRow = screen.getByTestId("dest-key-row");
  fireEvent.click(within(keyRow).getByRole("button", { name: "Replace" }));
  const secret = within(keyRow).getByLabelText("Replacement Webhook");
  expect(secret).toHaveAttribute("type", "password");
  fireEvent.change(secret, { target: { value: url } });
  fireEvent.keyDown(secret, { key: "Enter" });
}

describe("Slack in the Destination form", () => {
  it("D1/D2a: saves the webhook through the held route, never shows it, and saves the row by key_ref", async () => {
    const form = await slackForm();
    expect(within(form).getByTestId("dest-key-row").textContent).toContain("Webhook");
    expect(within(form).getByTestId("dest-form-verbs").textContent).toContain("HOOKS.SLACK.COM");

    typeWebhook(URL);
    await waitFor(() => expect(within(screen.getByTestId("dest-key-row")).getByText("SET")).toBeTruthy());
    const held = calls.find((c) => c.path === "/api/channels/slack-webhooks")!;
    expect(held.method).toBe("POST");
    expect(held.json).toMatchObject({ webhook_url: URL });
    expect(document.body.textContent).not.toContain("synthetic-secret");

    fireEvent.change(screen.getByTestId("dest-slack-label"), { target: { value: "#leads" } });
    expect((screen.getByTestId("dest-name") as HTMLInputElement).value).toBe("Slack #leads");
    fireEvent.click(screen.getByTestId("dest-save"));
    await waitFor(() => expect(calls.some((c) => c.path === "/api/channels/destinations" && c.method === "POST")).toBe(true));
    const saved = calls.find((c) => c.path === "/api/channels/destinations" && c.method === "POST")!.json!;
    expect(saved).toMatchObject({ channel: "slack", name: "Slack #leads", key_ref: KEY_REF, channel_label: "#leads" });
    expect(JSON.stringify(saved)).not.toContain("hooks.slack.com/services");
    expect(document.body.textContent).not.toContain("synthetic-secret");
  });

  it("the name fills from the channel name and stays editable", async () => {
    await slackForm();
    fireEvent.change(screen.getByTestId("dest-slack-label"), { target: { value: "#leads" } });
    const name = screen.getByTestId("dest-name") as HTMLInputElement;
    expect(name.value).toBe("Slack #leads");
    fireEvent.change(name, { target: { value: "Leads room" } });
    fireEvent.change(screen.getByTestId("dest-slack-label"), { target: { value: "#leads-2" } });
    expect((screen.getByTestId("dest-name") as HTMLInputElement).value).toBe("Leads room");
    expect(autoName({ channel: "slack", folder: "", repo: "", kind: "issue", number: "", key: "", space: "", to: "", slackLabel: " #ops " }))
      .toBe("Slack #ops");
  });

  it("D2b: a webhook off hooks.slack.com is KEY NOT SAVED · WEBHOOK NOT VALID", async () => {
    await slackForm();
    typeWebhook("https://example.com/hooks/abc");
    const refused = await screen.findByTestId("dest-key-refused");
    expect(refused).toHaveAttribute("data-code", "slack_webhook_invalid");
    expect(refused.textContent).toContain("KEY NOT SAVED");
    expect(refused.textContent).toContain("WEBHOOK NOT VALID");
    expect(within(screen.getByTestId("dest-key-row")).queryByText("SET")).toBeNull();
    expect(document.body.textContent).not.toContain("example.com/hooks");
  });

  it("Save without a webhook refuses NO WEBHOOK and sends nothing", async () => {
    await slackForm();
    fireEvent.change(screen.getByTestId("dest-slack-label"), { target: { value: "#leads" } });
    fireEvent.click(screen.getByTestId("dest-save"));
    const refused = await screen.findByTestId("dest-refused");
    expect(refused).toHaveAttribute("data-code", "slack_webhook_missing");
    expect(refused.textContent).toContain("NO WEBHOOK");
    expect(calls.some((c) => c.method === "POST")).toBe(false);
  });

  it("D3: the row carries SLACK, the label and HOOKS.SLACK.COM; Check says WEBHOOK SET · HOST OK and posts nothing", async () => {
    rows = [slackRow("chd_slack")];
    render(<Destinations />);
    const row = await screen.findByTestId("dest-row");
    expect(row.textContent).toContain("SLACK");
    expect(row.textContent).toContain("#leads");
    expect(row.textContent).toContain("HOOKS.SLACK.COM");
    fireEvent.click(within(row).getByText("Slack #leads"));
    const open = await screen.findByTestId("dest-open");
    expect(open.textContent).toContain("Channel name");
    fireEvent.click(screen.getByTestId("dest-check"));
    const result = await screen.findByTestId("dest-check-result");
    expect(result.textContent).toContain("WEBHOOK SET · HOST OK");
    expect(screen.getByTestId("dest-open").textContent).toContain("SET · hooks.slack.com");
    await waitFor(() => expect(screen.getByTestId("dest-row").textContent).toContain("WEBHOOK SET"));
    // Check is the destination check route only: no send, no preview, no webhook call.
    expect(calls.filter((c) => c.method === "POST").map((c) => c.path)).toEqual(["/api/channels/destinations/chd_slack/check"]);
  });

  it("a Check that finds no webhook says NO WEBHOOK", async () => {
    rows = [slackRow("chd_slack")];
    checkState = "slack_webhook_missing";
    render(<Destinations />);
    fireEvent.click(within(await screen.findByTestId("dest-row")).getByText("Slack #leads"));
    fireEvent.click(await screen.findByTestId("dest-check"));
    const result = await screen.findByTestId("dest-check-result");
    expect(result.textContent).toContain("NO WEBHOOK");
    expect(screen.getByTestId("dest-open").textContent).toContain("NOT SET");
  });

  it("Astra counsel r1 F1: Edit on a saved row never says SET while the webhook is unknown", async () => {
    // A saved Slack row whose webhook presence this session has not confirmed (a fresh page:
    // the list read does not open the keychain). The hub's Check then finds it missing.
    rows = [slackRow("chd_slack")];
    checkState = "slack_webhook_missing";
    render(<Destinations />);
    fireEvent.click(within(await screen.findByTestId("dest-row")).getByText("Slack #leads"));
    fireEvent.click(await screen.findByTestId("dest-edit"));
    const keyRow = await screen.findByTestId("dest-key-row");
    expect(within(keyRow).queryByText("SET")).toBeNull();
    expect(screen.getByTestId("dest-form").textContent).not.toContain("WEBHOOK SET");
    // The neutral state offers Check; a Check that finds no webhook says NO WEBHOOK, still no SET.
    fireEvent.click(within(keyRow).getByTestId("dest-key-check"));
    const missing = await screen.findByTestId("dest-key-missing");
    expect(missing.textContent).toContain("NO WEBHOOK");
    expect(within(screen.getByTestId("dest-key-row")).queryByText("SET")).toBeNull();
    // Save now refuses by name and sends nothing.
    fireEvent.click(screen.getByTestId("dest-save"));
    expect((await screen.findByTestId("dest-refused")).getAttribute("data-code")).toBe("slack_webhook_missing");
    expect(calls.filter((c) => c.method === "POST" && c.path === "/api/channels/destinations")).toEqual([]);
  });

  it("Edit on a saved row says SET only after a Check confirms the webhook", async () => {
    rows = [slackRow("chd_slack")];
    render(<Destinations />);
    fireEvent.click(within(await screen.findByTestId("dest-row")).getByText("Slack #leads"));
    fireEvent.click(await screen.findByTestId("dest-edit"));
    const keyRow = await screen.findByTestId("dest-key-row");
    expect(within(keyRow).queryByText("SET")).toBeNull();
    fireEvent.click(within(keyRow).getByTestId("dest-key-check"));
    await waitFor(() => expect(within(screen.getByTestId("dest-key-row")).getByText("SET")).toBeTruthy());
    expect(screen.queryByTestId("dest-key-check")).toBeNull();
  });
});
