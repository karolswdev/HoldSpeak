import { act, fireEvent, render, renderHook, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LedgerFilterBar, useLedgerFilter } from "../LedgerFilter";

afterEach(() => {
  localStorage.clear();
});

describe("useLedgerFilter", () => {
  const items = [
    { name: "alpha" },
    { name: "beta" },
    { name: "gamma" },
  ];
  const match = (item: { name: string }, q: string) =>
    item.name.toLowerCase().includes(q.toLowerCase());

  it("filters items by query", () => {
    const { result } = renderHook(() =>
      useLedgerFilter(items, { key: "test-filter", match }),
    );
    expect(result.current.filtered).toHaveLength(3);
    act(() => result.current.setQuery("alp"));
    expect(result.current.filtered).toHaveLength(1);
    expect(result.current.filtered[0].name).toBe("alpha");
  });

  it("persists query to localStorage", () => {
    const { result } = renderHook(() =>
      useLedgerFilter(items, { key: "persist-test", match }),
    );
    act(() => result.current.setQuery("beta"));
    expect(localStorage.getItem("hs.filter.persist-test")).toBe("beta");
  });

  it("restores query from localStorage on mount", () => {
    localStorage.setItem("hs.filter.restore-test", "gamma");
    const { result } = renderHook(() =>
      useLedgerFilter(items, { key: "restore-test", match }),
    );
    expect(result.current.query).toBe("gamma");
    expect(result.current.filtered).toHaveLength(1);
  });

  it("clears query and removes from localStorage", () => {
    localStorage.setItem("hs.filter.clear-test", "alpha");
    const { result } = renderHook(() =>
      useLedgerFilter(items, { key: "clear-test", match }),
    );
    act(() => result.current.clear());
    expect(result.current.query).toBe("");
    expect(localStorage.getItem("hs.filter.clear-test") || "").toBe("");
  });

  it("reports isActive only when query or tokens are present", () => {
    const { result } = renderHook(() =>
      useLedgerFilter(items, { key: "active-test", match }),
    );
    expect(result.current.isActive).toBe(false);
    act(() => result.current.setQuery("a"));
    expect(result.current.isActive).toBe(true);
    act(() => result.current.setQuery(""));
    expect(result.current.isActive).toBe(false);
    act(() => result.current.addToken("status", "done"));
    expect(result.current.isActive).toBe(true);
  });

  it("deduplicates tokens", () => {
    const { result } = renderHook(() =>
      useLedgerFilter(items, { key: "dedup-test", match }),
    );
    act(() => {
      result.current.addToken("status", "done");
      result.current.addToken("status", "done");
    });
    expect(result.current.tokens).toHaveLength(1);
  });
});

describe("LedgerFilterBar", () => {
  it("renders input and count", () => {
    const onChange = vi.fn();
    render(
      <LedgerFilterBar
        query=""
        onQueryChange={onChange}
        tokens={[]}
        onRemoveToken={vi.fn()}
        onClear={vi.fn()}
        total={10}
        matchCount={10}
        isActive={false}
      />,
    );
    expect(screen.getByPlaceholderText("Filter...")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.queryByText("Clear")).toBeNull();
  });

  it("shows clear button and ratio when active", () => {
    render(
      <LedgerFilterBar
        query="test"
        onQueryChange={vi.fn()}
        tokens={[]}
        onRemoveToken={vi.fn()}
        onClear={vi.fn()}
        total={10}
        matchCount={3}
        isActive={true}
      />,
    );
    expect(screen.getByText("3/10")).toBeInTheDocument();
    expect(screen.getByText("Clear")).toBeInTheDocument();
  });

  it("renders token pills with remove buttons", () => {
    const onRemove = vi.fn();
    render(
      <LedgerFilterBar
        query=""
        onQueryChange={vi.fn()}
        tokens={[{ field: "status", value: "done" }]}
        onRemoveToken={onRemove}
        onClear={vi.fn()}
        total={10}
        matchCount={5}
        isActive={true}
      />,
    );
    expect(screen.getByText("status")).toBeInTheDocument();
    expect(screen.getByText("done")).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Remove status filter: done" }),
    );
    expect(onRemove).toHaveBeenCalledWith("status", "done");
  });
});
