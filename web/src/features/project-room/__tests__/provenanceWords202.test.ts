/* HS-202-04 — the provenance token speaks whole words (F21).
 *
 * `surface-inventory-2026-09-20/02-coherence-astra.md:133`: "SEG and MTG
 * make provenance harder to read than segment/meeting. The abbreviation is
 * present; no rendered first-use definition was established."
 * Constitution tenet 4 (ASD-STE100) wants the common word, and HS-201-06
 * already paid the same debt one face over — `KEPT 3 SEGMENTS`, never
 * `RETAINED 3 SEG / 2 ART` (`meetings/MeetingIntelRecovery.tsx:57-61`).
 *
 * Three-letter LEAD EMBLEMS in the 52px ledger slot (`MTG` · `GH` · `J`,
 * `desk/surface/contract.md:265`) are a species contract with a fixed
 * width and are NOT this fence: they are a glyph, not a sentence. This
 * token is a full provenance LINE, where the word fits.
 */
import { describe, expect, it } from "vitest";
import { sourceToken } from "../RoomPeopleSection";

import type { RoomPersonCommitmentSource } from "../api";

const source = (segmentIndex?: number): RoomPersonCommitmentSource => ({
  kind: "meeting",
  meeting_id: "m1",
  label: "Architecture review",
  ...(segmentIndex == null ? {} : { segment_index: segmentIndex }),
});

describe("a commitment's source line (F21)", () => {
  it("names the meeting and the segment in words", () => {
    expect(sourceToken(source(3))).toBe(
      "Meeting · Architecture review · Segment 4",
    );
  });

  it("omits the segment when the wire has none", () => {
    expect(sourceToken(source())).toBe("Meeting · Architecture review");
  });

  it("never renders the undefined abbreviations", () => {
    expect(sourceToken(source(0))).not.toMatch(/\b(SEG|MTG)\b/);
  });
});
