import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { RecallFace, MemorySnippet } from "../RecallFace";
import TAPE from "../../__tests__/room-wires/recall10.json";
const io = vi.hoisted(() => ({ api: vi.fn() }));
vi.mock("../../../../lib/api", async original => ({ ...await original<typeof import("../../../../lib/api")>(), apiFetch: (...args: unknown[]) => io.api(...args) }));
beforeEach(() => { io.api.mockReset(); localStorage.clear(); io.api.mockResolvedValue(TAPE.recall); });
describe("Recall selection seats", () => {
  it("keeps current and superseded decisions distinct in the same list", async () => {
    render(<RecallFace />);
    expect(await screen.findByRole("row", { name: new RegExp(TAPE.recall.current[0].text) })).toHaveTextContent("current");
    expect(screen.getByRole("row", { name: new RegExp(TAPE.recall.superseded[0].text) })).toHaveTextContent("superseded");
    expect(screen.getByRole("button", { name: "Carry into brief" })).toBeDisabled();
  });
  it("selects before Carry and exposes source, successor and project as selection verbs", async () => {
    render(<RecallFace />); fireEvent.click(await screen.findByRole("row", { name: new RegExp(TAPE.recall.current[0].text) }));
    expect(screen.getByRole("button", { name: "Carry into brief" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Open source" })).toBeEnabled();
    fireEvent.click(screen.getByRole("row", { name: new RegExp(TAPE.recall.superseded[0].text) }));
    expect(screen.getByRole("button", { name: "Carry into brief" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Open successor" })).toBeDisabled();
    expect(document.querySelector(".object-list-row button,.object-list-row a,.recall-card,summary")).toBeNull();
  });
  it("searches from the field and keeps the last rows when reread fails", async () => {
    render(<RecallFace />); await screen.findByRole("row", { name: new RegExp(TAPE.recall.current[0].text) });
    const query = screen.getByRole("textbox", { name: "Search memory" }); fireEvent.change(query, { target: { value: "cut-over" } });
    io.api.mockRejectedValueOnce(new Error("Injected search failure")); fireEvent.keyDown(query, { key: "Enter" });
    await screen.findByText("Injected search failure"); expect(query).toHaveValue("cut-over");
    expect(screen.getByRole("row", { name: new RegExp(TAPE.recall.current[0].text) })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try again" })).toBeEnabled();
  });
  it("renders only the trusted FTS mark grammar as markup", () => {
    const view = render(<MemorySnippet value={'before <mark>match</mark> <script>bad</script>'} />);
    expect(view.container.querySelector("mark")).toHaveTextContent("match"); expect(view.container.querySelector("script")).toBeNull();
    expect(view.container).toHaveTextContent("<script>bad</script>");
  });
});
