import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PeopleCore } from "../PeopleCore";

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

function stub(handlers: Record<string, () => Response | Promise<Response>>) {
  vi.stubGlobal("fetch", vi.fn(async (input: string) => {
    const handler = handlers[String(input)];
    if (!handler) throw new Error(`Unexpected request: ${String(input)}`);
    return handler();
  }));
}

afterEach(() => vi.unstubAllGlobals());

describe("PeopleCore encrypted local plane", () => {
  it("names an unconfigured store without rendering a roster", async () => {
    stub({ "/api/people/readiness": () => json({ readiness: "unconfigured" }) });
    render(<PeopleCore />);
    expect(await screen.findByText("Not set up")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Set up" })).toBeTruthy();
    expect(screen.queryByLabelText("New relationship")).toBeNull();
  });

  it("clears roster data when a relationship read becomes locked", async () => {
    stub({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted", sync: "local_only", capture: "notes_only" }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Avery", relationship_kind: "direct_report" }] }),
      "/api/people/relationships/r1": () => json({ detail: "key locked" }, 423),
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
    });
    render(<PeopleCore />);
    fireEvent.click(await screen.findByRole("button", { name: /Avery/ }));
    expect(await screen.findByText("Locked")).toBeTruthy();
    expect(screen.queryByText("Avery")).toBeNull();
    expect(screen.queryByLabelText("New relationship")).toBeNull();
  });

  it("renders local trust facts and a manual relationship", async () => {
    stub({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted", sync: "local_only", capture: "notes_only" }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Avery", relationship_kind: "direct_report", manager_commitment_count: 1 }] }),
      "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Avery", relationship_kind: "peer", commitments: [], notes: [{ id: "n1", topic: "Collaboration", body: "Prefers written context", visibility: "shared_intent" }] } }),
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
    });
    render(<PeopleCore scope="people:r1" />);
    await screen.findByText("This device only");
    expect(screen.getByText("Encrypted")).toBeTruthy();
    expect(screen.getByText("Notes only")).toBeTruthy();
    await waitFor(() => expect(screen.getByRole("tab", { name: "1:1s" })).toBeTruthy());
    fireEvent.click(screen.getByRole("tab", { name: "Context" }));
    expect(screen.getByText("Prefers written context")).toBeTruthy();
    expect(screen.getByLabelText("Grounding note")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /^Speak / })).toBeNull();
  });
});
