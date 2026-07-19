// HS-101 B3 — the dated stream: the time grammar reads honestly and
// the composition puts the said-text at the primary step with verbs
// on the entry.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  SurfaceStream,
  SurfaceStreamDay,
  SurfaceStreamEntry,
} from "../Surface";
import { streamDate, streamDayLabel, streamTime } from "../format";

describe("the stream time grammar", () => {
  it("streamDate reads epoch seconds, epoch millis, ISO — and refuses junk", () => {
    const iso = "2026-07-19T09:38:00Z";
    expect(streamDate(iso)?.toISOString()).toBe("2026-07-19T09:38:00.000Z");
    const seconds = Math.floor(Date.parse(iso) / 1000);
    expect(streamDate(seconds)?.toISOString()).toBe(
      "2026-07-19T09:38:00.000Z",
    );
    expect(streamDate(Date.parse(iso))?.toISOString()).toBe(
      "2026-07-19T09:38:00.000Z",
    );
    expect(streamDate("not a time")).toBeNull();
    expect(streamDate(undefined)).toBeNull();
    expect(streamDate(Number.NaN)).toBeNull();
  });

  it("streamDayLabel: Today, Yesterday, then the honest date — Undated for null", () => {
    const now = new Date(2026, 6, 19, 12, 0, 0);
    expect(streamDayLabel(new Date(2026, 6, 19, 9, 0), now)).toMatch(
      /^Today — /,
    );
    expect(streamDayLabel(new Date(2026, 6, 18, 23, 59), now)).toMatch(
      /^Yesterday — /,
    );
    expect(streamDayLabel(new Date(2026, 6, 16), now)).not.toMatch(
      /Today|Yesterday/,
    );
    expect(streamDayLabel(null)).toBe("Undated");
  });

  it("streamTime is empty for null, HH:MM otherwise", () => {
    expect(streamTime(null)).toBe("");
    expect(streamTime(new Date(2026, 6, 19, 9, 5))).toMatch(/09.05/);
  });
});

describe("the stream composition", () => {
  it("head leads with the count at display step; entries carry when/said/meta/verbs", () => {
    const { container } = render(
      <SurfaceStream count={14} countLabel="today · 2 taught">
        <SurfaceStreamDay label="Today — Sun, Jul 19">
          <SurfaceStreamEntry
            when="09:38"
            meta={<span>→ Terminal</span>}
            verbs={<button type="button">Replay</button>}
          >
            Tightened the token gate.
          </SurfaceStreamEntry>
        </SurfaceStreamDay>
      </SurfaceStream>,
    );
    const count = container.querySelector(".surface-stream-head .surface-display");
    expect(count?.textContent).toBe("14");
    expect(screen.getByText("today · 2 taught")).toBeTruthy();
    expect(screen.getByText("Today — Sun, Jul 19")).toBeTruthy();
    const entry = container.querySelector(".surface-stream-entry");
    expect(entry?.querySelector(".surface-stream-when")?.textContent).toBe(
      "09:38",
    );
    expect(entry?.querySelector(".surface-stream-said")?.textContent).toBe(
      "Tightened the token gate.",
    );
    expect(
      entry?.querySelector(".surface-stream-meta")?.textContent,
    ).toContain("→ Terminal");
    // verbs sit ON the meta line and ride the reveal class — the
    // fluidity contract's hook (no reserved empty band under entries)
    const verbs = entry?.querySelector(".surface-stream-verbs");
    expect(verbs?.classList.contains("surface-row-verbs")).toBe(true);
    expect(verbs?.closest(".surface-stream-meta")).toBeTruthy();
  });
});
