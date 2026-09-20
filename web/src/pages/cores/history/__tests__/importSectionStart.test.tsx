// HS-201-10 — the Import gesture does not date the meeting by the file.
//
// Rehearsal defect 10: `body.append("started_at_ms", String(file.lastModified))`
// sent the file's mtime as the meeting's start, so a WAV copied onto the disk
// in June filed the meeting under JUN 03. The import moment is the only fact
// this gesture knows; the hub stamps it.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn(async () => ({ meeting_id: "abc12345" }));
vi.mock("../../../../lib/api", async () => {
  const actual = await vi.importActual<Record<string, unknown>>(
    "../../../../lib/api",
  );
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...(args as [])) };
});

import { ImportSection } from "../ImportSection";

/** A file whose mtime is three months old, exactly like the rehearsal's. */
function agedWav(): File {
  const file = new File([new Uint8Array([1, 2, 3, 4])], "core_path_smoke_16k.wav", {
    type: "audio/wav",
    lastModified: Date.parse("2026-06-03T10:00:00Z"),
  });
  return file;
}

describe("ImportSection start stamp", () => {
  beforeEach(() => apiFetch.mockClear());

  it("posts the file with no started_at_ms of its own", async () => {
    const { container } = render(
      <ImportSection onDone={vi.fn()} onImported={vi.fn()} />,
    );
    const input = container.querySelector("input[type=file]") as HTMLInputElement;
    const file = agedWav();
    expect(file.lastModified).toBe(Date.parse("2026-06-03T10:00:00Z"));
    Object.defineProperty(input, "files", { value: [file] });
    fireEvent.change(input);

    fireEvent.click(screen.getByRole("button", { name: "Import" }));

    await waitFor(() => expect(apiFetch).toHaveBeenCalled());
    const [path, init] = apiFetch.mock.calls[0] as unknown as [
      string,
      { body: FormData },
    ];
    expect(path).toBe("/api/meetings/import");
    const body = init.body as FormData;
    expect(body.get("file")).toBeTruthy();
    expect(body.get("started_at_ms")).toBeNull();
    expect([...body.keys()]).not.toContain("started_at_ms");
  });
});
