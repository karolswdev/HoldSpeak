/** PHILO-13-15 (C5) — `Send to ▸` from any document window: ONE composition
 * (the window menu and the Object menu), its reads and their words, the
 * withheld cases, the push seam, the Room link, and the artifact window's
 * SEND well. Built to the owner's ratified canvas (story-15-canvas, "Ratify,
 * build it", 2026-10-03). The glass proof through the real hub is
 * tests/e2e/test_philo13_15_send_to_glass.py. */
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { resolve as resolvePath } from "node:path";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Destination } from "../../features/channels/channels";

const apiFetch = vi.fn();
vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../pages/cores/connections/api", async () => {
  const actual = await vi.importActual<typeof import("../../pages/cores/connections/api")>("../../pages/cores/connections/api");
  return { ...actual, fetchConnections: () => Promise.resolve({ tools: [] }) };
});

import {
  SEND_TO, latestPublished, pickFor, primeSendTo, readDestinations, resetSendTo, sendToEntry, withSendTo,
} from "../windowSend";
import { SendWells, pickDestination, pickedDestination, resetSendStore } from "../surface/send";
import { MeetingSendWell } from "../../meetings/MeetingSendWell";
import { useDesk } from "../store";
import type { WorkMenuEntry } from "../components/DeskMenu";

const folder = (over: Partial<Destination> = {}): Destination => ({
  id: "chd_f", name: "Team updates", channel: "file", account: {}, target: { folder: "/Users/k/Team" },
  synced: false, state: "active", created_at: "2026-10-02T08:00:00Z", parked_at: null, ...over,
});
const jira = folder({ id: "chd_j", name: "PAY-118", channel: "jira", account: { site: "acme.atlassian.net", email: "o@acme.test" }, target: { key: "PAY-118" } });

type Route = (init: RequestInit & { json?: Record<string, unknown> }) => unknown;
let routes: Record<string, Route>;
beforeEach(() => {
  resetSendTo();
  resetSendStore();
  apiFetch.mockReset();
  routes = {
    "GET /api/channels/destinations": () => ({ destinations: [folder(), jira, folder({ id: "chd_p", name: "Old", state: "parked" })] }),
    "GET /api/channels/sends": () => ({ sends: [] }),
    "POST /api/channels/preview": () => ({ payload_digest: "dig", preview: { text: "# Doc" } }),
  };
  apiFetch.mockImplementation((path: string, init: RequestInit & { json?: Record<string, unknown> } = {}) => {
    const r = routes[`${init.method ?? "GET"} ${path.split("?")[0]}`];
    if (!r) return Promise.reject(new TypeError(`unrouted ${path}`));
    try { return Promise.resolve(r(init)); } catch (e) { return Promise.reject(e); }
  });
});

const sub = (e: WorkMenuEntry | null) => e as Extract<WorkMenuEntry, { type: "sub" }>;
const labels = (e: WorkMenuEntry | null) => sub(e).entries.map((x) => (x.type === "sep" ? "—" : x.label));
const settle = () => act(async () => { await new Promise((r) => setTimeout(r, 0)); });

describe("one composition: Send to ▸ with the saved destinations", () => {
  it("a decision window: `Send to` with the ACTIVE destinations as `<name> · <CHANNEL>`", async () => {
    await readDestinations();
    const e = sendToEntry("pullout:decision:dec-1");
    expect(sub(e).label).toBe(SEND_TO.label);
    expect(labels(e)).toEqual(["Team updates · FILE", "PAY-118 · JIRA"]);
  });

  it("the window menu: Send to ▸ leads, its own group, above Iconify", async () => {
    await readDestinations();
    const menu = withSendTo(sendToEntry("pullout:artifact:art-1"), [{ type: "item", id: "window.minimize", label: "Iconify", onSelect: () => {} }]);
    expect(menu.map((m) => m.type === "sep" ? "—" : m.label)).toEqual(["Send to", "—", "Iconify"]);
  });

  it("no saved destination: `Add destination` opens Settings at the form", async () => {
    routes["GET /api/channels/destinations"] = () => ({ destinations: [] });
    await readDestinations();
    const open = vi.spyOn(useDesk.getState(), "openSurfaceWindow").mockImplementation(() => {});
    const e = sendToEntry("pullout:decision:dec-1");
    expect(labels(e)).toEqual([SEND_TO.add]);
    (sub(e).entries[0] as Extract<WorkMenuEntry, { type: "item" }>).onSelect();
    expect(open).toHaveBeenCalledWith("configure-settings", "integrations");
    open.mockRestore();
  });

  it("withheld where the window's document cannot send: a note, Settings, an empty brief window", async () => {
    await readDestinations();
    expect(sendToEntry("pullout:note:n1")).toBeNull();
    expect(sendToEntry("surface-configure-settings")).toBeNull();
    expect(sendToEntry("chair:brief")).toBeNull();
    expect(sendToEntry(null)).toBeNull();
  });
});

describe("the reads: CHECKING, CAN'T CHECK, OFFLINE, a known absence", () => {
  it("a meeting: CHECKING while the summary is read (never a refusal), then `Send to`", async () => {
    let answer!: (v: unknown) => void;
    routes["GET /api/meetings/m1"] = () => new Promise((r) => { answer = r; });
    await readDestinations();
    primeSendTo("pullout:meeting:m1");
    expect(sub(sendToEntry("pullout:meeting:m1")).label).toBe(SEND_TO.checking);
    expect(labels(sendToEntry("pullout:meeting:m1"))).toContain("Team updates · FILE");
    answer({ id: "m1", intel: { summary: "We agreed." } });
    await settle();
    expect(sub(sendToEntry("pullout:meeting:m1")).label).toBe(SEND_TO.label);
  });

  it("a meeting known to have no summary: withheld", async () => {
    routes["GET /api/meetings/m2"] = () => ({ id: "m2", intel: { summary: "" } });
    await readDestinations();
    primeSendTo("pullout:meeting:m2");
    await settle();
    expect(sendToEntry("pullout:meeting:m2")).toBeNull();
  });

  it("the Room: CHECKING, then CAN'T CHECK on a failed read (the rows stay)", async () => {
    useDesk.setState({ windowsById: { "surface-project-memory": { id: "surface-project-memory", kind: "surface", applicationKey: "project-memory", scope: "project:p1", persistence: "workspace" } } } as never);
    routes["GET /api/projects/p1/updates"] = () => { throw new TypeError("Failed to fetch"); };
    await readDestinations();
    expect(sub(sendToEntry("surface-project-memory")).label).toBe(SEND_TO.checking);
    primeSendTo("surface-project-memory");
    await settle();
    const e = sendToEntry("surface-project-memory");
    expect(sub(e).label).toBe(SEND_TO.cantCheck);
    expect(labels(e)).toEqual(["Team updates · FILE", "PAY-118 · JIRA"]);
  });

  it("the Room with no published update: withheld", async () => {
    useDesk.setState({ windowsById: { "surface-project-memory": { id: "surface-project-memory", kind: "surface", applicationKey: "project-memory", scope: "project:p2", persistence: "workspace" } } } as never);
    routes["GET /api/projects/p2/updates"] = () => ({ updates: [{ id: "u1", lifecycle: "draft", published_at: null }] });
    await readDestinations();
    primeSendTo("surface-project-memory");
    await settle();
    expect(sendToEntry("surface-project-memory")).toBeNull();
  });

  it("offline: `Send to · OFFLINE` keeps the last-read rows; never read, it is withheld", async () => {
    routes["GET /api/channels/destinations"] = () => { throw new TypeError("Failed to fetch"); };
    await readDestinations();
    expect(sendToEntry("pullout:decision:dec-1")).toBeNull();
    routes["GET /api/channels/destinations"] = () => ({ destinations: [folder()] });
    await readDestinations();
    routes["GET /api/channels/destinations"] = () => { throw new TypeError("Failed to fetch"); };
    await readDestinations();
    const e = sendToEntry("pullout:decision:dec-1");
    expect(sub(e).label).toBe(SEND_TO.offline);
    expect(labels(e)).toEqual(["Team updates · FILE"]);
  });

  it("the tie rule: the greatest published_at, then the first the hub lists", () => {
    expect(latestPublished([
      { id: "u3", lifecycle: "draft", published_at: null },
      { id: "u2", lifecycle: "published", published_at: "2026-10-02T09:00:00" },
      { id: "u1", lifecycle: "published", published_at: "2026-10-02T09:00:00" },
      { id: "u0", lifecycle: "published", published_at: "2026-10-01T09:00:00" },
    ])).toBe("u2");
    expect(latestPublished([{ id: "u0", lifecycle: "superseded", published_at: "2026-10-01" }])).toBeNull();
  });
});

describe("the push seam and the pick", () => {
  it("a pick sets an OPEN well in place (no remount); a second pick changes it in place", async () => {
    render(<SendWells doc={{ ref: "desk_decision:dec-1", title: "Decision", label: "DECISION DEC1" }} />);
    const well = await screen.findByTestId("send-well");
    await screen.findAllByTestId("destination-row");
    act(() => pickDestination("desk_decision:dec-1", "chd_f"));
    const open = await screen.findByTestId("send-open");
    expect(open.getAttribute("data-destination")).toBe("Team updates");
    act(() => pickDestination("desk_decision:dec-1", "chd_j"));
    await waitFor(() => expect(screen.getByTestId("send-open").getAttribute("data-destination")).toBe("PAY-118"));
    expect(screen.getByTestId("send-well")).toBe(well);
  });

  it("the pick from the menu resolves the window's document and focuses the window; nothing is sent", async () => {
    await readDestinations();
    const focus = vi.spyOn(useDesk.getState(), "focusPanel").mockImplementation(() => {});
    pickFor("pullout:decision:dec-9", "chd_f");
    await waitFor(() => expect(pickedDestination("desk_decision:dec-9")).toBe("chd_f"));
    expect(focus).toHaveBeenCalledWith("pullout:decision:dec-9");
    expect(apiFetch.mock.calls.some(([p, i]) => String(p).startsWith("/api/channels/send") && (i as RequestInit)?.method === "POST")).toBe(false);
    focus.mockRestore();
  });

  it("Summary -> Digest keeps the picked destination and opens the digest's preview", async () => {
    const previews: string[] = [];
    routes["POST /api/channels/preview"] = (init) => { previews.push(String(init.json?.document_ref)); return { payload_digest: "d", preview: { text: "# x" } }; };
    render(<MeetingSendWell meetingId="m7" title="Vendor sync" />);
    await screen.findAllByTestId("destination-row");
    act(() => pickDestination("meeting_summary:m7", "chd_f"));
    await screen.findByTestId("send-open");
    const select = within(screen.getByTestId("doc-forms")).getByRole("combobox");
    fireEvent.change(select, { target: { value: "meeting_digest" } });
    await waitFor(() => expect(screen.getByTestId("send-well").getAttribute("data-doc")).toBe("meeting_digest:m7"));
    expect(pickedDestination("meeting_digest:m7")).toBe("chd_f");
    await waitFor(() => expect(previews).toContain("meeting_digest:m7"));
  });
});

describe("the SENDING / PREPARED chip (canvas P7)", () => {
  it("draws its word on --accent-text (4.26:1 on --accent was under the 4.5:1 floor)", () => {
    const css = readFileSync(resolvePath(__dirname, "../surface/patterns/state-chip.css"), "utf8");
    const rule = /\.surface-state-chip\[data-state="active"\]\s*\{([^}]*)\}/.exec(css)?.[1] ?? "";
    expect(rule).toContain("var(--accent-text)");
  });
});

import { ArtifactPullout } from "../pullouts/ArtifactPullout";
import type { WorldObject } from "../world";

describe("the artifact window (canvas P5)", () => {
  const art = {
    kind: "artifact", id: "art-1", title: "Cutover requirements",
    ref: { kind: "artifact", id: "art-1", title: "Cutover requirements", artifactType: "requirements_doc", bodyMarkdown: "# Cutover", sources: [] },
  } as unknown as WorldObject;

  it("its own SEND well on artifact:<id>; a pick opens its preview in place", async () => {
    render(<ArtifactPullout object={art} onClose={() => {}} />);
    const well = await screen.findByTestId("send-well");
    expect(well.getAttribute("data-doc")).toBe("artifact:art-1");
    await screen.findAllByTestId("destination-row");
    act(() => pickDestination("artifact:art-1", "chd_f"));
    expect((await screen.findByTestId("send-open")).getAttribute("data-destination")).toBe("Team updates");
  });

  it("Copy and Dictate about this are library Buttons", () => {
    render(<ArtifactPullout object={art} onClose={() => {}} />);
    for (const name of ["Copy", "Dictate about this"]) {
      const b = screen.getByText(name).closest("button")!;
      expect(b.className).not.toContain("desk-chip");
    }
    const src = readFileSync(resolvePath(__dirname, "../pullouts/ArtifactPullout.tsx"), "utf8");
    expect(src).not.toMatch(/<button\b/);
  });
});
