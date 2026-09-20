// HS-201-10 — the imported meeting's two facts: its length and its date.
//
// The 2026-09-20 rehearsal imported tests/fixtures/core_path_smoke_16k.wav
// (2.79 s) and the row read `JUN 03 · 1 MIN · ● RAN · 4 S`:
//   defect 9  — `1 MIN` for a 2.79 s file, beside the `5 S` the run took;
//   defect 10 — `JUN 03`, the file's mtime, three months back in the ledger.
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { durationToken, ledgerDate } from "../helpers";
import { CatalogRail } from "../CatalogRail";

const FIXTURE_SECONDS = 2.7946875; // the rehearsal's WAV, to the sample

describe("durationToken tells the truth about a short recording", () => {
  it("says seconds under a minute — never `1 MIN` for a 2.79 s file", () => {
    expect(durationToken(FIXTURE_SECONDS)).toBe("3 S");
    expect(durationToken(FIXTURE_SECONDS)).not.toBe("1 MIN");
    expect(durationToken(1)).toBe("1 S");
    expect(durationToken(45)).toBe("45 S");
    expect(durationToken(59.4)).toBe("59 S");
  });

  it("never rounds a real recording away to nothing", () => {
    // Below thirty seconds the old token rounded to `0 MIN` and returned
    // the empty string: a real recording with no length at all.
    expect(durationToken(0.6)).toBe("1 S");
    expect(durationToken(29)).toBe("29 S");
  });

  it("keeps minutes and hours where they belong", () => {
    expect(durationToken(60)).toBe("1 MIN");
    expect(durationToken(90)).toBe("2 MIN");
    expect(durationToken(1800)).toBe("30 MIN");
    expect(durationToken(36000)).toBe("10 HR");
  });

  it("stays empty when the wire carries no duration", () => {
    expect(durationToken(0)).toBe("");
    expect(durationToken(null)).toBe("");
    expect(durationToken(undefined)).toBe("");
    expect(durationToken("not a number")).toBe("");
    expect(durationToken(-5)).toBe("");
  });
});

describe("the imported row draws that length and today's date", () => {
  function row(startedAt: string) {
    return [
      {
        id: "imported-1",
        title: "core path smoke 16k",
        started_at: startedAt,
        duration_seconds: FIXTURE_SECONDS,
        capture_status: "finalized",
        intel_status: "disabled",
        transcriptWords: 9,
      },
    ];
  }

  function draw(startedAt: string) {
    render(
      <CatalogRail
        meetingRows={row(startedAt)}
        meetings={{ loading: false, error: "", reload: vi.fn(async () => ({})) }}
        selected={null}
        setSelected={vi.fn()}
        onRunIntelligence={vi.fn()}
        runningId={null}
      />,
    );
  }

  it("shows `3 S`, not `1 MIN`, for the rehearsal's file", () => {
    draw(new Date().toISOString());
    expect(screen.getByText("3 S")).toBeInTheDocument();
    expect(screen.queryByText("1 MIN")).toBeNull();
  });

  it("is dated the import moment, which the hub stamps as now", () => {
    const now = new Date();
    draw(now.toISOString());
    expect(screen.getByText(ledgerDate(now.toISOString()))).toBeInTheDocument();
    // The rehearsal's row said JUN 03 for a file imported on 2026-09-20.
    expect(screen.queryByText("JUN 03")).toBeNull();
  });
});
