// The Send well app (the Chair's Brief): the face half of the built-in
// "HoldSpeak folder" (owner ruling 2026-10-05, "strong defaults, batteries
// included"). The test diet (2026-10-11) moves the face facts of
// tests/e2e/test_builtin_send_folder_glass.py here; the hub half (the file
// written into Documents/HoldSpeak/Sent, the folder made by the first send,
// the iCloud egress on the proof) is tests/unit/test_desk_send.py.
//
// The real SendWells with its real store; only apiFetch is mocked, by URL,
// with the hub's REAL answers: every payload below is copied from the real
// hub (tests/unit/_philo10_send.py rig, a fresh desk, the e2e's seed); only
// the scratch HOME path is replaced by /Users/me.
//
// The other states of the well (refused, failed, unknown, prepared) are in
// web/src/desk/surface/send/__tests__/SendWell.test.tsx.

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../pages/cores/connections/api", async () => {
  const actual = await vi.importActual<typeof import("../../pages/cores/connections/api")>("../../pages/cores/connections/api");
  return { ...actual, fetchConnections: () => Promise.resolve({ tools: [] }) };
});

import { SendWells, resetSendStore, type DocRef } from "../surface/send";

const REF = "monday_brief:brief-d54cedb57b854fdab510b63fdf911c06";
const BRIEF: DocRef = { ref: REF, title: "Brief · Sunday 11 Oct 2026", label: "BRIEF 2026-10-11" };
const SENT = "/Users/me/Documents/HoldSpeak/Sent";
const TEAM = "/Users/me/Reports/Team";
const NAME = "HoldSpeak folder";
const PREVIEW_TEXT = "# Brief · Sunday 11 Oct 2026\nPeriod: OCT 09-11\nGenerated: 11 Oct 2026, 09:25\n\n2 things waiting.\n\n## Waiting\n- No engine for summaries\n  Choose an engine\n\n## Decisions\n- Review decision: Freeze the old ledger on Nov 3\n";
const DIGEST = "10f721389d743c63a14f0eff5d053ad671696c6b006e9ea69e00352e01a1b105";

/** GET /api/channels/destinations on a fresh desk (channel_service._destination_view). */
const builtin = (icloud: boolean) => ({
  id: "holdspeak-folder", name: NAME, channel: "file", account: {},
  target: { builtin: "documents", folder: SENT, display: "~/Documents/HoldSpeak/Sent", ...(icloud ? { cloud: "icloud" } : {}) },
  builtin: true, target_digest: "fd9961900ca6267811a8b99949df5afca789de5ccd014383651ea3ea9b9d43af",
  synced: icloud, state: "active", badge: icloud ? "cloud" : "local",
  created_at: "2026-10-11T15:25:29+00:00", parked_at: null, connection: null,
});
/** A saved folder (POST /api/channels/destinations, then the same view). */
const team = {
  id: "chd_team", name: "Team folder", channel: "file", account: {},
  target: { folder: TEAM, display: "~/Reports/Team" },
  builtin: false, target_digest: "e1", synced: false, state: "active", badge: "local",
  created_at: "2026-10-11T15:25:30+00:00", parked_at: null, connection: null,
};
/** POST /api/channels/preview. */
const preview = (dest: { id: string; badge: string }) => ({
  document_ref: REF, title: BRIEF.title, destination_id: dest.id, channel: "file", badge: dest.badge,
  payload_digest: DIGEST, size: 218, preview: { text: PREVIEW_TEXT },
});
/** The send row the hub stores and answers (POST /api/channels/send `.send`, GET /api/channels/sends). */
const sendRow = (dest: ReturnType<typeof builtin> | typeof team, id: string, icloud: boolean) => {
  const folder = String(dest.target.folder);
  const path = `${folder}/2026-10-11-brief-2026-10-11-brief-2026-10-11-${id}.md`;
  return {
    id: `chs_${id}`, document_ref: REF, destination_id: dest.id, destination_name: dest.name,
    channel: "file", badge: dest.badge, account: {}, target: dest.target, target_digest: dest.target_digest,
    payload_digest: DIGEST, document_json: { label: BRIEF.label, slug: "brief-2026-10-11", title: BRIEF.title },
    size: 218, preview: { text: PREVIEW_TEXT }, prepared_by: { kind: "owner", identity: "owner-session" },
    prepare_operation_id: null, send_operation_id: `op_${id}`, state: "sent", reason: null,
    proof: { ...(icloud ? { egress: "icloud" } : {}), path, sha256: DIGEST, size: 218 },
    file_path: path, created_at: "2026-10-11T15:25:31+00:00", dispatch_started_at: "2026-10-11T15:25:31+00:00",
    settled_at: "2026-10-11T15:25:31+00:00", dispatch_seq: 1, egress: icloud ? "icloud" : null,
  };
};

type Init = RequestInit & { json?: Record<string, unknown> };
let destinations: unknown[];
let stored: unknown[];
let posted: Record<string, unknown>[];

function wire(rows: unknown[], icloud = false) {
  destinations = rows;
  stored = [];
  posted = [];
  apiFetch.mockImplementation((path: string, init: Init = {}) => {
    const key = `${init.method ?? "GET"} ${path.split("?")[0]}`;
    if (key === "GET /api/channels/destinations") return Promise.resolve({ destinations });
    if (key === "GET /api/channels/sends") return Promise.resolve({ sends: stored });
    if (key === "POST /api/channels/preview") {
      const dest = (destinations as { id: string; badge: string }[]).find((d) => d.id === init.json?.destination_id)!;
      return Promise.resolve(preview(dest));
    }
    if (key === "POST /api/channels/send") {
      posted.push(init.json ?? {});
      const dest = (destinations as (ReturnType<typeof builtin> | typeof team)[]).find((d) => d.id === init.json?.destination_id)!;
      const row = sendRow(dest, String(stored.length + 1).padStart(8, "a"), icloud && dest.builtin);
      stored = [...stored, row];
      return Promise.resolve({ send: row, outcome: "sent", operation_id: row.send_operation_id, receipt: null });
    }
    return Promise.reject(new Error(`unrouted ${path}`));
  });
}

beforeEach(() => {
  resetSendStore();
  apiFetch.mockReset();
  localStorage.clear();
  sessionStorage.clear();
});

const rowOf = async (name: string) =>
  (await screen.findAllByTestId("destination-row")).find((r) => r.querySelector(`[data-destination='${name}']`))!;
const line = (el: Element) => (el.textContent ?? "").replace(/\s+/g, " ");
const openOf = (name: string) => document.querySelector<HTMLElement>(`[data-testid=send-open][data-destination='${name}']`);

async function press(name: string) {
  const open = await waitFor(() => {
    const o = openOf(name);
    expect(o).not.toBeNull();
    return o!;
  });
  const verb = await within(open).findByTestId("send-verb");
  await waitFor(() => expect((verb as HTMLButtonElement).disabled).toBe(false));
  fireEvent.click(verb);
  return waitFor(() => {
    const receipt = openOf(name)?.querySelector<HTMLElement>("[data-receipt=latest][data-state=sent]");
    expect(receipt).toBeTruthy();
    return receipt!;
  });
}

describe("the built-in HoldSpeak folder on a fresh desk (owner ruling 2026-10-05)", () => {
  it.each([["plain", false], ["icloud", true]] as const)(
    "%s Documents: ONE row, picked with no click; its words; Send says SAVED",
    async (_docs, icloud) => {
      // replaces: tests/e2e/test_builtin_send_folder_glass.py::TestBuiltinSendFolderGlass::test_the_builtin_folder_is_one_picked_row_and_send_writes_into_documents (face half)
      wire([builtin(icloud)], icloud);
      render(<SendWells doc={BRIEF} />);
      const row = await rowOf(NAME);
      expect(screen.getAllByTestId("destination-row")).toHaveLength(1);
      expect(screen.queryByTestId("send-none")).toBeNull();
      // Picked with no click: the preview of THIS brief and Send are open.
      const pv = await screen.findByTestId("send-preview");
      expect(pv.textContent).toContain("Review decision: Freeze the old ledger on Nov 3");
      const words = line(row);
      expect(words).toContain(NAME);
      expect(words).toContain("FILE");
      expect(words).not.toContain("THIS DEVICE");
      expect(words.includes("ICLOUD")).toBe(icloud);
      // The open destination leaves its target to the exact preview field.
      expect(pv.textContent).toContain("HoldSpeak/Sent");
      expect(words).not.toContain("~/");
      expect(row.querySelector(".send-target")).toBeNull();
      expect(screen.getByTestId("send-add-destination").textContent).toBe("Add destination");

      const receipt = await press(NAME);
      expect(posted).toEqual([expect.objectContaining({ document_ref: REF, destination_id: "holdspeak-folder", preview_digest: DIGEST })]);
      const said = line(receipt);
      expect(said).toContain("SAVED");
      expect(said.includes("ICLOUD")).toBe(icloud);
    },
  );
});

describe("a Phase 11 brief send to a saved folder with the built-in present", () => {
  it("two destinations: nothing picked by itself; each send has its own receipt; the built-in stays as it was", async () => {
    // replaces: tests/e2e/test_builtin_send_folder_glass.py::TestBuiltinSendFolderGlass::test_a_phase11_brief_send_to_a_saved_folder_with_the_builtin_present (face half)
    wire([builtin(false), team]);
    render(<SendWells doc={BRIEF} />);
    await rowOf("Team folder");
    await rowOf(NAME);
    expect(screen.getAllByTestId("destination-row")).toHaveLength(2);
    expect(document.querySelectorAll("[data-testid=send-open]")).toHaveLength(0);

    fireEvent.click(within(await rowOf("Team folder")).getByText("Team folder"));
    await press("Team folder");
    expect(posted.map((p) => p.destination_id)).toEqual(["chd_team"]);
    const builtinLine = line(await rowOf(NAME));
    expect(builtinLine).not.toContain("THIS DEVICE");
    expect(builtinLine).not.toContain("SAVED");

    fireEvent.click(within(await rowOf(NAME)).getByText(NAME));
    const receipt = await press(NAME);
    expect(line(receipt)).toContain("SAVED");
    expect(posted.map((p) => p.destination_id)).toEqual(["chd_team", "holdspeak-folder"]);
  });
});
