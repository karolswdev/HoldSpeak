/** PHILO-8-01 half B — a refused zone rename is never silent (the owner's
 * ratified canvas, 2026-09-26; the Astra-role check r1 ruling on question 6).
 * While the zone's field is open the refusal is its chip (`NAME TAKEN` /
 * `NOT SAVED`); after the field closed it is the write receipt `RENAME ZONE`
 * with Retry. The optimistic name is reverted on every refusal. */
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiRequest } from "../../../lib/api";

vi.mock("../../../lib/api", () => ({
  apiRequest: vi.fn(),
  apiFetch: vi.fn(() => Promise.resolve({})),
  newDeliveryId: vi.fn(() => "d"),
}));

import { useDesk } from "../../store";
import { clearWriteFailure, currentWriteFailure } from "../../hooks/useWriteReceipt";

const zone = { kind: "directory", id: "dir_a", name: "New zone", nameNormalized: "new zone", memberIds: [], createdAt: "" };
const reply = (status: number, body: unknown) =>
  Promise.resolve({ ok: status < 300, status, json: () => Promise.resolve(body) } as Response);
const nameNow = () => useDesk.getState().items.directory.find((d) => d.id === "dir_a")?.name;

describe("renameZone — the chip while the field is open", () => {
  beforeEach(() => {
    vi.mocked(apiRequest).mockReset();
    clearWriteFailure();
    useDesk.setState({
      renamingZoneId: "dir_a",
      zoneRenameError: null,
      items: { ...useDesk.getState().items, directory: [zone] as never },
    });
  });

  it("409 → NAME TAKEN on the chip, the name reverted", async () => {
    vi.mocked(apiRequest).mockImplementation(() => reply(409, { error: "zone_name_taken", existing_name: "Inbox" }));
    await useDesk.getState().renameZone("dir_a", "Inbox");
    expect(useDesk.getState().zoneRenameError).toMatchObject({ zoneId: "dir_a", name: "Inbox", code: "zone_name_taken", label: "NAME TAKEN" });
    expect(nameNow()).toBe("New zone");
    expect(currentWriteFailure()).toBeNull();
  });

  it("422 → NOT SAVED with the hub's reason in detail", async () => {
    vi.mocked(apiRequest).mockImplementation(() => reply(422, { error: "zone name must be 64 characters or fewer" }));
    await useDesk.getState().renameZone("dir_a", "x".repeat(65));
    expect(useDesk.getState().zoneRenameError).toMatchObject({ code: "invalid_arguments", label: "NOT SAVED", detail: "zone name must be 64 characters or fewer" });
    expect(nameNow()).toBe("New zone");
  });

  it("a network failure → NOT SAVED", async () => {
    vi.mocked(apiRequest).mockImplementation(() => Promise.reject(new TypeError("Failed to fetch")));
    await useDesk.getState().renameZone("dir_a", "Offline");
    expect(useDesk.getState().zoneRenameError).toMatchObject({ code: "not_saved", label: "NOT SAVED", detail: "HUB UNREACHABLE" });
    expect(nameNow()).toBe("New zone");
  });

  it("a 500 is not left as the optimistic name (was: kept silently)", async () => {
    vi.mocked(apiRequest).mockImplementation(() => reply(500, { error: "boom" }));
    await useDesk.getState().renameZone("dir_a", "Boom");
    expect(useDesk.getState().zoneRenameError).toMatchObject({ code: "http_500", label: "NOT SAVED" });
    expect(nameNow()).toBe("New zone");
  });

  it("200 → no error, the name kept", async () => {
    vi.mocked(apiRequest).mockImplementation(() => reply(200, { directory: { id: "dir_a" } }));
    await useDesk.getState().renameZone("dir_a", "Platform team");
    expect(useDesk.getState().zoneRenameError).toBeNull();
    expect(nameNow()).toBe("Platform team");
  });
});

describe("renameZone — the write receipt after the field closed", () => {
  beforeEach(() => {
    vi.mocked(apiRequest).mockReset();
    clearWriteFailure();
    useDesk.setState({
      renamingZoneId: null,
      zoneRenameError: null,
      items: { ...useDesk.getState().items, directory: [zone] as never },
    });
  });

  it("a refusal that lands with no field open → RENAME ZONE with Retry, which sends the name again", async () => {
    vi.mocked(apiRequest).mockImplementation(() => reply(409, { error: "zone_name_taken", existing_name: "Inbox" }));
    await useDesk.getState().renameZone("dir_a", "Inbox");
    const failure = currentWriteFailure();
    expect(failure).toMatchObject({ verb: "RENAME ZONE", reason: "NAME TAKEN" });
    expect(useDesk.getState().zoneRenameError).toBeNull();
    expect(nameNow()).toBe("New zone");
    vi.mocked(apiRequest).mockClear();
    vi.mocked(apiRequest).mockImplementation(() => reply(200, {}));
    failure!.retry!();
    await vi.waitFor(() => expect(apiRequest).toHaveBeenCalledTimes(1));
    expect(JSON.parse(String(vi.mocked(apiRequest).mock.calls[0][1]!.body))).toEqual({ name: "Inbox" });
  });
});
