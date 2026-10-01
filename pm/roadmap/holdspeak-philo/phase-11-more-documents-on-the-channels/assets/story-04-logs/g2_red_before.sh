#!/bin/bash
# Red-before for G2: the G2 case against the BASELINE SendWell and channels.ts, pinned to the
# story's base commit 3552be416 (story 01 head; Astra built-check r1 F2: HEAD no longer selects it).
set -u
BASE=3552be416c9d5d968adc162941f1f81a3c7c0b44
cd /Users/karol/dev/tools/wt-philo-11-04
D=web/src/features/g2redbefore
rm -rf "$D"; mkdir -p "$D/__tests__"
git show "$BASE":web/src/features/channels/SendWell.tsx > "$D/SendWell.tsx"
git show "$BASE":web/src/features/channels/channels.ts > "$D/channels.ts"
git show "$BASE":web/src/features/channels/channels.css > "$D/channels.css"
cat > "$D/__tests__/g2.test.tsx" <<'T'
import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, it, vi } from "vitest";
const apiFetch = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../../pages/cores/connections/api", async () => {
  const actual = await vi.importActual<typeof import("../../../pages/cores/connections/api")>("../../../pages/cores/connections/api");
  return { ...actual, fetchConnections: () => Promise.resolve({ tools: [] }) };
});
import { ApiError } from "../../../lib/api";
import { SendWell, useSends } from "../SendWell";
it("G2 on the baseline 3552be416: a preview refused by name shows its word and the size, never NO ANSWER", async () => {
  apiFetch.mockImplementation((path: string, init: { method?: string } = {}) => {
    const key = `${init.method ?? "GET"} ${path.split("?")[0]}`;
    if (key === "GET /api/channels/destinations") return Promise.resolve({ destinations: [{ id: "chd_1", name: "Folder Payments",
      channel: "file", account: {}, target: { folder: "/tmp/x" }, synced: false, state: "active", created_at: "", parked_at: null }] });
    if (key === "GET /api/channels/sends") return Promise.resolve({ sends: [] });
    if (key === "POST /api/channels/preview") return Promise.reject(new ApiError(400, "too large", {
      success: false, code: "payload_too_large:slack", error_code: "payload_too_large:slack", size: 41099, limit: 39000 }));
    return Promise.reject(new Error(key));
  });
  const u = { id: "u1", draftRevision: 3, deliveries: [] } as never;
  function Well() { const read = useSends("u1"); return <SendWell update={u} sendsRead={read} />; }
  render(<Well />);
  fireEvent.click(within(await screen.findByTestId("destination-row")).getByText("Folder Payments"));
  await new Promise((r) => setTimeout(r, 50));
  const open = screen.getByTestId("send-open");
  expect(open.textContent).toContain("TOO LARGE FOR SLACK");
  expect(open.textContent).toContain("41,099 / 39,000 CHARACTERS");
  expect(open.textContent).not.toContain("NO ANSWER");
});
T
cd web && npx vitest run src/features/g2redbefore 2>&1 | grep -v "^$" | tail -25
rc=${PIPESTATUS[0]}
cd .. && rm -rf "$D"
exit $rc
