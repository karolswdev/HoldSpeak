/** Regression: this fails on main's createWalk-backed Show me. */
import { expect, it, vi } from "vitest";
const api = vi.hoisted(() => vi.fn());
vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: api,
}));
import { startAppWalk } from "../appWalks";
it("starting a bundled app guide makes no walk request", async () => {
  api.mockResolvedValue({ id: "old-record", token: "x".repeat(43) });
  expect(await startAppWalk("surface-decisions", "surface-decisions")).toBe(
    true,
  );
  expect(api).not.toHaveBeenCalled();
});
