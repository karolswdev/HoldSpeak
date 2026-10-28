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
import checkedConnections from "./fixtures/connections-wire/connections-checked.json";
import emailKeyRefused from "./fixtures/destinations-wire/email-key-refused.json";
import emailKeySaved from "./fixtures/destinations-wire/email-key-saved.json";
import listEmail from "./fixtures/destinations-wire/list-email.json";
import listEmpty from "./fixtures/destinations-wire/list-empty.json";
import listTwo from "./fixtures/destinations-wire/list-two.json";
import saveRefusedJira from "./fixtures/destinations-wire/save-refused-jira.json";

type Answer = { status: number; body: unknown } | "no answer";
type Route = (init: RequestInit) => Answer | Promise<Answer>;
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
    const answer = key ? await routes[key](init) : { status: 404, body: { error: `not routed ${method} ${url}` } };
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
  // jsdom has no native scrollIntoView. Saving a destination schedules it
  // on the next frame, which can otherwise escape the test assertions.
  Element.prototype.scrollIntoView = vi.fn();
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
  it("keeps a parked long target and date together in the ledger facts slot", async () => {
    const destination = structuredClone(listTwo.destinations[0]);
    destination.state = "parked";
    destination.parked_at = "2026-10-14T12:00:00Z";
    destination.target.folder = "/Architecture/Research-and-platform-delivery/Quarterly-reports-and-owner-review";
    destination.target.display = destination.target.folder;
    listing({ destinations: [destination] });
    render(<Destinations />);
    const row = await screen.findByTestId("dest-parked-row");
    fireEvent.click(screen.getByText("Parked", { exact: true }));
    const cells = row.querySelector(":scope > .surface-ledger-cells");
    expect(cells).not.toBeNull();
    expect(cells).toContainElement(within(row).getByText("File", { exact: true }));
    expect(cells).toContainElement(row.querySelector(".send-target"));
    expect(cells?.textContent).toContain("Parked");
    expect(row.querySelector(".send-target")?.textContent).toContain("Quarterly-reports-and-owner-review");
    expect(within(row).queryByRole("button", { name: /Remove|Delete/ })).toBeNull();
  });

  // replaces: tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_destinations_group
  it("with no destination the add form is the group, with no counter", async () => {
    render(<Destinations />);
    await screen.findByTestId("dest-form");
    expect(groupLabel()).toBe("Destinations");
    expect(screen.queryByTestId("dest-list")).toBeNull();
  });

  it("keeps full destination rows wide under the Settings layout rules", async () => {
    render(<Destinations />);
    for (const channel of ["file", "github", "jira", "confluence", "email", "slack"]) {
      const form = await pickChannel(channel);
      const fullRows = form.querySelectorAll('.gadget-row[data-control-width="full"]');
      expect(fullRows.length).toBeGreaterThan(0);
      for (const row of fullRows) expect(row).toHaveAttribute("data-wide", "true");
    }
  });

  it("a synced folder is SYNCED FOLDER (cloud), with no same-device chip", async () => {
    render(<Destinations />);
    await screen.findByTestId("dest-form");
    fireEvent.change(screen.getByTestId("dest-folder"), { target: { value: "/Users/owner/Drive" } });
    expect(screen.getByTestId("dest-form-verbs").querySelector(".gadget-chip-egress")).toBeNull();
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
    fireEvent.change(screen.getByLabelText("To", { exact: true }), { target: { value: "lena@acme.io, tomas@acme.io" } });
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
    expect(result.textContent).toBe("✓Checked");
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
    expect(failed.textContent).toContain("Not removed");
    expect(failed.textContent).toContain("No answer");
    expect(within(failed).getByTestId("dest-remove-retry")).toBeTruthy();
    expect(screen.getByTestId("dest-open")).toBeTruthy();
    expect(groupLabel()).toBe("Destinations 2");
  });

  it("a destinations read with no answer: CANNOT READ DESTINATIONS, never the empty form", async () => {
    routes["GET /api/channels/destinations\\?include_parked=true"] = () => "no answer";
    render(<Destinations />);
    const unreadable = await screen.findByTestId("dest-unreadable");
    expect(unreadable.textContent).toContain("Cannot read destinations");
    expect(screen.queryByTestId("dest-form")).toBeNull();
  });
});

describe("the remote destination forms", () => {
  it("an account read failure keeps the draft, names the failed read and retries without blocking folders", async () => {
    routes["GET /api/connections"] = () => "no answer";
    render(<Destinations />);
    let form = await pickChannel("jira");
    fireEvent.change(screen.getByTestId("dest-key"), { target: { value: "PAY-118" } });
    expect(await within(form).findByText("Account read failed · Draft kept · Retry")).toBeTruthy();
    expect(within(form).queryByRole("button", { name: "Set up account" })).toBeNull();
    expect(within(form).queryByText("No Jira account")).toBeNull();
    expect(screen.getByTestId("dest-save")).toBeDisabled();
    routes["GET /api/connections"] = () => ok(checkedConnections);
    fireEvent.click(within(form).getByRole("button", { name: "Retry" }));
    await within(form).findByRole("combobox", { name: "Jira account" });
    expect(screen.getByTestId("dest-key")).toHaveValue("PAY-118");
    expect(screen.getByTestId("dest-save")).toBeEnabled();
    routes["GET /api/connections"] = () => "no answer";
    act(() => window.dispatchEvent(new Event("focus")));
    form = await pickChannel("file");
    fireEvent.change(screen.getByTestId("dest-folder"), { target: { value: "/Reports" } });
    expect(within(form).getByRole("button", { name: "Save" })).toBeEnabled();
  });
  it("missing accounts offer the real Accounts control and keep the destination draft", async () => {
    routes["GET /api/connections"] = () => ok({ tools: connections.tools.filter((t) => t.provider_id !== "jira") });
    const add = vi.fn();
    render(<div className="prefs-module"><div data-testid="connections-jira"><button data-testid="connections-add-open-jira" onClick={add}>Add account</button></div><Destinations /></div>);
    const form = await pickChannel("jira");
    fireEvent.change(screen.getByTestId("dest-key"), { target: { value: "PAY-118" } });
    expect(within(form).getByRole("button", { name: "Save" })).toBeDisabled();
    fireEvent.click(within(form).getByRole("button", { name: "Set up account" }));
    expect(add).toHaveBeenCalledOnce();
    expect(screen.getByTestId("dest-key")).toHaveValue("PAY-118");
  });
  // replaces: tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_the_remote_destination_forms_save
  it("Jira takes one key: two keys are REFUSED by name, nothing is listed", async () => {
    routes["GET /api/connections"] = () => ok(checkedConnections);
    routes["POST /api/channels/destinations"] = () => ({ status: 400, body: saveRefusedJira });
    render(<Destinations />);
    await pickChannel("jira");
    fireEvent.change(screen.getByTestId("dest-key"), { target: { value: "PAY-118 PAY-119" } });
    fireEvent.click(screen.getByTestId("dest-save"));
    const refused = await screen.findByTestId("dest-refused");
    expect(refused).toHaveAttribute("data-code", "jira_key_not_single");
    expect(refused.textContent).toContain("Refused");
    expect(refused.textContent).toContain("One key only");
    expect(screen.queryByTestId("dest-row")).toBeNull();
  });

  it("GitHub saves the repository and number the owner typed", async () => {
    routes["GET /api/connections"] = () => ok(checkedConnections);
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
  async function editEmail() {
    listing(listEmail);
    render(<Destinations />);
    const row = await waitFor(() => screen.getAllByTestId("dest-row").find((r) => r.textContent?.includes("Email lena@acme.io"))!);
    fireEvent.click(within(row).getByRole("button", { name: "Details" }));
    fireEvent.click(await screen.findByTestId("dest-edit"));
    return screen.getByTestId("dest-form");
  }
  // replaces: tests/e2e/test_philo10_04_send_face_glass.py::TestSendEmailGlass::test_the_email_destination_setup
  async function emailForm() {
    render(<Destinations />);
    const form = await pickChannel("email");
    fireEvent.change(within(form).getByLabelText("Provider"), { target: { value: "sendgrid" } });
    fireEvent.change(screen.getByTestId("dest-from"), { target: { value: "Karol@Acme.io" } });
    fireEvent.change(screen.getByLabelText("To", { exact: true }), { target: { value: "lena@acme.io, tomas@acme.io" } });
  }
  function typeKey(value: string) {
    const keyRow = screen.getByTestId("dest-key-row");
    fireEvent.click(within(keyRow).getByRole("button", { name: "Replace" }));
    const secret = within(keyRow).getByLabelText("Replacement SendGrid key");
    fireEvent.change(secret, { target: { value } });
    fireEvent.keyDown(secret, { key: "Enter" });
  }

  it("no safe key store: Could not save the key, the reason in the hover, and the key never shows", async () => {
    routes["PUT /api/channels/email-keys/.+"] = () => ({ status: 400, body: emailKeyRefused });
    await emailForm();
    typeKey("SG.glassKEY");
    const refused = await screen.findByTestId("dest-key-refused");
    expect(refused).toHaveAttribute("data-code", "email_key_store_not_native");
    expect(refused.textContent).toBe("Could not save the key · Nothing changed · Try again");
    expect(refused).toHaveAttribute("title", "NO SAFE KEY STORE");
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
    await waitFor(() => expect(Element.prototype.scrollIntoView).toHaveBeenCalledWith({ block: "start" }));
  });

  it("wraps recipient editors and saves comma and newline lists in their entered order", async () => {
    routes["PUT /api/channels/email-keys/.+"] = () => ok(emailKeySaved);
    routes["POST /api/channels/destinations"] = () => {
      listing(listEmail);
      return ok({ destination: listEmail.destinations[3] });
    };
    await emailForm();
    const to = screen.getByRole("textbox", { name: "To" });
    const cc = screen.getByRole("textbox", { name: "Cc" });
    expect(to.tagName).toBe("TEXTAREA");
    expect(cc.tagName).toBe("TEXTAREA");
    expect(screen.getByRole("button", { name: /^Speak To(?: ·|$)/ })).toBeTruthy();
    expect(screen.getByRole("button", { name: /^Speak Cc(?: ·|$)/ })).toBeTruthy();
    fireEvent.change(to, { target: { value: "\n lena@acme.io\ntomas@acme.io, noor@acme.io\n" } });
    fireEvent.change(cc, { target: { value: " ops@acme.io, \n team@acme.io\r\n " } });
    expect(screen.getByTestId("dest-name")).toHaveValue("Email lena@acme.io");
    typeKey("SG.glassKEY");
    await waitFor(() => expect(screen.getByTestId("dest-save")).toBeEnabled());
    fireEvent.click(screen.getByTestId("dest-save"));
    await waitFor(() => expect(screen.queryByTestId("dest-form")).toBeNull());
    expect(calls.find((c) => c.method === "POST")!.body).toMatchObject({
      channel: "email", name: "Email lena@acme.io", to: ["lena@acme.io", "tomas@acme.io", "noor@acme.io"],
      cc: ["ops@acme.io", "team@acme.io"],
    });
  });

  it("checks the saved email key locally and edits with its exact legacy ref without replacing the key", async () => {
    const saved = listEmail.destinations[3];
    routes["POST /api/channels/destinations/[^/]+/check"] = () => ok(checkEmail);
    routes["POST /api/channels/destinations"] = () => ok({ destination: saved });
    await editEmail();
    expect(screen.getByRole("textbox", { name: "To" })).toHaveValue("lena@acme.io\ntomas@acme.io");
    await waitFor(() => expect(within(screen.getByTestId("dest-key-row")).getByText("SET")).toBeTruthy());
    expect(screen.getByTestId("dest-save")).toBeEnabled();
    fireEvent.change(screen.getByLabelText("To", { exact: true }), { target: { value: "lena@acme.io\ntomas@acme.io, noor@acme.io" } });
    fireEvent.click(screen.getByTestId("dest-save"));
    await waitFor(() => expect(screen.queryByTestId("dest-form")).toBeNull());
    expect(calls.find((c) => c.url === "/api/channels/destinations" && c.method === "POST")!.body).toMatchObject({
      replaces: saved.id, key_ref: saved.account.key_ref, provider: "sendgrid",
      to: ["lena@acme.io", "tomas@acme.io", "noor@acme.io"],
    });
    expect(calls.filter((c) => c.method === "PUT")).toEqual([]);
  });

  it("checks a shared legacy key ref separately for each email provider", async () => {
    const saved = listEmail.destinations[3];
    const resend = { ...saved, id: "email-resend-same-ref", name: "Resend same key ref",
      account: { ...saved.account, provider: "resend" } };
    listing({ destinations: [saved, resend] });
    const sendgridCheck = `/api/channels/destinations/${saved.id}/check`;
    const resendCheck = `/api/channels/destinations/${resend.id}/check`;
    routes[`POST ${sendgridCheck}`] = () => ok(checkEmail);
    routes[`POST ${resendCheck}`] = () => ok({ ...checkEmail, destination: resend,
      check: { ...checkEmail.check, state: "email_key_missing" } });
    render(<Destinations />);
    const edit = async (name: string) => {
      const row = await waitFor(() => screen.getAllByTestId("dest-row").find((r) => r.textContent?.includes(name))!);
      fireEvent.click(within(row).getByRole("button", { name: "Details" }));
      fireEvent.click(await screen.findByTestId("dest-edit"));
    };
    await edit(saved.name);
    await waitFor(() => expect(screen.getByTestId("dest-save")).toBeEnabled());
    fireEvent.click(screen.getByTestId("dest-cancel"));
    await edit(resend.name);
    await waitFor(() => expect(calls.some((c) => c.url === resendCheck)).toBe(true));
    await waitFor(() => expect(screen.getByTestId("dest-email-key-check").textContent).toContain("No key"));
    expect(screen.getByTestId("dest-save")).toBeDisabled();
    expect(within(screen.getByTestId("dest-key-row")).queryByText("SET")).toBeNull();
    fireEvent.click(screen.getByTestId("dest-cancel"));
    await edit(saved.name);
    await waitFor(() => expect(screen.getByTestId("dest-save")).toBeEnabled());
    expect(calls.filter((c) => c.url === sendgridCheck)).toHaveLength(1);
    expect(calls.filter((c) => c.method === "PUT")).toEqual([]);
  });

  it.each([
    ["email_key_missing", "No key"],
    ["email_key_store_locked", "Key store locked"],
    ["email_key_store_not_native", "No safe key store"],
    ["no_answer", "No answer"],
  ])("keeps an unreadable saved email key disabled with %s and retries its local read", async (code, label) => {
    routes["POST /api/channels/destinations/[^/]+/check"] = () => code === "no_answer"
      ? "no answer" : ok({ ...checkEmail, check: { ...checkEmail.check, state: code } });
    await editEmail();
    const failed = await screen.findByTestId("dest-email-key-check");
    await waitFor(() => expect(failed.textContent).toContain(label));
    expect(screen.getByTestId("dest-save")).toBeDisabled();
    expect(within(screen.getByTestId("dest-key-row")).queryByText("SET")).toBeNull();
    routes["POST /api/channels/destinations/[^/]+/check"] = () => ok(checkEmail);
    fireEvent.click(within(failed).getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(screen.getByTestId("dest-save")).toBeEnabled());
    expect(calls.filter((c) => c.method === "PUT")).toEqual([]);
  });

  it("ignores a pending saved-key check after the sender and provider change", async () => {
    let finish!: (answer: Answer) => void;
    routes["POST /api/channels/destinations/[^/]+/check"] = () => new Promise((resolve) => { finish = resolve; });
    const form = await editEmail();
    await waitFor(() => expect(calls.some((c) => c.url.endsWith("/check"))).toBe(true));
    fireEvent.change(screen.getByTestId("dest-from"), { target: { value: "other@acme.io" } });
    fireEvent.change(within(form).getByLabelText("Provider"), { target: { value: "resend" } });
    await act(async () => { finish(ok(checkEmail)); });
    expect(within(screen.getByTestId("dest-key-row")).queryByText("SET")).toBeNull();
    expect(screen.getByTestId("dest-save")).toBeDisabled();
    const keyRow = screen.getByTestId("dest-key-row");
    routes["PUT /api/channels/email-keys/.+"] = () => ok(emailKeySaved);
    routes["POST /api/channels/destinations"] = () => ok({ destination: listEmail.destinations[3] });
    fireEvent.click(within(keyRow).getByRole("button", { name: "Replace" }));
    const replacement = within(keyRow).getByLabelText("Replacement Resend key");
    fireEvent.change(replacement, { target: { value: "re.glassKEY" } });
    fireEvent.keyDown(replacement, { key: "Enter" });
    await waitFor(() => expect(screen.getByTestId("dest-save")).toBeEnabled());
    fireEvent.click(screen.getByTestId("dest-save"));
    await waitFor(() => expect(screen.queryByTestId("dest-form")).toBeNull());
    expect(calls.find((c) => c.url === "/api/channels/destinations" && c.method === "POST")!.body).toMatchObject({
      replaces: listEmail.destinations[3].id, provider: "resend", from_email: "other@acme.io", key_ref: "resend-other@acme.io",
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
    expect(await check("ready")).toContain("Sender not checked");
    expect(screen.getByTestId("dest-open").querySelector("dl")?.textContent).toContain("SET");
    state = { state: "key_changed", answered_at: "2026-08-01T09:00:00+00:00" };
    expect(await check("key_changed")).toBe("⚠Not checked since key change");
    state = { state: "sender_accepted", answered_at: "2026-09-29T10:05:00+00:00" };
    const accepted = await check("sender_accepted");
    expect(accepted).toMatch(/^✓Sender accepted ?Last send /);
    expect(accepted).not.toContain("Verified");
    state = { state: "sender_not_verified", answered_at: "2026-09-29T10:07:00+00:00" };
    expect(await check("sender_not_verified")).toMatch(/^✗Sender not verified ?Last send /);
    await act(async () => {});
  });
});
