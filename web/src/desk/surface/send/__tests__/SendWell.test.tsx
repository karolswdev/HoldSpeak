// PHILO-11-04: the SEND well species on a NON-update document (the brief),
// one case per state, against the wire client (apiFetch mocked by URL). The
// update's own cases stay in features/channels/__tests__/SendWell.test.tsx;
// its glass fence through the real hub is tests/e2e/test_philo10_04_send_face_glass.py.

import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Destination, Send } from "../../../../features/channels/channels";

const apiFetch = vi.fn();
vi.mock("../../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../../lib/api")>("../../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../../../pages/cores/connections/api", async () => {
  const actual = await vi.importActual<typeof import("../../../../pages/cores/connections/api")>("../../../../pages/cores/connections/api");
  return { ...actual, fetchConnections: () => Promise.resolve({ tools: [] }) };
});

import { ApiError } from "../../../../lib/api";
import { PreparedChip, SendWells, resetSendStore, type DocRef } from "..";

const REF = "monday_brief:b1";
const BRIEF: DocRef = { ref: REF, title: "Brief Sep 29", label: "BRIEF SEP 29" };
const FOLDER = "/Users/karol/Reports/Team";
const folder = (over: Partial<Destination> = {}): Destination => ({
  id: "chd_f", name: "Team folder", channel: "file", account: {}, target: { folder: FOLDER },
  synced: false, state: "active", created_at: "2026-09-29T10:00:00Z", parked_at: null, ...over,
});
const slack = (over: Partial<Destination> = {}): Destination => ({
  id: "chd_s", name: "Slack #leads", channel: "slack", account: { key_ref: "leads", key_present: true },
  target: { channel_label: "#leads" }, synced: false, state: "active", created_at: "2026-09-29T10:00:00Z", parked_at: null, ...over,
});
const send = (over: Partial<Send> = {}): Send => ({
  id: "chs_1", document_ref: REF, destination_id: "chd_f", destination_name: "Team folder",
  channel: "file", account: {}, target: { folder: FOLDER }, payload_digest: "d", preview: { text: "# Brief" },
  prepared_by: { kind: "owner", identity: "" }, prepare_operation_id: null, state: "sent", reason: null,
  proof: { path: `${FOLDER}/2026-09-29-brief.md` }, file_path: `${FOLDER}/2026-09-29-brief.md`,
  created_at: "2026-09-29T10:00:00Z", dispatch_started_at: "2026-09-29T10:00:00Z", settled_at: "2026-09-29T10:00:01Z",
  ...over,
});

type Route = (init: RequestInit & { json?: Record<string, unknown> }, path: string) => unknown;
let routes: Record<string, Route>;
let previews: string[];
beforeEach(() => {
  resetSendStore();
  apiFetch.mockReset();
  previews = [];
  routes = {
    "GET /api/channels/destinations": () => ({ destinations: [folder()] }),
    "GET /api/channels/sends": () => ({ sends: [] }),
    "POST /api/channels/preview": (init) => {
      previews.push(String(init.json?.document_ref));
      return { payload_digest: "dig1", preview: { text: "# Brief\n\n## People\n\nPriya Nair: they owe 1" } };
    },
  };
  apiFetch.mockImplementation((path: string, init: RequestInit & { json?: Record<string, unknown> } = {}) => {
    const r = routes[`${init.method ?? "GET"} ${path.split("?")[0]}`];
    if (!r) return Promise.reject(new Error(`unrouted ${path}`));
    try { return Promise.resolve(r(init, path)); } catch (e) { return Promise.reject(e); }
  });
});
afterEach(() => vi.useRealTimers());

const pick = async (name: string) => {
  const row = (await screen.findAllByTestId("destination-row")).find((r) => r.textContent?.includes(name))!;
  fireEvent.click(within(row).getByText(name));
  return row;
};
const noManualRow = () => {
  expect(screen.queryByTestId("deliver-verb")).toBeNull();
  expect(screen.queryByTestId("deliver-to")).toBeNull();
  expect(document.body.textContent).not.toContain("Mark delivered");
  expect(document.body.textContent).not.toContain("DELIVERY");
};

describe("the SEND well species on a brief (not an update)", () => {
  it("no destination: NO DESTINATION + Add destination; no history head, no counter of zero", async () => {
    routes["GET /api/channels/destinations"] = () => ({ destinations: [] });
    render(<SendWells doc={BRIEF} />);
    const none = await screen.findByTestId("send-none");
    expect(none.textContent).toContain("NO DESTINATION");
    expect(within(none).getByTestId("send-add-destination").textContent).toBe("Add destination");
    expect(screen.getByTestId("send-well").getAttribute("data-doc")).toBe(REF);
    expect(screen.queryByTestId("send-history")).toBeNull();
    noManualRow();
  });

  it("picked: the preview of THIS document opens with Send; the row keeps the one grammar", async () => {
    render(<SendWells doc={BRIEF} />);
    const row = await pick("Team folder");
    expect(row.querySelector(".send-cells")?.textContent).toContain("THIS DEVICE");
    const preview = await screen.findByTestId("send-preview");
    expect(preview.textContent).toContain("Priya Nair: they owe 1");
    expect(previews).toEqual([REF]);
    const verb = screen.getByTestId("send-verb");
    await waitFor(() => expect((verb as HTMLButtonElement).disabled).toBe(false));
    expect(verb.textContent).toBe("Send");
    noManualRow();
  });

  it("SENT: SAVED + the exact path; SENDS 1 from the ended sends; the wire carries document_ref", async () => {
    let stored: Send[] = [];
    routes["GET /api/channels/sends"] = () => ({ sends: stored });
    routes["POST /api/channels/send"] = (init) => {
      expect(init.json).toMatchObject({ document_ref: REF, destination_id: "chd_f", preview_digest: "dig1" });
      expect(init.json).not.toHaveProperty("update_id");
      stored = [send()];
      return { send: stored[0] };
    };
    render(<SendWells doc={BRIEF} />);
    await pick("Team folder");
    const verb = await screen.findByTestId("send-verb");
    await waitFor(() => expect((verb as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(verb);
    const sent = await screen.findByTestId("send-sent");
    expect(sent.textContent).toContain("SAVED");
    expect(within(sent).getByTestId("proof").textContent).toBe(`${FOLDER}/2026-09-29-brief.md`);
    const history = await screen.findByTestId("send-history");
    expect(history.querySelector("h3")?.textContent).toBe("SENDS 1");
    expect(within(history).getByTestId("history-word").textContent).toBe("SAVED");
    noManualRow();
  });

  it("POSTED: a Slack send shows POSTED and the channel, never a link", async () => {
    routes["GET /api/channels/destinations"] = () => ({ destinations: [slack()] });
    routes["GET /api/channels/sends"] = () => ({ sends: [send({
      destination_id: "chd_s", destination_name: "Slack #leads", channel: "slack", account: { key_ref: "leads" },
      target: { channel_label: "#leads" }, proof: { ok: true }, file_path: null,
    })] });
    render(<SendWells doc={BRIEF} />);
    const row = await pick("Slack #leads");
    expect(row.textContent).toContain("HOOKS.SLACK.COM");
    expect(row.textContent).toContain("WEBHOOK SET");
    const sent = await screen.findByTestId("send-sent");
    expect(sent.textContent).toContain("POSTED");
    const proof = within(sent).getByTestId("proof");
    expect(proof.textContent).toBe("#leads");
    expect(proof.tagName).not.toBe("BUTTON");
    expect(proof.getAttribute("data-href")).toBeNull();
    const history = screen.getByTestId("send-history");
    expect(history.querySelector("h3")?.textContent).toBe("SENDS 1");
    expect(history.querySelector("[data-href]")).toBeNull();
    expect(screen.getByTestId("send-verb").textContent).toBe("Send again");
  });

  it("REFUSED on Send: the refusal word and NOTHING SENT", async () => {
    routes["POST /api/channels/send"] = () => {
      throw new ApiError(409, "changed", { success: false, error_code: "destination_changed" });
    };
    render(<SendWells doc={BRIEF} />);
    await pick("Team folder");
    const verb = await screen.findByTestId("send-verb");
    await waitFor(() => expect((verb as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(verb);
    const refused = await screen.findByTestId("send-refused");
    expect(refused.textContent).toContain("REFUSED");
    expect(refused.textContent).toContain("DESTINATION CHANGED");
    expect(refused.textContent).toContain("NOTHING SENT");
  });

  it("REFUSED preview over the Slack limit (G2, canvas T1): the named word and the size, never NO ANSWER, no Send", async () => {
    routes["GET /api/channels/destinations"] = () => ({ destinations: [slack()] });
    routes["POST /api/channels/preview"] = () => {
      throw new ApiError(400, "too large", {
        success: false, code: "payload_too_large:slack", error_code: "payload_too_large:slack", size: 41099, limit: 39000,
      });
    };
    render(<SendWells doc={BRIEF} />);
    await pick("Slack #leads");
    const refused = await screen.findByTestId("preview-refused");
    expect(refused.getAttribute("data-code")).toBe("payload_too_large:slack");
    expect(refused.textContent).toContain("REFUSED");
    expect(refused.textContent).toContain("TOO LARGE FOR SLACK");
    expect(within(refused).getByTestId("preview-size").textContent).toBe("41,099 / 39,000 CHARACTERS");
    expect(refused.textContent).toContain("NOTHING SENT");
    expect(refused.textContent).toContain("HOOKS.SLACK.COM");
    expect(screen.getByTestId("send-open").textContent).not.toContain("NO ANSWER");
    expect(screen.queryByTestId("send-verb")).toBeNull();
    expect(screen.queryByTestId("preview-failed")).toBeNull();
  });

  it("a preview refusal with no top-level size names its word only (no invented number; no nested form)", async () => {
    routes["POST /api/channels/preview"] = () => {
      throw new ApiError(404, "gone", { success: false, error_code: "document_not_found", context: { size: 41099, limit: 39000 } });
    };
    render(<SendWells doc={BRIEF} />);
    await pick("Team folder");
    const refused = await screen.findByTestId("preview-refused");
    expect(refused.textContent).toContain("DOCUMENT NOT FOUND");
    expect(screen.queryByTestId("preview-size")).toBeNull();
  });

  it("a preview with no answer at all stays NO PREVIEW · NO ANSWER with Retry", async () => {
    routes["POST /api/channels/preview"] = () => { throw new TypeError("Failed to fetch"); };
    render(<SendWells doc={BRIEF} />);
    await pick("Team folder");
    const failed = await screen.findByTestId("preview-failed");
    expect(failed.textContent).toContain("NO ANSWER");
    expect(within(failed).getByTestId("preview-retry").textContent).toBe("Retry");
  });

  it("FAILED: the latest send's failure word and NOTHING SENT; no SENDS head for a failure", async () => {
    routes["GET /api/channels/sends"] = () => ({ sends: [send({ state: "failed", reason: "permission_denied", proof: null })] });
    render(<SendWells doc={BRIEF} />);
    await pick("Team folder");
    const failed = await screen.findByTestId("send-failed");
    expect(failed.textContent).toContain("FAILED");
    expect(failed.textContent).toContain("NO PERMISSION");
    expect(failed.textContent).toContain("NOTHING SENT");
    expect(screen.getByTestId("send-last-failed").textContent).toContain("LAST SEND FAILED");
    expect(screen.queryByTestId("send-history")).toBeNull();
  });

  it("UNKNOWN: RESULT UNKNOWN on the row and in the history (SENDS, no counter of zero)", async () => {
    routes["GET /api/channels/sends"] = () => ({ sends: [send({ state: "unknown", reason: "no_answer", proof: null })] });
    render(<SendWells doc={BRIEF} />);
    await pick("Team folder");
    const unknown = await screen.findByTestId("send-unknown");
    expect(unknown.textContent).toContain("RESULT UNKNOWN");
    expect(unknown.textContent).toContain("NO ANSWER");
    const history = screen.getByTestId("send-history");
    expect(history.querySelector("h3")?.textContent).toBe("SENDS");
    expect(within(history).getByTestId("history-row").textContent).toContain("RESULT UNKNOWN · CHECK Team folder");
  });

  it("PREPARED, refused PREVIEW CHANGED: the row shows the word, Send goes, Discard stays", async () => {
    routes["GET /api/channels/sends"] = () => ({ sends: [send({
      id: "chs_old", state: "prepared", prepare_operation_id: "op_p", prepared_by: { kind: "steward", identity: "" },
      dispatch_started_at: null, settled_at: null, proof: null, file_path: null,
    })] });
    routes["POST /api/channels/send"] = () => {
      throw new ApiError(409, "changed", { success: false, error_code: "preview_changed" });
    };
    render(<SendWells doc={BRIEF} />);
    fireEvent.click(await screen.findByTestId("prepared-send"));
    const chip = await screen.findByTestId("prepared-refused-chip");
    expect(chip.getAttribute("data-code")).toBe("preview_changed");
    expect(chip.textContent).toContain("PREVIEW CHANGED");
    expect(screen.queryByTestId("prepared-send")).toBeNull();
    expect(screen.getByTestId("prepared-discard").textContent).toBe("Discard");
  });

  it("PREPARED: first in SEND, the document's label, BY STEWARD, Send + Discard; the head chip counts it", async () => {
    routes["GET /api/channels/sends"] = () => ({ sends: [send({
      id: "chs_p", state: "prepared", prepare_operation_id: "op_p", prepared_by: { kind: "steward", identity: "" },
      dispatch_started_at: null, settled_at: null, proof: null, file_path: null,
    })] });
    render(<><PreparedChip docRef={REF} /><SendWells doc={BRIEF} /></>);
    const row = await screen.findByTestId("prepared-row");
    expect(within(row).getByTestId("prepared-label").textContent).toBe("BRIEF SEP 29");
    expect(within(row).getByTestId("prepared-by").textContent).toBe("BY STEWARD");
    expect(row.textContent).not.toContain("REV");
    expect(screen.getByTestId("prepared-send").textContent).toBe("Send");
    expect(screen.getByTestId("prepared-discard").textContent).toBe("Discard");
    expect((await screen.findByTestId("doc-prepared-chip")).textContent).toContain("PREPARED ×1");
    expect(screen.getByTestId("doc-prepared-chip").hasAttribute("data-head-chip")).toBe(true);
    const well = screen.getByTestId("send-well");
    const order = [...well.querySelectorAll("[data-testid=prepared-list], [data-testid=destination-list]")].map((e) => e.getAttribute("data-testid"));
    expect(order).toEqual(["prepared-list", "destination-list"]);
    noManualRow();
  });

  it("no PREPARED chip at zero", async () => {
    const { container } = render(<PreparedChip docRef={REF} />);
    await waitFor(() => expect(apiFetch).toHaveBeenCalled());
    expect(container.textContent).toBe("");
  });

  it("two seats of one document share one pick (the Chair and Intelligence -> BRIEF)", async () => {
    render(<><div data-testid="seat-a"><SendWells doc={BRIEF} /></div><div data-testid="seat-b"><SendWells doc={BRIEF} /></div></>);
    const a = screen.getByTestId("seat-a");
    const b = screen.getByTestId("seat-b");
    fireEvent.click(within(await within(a).findByTestId("destination-row")).getByText("Team folder"));
    await within(b).findByTestId("send-preview");
    await within(a).findByTestId("send-preview");
  });

  it("T2: PREVIEW CHANGED reads a fresh preview; Send again carries the NEW digest and settles", async () => {
    let n = 0;
    const digests: unknown[] = [];
    let stored: Send[] = [];
    routes["GET /api/channels/sends"] = () => ({ sends: stored });
    routes["POST /api/channels/preview"] = () => ({ payload_digest: `dig${++n}`, preview: { text: `# Brief v${n}` } });
    routes["POST /api/channels/send"] = (init) => {
      digests.push(init.json?.preview_digest);
      if (init.json?.preview_digest === "dig1") {
        throw new ApiError(409, "changed", { success: false, error_code: "preview_changed" });
      }
      stored = [send({ payload_digest: String(init.json?.preview_digest) })];
      return { send: stored[0] };
    };
    render(<SendWells doc={BRIEF} />);
    await pick("Team folder");
    const verb = await screen.findByTestId("send-verb");
    await waitFor(() => expect((verb as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(verb);
    expect((await screen.findByTestId("send-refused")).textContent).toContain("PREVIEW CHANGED");
    await waitFor(() => expect(screen.getByTestId("send-preview-body").textContent).toContain("Brief v2"));
    const again = screen.getByTestId("send-verb");
    await waitFor(() => expect((again as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(again);
    expect((await screen.findByTestId("send-sent")).textContent).toContain("SAVED");
    expect(digests).toEqual(["dig1", "dig2"]);
  });
});

describe("document identity: a well that changes document never shows or sends the old one (Astra r1 F1)", () => {
  const A: DocRef = { ref: "monday_brief:A", title: "Brief A", label: "BRIEF A" };
  const B: DocRef = { ref: "monday_brief:B", title: "Brief B", label: "BRIEF B" };
  const prepared = (ref: string, id: string) => send({
    id, document_ref: ref, state: "prepared", prepare_operation_id: `op_${id}`, dispatch_started_at: null,
    settled_at: null, proof: null, file_path: null,
  });
  const refOf = (path: string) => decodeURIComponent(path.split("document_ref=")[1] ?? "");
  const flush = () => act(async () => { await new Promise((r) => setTimeout(r, 30)); });

  it("prepared A switched to B with B's read delayed: Send submits B's send_id or nothing", async () => {
    let releaseB: (v: unknown) => void = () => {};
    const bRead = new Promise((r) => { releaseB = r; });
    const submitted: unknown[] = [];
    routes["GET /api/channels/sends"] = (_init, path) =>
      refOf(path) === A.ref ? { sends: [prepared(A.ref, "chs_prepared_A")] } : bRead;
    routes["POST /api/channels/send"] = (init) => {
      submitted.push(init.json?.send_id);
      return { send: { ...prepared(B.ref, String(init.json?.send_id)), state: "sent" } };
    };
    const { rerender } = render(<SendWells doc={A} />);
    await screen.findByTestId("prepared-send");
    rerender(<SendWells doc={B} />);
    await flush();
    const early = screen.queryByTestId("prepared-send");
    if (early) { fireEvent.click(early); await flush(); }
    expect(submitted.filter((id) => id !== "chs_prepared_B")).toEqual([]);
    expect(screen.queryByTestId("prepared-list")?.textContent ?? "").not.toContain("BRIEF A");
    await act(async () => { releaseB({ sends: [prepared(B.ref, "chs_prepared_B")] }); });
    fireEvent.click(await screen.findByTestId("prepared-send"));
    await waitFor(() => expect(submitted).toContain("chs_prepared_B"));
    expect(submitted.filter((id) => id !== "chs_prepared_B")).toEqual([]);
  });

  it("a late read for A never populates B's history", async () => {
    let releaseA: (v: unknown) => void = () => {};
    const aRead = new Promise((r) => { releaseA = r; });
    let aAsked = false;
    routes["GET /api/channels/sends"] = (_init, path) => {
      if (refOf(path) === A.ref && !aAsked) { aAsked = true; return aRead; }
      return { sends: [] };
    };
    const { rerender } = render(<SendWells doc={A} />);
    await waitFor(() => expect(aAsked).toBe(true));
    rerender(<SendWells doc={B} />);
    await flush();
    await act(async () => { releaseA({ sends: [send({ document_ref: A.ref, destination_name: "Folder for A" })] }); });
    await flush();
    expect(screen.queryByTestId("send-history")).toBeNull();
    expect(document.body.textContent).not.toContain("Folder for A");
    expect(screen.getByTestId("send-well").getAttribute("data-doc")).toBe(B.ref);
  });
});

describe("the receipt survives the click that leaves the row (Astra r2 F1)", () => {
  const other = folder({ id: "chd_o", name: "Other folder", target: { folder: "/Users/karol/Reports/Other" } });
  const pressSend = async () => {
    const verb = await screen.findByTestId("send-verb");
    await waitFor(() => expect((verb as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(verb);
  };
  const rowOf = (name: string) => screen.getAllByTestId("destination-row").find((r) => r.textContent?.includes(name))!;

  it("FAILED, then the row is closed: the failure word, NOTHING SENT and the egress stay on the row", async () => {
    let stored: Send[] = [];
    routes["GET /api/channels/sends"] = () => ({ sends: stored });
    routes["POST /api/channels/send"] = () => {
      stored = [send({ state: "failed", reason: "permission_denied", proof: null })];
      return { send: stored[0] };
    };
    render(<SendWells doc={BRIEF} />);
    await pick("Team folder");
    await pressSend();
    expect((await screen.findByTestId("send-failed")).textContent).toContain("NO PERMISSION");
    fireEvent.click(within(rowOf("Team folder")).getByText("Team folder"));   // close it
    await waitFor(() => expect(screen.queryByTestId("send-open")).toBeNull());
    const row = rowOf("Team folder");
    expect(row.textContent).toContain("FAILED");
    expect(row.textContent).toContain("NO PERMISSION");
    expect(row.textContent).toContain("NOTHING SENT");
    expect(row.textContent).toContain("THIS DEVICE");
  });

  it("REFUSED, then another row is picked: the refusal word and NOTHING SENT stay on the first row", async () => {
    routes["GET /api/channels/destinations"] = () => ({ destinations: [folder(), other] });
    routes["POST /api/channels/send"] = () => {
      throw new ApiError(409, "changed", { success: false, error_code: "destination_changed" });
    };
    render(<SendWells doc={BRIEF} />);
    await pick("Team folder");
    await pressSend();
    await screen.findByTestId("send-refused");
    await pick("Other folder");
    await waitFor(() => expect(screen.getByTestId("send-open").getAttribute("data-destination")).toBe("Other folder"));
    const row = rowOf("Team folder");
    expect(row.textContent).toContain("REFUSED");
    expect(row.textContent).toContain("DESTINATION CHANGED");
    expect(row.textContent).toContain("NOTHING SENT");
  });
});

