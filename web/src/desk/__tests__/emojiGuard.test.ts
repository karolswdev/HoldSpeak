/** HS-148-05 — the emoji guard: the Phase-129 sprites-never-emoji
 * doctrine finally enforced. This test sweeps the UI-label and glyph
 * SOURCE files for emoji codepoints. The allowed vocabulary is the
 * established geometric/dingbat set, explicitly enumerated below.
 *
 * Fails on any Emoji_Presentation codepoint or common emoji range
 * character that is NOT in the allowed set. */
import { describe, expect, it } from "vitest";
import fs from "node:fs";
import path from "node:path";

// ── The allowed unicode glyph vocabulary (HS-148-05) ──────────────
// Every character here is a geometric/dingbat/symbol from the shipped
// code. Adding a new glyph to this set is a conscious act; adding an
// emoji is a test failure.
const ALLOWED_GLYPHS = new Set([
  // DESK_TOOLS program glyphs (tools.ts)
  "⌁", // ELECTRIC ARROW — Speak
  "✦", // BLACK FOUR POINTED STAR — Ask AI
  "▣", // WHITE SQUARE WITH VERTICAL BISECTING LINE — Meetings / Runs on
  "⚙", // GEAR — Settings
  "⚒", // HAMMER AND PICK — Workbenches
  "◉", // FISHEYE — Agents and coder sessions
  "↗", // NORTH EAST ARROW — Integrations
  "⌘", // PLACE OF INTEREST SIGN — Commands
  "◷", // WHITE CIRCLE WITH UPPER RIGHT QUADRANT — Cadence
  "§", // SECTION SIGN — Context
  "≋", // TRIPLE TILDE — Activity
  "∷", // PROPORTION — Processes
  // KIND_GLYPH create-noun glyphs (tools.ts)
  "▤", // horizontal rules — note
  "◈", // diamond with inner — decision
  "⬡", // hexagon — kb
  "◎", // bullseye — recipe/agent
  "⟁", // triangle with dots — workflow
  "⊞", // boxed plus — workbench
  "◰", // square upper-left quadrant — zone
  // verbRegistry.ts object/desk verb glyphs
  "◆", // BLACK DIAMOND — Intelligence
  "⊕", // CIRCLED PLUS — People
  "▷", // WHITE RIGHT-POINTING TRIANGLE — Open
  "⊙", // CIRCLED DOT — Get Info
  "✎", // LOWER RIGHT PENCIL — Edit
  "⌶", // APL FUNCTIONAL SYMBOL I-BEAM — Rename
  "⧉", // TWO JOINED SQUARES — Duplicate
  "↦", // RIGHTWARDS ARROW FROM BAR — Move to Zone
  "⌫", // ERASE TO THE LEFT — Delete
  // DeskToolShelf.tsx inline deck glyphs
  "◇", // WHITE DIAMOND — contextual capability
  "▸", // BLACK RIGHT-POINTING SMALL TRIANGLE — generic verb
  // DeskMenu.tsx menu chrome
  "◂", // BLACK LEFT-POINTING SMALL TRIANGLE — back row
  "»", // RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK — submenu
]);

// ── The files to sweep ────────────────────────────────────────────
// These are the source files that emit glyph/label text into menu,
// deck, and palette UI. windowMenuAdapter.tsx uses only VerbGlyph
// React components (no string glyphs) but is swept for completeness.
const DESK_SRC = path.resolve(__dirname, "..");
const SWEEP_FILES = [
  path.join(DESK_SRC, "verbRegistry.ts"),
  path.join(DESK_SRC, "tools.ts"),
  path.join(DESK_SRC, "floorMenu.ts"),
  path.join(DESK_SRC, "components", "DeskChrome.tsx"),
  path.join(DESK_SRC, "components", "DeskToolShelf.tsx"),
  path.join(DESK_SRC, "windowMenuAdapter.tsx"),
];

// ── Emoji detection ───────────────────────────────────────────────
// Match Emoji_Presentation codepoints and common emoji ranges.
// This covers:
//   - U+1F600..U+1F64F  Emoticons
//   - U+1F300..U+1F5FF  Misc Symbols and Pictographs
//   - U+1F680..U+1F6FF  Transport and Map Symbols
//   - U+1F900..U+1F9FF  Supplemental Symbols and Pictographs
//   - U+1FA00..U+1FA6F  Chess Symbols
//   - U+1FA70..U+1FAFF  Symbols and Pictographs Extended-A
//   - U+2600..U+26FF    Misc Symbols (subset: emoji-presentation)
//   - U+2700..U+27BF    Dingbats (subset: emoji-presentation)
//   - U+FE00..U+FE0F    Variation Selectors (emoji vs text)
//   - U+200D            Zero Width Joiner (emoji sequences)
// The allowed set exempts the geometric/dingbat characters we use.
const EMOJI_RANGES =
  /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{200D}\u{FE00}-\u{FE0F}]/u;

// Extended check: some emoji live in the Misc Symbols (2600-26FF) and
// Dingbats (2700-27BF) blocks. We check those ranges but allow our
// known-good characters.
const MISC_SYMBOL_EMOJI =
  /[\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u;

function findEmoji(
  content: string,
  filePath: string,
): { file: string; line: number; char: string; cp: string }[] {
  const hits: { file: string; line: number; char: string; cp: string }[] = [];
  const lines = content.split("\n");
  for (let i = 0; i < lines.length; i++) {
    // Skip comment-only lines (// ...) to reduce noise.
    const trimmed = lines[i].trimStart();
    if (trimmed.startsWith("//") || trimmed.startsWith("*") || trimmed.startsWith("/*")) continue;
    for (const ch of lines[i]) {
      const cp = ch.codePointAt(0)!;
      // Always-emoji ranges (supplemental planes).
      if (EMOJI_RANGES.test(ch) && !ALLOWED_GLYPHS.has(ch)) {
        hits.push({
          file: path.basename(filePath),
          line: i + 1,
          char: ch,
          cp: `U+${cp.toString(16).toUpperCase().padStart(4, "0")}`,
        });
        continue;
      }
      // Misc Symbols / Dingbats — only flag if NOT in our allowed set.
      if (MISC_SYMBOL_EMOJI.test(ch) && !ALLOWED_GLYPHS.has(ch)) {
        hits.push({
          file: path.basename(filePath),
          line: i + 1,
          char: ch,
          cp: `U+${cp.toString(16).toUpperCase().padStart(4, "0")}`,
        });
      }
    }
  }
  return hits;
}

describe("emoji guard (HS-148-05)", () => {
  it("the sweep file set exists and is non-empty", () => {
    for (const f of SWEEP_FILES) {
      expect(fs.existsSync(f), `sweep file missing: ${f}`).toBe(true);
    }
    expect(SWEEP_FILES.length).toBeGreaterThanOrEqual(6);
  });

  it("no emoji codepoints in the glyph/label source files", () => {
    const allHits: { file: string; line: number; char: string; cp: string }[] =
      [];
    for (const f of SWEEP_FILES) {
      const content = fs.readFileSync(f, "utf-8");
      allHits.push(...findEmoji(content, f));
    }
    expect(allHits, formatHits(allHits)).toHaveLength(0);
  });

  it("the allowed vocabulary passes (sanity)", () => {
    // Build a fake source line with every allowed glyph.
    const line = `glyph: "${[...ALLOWED_GLYPHS].join("")}"`;
    const hits = findEmoji(line, "sanity.ts");
    expect(hits).toHaveLength(0);
  });

  it("an injected emoji is caught (proof of detection)", () => {
    const line = 'glyph: "\u{1F600}"'; // 😀
    const hits = findEmoji(line, "injected.ts");
    expect(hits.length).toBeGreaterThan(0);
    expect(hits[0].cp).toBe("U+1F600");
  });
});

function formatHits(
  hits: { file: string; line: number; char: string; cp: string }[],
): string {
  if (hits.length === 0) return "";
  return (
    "Emoji codepoints found in glyph/label sources (the Phase-129 " +
    "sprites-never-emoji doctrine). Remove or replace with a " +
    "geometric/dingbat character and add it to ALLOWED_GLYPHS:\n" +
    hits.map((h) => `  ${h.file}:${h.line} ${h.char} (${h.cp})`).join("\n")
  );
}
