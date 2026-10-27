import { act, fireEvent, render, renderHook, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DesignReference } from "../../../pages/cores/design-reference/DesignReference";
import { RepositoryBrowserView } from "../RepositoryBrowserView";
import { useRepositoryBrowser, type RepositoryReadAdapter } from "../RepositoryBrowserController";
import type { RepoFile } from "../../repository";
import { ApiError } from "../../../lib/api";

const rootFiles: RepoFile[] = [
  { name: "src", path: "src", type: "dir" },
  { name: "README.md", path: "README.md", type: "file" },
  { name: "CHANGELOG.md", path: "CHANGELOG.md", type: "file" },
];
const sourceFiles: RepoFile[] = [{ name: "index.ts", path: "src/index.ts", type: "file" }];
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

describe("repository read browser", () => {
  it("keeps the prior location and material after a refused directory, then retries the captured path", async () => {
    const second = deferred<RepoFile[]>();
    const tree = vi.fn((path: string) => path === "src" ? second.promise : Promise.resolve(rootFiles));
    const adapter: RepositoryReadAdapter = { tree, file: vi.fn() };
    const { result } = renderHook(() => useRepositoryBrowser(adapter));
    await waitFor(() => expect(result.current.entry.files).toEqual(rootFiles));
    act(() => result.current.navigate("src"));
    await act(async () => second.reject(new Error("refused")));
    expect(result.current.entry.path).toBe("");
    expect(result.current.entry.files).toEqual(rootFiles);
    expect(result.current.failure).toMatchObject({ kind: "tree", path: "src" });
    expect(result.current.canBack).toBe(true);
    act(() => result.current.back());
    expect(result.current.failure).toBeNull();
    expect(result.current.entry.path).toBe("");
    act(() => result.current.navigate("src"));
    await waitFor(() => expect(result.current.failure?.path).toBe("src"));
    act(() => result.current.retry());
    expect(tree).toHaveBeenLastCalledWith("src");
  });

  it("names a missing initial path and keeps root as a recovery route", async () => {
    const adapter: RepositoryReadAdapter = {
      tree: (path) => path === "gone" ? Promise.reject(new ApiError(404, "missing", {})) : Promise.resolve(rootFiles),
      file: vi.fn(),
    };
    const { result } = renderHook(() => useRepositoryBrowser(adapter, "gone"));
    await waitFor(() => expect(result.current.failure?.message).toBe("NOT FOUND · gone"));
    expect(result.current.entry.path).toBe("gone");
    act(() => result.current.navigate(""));
    await waitFor(() => expect(result.current.entry.path).toBe(""));
    expect(result.current.entry.files).toEqual(rootFiles);
    act(() => result.current.back());
    await waitFor(() => expect(result.current.failure?.message).toBe("NOT FOUND · gone"));
  });

  it("rejects late success and late refusal after a newer location, and Back/Forward restore each entry", async () => {
    const stale = deferred<RepoFile[]>();
    const staleError = deferred<RepoFile[]>();
    const tree = vi.fn((path: string) => path === "old" ? stale.promise : path === "bad" ? staleError.promise : Promise.resolve(path === "src" ? sourceFiles : rootFiles));
    const { result } = renderHook(() => useRepositoryBrowser({ tree, file: vi.fn() }));
    await waitFor(() => expect(result.current.entry.files).toEqual(rootFiles));
    act(() => { result.current.navigate("old"); result.current.navigate("src"); });
    await waitFor(() => expect(result.current.entry.path).toBe("src"));
    await act(async () => stale.resolve([{ name: "wrong", path: "wrong", type: "file" }]));
    expect(result.current.entry.files).toEqual(sourceFiles);
    act(() => { result.current.navigate("bad"); result.current.navigate(""); });
    await waitFor(() => expect(result.current.entry.path).toBe(""));
    await act(async () => staleError.reject(new Error("late")));
    expect(result.current.failure).toBeNull();
    act(() => result.current.back());
    expect(result.current.entry.path).toBe("src");
    act(() => result.current.forward());
    expect(result.current.entry.path).toBe("");
  });

  it("shows exact captured file content and keeps it through a later failed read", async () => {
    const delayed = deferred<string>();
    const file = vi.fn((path: string) => path === "README.md" ? Promise.resolve("# exact source\n") : delayed.promise);
    const adapter: RepositoryReadAdapter = { tree: () => Promise.resolve(rootFiles), file };
    function Browser() {
      const browser = useRepositoryBrowser(adapter);
      return <RepositoryBrowserView browser={browser} />;
    }
    render(<Browser />);
    await screen.findByRole("row", { name: "README.md" });
    fireEvent.click(screen.getByRole("row", { name: "README.md" }));
    await waitFor(() => expect(screen.getByTestId("repo-file-content").textContent).toBe("# exact source\n"));
    fireEvent.click(screen.getByRole("row", { name: "CHANGELOG.md" }));
    await act(async () => delayed.reject(new Error("refused")));
    expect(screen.getByText("READ REFUSED · CHANGELOG.md")).toBeTruthy();
    expect(screen.getByTestId("repo-file-content").textContent).toBe("# exact source\n");
    expect(screen.getByText("README.md · RETAINED COPY")).toBeTruthy();
    expect(file).toHaveBeenLastCalledWith("CHANGELOG.md");
  });

  it("refresh marks old content retained, then reads the changed file from the refreshed tree", async () => {
    const nextTree = deferred<RepoFile[]>();
    const nextFile = deferred<string>();
    let treeCalls = 0;
    let fileCalls = 0;
    const adapter: RepositoryReadAdapter = {
      tree: () => ++treeCalls === 1 ? Promise.resolve(rootFiles) : nextTree.promise,
      file: () => ++fileCalls === 1 ? Promise.resolve("old branch") : nextFile.promise,
    };
    const { result } = renderHook(() => useRepositoryBrowser(adapter));
    await waitFor(() => expect(result.current.entry.files).toEqual(rootFiles));
    act(() => result.current.inspect("README.md"));
    await waitFor(() => expect(result.current.entry.inspection?.content).toBe("old branch"));
    act(() => result.current.refresh());
    expect(result.current.entry.inspection).toMatchObject({ content: "old branch", retained: true });
    await act(async () => nextTree.resolve(rootFiles));
    expect(result.current.entry.inspection?.retained).toBe(true);
    await act(async () => nextFile.resolve("new branch"));
    expect(result.current.entry.inspection).toEqual({ path: "README.md", content: "new branch", retained: false });
  });

  it("refresh keeps a removed file as a labelled retained copy with a missing outcome", async () => {
    let treeCalls = 0;
    const adapter: RepositoryReadAdapter = {
      tree: () => Promise.resolve(++treeCalls === 1 ? rootFiles : rootFiles.filter((file) => file.path !== "README.md")),
      file: () => Promise.resolve("former content"),
    };
    const { result } = renderHook(() => useRepositoryBrowser(adapter));
    await waitFor(() => expect(result.current.entry.files).toEqual(rootFiles));
    act(() => result.current.inspect("README.md"));
    await waitFor(() => expect(result.current.entry.inspection?.content).toBe("former content"));
    act(() => result.current.refresh());
    await waitFor(() => expect(result.current.failure?.message).toBe("NOT FOUND · README.md"));
    expect(result.current.entry.inspection).toMatchObject({ content: "former content", retained: true });
  });

  it("a late file success cannot replace a newer selection or reopen closed inspection", async () => {
    const late = deferred<string>();
    const afterClose = deferred<string>();
    const file = vi.fn((path: string) => path === "README.md" ? late.promise : afterClose.promise);
    const { result } = renderHook(() => useRepositoryBrowser({ tree: () => Promise.resolve(rootFiles), file }));
    await waitFor(() => expect(result.current.entry.files).toEqual(rootFiles));
    act(() => { result.current.inspect("README.md"); result.current.inspect("CHANGELOG.md"); });
    await act(async () => late.resolve("old material"));
    expect(result.current.entry.inspection).toBeNull();
    await act(async () => afterClose.resolve("new material"));
    expect(result.current.entry.inspection).toEqual({ path: "CHANGELOG.md", content: "new material", retained: false });

    const next = deferred<string>();
    file.mockImplementation(() => next.promise);
    act(() => { result.current.inspect("README.md"); result.current.closeInspection(); });
    await act(async () => next.resolve("after close"));
    expect(result.current.entry.inspection).toBeNull();
  });

  it("Components uses the production browser for populated, refused, and resumed specimens", async () => {
    render(<DesignReference />);
    fireEvent.click(within(screen.getByRole("navigation", { name: "Patterns" })).getByRole("button", { name: "Resources" }));
    await screen.findByRole("row", { name: "README.md" });
    fireEvent.change(screen.getByRole("combobox", { name: "Example state" }), { target: { value: "failed" } });
    await screen.findByText("READ REFUSED · src");
    expect(screen.getByRole("row", { name: "README.md" })).toBeTruthy();
    fireEvent.change(screen.getByRole("combobox", { name: "Example state" }), { target: { value: "resumed" } });
    await waitFor(() => expect(screen.getByTestId("repo-file-content").textContent).toBe("# HoldSpeak\n\nA registered repository.\nRead this file in the current view.\n"));
  });
});
