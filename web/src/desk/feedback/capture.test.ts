import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { waitFor } from "@testing-library/react";
import { captureWindowPng } from "./capture";

const renderer = vi.hoisted(() => ({ toPng: vi.fn() }));
vi.mock("html-to-image", () => renderer);

const fonts = Object.getOwnPropertyDescriptor(document, "fonts");
let root: HTMLDivElement;
const wrappers = () => Array.from(document.body.children).filter(
  (node) => node instanceof HTMLElement && node.style.left === "-100000px",
);

beforeEach(() => {
  renderer.toPng.mockReset().mockResolvedValue("data:image/png;base64,PNG_BYTES");
  root = document.createElement("div");
  root.style.setProperty("--capture-test-token", "red");
  root.style.content = "normal";
  root.style.fill = "none";
  root.style.insetInlineStart = "888px";
  root.style.insetBlockStart = "64px";
  root.style.right = "152px";
  root.style.bottom = "183px";
  root.innerHTML = '<input aria-label="Draft" value="draft"><span style="color: rgb(2, 3, 4)">Report</span><svg><path style="fill: rgb(7, 8, 9)" d="M0 0h4v4z" /></svg>';
  document.body.appendChild(root);
  // jsdom has no pseudo style computation. Supply that browser capability
  // at the leaf while retaining real computed styles for the frozen tree.
  const compute = window.getComputedStyle.bind(window);
  vi.stubGlobal("getComputedStyle", vi.fn((node: Element, pseudo?: string | null) => {
    if (pseudo && node === root && pseudo === "::before") {
      const style = document.createElement("span").style;
      style.content = '"Snapshot marker"';
      style.color = "rgb(5, 6, 7)";
      return style;
    }
    if (pseudo) return document.createElement("span").style;
    return compute(node);
  }));
});
afterEach(() => {
  document.body.replaceChildren();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  if (fonts) Object.defineProperty(document, "fonts", fonts);
  else Reflect.deleteProperty(document, "fonts");
});

describe("frozen window rendering", () => {
  it("passes resolved styles without per-element token duplication and keeps live values", async () => {
    root.querySelector("input")!.value = "unsaved value";
    renderer.toPng.mockImplementation(async (node, options) => {
      expect(node.querySelector("input").value).toBe("unsaved value");
      expect(node.querySelector("span").style.color).toBe("rgb(2, 3, 4)");
      expect(node.querySelector("span").style.getPropertyValue("--capture-test-token")).toBe("");
      expect(node.querySelector("path").style.fill).toBe("rgb(7, 8, 9)");
      expect(node.querySelector("style").textContent).toContain('content: "Snapshot marker"');
      expect(node.style.insetInlineStart).toBe("");
      expect(node.style.insetBlockStart).toBe("");
      expect(node.style.left).toBe("0px");
      expect(node.style.top).toBe("0px");
      expect(node.style.right).toBe("auto");
      expect(node.style.bottom).toBe("auto");
      expect(options.includeStyleProperties).toEqual([]);
      return "data:image/png;base64,PNG_BYTES";
    });
    await expect(captureWindowPng(root)).resolves.toBe("PNG_BYTES");
    expect(wrappers()).toHaveLength(0);
    expect(root.querySelector("input")!.value).toBe("unsaved value");
  });

  it("cancels while fonts are pending and removes the temporary window immediately", async () => {
    Object.defineProperty(document, "fonts", { configurable: true, value: { ready: new Promise(() => {}) } });
    const controller = new AbortController();
    const pending = captureWindowPng(root, controller.signal);
    const rejected = expect(pending).rejects.toMatchObject({ name: "AbortError" });
    await waitFor(() => expect(wrappers()).toHaveLength(1));
    controller.abort();
    await rejected;
    expect(wrappers()).toHaveLength(0);
    expect(renderer.toPng).not.toHaveBeenCalled();
  });

  it("cancels pending rendering without waiting for a late image", async () => {
    let complete!: (value: string) => void;
    renderer.toPng.mockImplementation(() => new Promise<string>((resolve) => { complete = resolve; }));
    const controller = new AbortController();
    const pending = captureWindowPng(root, controller.signal);
    const rejected = expect(pending).rejects.toMatchObject({ name: "AbortError" });
    await waitFor(() => expect(renderer.toPng).toHaveBeenCalledOnce());
    const options = renderer.toPng.mock.calls[0][1];
    expect(options.fetchRequestInit.signal).toBe(controller.signal);
    controller.abort();
    await rejected;
    expect(wrappers()).toHaveLength(0);
    expect(() => options.filter(root)).toThrow("cancelled");
    complete("data:image/png;base64,LATE_IMAGE");
    await Promise.resolve();
    expect(wrappers()).toHaveLength(0);
  });

  it("removes the temporary window when font loading fails", async () => {
    let fail!: (reason: Error) => void;
    const ready = new Promise((_, reject) => { fail = reject; });
    Object.defineProperty(document, "fonts", { configurable: true, value: { ready } });
    const pending = captureWindowPng(root);
    const rejected = expect(pending).rejects.toThrow("Font failed");
    await waitFor(() => expect(wrappers()).toHaveLength(1));
    fail(new Error("Font failed"));
    await rejected;
    expect(wrappers()).toHaveLength(0);
  });

  it("names an image failure when the renderer rejects with a browser event", async () => {
    renderer.toPng.mockRejectedValue(new Event("error"));
    await expect(captureWindowPng(root)).rejects.toThrow("Window image failed. Try again.");
    expect(wrappers()).toHaveLength(0);
  });
});
