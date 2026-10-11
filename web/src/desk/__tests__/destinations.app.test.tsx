/* Destinations (Settings › Connections › Destinations), the face half (the test diet, 2026-10-11).
 *
 * The real Destinations group, its form and the channels wire. Only `fetch`
 * is a double. It answers with the live hub's own answers, written by
 * tests/integration/test_desk_destinations.py (which also proves they carry
 * no invented field). The email Check states other than `ready` are the
 * live `check-email.json` answer with the hub's own other states
 * (`holdspeak/services/channel_service.py`, `_email_state`: key_changed,
 * sender_accepted, sender_not_verified, with `answered_at` the send's
 * `dispatch_started_at`).
 */
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Destinations } from "../../pages/cores/connections/Destinations";
import checkEmail from "./fixtures/destinations-wire/check-email.json";
import checkReady from "./fixtures/destinations-wire/check-ready.json";
import connections from "./fixtures/destinations-wire/connections.json";
import emailKeyRefused from "./fixtures/destinations-wire/email-key-refused.json";
import emailKeySaved from "./fixtures/destinations-wire/email-key-saved.json";
import listEmail from "./fixtures/destinations-wire/list-email.json";
import listEmpty from "./fixtures/destinations-wire/list-empty.json";
import listTwo from "./fixtures/destinations-wire/list-two.json";
import saveRefusedJira from "./fixtures/destinations-wire/save-refused-jira.json";

type Answer = { status: number; body: unknown } | "no answer";
type Route = (init: RequestInit) => Answer;
const calls: { method: string; url: string; body?: unknown }[] = [];
let routes: Record<string, Route> = {};

const ok = (body: unknown): Answer => ({ status: 200, body });

function stubFetch() {
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = String(input);
    const method = init.method ?? "GET";
    calls.push({ method, url, body: init.body ? JSON.parse(String(init.body)) : undefined });
    const key = Object.keys(routes).find((k) => {
      const [m, pattern] = k.split(" ");
      return m === method && new RegExp(`^${pattern}$`).test(url);
    });
    const answer = key ? routes[key](init) : { status: 404, body: { error: `not routed ${method} ${url}` } };
    if (answer === "no answer") throw new TypeError("Failed to fetch");
    return new Response(JSON.stringify(answer.body), {
      status: answer.status, headers: { "content-type": "application/json" },
    });
  }));
}

function listing(list: { destinations: unknown[] }) {
  routes["GET /api/channels/destinations\\?include_parked=true"] = () => ok(list);
}

beforeEach(() => {
  calls.length = 0;
  routes = { "GET /api/connections": () => ok(connections) };
  listing(listEmpty);
  stubFetch();
});
afterEach(() => vi.unstubAllGlobals());

const groupLabel = () => screen.getByTestId("destinations").querySelector(".gadget-group-label")?.textContent;
const egress = () => screen.getByTestId("dest-form-verbs").querySelector(".gadget-chip-egress") as HTMLElement;

async function pickChannel(value: string) {
  const form = await screen.findByTestId("dest-form");
  fireEvent.change(within(form).getByLabelText("Channel"), { target: { value } });
  return screen.getByTestId("dest-form");
}

describe("the Destinations group", () => {
  // replaces: tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_destinations_group
  it("with no destination the add form is the group, with no counter", async () => {
    render(<Destinations />);
    await screen.findByTestId("dest-form");
    expect(groupLabel()).toBe("Destinations");
    expect(screen.queryByTestId("dest-list")).toBeNull();
  });

  it("a synced folder is SYNCED FOLDER (cloud), never THIS DEVICE", async () => {
    render(<Destinations />);
    await screen.findByTestId("dest-form");
    fireEvent.change(screen.getByTestId("dest-folder"), { target: { value: "/Users/owner/Drive" } });
    expect(egress().textContent).toBe("THIS DEVICE");
    fireEvent.click(within(screen.getByTestId("dest-form")).getByText("SYNCED"));
    expect(egress().textContent).toBe("SYNCED FOLDER");
    expect(egress()).toHaveAttribute("data-scope", "cloud");
  });

  it("each channel's form names the destination by itself", async () => {
    render(<Destinations />);
    await pickChannel("github");
    fireEvent.change(screen.getByTestId("dest-repo"), { target: { value: "karol/Payments-Ops" } });
    fireEvent.change(screen.getByTestId("dest-number"), { target: { value: "42" } });
    expect((screen.getByTestId("dest-name") as HTMLInputElement).value).toBe("karol/Payments-Ops #42");
    await pickChannel("confluence");
    fireEvent.change(screen.getByTestId("dest-space"), { target: { value: "98304" } });
    expect((screen.getByTestId("dest-name") as HTMLInputElement).value).toBe("Confluence space 98304");
    const form = await pickChannel("email");
    fireEvent.change(within(form).getByLabelText("Provider"), { target: { value: "sendgrid" } });
    fireEvent.change(screen.getByTestId("dest-from"), { target: { value: "Karol@Acme.io" } });
    fireEvent.change(screen.getByTestId("dest-to"), { target: { value: "lena@acme.io, tomas@acme.io" } });
    expect((screen.getByTestId("dest-name") as HTMLInputElement).value).toBe("Email lena@acme.io");
    // The key row: present or absent, never the key.
    const keyRow = screen.getByTestId("dest-key-row");
    expect(keyRow.textContent).toContain("SendGrid key");
    expect(keyRow.textContent).toContain("—");
    expect(egress().textContent).toBe("API.SENDGRID.COM");
    expect(egress()).toHaveAttribute("data-scope", "cloud");
  });

  it("two saved folders: Destinations 2; a Check reads CHECKED and the Checked time", async () => {
    listing(listTwo);
    routes["POST /api/channels/destinations/[^/]+/check"] = () => ok(checkReady);
    render(<Destinations />);
    await waitFor(() => expect(screen.getAllByTestId("dest-row")).toHaveLength(2));
    expect(groupLabel()).toBe("Destinations 2");
    const reports = screen.getAllByTestId("dest-row").find((r) => r.textContent?.includes("Folder Reports"))!;
    fireEvent.click(within(reports).getByText("Folder Reports"));
    fireEvent.click(await screen.findByTestId("dest-check"));
    const result = await screen.findByTestId("dest-check-result");
    expect(result).toHaveAttribute("data-code", "ready");
    expect(result.textContent).toBe("✓CHECKED");
    expect(screen.getByTestId("dest-open").querySelector("dl")?.textContent).toContain("Checked");
  });

  it("a Remove with no answer stays open, NOT REMOVED · NO ANSWER, with Retry; the count stays", async () => {
    listing(listTwo);
    routes["DELETE /api/channels/destinations/[^/]+"] = () => "no answer";
    render(<Destinations />);
    await waitFor(() => expect(screen.getAllByTestId("dest-row")).toHaveLength(2));
    const drive = screen.getAllByTestId("dest-row").find((r) => r.textContent?.includes("Folder Drive"))!;
    fireEvent.click(within(drive).getByText("Folder Drive"));
    const remove = await screen.findByTestId("dest-remove");
    fireEvent.click(remove);
    expect(remove.textContent?.trim()).toBe("Remove?");
    fireEvent.click(remove);
    const failed = await screen.findByTestId("dest-remove-failed");
    expect(failed.textContent).toContain("NOT REMOVED");
    expect(failed.textContent).toContain("NO ANSWER");
    expect(within(failed).getByTestId("dest-remove-retry")).toBeTruthy();
    expect(screen.getByTestId("dest-open")).toBeTruthy();
    expect(groupLabel()).toBe("Destinations 2");
  });

  it("a destinations read with no answer: CANNOT READ DESTINATIONS, never the empty form", async () => {
    routes["GET /api/channels/destinations\\?include_parked=true"] = () => "no answer";
    render(<Destinations />);
    const unreadable = await screen.findByTestId("dest-unreadable");
    expect(unreadable.textContent).toContain("CANNOT READ DESTINATIONS");
    expect(screen.queryByTestId("dest-form")).toBeNull();
  });
});

describe("the remote destination forms", () => {
  // replaces: tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_the_remote_destination_forms_save
  it("Jira takes one key: two keys are REFUSED by name, nothing is listed", async () => {
    routes["POST /api/channels/destinations"] = () => ({ status: 400, body: saveRefusedJira });
    render(<Destinations />);
    await pickChannel("jira");
    fireEvent.change(screen.getByTestId("dest-key"), { target: { value: "PAY-118 PAY-119" } });
    fireEvent.click(screen.getByTestId("dest-save"));
    const refused = await screen.findByTestId("dest-refused");
    expect(refused).toHaveAttribute("data-code", "jira_key_not_single");
    expect(refused.textContent).toContain("REFUSED");
    expect(refused.textContent).toContain("ONE KEY ONLY");
    expect(screen.queryByTestId("dest-row")).toBeNull();
  });

  it("GitHub saves the repository and number the owner typed", async () => {
    routes["POST /api/channels/destinations"] = () => ok({ destination: listTwo.destinations[1] });
    render(<Destinations />);
    await pickChannel("github");
    fireEvent.change(screen.getByTestId("dest-repo"), { target: { value: "acme/Payments" } });
    fireEvent.change(screen.getByTestId("dest-number"), { target: { value: "42" } });
    fireEvent.click(screen.getByTestId("dest-save"));
    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    expect(calls.find((c) => c.method === "POST")!.body).toMatchObject({
      channel: "github", name: "acme/Payments #42", host: "github.com", repo: "acme/Payments", kind: "issue", number: 42,
    });
  });
});

describe("the email destination setup", () => {
  // replaces: tests/e2e/test_philo10_04_send_face_glass.py::TestSendEmailGlass::test_the_email_destination_setup
  async function emailForm() {
    render(<Destinations />);
    const form = await pickChannel("email");
    fireEvent.change(within(form).getByLabelText("Provider"), { target: { value: "sendgrid" } });
    fireEvent.change(screen.getByTestId("dest-from"), { target: { value: "Karol@Acme.io" } });
    fireEvent.change(screen.getByTestId("dest-to"), { target: { value: "lena@acme.io, tomas@acme.io" } });
  }
  function typeKey(value: string) {
    const keyRow = screen.getByTestId("dest-key-row");
    fireEvent.click(within(keyRow).getByRole("button", { name: "Replace" }));
    const secret = within(keyRow).getByLabelText("Replacement SendGrid key");
    fireEvent.change(secret, { target: { value } });
    fireEvent.keyDown(secret, { key: "Enter" });
  }

  it("no safe key store: KEY NOT SAVED · NO SAFE KEY STORE, and the key never shows", async () => {
    routes["PUT /api/channels/email-keys/.+"] = () => ({ status: 400, body: emailKeyRefused });
    await emailForm();
    typeKey("SG.glassKEY");
    const refused = await screen.findByTestId("dest-key-refused");
    expect(refused).toHaveAttribute("data-code", "email_key_store_not_native");
    expect(refused.textContent).toContain("KEY NOT SAVED");
    expect(refused.textContent).toContain("NO SAFE KEY STORE");
    expect(document.body.innerHTML).not.toContain("glassKEY");
  });

  it("a saved key reads SET, never the key; the save names the key by its ref", async () => {
    routes["PUT /api/channels/email-keys/.+"] = () => ok(emailKeySaved);
    routes["POST /api/channels/destinations"] = () => {
      listing(listEmail);
      return ok({ destination: listEmail.destinations[3] });
    };
    await emailForm();
    typeKey("SG.glassKEY");
    await waitFor(() => expect(within(screen.getByTestId("dest-key-row")).getByText("SET")).toBeTruthy());
    expect(document.body.innerHTML).not.toContain("glassKEY");
    const put = calls.find((c) => c.method === "PUT")!;
    expect(put.url).toBe("/api/channels/email-keys/sendgrid-karol%40acme.io");
    fireEvent.click(screen.getByTestId("dest-save"));
    await waitFor(() => expect(screen.getAllByTestId("dest-row").some((r) => r.textContent?.includes("Email lena@acme.io"))).toBe(true));
    expect(calls.find((c) => c.method === "POST")!.body).toMatchObject({
      channel: "email", provider: "sendgrid", key_ref: "sendgrid-karol@acme.io", to: ["lena@acme.io", "tomas@acme.io"],
    });
  });

  it("Check reports the SENDER from the provider's last answer, never a fresh verification", async () => {
    listing(listEmail);
    let state: { state: string; answered_at: string | null } = { state: "ready", answered_at: null };
    routes["POST /api/channels/destinations/[^/]+/check"] = () => ok({ ...checkEmail, check: { ...checkEmail.check, ...state } });
    render(<Destinations />);
    const row = await waitFor(() => screen.getAllByTestId("dest-row").find((r) => r.textContent?.includes("Email lena@acme.io"))!);
    fireEvent.click(within(row).getByText("Email lena@acme.io"));
    const check = async (expected: string) => {
      fireEvent.click(await screen.findByTestId("dest-check"));
      await waitFor(() => expect(screen.getByTestId("dest-check-result")).toHaveAttribute("data-code", expected));
      return screen.getByTestId("dest-check-result").textContent?.replace(/\s+/g, " ").trim() ?? "";
    };
    expect(await check("ready")).toContain("SENDER NOT CHECKED");
    expect(screen.getByTestId("dest-open").querySelector("dl")?.textContent).toContain("SET");
    state = { state: "key_changed", answered_at: "2026-08-01T09:00:00+00:00" };
    expect(await check("key_changed")).toBe("⚠NOT CHECKED SINCE KEY CHANGE");
    state = { state: "sender_accepted", answered_at: "2026-09-29T10:05:00+00:00" };
    const accepted = await check("sender_accepted");
    expect(accepted).toMatch(/^✓SENDER ACCEPTED ?LAST SEND /);
    expect(accepted).not.toContain("VERIFIED");
    state = { state: "sender_not_verified", answered_at: "2026-09-29T10:07:00+00:00" };
    expect(await check("sender_not_verified")).toMatch(/^✗SENDER NOT VERIFIED ?LAST SEND /);
    await act(async () => {});
  });
});
