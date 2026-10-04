import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ConstitutionalContextCore } from "../ConstitutionalContextCore";

const RAW = "'Database' object has no attribute '_conn'";

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
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
    fireEvent.change(pad, { target: { value: "I lead three engineers." } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(screen.getByText("Not saved")).toBeTruthy());
    expect(container.textContent).not.toContain("_conn");
    expect(container.textContent).not.toContain("object has no attribute");
    // The text stays in the pad, so a second Save can try again.
    expect((pad as HTMLTextAreaElement).value).toBe("I lead three engineers.");
    expect(screen.getByRole("button", { name: "Save" })).not.toBeDisabled();
  });
});
