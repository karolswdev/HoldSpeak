/* PHILO-13-06 (B1), Astra's pass: every explicit Prep open lands on Prep.
 *
 * Red on 10af6575: open Priya on Prep, choose Now, open the same 1:1 again —
 * the scope string is unchanged (`people:r1:prep`), so the lens effect never
 * re-ran and People stayed on Now (PeopleCore.tsx:310).
 *
 * PHILO-17 (2b): the open lands in the person's own window
 * (PersonWindowBody); the fence follows it there.
 */
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PersonWindowBody } from "../PeopleCore";
import { openPerson } from "../../../desk/openObject";
import { personWindowRef } from "../../../desk/objectWindows";

vi.mock("../../../desk/shell", async (original) => ({
  ...(await original<typeof import("../../../desk/shell")>()),
  openPrimitive: vi.fn(),
}));

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

afterEach(() => vi.unstubAllGlobals());

const selectedLens = () => screen.getAllByRole("tab").find((t) => t.getAttribute("aria-selected") === "true")?.textContent;

// The full desk suite runs in parallel; a slow render under that load must not
// read as a failure, so the waits take 5 s, not the 1 s default (#1100).
describe("PHILO-13-06: a repeat Prep open re-applies Prep", () => {
  it("Prep → Now → the same open again lands on Prep", async () => {
    const handlers: Record<string, () => Response> = {
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted", sync: "local_only", capture: "notes_only" }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Priya Nair", relationship_kind: "peer" }] }),
      "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Priya Nair", relationship_kind: "peer", calendar_links: [] } }),
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
    };
    vi.stubGlobal("fetch", vi.fn(async (input: string) => (handlers[String(input)] ?? (() => json({})))()));

    // The 1:1 row's open: THAT person, on Prep.
    personWindowRef("people:r1:prep");
    render(<PersonWindowBody relationshipId="r1" />);
    await waitFor(() => expect(selectedLens()).toBe("Prep"), { timeout: 5000 });

    fireEvent.click(screen.getByRole("tab", { name: "Now" }));
    expect(selectedLens()).toBe("Now");

    // The 1:1 row again: the same scope, an explicit Prep open.
    await act(async () => { openPerson("r1", "prep"); });
    await waitFor(() => expect(selectedLens()).toBe("Prep"), { timeout: 5000 });
  });
});
