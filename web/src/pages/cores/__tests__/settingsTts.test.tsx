import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TtsSettingsBlock } from "../settingsTts";

let unavailable: boolean;
let installed: boolean;
let ready: boolean;
beforeEach(() => {
  unavailable = false; installed = false; ready = false;
  vi.stubGlobal("speechSynthesis", { getVoices: () => [] });
  vi.stubGlobal("fetch", vi.fn(async (_url: string, init?: RequestInit) => new Response(JSON.stringify(
    unavailable ? { error: "Unavailable" } : init?.method === "POST" ? { receipt: { downloaded: true } } : { installed, model_ready: ready },
  ), { status: unavailable ? 503 : 200, headers: { "content-type": "application/json" } })));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

describe("Settings speech", () => {
  it("a failed status read offers Retry instead of an install instruction", async () => {
    unavailable = true;
    render(<TtsSettingsBlock />);
    const retry = await screen.findByRole("button", { name: "Retry" });
    expect(screen.queryByText(/pip install/)).toBeNull();
    unavailable = false;
    fireEvent.click(retry);
    expect(await screen.findByText(/pip install/)).toBeTruthy();
  });
  it("does not claim browser voice is available when the browser lacks synthesis", async () => {
    vi.stubGlobal("speechSynthesis", undefined);
    render(<TtsSettingsBlock />);
    expect(await screen.findByText("Not available")).toBeTruthy();
    expect(screen.queryByText("ACTIVE")).toBeNull();
  });
  it("an installed server can download its model and report the accepted result", async () => {
    installed = true;
    render(<TtsSettingsBlock />);
    const download = await screen.findByRole("button", { name: "Download model" });
    expect(screen.getByText(/huggingface.co/)).toBeTruthy();
    fireEvent.click(download);
    await waitFor(() => expect(screen.getByRole("status").textContent).toBe("Downloaded"));
    expect(screen.getByText("Ready")).toBeTruthy();
  });
});
