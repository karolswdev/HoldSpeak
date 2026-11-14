import { useState } from "react";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import recorded from "./fixtures/note-held-retry-return.json";
import prepared from "./fixtures/icloud-prepared-send.json";
import channelPreviews from "./fixtures/channel-previews-20261113.recorded.json";
import {previewOf, type Destination} from "../../../../features/channels/channels";

const api = vi.fn();
vi.mock("../../../../lib/api", async () => ({
  ...(await vi.importActual<object>("../../../../lib/api")),
  apiFetch: (...args: unknown[]) => api(...args),
}));
vi.mock("../../../../pages/cores/connections/api", async () => ({
  ...(await vi.importActual<object>("../../../../pages/cores/connections/api")),
  fetchConnections: () => Promise.resolve({ tools: [] }),
}));
import { SendFace, PreviewWell, ProofCell, SendWell, SendWells, retryInline, resetSendStore } from "..";

let destinations = recorded.destinations;
let preview: unknown = recorded.old_preview;
let sends: unknown[] = [];
let posts: Record<string, unknown>[];
const doc = {
  ref: recorded.old_preview.document_ref,
  title: "Weekly report",
  label: "Note",
  version: "2",
};
beforeEach(() => {
  resetSendStore();
  localStorage.clear();
  sessionStorage.clear();
  destinations = structuredClone(recorded.destinations);
  preview = recorded.old_preview;
  sends = [];
  posts = [];
  api.mockReset();
  api.mockImplementation((path: string, init: { method?: string; json?: Record<string, unknown> } = {}) => {
    if (path.startsWith("/api/channels/destinations")) return Promise.resolve(destinations);
    if (path.startsWith("/api/channels/sends")) return Promise.resolve({ sends });
    if (path === "/api/channels/preview") return Promise.resolve(preview);
    if (path === "/api/channels/send") {
      posts.push(init.json!);
      return Promise.resolve(recorded.new_send);
    }
    return Promise.reject(new Error(`No answer for ${path}`));
  });
});

it("keeps Cancel then Send in the kit completion row, with no top action bar or private destination chips", async () => {
  render(<SendWells doc={doc} onBack={() => {}} />);
  await screen.findByTestId("send-preview");
  const send = screen.getByTestId("send-verb");
  const actions = send.closest(".surface-inspector-actions")!;
  expect(
    within(actions as HTMLElement)
      .getAllByRole("button")
      .map((b) => b.textContent),
  ).toEqual(["Edit", "Add destination", "Cancel", "Send"]);
  expect(screen.queryByTestId("send-sheet-header")).toBeNull();
  expect(document.querySelector(".send-destination-chip")).toBeNull();
  expect(screen.getByRole("combobox", { name: "Destination" })).toBeInTheDocument();
  expect(within(actions as HTMLElement).getByTestId("send-destination-word")).toHaveTextContent(
    destinations.destinations[0].name,
  );
  expect(screen.getByTestId("send-add-destination").closest(".gadget-row")).not.toBe(
    screen.getByRole("combobox", { name: "Destination" }).closest(".gadget-row"),
  );
  expect(screen.getByTestId("send-add-destination").closest("[data-verb-row]")).not.toBeNull();
  expect(screen.getByRole("region", { name: "Preview" })).toBeVisible();
  expect(screen.queryByRole("tab", { name: "Folder" })).toBeNull();
  expect(posts).toEqual([]);
});

it("requires a fresh preview when the saved destination changes under the same id", async () => {
  const view = render(<SendWells doc={doc} />);
  await screen.findByTestId("send-preview");
  let finish!: (answer: unknown) => void;
  preview = new Promise((resolve) => {
    finish = resolve;
  });
  destinations = structuredClone(destinations);
  destinations.destinations[0].target.folder += "/Changed";
  destinations.destinations[0].name = "Changed target";
  fireEvent(window, new Event("focus"));
  await waitFor(() => expect(api.mock.calls.filter(([path]) => path === "/api/channels/preview")).toHaveLength(2));
  expect(screen.getByTestId("send-verb")).toBeDisabled();
  expect(screen.getByTestId("send-destination-word")).toHaveTextContent(/^Changed target$/);
  fireEvent.click(screen.getByTestId("send-verb"));
  expect(posts).toEqual([]);
  await act(async () => finish(recorded.new_preview));
  await waitFor(() => expect(screen.getByTestId("send-verb")).toBeEnabled());
  fireEvent.click(screen.getByTestId("send-verb"));
  await waitFor(() => expect(posts[0]?.preview_digest).toBe(recorded.new_preview.payload_digest));
  view.unmount();
});

it("drops a late preview from the former document version and sends only the new digest after an owner press", async () => {
  let old!: (answer: unknown) => void;
  preview = new Promise((resolve) => {
    old = resolve;
  });
  const view = render(<SendWells doc={doc} />);
  await waitFor(() => expect(api.mock.calls.some(([path]) => path === "/api/channels/preview")).toBe(true));
  preview = recorded.new_preview;
  view.rerender(<SendWells doc={{ ...doc, version: "3" }} />);
  await screen.findByTestId("send-preview");
  await act(async () => old(recorded.old_preview));
  expect(screen.getByTestId("send-preview")).toHaveTextContent(
    recorded.new_preview.preview.text.replace(/^# /, "").trim(),
  );
  expect(posts).toEqual([]);
  fireEvent.click(screen.getByTestId("send-verb"));
  await waitFor(() => expect(posts[0]?.preview_digest).toBe(recorded.new_preview.payload_digest));
});

it("keeps tokens and keyed webhook URLs out of preview text, titles, attributes and feedback", async () => {
  const secret = "https://hooks.slack.com/services/T123/B456/private-key";
  const token = "github_pat_secretValue123456789";
  preview = {
    ...recorded.old_preview,
    preview: {
      text: `Token: ${token}\n${secret}\nhttps://example.com/hook?key=private-value`,
    },
  };
  render(<SendWells doc={{ ...doc, title: secret }} />);
  const rendered = await screen.findByTestId("send-preview");
  for (const value of [secret, token, "private-value"]) expect(document.body.innerHTML).not.toContain(value);
  expect(rendered).toHaveAttribute("data-feedback-redact", "true");
  expect(rendered).toHaveTextContent("secret hidden");
});

it("closes the discard question when the prepared send's saved content changes", async () => {
  destinations = prepared.destinations as typeof destinations;
  sends = structuredClone(prepared.before.sends);
  const preparedDoc = { ref: prepared.ref, title: "Report", label: "Update" };
  const read = {
    data: structuredClone(prepared.before.sends),
    failed: false,
    reload: () => {},
  };
  const view = render(<SendWell doc={preparedDoc} sendsRead={read as never} />);
  const discard = await screen.findByTestId("prepared-discard");
  expect(discard.closest(".surface-inspector-actions")).toContainElement(screen.getByTestId("prepared-send"));
  fireEvent.click(discard);
  expect(screen.getByTestId("inspector-question")).toBeInTheDocument();
  expect(
    within(screen.getByTestId("inspector-question")).getByRole("button", {
      name: "Cancel",
    }),
  ).toHaveFocus();
  view.rerender(
    <SendWell
      doc={preparedDoc}
      sendsRead={
        {
          ...read,
          data: [{ ...read.data[0], payload_digest: "changed-revision" }],
        } as never
      }
    />,
  );
  expect(screen.queryByTestId("inspector-question")).toBeNull();
  expect(posts).toEqual([]);
});

it("shows one discard receipt until a newer send replaces it", async () => {
  destinations = prepared.destinations as typeof destinations;
  const earlier = {
    ...prepared.after.send,
    dispatch_started_at: "2026-11-10T10:00:00Z",
    settled_at: "2026-11-10T10:00:01Z",
  };
  const discarded = {
    ...prepared.before.sends[0],
    id: "discarded-send",
    state: "discarded",
    settled_at: "2026-11-10T10:01:00Z",
  };
  const read = { data: [earlier, discarded], failed: false, reload: () => {} };
  const preparedDoc = { ref: prepared.ref, title: "Report", label: "Update" };
  const view = render(<SendWell doc={preparedDoc} sendsRead={read as never} />);
  expect(await screen.findByTestId("prepared-result")).not.toHaveTextContent("Discarded");
  expect(screen.getAllByText("Discarded", {exact:true})).toHaveLength(1);
  expect(screen.queryByTestId("send-sent")).toBeNull();
  const newer = { ...earlier, dispatch_started_at: "2026-11-10T10:02:00Z", settled_at: "2026-11-10T10:02:01Z" };
  view.rerender(<SendWell doc={preparedDoc} sendsRead={{ ...read, data: [newer, discarded] } as never} />);
  expect(await screen.findByTestId("send-sent")).toHaveTextContent("Saved");
  expect(screen.queryByTestId("prepared-result")).toBeNull();
});

it.each([false, true])(
  "keeps a Needs you retry on its original preview and command when the destination is parked: %s",
  async (parked) => {
    Object.assign(destinations.destinations[0], { builtin: false });
    const destination = destinations.destinations[0];
    api.mockRejectedValueOnce(new TypeError("answer lost"));
    await retryInline(doc.ref, destination.id, recorded.old_preview.payload_digest);
    sends = [recorded.old_send.send];
    preview = recorded.new_preview;
    if (parked) {
      destinations = structuredClone(destinations);
      Object.assign(destinations.destinations[0], { state: "parked" });
      const handler = api.getMockImplementation()!;
      api.mockImplementation((path: string, init: unknown) =>
        path.startsWith("/api/channels/destinations")
          ? Promise.resolve(path.includes("include_parked") ? destinations : { destinations: [] })
          : handler(path, init),
      );
    }
    render(<SendWells doc={{ ...doc, version: "3" }} />);
    const body = await screen.findByTestId("send-preview-body");
    expect(body).toHaveTextContent(recorded.old_preview.preview.text.replace(/^# /, "").trim());
    expect(body).not.toHaveTextContent(recorded.new_preview.preview.text.replace(/^# /, "").trim());
    const retry = screen.getByTestId("send-retry");
    await waitFor(() => expect(retry).toBeEnabled());
    fireEvent.click(retry);
    const commands = () =>
      api.mock.calls.filter(([path]) => path === "/api/channels/send").map(([, init]) => init.json);
    await waitFor(() => expect(commands()).toHaveLength(2));
    expect(commands()[1]).toEqual(commands()[0]);
  },
);

it("opens the selected stored receipt in the same window", async () => {
  sends = [recorded.old_send.send];
  render(<SendWells doc={doc} onBack={() => {}} />);
  fireEvent.click(await screen.findByRole("tab", { name: "Sent" }));
  const history = await screen.findByTestId("send-history");
  fireEvent.click(within(history).getByTestId("history-row"));
  const facts = history.querySelector(".surface-inspector-facts");
  expect(facts).not.toBeNull();
  expect(document.querySelector(".surface-inspector-object img")).not.toBeNull();
  expect(facts).toHaveTextContent("Saved");
  expect(screen.getByTestId("send-destination-word")).toHaveTextContent(recorded.old_send.send.destination_name);
  expect(within(facts as HTMLElement).getByTestId("proof")).toHaveTextContent(
    recorded.old_send.send.proof.path.split("/").at(-1)!,
  );
});

it("selects a frozen send in the Destination pop-up without adding a second list", async () => {
  destinations = prepared.destinations as typeof destinations;
  const first = prepared.before.sends[0], second = {...first,id:"second-prepared",destination_name:"Second folder"};
  const read = {data:[first,second],failed:false,reload:()=>{}};
  render(<SendWell doc={{ref:prepared.ref,title:"Report",label:"Update"}} sendsRead={read as never}/>);
  const destination = await screen.findByRole("combobox",{name:"Destination"});
  fireEvent.change(destination,{target:{value:second.id}});
  expect(screen.queryByRole("grid",{name:"Prepared sends"})).toBeNull();
  expect(screen.getByTestId("send-destination-word")).toHaveTextContent(/^Second folder$/);
  fireEvent.click(screen.getByTestId("prepared-send"));
  await waitFor(()=>expect(posts[0]?.send_id).toBe(second.id));
});


it("refuses an owner press on a masked preview and enables Send only after a clean fresh preview", async () => {
  preview = {...recorded.old_preview, preview:{text:"Token: github_pat_hiddenValue123"}};
  const view = render(<SendWells doc={doc} />);
  await screen.findByTestId("send-preview");
  const verb = screen.getByTestId("send-verb");
  expect(verb).toBeDisabled();
  fireEvent.click(verb);
  expect(posts).toHaveLength(0);
  expect(verb.closest(".surface-inspector-actions")).toHaveTextContent("This text holds a credential. Edit it before you send.");
  expect(screen.getByTestId("send-edit")).toBeEnabled();
  preview = recorded.new_preview;
  view.rerender(<SendWells doc={{...doc,version:"clean"}} />);
  await waitFor(() => expect(screen.getByTestId("send-verb")).toBeEnabled());
  expect(screen.queryByText("This text holds a credential. Edit it before you send.")).not.toBeInTheDocument();
  fireEvent.click(screen.getByTestId("send-verb"));
  await waitFor(() => expect(posts).toHaveLength(1));
  expect(posts[0].preview_digest).toBe(recorded.new_preview.payload_digest);
});

it("refuses a masked frozen send and keeps Edit available", async () => {
  destinations = prepared.destinations as typeof destinations;
  const rows = structuredClone(prepared.before.sends);
  rows[0].preview.text = "https://example.com/hook?key=hidden";
  const read = {data:rows,failed:false,reload:() => {}};
  render(<SendWell doc={{ref:prepared.ref,title:"Report",label:"Update"}} sendsRead={read as never} />);
  const verb = await screen.findByTestId("prepared-send");
  expect(verb).toBeDisabled();
  fireEvent.click(verb);
  expect(posts).toHaveLength(0);
  expect(verb.closest(".surface-inspector-actions")).toHaveTextContent("This text holds a credential.");
  expect(screen.getByTestId("send-edit")).toBeEnabled();
});

it("honors the hub credential flag for transport content absent from the readable body", async () => {
  preview = {...recorded.old_preview,preview:{text:"A readable line",credential_blocked:true}};
  render(<SendWells doc={doc} />);
  await screen.findByTestId("send-preview");
  fireEvent.click(screen.getByTestId("send-verb"));
  expect(screen.getByTestId("send-verb")).toBeDisabled();
  expect(posts).toHaveLength(0);
});

it("suppresses the second click even when the first receipt arrives between activations", async () => {
  render(<SendWells doc={doc} />);
  await screen.findByTestId("send-preview");
  fireEvent.click(screen.getByTestId("send-verb"),{detail:1});
  await waitFor(() => expect(posts).toHaveLength(1));
  await waitFor(() => expect(screen.getByTestId("send-verb")).toBeEnabled());
  fireEvent.click(screen.getByTestId("send-verb"),{detail:2});
  await act(async () => {});
  expect(posts).toHaveLength(1);
  fireEvent.click(screen.getByTestId("send-verb"),{detail:1});
  await waitFor(() => expect(posts).toHaveLength(2));
});

it("cancels held Return keydown until release after a fast receipt", async () => {
  render(<SendWells doc={doc} />);
  await screen.findByTestId("send-preview");
  let verb = screen.getByTestId("send-verb");
  expect(fireEvent.keyDown(verb,{key:"Enter",repeat:false})).toBe(true);
  fireEvent.click(verb,{detail:0});
  await waitFor(() => expect(posts).toHaveLength(1));
  await waitFor(() => expect(screen.getByTestId("send-verb")).toBeEnabled());
  verb = screen.getByTestId("send-verb");
  expect(fireEvent.keyDown(verb,{key:"Enter",repeat:true})).toBe(false);
  expect(fireEvent.keyDown(verb,{key:"Enter",repeat:false})).toBe(false);
  expect(posts).toHaveLength(1);
  fireEvent.keyUp(verb,{key:"Enter"});
  await act(async () => {});
  expect(fireEvent.keyDown(verb,{key:"Enter",repeat:false})).toBe(true);
  fireEvent.click(verb,{detail:0});
  await waitFor(() => expect(posts).toHaveLength(2));
  fireEvent.keyUp(verb,{key:"Enter"});
});


it("keeps a failed credential-edit draft visible with the retained preview and an Edit retry", async () => {
  destinations = prepared.destinations as typeof destinations;
  const rows = structuredClone(prepared.before.sends);
  rows[0].preview.text = "Token: github_pat_privateValue123";
  render(<SendWell doc={{ref:prepared.ref,title:"Report",label:"Update"}} sendsRead={{data:rows,failed:false,reload:()=>{}} as never} />);
  const edit = await screen.findByTestId("send-edit");
  fireEvent.click(edit);
  await waitFor(() => expect(screen.getByTestId("prepared-send").closest(".surface-inspector-actions")).toHaveTextContent("The preview stays here"));
  expect(screen.getByTestId("prepared-preview")).toBeInTheDocument();
  expect(edit).toBeEnabled();
  expect(screen.getByTestId("prepared-send")).toBeDisabled();
  expect(posts).toHaveLength(0);
});

it("draws Send verbs as plated Buttons and omits a lone channel strip", async () => {
  render(<SendWells doc={doc} onBack={() => {}} />);
  await screen.findByTestId("send-preview");
  expect(screen.queryByRole("tablist",{name:"Send to"})).toBeNull();
  for (const id of ["send-edit","send-add-destination","send-back"]) expect(screen.getByTestId(id)).toHaveClass("btn--secondary");
});
it("keeps the frozen preview behind its discard question", async () => {
  destinations = prepared.destinations as typeof destinations;
  render(<SendWell doc={{ref:prepared.ref,title:"Report",label:"Update"}} sendsRead={{data:prepared.before.sends,failed:false,reload:()=>{}} as never} />);
  fireEvent.click(await screen.findByTestId("prepared-discard"));
  expect(screen.getByTestId("prepared-preview")).toBeVisible();
  expect(screen.getByTestId("inspector-question")).toHaveTextContent("Discard send");
});

it("keeps a receipt's full path for hover and copy across the fitted line", async () => {
  const writeText=vi.fn().mockResolvedValue(undefined);
  Object.defineProperty(navigator,"clipboard",{configurable:true,value:{writeText}});
  const path=recorded.old_send.send.proof.path;
  render(<ProofCell channel="file" proof={{path}} />);
  expect(screen.getByTestId("proof")).toHaveAttribute("title",path);
  fireEvent.click(screen.getByRole("button",{name:"Copy path"}));
  await waitFor(()=>expect(writeText).toHaveBeenCalledWith(path));
  expect(await screen.findByText("Copied")).toBeVisible();
});


it("returns focus to the source's opening control after Cancel", async () => {
  function Host() {
    const [opened, setOpened] = useState(false);
    return <><button onClick={() => setOpened(true)}>Open Send</button>{opened ? <SendWells doc={doc} onBack={() => setOpened(false)} /> : null}</>;
  }
  render(<Host />);
  const opener = screen.getByRole("button", { name: "Open Send" });
  opener.focus(); fireEvent.click(opener);
  await screen.findByTestId("send-preview");
  const cancel = screen.getByTestId("send-back");
  cancel.focus(); fireEvent.click(cancel);
  await waitFor(() => expect(opener).toHaveFocus());
});

it("shows delivery state in the shared status seat and labels prepared facts", async () => {
  destinations = prepared.destinations as typeof destinations;
  const view = render(<SendWell doc={{ref:prepared.ref,title:"Report",label:"Update"}} sendsRead={{data:prepared.before.sends,failed:false,reload:()=>{}} as never} />);
  expect(await screen.findByTestId("send-status")).toHaveTextContent("Prepared");
  const facts = screen.getByTestId("prepared-by").closest(".surface-inspector-facts")!;
  expect(facts).toHaveTextContent("PreparedBy you");
  expect(facts).toHaveTextContent("DocumentUpdate");
  expect(screen.queryByTestId("prepared-result")).toBeNull();
  view.rerender(<SendWell doc={{ref:prepared.ref,title:"Report",label:"Update"}} sendsRead={{data:[prepared.after.send],failed:false,reload:()=>{}} as never} />);
  await waitFor(()=>expect(screen.getByTestId("send-status")).toHaveTextContent("Sent at"));
});

it("distinguishes a new send, a failed send and an unknown result", async () => {
  const read = {data:[],failed:false,reload:()=>{}};
  const view = render(<SendWell doc={doc} sendsRead={read} />);
  await screen.findByTestId("send-preview");
  expect(screen.getByTestId("send-status")).toHaveTextContent("New");
  for (const [state, word] of [["failed","Failed"],["unknown","Result unknown"]]) {
    view.rerender(<SendWell doc={doc} sendsRead={{...read,data:[{...recorded.old_send.send,state,proof:null}] } as never} />);
    expect(screen.getByTestId("send-status")).toHaveTextContent(word);
  }
});

it("formats dates in the displayed preview while keeping the frozen payload", async () => {
  preview = {...recorded.old_preview,title:"Report · 2026-11-12",preview:{...recorded.old_preview.preview,text:"# Report · 2026-11-12\n\nBody 2026-11-12"}};
  render(<SendWells doc={doc} />);
  const body = await screen.findByTestId("send-preview-body");
  expect(within(body).getByRole("heading")).toHaveTextContent("Report · Nov 12");
  expect(body).toHaveTextContent("Body Nov 12");
  expect((preview as typeof recorded.old_preview).preview.text).toContain("# Report · 2026-11-12");
});

it("does not treat a date inside a title as a time field", async () => {
  const {faceTimeWords} = await import("../../format");
  expect(faceTimeWords("Report · 2026-11-12")).toBe("Report · 2026-11-12");
  expect(faceTimeWords("2026-11-12")).toBe("Nov 12");
});


it("names the preview read while Send waits for its first payload", async () => {
  preview = new Promise(() => {});
  render(<SendWells doc={doc} />);
  expect(await screen.findByTestId("send-preview-loading")).toHaveTextContent("Preparing preview…");
  expect(screen.getByTestId("send-verb")).toBeDisabled();
});

it("names a first dispatch without offering to send it again", async () => {
  render(<SendWell doc={doc} sendsRead={{data:[{...recorded.old_send.send,state:"dispatching"}],failed:false,reload:()=>{}} as never} />);
  await screen.findByTestId("send-preview");
  expect(screen.getByTestId("send-verb")).toHaveTextContent(/^Sending…$/);
  expect(screen.getByTestId("send-verb")).toBeDisabled();
});


it("uses Refused in the status seat after a stale owner press", async () => {
  const {Refusal} = await import("../../../../features/channels/channels");
  api.mockImplementation((path: string) => {
    if (path.startsWith("/api/channels/destinations")) return Promise.resolve(destinations);
    if (path.startsWith("/api/channels/sends")) return Promise.resolve({sends:[]});
    if (path === "/api/channels/preview") return Promise.resolve(preview);
    if (path === "/api/channels/send") return Promise.reject(new Refusal("preview_changed", {}));
    return Promise.reject(new Error(path));
  });
  render(<SendWells doc={doc} />);
  await screen.findByTestId("send-preview");
  fireEvent.click(screen.getByTestId("send-verb"));
  await screen.findByTestId("send-refused");
  expect(screen.getByTestId("send-status")).toHaveTextContent("Refused");
  expect(screen.getByTestId("send-status")).not.toHaveTextContent("Failed");
});


it("keeps Retry available when the last read is dispatching but its answer was lost", async () => {
  const reply = api.getMockImplementation()!;
  api.mockImplementation((path: string, init?: {method?:string;json?:Record<string,unknown>}) =>
    path === "/api/channels/send" ? Promise.reject(new TypeError("Lost answer")) : reply(path, init));
  const read = {data:[],failed:false,reload:()=>{}};
  const view = render(<SendWell doc={doc} sendsRead={read} />);
  await screen.findByTestId("send-preview");
  fireEvent.click(screen.getByTestId("send-verb"));
  await screen.findByTestId("send-retry");
  view.rerender(<SendWell doc={doc} sendsRead={{...read,data:[{...recorded.old_send.send,state:"dispatching"}]} as never} />);
  expect(screen.getByTestId("send-retry")).toHaveTextContent(/^Retry$/);
  expect(screen.getByTestId("send-retry")).toBeEnabled();
});

it("names the newest frozen document first and keeps its time in the row", async () => {
  sends = [recorded.old_send.send, recorded.new_send.send];
  render(<SendWells doc={doc} />);
  fireEvent.click(await screen.findByRole("tab", {name:"Sent"}));
  const row = screen.getAllByTestId("history-row")[0];
  expect(row).toHaveAttribute("data-object-id", recorded.new_send.send.id);
  expect(row).toHaveTextContent(recorded.new_send.send.document_json.title);
  expect(row).toHaveTextContent(/Oct|Nov/);
  fireEvent.click(row);
  expect(document.querySelector(".surface-inspector-object img")).not.toBeNull();
});

it("formats preview date words without changing code or source paths", async () => {
  preview = {...recorded.old_preview, preview:{text:"# Report · 2026-11-12\n\n`2026-11-12` and /reports/2026-11-12.md and 2026-11-12.md"}};
  render(<SendWells doc={doc} />);
  const body = await screen.findByTestId("send-preview-body");
  expect(within(body).getByRole("heading")).toHaveTextContent("Report · Nov 12");
  expect(body.querySelector("code")).toHaveTextContent("2026-11-12");
  expect(body).toHaveTextContent("/reports/2026-11-12.md and 2026-11-12.md");
});

it.each(["Weekly report · 2026-11-12", "*Weekly report · 2026-11-12*"])("uses the same date words in the channel preview %s", body => {
  render(<PreviewWell preview={{fields:[],body_kind:"text",body}} testid="plain-preview" />);
  expect(screen.getByTestId("send-preview-body")).toHaveTextContent("Weekly report · Nov 12");
  expect(screen.getByTestId("send-preview-body")).not.toHaveTextContent("2026-11-12");
});


it("shows Slack bold through the shared reader and keeps code literal", () => {
  const body="*Weekly report · 2026-11-12*\n\n`*keep these stars*`";
  render(<PreviewWell preview={{fields:[],body_kind:"slack",body}} testid="slack-preview" />);
  const preview=screen.getByTestId("send-preview-body");
  expect(preview.querySelector("strong")).toHaveTextContent("Weekly report · Nov 12");
  expect(preview.querySelector("strong")).not.toHaveTextContent("*");
  expect(preview.querySelector("code")).toHaveTextContent("*keep these stars*");
  expect(body).toContain("2026-11-12");
});


it.each(Object.entries(channelPreviews.channels))("names %s in words at the Send act, without a host chip", (_channel, recording) => {
  const destination=recording.destination as unknown as Destination;
  render(<SendFace destination={destination} preview={previewOf(destination.channel,destination.target,destination.account,recording.reply.preview)} completion={{cancel:vi.fn(),primary:{label:"Send",testId:"send-verb",run:vi.fn()}}} />);
  const actions=screen.getByTestId("send-verb").closest<HTMLElement>(".surface-inspector-actions")!;
  expect(actions).toHaveTextContent(destination.name);
  expect(actions).toHaveTextContent(destination.channel === "email" ? "via Resend" : "on Slack");
  expect(screen.queryByText("api.resend.com")).toBeNull();
  expect(screen.queryByText("hooks.slack.com")).toBeNull();
  if (destination.channel === "slack") {
    const weekly=[...screen.getByTestId("send-preview-body").querySelectorAll("strong")].find(e=>e.textContent?.includes("Weekly report"));
    expect(weekly).toHaveTextContent("Weekly report · Nov 12");
    expect(weekly).not.toHaveTextContent("*");
  }
});
