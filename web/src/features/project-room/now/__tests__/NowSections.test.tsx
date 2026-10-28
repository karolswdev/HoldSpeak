import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { thisWeekGroups, WaitingOnSection } from "../NowSections";
import { resetSendStore } from "../../../../desk/surface/send";
import type { RoomNeedsYouItem } from "../../model";

const apiFetch = vi.fn();
vi.mock("../../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../../lib/api")>("../../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../../../pages/cores/connections/api", async () => {
  const actual = await vi.importActual<typeof import("../../../../pages/cores/connections/api")>("../../../../pages/cores/connections/api");
  return { ...actual, fetchConnections: () => Promise.resolve({ tools: [] }) };
});

const PR_URL = "https://github.com/acme/payments/pull/42";
const STEP = {
  step_id: "step-waiting-1",
  state: "proposed",
  pr_number: 42,
  pr_title: "Payments migration review",
  pr_url: PR_URL,
  reviewer_login: "mira",
  days: 3,
  comment_text: "This PR has been waiting for review for 3 days. Flagged by HoldSpeak.",
  host: "github.com",
  created_at: "2026-10-19T10:00:00Z",
};

const waiting = (url: string | null): RoomNeedsYouItem[] => [{
  source: "action_item",
  title: "Review the payments migration",
  why: "WAITING ON MIRA",
  since: "2026-10-18T10:00:00Z",
  url,
  verb: "open",
  severity: "warning",
  direction: "theirs",
  owner: "Mira",
  dueAt: "2026-10-21",
}];

afterEach(() => { vi.clearAllMocks(); resetSendStore(); });

describe("Waiting on Nudge", () => {
  it("requires the waiting row to carry the real destination", () => {
    render(<WaitingOnSection items={waiting(null)} nudges={[STEP]} />);
    expect(screen.getByTestId("waiting-on-row")).toBeTruthy();
    expect(screen.queryByTestId("waiting-on-nudge")).toBeNull();
  });

  it("opens a prepared Send well and sends only after the owner presses Send", async () => {
    apiFetch.mockResolvedValue({ success: true, sent_at: "2026-10-19T10:01:00Z" });
    render(<WaitingOnSection items={waiting(PR_URL)} nudges={[STEP]} />);

    expect(screen.getByTestId("waiting-on-nudge")).toBeTruthy();
    expect(apiFetch).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("waiting-on-nudge"));
    expect(await screen.findByTestId("nudge-card")).toBeTruthy();
    expect(screen.getByTestId("nudge-card").textContent).toContain("Nudge ready");
    expect(screen.getByTestId("nudge-card").textContent).toContain("GITHUB.COM");
    expect(apiFetch).not.toHaveBeenCalled();

    fireEvent.click(screen.getByTestId("nudge-send"));
    await waitFor(() => expect(screen.getByTestId("nudge-receipt-row")).toBeTruthy());
    expect(apiFetch).toHaveBeenCalledWith(
      "/api/nudges/step-waiting-1/send",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("opens the same Send well for an exact saved Jira destination", async () => {
    const destination = {
      id: "dest-jira-payments",
      name: "Jira Payments",
      channel: "jira",
      account: { site: "acme.atlassian.net", email: "owner@example.com" },
      target: { key: "PAY-123" },
      synced: false,
      state: "active",
      created_at: "2026-10-19T10:00:00Z",
      parked_at: null,
    };
    const documentRef = "project_nudge:project-1:action-1";
    const calls: Array<[string, RequestInit | undefined]> = [];
    apiFetch.mockImplementation((path: string, init?: RequestInit) => {
      calls.push([path, init]);
      if (path === "/api/channels/destinations") return Promise.resolve({ destinations: [destination] });
      if (path.startsWith("/api/channels/sends?")) return Promise.resolve({ sends: [] });
      if (path === "/api/channels/preview") return Promise.resolve({
        payload_digest: "preview-jira",
        preview: { title: "Payments migration · Review request", text: "Please review: Review the migration" },
      });
      if (path === "/api/channels/send") return Promise.resolve({ send: {
        id: "send-jira-1", document_ref: documentRef, destination_id: destination.id,
        destination_name: destination.name, channel: "jira", account: destination.account,
        target: destination.target, payload_digest: "preview-jira", preview: { text: "Please review" },
        prepared_by: { kind: "owner", identity: "" }, prepare_operation_id: null,
        state: "sent", reason: null, proof: { key: "PAY-123" }, file_path: null,
        created_at: "2026-10-19T10:00:00Z", dispatch_started_at: "2026-10-19T10:00:00Z",
        settled_at: "2026-10-19T10:00:01Z",
      } });
      return Promise.reject(new Error(`unrouted ${path}`));
    });
    const nudge = {
      documentRef,
      destinationId: destination.id,
      destinationName: destination.name,
      channel: "jira",
      target: "PAY-123",
      title: "Payments migration · Review request",
    };
    render(<WaitingOnSection items={[{
      ...waiting(null)[0],
      nudge,
    }]} />);

    expect(screen.getByTestId("waiting-on-nudge")).toBeTruthy();
    expect(calls).toEqual([]);
    fireEvent.click(screen.getByTestId("waiting-on-nudge"));
    expect(await screen.findByTestId("generic-nudge-card")).toBeTruthy();
    expect(await screen.findByText("Nudge ready")).toBeTruthy();
    await waitFor(() => expect(calls.some(([path]) => path === "/api/channels/preview")).toBe(true));
    expect(calls.some(([path, init]) => path === "/api/channels/send" && init?.method === "POST")).toBe(false);
    fireEvent.click(await screen.findByTestId("send-verb"));
    await waitFor(() => expect(calls.some(([path, init]) => path === "/api/channels/send" && init?.method === "POST")).toBe(true));
  });
});

describe("the Room Now page groups", () => {
  it("puts open work before decisions and keeps the page source", () => {
    const groups = thisWeekGroups(
      {
        nextDate: null,
        lastUpdateAt: null,
        meetingsThisWeek: 0,
        risks: [],
        decided: [{ id: "d1", text: "Keep the ledger read-only", at: "", ref: "", source: "", sourceRef: "decision:d1" }],
      },
      [{
        slug: "what-is-open",
        question: "What is open and who owes it?",
        sentences: [{ text: "Mira owes the rollback runbook.", refs: [{ ref: "meeting:m1", token: "1:1 WITH MIRA", opens: true }] }],
        built_at: "2026-10-19T09:00:00Z",
        stale: false,
        new_sources: 0,
        model: "pages",
        boundary: "local",
      }],
    );

    expect(groups.map((group) => group.title)).toEqual(["Open", "Decided"]);
    expect(groups[0].lines[0].refs).toEqual([{ ref: "meeting:m1", token: "1:1 WITH MIRA", opens: true }]);
  });

  it("names an open risk item as a dot and a word, not a Risk token (W3-B)", () => {
    const groups = thisWeekGroups({
      nextDate: null, lastUpdateAt: null, meetingsThisWeek: 0, decided: [],
      risks: [
        { text: "Card vault vendor contract ends", ref: "project_item:i1", token: "RISK", source: "Risk", opens: true },
        { text: "Settlement may slip", ref: "meeting:m1", token: "MTG", source: "Standup", opens: true },
      ],
    }, []);
    const [risk, said] = groups[0].lines;
    expect(risk.riskRef).toBe("project_item:i1");
    expect(risk.refs).toEqual([]);
    expect(said.riskRef).toBeUndefined();
    expect(said.refs).toEqual([{ ref: "meeting:m1", token: "MTG", opens: true }]);
  });
});
