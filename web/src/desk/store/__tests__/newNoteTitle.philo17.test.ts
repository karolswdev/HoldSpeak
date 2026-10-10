/** PHILO-17 objverbs — Desk ▸ New Note posts no title.
 *
 * The walk: New Note pre-filled the title "New note" with the caret at the
 * end, so typing gave "New noteAsk…". The note now starts with no title; the
 * editor's title field shows the placeholder, and the placeholder is never
 * kept as the note's name.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiRequest } from "../../../lib/api";

vi.mock("../../../lib/api", () => ({
  apiRequest: vi.fn(),
  apiFetch: vi.fn(() => Promise.resolve({})),
  newDeliveryId: vi.fn(() => "d"),
}));

import { useDesk } from "../../store";
import { primitiveName } from "../../windowName";

describe("createPrimitive('note') — no placeholder title", () => {
  beforeEach(() => {
    vi.mocked(apiRequest).mockReset();
    useDesk.setState({ refresh: vi.fn(() => Promise.resolve()), editingId: null });
  });

  it("posts an empty title and opens the editor", async () => {
    vi.mocked(apiRequest).mockImplementation(() =>
      Promise.resolve({
        ok: true,
        status: 201,
        json: () => Promise.resolve({ note: { id: "note_new", title: "", body_markdown: "", tags: [] } }),
      } as Response),
    );
    await useDesk.getState().createPrimitive("note");
    const posts = vi
      .mocked(apiRequest)
      .mock.calls.filter(([url, init]) => url === "/api/notes" && init?.method === "POST")
      .map(([, init]) => JSON.parse(String(init!.body)));
    expect(posts).toEqual([{ title: "", body_markdown: "" }]);
    expect(useDesk.getState().editingId).toBe("note_new");
  });

  it("an untitled note is still named on the desk (shown, not kept)", () => {
    expect(primitiveName("note", { title: "", bodyMarkdown: "" }, "note_new")).toBe("New note");
    expect(primitiveName("note", { title: "", bodyMarkdown: "Ask Avery about the cutover" }, "note_new")).toBe(
      "Ask Avery about the cutover",
    );
  });
});
