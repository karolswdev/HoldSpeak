import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ConstitutionalContextCore } from "../ConstitutionalContextCore";
import type { ContextState, HistoryEntry } from "../core-types";

const RAW = "'Database' object has no attribute '_conn'";

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

// Software fixtures of the existing Context wire contract. These unit cases
// prove rendered state; they do not prove the real hub or browser geometry.
function contextReplies(context: ContextState, revisions: HistoryEntry[] = [], savedContext = context) {
  const fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    if (init?.method === "PUT") return json({ context: savedContext });
    if (String(input).endsWith("/history")) return json({ revisions });
    return json({ context });
  });
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

afterEach(() => vi.unstubAllGlobals());

describe("Context save failure", () => {
  it("reads as plain words and never prints the server exception", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (init?.method === "PUT") return json({ error: RAW }, 500);
        if (url.endsWith("/history")) return json({ revisions: [] });
        return json({
          context: { content: "", revision: 0, content_hash: "", char_limit: 32768 },
        });
      }),
    );
    const { container } = render(<ConstitutionalContextCore />);
    const pad = await screen.findByRole("textbox", {
      name: "Constitutional context",
    });
    expect(screen.queryByText("Revision 0")).toBeNull();
    expect(screen.queryByText("About 0 tokens")).toBeNull();
    expect(screen.queryByText("0 of 32,768 characters")).toBeNull();
    fireEvent.change(pad, { target: { value: "I lead three engineers." } });
    expect(screen.getByText("About 6 tokens")).toBeTruthy();
    expect(screen.getByText("23 of 32,768 characters")).toBeTruthy();
    expect(screen.getByText("Not saved yet")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(screen.getByText("Not saved")).toBeTruthy());
    expect(container.textContent).not.toContain("_conn");
    expect(container.textContent).not.toContain("object has no attribute");
    // The text stays in the pad, so a second Save can try again.
    expect((pad as HTMLTextAreaElement).value).toBe("I lead three engineers.");
    expect(screen.getByRole("button", { name: "Save" })).not.toBeDisabled();

    // Clearing the draft keeps its real unsaved state without empty meters.
    fireEvent.change(pad, { target: { value: "" } });
    expect(screen.queryByText(/^About \d+ tokens$/)).toBeNull();
    expect(screen.queryByText(/characters$/)).toBeNull();
    expect(screen.getByText("Not saved yet")).toBeTruthy();
    expect(screen.queryByText("Not saved")).toBeNull();
  });
});

describe("Context status", () => {
  const current: ContextState = {
    content: "Senior architect", revision: 4, content_hash: "", char_limit: 32768,
  };

  it("keeps the empty editor mounted when the response has no Context payload", async () => {
    // Same missing-payload software fixture as scrollOwnership.test.tsx.
    vi.stubGlobal("fetch", vi.fn(async () => json({})));
    render(<ConstitutionalContextCore />);
    const pad = await screen.findByRole("textbox", { name: "Constitutional context" });
    expect(pad).toHaveValue("");
    expect(screen.queryByText(/^Revision /)).toBeNull();
    expect(screen.queryByText(/tokens$/)).toBeNull();
    expect(screen.queryByText(/characters$/)).toBeNull();
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });

  it("keeps a real revision and saved outcome when the draft is cleared", async () => {
    const fetch = contextReplies(current, [], { ...current, content: "", revision: 5 });
    render(<ConstitutionalContextCore />);
    const pad = await screen.findByRole("textbox", { name: "Constitutional context" });
    expect(screen.getByText("Revision 4")).toBeTruthy();
    expect(screen.getByText("About 4 tokens")).toBeTruthy();
    expect(screen.getByText("16 of 32,768 characters")).toBeTruthy();

    fireEvent.change(pad, { target: { value: "" } });
    expect(screen.getByText("Revision 4")).toBeTruthy();
    expect(screen.queryByText(/tokens$/)).toBeNull();
    expect(screen.queryByText(/characters$/)).toBeNull();
    expect(screen.getByText("Not saved yet")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await screen.findByText(/^Saved \d\d:\d\d$/);
    expect(screen.getByText("Revision 5")).toBeTruthy();
    expect(screen.queryByText("Not saved yet")).toBeNull();
    expect(screen.queryByText(/tokens$/)).toBeNull();
    expect(screen.queryByText(/characters$/)).toBeNull();
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
    const put = fetch.mock.calls.find(([, init]) => init?.method === "PUT");
    expect(JSON.parse(String(put?.[1]?.body))).toEqual({ content: "" });
  });

  it("keeps History selection and Cancel for nonempty and empty revisions", async () => {
    contextReplies(current, [
      { content: "Prior role", revision: 3, content_hash: "", created_at: "2026-10-15T09:00:00Z" },
      { content: "", revision: 2, content_hash: "", created_at: "2026-10-14T09:00:00Z" },
    ]);
    render(<ConstitutionalContextCore />);
    const history = await screen.findByRole("combobox", { name: "Version history" });
    const pad = screen.getByRole("textbox", { name: "Constitutional context" });

    fireEvent.change(history, { target: { value: "3" } });
    expect(pad).toHaveValue("Prior role");
    expect(screen.getByText("Viewing revision 3")).toBeTruthy();
    expect(screen.getByText("About 3 tokens")).toBeTruthy();
    expect(screen.getByText("10 of 32,768 characters")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Restore" })).not.toBeDisabled();

    fireEvent.change(history, { target: { value: "2" } });
    expect(pad).toHaveValue("");
    expect(screen.getByText("Viewing revision 2")).toBeTruthy();
    expect(screen.getByText("Not saved yet")).toBeTruthy();
    expect(screen.getByText("Revision 4")).toBeTruthy();
    expect(screen.queryByText(/tokens$/)).toBeNull();
    expect(screen.queryByText(/characters$/)).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    await waitFor(() => expect(pad).toHaveValue("Senior architect"));
    expect(history).toHaveValue("current");
    expect(screen.queryByText(/^Viewing revision/)).toBeNull();
    expect(screen.queryByText("Not saved yet")).toBeNull();
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });
});
