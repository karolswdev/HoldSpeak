/** PHILO-8-02 round six — a failure about a subject is cleared only by a
 * landed write about the same subject (the Workbench's local channel). */
import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { useWriteReceipt } from "../useWriteReceipt";

const refuse = async () => {
  throw Object.assign(new Error("Item locked"), { name: "ApiError", status: 403 });
};
const land = async () => "ok";

describe("useWriteReceipt subject rule", () => {
  it("another subject's success keeps the failure; the same subject's success clears it", async () => {
    const { result } = renderHook(() => useWriteReceipt());
    await act(async () => { await result.current.attempt("REMOVE ITEM", refuse, { subject: "a" }); });
    expect(result.current.failure?.subject).toBe("a");
    await act(async () => { await result.current.attempt("REMOVE ITEM", land, { subject: "b" }); });
    expect(result.current.failure?.subject).toBe("a");
    expect(result.current.failure?.detail).toBe("Item locked");
    await act(async () => { await result.current.attempt("REMOVE ITEM", land, { subject: "a" }); });
    expect(result.current.failure).toBeNull();
  });

  it("a failure without a subject is still cleared by any landed write", async () => {
    const { result } = renderHook(() => useWriteReceipt());
    await act(async () => { await result.current.attempt("SAVE", refuse); });
    expect(result.current.failure).not.toBeNull();
    await act(async () => { await result.current.attempt("SAVE", land); });
    expect(result.current.failure).toBeNull();
  });
});

// Round seven — the desk (module) channel, by construction.
import { clearWriteFailure, currentWriteFailure, dismissWriteFailure, reportWriteFailure } from "../useWriteReceipt";

describe("desk channel subject rule", () => {
  it("a subject-less clear does not remove a failure about a subject; a matching clear does", () => {
    reportWriteFailure("DELETE", "HTTP 403", undefined, "decision:a");
    clearWriteFailure();
    expect(currentWriteFailure()?.subject).toBe("decision:a");
    clearWriteFailure("decision:b");
    expect(currentWriteFailure()?.subject).toBe("decision:a");
    clearWriteFailure("decision:a");
    expect(currentWriteFailure()).toBeNull();
  });

  it("a failure with no subject is removed by any clear", () => {
    reportWriteFailure("CREATE zone", "HTTP 500");
    clearWriteFailure("note:x");
    expect(currentWriteFailure()).toBeNull();
  });

  it("the owner's dismissal removes any failure", () => {
    reportWriteFailure("DELETE", "HTTP 403", undefined, "decision:a");
    dismissWriteFailure();
    expect(currentWriteFailure()).toBeNull();
  });
});
