// HS-132-11 — the answer reaches the waiting agent, and the desk says so.
// The Send reply verb posts to the real reply route; a send leaves an in-flow
// receipt naming the pane, a refusal names why in-flow and delivers nothing.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CadenceCore } from "../CadenceCore";

const LOOP = {
  id: "loop-1",
  title: "SQLite or config?",
  source_type: "agent_question",
  status: "open",
  stale_score: 90,
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

/** The three reads CadenceCore opens with, plus one scripted reply answer. */
function stubDesk(reply: () => Response) {
  const posts: { url: string; body: unknown }[] = [];
  const fetcher = vi.fn(async (input: string, init?: RequestInit) => {
    const url = String(input);
    if (init?.method === "POST") {
      posts.push({ url, body: JSON.parse(String(init.body ?? "{}")) });
      return reply();
    }
    if (url.startsWith("/api/cadence/status")) return json({ enabled: true });
    if (url.startsWith("/api/cadence/loops")) return json({ loops: [LOOP] });
    if (url.startsWith("/api/cadence/history")) return json({ nudges: [] });
    throw new Error(`Unexpected request: ${url}`);
  });
  vi.stubGlobal("fetch", fetcher);
  return posts;
}

async function typeReply(text: string) {
  const pad = await screen.findByLabelText("Reply to SQLite or config?");
  fireEvent.change(pad, { target: { value: text } });
  return pad;
}

afterEach(() => vi.unstubAllGlobals());

describe("CadenceCore reply", () => {
  it("posts the typed answer and receipts the pane it landed in", async () => {
    const posts = stubDesk(() =>
      json({ delivered: true, pane: "editor:0.1", operation_id: "op_1" }),
    );
    render(<CadenceCore />);

    const pad = await typeReply("Use SQLite; add a migration.");
    fireEvent.click(screen.getByRole("button", { name: "Send reply" }));

    await waitFor(() => expect(posts.length).toBe(1));
    expect(posts[0].url).toBe("/api/cadence/loops/loop-1/reply");
    expect(posts[0].body).toEqual({ text: "Use SQLite; add a migration." });
    expect(await screen.findByText(/Sent to editor:0\.1/)).toBeTruthy();
    // The answered question is done being typed at.
    await waitFor(() => expect((pad as HTMLTextAreaElement).value).toBe(""));
  });

  it("names the refusal in flow and keeps the answer on the pad", async () => {
    stubDesk(() =>
      json({ detail: "no terminal pane for this agent session" }, 409),
    );
    const { container } = render(<CadenceCore />);

    const pad = await typeReply("Use SQLite.");
    fireEvent.click(screen.getByRole("button", { name: "Send reply" }));

    expect(
      await screen.findByText("no terminal pane for this agent session"),
    ).toBeTruthy();
    expect(container.querySelector(".surface-receipt-line")).toBeNull();
    expect((pad as HTMLTextAreaElement).value).toBe("Use SQLite.");
  });
});
