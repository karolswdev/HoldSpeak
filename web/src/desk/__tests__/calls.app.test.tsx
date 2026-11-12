/* Calls face: real declared HTTP answers from test_calls_face_tapes.py;
 * Phone answers are the existing phone route recordings. */
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import tape from "../calls/__fixtures__/calls.face.json";
import ready from "../calls/__fixtures__/line.calls.ready.json";
import starting from "../calls/__fixtures__/line.calls.starting.json";
import { MastSlotContext } from "../surface/patterns/Mast";
import settings from "../calls/__fixtures__/line.settings.json";
import phoneStatus from "../calls/__fixtures__/phone.settings.json";
import phoneThread from "../calls/__fixtures__/phone.thread.json";
import phoneCalls from "../calls/__fixtures__/phone.calls.json";
import phoneVerbs from "../calls/__fixtures__/phone.verbs.face.json";
import pushStored from "../calls/__fixtures__/phone.push.stored.json";
import telnyxSettings from "../calls/__fixtures__/line.telnyx.settings.connected.json";
import telnyxStatus from "../calls/__fixtures__/line.telnyx.status.connected.json";
import { ApiError } from "../../lib/api";
import { CallsCore } from "../calls/CallsWindow";
import { usePhoneFocus } from "../calls/phoneFocus";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  openRef: vi.fn(),
  listeners: new Map<string, Set<(frame: { data: unknown }) => void>>(),
}));
vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  apiFetch: mocks.apiFetch,
}));
vi.mock("../openObject", () => ({ openRef: mocks.openRef }));
vi.mock("../../runtime/RuntimeBus", () => ({
  useOptionalRuntimeBus: () => ({
    subscribe: (type: string, fn: (frame: { data: unknown }) => void) => {
      const listeners = mocks.listeners.get(type) ?? new Set();
      listeners.add(fn);
      mocks.listeners.set(type, listeners);
      return () => listeners.delete(fn);
    },
  }),
}));
type Answer = unknown | ((init: { json?: unknown }) => unknown);
let requests: string[];
function hub(extra: Record<string, Answer> = {}) {
  const answers: Record<string, Answer> = {
    "GET /api/settings": { calls: settings },
    "GET /api/calls/status": ready,
    "GET /api/calls": tape.recent,
    "GET /api/calls/call-face": tape.detail,
    ...extra,
  };
  mocks.apiFetch.mockImplementation(async (path: string, init = {}) => {
    const key = `${init.method ?? "GET"} ${path}`;
    requests.push(key);
    if (!(key in answers)) throw new ApiError(404, "Not found", {});
    const answer = answers[key];
    return typeof answer === "function"
      ? answer(init)
      : structuredClone(answer);
  });
}
function row(id = "call-face") {
  return id === "phone"
    ? screen.getByTestId("calls-rail-phone")
    : screen
        .getAllByTestId("calls-row")
        .find((row) => row.getAttribute("data-call") === id)!;
}
async function waitCalls() {
  return (await screen.findAllByTestId("calls-row"))[0];
}
async function selectCall() {
  fireEvent.click(await waitCalls());
  await screen.findByTestId("calls-document");
}
function frame(call: unknown) {
  act(() => {
    for (const listener of mocks.listeners.get("call_state") ?? [])
      listener({ data: { reason: "ended", call } });
  });
}
async function chooseView(label: string) {
  fireEvent.click(screen.getByRole("button", { name: "Call view" }));
  fireEvent.click(await screen.findByRole("menuitem", { name: label }));
}
function phoneHub(extra: Record<string, Answer> = {}) {
  hub({
    "GET /api/settings": { calls: { ...settings, phone_on: true } },
    "GET /api/phone/status": phoneStatus,
    "GET /api/phone/messages?after_seq=0": phoneThread,
    "GET /api/phone/calls": phoneCalls,
    ...extra,
  });
}
async function openPhone() {
  fireEvent.click(await screen.findByTestId("calls-rail-phone"));
  await screen.findByTestId("phone-wing");
}

beforeEach(() => {
  requests = [];
  mocks.apiFetch.mockReset();
  mocks.openRef.mockReset();
  mocks.listeners.clear();
  usePhoneFocus.setState({ pending: false, replyTo: null, callId: null });
});
afterEach(cleanup);

describe("Calls selection and results", () => {
  it("uses the shared grouped selection list and has no card, inner Mast or row verbs", async () => {
    hub();
    const { container } = render(<CallsCore />);
    await waitCalls();
    expect(screen.getByRole("grid", { name: "Calls" })).toBeInTheDocument();
    expect(screen.getByText("Recent", { exact: true })).toBeInTheDocument();
    expect(
      screen.getByText("Your phone", {
        exact: true,
        selector: ".object-list-group-label",
      }),
    ).toBeInTheDocument();
    expect(
      container.querySelector(".cl-plate, .surface-mast, .surface-rail"),
    ).toBeNull();
    expect(row().querySelector("button")).toBeNull();
    expect(screen.getByTestId("calls-call-me")).not.toBeDisabled();
    expect(screen.getByTestId("calls-open-note")).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Open transcript" }),
    ).toBeDisabled();
    expect(requests).not.toContain("GET /api/calls/call-face");
    await selectCall();
    expect(screen.getByTestId("calls-open-note")).not.toBeDisabled();
    expect(screen.getAllByTestId("calls-result")[0]).toHaveTextContent(
      "Platform plan",
    );
    expect(
      screen
        .getByTestId("calls-document")
        .closest('[data-feedback-redact="true"]'),
    ).toBeTruthy();
  });
  it("opens the note, selected result and full transcript from their verbs", async () => {
    hub();
    render(<CallsCore />);
    await selectCall();
    fireEvent.click(screen.getByTestId("calls-open-note"));
    expect(mocks.openRef).toHaveBeenCalledWith(tape.detail.note_ref);
    fireEvent.click(screen.getAllByTestId("calls-result")[0]);
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    expect(mocks.openRef).toHaveBeenCalledWith("note:platform-plan");
    fireEvent.click(screen.getByRole("button", { name: "Open transcript" }));
    expect(screen.getByTestId("calls-transcript")).toHaveTextContent(
      "Review the platform plan.",
    );
    expect(screen.getByTestId("calls-transcript")).toHaveTextContent("0:05");
    expect(screen.getByTestId("calls-transcript")).toHaveAttribute(
      "data-feedback-redact",
      "true",
    );
  });
  it("Return opens the selected call transcript", async () => {
    hub();
    render(<CallsCore />);
    await selectCall();
    fireEvent.keyDown(row(), { key: "Enter" });
    expect(await screen.findByTestId("calls-transcript")).toHaveTextContent(
      "What can I do?",
    );
  });
  it("a failed detail read keeps the selection and retry fills the inspector", async () => {
    let fail = true;
    hub({
      "GET /api/calls/call-face": () => {
        if (fail) throw new Error("Read failed");
        return tape.detail;
      },
    });
    render(<CallsCore />);
    fireEvent.click(await waitCalls());
    expect(
      await screen.findByText("Read failed", { exact: false }),
    ).toBeInTheDocument();
    expect(row()).toHaveAttribute("aria-selected", "true");
    fail = false;
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByTestId("calls-document")).toHaveTextContent(
      "Review the platform plan.",
    );
  });
  it("ignores a late detail after another selection", async () => {
    let resolve!: (value: unknown) => void;
    hub({
      "GET /api/calls/call-face": () =>
        new Promise((done) => {
          resolve = done;
        }),
    });
    render(<CallsCore />);
    fireEvent.click(await waitCalls());
    await waitFor(() => expect(resolve).toBeTruthy());
    fireEvent.click(row("phone"));
    await act(async () => resolve(tape.detail));
    expect(screen.queryByTestId("calls-document")).toBeNull();
    expect(screen.getByText("No phone yet")).toBeInTheDocument();
  });
  it("a refused Call me keeps the selected result; retry shows the acknowledged call", async () => {
    let fail = true;
    hub({
      "POST /api/calls/place": () => {
        if (fail) throw new ApiError(409, "Refused", { reason: "busy" });
        return tape.placed;
      },
    });
    render(<CallsCore />);
    await selectCall();
    fireEvent.click(screen.getByTestId("calls-call-me"));
    expect(await screen.findByTestId("calls-refusal")).toHaveTextContent(
      "A call is on the line",
    );
    expect(screen.getByTestId("calls-document")).toHaveTextContent(
      "Platform plan",
    );
    fail = false;
    fireEvent.click(screen.getByTestId("calls-call-me"));
    expect(await screen.findByTestId("calls-hold")).toBeInTheDocument();
  });
});

describe("the live call", () => {
  function liveHub(extra: Record<string, Answer> = {}) {
    hub({
      "GET /api/calls/status": { ...ready, active: tape.held },
      "GET /api/calls": tape.listed,
      "GET /api/calls/call-face": tape.held,
      ...extra,
    });
  }
  it.each(["approve", "deny"] as const)(
    "%s answers the shown question and keeps the transcript",
    async (decision) => {
      let body: unknown;
      liveHub({
        "POST /api/calls/call-face/decide": (init: { json?: unknown }) => {
          body = init.json;
          return decision === "approve" ? tape.approved : tape.denied;
        },
      });
      render(<CallsCore />);
      await screen.findByTestId("calls-hold");
      expect(screen.getByTestId("calls-call-me")).toBeDisabled();
      fireEvent.click(
        screen.getByTestId(decision === "approve" ? "calls-yes" : "calls-no"),
      );
      await waitFor(() =>
        expect(screen.queryByTestId("calls-hold")).toBeNull(),
      );
      expect(body).toEqual({ decision });
      expect(screen.getByRole("log", { name: "Transcript" })).toHaveTextContent(
        "Review the platform plan.",
      );
      if (decision === "approve")
        expect(
          screen
            .getAllByTestId("calls-result")
            .some((result) => result.textContent?.includes("Sent on your yes")),
        ).toBe(true);
    },
  );
  it("a refused answer keeps the question for retry", async () => {
    liveHub({
      "POST /api/calls/call-face/decide": () => {
        throw new Error("Answer failed");
      },
    });
    render(<CallsCore />);
    fireEvent.click(await screen.findByTestId("calls-yes"));
    expect(await screen.findByTestId("calls-refusal")).toHaveTextContent(
      "Answer failed",
    );
    expect(screen.getByTestId("calls-hold")).toBeInTheDocument();
  });
  it("Hang up keeps the call results and transcript note", async () => {
    liveHub({ "POST /api/calls/call-face/hangup": tape.ended });
    render(<CallsCore />);
    await screen.findByTestId("calls-hold");
    await waitFor(() =>
      expect(screen.getByTestId("calls-hangup")).not.toBeDisabled(),
    );
    fireEvent.click(screen.getByTestId("calls-hangup"));
    await waitFor(() => expect(screen.queryByTestId("calls-hold")).toBeNull());
    await waitFor(() =>
      expect(screen.getByTestId("calls-call-me")).not.toBeDisabled(),
    );
    fireEvent.click(screen.getByTestId("calls-open-note"));
    expect(mocks.openRef).toHaveBeenCalledWith(tape.ended.note_ref);
    fireEvent.click(screen.getByRole("button", { name: "Open transcript" }));
    expect(screen.getByTestId("calls-transcript")).toHaveTextContent(
      "Review the platform plan.",
    );
  });
  it("the ended frame retains the selected call", async () => {
    liveHub();
    render(<CallsCore />);
    await screen.findByTestId("calls-hold");
    frame(tape.detail);
    expect(screen.getByTestId("calls-document")).toHaveTextContent("Done");
    expect(row()).toHaveAttribute("aria-selected", "true");
  });
});

describe("Phone and setup", () => {
  it("keeps the draft on send failure, replies to the selected line and renders the returned thread", async () => {
    const incoming = phoneThread.messages.find(
      (message) => message.direction === "from_phone",
    )!;
    let failed = true,
      body: unknown;
    phoneHub({
      "POST /api/phone/messages": (init: { json?: unknown }) => {
        body = init.json;
        if (failed) throw new Error("Phone offline");
        return incoming;
      },
      [`GET /api/phone/messages?after_seq=${phoneThread.last_seq}`]:
        phoneThread,
    });
    render(<CallsCore />);
    await openPhone();
    fireEvent.click(
      screen
        .getAllByTestId("phone-message")
        .find((row) => row.getAttribute("data-message") === incoming.id)!,
    );
    fireEvent.click(screen.getByTestId("phone-reply"));
    fireEvent.change(
      screen.getByRole("textbox", { name: "Message your phone" }),
      { target: { value: "Keep the staging window" } },
    );
    fireEvent.click(screen.getByTestId("phone-send"));
    expect(await screen.findByTestId("phone-refusal")).toHaveTextContent(
      "Your words are kept",
    );
    expect(
      screen.getByRole("textbox", { name: "Message your phone" }),
    ).toHaveValue("Keep the staging window");
    failed = false;
    fireEvent.click(screen.getByTestId("phone-send"));
    await waitFor(() =>
      expect(
        screen.getByRole("textbox", { name: "Message your phone" }),
      ).toHaveValue(""),
    );
    expect(body).toMatchObject({
      text: "Keep the staging window",
      reply_to: incoming.id,
    });
  });
  it.each(["again", "ring"] as const)(
    "Phone %s renders the returned Ringing row",
    async (verb) => {
      const wire = phoneVerbs[verb];
      let pressed = false;
      phoneHub({
        "GET /api/phone/calls": () => (pressed ? wire.after : wire.before),
        [`POST /api/phone/calls/${wire.id}/${verb}`]: () => {
          pressed = true;
          return wire.response;
        },
      });
      render(<CallsCore />);
      await openPhone();
      fireEvent.click(
        screen
          .getAllByTestId("phone-call")
          .find((row) => row.getAttribute("data-call") === wire.id)!,
      );
      fireEvent.click(
        screen.getByTestId(
          verb === "ring" ? "phone-call-ring" : "phone-call-again",
        ),
      );
      await waitFor(() =>
        expect(requests).toContain(`POST /api/phone/calls/${wire.id}/${verb}`),
      );
      await waitFor(() =>
        expect(screen.getByTestId("phone-wing")).toHaveTextContent("Ringing"),
      );
    },
  );
  it("View keeps Line and Phone setup in the same window", async () => {
    phoneHub({ "GET /api/phone/push": pushStored });
    render(<CallsCore />);
    await waitCalls();
    await chooseView("Line setup");
    expect(await screen.findByTestId("line-settings")).toBeInTheDocument();
    await chooseView("Line account");
    expect(await screen.findByTestId("line-from-calls")).toBeVisible();
    expect(screen.queryByTestId("line-egress")).toBeNull();
    await chooseView("Phone setup");
    expect(await screen.findByTestId("phone-settings")).toBeInTheDocument();
    await chooseView("Phone alerts");
    expect(await screen.findByTestId("phone-push-key-id")).toBeVisible();
    expect(screen.queryByTestId("phone-egress")).toBeNull();
  });
});

describe("phone draft custody across Views", () => {
  it("keeps unsent words when setup opens and closes", async () => {
    phoneHub();
    render(<CallsCore />);
    await openPhone();
    fireEvent.click(screen.getByTestId("phone-new-message"));
    fireEvent.change(
      screen.getByRole("textbox", { name: "Message your phone" }),
      { target: { value: "Keep my reply" } },
    );
    await chooseView("Line setup");
    await screen.findByTestId("line-settings");
    await chooseView("All calls");
    expect(
      await screen.findByRole("textbox", { name: "Message your phone" }),
    ).toHaveValue("Keep my reply");
    fireEvent.click(screen.getByRole("button", {name:"Cancel", exact:true}));
    expect(screen.queryByRole("textbox", {name:"Message your phone"})).toBeNull();
    fireEvent.click(screen.getByTestId("phone-new-message"));
    expect(screen.getByRole("textbox", {name:"Message your phone"})).toHaveValue("Keep my reply");
  });
  it("keeps the pending send and newer words when its pane returns", async () => {
    let resolve!: (value: unknown) => void;
    phoneHub({
      "POST /api/phone/messages": () =>
        new Promise((done) => {
          resolve = done;
        }),
      [`GET /api/phone/messages?after_seq=${phoneThread.last_seq}`]:
        phoneThread,
    });
    render(<CallsCore />);
    await openPhone();
    fireEvent.click(screen.getByTestId("phone-new-message"));
    fireEvent.change(
      screen.getByRole("textbox", { name: "Message your phone" }),
      { target: { value: "First message" } },
    );
    fireEvent.click(screen.getByTestId("phone-send"));
    await waitFor(() => expect(resolve).toBeTruthy());
    await chooseView("Line setup");
    await screen.findByTestId("line-settings");
    await chooseView("All calls");
    expect(screen.getByTestId("phone-send")).toBeDisabled();
    fireEvent.change(
      screen.getByRole("textbox", { name: "Message your phone" }),
      { target: { value: "Newer words" } },
    );
    await act(async () => resolve(phoneThread.messages[0]));
    await waitFor(() =>
      expect(screen.getByTestId("phone-send")).not.toBeDisabled(),
    );
    expect(
      screen.getByRole("textbox", { name: "Message your phone" }),
    ).toHaveValue("Newer words");
  });
});

it("an empty calls answer has one plain empty line and no zero count", async () => {
  hub({ "GET /api/calls": { calls: [] } });
  render(<CallsCore />);
  expect(await screen.findByText("No calls yet")).toBeInTheDocument();
  expect(screen.getByTestId("calls-status").textContent).not.toMatch(/\b0\b/);
  expect(screen.getByTestId("calls-call-me")).not.toBeDisabled();
});

it("View gives Telnyx its existing setup pane", async () => {
  hub({
    "GET /api/settings": { calls: telnyxSettings },
    "GET /api/calls/line/telnyx/status": telnyxStatus,
  });
  render(<CallsCore />);
  await waitCalls();
  await chooseView("Telnyx setup");
  const pane = await screen.findByTestId("telnyx-setup");
  await waitFor(() =>
    expect(within(pane).getByLabelText("Area code")).toBeVisible(),
  );
});

it("a phone focus request reads its call even before the list contains it", async () => {
  hub({ "GET /api/calls": { calls: [] } });
  usePhoneFocus.setState({ pending: true, callId: "call-face", replyTo: null });
  render(<CallsCore />);
  expect(await screen.findByTestId("calls-document")).toHaveTextContent(
    "Review the platform plan.",
  );
  expect(row()).toHaveAttribute("aria-selected", "true");
});

it("a failed calls read says not read and retry restores the list", async () => {
  let fail = true;
  hub({
    "GET /api/calls": () => {
      if (fail) throw new Error("The calls were not read");
      return tape.recent;
    },
  });
  render(<CallsCore />);
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "The calls were not read",
  );
  expect(screen.getByTestId("calls-status")).toHaveTextContent(
    "Calls not read",
  );
  expect(screen.getByTestId("calls-status")).not.toHaveTextContent(
    "Calls are off",
  );
  fail = false;
  fireEvent.click(screen.getByRole("button", { name: "Try again" }));
  await waitCalls();
  expect(screen.getByTestId("calls-status")).toHaveTextContent(
    "Ready for calls",
  );
});

it("the Mast uses the line's starting state", async () => {
  const publish = vi.fn();
  hub({ "GET /api/calls/status": starting });
  render(
    <MastSlotContext.Provider value={publish}>
      <CallsCore />
    </MastSlotContext.Provider>,
  );
  await waitCalls();
  await waitFor(() =>
    expect(
      publish.mock.calls.some(([value]) => value?.line === "Line starting"),
    ).toBe(true),
  );
  expect(screen.getByTestId("calls-call-me")).toBeDisabled();
});

it("Hang up remains live during an answer and a late answer cannot reopen the call", async () => {
  let finish!: (value: unknown) => void;
  hub({"GET /api/calls/status": {...ready,active:tape.held}, "GET /api/calls":tape.listed,
    "GET /api/calls/call-face":tape.held,
    "POST /api/calls/call-face/decide": () => new Promise(resolve => {finish=resolve;}),
    "POST /api/calls/call-face/hangup":tape.ended});
  render(<CallsCore />); fireEvent.click(await screen.findByTestId("calls-yes"));
  await waitFor(() => expect(finish).toBeTruthy());
  expect(screen.getByTestId("calls-hangup")).not.toBeDisabled();
  fireEvent.click(screen.getByTestId("calls-hangup"));
  await waitFor(() => expect(screen.getByTestId("calls-call-me")).not.toBeDisabled());
  await act(async () => finish(tape.approved));
  expect(screen.getByTestId("calls-call-me")).not.toBeDisabled();
  expect(screen.getByTestId("calls-document")).toHaveTextContent("Done");
  expect(screen.queryByTestId("calls-hold")).toBeNull();
});
