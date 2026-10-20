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

// ── Betterment send S1: the Send face tells the truth ──────────────────────
//
// Every answer below is the REAL hub's, recorded by tests/unit/test_desk_send.py
// (fixtures/send-hub/*.json; HOLDSPEAK_WIRE_WRITE=1 rewrites them) through the
// recon's runner scripts (gh and acli never ran, nothing left the machine).

import BEFORE from "./fixtures/send-hub/destinations-before-send.json";
import POSTED from "./fixtures/send-hub/destinations-after-posted.json";
import NO_ANSWER from "./fixtures/send-hub/sends-no-answer.json";
import UNCHECKED from "./fixtures/send-hub/unchecked-update.json";
import { MeetingSendWell } from "../../meetings/MeetingSendWell";
import { pickFor, resetSendTo } from "../windowSend";
import { keepPlace } from "../deskMemory";
import { useDesk } from "../store";

type Recorded = {
  document_ref: string;
  destinations: { id: string; name: string; channel: string }[];
  sends: unknown[];
  previews: { destination_id: string }[];
};

function replay(rec: Recorded, posted: Record<string, unknown>[] = []) {
  apiFetch.mockImplementation((path: string, init: Init = {}) => {
    const key = `${init.method ?? "GET"} ${path.split("?")[0]}`;
    if (key === "GET /api/channels/destinations") return Promise.resolve({ destinations: rec.destinations });
    if (key === "GET /api/channels/sends") {
      const asked = new URLSearchParams(path.split("?")[1] ?? "").get("document_ref");
      return Promise.resolve({ sends: asked === rec.document_ref ? rec.sends : [] });
    }
    if (key === "POST /api/channels/preview") return Promise.resolve(rec.previews.find((p) => p.destination_id === init.json?.destination_id));
    if (key === "POST /api/channels/send") { posted.push(init.json ?? {}); return new Promise(() => {}); }
    return Promise.reject(new TypeError(`unrouted ${path}`));
  });
}

const docOf = (rec: Recorded): DocRef => ({ ref: rec.document_ref, title: "Brief", label: "BRIEF" });
const destId = (rec: Recorded, name: string) => rec.destinations.find((d) => d.name === name)!.id;

async function openRow(name: string) {
  fireEvent.click((await rowOf(name)).querySelector<HTMLElement>(`.surface-primary[data-destination='${name}']`)!);
  return waitFor(() => {
    const o = openOf(name);
    expect(o?.querySelector("[data-testid=send-verbs]")).toBeTruthy();
    return o!;
  });
}

describe("betterment send S1: the account chip says only a sign-in failure, and a good send is a good check", () => {
  it("the Accounts check could not reach GitHub: the GitHub row says so; after a recorded POSTED it says nothing", async () => {
    replay(BEFORE as Recorded);
    const first = render(<SendWells doc={docOf(BEFORE as Recorded)} />);
    expect(line(await rowOf("acme/payments #42"))).toContain("COULD NOT CHECK");
    // Jira was never checked: no NEVER CHECKED chip (nothing failed).
    expect(line(await rowOf("PAY-12 ticket"))).not.toMatch(/NEVER CHECKED|NOT CHECKED/);
    first.unmount();

    resetSendStore();
    replay(POSTED as Recorded);
    render(<SendWells doc={docOf(POSTED as Recorded)} />);
    for (const name of ["acme/payments #42", "PAY-12 ticket"]) {
      const words = line(await waitFor(async () => {
        const r = await rowOf(name);
        expect(line(r)).toMatch(/POSTED|COMMENTED/);
        return r;
      }));
      expect(words).not.toMatch(/COULD NOT CHECK|UNREACHABLE|NOT CHECKED|NEVER CHECKED|CONNECTED|WORKS/);
    }
    // After a send that worked, the verb stays "Send again".
    const open = await openRow("acme/payments #42");
    expect(within(open).getByTestId("send-verb").textContent).toBe("Send again");
  });
});

describe("betterment send S8: an unchecked published update stays sendable", () => {
  it("replays the producer's warning above the published words", async () => {
    const rec = UNCHECKED as Recorded;
    replay(rec);
    render(<SendWells doc={docOf(rec)} />);

    const preview = await screen.findByTestId("send-preview");
    expect(preview.textContent).toContain("WarningNot checked yet: no claim in this update was accepted");
    expect(preview.textContent).toContain("The rollout is complete.");
    expect(preview.textContent).toContain("No decisions in this window.");
    expect(preview.textContent).not.toContain("UNVERIFIED");
  });
});

describe("betterment send S1: a failed send says Try again; a send with no answer says what to do", () => {
  it("FAILED: the verb is Try again, not Send again", async () => {
    replay(NO_ANSWER as Recorded);
    render(<SendWells doc={docOf(NO_ANSWER as Recorded)} />);
    const open = await openRow("acme/payments #4242");
    expect(within(open).getByTestId("send-failed")).toBeTruthy();
    expect(within(open).getByTestId("send-verb").textContent).toBe("Try again");
  });

  it.each([["first read", false], ["after a reload", true]] as const)(
    "no answer in time (%s): the line, Check PAY-12, Try again; never SENDING",
    async (_when, reload) => {
      replay(NO_ANSWER as Recorded);
      if (reload) resetSendStore(true);
      render(<SendWells doc={docOf(NO_ANSWER as Recorded)} />);
      const open = await openRow("PAY-12 ticket");
      expect(within(open).getByTestId("send-no-answer").textContent)
        .toBe("No answer from Jira. Check PAY-12 before you try again.");
      const check = within(open).getByTestId("send-check");
      expect(check.textContent).toBe("Check PAY-12");
      expect(check.getAttribute("data-href")).toBe("https://acme.atlassian.net/browse/PAY-12");
      const verb = within(open).getByTestId("send-verb") as HTMLButtonElement;
      expect(verb.textContent).toBe("Try again");
      expect(verb.disabled).toBe(false);
      expect(line(open)).not.toContain("SENDING");
      expect(line(await rowOf("PAY-12 ticket"))).not.toContain("SENDING");
    },
  );
});

describe("betterment send S1: Send to ▸ opens the well with THAT destination, on the form it shows", () => {
  it("the meeting's well opens on Summary (his last form): Send to ▸ PAY-12 picks PAY-12 there, not the last-used row", async () => {
    const rec = NO_ANSWER as Recorded;
    replay({ ...rec, sends: [] });
    resetSendTo();
    const meeting = "m-s1-pick";
    keepPlace(`meeting/form/${meeting}`, "meeting_summary");
    keepPlace(`send/pick/meeting_summary:${meeting}`, destId(rec, "acme/payments #4242"));   // the last-used row
    useDesk.setState({ windowsById: {
      "surface-meetings": { id: "surface-meetings", kind: "surface", applicationKey: "meetings", scope: `meeting:${meeting}`, persistence: "workspace" },
    } } as never);
    const front = vi.spyOn(useDesk.getState(), "restorePanel").mockImplementation(() => {});
    try {
      // The well is not mounted yet (the recon's case); the meeting read gets no answer.
      pickFor("surface-meetings", destId(rec, "PAY-12 ticket"));
      render(<MeetingSendWell meetingId={meeting} title="Payments platform sync" />);
      await waitFor(() => expect(screen.getByTestId("send-well").getAttribute("data-doc")).toBe(`meeting_summary:${meeting}`));
      await waitFor(() => expect(openOf("PAY-12 ticket")).not.toBeNull());
      expect(openOf("acme/payments #4242")).toBeNull();
      expect(document.querySelectorAll("[data-testid=send-open]")).toHaveLength(1);
    } finally {
      front.mockRestore();
      keepPlace(`meeting/form/${meeting}`, "");
      keepPlace(`send/pick/meeting_summary:${meeting}`, "");
    }
  });
});

describe("betterment send S1: a GitHub destination saves from the form", () => {
  it("the Accounts row knows no login: Save still works (the hub asks gh), and the saved row shows the login gh named", async () => {
    const { Destinations } = await import("../../pages/cores/connections/Destinations");
    const rec = BEFORE as Recorded & { destinations: Record<string, unknown>[] };
    const github = rec.destinations.find((d) => d.channel === "github")!;
    let listed: unknown[] = [];
    const saved: Record<string, unknown>[] = [];
    apiFetch.mockImplementation((path: string, init: Init = {}) => {
      const key = `${init.method ?? "GET"} ${path.split("?")[0]}`;
      if (key === "GET /api/channels/destinations") return Promise.resolve({ destinations: listed });
      if (key === "POST /api/channels/destinations") {
        saved.push(init.json ?? {});
        listed = rec.destinations;
        return Promise.resolve({ destination: github, replaced: null });
      }
      return Promise.reject(new TypeError(`unrouted ${path}`));
    });
    render(<Destinations />);
    const form = await screen.findByTestId("dest-form");
    fireEvent.change(within(form).getByLabelText("Channel"), { target: { value: "github" } });
    const account = screen.getByTestId("dest-github-account");
    expect(line(account)).not.toMatch(/COULD NOT CHECK|UNREACHABLE|Set up account/);
    fireEvent.change(screen.getByTestId("dest-repo"), { target: { value: "acme/payments" } });
    fireEvent.change(screen.getByTestId("dest-number"), { target: { value: "42" } });
    const save = screen.getByTestId("dest-save") as HTMLButtonElement;
    expect(save.disabled).toBe(false);
    fireEvent.click(save);
    await waitFor(() => expect(saved).toEqual([expect.objectContaining({ channel: "github", repo: "acme/payments", number: 42 })]));
    const open = await screen.findByTestId("dest-open");
    expect(line(open)).toContain("@karol-arch");
  });
});
